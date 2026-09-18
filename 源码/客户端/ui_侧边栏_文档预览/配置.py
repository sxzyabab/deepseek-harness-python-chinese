"""Host 配置与浏览器文档预览共用的缓存上限。"""

__all__=['默认配置','配置模式']#仅中文公开名

默认配置={#Office 缓存默认
    'office':{#Office
        'maxCachedEntries':8,#条数
        'maxCachedBytes':64*1024*1024,#字节
        'maxPending':8,#待办
        'maxReaders':32,#读者
    },
}#默认结束

配置模式=默认配置#部署上限模式别名
