"""与界域无关的 Runtime 操作与结果。

对齐上游 `shared/cdp/operations.ts`。公开面仅中文名。
"""
__all__=[#仅中文公开名
    '运行时调用参数','运行时执行上下文','运行时求值请求',
    '运行时获取属性请求','运行时调用函数请求','运行时等待承诺请求',
    '运行时完成','运行时属性结果',
]#公开面结束

def 运行时调用参数(种类,**字段):#调用参数
    """向被检查界域中函数提供的一个参数。"""
    return {'kind':种类,**字段}#判别联合

def 运行时执行上下文(种类,id):#执行上下文
    """一个界域内原生子执行上下文的后端本地选择器。"""
    return {'kind':种类,'id':id}#数字或唯一id

class 运行时求值请求:#求值请求
    """Runtime 后端支持的、与引擎无关的求值选项。"""
    def __init__(自身,expression,context=None,objectGroup=None,includeCommandLineAPI=None,silent=None,returnByValue=None,generatePreview=None,userGesture=None,awaitPromise=None,disableBreaks=None,replMode=None,allowUnsafeEvalBlockedByCSP=None,throwOnSideEffect=None,serializationOptions=None,timeoutMs=None):#构造
        """保存求值请求字段。"""
        自身.expression=expression#表达式
        自身.context=context#执行上下文
        自身.objectGroup=objectGroup#对象组
        自身.includeCommandLineAPI=includeCommandLineAPI#是否含命令行API
        自身.silent=silent#是否静默
        自身.returnByValue=returnByValue#是否按值返回
        自身.generatePreview=generatePreview#是否生成预览
        自身.userGesture=userGesture#是否用户手势
        自身.awaitPromise=awaitPromise#是否等待Promise
        自身.disableBreaks=disableBreaks#是否禁用断点
        自身.replMode=replMode#是否REPL模式
        自身.allowUnsafeEvalBlockedByCSP=allowUnsafeEvalBlockedByCSP#是否允许被CSP挡住的不安全eval
        自身.throwOnSideEffect=throwOnSideEffect#副作用时是否抛错
        自身.serializationOptions=serializationOptions#序列化选项
        自身.timeoutMs=timeoutMs#超时毫秒

class 运行时获取属性请求:#获取属性请求
    """对一个后端对象的属性枚举请求。"""
    def __init__(自身,handle,ownProperties=None,accessorPropertiesOnly=None,generatePreview=None,nonIndexedPropertiesOnly=None):#构造
        """保存获取属性请求字段。"""
        自身.handle=handle#对象句柄
        自身.ownProperties=ownProperties#仅自有
        自身.accessorPropertiesOnly=accessorPropertiesOnly#仅访问器
        自身.generatePreview=generatePreview#是否生成预览
        自身.nonIndexedPropertiesOnly=nonIndexedPropertiesOnly#仅非索引属性

class 运行时调用函数请求:#调用函数请求
    """在一个被检查界域内的函数调用请求。"""
    def __init__(自身,functionDeclaration,context=None,receiver=None,arguments=None,objectGroup=None,silent=None,returnByValue=None,generatePreview=None,userGesture=None,awaitPromise=None,throwOnSideEffect=None,serializationOptions=None):#构造
        """保存调用函数请求字段。"""
        自身.functionDeclaration=functionDeclaration#函数声明源
        自身.context=context#执行上下文
        自身.receiver=receiver#接收者句柄
        自身.arguments=tuple(arguments) if arguments is not None else None#参数列表
        自身.objectGroup=objectGroup#对象组
        自身.silent=silent#是否静默
        自身.returnByValue=returnByValue#是否按值返回
        自身.generatePreview=generatePreview#是否生成预览
        自身.userGesture=userGesture#是否用户手势
        自身.awaitPromise=awaitPromise#是否等待Promise
        自身.throwOnSideEffect=throwOnSideEffect#副作用时是否抛错
        自身.serializationOptions=serializationOptions#序列化选项

class 运行时等待承诺请求:#等待Promise请求
    """对一个保留后端对象的 Promise 等待请求。"""
    def __init__(自身,promise,returnByValue=None,generatePreview=None):#构造
        """保存等待 Promise 请求字段。"""
        自身.promise=promise#Promise句柄
        自身.returnByValue=returnByValue#是否按值返回
        自身.generatePreview=generatePreview#是否生成预览

class 运行时完成:#完成结果
    """求值、函数调用与等待 Promise 的共用结果。"""
    def __init__(自身,result,exceptionDetails=None):#构造
        """保存完成结果字段。"""
        自身.result=result#结果值
        自身.exceptionDetails=exceptionDetails#异常详情

class 运行时属性结果:#属性结果
    """属性枚举的共用结果。"""
    def __init__(自身,properties,internalProperties=None,privateProperties=None,exceptionDetails=None):#构造
        """保存属性结果字段。"""
        自身.properties=tuple(properties)#普通属性
        自身.internalProperties=tuple(internalProperties) if internalProperties is not None else None#内部属性
        自身.privateProperties=tuple(privateProperties) if privateProperties is not None else None#私有属性
        自身.exceptionDetails=exceptionDetails#异常详情
