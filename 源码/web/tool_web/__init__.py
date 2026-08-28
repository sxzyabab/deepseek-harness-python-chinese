"""面向模型的 `web_search` 与 `web_fetch` 工具，建立在 `ctx.web` 上。本包负责 schema、校验、提示词指引、上限与展示，从不实现具体提供方。启用控制工具注册；已启用的工具在提供方不可用时仍可见，执行时以结构化错误失败。"""
from ...依赖.schemastery import 路径上节点,布尔字段,数字字段#配置字段
from .搜索 import (#再导出搜索工具 API
    网络搜索最大结果数,#搜索返回来源的默认上限
    应用网络搜索工具,#注册搜索工具
    格式化搜索输出,#拼面向模型的搜索文本
    解析搜索参数,#收成缝的请求字段
    呈现搜索调用,#进行中搜索卡片
    呈现搜索结果,#完成态搜索卡片
    搜索元自值,#从结果值抽出展示 meta
    搜索元自结果,#校验回放 meta
)#搜索模块
from .抓取 import (#再导出抓取工具 API
    应用网络抓取工具,#注册抓取工具
    格式化抓取输出,#拼面向模型的抓取文本
    解析抓取参数,#收成缝的请求字段
    呈现抓取调用,#进行中抓取卡片
    呈现抓取结果,#完成态抓取卡片
    抓取元自值,#从结果值抽出展示 meta
    抓取元自结果,#校验回放 meta
)#抓取模块

__all__=[#公开面
    '名称','注入','应用','配置模式','Config','name','inject',
    '网络搜索最大结果数','应用网络搜索工具','格式化搜索输出',
    '解析搜索参数','呈现搜索调用','呈现搜索结果','搜索元自值','搜索元自结果',
    '应用网络抓取工具','格式化抓取输出','解析抓取参数',
    '呈现抓取调用','呈现抓取结果','抓取元自值','抓取元自结果',
]#结束

名称='tool-web'#加载器诊断使用的 Cordis 插件名
注入=['tools','web','systemPrompt']#web 工具套件所需的服务
name=名称#Cordis插件名
inject=注入#Cordis依赖声明
默认网络工具超时毫秒=30000#web 工具的默认协作式工具调用超时预算（毫秒）
默认抓取最大输出字符=200000#一次 web_fetch 输出以及同步转换源字符的默认上限

配置模式=路径上节点({#插件配置：注册哪些 web 工具、来源上限、各工具预算、抓取输出上限
    'search':布尔字段(默认值=True),#是否注册 web_search
    'fetch':布尔字段(默认值=True),#是否注册 web_fetch
    'searchMaxResults':数字字段(默认值=网络搜索最大结果数),#一次 web_search 返回的来源上限
    'fetchTimeoutMs':数字字段(默认值=默认网络工具超时毫秒),#web_fetch 的协作超时预算
    'searchTimeoutMs':数字字段(默认值=默认网络工具超时毫秒),#web_search 的协作超时预算
    'fetchMaxOutputChars':数字字段(默认值=默认抓取最大输出字符),#同步转换源字符与完整输出上限
})#配置模式结束
Config=配置模式#Cordis 配置模式

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 断言正整数(名称字,值):#拒绝非正整数
    """配置的条数、超时和字符上限必须是正整数。"""
    if isinstance(值,bool):#布尔不是整数
        raise Exception('tool-web: '+名称字+' must be a positive integer')#加载时大声失败
    if isinstance(值,int):#整型
        if 值<1:#小于 1
            raise Exception('tool-web: '+名称字+' must be a positive integer')#加载时大声失败
        return#合格
    if isinstance(值,float) and 值.is_integer() and 值>=1:#整值正浮点
        return#合格
    raise Exception('tool-web: '+名称字+' must be a positive integer')#加载时大声失败

def 应用(上下文,配置):#按配置注册已启用工具
    """注册已启用的 web 工具。`search`/`fetch` 默认 true；只要其中一个的产品在配置里关掉另一个。每个工具的协作超时预算在这里解析，作为 ToolDefinition.timeoutMs 交给超时策略强制执行。工具的 disposer 按 fiber 作用域，不需要手工拆除。"""
    已解析=配置#schemastery（Config）已填完每个带默认值的字段
    断言正整数('searchMaxResults',取字段(已解析,'searchMaxResults'))#来源上限必须为正整数
    断言正整数('fetchTimeoutMs',取字段(已解析,'fetchTimeoutMs'))#抓取超时必须为正整数
    断言正整数('searchTimeoutMs',取字段(已解析,'searchTimeoutMs'))#搜索超时必须为正整数
    断言正整数('fetchMaxOutputChars',取字段(已解析,'fetchMaxOutputChars'))#输出上限必须为正整数
    if 取字段(已解析,'search'):#启用搜索
        应用网络搜索工具(上下文,取字段(已解析,'searchMaxResults'),取字段(已解析,'searchTimeoutMs'),取字段(已解析,'fetch'))#注册搜索，并告知是否有 fetch
    if 取字段(已解析,'fetch'):#启用抓取
        应用网络抓取工具(上下文,取字段(已解析,'fetchTimeoutMs'),取字段(已解析,'fetchMaxOutputChars'))#注册抓取

apply=应用#Cordis插件入口
default=应用#默认导出
默认=应用#中文默认导出
