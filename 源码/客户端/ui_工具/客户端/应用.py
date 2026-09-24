from .文案 import 会话命名空间#会话文案命名空间
from .工具调用树 import 工具调用树#工具调用树组件
from .工具详情 import 工具详情#工具详情渲染器
from .提问行 import 提问工具视图#提问原子视图
from .bash样例 import bash工具视图样例#bash 原子视图
from .文件变更行 import 文件变更工具视图#文件变更原子视图
from .读行 import 读工具视图#读取原子视图
from .检索行 import 检索工具视图#检索原子视图
from .待办行 import 待办工具视图#待办原子视图
from .网页行 import 网页工具视图#网页原子视图
from .槽 import 槽名工具调用视图,槽名聊天节点,槽名详情工具#槽名

__all__=['依赖','应用']#仅中文公开名

依赖=['slots','remote']#槽登记表与宿主事实面

def 绑定工具调用参数前缀(_标准,钩上下文):
    """到组件调用前不订阅；只读本调用的参数原文前缀。"""
    助手=钩上下文['assistant'] if 'assistant' in 钩上下文 else None
    调用标识=钩上下文['callId']
    def 取前缀():
        """preparing 阶段的 argsRaw；其余阶段空串。"""
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

def 应用(上下文):#挂载整棵 Tool 渲染器与内置原子登记
    """登记调用树、详情与内置 toolview 插件。"""
    命名空间=会话命名空间#词典席
    def 取宿主():
        return 上下文.remote.$host
    def 订宿主(监听):
        return 上下文.on('connection/reset',监听)
    宿主信息={'getSnapshot':取宿主,'subscribe':订宿主}
    def 工具注入():
        """注入宿主事实钩。"""
        return {'hooks':{'hostInfo':宿主信息}}
    def 登记调用树():#等聊天节点槽再登记
        """按 tool-call 键分发调用树。"""
        return 上下文.slots.register({#节点登记
            'name':槽名聊天节点,#聊天节点槽名
            'key':'tool-call',#按 tool-call 键分发
            'locale':命名空间,#会话文案
            'children':{#子槽声明
                槽名工具调用视图:{#按工具名分发
                    'kind':'keyed','scope':'session',
                    'inject':{'hooks':{'toolCallArgumentsPartial':绑定工具调用参数前缀}},
                },
            },
            'inject':工具注入,#宿主事实
        },工具调用树)#组件
    上下文.slots.inject(槽名聊天节点,登记调用树)#等槽
    def 登记详情():#等详情槽再登记
        """登记工具详情。"""
        return 上下文.slots.register({#详情登记
            'name':槽名详情工具,#工具详情槽名
            'locale':命名空间,#会话文案
        },工具详情)#组件
    上下文.slots.inject(槽名详情工具,登记详情)#等槽
    for 插件 in (#内置原子视图
        bash工具视图样例,读工具视图,文件变更工具视图,
        检索工具视图,网页工具视图,待办工具视图,提问工具视图,
    ):#逐个挂载
        if 'apply' in 插件 and callable(插件['apply']):#有 apply
            插件['apply'](上下文)#走登记函数
        else:#字典登记面
            if 'keys' in 插件 and 插件['keys'] is not None:#多键
                键列表=插件['keys']#键表
            elif 'key' in 插件 and 插件['key'] is not None:#单键
                键列表=(插件['key'],)#单键表
            else:#无键
                键列表=()#空
            组件=插件['component'] if 'component' in 插件 else None#组件
            for 键 in 键列表:#逐键
                if 键 is None or 组件 is None:#缺
                    continue#跳
                def 登记(键=键,组件=组件):#闭包保键
                    """登记一键。"""
                    return 上下文.slots.register({#按键条目
                        'name':槽名工具调用视图,'key':键,'locale':命名空间,#选项
                    },组件)#组件
                上下文.slots.inject(槽名工具调用视图,登记)#等槽

inject=依赖#框架槽
apply=应用#框架槽
