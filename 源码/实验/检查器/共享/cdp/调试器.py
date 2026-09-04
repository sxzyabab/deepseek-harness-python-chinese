"""活动调试器后端使用的、与界域无关的值。

对齐上游 `shared/cdp/debugger.ts`。公开面仅中文名。
"""
__all__=[#仅中文公开名
    '运行时调试位置','运行时调试作用域','运行时调试调用帧',
    '运行时调用帧求值请求','运行时调试器启用请求','运行时调试器恢复请求',
    '运行时调试器事件','运行时调用帧求值',
]#公开面结束

class 运行时调试位置:#调试位置
    """与 CDP ScriptId 分配策略无关的一个源位置。"""
    def __init__(自身,scriptKey,lineNumber,columnNumber=None):#构造
        """保存调试位置字段。"""
        自身.scriptKey=scriptKey#脚本键
        自身.lineNumber=lineNumber#行号
        自身.columnNumber=columnNumber#列号

class 运行时调试作用域:#调试作用域
    """附着在已暂停调用帧上的一个词法作用域。"""
    def __init__(自身,type,object,name=None,startLocation=None,endLocation=None):#构造
        """保存调试作用域字段。"""
        自身.type=type#作用域类型
        自身.object=object#作用域对象
        自身.name=name#作用域名
        自身.startLocation=startLocation#起始位置
        自身.endLocation=endLocation#结束位置

class 运行时调试调用帧:#调试调用帧
    """一个已暂停的 JavaScript 调用帧。"""
    def __init__(自身,callFrameId,functionName,location,url,scopeChain,thisObject,functionLocation=None,returnValue=None):#构造
        """保存调试调用帧字段。"""
        自身.callFrameId=callFrameId#调用帧标识
        自身.functionName=functionName#函数名
        自身.functionLocation=functionLocation#函数位置
        自身.location=location#当前位置
        自身.url=url#源URL
        自身.scopeChain=tuple(scopeChain)#作用域链
        自身.thisObject=thisObject#this对象
        自身.returnValue=returnValue#返回值

class 运行时调用帧求值请求:#调用帧求值请求
    """在一个已暂停调用帧上的、与引擎无关的求值请求。"""
    def __init__(自身,callFrameId,expression,objectGroup=None,includeCommandLineAPI=None,silent=None,returnByValue=None,generatePreview=None,throwOnSideEffect=None,timeoutMs=None):#构造
        """保存调用帧求值请求字段。"""
        自身.callFrameId=callFrameId#调用帧标识
        自身.expression=expression#表达式
        自身.objectGroup=objectGroup#对象组
        自身.includeCommandLineAPI=includeCommandLineAPI#是否含命令行API
        自身.silent=silent#是否静默
        自身.returnByValue=returnByValue#是否按值返回
        自身.generatePreview=generatePreview#是否生成预览
        自身.throwOnSideEffect=throwOnSideEffect#副作用时是否抛错
        自身.timeoutMs=timeoutMs#超时毫秒

class 运行时调试器启用请求:#启用调试器请求
    """启用 Debugger 时请求的可选原生脚本缓存上限。"""
    def __init__(自身,maxScriptsCacheSize=None):#构造
        """保存启用请求字段。"""
        自身.maxScriptsCacheSize=maxScriptsCacheSize#脚本缓存上限

class 运行时调试器恢复请求:#恢复调试器请求
    """恢复原生调试器时请求的可选终止。"""
    def __init__(自身,terminateOnResume=None):#构造
        """保存恢复请求字段。"""
        自身.terminateOnResume=terminateOnResume#恢复时是否终止

def 运行时调试器事件(类型,**字段):#调试器事件
    """界域后端发出的调试器生命周期通知。"""
    return {'type':类型,**字段}#判别联合

运行时调用帧求值=object#调用帧求值结果别名占位
