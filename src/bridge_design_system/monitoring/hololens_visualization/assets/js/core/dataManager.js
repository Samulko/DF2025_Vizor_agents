 /**
 * 数据管理器 - 负责JSON文件的读取、轮询和数据处理
 */
class DataManager {
    constructor() {
        this.dataPath = '../../design_profile.json';
        this.currentData = null;
        this.lastTimestamp = null;
        this.pollingInterval = null;
        this.isPolling = false;
        this.retryCount = 0;
        this.maxRetries = 3;
        this.retryDelay = 1000;
        
        this.eventListeners = {
            'dataLoaded': [],
            'dataChanged': [],
            'dataError': [],
            'connectionLost': [],
            'connectionRestored': []
        };
        
        this.init();
    }

    /**
     * 初始化数据管理器
     */
    init() {
        // 立即尝试首次读取
        this.loadData();
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
                    console.error(`DataManager: 事件回调执行错误 [${event}]`, error);
                }
            });
        }
    }

    /**
     * 加载数据文件
     * @returns {Promise<Object>} 数据对象
     */
    async loadData() {
        try {
            const response = await fetch(this.dataPath);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            // 验证数据格式
            if (!this.validateData(data)) {
                throw new Error('数据格式无效');
            }
            
            // 检查数据是否发生变化
            const hasChanged = this.hasDataChanged(data);
            
            // 更新当前数据
            this.currentData = data;
            this.lastTimestamp = data.timestamp;
            this.retryCount = 0;
            
            // 触发相应事件
            if (hasChanged) {
                this.triggerEvent('dataChanged', data);
            } else {
                this.triggerEvent('dataLoaded', data);
            }
            
            return data;
            
        } catch (error) {
            console.error('DataManager: 加载数据失败', error);
            this.handleError(error);
            throw error;
        }
    }

    /**
     * 验证数据格式
     * @param {Object} data 数据对象
     * @returns {boolean} 是否有效
     */
    validateData(data) {
        if (!data || typeof data !== 'object') {
            return false;
        }
        
        const requiredFields = ['Self-Weight', 'Storage', 'Complexity', 'timestamp'];
        for (const field of requiredFields) {
            if (!(field in data)) {
                return false;
            }
        }
        
        // 验证数值范围
        const numericFields = ['Self-Weight', 'Storage', 'Complexity'];
        for (const field of numericFields) {
            const value = data[field];
            if (typeof value !== 'number' || value < 0 || value > 100) {
                return false;
            }
        }
        
        // 验证时间戳
        if (typeof data.timestamp !== 'number' || data.timestamp <= 0) {
            return false;
        }
        
        return true;
    }

    /**
     * 检查数据是否发生变化
     * @param {Object} newData 新数据
     * @returns {boolean} 是否发生变化
     */
    hasDataChanged(newData) {
        if (!this.currentData) {
            return true; // 首次加载
        }
        
        // 检查时间戳
        if (newData.timestamp !== this.lastTimestamp) {
            return true;
        }
        
        // 检查数值
        const fields = ['Self-Weight', 'Storage', 'Complexity'];
        for (const field of fields) {
            if (newData[field] !== this.currentData[field]) {
                return true;
            }
        }
        
        return false;
    }

    /**
     * 处理错误
     * @param {Error} error 错误对象
     */
    handleError(error) {
        this.retryCount++;
        
        if (this.retryCount <= this.maxRetries) {
            // 重试
            console.log(`DataManager: Retrying data load (${this.retryCount}/${this.maxRetries})`);
            setTimeout(() => {
                this.loadData();
            }, this.retryDelay * this.retryCount);
        } else {
            // 达到最大重试次数
            console.error('DataManager: Reached maximum retries, stopping retries');
            this.triggerEvent('dataError', error);
            this.triggerEvent('connectionLost', error);
        }
    }

    /**
     * 开始轮询
     * @param {number} interval 轮询间隔（毫秒）
     */
    startPolling(interval = 500) {
        if (this.isPolling) {
            return;
        }
        
        this.isPolling = true;
        this.pollingInterval = setInterval(() => {
            this.loadData().catch(error => {
                // 轮询中的错误已经在loadData中处理
            });
        }, interval);
        
        console.log(`DataManager: Starting polling, interval ${interval}ms`);
    }

    /**
     * 停止轮询
     */
    stopPolling() {
        if (this.pollingInterval) {
            clearInterval(this.pollingInterval);
            this.pollingInterval = null;
        }
        this.isPolling = false;
        console.log('DataManager: Stopping polling');
    }

    /**
     * 获取当前数据
     * @returns {Object|null} 当前数据
     */
    getCurrentData() {
        return this.currentData;
    }

    /**
     * 获取指定字段的值
     * @param {string} field 字段名
     * @returns {number|null} 字段值
     */
    getValue(field) {
        if (this.currentData && this.currentData[field] !== undefined) {
            return this.currentData[field];
        }
        return null;
    }

    /**
     * 获取所有数值
     * @returns {Object} 数值对象
     */
    getValues() {
        if (!this.currentData) {
            return {
                'Self-Weight': 0,
                'Storage': 0,
                'Complexity': 0
            };
        }
        
        return {
            'Self-Weight': this.currentData['Self-Weight'],
            'Storage': this.currentData['Storage'],
            'Complexity': this.currentData['Complexity']
        };
    }

    /**
     * 检查连接状态
     * @returns {boolean} 是否连接正常
     */
    isConnected() {
        return this.currentData !== null && this.retryCount === 0;
    }

    /**
     * 重置连接状态
     */
    resetConnection() {
        this.retryCount = 0;
        this.triggerEvent('connectionRestored', null);
    }

    /**
     * 设置数据路径
     * @param {string} path 数据文件路径
     */
    setDataPath(path) {
        this.dataPath = path;
    }

    /**
     * 设置轮询间隔
     * @param {number} interval 轮询间隔（毫秒）
     */
    setPollingInterval(interval) {
        if (this.isPolling) {
            this.stopPolling();
            this.startPolling(interval);
        }
    }

    /**
     * 销毁数据管理器
     */
    destroy() {
        this.stopPolling();
        this.eventListeners = {};
        this.currentData = null;
    }
}

// 导出到全局作用域
window.DataManager = DataManager;