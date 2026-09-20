"""面向模型的 web_search 与 web_fetch 工具：负责 schema、校验、提示词与呈现，不实现提供方。"""
from ...依赖.schemastery import 布尔字段,数字字段
from .搜索 import (
    网络搜索最大结果数,
    应用网络搜索工具,
    格式化搜索输出,
    解析搜索参数,
    呈现搜索调用,
    呈现搜索结果,
    搜索元自值,
    搜索元自结果,
)
from .抓取 import (
    应用网络抓取工具,
    格式化抓取输出,
    解析抓取参数,
    呈现抓取调用,
    呈现抓取结果,
    抓取元自值,
    抓取元自结果,
)

class 网页工具错误(Exception):
    """tool-web 加载或参数校验失败。"""

__all__=[
    '包名','名称','依赖','应用','默认','配置模式',
    '网页工具错误',
    '网络搜索最大结果数','应用网络搜索工具','格式化搜索输出',
    '解析搜索参数','呈现搜索调用','呈现搜索结果','搜索元自值','搜索元自结果',
    '应用网络抓取工具','格式化抓取输出','解析抓取参数',
    '呈现抓取调用','呈现抓取结果','抓取元自值','抓取元自结果',
]

包名='@deepseek-ai/dsh-tool-web'
名称='tool-web'
依赖=['tools','web','systemPrompt']
默认网络工具超时毫秒=30000#协作式工具调用超时预算（毫秒）
默认抓取最大输出字符=200000#一次 web_fetch 输出及同步转换源字符上限

配置模式={
    'search':布尔字段(默认值=True),#是否注册 web_search
    'fetch':布尔字段(默认值=True),#是否注册 web_fetch
    'searchMaxResults':数字字段(默认值=网络搜索最大结果数),#一次 web_search 返回的来源上限
    'fetchTimeoutMs':数字字段(默认值=默认网络工具超时毫秒),#web_fetch 协作超时预算
    'searchTimeoutMs':数字字段(默认值=默认网络工具超时毫秒),#web_search 协作超时预算
    'fetchMaxOutputChars':数字字段(默认值=默认抓取最大输出字符),#同步转换源字符与完整输出上限
}

def 断言正整数(名称字,值):
    """配置的条数、超时和字符上限必须是正整数。"""
    if isinstance(值,bool):
        raise 网页工具错误('tool-web: '+名称字+' must be a positive integer')
    if isinstance(值,int):
        if 值<1:
            raise 网页工具错误('tool-web: '+名称字+' must be a positive integer')
        return
    if isinstance(值,float) and 值.is_integer() and 值>=1:
        return
    raise 网页工具错误('tool-web: '+名称字+' must be a positive integer')

def 应用(上下文,配置):
    """注册已启用的 web 工具。协作超时预算写入 ToolDefinition.timeoutMs，由超时策略强制执行。"""
    已解析=配置
    断言正整数('searchMaxResults',已解析['searchMaxResults'])
    断言正整数('fetchTimeoutMs',已解析['fetchTimeoutMs'])
    断言正整数('searchTimeoutMs',已解析['searchTimeoutMs'])
    断言正整数('fetchMaxOutputChars',已解析['fetchMaxOutputChars'])
    if 已解析['search'] is True:#布尔配置，不是判空
        应用网络搜索工具(上下文,已解析['searchMaxResults'],已解析['searchTimeoutMs'],已解析['fetch'])
    if 已解析['fetch'] is True:
        应用网络抓取工具(上下文,已解析['fetchTimeoutMs'],已解析['fetchMaxOutputChars'])

默认=应用
name=名称#框架槽
inject=依赖#框架槽
apply=应用#框架槽
Config=配置模式#框架槽
default=默认#框架槽
