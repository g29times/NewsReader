/**
 * 通用缓存管理类
 * 支持：
 * 1. 多种类型数据缓存（文本、二进制、Base64等）
 * 2. TTL过期控制
 * 3. 容量限制和LRU清理
 * 4. 数据压缩（仅文本）
 */
class CacheManager {
    /**
     * 设置缓存并更新统计信息
     * @param {string} key - 缓存键
     * @param {*} data - 缓存数据
     * @param {Object} options - 可选配置
     * @param {Function} updateStatsCallback - 更新统计信息的回调函数
     * @returns {boolean} 是否成功
     */
    setAndUpdateStats(key, data, options = {}, updateStatsCallback) {
        const success = this.set(key, data, options);
        if (success && typeof updateStatsCallback === 'function') {
            updateStatsCallback(this.getStats());
        }
        return success;
    }

    /**
     * 删除缓存并更新统计信息
     * @param {string} key - 缓存键
     * @param {Function} updateStatsCallback - 更新统计信息的回调函数
     * @returns {boolean} 是否成功
     */
    deleteAndUpdateStats(key, updateStatsCallback) {
        const success = this.delete(key);
        if (success && typeof updateStatsCallback === 'function') {
            updateStatsCallback(this.getStats());
        }
        return success;
    }

    /**
     * 清空缓存并更新统计信息
     * @param {Function} updateStatsCallback - 更新统计信息的回调函数
     */
    clearAndUpdateStats(updateStatsCallback) {
        this.clear();
        if (typeof updateStatsCallback === 'function') {
            updateStatsCallback(this.getStats());
        }
    }

    /**
     * 初始化缓存管理器
     * @param {Object} options - 配置选项
     * @param {number} options.ttl - 默认过期时间（秒）
     * @param {number} options.maxSize - 最大缓存大小（字节）
     * @param {string} options.storageKey - localStorage的键名
     * @param {boolean} options.compression - 是否启用压缩
     */
    constructor(options = {}) {
        try {
            this.ttl = options.ttl || 3600; // 默认1小时
            this.maxSize = options.maxSize || 104857600; // 默认100MB
            this.storageKey = options.storageKey || 'cache_storage';
            this.compression = options.compression || false;
            this._cache = {};
            this.currentSize = 0;

            // 从localStorage恢复缓存
            this._loadFromStorage();
            // 清理过期项
            this._cleanExpired();
        } catch (error) {
            console.warn('CacheManager initialization failed:', error);
            // 初始化失败时使用默认值
            this._cache = {};
            this.currentSize = 0;
        }
    }

    /**
     * 从localStorage加载缓存
     * @private
     */
    _loadFromStorage() {
        try {
            const stored = localStorage.getItem(this.storageKey);
            if (stored) {
                const parsed = JSON.parse(stored);
                // 验证缓存数据的格式
                if (typeof parsed === 'object' && parsed !== null) {
                    this._cache = parsed;
                    this._updateSize();
                    console.log('Cache loaded from storage');
                } else {
                    throw new Error('Invalid cache data format');
                }
            }
        } catch (error) {
            console.warn('Failed to load cache from storage:', error);
            // 加载失败时重置缓存
            this._cache = {};
            this.currentSize = 0;
            // 清理可能损坏的存储
            localStorage.removeItem(this.storageKey);
        }
    }

    /**
     * 保存缓存到localStorage
     * @private
     */
    _saveToStorage() {
        try {
            const serialized = JSON.stringify(this._cache);
            localStorage.setItem(this.storageKey, serialized);
        } catch (error) {
            console.warn('Failed to save cache to storage:', error);
            // 存储失败时尝试清理过期项后重试
            try {
                this._cleanExpired();
                localStorage.setItem(this.storageKey, JSON.stringify(this._cache));
            } catch (retryError) {
                console.warn('Failed to save cache to storage:', retryError);
                // 如果还是失败，清除localStorage中的缓存
                localStorage.removeItem(this.storageKey);
            }
        }
    }

    /**
     * 计算数据大小（字节）
     * @param {*} data - 要计算大小的数据
     * @returns {number} 数据大小（字节）
     */
    _getDataSize(data) {
        if (typeof data === 'string') {
            return new Blob([data]).size;
        } else if (data instanceof Blob) {
            return data.size;
        } else {
            return new Blob([JSON.stringify(data)]).size;
        }
    }

    /**
     * 压缩文本数据
     * @private
     */
    _compress(text) {
        if (!this.compression || typeof text !== 'string') {
            return text;
        }
        try {
            // 使用 Uint8Array 来处理二进制数据
            const textBytes = new TextEncoder().encode(text);
            const compressed = pako.deflate(textBytes);
            const base64 = btoa(String.fromCharCode.apply(null, compressed));
            return base64;
        } catch (error) {
            console.warn('Compression failed:', error);
            return text;
        }
    }

    /**
     * 解压缩文本数据
     * @private
     */
    _decompress(base64) {
        if (!this.compression || typeof base64 !== 'string') {
            return base64;
        }
        try {
            // 转换Base64为二进制数组
            const binaryString = atob(base64);
            const bytes = new Uint8Array(binaryString.length);
            for (let i = 0; i < binaryString.length; i++) {
                bytes[i] = binaryString.charCodeAt(i);
            }
            // 解压缩
            const decompressed = pako.inflate(bytes, { to: 'string' });
            return decompressed;
        } catch (error) {
            console.warn('Decompression failed:', error);
            return base64;
        }
    }

    /**
     * 清理过期缓存
     */
    _cleanExpired() {
        const now = Date.now();
        Object.keys(this._cache).forEach(key => {
            if (this._cache[key].expiry < now) {
                delete this._cache[key];
            }
        });
    }

    /**
     * 更新当前缓存大小
     */
    _updateSize() {
        this.currentSize = this._getDataSize(JSON.stringify(this._cache));
    }

    /**
     * 执行LRU清理
     * @param {number} requiredSize - 需要的空间大小
     */
    _performLRUCleanup(requiredSize) {
        const entries = Object.entries(this._cache)
            .sort(([, a], [, b]) => a.lastAccess - b.lastAccess);

        while (this.currentSize + requiredSize > this.maxSize && entries.length) {
            const [key] = entries.shift();
            delete this._cache[key];
            this._updateSize();
        }
    }

    /**
     * 设置缓存
     * @param {string} key - 缓存键
     * @param {*} data - 缓存数据
     * @param {Object} options - 可选配置
     */
    set(key, data, options = {}) {
        try {
            const ttl = options.ttl || this.ttl;
            const type = options.type || 'json';
            const dataSize = this._getDataSize(data);

            // 检查并清理空间
            this._cleanExpired();
            if (this.currentSize + dataSize > this.maxSize) {
                this._performLRUCleanup(dataSize);
            }

            // 如果清理后仍然超出限制，则不缓存
            if (this.currentSize + dataSize > this.maxSize) {
                console.warn('Cache item too large:', key);
                return false;
            }

            let processedData = data;
            if (type === 'blob') {
                // 转换Blob为Base64
                return new Promise((resolve) => {
                    const reader = new FileReader();
                    reader.onloadend = () => {
                        try {
                            this._cache[key] = {
                                data: reader.result,
                                type,
                                expiry: Date.now() + (ttl * 1000),
                                lastAccess: Date.now()
                            };
                            this._updateSize();
                            this._saveToStorage();
                            console.log('Cache Blob successfully:', key);
                            resolve(true);
                        } catch (error) {
                            console.warn('Failed to cache blob:', error);
                            resolve(false);
                        }
                    };
                    reader.onerror = () => {
                        console.warn('Failed to read blob:', reader.error);
                        resolve(false);
                    };
                    reader.readAsDataURL(data);
                });
            }
            try {
                if (type === 'json') {
                    // 先转换为JSON字符串
                    processedData = JSON.stringify(data);
                    // 如果启用了压缩，再进行压缩
                    if (this.compression) {
                        processedData = this._compress(processedData);
                    }
                } else if (type === 'text' && this.compression) {
                    processedData = this._compress(data);
                }
            } catch (error) {
                console.warn('Failed to process data for caching:', error);
                return false;
            }
            console.log('Cache data successfully:', key);
            this._cache[key] = {
                data: processedData,
                type,
                expiry: Date.now() + (ttl * 1000),
                lastAccess: Date.now()
            };

            this._updateSize();
            this._saveToStorage();
            return true;
        } catch (error) {
            console.warn('Cache set operation failed:', error);
            return false;
        }
    }

    /**
     * 获取缓存
     * @param {string} key - 缓存键
     */
    get(key) {
        try {
            const cached = this._cache[key];
            if (!cached || cached.expiry < Date.now()) {
                return null;
            }

            cached.lastAccess = Date.now();
            this._saveToStorage();

            let data = cached.data;
            console.log('Retrieved cached data for:', key, 'type:', cached.type);

            if (cached.type === 'blob') {
                try {
                    const [metadata, base64] = data.split(',');
                    const mimeType = metadata.split(':')[1].split(';')[0];
                    const binary = atob(base64);
                    const array = new Uint8Array(binary.length);
                    for (let i = 0; i < binary.length; i++) {
                        array[i] = binary.charCodeAt(i);
                    }
                    return new Blob([array], { type: mimeType });
                } catch (error) {
                    console.warn('Failed to process blob data:', error);
                    return null;
                }
            }

            try {
                if (cached.type === 'json') {
                    // 如果启用了压缩，先解压缩
                    if (this.compression) {
                        data = this._decompress(data);
                    }
                    // 然后解析JSON
                    data = JSON.parse(data);
                } else if (cached.type === 'text' && this.compression) {
                    data = this._decompress(data);
                }
            } catch (error) {
                console.warn('Failed to process cached data:', error);
                return null;
            }

            return data;
        } catch (error) {
            console.warn('Cache get operation failed:', error);
            return null;
        }
    }

    /**
     * 删除指定键的缓存项
     * @param {string} key - 要删除的缓存键
     */
    delete(key) {
        try {
            if (this._cache[key]) {
                delete this._cache[key];
                this._updateSize();
                this._saveToStorage();
                console.log('Cache deleted:', key);
                return true;
            }
            console.log('Cache not found:', key);
            return false;
        } catch (error) {
            console.warn('Cache delete operation failed:', error);
            return false;
        }
    }

    /**
     * 清空所有缓存
     */
    clear() {
        try {
            // 清空内存缓存
            this._cache = {};
            this.currentSize = 0;
            
            // 清空localStorage
            localStorage.removeItem(this.storageKey);
            console.log('Cache cleared successfully');
        } catch (error) {
            console.warn('Cache clear operation failed:', error);
            // 即使失败也要尝试清空内存缓存
            this._cache = {};
            this.currentSize = 0;
        }
    }

    /**
     * 获取缓存统计信息
     * @returns {Object} 统计信息
     */
    getStats() {
        try {
            return {
                itemCount: Object.keys(this._cache).length,
                currentSize: this.currentSize,
                maxSize: this.maxSize,
                usagePercentage: (this.currentSize / this.maxSize) * 100
            };
        } catch (error) {
            console.warn('Failed to get cache stats:', error);
            return {
                itemCount: 0,
                currentSize: 0,
                maxSize: this.maxSize,
                usagePercentage: 0
            };
        }
    }
}
