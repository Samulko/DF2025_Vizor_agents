 /**
 * Render engine - responsible for creating, updating, and managing SVG graphics
 */
class RenderEngine {
    constructor() {
        this.svg = null;
        this.circlesGroup = null;
        this.labelsGroup = null;
        this.config = null;
        this.animationFrame = null;
        this.lastTime = 0;
        
        // 新增：数据状态管理
        this.circleElements = {}; // 存储CircleElement实例
        this.hasLiveData = false; // 是否有真实数据
        this.dataCheckInterval = null; // 数据检查定时器
        
        this.init();
    }

    /**
     * Initialize render engine
     */
    init() {
        this.svg = document.getElementById('circles-canvas');
        this.circlesGroup = document.getElementById('circles-group');
        this.labelsGroup = document.getElementById('labels-group');
        
        if (!this.svg || !this.circlesGroup || !this.labelsGroup) {
            console.error('RenderEngine: 无法找到必要的SVG元素');
            return;
        }

        // Load configuration
        this.loadConfig();
        
        // Start render loop
        this.startRenderLoop();
        
        // 新增：启动数据监听
        this.startDataMonitoring();
        
        // 新增：监听窗口大小变化
        this.startWindowResizeListener();
    }

    /**
     * Wait for configuration to be loaded
     */
    async waitForConfig() {
        if (this.config) {
            return this.config;
        }
        
        // Wait for config to be loaded
        while (!this.config) {
            await new Promise(resolve => setTimeout(resolve, 10));
        }
        
        return this.config;
    }

    /**
     * Load configuration file
     */
    async loadConfig() {
        try {
            const response = await fetch('assets/config/circles.json');
            this.config = await response.json();
        } catch (error) {
            console.error('RenderEngine: 加载配置文件失败', error);
            // Use default configuration
            this.config = this.getDefaultConfig();
        }
    }

    /**
     * Get default configuration
     */
    getDefaultConfig() {
        const windowWidth = window.innerWidth;
        const windowHeight = window.innerHeight;
        
        // 圆直径更大 - 最大60%，最小40%
        const windowSize = Math.min(windowWidth, windowHeight);
        const maxDiameter = windowSize * 0.6; // 60% of window size
        const minDiameter = windowSize * 0.4; // 40% of window size
        
        const minRadius = minDiameter / 2; // 半径 = 直径 / 2
        const maxRadius = maxDiameter / 2;
        
        // 响应式位置计算 - 增加间距以适应更大的圆
        const centerX = windowWidth * 0.5;
        const centerY = windowHeight * 0.5;
        const spacing = Math.max(maxRadius * 1.5, windowSize * 0.7); // 更大间距
        
        return {
            circles: {
                weight: {
                    name: "Self-Weight",
                    color: "#FF3030",
                    gradientId: "weightGradient",
                    position: {x: centerX - spacing, y: centerY - spacing * 0.5},
                    minRadius: minRadius,
                    maxRadius: maxRadius,
                    defaultValue: 20
                },
                storage: {
                    name: "Storage",
                    color: "#FFCC00",
                    gradientId: "storageGradient",
                    position: {x: centerX + spacing, y: centerY - spacing * 0.5},
                    minRadius: minRadius,
                    maxRadius: maxRadius,
                    defaultValue: 60
                },
                complexity: {
                    name: "Complexity",
                    color: "#3366FF",
                    gradientId: "complexityGradient",
                    position: {x: centerX, y: centerY + spacing * 0.8},
                    minRadius: minRadius,
                    maxRadius: maxRadius,
                    defaultValue: 20
                }
            },
            animations: {
                breathing: {
                    amplitude: 3,
                    period: 3500,
                    phaseOffset: [0, 1200, 2400]
                },
                transition: {
                    duration: 650,
                    easing: "ease-out"
                }
            }
        };
    }

    /**
     * Start render loop
     */
    startRenderLoop() {
        const render = (currentTime) => {
            this.animationFrame = requestAnimationFrame(render);
            
            if (currentTime - this.lastTime >= 16) { // Approx 60fps
                this.update(currentTime);
                this.lastTime = currentTime;
            }
        };
        
        render(0);
    }

    /**
     * Stop render loop
     */
    stopRenderLoop() {
        if (this.animationFrame) {
            cancelAnimationFrame(this.animationFrame);
            this.animationFrame = null;
        }
    }

    /**
     * Update rendering
     * @param {number} currentTime Current time
     */
    update(currentTime) {
        // Update all circles and labels
        this.updateCircles(currentTime);
        this.updateLabels(currentTime);
    }

    /**
     * Create circle element
     * @param {string} id Circle ID
     * @param {Object} config Circle configuration
     * @returns {SVGCircleElement} Circle element
     */
    createCircle(id, config) {
        try {
            const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
            circle.id = `circle-${id}`;
            circle.setAttribute('cx', config.position.x);
            circle.setAttribute('cy', config.position.y);
            circle.setAttribute('r', config.minRadius);
            circle.setAttribute('fill', `url(#${config.gradientId})`);
            circle.setAttribute('stroke', ColorUtils.createTransparentColor(config.color, 0.3));
            circle.setAttribute('stroke-width', '2');
            circle.classList.add('circle');
            circle.dataset.state = 'initializing';
            circle.dataset.value = config.defaultValue || 0;
            
            this.circlesGroup.appendChild(circle);
            return circle;
        } catch (error) {
            console.error(`RenderEngine: 创建圆圈 ${id} 失败`, error);
            return null;
        }
    }

    /**
     * Create label element
     * @param {string} id Label ID
     * @param {Object} config Label configuration
     * @returns {SVGTextElement} Label element
     */
    createLabel(id, config) {
        try {
            const label = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            label.id = `label-${id}`;
            label.setAttribute('x', config.position.x);
            label.setAttribute('y', config.position.y);
            label.setAttribute('text-anchor', 'middle');
            label.setAttribute('dominant-baseline', 'central');
            
            // 调整字体大小以适应更大的圆 - 字体大小约为圆半径的30%
            const fontSize = Math.max(80, config.maxRadius * 0.3); // 字体大小为圆半径的30%，最小80px
            label.setAttribute('font-size', fontSize);
            
            label.setAttribute('font-weight', '900'); // 更粗 (之前是800)
            label.setAttribute('font-family', 'Montserrat, sans-serif');
            label.setAttribute('fill', '#FFFFFF');
            label.textContent = config.defaultValue || 0;
            label.classList.add('label');
            label.dataset.state = 'initializing';
            label.dataset.value = config.defaultValue || 0;
            
            this.labelsGroup.appendChild(label);
            return label;
        } catch (error) {
            console.error(`RenderEngine: 创建标签 ${id} 失败`, error);
            return null;
        }
    }

    /**
     * Update circles
     * @param {number} currentTime Current time
     */
    updateCircles(currentTime) {
        if (!this.config) return;

        Object.keys(this.config.circles).forEach((circleId, index) => {
            const circle = document.getElementById(`circle-${circleId}`);
            if (!circle) return;

            const config = this.config.circles[circleId];
            const state = circle.dataset.state || 'initializing';
            
            // Update circle based on state
            this.updateCircleByState(circle, config, state, currentTime, index);
        });
    }

    /**
     * Update circle based on state
     * @param {SVGCircleElement} circle Circle element
     * @param {Object} config Circle configuration
     * @param {string} state State
     * @param {number} currentTime Current time
     * @param {number} index Circle index
     */
    updateCircleByState(circle, config, state, currentTime, index) {
        const breathingConfig = this.config.animations.breathing;
        const phaseOffset = breathingConfig.phaseOffset[index] || 0;

        switch (state) {
            case 'initializing':
                // Random change
                const randomValue = MathUtils.randomInt(0, 100);
                const randomRadius = MathUtils.calculateRadius(randomValue, config.minRadius, config.maxRadius);
                circle.setAttribute('r', randomRadius);
                circle.classList.remove('circle-state-stable', 'circle-state-locked', 'circle-state-updating', 'circle-state-error');
                circle.classList.add('circle-state-initializing');
                break;

            case 'locked':
            case 'updating':
                // Transition animation
                const targetValue = parseInt(circle.dataset.value) || config.defaultValue;
                const targetRadius = MathUtils.calculateRadius(targetValue, config.minRadius, config.maxRadius);
                const currentRadius = parseFloat(circle.getAttribute('r'));
                
                if (Math.abs(currentRadius - targetRadius) > 0.1) {
                    const transitionDuration = this.config.animations.transition.duration;
                    const progress = Math.min(1, (currentTime % transitionDuration) / transitionDuration);
                    const newRadius = MathUtils.lerp(currentRadius, targetRadius, MathUtils.easeOutCubic(progress));
                    circle.setAttribute('r', newRadius);
                }
                
                circle.classList.remove('circle-state-initializing', 'circle-state-stable', 'circle-state-error');
                circle.classList.add(`circle-state-${state}`);
                break;

            case 'stable':
                // Breathing animation
                const baseValue = parseInt(circle.dataset.value) || config.defaultValue;
                const baseRadius = MathUtils.calculateRadius(baseValue, config.minRadius, config.maxRadius);
                const breathingValue = MathUtils.breathingValue(
                    currentTime, 
                    breathingConfig.period, 
                    breathingConfig.amplitude, 
                    phaseOffset
                );
                const breathingRadius = baseRadius + breathingValue;
                circle.setAttribute('r', breathingRadius);
                
                circle.classList.remove('circle-state-initializing', 'circle-state-locked', 'circle-state-updating', 'circle-state-error');
                circle.classList.add('circle-state-stable');
                break;

            case 'error':
                // Error state - 保持原有颜色，使用随机动画
                const errorValue = MathUtils.randomInt(0, 100);
                const errorRadius = MathUtils.calculateRadius(errorValue, config.minRadius, config.maxRadius);
                circle.setAttribute('r', errorRadius);
                
                circle.classList.remove('circle-state-initializing', 'circle-state-locked', 'circle-state-updating', 'circle-state-stable');
                circle.classList.add('circle-state-error');
                break;
        }
    }

    /**
     * Update labels
     * @param {number} currentTime Current time
     */
    updateLabels(currentTime) {
        if (!this.config) return;

        Object.keys(this.config.circles).forEach((circleId) => {
            const label = document.getElementById(`label-${circleId}`);
            if (!label) return;

            const config = this.config.circles[circleId];
            const state = label.dataset.state || 'initializing';
            
            // Update label based on state
            this.updateLabelByState(label, config, state, currentTime);
        });
    }

    /**
     * Update label based on state
     * @param {SVGTextElement} label Label element
     * @param {Object} config Label configuration
     * @param {string} state State
     * @param {number} currentTime Current time
     */
    updateLabelByState(label, config, state, currentTime) {
        switch (state) {
            case 'initializing':
                // Random number
                const randomValue = MathUtils.randomInt(0, 100);
                label.textContent = randomValue;
                label.classList.remove('label-state-stable', 'label-state-locked', 'label-state-updating', 'label-state-error');
                label.classList.add('label-state-initializing');
                break;

            case 'locked':
                // Locked number
                const lockedValue = parseInt(label.dataset.value) || config.defaultValue;
                label.textContent = lockedValue;
                label.classList.remove('label-state-initializing', 'label-state-stable', 'label-state-updating', 'label-state-error');
                label.classList.add('label-state-locked');
                break;

            case 'stable':
                // Stable display
                const stableValue = parseInt(label.dataset.value) || config.defaultValue;
                label.textContent = stableValue;
                label.classList.remove('label-state-initializing', 'label-state-locked', 'label-state-updating', 'label-state-error');
                label.classList.add('label-state-stable');
                break;

            case 'updating':
                // Updating number
                const updatingValue = parseInt(label.dataset.value) || config.defaultValue;
                label.textContent = updatingValue;
                label.classList.remove('label-state-initializing', 'label-state-locked', 'label-state-stable', 'label-state-error');
                label.classList.add('label-state-updating');
                break;

            case 'error':
                // Error state - 使用随机数字，保持动画
                const errorValue = MathUtils.randomInt(0, 100);
                label.textContent = errorValue;
                label.classList.remove('label-state-initializing', 'label-state-locked', 'label-state-updating', 'label-state-stable');
                label.classList.add('label-state-error');
                break;
        }
    }

    /**
     * Set circle state
     * @param {string} circleId Circle ID
     * @param {string} state State
     * @param {number} value Value
     */
    setCircleState(circleId, state, value) {
        const circle = document.getElementById(`circle-${circleId}`);
        const label = document.getElementById(`label-${circleId}`);
        
        if (circle) {
            circle.dataset.state = state;
            circle.dataset.value = value;
        }
        
        if (label) {
            label.dataset.state = state;
            label.dataset.value = value;
        }
    }

    /**
     * Create all circles and labels
     */
    createAllElements() {
        if (!this.config) {
            console.error('RenderEngine: 配置未加载，无法创建元素');
            return;
        }

        console.log('RenderEngine: 开始创建所有SVG元素...');

        Object.keys(this.config.circles).forEach((circleId) => {
            const config = this.config.circles[circleId];
            console.log(`RenderEngine: 创建圆圈和标签 ${circleId}`);
            
            const circle = this.createCircle(circleId, config);
            const label = this.createLabel(circleId, config);
            
            if (circle && label) {
                console.log(`RenderEngine: 成功创建 ${circleId} 元素`);
                
                // 创建CircleElement实例并存储
                if (window.CircleElement) {
                    this.circleElements[circleId] = new CircleElement(circleId, config);
                    console.log(`RenderEngine: 创建CircleElement实例 ${circleId}`);
                } else {
                    console.warn('RenderEngine: CircleElement类未找到，无法创建实例');
                }
            } else {
                console.error(`RenderEngine: 创建 ${circleId} 元素失败`);
            }
        });

        console.log('RenderEngine: 所有SVG元素创建完成');
    }

    /**
     * Clear all elements
     */
    clearAllElements() {
        if (this.circlesGroup) {
            this.circlesGroup.innerHTML = '';
        }
        if (this.labelsGroup) {
            this.labelsGroup.innerHTML = '';
        }
    }

    /**
     * Destroy render engine
     */
    destroy() {
        // 停止数据监听
        if (this.dataCheckInterval) {
            clearInterval(this.dataCheckInterval);
            this.dataCheckInterval = null;
        }
        
        // 销毁所有CircleElement实例
        Object.keys(this.circleElements).forEach(circleId => {
            const circleElement = this.circleElements[circleId];
            if (circleElement && typeof circleElement.destroy === 'function') {
                circleElement.destroy();
            }
        });
        this.circleElements = {};
        
        this.stopRenderLoop();
        this.clearAllElements();
    }

    /**
     * 启动数据监听 - 检查design_profile.json的变化
     */
    startDataMonitoring() {
        console.log('RenderEngine: 启动数据监听...');
        
        // 每5秒检查一次design_profile.json
        this.dataCheckInterval = setInterval(() => {
            this.checkDesignProfileData();
        }, 5000);
        
        // 立即检查一次
        this.checkDesignProfileData();
    }

    /**
     * 检查design_profile.json数据
     */
    async checkDesignProfileData() {
        try {
            const response = await fetch('../design_profile.json');
            if (response.ok) {
                const data = await response.json();
                
                // 检查是否有有效数据
                const hasValidData = this.validateDesignProfileData(data);
                
                // 如果数据状态发生变化
                if (hasValidData !== this.hasLiveData) {
                    const previousState = this.hasLiveData;
                    this.hasLiveData = hasValidData;
                    
                    if (hasValidData) {
                        console.log('RenderEngine: 检测到数据变化，切换到有数据状态');
                        // 检测到数据变化，所有圆切换到stable状态
                        this.switchToDataMode();
                    } else {
                        console.log('RenderEngine: 数据消失，切换到无数据状态');
                        // 数据消失，所有圆切换到initializing状态
                        this.switchToNoDataMode();
                    }
                    
                    // 通知所有CircleElement切换动画模式
                    this.updateAllCircleElementsDataState(hasValidData);
                }
            } else {
                // 文件不存在或无法访问
                if (this.hasLiveData) {
                    this.hasLiveData = false;
                    console.log('RenderEngine: 数据文件不可访问，切换到无数据状态');
                    this.switchToNoDataMode();
                    this.updateAllCircleElementsDataState(false);
                }
            }
        } catch (error) {
            console.error('RenderEngine: 检查design_profile.json失败', error);
            // 错误时保持当前状态，不切换动画模式
        }
    }

    /**
     * 验证design_profile.json数据是否有效
     * @param {Object} data 数据对象
     * @returns {boolean} 是否有效
     */
    validateDesignProfileData(data) {
        // 检查是否有必要的字段
        if (!data || typeof data !== 'object') {
            return false;
        }
        
        // 检查是否有任何有效的数值字段
        const validFields = ['surface_area', 'storage_capacity', 'complexity_score'];
        return validFields.some(field => {
            const value = data[field];
            return typeof value === 'number' && !isNaN(value) && value >= 0;
        });
    }

    /**
     * 更新所有CircleElement的数据状态
     * @param {boolean} hasLiveData 是否有真实数据
     */
    updateAllCircleElementsDataState(hasLiveData) {
        Object.keys(this.circleElements).forEach(circleId => {
            const circleElement = this.circleElements[circleId];
            if (circleElement && typeof circleElement.setLiveData === 'function') {
                circleElement.setLiveData(hasLiveData);
            }
        });
    }

    /**
     * 切换到有数据模式
     */
    switchToDataMode() {
        Object.keys(this.config.circles).forEach(circleId => {
            const circle = document.getElementById(`circle-${circleId}`);
            const label = document.getElementById(`label-${circleId}`);
            
            if (circle && label) {
                // 切换到stable状态，数字停止变化
                this.setCircleState(circleId, 'stable', parseInt(circle.dataset.value) || this.config.circles[circleId].defaultValue);
            }
        });
    }

    /**
     * 切换到无数据模式
     */
    switchToNoDataMode() {
        Object.keys(this.config.circles).forEach(circleId => {
            const circle = document.getElementById(`circle-${circleId}`);
            const label = document.getElementById(`label-${circleId}`);
            
            if (circle && label) {
                // 切换到initializing状态，数字开始变化
                this.setCircleState(circleId, 'initializing', parseInt(circle.dataset.value) || this.config.circles[circleId].defaultValue);
            }
        });
    }

    /**
     * 启动窗口大小变化监听器
     */
    startWindowResizeListener() {
        let resizeTimeout;
        window.addEventListener('resize', () => {
            // 防抖处理
            clearTimeout(resizeTimeout);
            resizeTimeout = setTimeout(() => {
                console.log('RenderEngine: 窗口大小变化，重新计算配置');
                this.handleWindowResize();
            }, 300);
        });
    }

    /**
     * 处理窗口大小变化
     */
    handleWindowResize() {
        // 重新计算配置
        this.config = this.getDefaultConfig();
        
        // 更新现有圆的尺寸和位置
        this.updateCirclesForResize();
        
        // 更新现有标签的尺寸和位置
        this.updateLabelsForResize();
    }

    /**
     * 更新圆的尺寸和位置以适应窗口大小变化
     */
    updateCirclesForResize() {
        if (!this.config) return;
        
        Object.keys(this.config.circles).forEach(circleId => {
            const circle = document.getElementById(`circle-${circleId}`);
            const config = this.config.circles[circleId];
            
            if (circle && config) {
                // 更新位置
                circle.setAttribute('cx', config.position.x);
                circle.setAttribute('cy', config.position.y);
                
                // 更新半径（保持当前值的比例）
                const currentValue = parseInt(circle.dataset.value) || config.defaultValue;
                const newRadius = MathUtils.calculateRadius(currentValue, config.minRadius, config.maxRadius);
                circle.setAttribute('r', newRadius);
            }
        });
    }

    /**
     * 更新标签的尺寸和位置以适应窗口大小变化
     */
    updateLabelsForResize() {
        if (!this.config) return;
        
        Object.keys(this.config.circles).forEach(circleId => {
            const label = document.getElementById(`label-${circleId}`);
            const config = this.config.circles[circleId];
            
            if (label && config) {
                // 更新位置
                label.setAttribute('x', config.position.x);
                label.setAttribute('y', config.position.y);
                
                // 更新字体大小
                const fontSize = Math.max(80, config.maxRadius * 0.3);
                label.setAttribute('font-size', fontSize);
            }
        });
    }
}

// Export to global scope
window.RenderEngine = RenderEngine;