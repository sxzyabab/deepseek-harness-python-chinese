'挂上操作卡片和它的 Remote'
from ....类型化远程调用.协议 import 严格编解码,调用描述符,远程贡献
from . import 挂载,文案,注册表,卡片,提议行

__all__=['挂载','文案','注册表','卡片','提议行','依赖','应用','远程贡献值']

包名='@deepseek-ai/dsh-action-cards'
服务名='actionCards'
命名='actionCards'
前缀=包名+'#'+命名+'/'


def 严格(符号):
    '透传严格编解码。结构由宿主方法收'
    return 严格编解码(符号)


远程贡献值=远程贡献(包名,[
    调用描述符(
        前缀+'act',服务名,命名,'act',
        [
            {'name':'sessionId','wire':'sessionId','source':'lookup','lookup':'agent','codec':严格('string')},
            {'name':'callId','wire':'callId','source':'json','codec':严格('string')},
            {'name':'verb','wire':'verb','source':'json','codec':严格('string')},
            {'name':'payload','wire':'payload','source':'json','optional':True,'codec':严格('json')},
        ],
        严格('ActionCardResult'),
        {'file':'src/index.ts','line':338,'column':3},
        作用域={'context':'agent','wire':'sessionId'},
    ),
])

依赖=挂载.依赖
inject=依赖


def 应用(上下文,配置值=None):
    '挂上操作卡片和它的 Remote。返回卸除函数'
    return 挂载.挂载操作卡片(上下文,远程贡献值)


apply=应用
