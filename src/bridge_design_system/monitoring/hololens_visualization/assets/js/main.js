/**
 * 应用主入口 - 启动HoloLens三圆可视化系统
 */
class Main {
    constructor() {
        this.app = null;
        this.isInitialized = false;
        this.debugMode = false;
        
        this.init();
    }

    /**
     * 初始化应用
     */
    async init() {
        try {
            console.log('Main: 开始初始化HoloLens三圆可视化系统...');
            
            // 检查调试模式
            this.checkDebugMode();
            
            // 启动应用程序
            await this.startApplication();
            
        } catch (error) {
            console.error('Main: 初始化失败', error);
            this.handleInitializationError(error);
        }
    }

    /**
     * 检查调试模式
     */
    checkDebugMode() {
        this.debugMode = localStorage.getItem('debug') === 'true';
        
        if (this.debugMode) {
            console.log('Main: 调试模式已启用');
            this.enableDebugFeatures();
        }
    }

    /**
     * 启用调试功能
     */
    enableDebugFeatures() {
        // 添加调试信息到页面
        this.addDebugInfo();
        
        // 添加测试数据到全局作用域
        window.testData = {
            "Self-Weight": 80,
            "Storage": 30,
            "Complexity": 50,
            "timestamp": Date.now()
        };
        
        // 添加测试函数
        window.testStateChange = (state) => {
            if (this.app) {
                this.app.setState(state);
            }
        };
        
        window.testDataChange = (data) => {
            if (this.app && this.app.dataManager) {
                this.app.dataManager.triggerEvent('dataChanged', data);
            }
        };
    }

    /**
     * 添加调试信息
     */
    addDebugInfo() {
        const debugInfo = document.createElement('div');
        debugInfo.id = 'debug-info';
        debugInfo.style.cssText = `
            position: fixed;
            top: 10px;
            right: 10px;
            background: rgba(0, 0, 0, 0.8);
            color: #00FF00;
            padding: 10px;
            border-radius: 5px;
            font-family: monospace;
            font-size: 12px;
            z-index: 10000;
            max-width: 300px;
        `;
        debugInfo.innerHTML = `
            <div><strong>调试模式</strong></div>
            <div>状态: <span id="debug-state">初始化中...</span></div>
            <div>数据: <span id="debug-data">等待连接...</span></div>
            <div>FPS: <span id="debug-fps">--</span></div>
            <hr style="margin: 5px 0; border-color: #333;">
            <div><strong>测试命令:</strong></div>
            <div>testStateChange('stable')</div>
            <div>testDataChange(window.testData)</div>
        `;
        
        document.body.appendChild(debugInfo);
        
        // 定期更新调试信息
        this.startDebugUpdate();
    }

    /**
     * 开始调试信息更新
     */
    startDebugUpdate() {
        let frameCount = 0;
        let lastTime = performance.now();
        
        const updateDebug = () => {
            frameCount++;
            const currentTime = performance.now();
            
            if (currentTime - lastTime >= 1000) {
                const fps = Math.round((frameCount * 1000) / (currentTime - lastTime));
                const fpsElement = document.getElementById('debug-fps');
                if (fpsElement) {
                    fpsElement.textContent = fps;
                }
                
                frameCount = 0;
                lastTime = currentTime;
            }
            
            // 更新状态信息
            if (this.app) {
                const stateElement = document.getElementById('debug-state');
                if (stateElement) {
                    stateElement.textContent = this.app.getCurrentState();
                }
                
                const dataElement = document.getElementById('debug-data');
                if (dataElement) {
                    const data = this.app.dataManager.getCurrentData();
                    if (data) {
                        dataElement.textContent = `W:${data['Self-Weight']} S:${data['Storage']} C:${data['Complexity']}`;
                    } else {
                        dataElement.textContent = '无数据';
                    }
                }
            }
            
            requestAnimationFrame(updateDebug);
        };
        
        updateDebug();
    }

    /**
     * 启动应用程序
     */
    async startApplication() {
        try {
            console.log('Main: 启动应用程序...');
            
            // 创建应用实例
            this.app = new App();
            
            // 等待应用初始化完成
            await this.app.waitForInitialization();
            
            // 绑定应用事件
            this.bindAppEvents();
            
            // 标记为已初始化
            this.isInitialized = true;
            
            console.log('Main: 应用程序启动完成');
            
            // 触发启动完成事件
            this.triggerStartupComplete();
            
        } catch (error) {
            console.error('Main: 应用程序启动失败', error);
            this.handleStartupError(error);
        }
    }

    /**
     * 绑定应用事件
     */
    bindAppEvents() {
        if (!this.app) return;
        
        // 状态变化事件
        this.app.addEventListener('stateChanged', (data) => {
            this.handleStateChanged(data);
        });
        
        // 数据管理器事件
        if (this.app.dataManager) {
            this.app.dataManager.addEventListener('dataLoaded', (data) => {
                this.handleDataLoaded(data);
            });
            
            this.app.dataManager.addEventListener('dataChanged', (data) => {
                this.handleDataChanged(data);
            });
            
            this.app.dataManager.addEventListener('dataError', (error) => {
                this.handleDataError(error);
            });
        }
        
        // 动画管理器事件
        if (this.app.animationManager) {
            this.app.animationManager.addEventListener('dataUpdated', (data) => {
                this.handleAnimationDataUpdated(data);
            });
            
            this.app.animationManager.addEventListener('collisionDetected', (data) => {
                this.handleCollisionDetected(data);
            });
        }
    }

    /**
     * 处理状态变化
     * @param {Object} data 状态变化数据
     */
    handleStateChanged(data) {
        console.log(`Main: 状态变化 ${data.previousState} → ${data.currentState}`);
        
        // 更新状态指示器
        this.updateStatusIndicator(data.currentState);
        
        // 调试模式下的额外处理
        if (this.debugMode) {
            this.logStateChange(data);
        }
    }

    /**
     * 处理数据加载
     * @param {Object} data 数据对象
     */
    handleDataLoaded(data) {
        console.log('Main: 数据加载成功', data);
        
        // 调试模式下的额外处理
        if (this.debugMode) {
            this.logDataLoaded(data);
        }
    }

    /**
     * 处理数据变化
     * @param {Object} data 新数据
     */
    handleDataChanged(data) {
        console.log('Main: 数据发生变化', data);
        
        // 调试模式下的额外处理
        if (this.debugMode) {
            this.logDataChanged(data);
        }
    }

    /**
     * 处理数据错误
     * @param {Error} error 错误对象
     */
    handleDataError(error) {
        console.warn('Main: 数据错误，保持当前状态', error);
        
        // 系统不再有错误状态，保持当前状态
    }
    
    /**
     * 处理动画数据更新
     * @param {Object} data 更新数据
     */
    handleAnimationDataUpdated(data) {
        console.log('Main: 动画数据更新', data);
        
        if (this.debugMode) {
            this.updateDebugInfo('animation', `更新次数: ${data.updateCount}`);
        }
    }
    
    /**
     * 处理碰撞检测
     * @param {Object} data 碰撞数据
     */
    handleCollisionDetected(data) {
        console.log('Main: 检测到碰撞', data);
        
        if (this.debugMode) {
            this.updateDebugInfo('collision', `${data.circle1.id} ↔ ${data.circle2.id}`);
        }
    }

    /**
     * 更新状态指示器
     * @param {string} state 状态名称
     */
    updateStatusIndicator(state) {
        const statusText = document.getElementById('status-text');
        if (!statusText) return;
        
        // 获取更新计数
        let updateCount = 0;
        if (this.app && this.app.animationManager) {
            updateCount = this.app.animationManager.getUpdateCount();
        }
        
        const statusMessages = {
            initializing: 'Initializing...',
            locked: 'Data Locked',
            stable: `Updated ${updateCount} times`,
            updating: 'Data Updating'
        };
        
        statusText.textContent = statusMessages[state] || 'Unknown State';
        statusText.className = `status-${state}`;
    }
    
    /**
     * 更新调试信息
     * @param {string} type 信息类型
     * @param {string} message 信息内容
     */
    updateDebugInfo(type, message) {
        const debugInfo = document.getElementById('debug-info');
        if (!debugInfo) return;
        
        const infoElement = debugInfo.querySelector(`#debug-${type}`);
        if (infoElement) {
            infoElement.textContent = message;
        }
    }

    /**
     * 处理初始化错误
     * @param {Error} error 错误对象
     */
    handleInitializationError(error) {
        console.error('Main: 初始化错误', error);
        
        // 显示错误信息
        this.showErrorMessage('Initialization Failed: ' + error.message);
    }

    /**
     * 处理启动错误
     * @param {Error} error 错误对象
     */
    handleStartupError(error) {
        console.error('Main: 启动错误', error);
        
        // 显示错误信息
        this.showErrorMessage('Startup Failed: ' + error.message);
    }

    /**
     * 显示错误信息
     * @param {string} message 错误消息
     */
    showErrorMessage(message) {
        const errorDiv = document.createElement('div');
        errorDiv.style.cssText = `
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: rgba(255, 0, 0, 0.9);
            color: white;
            padding: 20px;
            border-radius: 10px;
            font-family: Arial, sans-serif;
            font-size: 16px;
            z-index: 10000;
            text-align: center;
        `;
        errorDiv.textContent = message;
        
        document.body.appendChild(errorDiv);
        
        // 5秒后自动移除
        setTimeout(() => {
            if (errorDiv.parentNode) {
                errorDiv.parentNode.removeChild(errorDiv);
            }
        }, 5000);
    }

    /**
     * 触发启动完成事件
     */
    triggerStartupComplete() {
        // 可以在这里添加启动完成后的逻辑
        console.log('Main: System startup complete, waiting for data connection...');
    }

    /**
     * 调试模式下的日志记录
     */
    logStateChange(data) {
        console.log('🔄 State Change:', data);
    }

    logDataLoaded(data) {
        console.log('📊 Data Loaded:', data);
    }

    logDataChanged(data) {
        console.log('🔄 Data Changed:', data);
    }

    /**
     * 获取应用实例
     * @returns {App|null} 应用实例
     */
    getApp() {
        return this.app;
    }

    /**
     * 检查是否已初始化
     * @returns {boolean} 是否已初始化
     */
    isAppInitialized() {
        return this.isInitialized;
    }

    /**
     * 销毁应用
     */
    destroy() {
        if (this.app) {
            this.app.destroy();
            this.app = null;
        }
        
        this.isInitialized = false;
        
        console.log('Main: Application destroyed');
    }
}

// 全局错误处理
window.addEventListener('error', (event) => {
    console.error('Global Error:', event.error);
});

window.addEventListener('unhandledrejection', (event) => {
    console.error('Unhandled Promise Rejection:', event.reason);
});

// 创建并启动应用
const main = new Main();

// 导出到全局作用域
window.main = main; 