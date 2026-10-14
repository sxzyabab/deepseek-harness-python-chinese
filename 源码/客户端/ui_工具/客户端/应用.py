from .文案 import 会话命名空间
from ....基础设施.通用工具 import 获取内部数据
from .工具调用树 import 工具调用树
from .提问行 import 提问工具视图
from .bash样例 import bash工具视图样例
from .文件变更行 import 文件变更工具视图
from .读行 import 读工具视图
from .检索行 import 检索工具视图
from .待办行 import 待办工具视图
from .网页行 import 网页工具视图
from .槽 import 槽名工具调用视图,槽名聊天节点

__all__=['依赖','应用']

依赖=['slots','remote']

def 绑定工具调用参数前缀(_标准,钩上下文):
    '到组件调用前不订阅；只读本调用的参数原文前缀'
    助手=钩上下文['assistant'] if 'assistant' in 钩上下文 else None
    调用标识=钩上下文['callId']
    def 取前缀():
        'preparing 阶段的 argsRaw；其余阶段空串'
        if 助手 is None:
            return ''
        快照=助手['getSnapshot']()
        if 快照 is None:
            return ''
        块表=快照['blocks'] if 'blocks' in 快照 else ()
        for 候选 in 块表:
            if 'kind' in 候选 and 候选['kind']=='tool-call' and 'callId' in 候选 and 候选['callId']==调用标识:
                return 候选['argsRaw'] if 'argsRaw' in 候选 else ''
        return ''
    return 取前缀

def 应用(上下文):
    '登记调用树，以及挂在 tool.call.toolview 上的内置工具卡'
    命名空间=会话命名空间
    def 取宿主():
        return 获取内部数据(上下文.remote,'host')
    def 订宿主(监听):
        return 上下文.on('connection/reset',监听)
    宿主信息={'getSnapshot':取宿主,'subscribe':订宿主}
    def 工具注入():
        '注入宿主事实钩'
        return {'hooks':{'hostInfo':宿主信息}}
    def 登记调用树():
        '按 tool-call 键分发调用树'
        return 上下文.slots.register({
            'name':槽名聊天节点,
            'key':'tool-call',
            'locale':命名空间,
            'children':{
                槽名工具调用视图:{
                    'kind':'keyed','scope':'session',
                    'inject':{'hooks':{'toolCallArgumentsPartial':绑定工具调用参数前缀}},
                },
            },
            'inject':工具注入,
        },工具调用树)
    上下文.slots.inject(槽名聊天节点,登记调用树)
    for 插件 in (
        bash工具视图样例,读工具视图,文件变更工具视图,
        检索工具视图,网页工具视图,待办工具视图,提问工具视图,
    ):
        if 'apply' in 插件 and callable(插件['apply']):
            插件['apply'](上下文)
        else:
            if 'keys' in 插件 and 插件['keys'] is not None:
                键列表=插件['keys']
            elif 'key' in 插件 and 插件['key'] is not None:
                键列表=(插件['key'],)
            else:
                键列表=()
            组件=插件['component'] if 'component' in 插件 else None
            for 键 in 键列表:
                if 键 is None or 组件 is None:
                    continue
                def 登记(键=键,组件=组件):
                    '登记一键'
                    return 上下文.slots.register({
                        'name':槽名工具调用视图,'key':键,'locale':命名空间,
                    },组件)
                上下文.slots.inject(槽名工具调用视图,登记)

inject=依赖
apply=应用
