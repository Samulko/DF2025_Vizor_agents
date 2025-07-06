 /**
 * Color utility class - handles state-related color switching and effects
 */
class ColorUtils {
    /**
     * Color configuration
     */
    static COLORS = {
        WEIGHT: '#FF3030',
        STORAGE: '#FFCC00',
        COMPLEXITY: '#3366FF',
        WHITE: '#FFFFFF',
        WARNING: '#FF0000',
        TRANSPARENT: 'transparent'
    };

    /**
     * State color mapping
     */
    static STATE_COLORS = {
        initializing: {
            weight: '#FF3030',
            storage: '#FFCC00',
            complexity: '#3366FF'
        },
        locked: {
            weight: '#FF3030',
            storage: '#FFCC00',
            complexity: '#3366FF'
        },
        stable: {
            weight: '#FF3030',
            storage: '#FFCC00',
            complexity: '#3366FF'
        },
        updating: {
            weight: '#FF3030',
            storage: '#FFCC00',
            complexity: '#3366FF'
        },
        error: {
            weight: '#FF0000',
            storage: '#FF0000',
            complexity: '#FF0000'
        }
    };

    /**
     * Get the color corresponding to the state
     * @param {string} circleType Circle type (weight/storage/complexity)
     * @param {string} state State
     * @returns {string} Color value
     */
    static getStateColor(circleType, state) {
        return this.STATE_COLORS[state]?.[circleType] || this.COLORS.WEIGHT;
    }

    /**
     * Convert hexadecimal color to RGB object
     * @param {string} hex Hexadecimal color
     * @returns {Object} RGB object {r, g, b}
     */
    static hexToRgb(hex) {
        const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
        return result ? {
            r: parseInt(result[1], 16),
            g: parseInt(result[2], 16),
            b: parseInt(result[3], 16)
        } : null;
    }

    /**
     * Convert RGB object to hexadecimal color
     * @param {number} r Red value (0-255)
     * @param {number} g Green value (0-255)
     * @param {number} b Blue value (0-255)
     * @returns {string} Hexadecimal color
     */
    static rgbToHex(r, g, b) {
        return "#" + ((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1);
    }

    /**
     * Adjust color brightness
     * @param {string} hex Hexadecimal color
     * @param {number} factor Brightness factor (0-2, 1 is original color)
     * @returns {string} Adjusted color
     */
    static adjustBrightness(hex, factor) {
        const rgb = this.hexToRgb(hex);
        if (!rgb) return hex;

        const r = Math.min(255, Math.max(0, Math.round(rgb.r * factor)));
        const g = Math.min(255, Math.max(0, Math.round(rgb.g * factor)));
        const b = Math.min(255, Math.max(0, Math.round(rgb.b * factor)));

        return this.rgbToHex(r, g, b);
    }

    /**
     * Adjust color saturation
     * @param {string} hex Hexadecimal color
     * @param {number} factor Saturation factor (0-2, 1 is original color)
     * @returns {string} Adjusted color
     */
    static adjustSaturation(hex, factor) {
        const rgb = this.hexToRgb(hex);
        if (!rgb) return hex;

        // Convert to HSL
        const hsl = this.rgbToHsl(rgb.r, rgb.g, rgb.b);
        hsl.s = Math.min(1, Math.max(0, hsl.s * factor));
        
        // Convert back to RGB
        const newRgb = this.hslToRgb(hsl.h, hsl.s, hsl.l);
        return this.rgbToHex(newRgb.r, newRgb.g, newRgb.b);
    }

    /**
     * RGB to HSL
     * @param {number} r Red value (0-255)
     * @param {number} g Green value (0-255)
     * @param {number} b Blue value (0-255)
     * @returns {Object} HSL object {h, s, l}
     */
    static rgbToHsl(r, g, b) {
        r /= 255;
        g /= 255;
        b /= 255;

        const max = Math.max(r, g, b);
        const min = Math.min(r, g, b);
        let h, s, l = (max + min) / 2;

        if (max === min) {
            h = s = 0;
        } else {
            const d = max - min;
            s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
            switch (max) {
                case r: h = (g - b) / d + (g < b ? 6 : 0); break;
                case g: h = (b - r) / d + 2; break;
                case b: h = (r - g) / d + 4; break;
            }
            h /= 6;
        }

        return { h, s, l };
    }

    /**
     * HSL to RGB
     * @param {number} h Hue (0-1)
     * @param {number} s Saturation (0-1)
     * @param {number} l Lightness (0-1)
     * @returns {Object} RGB object {r, g, b}
     */
    static hslToRgb(h, s, l) {
        let r, g, b;

        if (s === 0) {
            r = g = b = l;
        } else {
            const hue2rgb = (p, q, t) => {
                if (t < 0) t += 1;
                if (t > 1) t -= 1;
                if (t < 1/6) return p + (q - p) * 6 * t;
                if (t < 1/2) return q;
                if (t < 2/3) return p + (q - p) * (2/3 - t) * 6;
                return p;
            };

            const q = l < 0.5 ? l * (1 + s) : l + s - l * s;
            const p = 2 * l - q;
            r = hue2rgb(p, q, h + 1/3);
            g = hue2rgb(p, q, h);
            b = hue2rgb(p, q, h - 1/3);
        }

        return {
            r: Math.round(r * 255),
            g: Math.round(g * 255),
            b: Math.round(b * 255)
        };
    }

    /**
     * Create a glowing effect color
     * @param {string} baseColor Base color
     * @param {number} intensity Glow intensity (0-1)
     * @returns {string} Glow color
     */
    static createGlowColor(baseColor, intensity = 0.8) {
        return this.adjustBrightness(baseColor, 1 + intensity * 0.5);
    }

    /**
     * Create a warning color
     * @param {string} baseColor Base color
     * @param {number} warningLevel Warning level (0-1)
     * @returns {string} Warning color
     */
    static createWarningColor(baseColor, warningLevel = 1) {
        const rgb = this.hexToRgb(baseColor);
        if (!rgb) return this.COLORS.WARNING;

        // Mix red warning color
        const warningRgb = this.hexToRgb(this.COLORS.WARNING);
        const r = Math.round(rgb.r * (1 - warningLevel) + warningRgb.r * warningLevel);
        const g = Math.round(rgb.g * (1 - warningLevel) + warningRgb.g * warningLevel);
        const b = Math.round(rgb.b * (1 - warningLevel) + warningRgb.b * warningLevel);

        return this.rgbToHex(r, g, b);
    }

    /**
     * Create a flash effect color
     * @param {string} baseColor Base color
     * @returns {string} Flash color
     */
    static createFlashColor(baseColor) {
        return this.adjustBrightness(baseColor, 1.5);
    }

    /**
     * Get gradient stop color
     * @param {string} baseColor Base color
     * @param {number} stopOffset Stop position (0-1)
     * @param {number} opacity Opacity (0-1)
     * @returns {string} Gradient stop color
     */
    static getGradientStopColor(baseColor, stopOffset, opacity = 1) {
        const rgb = this.hexToRgb(baseColor);
        if (!rgb) return baseColor;

        // Adjust brightness based on stop position
        const brightness = 1 - stopOffset * 0.5;
        const adjustedColor = this.adjustBrightness(baseColor, brightness);
        
        if (opacity === 1) return adjustedColor;
        
        // Add opacity
        const adjustedRgb = this.hexToRgb(adjustedColor);
        return `rgba(${adjustedRgb.r}, ${adjustedRgb.g}, ${adjustedRgb.b}, ${opacity})`;
    }

    /**
     * Check if color is dark
     * @param {string} hex Hexadecimal color
     * @returns {boolean} Whether it is dark
     */
    static isDarkColor(hex) {
        const rgb = this.hexToRgb(hex);
        if (!rgb) return false;
        
        // Calculate brightness
        const brightness = (rgb.r * 299 + rgb.g * 587 + rgb.b * 114) / 1000;
        return brightness < 128;
    }

    /**
     * Get contrast color (for text)
     * @param {string} backgroundColor Background color
     * @returns {string} Contrast color
     */
    static getContrastColor(backgroundColor) {
        return this.isDarkColor(backgroundColor) ? this.COLORS.WHITE : '#000000';
    }

    /**
     * Create semi-transparent color
     * @param {string} hex Hexadecimal color
     * @param {number} alpha Opacity (0-1)
     * @returns {string} Semi-transparent color
     */
    static createTransparentColor(hex, alpha) {
        const rgb = this.hexToRgb(hex);
        if (!rgb) return hex;
        
        return `rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, ${alpha})`;
    }
}

// Export to global scope
window.ColorUtils = ColorUtils;