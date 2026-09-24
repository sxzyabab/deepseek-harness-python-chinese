"""Host 配置与浏览器文档预览共用的缓存上限。"""

__all__=['默认配置','配置模式']#仅中文公开名

默认配置={
    'office':{
        'maxCachedEntries':8,
        'maxCachedBytes':64*1024*1024,
        'maxPending':8,
        'maxReaders':32,
    },
    'excel':{
        'maxBytes':16*1024*1024,
        'maxCells':250000,
        'timeoutMs':15000,
    },
}

配置模式=默认配置
