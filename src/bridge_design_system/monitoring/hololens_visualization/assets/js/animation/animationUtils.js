/**
 * 动画工具函数 - 提供统一的动画计算和性能优化工具
 */
class AnimationUtils {
    constructor() {
        this.targetFPS = 60;
        this.frameInterval = 1000 / this.targetFPS;
        this.lastFrameTime = 0;
        this.frameCount = 0;
        this.fpsStats = {
            current: 0,
            average: 0,
            min: Infinity,
            max: 0
        };
    }

    /**
     * 计算呼吸动画值
     * @param {number} currentTime 当前时间
     * @param {number} period 周期
     * @param {number} amplitude 幅度
     * @param {number} phaseOffset 相位偏移
     * @returns {number} 呼吸值
     */
    static breathingValue(currentTime, period, amplitude, phaseOffset = 0) {
        const time = currentTime + phaseOffset;
        return Math.sin((time / period) * 2 * Math.PI) * amplitude;
    }

    /**
     * 计算半径
     * @param {number} value 数值 (0-100)
     * @param {number} minRadius 最小半径
     * @param {number} maxRadius 最大半径
     * @returns {number} 计算后的半径
     */
    static calculateRadius(value, minRadius, maxRadius) {
        const clampedValue = AnimationUtils.clamp(value, 0, 100);
        return minRadius + (clampedValue / 100) * (maxRadius - minRadius);
    }

    /**
     * 线性插值
     * @param {number} start 起始值
     * @param {number} end 结束值
     * @param {number} progress 进度 (0-1)
     * @returns {number} 插值结果
     */
    static lerp(start, end, progress) {
        return start + (end - start) * progress;
    }

    /**
     * 缓动函数 - 缓出三次方
     * @param {number} t 时间进度 (0-1)
     * @returns {number} 缓动后的进度
     */
    static easeOutCubic(t) {
        return 1 - Math.pow(1 - t, 3);
    }

    /**
     * 缓动函数 - 缓出二次方
     * @param {number} t 时间进度 (0-1)
     * @returns {number} 缓动后的进度
     */
    static easeOutQuad(t) {
        return t * (2 - t);
    }

    /**
     * 缓动函数 - 缓入缓出
     * @param {number} t 时间进度 (0-1)
     * @returns {number} 缓动后的进度
     */
    static easeInOut(t) {
        return t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t;
    }

    /**
     * 计算透明度
     * @param {number} value 数值 (0-100)
     * @param {number} minOpacity 最小透明度 (默认0.2)
     * @returns {number} 透明度值
     */
    static calculateOpacity(value, minOpacity = 0.2) {
        const clampedValue = AnimationUtils.clamp(value, 0, 100);
        return Math.max(minOpacity, clampedValue / 100);
    }

    /**
     * 生成随机整数
     * @param {number} min 最小值
     * @param {number} max 最大值
     * @returns {number} 随机整数
     */
    static randomInt(min, max) {
        return Math.floor(Math.random() * (max - min + 1)) + min;
    }

    /**
     * 生成随机浮点数
     * @param {number} min 最小值
     * @param {number} max 最大值
     * @returns {number} 随机浮点数
     */
    static randomFloat(min, max) {
        return Math.random() * (max - min) + min;
    }

    /**
     * 限制数值范围
     * @param {number} value 数值
     * @param {number} min 最小值
     * @param {number} max 最大值
     * @returns {number} 限制后的数值
     */
    static clamp(value, min, max) {
        return Math.min(Math.max(value, min), max);
    }

    /**
     * 计算两点之间的距离
     * @param {number} x1 第一个点的X坐标
     * @param {number} y1 第一个点的Y坐标
     * @param {number} x2 第二个点的X坐标
     * @param {number} y2 第二个点的Y坐标
     * @returns {number} 距离
     */
    static distance(x1, y1, x2, y2) {
        const dx = x2 - x1;
        const dy = y2 - y1;
        return Math.sqrt(dx * dx + dy * dy);
    }

    /**
     * 计算角度
     * @param {number} x1 第一个点的X坐标
     * @param {number} y1 第一个点的Y坐标
     * @param {number} x2 第二个点的X坐标
     * @param {number} y2 第二个点的Y坐标
     * @returns {number} 角度（弧度）
     */
    static angle(x1, y1, x2, y2) {
        return Math.atan2(y2 - y1, x2 - x1);
    }

    /**
     * 更新FPS统计
     * @param {number} currentTime 当前时间
     */
    updateFPSStats(currentTime) {
        this.frameCount++;
        
        if (currentTime - this.lastFrameTime >= 1000) {
            this.fpsStats.current = this.frameCount;
            this.fpsStats.average = (this.fpsStats.average + this.fpsStats.current) / 2;
            this.fpsStats.min = Math.min(this.fpsStats.min, this.fpsStats.current);
            this.fpsStats.max = Math.max(this.fpsStats.max, this.fpsStats.current);
            
            this.frameCount = 0;
            this.lastFrameTime = currentTime;
        }
    }

    /**
     * 获取FPS统计信息
     * @returns {Object} FPS统计
     */
    getFPSStats() {
        return { ...this.fpsStats };
    }

    /**
     * 检查是否需要跳过帧
     * @param {number} currentTime 当前时间
     * @returns {boolean} 是否跳过帧
     */
    shouldSkipFrame(currentTime) {
        return currentTime - this.lastFrameTime < this.frameInterval;
    }

    /**
     * 设置目标FPS
     * @param {number} fps 目标帧率
     */
    setTargetFPS(fps) {
        this.targetFPS = fps;
        this.frameInterval = 1000 / this.targetFPS;
    }

    /**
     * 创建动画循环
     * @param {Function} callback 回调函数
     * @param {number} targetFPS 目标帧率
     * @returns {Function} 停止函数
     */
    createAnimationLoop(callback, targetFPS = 60) {
        this.setTargetFPS(targetFPS);
        let animationId = null;
        
        const animate = (currentTime) => {
            this.updateFPSStats(currentTime);
            
            if (!this.shouldSkipFrame(currentTime)) {
                callback(currentTime);
            }
            
            animationId = requestAnimationFrame(animate);
        };
        
        animationId = requestAnimationFrame(animate);
        
        // 返回停止函数
        return () => {
            if (animationId) {
                cancelAnimationFrame(animationId);
                animationId = null;
            }
        };
    }

    /**
     * 创建缓动动画
     * @param {Object} config 配置对象
     * @returns {Function} 动画函数
     */
    static createEasingAnimation(config) {
        const {
            startValue,
            endValue,
            duration,
            easing = AnimationUtils.easeOutCubic,
            onUpdate,
            onComplete
        } = config;
        
        const startTime = performance.now();
        
        return (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            const easedProgress = easing(progress);
            
            const currentValue = AnimationUtils.lerp(startValue, endValue, easedProgress);
            
            if (onUpdate) {
                onUpdate(currentValue, easedProgress);
            }
            
            if (progress >= 1 && onComplete) {
                onComplete();
            }
            
            return progress < 1;
        };
    }

    /**
     * 创建脉冲动画
     * @param {Object} config 配置对象
     * @returns {Function} 动画函数
     */
    static createPulseAnimation(config) {
        const {
            baseValue,
            amplitude,
            frequency,
            onUpdate
        } = config;
        
        return (currentTime) => {
            const pulseValue = baseValue + Math.sin(currentTime * frequency) * amplitude;
            
            if (onUpdate) {
                onUpdate(pulseValue);
            }
            
            return true; // 持续动画
        };
    }

    /**
     * 性能监控
     */
    static performanceMonitor = {
        startTime: 0,
        endTime: 0,
        
        start() {
            this.startTime = performance.now();
        },
        
        end() {
            this.endTime = performance.now();
            return this.endTime - this.startTime;
        },
        
        measure(callback) {
            this.start();
            const result = callback();
            const duration = this.end();
            return { result, duration };
        }
    };

    /**
     * 内存使用监控
     * @returns {Object} 内存使用信息
     */
    static getMemoryUsage() {
        if (performance.memory) {
            return {
                used: performance.memory.usedJSHeapSize,
                total: performance.memory.totalJSHeapSize,
                limit: performance.memory.jsHeapSizeLimit
            };
        }
        return null;
    }

    /**
     * 防抖函数
     * @param {Function} func 函数
     * @param {number} delay 延迟时间
     * @returns {Function} 防抖后的函数
     */
    static debounce(func, delay) {
        let timeoutId;
        return function (...args) {
            clearTimeout(timeoutId);
            timeoutId = setTimeout(() => func.apply(this, args), delay);
        };
    }

    /**
     * 节流函数
     * @param {Function} func 函数
     * @param {number} limit 限制时间
     * @returns {Function} 节流后的函数
     */
    static throttle(func, limit) {
        let inThrottle;
        return function (...args) {
            if (!inThrottle) {
                func.apply(this, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }
}

// 全局注册
window.AnimationUtils = AnimationUtils; 