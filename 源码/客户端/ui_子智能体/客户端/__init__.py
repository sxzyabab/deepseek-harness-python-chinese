from .文案 import 命名空间,中文,英文,子智能体文案键#词典
from .只读认领 import 选择只读子智能体#认领判定
from .只读撰写器 import 只读撰写器,样式表 as 只读样式表#只读面
from .目录动作 import (
    目录动作,格式化令牌,格式化时长,格式化精确时长,令牌合计,活动时长毫秒,样式表 as 目录样式表,
)
from .侧栏聊天 import 登记侧栏聊天,子智能体聊天地址#侧栏聊天

__all__=[
    '依赖','应用','命名空间','中文','英文','子智能体文案键',
    '选择只读子智能体','只读撰写器','目录动作',
    '格式化令牌','格式化时长','格式化精确时长','令牌合计','活动时长毫秒',
    '只读样式表','目录样式表','登记侧栏聊天','子智能体聊天地址',
]

依赖=['sessions','uiWorkspace','slots','locale','sidebarRight']

def 应用(上下文):
    """登记子智能体目录、侧栏聊天与只读编写器。"""
    def 登记词典():
        """登记本插件词典。"""
        return 上下文.locale.register(命名空间,{'zh':中文,'en':英文})
    上下文.副作用(登记词典,'ui-subagent: dictionaries')
    def 挂侧栏聊天(子上下文):
        """资源和侧栏类型可用后登记。"""
        登记侧栏聊天(子上下文,上下文.locale.bind(命名空间))
    上下文.依赖启动(['resources','sidebarRightTabs'],挂侧栏聊天)

    def 目录动作面(_父会话标识=None):
        """打开子项、侧栏打开、刷新投影。"""
        def 打开子(地址):
            """主工作区打开。"""
            上下文.uiWorkspace.openSession(地址)
        def 侧栏打开子(地址):
            """侧栏新窗格打开。"""
            上下文.sidebarRight.openResource(子智能体聊天地址(地址),{
                'kind':'subagentchat',
                'preferNewPane':True,
            })
        def 刷新投影(父会话标识):
            """刷新投影。"""
            上下文.sessions.refreshProjections(父会话标识)
        return {
            'openChild':打开子,
            'openChildAside':侧栏打开子,
            'refreshProjection':刷新投影,
        }

    def 登记谱系():
        """标题旁谱系。"""
        return 上下文.slots.register({
            'name':'conversation.session.header.lineage',
            'locale':命名空间,
            'inject':目录动作面,
        },目录动作)
    上下文.slots.inject('conversation.session.header.lineage',登记谱系)

    def 登记目录():
        """标题动作带目录。"""
        return 上下文.slots.register({
            'name':'conversation.session.header.actions',
            'id':'subagent-catalog',
            'order':-30,
            'locale':命名空间,
            'inject':目录动作面,
        },目录动作)
    上下文.slots.inject('conversation.session.header.actions',登记目录)

    def 登记只读():
        """只读编写器。"""
        return 上下文.slots.register({
            'name':'conversation.composer',
            'priority':-10,
            'locale':命名空间,
            'select':选择只读子智能体,
        },只读撰写器)
    上下文.slots.inject('conversation.composer',登记只读)

inject=依赖
apply=应用
