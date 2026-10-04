__all__=[#仅中文公开名
    '检查器错误','Client源远程错误','Client运行时远程错误','检查器查询远程错误',
    '客户端源目录错误','客户端运行时执行错误','宿主cdp桥不可用错误',
    '运行时调用帧','运行时栈跟踪','运行时异常详情','宿主cdp桥原因',
]#公开面结束

class 检查器错误(Exception):#检查器错误基类
    '检查器包内错误基类'
    def __init__(自身,消息):#构造
        '记下英文诊断'
        super().__init__(消息)#基类
        自身.消息=消息#诊断

class Client源远程错误(Exception):#Client源远程错误
    'Client 源目录有意返回的错误'
    def __init__(自身,码,信息):#构造
        '保存错误码'
        super().__init__(信息)#基类
        自身.code=码#错误码

class Client运行时远程错误(Exception):#Client Runtime远程错误
    'Client Runtime 执行器有意返回的错误'
    def __init__(自身,码,信息):#构造
        '保存错误码'
        super().__init__(信息)#基类
        自身.code=码#错误码

class 检查器查询远程错误(Exception):#远程查询错误
    'Worker 查询处理器故意返回的失败'
    def __init__(自身,code,message):#错误码与信息
        '保存错误码与信息'
        super().__init__(message)#设置消息
        自身.code=code#错误码

class 客户端源目录错误(Exception):#Client源目录错误
    'Client 源传输序列化的有意错误'
    def __init__(自身,code,message):#绑定错误码
        '保存码与信息'
        super().__init__(message)#基类
        自身.code=code#错误码
        自身.message=message#信息

class 客户端运行时执行错误(Exception):#Client运行时执行错误
    '经类型化 Client Runtime 错误结果返回的失败'
    def __init__(自身,code,message):#绑定错误码
        '保存错误码与信息'
        super().__init__(message)#基类消息
        自身.code=code#错误码
        自身.message=message#信息

宿主cdp桥原因='Host Runtime is attached directly from the Inspector Worker'#拒绝原因

class 宿主cdp桥不可用错误(Exception):#Host CDP桥不可用
    'Host Runtime 使用 Worker 侧 Node inspector session，而非 source RPC'
    def __init__(自身,操作):#构造
        '保存操作名'
        super().__init__(f'inspector protocol: {操作} cannot use the Host source bridge; {宿主cdp桥原因}')#消息

class 运行时调用帧:#调用帧
    'Runtime 异常栈中的一个源位置'
    def __init__(自身,functionName,url,lineNumber,columnNumber,scriptKey=None):#构造
        '保存调用帧字段'
        自身.functionName=functionName#函数名
        自身.scriptKey=scriptKey#脚本键
        自身.url=url#源URL
        自身.lineNumber=lineNumber#行号
        自身.columnNumber=columnNumber#列号

class 运行时栈跟踪:#栈跟踪
    '与 Debugger 脚本 id 无关的 JavaScript 栈信息'
    def __init__(自身,callFrames,description=None,parent=None):#构造
        '保存栈跟踪字段'
        自身.description=description#描述
        自身.callFrames=tuple(callFrames)#调用帧
        自身.parent=parent#父栈

class 运行时异常详情:#异常详情
    '执行一条 Runtime 命令时产生的 JavaScript 异常'
    def __init__(自身,text,lineNumber,columnNumber,url=None,stackTrace=None,exception=None):#构造
        '保存异常详情字段'
        自身.text=text#异常文本
        自身.lineNumber=lineNumber#行号
        自身.columnNumber=columnNumber#列号
        自身.url=url#源URL
        自身.stackTrace=stackTrace#栈跟踪
        自身.exception=exception#异常对象
