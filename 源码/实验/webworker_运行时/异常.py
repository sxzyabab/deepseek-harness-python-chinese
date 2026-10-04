__all__=['运行时错误','中止错误','隧道逻辑流错误','地锁启动器错误']

class 运行时错误(Exception):
    'webworker 运行时包内错误基类'
    def __init__(自身,消息):
        '记下英文诊断'
        super().__init__(消息)
        自身.消息=消息

class 中止错误(Exception):
    '携带 Node 稳定错误码的取消错误；中止原因作异常属性，不挂在信号上'
    def __init__(自身,原因=None):
        '记下 AbortError 面与可选原因'
        super().__init__('The operation was aborted')
        自身.name='AbortError'
        自身.code='ABORT_ERR'
        自身.原因=原因

class 隧道逻辑流错误(Exception):#隧道逻辑流错误
    '跨独立打包的 Client 代码携带流语义的错误'

    def __init__(自身,失败,原因=None):#构造错误
        '按失败种类填充远程流失败标记'
        super().__init__(失败['message'] if 'message' in 失败 else '')#基类
        自身.name='TunnelLogicalStreamError'#错误名
        if 'kind' in 失败 and 失败['kind']=='remote':#远程失败
            自身.dshRemoteStreamFailure={'kind':'remote','code':失败['code'] if 'code' in 失败 else None,'details':失败['details'] if 'details' in 失败 else None}#远程标记
        else:#载体失败
            自身.dshRemoteStreamFailure={'kind':'carrier'}#载体标记
        if 原因 is not None:#带cause
            自身.__cause__=原因#cause

class 地锁启动器错误(Exception):#启动器错误
    '启动器自有失败；调用方以其消息加 `landlock-run:` 前缀打印'
