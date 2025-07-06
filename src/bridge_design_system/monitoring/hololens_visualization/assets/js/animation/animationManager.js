/**
 * 统一动画管理器 - 管理所有圆圈和标签的动画逻辑
 * 合并了CircleElement、LabelDisplay和ThreeCircles的功能
 */
class AnimationManager {
    constructor(renderEngine, dataManager) {
        this.renderEngine = renderEngine;
        this.dataManager = dataManager;
        this.circles = {};
        this.labels = {};
        this.config = null;
        
        // 统一动画状态
        this.animationState = 'random'; // 'random' | 'stable' | 'transitioning'
        this.lastDataUpdate = null;
        this.updateCount = 0;
        
        // 动画时间管理
        this.animationFrame = null;
        this.lastUpdateTime = 0;
        this.lastRandomUpdate = 0;
        this.randomAnimationInterval = 500; // 500ms间隔，每0.5秒变2次
        
        // 物理碰撞检测
        this.collisionDetector = new CollisionDetector();
        
        // 事件监听器
        this.eventListeners = {
            'animationStarted': [],
            'animationStopped': [],
            'dataUpdated': [],
            'collisionDetected': []
        };
        
        this.init();
    }

    /**
     * 初始化动画管理器
     */
    async init() {
        try {
            console.log('AnimationManager: 开始初始化...');
            
            // 使用渲染引擎的配置
            this.config = this.renderEngine.config;
            
            // 创建圆圈和标签组件
            this.createComponents();
            
            // 绑定数据管理器事件
            this.bindDataEvents();
            
            // 启动动画循环
            this.startAnimation();
            
            console.log('AnimationManager: 初始化成功');
            
        } catch (error) {
            console.error('AnimationManager: 初始化失败', error);
        }
    }

    /**
     * 创建圆圈和标签组件
     */
    createComponents() {
        const circleIds = ['weight', 'storage', 'complexity'];
        
        circleIds.forEach(circleId => {
            const config = this.config.circles[circleId];
            
            // 创建圆圈组件
            this.circles[circleId] = {
                id: circleId,
                config: config,
                currentValue: config.defaultValue || 0,
                targetValue: config.defaultValue || 0,
                currentRadius: config.minRadius,
                targetRadius: config.minRadius,
                position: config.position,
                color: config.color,
                element: document.getElementById(`circle-${circleId}`),
                isLiveData: false
            };
            
            // 创建标签组件
            this.labels[circleId] = {
                id: circleId,
                config: config,
                currentValue: config.defaultValue || 0,
                displayValue: config.defaultValue || 0,
                element: document.getElementById(`label-${circleId}`)
            };
        });
    }

    /**
     * 绑定数据管理器事件
     */
    bindDataEvents() {
        this.dataManager.addEventListener('dataLoaded', (data) => {
            this.handleDataLoaded(data);
        });
        
        this.dataManager.addEventListener('dataChanged', (data) => {
            this.handleDataChanged(data);
        });
        
        this.dataManager.addEventListener('dataError', (error) => {
            this.handleDataError(error);
        });
    }

    /**
     * 开始动画循环
     */
    startAnimation() {
        const animate = (currentTime) => {
            this.animationFrame = requestAnimationFrame(animate);
            
            if (currentTime - this.lastUpdateTime >= 16) { // 约60fps
                this.updateAnimation(currentTime);
                this.lastUpdateTime = currentTime;
            }
        };
        
        animate(0);
        this.triggerEvent('animationStarted', { type: 'main' });
    }

    /**
     * 更新动画
     * @param {number} currentTime 当前时间
     */
    updateAnimation(currentTime) {
        switch (this.animationState) {
            case 'random':
                this.updateRandomAnimation(currentTime);
                break;
            case 'stable':
                this.updateStableAnimation(currentTime);
                break;
            case 'transitioning':
                this.updateTransitionAnimation(currentTime);
                break;
        }
        
        // 检测碰撞
        this.collisionDetector.detectCollisions(this.circles);
    }

    /**
     * 更新随机动画 - 数字和圆圈同步变化
     * @param {number} currentTime 当前时间
     */
    updateRandomAnimation(currentTime) {
        if (currentTime - this.lastRandomUpdate >= this.randomAnimationInterval) {
            this.updateAllRandomValues();
            this.lastRandomUpdate = currentTime;
        }
    }

    /**
     * 更新所有随机数值
     */
    updateAllRandomValues() {
        Object.keys(this.circles).forEach(circleId => {
                    const randomValue = AnimationUtils.randomInt(0, 100);
        const randomRadius = AnimationUtils.calculateRadius(
            randomValue, 
            this.circles[circleId].config.minRadius, 
            this.circles[circleId].config.maxRadius
        );
            
            // 更新圆圈
            this.updateCircle(circleId, randomValue, randomRadius);
            
            // 更新标签
            this.updateLabel(circleId, randomValue);
        });
    }

    /**
     * 更新稳定状态动画 - 只有圆圈微浮动，数字静止
     * @param {number} currentTime 当前时间
     */
    updateStableAnimation(currentTime) {
        Object.keys(this.circles).forEach(circleId => {
            const circle = this.circles[circleId];
            
            // 微浮动动画
            const breathingConfig = {
                amplitude: 2, // 很小的幅度
                period: 4000, // 4秒周期
                phaseOffset: this.getBreathingPhaseOffset(circleId)
            };
            
            const breathingValue = AnimationUtils.breathingValue(
                currentTime,
                breathingConfig.period,
                breathingConfig.amplitude,
                breathingConfig.phaseOffset
            );
            
            const breathingRadius = circle.targetRadius + breathingValue;
            this.updateCircleRadius(circleId, breathingRadius);
        });
    }

    /**
     * 更新过渡动画
     * @param {number} currentTime 当前时间
     */
    updateTransitionAnimation(currentTime) {
        // 过渡动画逻辑
        // 这里可以实现从当前值到目标值的平滑过渡
    }

    /**
     * 处理数据加载成功
     * @param {Object} data 数据对象
     */
    handleDataLoaded(data) {
        this.switchToStableState(data);
    }

    /**
     * 处理数据变化
     * @param {Object} data 新数据
     */
    handleDataChanged(data) {
        this.updateCount++;
        this.lastDataUpdate = Date.now();
        
        // 切换到稳定状态：数字停止变化，圆圈开始微浮动
        this.switchToStableState(data);
        
        // 更新状态指示器
        this.updateStatusIndicator();
        
        // 触发强调效果
        this.triggerEmphasisEffect();
        
        this.triggerEvent('dataUpdated', {
            data: data,
            updateCount: this.updateCount
        });
    }

    /**
     * 处理数据错误
     * @param {Error} error 错误对象
     */
    handleDataError(error) {
        console.warn('AnimationManager: 数据错误，继续使用当前状态', error);
        // 不切换到错误状态，保持当前状态
    }

    /**
     * 切换到稳定状态
     * @param {Object} data 数据对象
     */
    switchToStableState(data) {
        this.animationState = 'stable';
        
        const valueKeys = ['Self-Weight', 'Storage', 'Complexity'];
        const circleIds = Object.keys(this.circles);
        
        circleIds.forEach((circleId, index) => {
            const value = data.values ? data.values[valueKeys[index]] : data[valueKeys[index]];
            
            if (value !== undefined) {
                // 立即更新数字到最终值
                this.updateLabel(circleId, value);
                
                // 更新圆圈目标值
                            const targetRadius = AnimationUtils.calculateRadius(
                value, 
                this.circles[circleId].config.minRadius, 
                this.circles[circleId].config.maxRadius
            );
                
                this.circles[circleId].targetValue = value;
                this.circles[circleId].targetRadius = targetRadius;
                this.circles[circleId].isLiveData = true;
                
                // 立即更新圆圈到目标大小
                this.updateCircle(circleId, value, targetRadius);
            }
        });
        
        console.log('AnimationManager: 切换到稳定状态');
    }

    /**
     * 更新圆圈
     * @param {string} circleId 圆圈ID
     * @param {number} value 数值
     * @param {number} radius 半径
     */
    updateCircle(circleId, value, radius) {
        const circle = this.circles[circleId];
        if (!circle || !circle.element) return;
        
        // 更新半径
        this.updateCircleRadius(circleId, radius);
        
        // 更新透明度（数值越低，透明度越高，最低20%）
        const opacity = Math.max(0.2, value / 100);
        circle.element.style.opacity = opacity;
        
        // 更新数据属性
        circle.element.dataset.value = value;
        circle.currentValue = value;
        circle.currentRadius = radius;
    }

    /**
     * 更新圆圈半径
     * @param {string} circleId 圆圈ID
     * @param {number} radius 半径
     */
    updateCircleRadius(circleId, radius) {
        const circle = this.circles[circleId];
        if (!circle || !circle.element) return;
        
        circle.element.setAttribute('r', radius);
        circle.currentRadius = radius;
    }

    /**
     * 更新标签
     * @param {string} circleId 圆圈ID
     * @param {number} value 数值
     */
    updateLabel(circleId, value) {
        const label = this.labels[circleId];
        if (!label || !label.element) return;
        
        const displayValue = Math.round(value);
        label.element.textContent = displayValue;
        label.element.dataset.value = displayValue;
        label.currentValue = value;
        label.displayValue = displayValue;
    }

    /**
     * 更新状态指示器
     */
    updateStatusIndicator() {
        const statusElement = document.getElementById('status-text');
        if (statusElement) {
            statusElement.textContent = `Updated ${this.updateCount} times`;
        }
    }

    /**
     * 触发强调效果
     */
    triggerEmphasisEffect() {
        Object.keys(this.circles).forEach(circleId => {
            const circle = this.circles[circleId];
            const label = this.labels[circleId];
            
            if (circle.element) {
                circle.element.classList.add('emphasis-effect');
            }
            if (label.element) {
                label.element.classList.add('emphasis-effect');
            }
        });
        
        // 3秒后移除强调效果
        setTimeout(() => {
            Object.keys(this.circles).forEach(circleId => {
                const circle = this.circles[circleId];
                const label = this.labels[circleId];
                
                if (circle.element) {
                    circle.element.classList.remove('emphasis-effect');
                }
                if (label.element) {
                    label.element.classList.remove('emphasis-effect');
                }
            });
        }, 3000);
    }

    /**
     * 获取呼吸动画相位偏移
     * @param {string} circleId 圆圈ID
     * @returns {number} 相位偏移
     */
    getBreathingPhaseOffset(circleId) {
        const offsets = {
            'weight': 0,
            'storage': 1200,
            'complexity': 2400
        };
        return offsets[circleId] || 0;
    }

    /**
     * 获取圆圈信息
     * @param {string} circleId 圆圈ID
     * @returns {Object|null} 圆圈信息
     */
    getCircle(circleId) {
        return this.circles[circleId] || null;
    }

    /**
     * 获取标签信息
     * @param {string} circleId 圆圈ID
     * @returns {Object|null} 标签信息
     */
    getLabel(circleId) {
        return this.labels[circleId] || null;
    }

    /**
     * 获取当前状态
     * @returns {string} 当前状态
     */
    getCurrentState() {
        return this.animationState;
    }

    /**
     * 获取更新计数
     * @returns {number} 更新计数
     */
    getUpdateCount() {
        return this.updateCount;
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
                    console.error(`AnimationManager: Error executing event callback [${event}]`, error);
                }
            });
        }
    }

    /**
     * 销毁动画管理器
     */
    destroy() {
        if (this.animationFrame) {
            cancelAnimationFrame(this.animationFrame);
            this.animationFrame = null;
        }
        
        // 清理事件监听器
        this.eventListeners = {};
        
        console.log('AnimationManager: 已销毁');
    }
}

// 全局注册
window.AnimationManager = AnimationManager; 