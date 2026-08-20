"""仅浏览器侧栏插件：把侧栏壳登记进布局拥有的槽。

对齐上游 `ui-sidebar/src/client/index.ts`。公开面仅中文名。
结构树 `侧栏根` 接线；完整 DOM/CSS 像素半需浏览器运行时，本包以样式表字符串落盘。
"""
from .文案 import 中文,英文,侧栏文案键#词典
from .约定.槽位 import 侧栏槽名,侧栏子槽,侧栏词表命名空间#槽约定
from .侧栏根 import 侧栏根,折叠落定毫秒,滚动条滞留毫秒,样式表#根组件

__all__=[#仅中文公开名
    '注入','应用','命名空间','中文','英文','侧栏文案键',
    '侧栏槽名','侧栏子槽','侧栏词表命名空间',
    '侧栏根','折叠落定毫秒','滚动条滞留毫秒','样式表',
]#公开面结束

命名空间=侧栏词表命名空间#词表命名空间
注入=['slots','layout','sessions','workspaces','locale']#槽位、布局、会话、工作区、文案

def 应用(上下文):#安装侧栏壳
    """登记词典与侧栏壳槽位。"""
    上下文.effect(lambda:上下文.locale.register(命名空间,{'zh':中文,'en':英文}),'ui-sidebar: dictionaries')#登记中英文案
    def 注入面():#根注入
        """开新会话与切换侧栏。"""
        return {#注入
            'startSession':lambda 工作区标识=None:上下文.workspaces.startSession(工作区标识),#开新会话
            'toggleSidebar':lambda:上下文.layout.toggleSidebar(),#切换侧栏
        }#注入结束
    def 挂槽():#登记侧栏槽
        """登记侧栏壳。"""
        return 上下文.slots.register({#登记
            'name':侧栏槽名,#槽名
            'locale':命名空间,#文案
            'children':侧栏子槽,#子槽
            'inject':注入面,#注入
        },侧栏根)#根组件
    上下文.effect(挂槽,'ui-sidebar: slot registration')#槽位登记
