/**
 * 物理碰撞检测器 - 检测圆圈边缘碰撞并处理弹开效果
 */
class CollisionDetector {
    constructor() {
        this.collisionThreshold = 5; // 碰撞检测阈值
        this.pushForce = 0.1; // 推力系数
        this.visualEffectDuration = 1000; // 视觉效果持续时间
    }

    /**
     * 检测所有圆圈的碰撞
     * @param {Object} circles 圆圈对象集合
     */
    detectCollisions(circles) {
        const circleArray = Object.values(circles);
        
        for (let i = 0; i < circleArray.length; i++) {
            for (let j = i + 1; j < circleArray.length; j++) {
                const circle1 = circleArray[i];
                const circle2 = circleArray[j];
                
                if (this.isColliding(circle1, circle2)) {
                    this.handleCollision(circle1, circle2);
                }
            }
        }
    }

    /**
     * 检查两个圆圈是否碰撞
     * @param {Object} circle1 第一个圆圈
     * @param {Object} circle2 第二个圆圈
     * @returns {boolean} 是否碰撞
     */
    isColliding(circle1, circle2) {
        const distance = this.calculateDistance(circle1, circle2);
        const minDistance = circle1.currentRadius + circle2.currentRadius + this.collisionThreshold;
        
        return distance < minDistance;
    }

    /**
     * 计算两个圆圈之间的距离
     * @param {Object} circle1 第一个圆圈
     * @param {Object} circle2 第二个圆圈
     * @returns {number} 距离
     */
    calculateDistance(circle1, circle2) {
        const dx = circle1.position.x - circle2.position.x;
        const dy = circle1.position.y - circle2.position.y;
        return Math.sqrt(dx * dx + dy * dy);
    }

    /**
     * 处理碰撞
     * @param {Object} circle1 第一个圆圈
     * @param {Object} circle2 第二个圆圈
     */
    handleCollision(circle1, circle2) {
        const distance = this.calculateDistance(circle1, circle2);
        const minDistance = circle1.currentRadius + circle2.currentRadius + this.collisionThreshold;
        const overlap = minDistance - distance;
        
        if (overlap > 0) {
            // 计算推力
            const pushForce = overlap * this.pushForce;
            
            // 计算推力方向
            const angle = Math.atan2(circle2.position.y - circle1.position.y, circle2.position.x - circle1.position.x);
            
            // 应用推力到位置（轻微调整）
            const pushX = Math.cos(angle) * pushForce;
            const pushY = Math.sin(angle) * pushForce;
            
            // 更新圆圈位置
            this.applyPositionAdjustment(circle1, -pushX, -pushY);
            this.applyPositionAdjustment(circle2, pushX, pushY);
            
            // 触发碰撞视觉效果
            this.triggerCollisionEffect(circle1, circle2);
            
            // 触发碰撞事件
            this.triggerCollisionEvent(circle1, circle2, distance, pushForce);
        }
    }

    /**
     * 应用位置调整
     * @param {Object} circle 圆圈对象
     * @param {number} deltaX X方向调整
     * @param {number} deltaY Y方向调整
     */
    applyPositionAdjustment(circle, deltaX, deltaY) {
        // 更新位置
        circle.position.x += deltaX;
        circle.position.y += deltaY;
        
        // 更新SVG元素位置
        if (circle.element) {
            circle.element.setAttribute('cx', circle.position.x);
            circle.element.setAttribute('cy', circle.position.y);
        }
        
        // 更新对应的标签位置
        const labelId = `label-${circle.id}`;
        const labelElement = document.getElementById(labelId);
        if (labelElement) {
            labelElement.setAttribute('x', circle.position.x);
            labelElement.setAttribute('y', circle.position.y);
        }
    }

    /**
     * 触发碰撞视觉效果
     * @param {Object} circle1 第一个圆圈
     * @param {Object} circle2 第二个圆圈
     */
    triggerCollisionEffect(circle1, circle2) {
        // 为碰撞的圆圈添加视觉强调效果
        if (circle1.element) {
            circle1.element.classList.add('collision-effect');
        }
        if (circle2.element) {
            circle2.element.classList.add('collision-effect');
        }
        
        // 移除视觉效果
        setTimeout(() => {
            if (circle1.element) {
                circle1.element.classList.remove('collision-effect');
            }
            if (circle2.element) {
                circle2.element.classList.remove('collision-effect');
            }
        }, this.visualEffectDuration);
    }

    /**
     * 触发碰撞事件
     * @param {Object} circle1 第一个圆圈
     * @param {Object} circle2 第二个圆圈
     * @param {number} distance 距离
     * @param {number} pushForce 推力
     */
    triggerCollisionEvent(circle1, circle2, distance, pushForce) {
        const event = new CustomEvent('collisionDetected', {
            detail: {
                circle1: {
                    id: circle1.id,
                    position: { x: circle1.position.x, y: circle1.position.y },
                    radius: circle1.currentRadius
                },
                circle2: {
                    id: circle2.id,
                    position: { x: circle2.position.x, y: circle2.position.y },
                    radius: circle2.currentRadius
                },
                distance: distance,
                pushForce: pushForce,
                timestamp: Date.now()
            }
        });
        
        document.dispatchEvent(event);
    }

    /**
     * 设置碰撞检测参数
     * @param {Object} config 配置对象
     */
    setConfig(config) {
        if (config.collisionThreshold !== undefined) {
            this.collisionThreshold = config.collisionThreshold;
        }
        if (config.pushForce !== undefined) {
            this.pushForce = config.pushForce;
        }
        if (config.visualEffectDuration !== undefined) {
            this.visualEffectDuration = config.visualEffectDuration;
        }
    }

    /**
     * 获取碰撞检测统计信息
     * @returns {Object} 统计信息
     */
    getStats() {
        return {
            collisionThreshold: this.collisionThreshold,
            pushForce: this.pushForce,
            visualEffectDuration: this.visualEffectDuration
        };
    }
}

// 全局注册
window.CollisionDetector = CollisionDetector; 