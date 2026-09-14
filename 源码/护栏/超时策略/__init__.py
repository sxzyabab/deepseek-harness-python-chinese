from ...依赖 import cordis#外部依赖胶水
from ...工具.超时 import 截止,取超时#截止武装与按码判定

工具超时码='TOOL_TIMEOUT'#本插件拥有的超时错误码；同时用作内部截止分类码和替换结果上的结构化错误 code
名称='timeout-policy'#loader 诊断所用的 Cordis 插件名
注入=['tools']#本插件包装（tools/execute）并读取（get）的工具注册表服务

__all__=['工具超时码','名称','注入','应用']#仅中文公开名；Cordis 槽英文别名不入表

def 写信号(执行,信号):
    """写回执行载体上的 `signal`。"""
    执行['signal']=信号#英文字段

def 读信号(执行):
    """读执行上的取消信号。"""
    return 执行['signal'] if 'signal' in 执行 else None#缺席为无

def 工具超时结果(超时毫秒):
    """本插件截止胜出时替换上去的结构化结果。"""
    消息='tool call timed out after '+str(超时毫秒)+'ms'#面向模型的超时文案，字面量不翻译
    return {#超时结构化结果
        'content':[{'type':'text','text':'Error: '+消息}],#模型可见错误文本
        'isError':True,#标记为错误结果
        'error':{'message':消息,'info':{'name':'ToolTimeoutError','code':工具超时码}},#结构化超时错误
    }#返回超时结果

def 应用(上下文对象):
    """注册超时包装器。解析工具定义，临时替换 `exec.signal`，委托，恢复上游信号，且仅在本包装器自己的计时器开火时替换结果。"""
    def 执行臂(执行,下一步,*剩余):
        """环绕单次工具执行：有预算则武装截止，无预算则原样委托。"""
        定义=上下文对象.tools.获取(执行['name'],执行['agent'] if 'agent' in 执行 else None)#读取工具声明
        超时毫秒=定义['timeoutMs'] if 定义 is not None and 'timeoutMs' in 定义 else None#工具声明的预算
        if 超时毫秒 is None:#无预算则直接委托
            return 下一步()#委托下游
        句柄=截止(读信号(执行),超时毫秒,工具超时码)#武装带本码的截止
        上游=读信号(执行)#保存上游信号
        写信号(执行,句柄.信号)#换上本截止信号
        try:#委托下游执行
            结果=下一步()#等待工具完成
            if 取超时(句柄.信号,工具超时码) is not None:#本包装器超时胜出
                return 工具超时结果(超时毫秒)#替换为结构化超时结果
            return 结果#未超时则返回原结果
        finally:#无论成败都恢复信号并释放定时器
            写信号(执行,上游)#还原调用方信号
            句柄.释放()#清除已武装定时器
    上下文对象.监听('tools/execute',执行臂)#安装环绕监听

apply=应用#Cordis插件入口
default=应用#默认导出
name=名称#Cordis插件名
inject=注入#Cordis依赖声明
