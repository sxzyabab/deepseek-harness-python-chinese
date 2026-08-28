"""登记 Tool 调用树、详情渲染器与内置原子视图。

对齐上游 `ui-tool/src/client/apply.ts`。公开面仅中文名。
"""
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

__all__=['注入','应用']#仅中文公开名

注入=['slots']#依赖 slots 服务

def 应用(上下文):#挂载整棵 Tool 渲染器与内置原子登记
    """登记调用树、详情与内置 toolview 插件。"""
    命名空间=会话命名空间#词典席
    def 登记调用树():#等聊天节点槽再登记
        """按 tool-call 键分发调用树。"""
        return 上下文.slots.register({#节点登记
            'name':槽名聊天节点,#聊天节点槽名
            'key':'tool-call',#按 tool-call 键分发
            'locale':命名空间,#会话文案
            'children':{#子槽声明
                槽名工具调用视图:{'kind':'keyed','scope':'session'},#按工具名分发
            },#结束 children
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
        if callable(插件.get('apply')):#有 apply
            插件['apply'](上下文)#走登记函数
        else:#字典登记面
            键们=插件.get('keys') or ((插件.get('key'),) if 插件.get('key') else ())#键表
            组件=插件.get('component')#组件
            for 键 in 键们:#逐键
                if 键 is None or 组件 is None:#缺
                    continue#跳
                def 登记(键=键,组件=组件):#闭包保键
                    """登记一键。"""
                    return 上下文.slots.register({#按键条目
                        'name':槽名工具调用视图,'key':键,'locale':命名空间,#选项
                    },组件)#组件
                上下文.slots.inject(槽名工具调用视图,登记)#等槽
