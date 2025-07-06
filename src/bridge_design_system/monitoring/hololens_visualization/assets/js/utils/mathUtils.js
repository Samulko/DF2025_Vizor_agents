/**
 * 数学工具类 - 提供各种数学计算和动画算法
 */
class MathUtils {
    /**
     * 生成指定范围内的随机整数
     * @param {number} min 最小值
     * @param {number} max 最大值
     * @returns {number} 随机整数
     */
    static randomInt(min, max) {
        return Math.floor(Math.random() * (max - min + 1)) + min;
    }

    /**
     * 生成指定范围内的随机浮点数
     * @param {number} min 最小值
     * @param {number} max 最大值
     * @returns {number} 随机浮点数
     */
    static randomFloat(min, max) {
        return Math.random() * (max - min) + min;
    }

    /**
     * 线性插值
     * @param {number} start 起始值
     * @param {number} end 结束值
     * @param {number} t 插值因子 (0-1)
     * @returns {number} 插值结果
     */
    static lerp(start, end, t) {
        return start + (end - start) * t;
    }

    /**
     * 限制数值在指定范围内
     * @param {number} value 输入值
     * @param {number} min 最小值
     * @param {number} max 最大值
     * @returns {number} 限制后的值
     */
    static clamp(value, min, max) {
        return Math.min(Math.max(value, min), max);
    }

    /**
     * 将值从源范围映射到目标范围
     * @param {number} value 输入值
     * @param {number} sourceMin 源范围最小值
     * @param {number} sourceMax 源范围最大值
     * @param {number} targetMin 目标范围最小值
     * @param {number} targetMax 目标范围最大值
     * @returns {number} 映射后的值
     */
    static map(value, sourceMin, sourceMax, targetMin, targetMax) {
        return targetMin + (targetMax - targetMin) * (value - sourceMin) / (sourceMax - sourceMin);
    }

    /**
     * 缓动函数 - 弹性缓出
     * @param {number} t 时间因子 (0-1)
     * @returns {number} 缓动后的值
     */
    static easeOutElastic(t) {
        const p = 0.3;
        return Math.pow(2, -10 * t) * Math.sin((t - p / 4) * (2 * Math.PI) / p) + 1;
    }

    /**
     * 缓动函数 - 二次缓出
     * @param {number} t 时间因子 (0-1)
     * @returns {number} 缓动后的值
     */
    static easeOutQuad(t) {
        return t * (2 - t);
    }

    /**
     * 缓动函数 - 三次缓出
     * @param {number} t 时间因子 (0-1)
     * @returns {number} 缓动后的值
     */
    static easeOutCubic(t) {
        return 1 - Math.pow(1 - t, 3);
    }

    /**
     * 计算呼吸动画的当前值
     * @param {number} time 当前时间 (毫秒)
     * @param {number} period 周期 (毫秒)
     * @param {number} amplitude 振幅
     * @param {number} phaseOffset 相位偏移 (毫秒)
     * @returns {number} 呼吸值
     */
    static breathingValue(time, period, amplitude, phaseOffset = 0) {
        const normalizedTime = (time + phaseOffset) % period;
        const phase = (normalizedTime / period) * 2 * Math.PI;
        return Math.sin(phase) * amplitude;
    }

    /**
     * 计算圆圈半径
     * @param {number} value 数值 (0-100)
     * @param {number} minRadius 最小半径
     * @param {number} maxRadius 最大半径
     * @returns {number} 计算后的半径
     */
    static calculateRadius(value, minRadius, maxRadius) {
        return this.map(value, 0, 100, minRadius, maxRadius);
    }

    /**
     * 计算数字宽度（用于自适应圆圈大小）
     * @param {string} text 文本内容
     * @param {string} font 字体样式
     * @returns {number} 文本宽度
     */
    static getTextWidth(text, font = '18px Arial') {
        const canvas = document.createElement('canvas');
        const context = canvas.getContext('2d');
        context.font = font;
        return context.measureText(text).width;
    }

    /**
     * 计算自适应圆圈半径
     * @param {number} value 数值
     * @param {string} text 显示文本
     * @param {number} minRadius 最小半径
     * @param {number} maxRadius 最大半径
     * @returns {number} 自适应半径
     */
    static calculateAdaptiveRadius(value, text, minRadius, maxRadius) {
        const textWidth = this.getTextWidth(text);
        const baseRadius = this.calculateRadius(value, minRadius, maxRadius);
        const textRadius = textWidth / 2 + 2; // 文本半径 + 2px边距
        return Math.max(baseRadius, textRadius);
    }

    /**
     * 计算两点间距离
     * @param {number} x1 点1的x坐标
     * @param {number} y1 点1的y坐标
     * @param {number} x2 点2的x坐标
     * @param {number} y2 点2的y坐标
     * @returns {number} 距离
     */
    static distance(x1, y1, x2, y2) {
        return Math.sqrt(Math.pow(x2 - x1, 2) + Math.pow(y2 - y1, 2));
    }

    /**
     * 检查两个圆圈是否重叠
     * @param {number} x1 圆圈1的x坐标
     * @param {number} y1 圆圈1的y坐标
     * @param {number} r1 圆圈1的半径
     * @param {number} x2 圆圈2的x坐标
     * @param {number} y2 圆圈2的y坐标
     * @param {number} r2 圆圈2的半径
     * @returns {boolean} 是否重叠
     */
    static circlesOverlap(x1, y1, r1, x2, y2, r2) {
        const dist = this.distance(x1, y1, x2, y2);
        return dist < (r1 + r2);
    }

    /**
     * 计算重叠区域面积
     * @param {number} x1 圆圈1的x坐标
     * @param {number} y1 圆圈1的y坐标
     * @param {number} r1 圆圈1的半径
     * @param {number} x2 圆圈2的x坐标
     * @param {number} y2 圆圈2的y坐标
     * @param {number} r2 圆圈2的半径
     * @returns {number} 重叠面积
     */
    static overlapArea(x1, y1, r1, x2, y2, r2) {
        const dist = this.distance(x1, y1, x2, y2);
        
        if (dist >= r1 + r2) return 0; // 不重叠
        if (dist <= Math.abs(r1 - r2)) {
            // 一个圆完全包含另一个圆
            return Math.PI * Math.min(r1, r2) * Math.min(r1, r2);
        }
        
        // 部分重叠
        const a = r1 * r1;
        const b = r2 * r2;
        const x = (a - b + dist * dist) / (2 * dist);
        const y = Math.sqrt(a - x * x);
        
        return a * Math.acos(x / r1) + b * Math.acos((dist - x) / r2) - dist * y;
    }

    /**
     * 生成随机颜色变化
     * @param {string} baseColor 基础颜色
     * @param {number} variation 变化幅度 (0-1)
     * @returns {string} 变化后的颜色
     */
    static randomColorVariation(baseColor, variation = 0.1) {
        // 这里可以扩展为更复杂的颜色变化算法
        return baseColor;
    }
}

// 导出到全局作用域
window.MathUtils = MathUtils;