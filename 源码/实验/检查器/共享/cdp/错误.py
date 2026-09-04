"""与界域无关的 JavaScript 异常与栈信息。

对齐上游 `shared/cdp/errors.ts`。公开面仅中文名。
"""
__all__=['运行时调用帧','运行时栈跟踪','运行时异常详情']#仅中文公开名

class 运行时调用帧:#调用帧
    """Runtime 异常栈中的一个源位置。"""
    def __init__(自身,functionName,url,lineNumber,columnNumber,scriptKey=None):#构造
        """保存调用帧字段。"""
        自身.functionName=functionName#函数名
        自身.scriptKey=scriptKey#脚本键
        自身.url=url#源URL
        自身.lineNumber=lineNumber#行号
        自身.columnNumber=columnNumber#列号

class 运行时栈跟踪:#栈跟踪
    """与 Debugger 脚本 id 无关的 JavaScript 栈信息。"""
    def __init__(自身,callFrames,description=None,parent=None):#构造
        """保存栈跟踪字段。"""
        自身.description=description#描述
        自身.callFrames=tuple(callFrames)#调用帧
        自身.parent=parent#父栈

class 运行时异常详情:#异常详情
    """执行一条 Runtime 命令时产生的 JavaScript 异常。"""
    def __init__(自身,text,lineNumber,columnNumber,url=None,stackTrace=None,exception=None):#构造
        """保存异常详情字段。"""
        自身.text=text#异常文本
        自身.lineNumber=lineNumber#行号
        自身.columnNumber=columnNumber#列号
        自身.url=url#源URL
        自身.stackTrace=stackTrace#栈跟踪
        自身.exception=exception#异常对象
