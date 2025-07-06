 /**
 * 应用控制器 - 管理应用程序状态机和生命周期
 */
class App {
    constructor() {
        this.currentState = 'initializing';
        this.previousState = null;
        this.stateHistory = [];
        this.maxHistoryLength = 10;
        
        this.renderEngine = null;
        this.dataManager = null;
        this.animationManager = null;
        
        this.eventListeners = {
            'stateChanged': [],
            'stateEntered': [],
            'stateExited': []
        };
        
        this.stateConfig = {
            initializing: {
                duration: null, // 无限期，直到数据加载成功
                autoTransition: true,
                canRetry: false
            },
            locked: {
                duration: 800, // 过渡时间
                autoTransition: true,
                canRetry: false
            },
            stable: {
                duration: null, // 无限期，直到数据变化
                autoTransition: false,
                canRetry: true
            },
            updating: {
                duration: 800, // 过渡时间
                autoTransition: true,
                canRetry: false
            },
            error: {
                duration: null, // 无限期，直到连接恢复
                autoTransition: false,
                canRetry: true
            }
        };
        
        this.stateTimers = {};
        
        this.init();
    }

    /**
     * 初始化应用
     */
    async init() {
        try {
            console.log('App: 开始初始化应用...');
            
            // 1. 初始化渲染引擎
            this.renderEngine = new RenderEngine();
            
            // 2. 等待渲染引擎配置加载完成
            await this.renderEngine.waitForConfig();
            
            // 3. 创建所有SVG元素（必须在组件初始化之前）
            this.renderEngine.createAllElements();
            
            // 4. 初始化数据管理器
            this.dataManager = new DataManager();
            
            // 5. 初始化统一动画管理器（此时SVG元素已存在）
            this.animationManager = new AnimationManager(this.renderEngine, this.dataManager);
            
            // 6. 绑定事件监听器
            this.bindEvents();
            
            // 7. 启动状态机
            this.setState('initializing');
            
            console.log('App: 应用初始化完成');
            
        } catch (error) {
            console.error('App: 初始化失败', error);
            this.setState('error');
        }
    }

    /**
     * 绑定事件监听器
     */
    bindEvents() {
        // 数据管理器事件
        this.dataManager.addEventListener('dataLoaded', (data) => {
            this.handleDataLoaded(data);
        });
        
        this.dataManager.addEventListener('dataChanged', (data) => {
            this.handleDataChanged(data);
        });
        
        this.dataManager.addEventListener('dataError', (error) => {
            this.handleDataError(error);
        });
        
        this.dataManager.addEventListener('connectionLost', (error) => {
            this.handleConnectionLost(error);
        });
        
        this.dataManager.addEventListener('connectionRestored', () => {
            this.handleConnectionRestored();
        });
    }

    /**
     * 设置应用状态
     * @param {string} newState 新状态
     * @param {Object} data 状态数据
     */
    setState(newState, data = {}) {
        if (newState === this.currentState) {
            return;
        }
        
        if (!this.stateConfig[newState]) {
            console.error(`App: 未知状态 ${newState}`);
            return;
        }
        
        // 退出当前状态
        this.exitState(this.currentState);
        
        // 更新状态历史
        this.previousState = this.currentState;
        this.currentState = newState;
        this.addToHistory(newState);
        
        // 进入新状态
        this.enterState(newState, data);
        
        // 触发状态变化事件
        this.triggerEvent('stateChanged', {
            previousState: this.previousState,
            currentState: this.currentState,
            data: data
        });
        
        console.log(`App: 状态切换 ${this.previousState} → ${this.currentState}`);
    }

    /**
     * 进入状态
     * @param {string} state 状态名称
     * @param {Object} data 状态数据
     */
    enterState(state, data) {
        const config = this.stateConfig[state];
        
        // 更新动画管理器状态
        this.updateAnimationState(state, data);
        
        // 更新状态指示器
        this.updateStatusIndicator(state);
        
        // 处理状态特定的逻辑
        switch (state) {
            case 'initializing':
                this.handleInitializingState();
                break;
            case 'locked':
                this.handleLockedState(data);
                break;
            case 'stable':
                this.handleStableState();
                break;
            case 'updating':
                this.handleUpdatingState(data);
                break;
            case 'error':
                this.handleErrorState();
                break;
        }
        
        // 设置自动转换定时器
        if (config.autoTransition && config.duration) {
            this.stateTimers[state] = setTimeout(() => {
                this.handleAutoTransition(state);
            }, config.duration);
        }
        
        this.triggerEvent('stateEntered', { state, data });
    }

    /**
     * 退出状态
     * @param {string} state 状态名称
     */
    exitState(state) {
        // 清除定时器
        if (this.stateTimers[state]) {
            clearTimeout(this.stateTimers[state]);
            delete this.stateTimers[state];
        }
        
        // 状态特定的清理逻辑
        switch (state) {
            case 'initializing':
                this.cleanupInitializingState();
                break;
            case 'stable':
                this.cleanupStableState();
                break;
            case 'error':
                this.cleanupErrorState();
                break;
        }
        
        this.triggerEvent('stateExited', { state });
    }

    /**
     * 更新动画管理器状态
     * @param {string} state 状态名称
     * @param {Object} data 状态数据
     */
    updateAnimationState(state, data) {
        if (this.animationManager) {
            // 动画管理器会自动处理状态切换
            console.log(`App: 动画管理器状态更新 ${state}`);
        }
    }

    /**
     * 更新状态指示器
     * @param {string} state 状态名称
     */
    updateStatusIndicator(state) {
        const statusElement = document.getElementById('status-text');
        const indicatorElement = document.getElementById('status-indicator');
        
        if (!statusElement || !indicatorElement) return;
        
        // 获取更新计数
        let updateCount = 0;
        if (this.animationManager) {
            updateCount = this.animationManager.getUpdateCount();
        }
        
        const statusMessages = {
            'initializing': 'Initializing...',
            'locked': 'Data Locked',
            'stable': `Updated ${updateCount} times`,
            'updating': 'Updating...'
        };
        
        const message = statusMessages[state] || 'Unknown State';
        statusElement.textContent = message;
        
        // 更新状态指示器的数据属性
        indicatorElement.dataset.state = state;
        
        console.log(`App: Status updated to "${message}"`);
    }

    /**
     * 处理初始化状态
     */
    handleInitializingState() {
        // 动画管理器会自动处理初始化状态
        console.log('App: 进入初始化状态');
    }

    /**
     * 处理锁定状态
     * @param {Object} data 状态数据
     */
    handleLockedState(data) {
        // 动画管理器会自动处理锁定状态
        console.log('App: 进入锁定状态');
    }

    /**
     * 处理稳定状态
     */
    handleStableState() {
        // 开始轮询
        this.dataManager.startPolling();
        
        // 动画管理器会自动处理稳定状态
        console.log('App: 进入稳定状态');
    }

    /**
     * 处理更新状态
     * @param {Object} data 状态数据
     */
    handleUpdatingState(data) {
        // 停止轮询
        this.dataManager.stopPolling();
        
        // 动画管理器会自动处理更新状态
        console.log('App: 进入更新状态');
    }

    /**
     * 处理错误状态 - 已移除，系统无错误状态
     */
    handleErrorState() {
        // 系统不再有错误状态，保持当前状态
        console.log('App: 系统无错误状态，保持当前状态');
    }

    /**
     * 清理初始化状态
     */
    cleanupInitializingState() {
        // 动画管理器会自动清理
        console.log('App: 清理初始化状态');
    }

    /**
     * 清理稳定状态
     */
    cleanupStableState() {
        this.dataManager.stopPolling();
        
        // 动画管理器会自动清理
        console.log('App: 清理稳定状态');
    }

    /**
     * 清理错误状态 - 已移除
     */
    cleanupErrorState() {
        // 系统不再有错误状态
        console.log('App: 系统无错误状态需要清理');
    }

    /**
     * 处理自动转换
     * @param {string} state 当前状态
     */
    handleAutoTransition(state) {
        switch (state) {
            case 'locked':
                this.setState('stable');
                break;
            case 'updating':
                this.setState('stable');
                break;
        }
    }

    /**
     * 处理数据加载成功
     * @param {Object} data 数据对象
     */
    handleDataLoaded(data) {
        if (this.currentState === 'initializing') {
            this.setState('locked', { values: data });
        }
    }

    /**
     * 处理数据变化
     * @param {Object} data 新数据
     */
    handleDataChanged(data) {
        if (this.currentState === 'stable') {
            this.setState('updating', { values: data });
        }
    }

    /**
     * 处理数据错误 - 已移除错误状态
     * @param {Error} error 错误对象
     */
    handleDataError(error) {
        // 系统不再有错误状态，保持当前状态
        console.warn('App: 数据错误，保持当前状态', error);
    }

    /**
     * 处理连接丢失 - 已移除错误状态
     * @param {Error} error 错误对象
     */
    handleConnectionLost(error) {
        // 系统不再有错误状态，保持当前状态
        console.warn('App: 连接丢失，保持当前状态', error);
    }

    /**
     * 处理连接恢复 - 已移除错误状态
     */
    handleConnectionRestored() {
        // 系统不再有错误状态
        console.log('App: 连接恢复');
    }

    /**
     * 添加状态到历史记录
     * @param {string} state 状态名称
     */
    addToHistory(state) {
        this.stateHistory.push({
            state: state,
            timestamp: Date.now()
        });
        
        // 限制历史记录长度
        if (this.stateHistory.length > this.maxHistoryLength) {
            this.stateHistory.shift();
        }
    }

    /**
     * 获取当前状态
     * @returns {string} 当前状态
     */
    getCurrentState() {
        return this.currentState;
    }

    /**
     * 获取状态历史
     * @returns {Array} 状态历史
     */
    getStateHistory() {
        return [...this.stateHistory];
    }

    /**
     * 添加事件监听器
     * @param {string} event 事件名称
     * @param {Function} callback 回调函数
     */
    addEventListener(event, callback) {
        if (this.eventListeners[event]) {
            this.eventListeners[event].push(callback);
        }
    }

    /**
     * 移除事件监听器
     * @param {string} event 事件名称
     * @param {Function} callback 回调函数
     */
    removeEventListener(event, callback) {
        if (this.eventListeners[event]) {
            const index = this.eventListeners[event].indexOf(callback);
            if (index > -1) {
                this.eventListeners[event].splice(index, 1);
            }
        }
    }

    /**
     * 触发事件
     * @param {string} event 事件名称
     * @param {*} data 事件数据
     */
    triggerEvent(event, data) {
        if (this.eventListeners[event]) {
            this.eventListeners[event].forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    console.error(`App: 事件回调执行错误 [${event}]`, error);
                }
            });
        }
    }

    /**
     * 销毁应用
     */
    destroy() {
        // 清除所有定时器
        Object.keys(this.stateTimers).forEach(state => {
            if (this.stateTimers[state]) {
                clearTimeout(this.stateTimers[state]);
            }
        });
        
        // 销毁组件
        if (this.animationManager) {
            this.animationManager.destroy();
        }
        
        if (this.dataManager) {
            this.dataManager.destroy();
        }
        
        if (this.renderEngine) {
            this.renderEngine.destroy();
        }
        
        // 清理事件监听器
        this.eventListeners = {};
        
        console.log('App: 应用已销毁');
    }

    /**
     * 等待初始化完成
     */
    async waitForInitialization() {
        // 等待所有组件初始化完成
        if (this.renderEngine && this.dataManager && this.animationManager) {
            return true;
        }
        
        // 如果还没初始化完成，等待
        while (!this.renderEngine || !this.dataManager || !this.animationManager) {
            await new Promise(resolve => setTimeout(resolve, 10));
        }
        
        return true;
    }
}

// 导出到全局作用域
window.App = App;