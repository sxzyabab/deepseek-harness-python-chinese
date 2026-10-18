'Host 配置与浏览器文档预览共用的缓存上限'

__all__=['配置','Config']

最大安全整数=9007199254740991
定时器上限=2147483647
办公默认={
    'maxCachedEntries':8,
    'maxCachedBytes':64*1024*1024,
    'maxPending':8,
    'maxReaders':32,
}
表格默认={
    'maxBytes':16*1024*1024,
    'maxCells':250000,
    'timeoutMs':15000,
}
办公上限={
    'maxCachedEntries':最大安全整数,
    'maxCachedBytes':最大安全整数,
    'maxPending':最大安全整数,
    'maxReaders':最大安全整数,
}
表格上限={
    'maxBytes':最大安全整数,
    'maxCells':最大安全整数,
    'timeoutMs':定时器上限,
}

def 取自然数(块,键,默认,上限):
    '缺省用默认。给出的值必须是 1 到上限之间的整数'
    if not isinstance(块,dict) or 键 not in 块 or 块[键] is None:
        return 默认
    值=块[键]
    if isinstance(值,bool) or not isinstance(值,int) or 值<1 or 值>上限:
        raise ValueError('document preview config '+键)
    return 值

def 配置(输入=None):
    '补齐 Office 与表格缓存上限。空对象得到全部默认。0 或越过上限则抛错'
    if 输入 is None:
        输入={}
    if not isinstance(输入,dict):
        raise TypeError('document preview config')
    办公=输入['office'] if 'office' in 输入 and 输入['office'] is not None else {}
    表格=输入['excel'] if 'excel' in 输入 and 输入['excel'] is not None else {}
    if not isinstance(办公,dict) or not isinstance(表格,dict):
        raise TypeError('document preview config')
    return {
        'office':{键:取自然数(办公,键,办公默认[键],办公上限[键]) for 键 in 办公默认},
        'excel':{键:取自然数(表格,键,表格默认[键],表格上限[键]) for 键 in 表格默认},
    }

Config=配置
