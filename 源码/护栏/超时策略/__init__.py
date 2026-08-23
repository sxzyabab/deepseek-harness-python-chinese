"""协作式工具调用超时强制器。工具声明 `timeoutMs` 并承诺遵守 `exec.signal`；本包装器武装该截止时间，并把自身到期映射为 `TOOL_TIMEOUT`，不与工具 Promise 竞态或丢弃它。

FIXME: 首次打标签发布前敲定拟议的 `@deepseek-ai/dsh-timeout-guard` 重命名——仅建议，使名称与其所在的 `guard/` 对齐；在决议时再定
（重新分组 Agent Note：architecture/2026-07-29-package-regrouping）。
"""
from ...依赖 import cordis#外部依赖胶水
是否thenable=cordis.工具.是否thenable#可等待判定
from ...工具.超时 import 截止,取超时#截止武装与按码判定

工具超时码='TOOL_TIMEOUT'#本插件拥有的超时错误码；同时用作内部截止分类码和替换结果上的结构化错误 code
名称='timeout-policy'#loader 诊断所用的 Cordis 插件名
注入=['tools']#本插件包装（tools/execute）并读取（get）的工具注册表服务
name=名称#Cordis插件名
inject=注入#Cordis依赖声明

__all__=['工具超时码','名称','注入','应用','默认']#仅中文公开名；Cordis 槽英文别名不入表

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 解开(值):#承诺则等待否则原样
    """承诺则等待，否则原样返回。"""
    if 是否thenable(值):#可等待
        return 值.等待()#等待承诺
    return 值#同步值

def 写信号(执行,信号):#把信号写回执行载体
    """写回 `signal`；若载体也暴露中文字段则一并同步。"""
    if isinstance(执行,dict):#映射形态执行
        执行['signal']=信号#英文字段
        if '信号' in 执行:#已有中文字段才同步
            执行['信号']=信号#中文字段
        return#写完
    setattr(执行,'signal',信号)#对象英文字段
    if hasattr(执行,'信号'):#对象中文字段
        setattr(执行,'信号',信号)#同步中文

def 读信号(执行):#读执行上的取消信号
    """优先英文字段 `signal`，再试中文 `信号`。"""
    信号=取字段(执行,'signal')#英文
    if 信号 is not None:#已有
        return 信号#英文信号
    return 取字段(执行,'信号')#中文或缺席

def 工具超时结果(超时毫秒):#组装超时替换结果
    """本插件截止胜出时替换上去的结构化结果。`content` 是面向模型的消息；`error.code` 是本插件拥有的同一 `TOOL_TIMEOUT`，以便重试/沙盒插件（以及回放）按它路由。"""
    消息='tool call timed out after '+str(超时毫秒)+'ms'#面向模型的超时文案，字面量不翻译
    return {#超时结构化结果
        'content':[{'type':'text','text':'Error: '+消息}],#模型可见错误文本
        'isError':True,#标记为错误结果
        'error':{'message':消息,'info':{'name':'ToolTimeoutError','code':工具超时码}},#结构化超时错误
    }#返回超时结果

def 应用(上下文对象):#安装工具调用超时包装
    """注册超时包装器。它解析调用方可见的工具定义，临时替换 `exec.signal`，委托，恢复上游信号，且仅在本包装器自己的计时器开火时替换结果。"""
    def 执行臂(执行,下一步,*剩余):#包装 tools/execute
        """环绕单次工具执行：有预算则武装截止，无预算则原样委托。"""
        工具服务=取字段(上下文对象,'tools')#工具注册表
        取法=getattr(工具服务,'获取',None) or getattr(工具服务,'get',None)#中文或英文查找
        定义=取法(取字段(执行,'name'),取字段(执行,'agent')) if callable(取法) else None#读取工具声明
        超时毫秒=取字段(定义,'timeoutMs')#工具声明的预算
        # 未声明预算的工具：不加截止，原样委托。
        if 超时毫秒 is None:#无预算则直接委托
            return 解开(下一步())#委托下游
        句柄=截止(读信号(执行),超时毫秒,工具超时码)#武装带本码的截止
        # 把派生截止换到 exec 上再派发，然后恢复调用方自己的信号，使执行后监听器永远看不到本插件（可能已中止的）超时信号。
        上游=读信号(执行)#保存上游信号
        写信号(执行,取字段(句柄,'signal') or 取字段(句柄,'信号'))#换上本截止信号
        try:#委托下游执行
            结果=解开(下一步())#等待工具完成
            # 若是我们的计时器开火（按码限定范围——嵌套外层截止在此读成 None），工具/能力已看到中止并进入静止；用模型看到的结构化 TOOL_TIMEOUT 替换它返回的任何东西（它自己的中止结果）。
            if 取超时(取字段(句柄,'signal') or 取字段(句柄,'信号'),工具超时码) is not None:#本包装器超时胜出
                return 工具超时结果(超时毫秒)#替换为结构化超时结果
            return 结果#未超时则返回原结果
        finally:#无论成败都恢复信号并释放定时器
            写信号(执行,上游)#还原调用方信号
            释放=getattr(句柄,'释放',None) or getattr(句柄,'dispose',None)#中文或英文释放
            if callable(释放):#有释放入口
                释放()#清除已武装定时器
    上下文对象.on('tools/execute',执行臂)#安装环绕监听

apply=应用#Cordis插件入口
default=应用#默认导出
默认=应用#中文默认导出
