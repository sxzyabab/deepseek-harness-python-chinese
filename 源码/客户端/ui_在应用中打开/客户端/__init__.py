'登记文案、工作区目录按钮，以及文档和投递文件的打开按钮。'
from ....宿主.在应用中打开.共享 import 图标前缀
from . import (
    文案,
    应用列表,
    控制器,
    打开路径,
    文件应用,
    打开目标按钮,
    在应用中打开动作,
    打开路径动作,
    打开路径空动作,
    文件路由动作,
)
from .文案 import 中文,英文,命名空间

__all__=[
    '文案','应用列表','控制器','打开路径','文件应用','打开目标按钮',
    '在应用中打开动作','打开路径动作','打开路径空动作','文件路由动作',
    '依赖','命名空间','应用','会话头打开动作',
]

依赖=['sessions','slots','locale','remote','remote.session','shortcuts','layout']


class 会话头打开动作:
    '会话头上的目录按钮。没有工作区目录时不画'
    def __init__(自身,属性=None):
        '记下 props。键齐了就画'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.内=None
        自身.根=None
        自身.已订=False
        自身.绘制中=False
        自身.待重画=False
        if 'window' in 自身.属性 and 'useSessions' in 自身.属性:
            自身.渲染()

    def 更新(自身,属性):
        '换上新的 props'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 确保订阅(自身):
        '会话列表变了就重画'
        if 自身.已订:
            return
        自身.已订=True
        钩=自身.属性.get('useSessions')
        订=getattr(钩,'_subscribe',None)
        if not callable(订):
            return

        def 变更():
            '会话快照变了'
            if 自身.绘制中:
                自身.待重画=True
                return
            自身.渲染()

        订(变更)

    def 渲染(自身):
        '有工作区目录才画出目录按钮'
        if 自身.绘制中:
            自身.待重画=True
            return 自身.根
        自身.绘制中=True
        try:
            自身.确保订阅()
            属性=自身.属性

            def 取目录(状态):
                '这一会话的工作区目录'
                行=状态['byId'].get(属性['sessionId'])
                if 行 is None:
                    return None
                return 行.get('cwd')

            目录=属性['useSessions'](取目录)
            if not 目录:
                if 自身.内 is not None and 自身.内.根 is not None:
                    自身.内.根.remove()
                自身.内=None
                自身.根=None
            else:
                面=dict(属性)
                面['absolutePath']=目录
                if 自身.内 is None:
                    自身.内=在应用中打开动作.在应用中打开动作(面)
                else:
                    自身.内.更新(面)
                    自身.内.渲染()
                自身.根=自身.内.根
        finally:
            自身.绘制中=False
        if 自身.待重画:
            自身.待重画=False
            return 自身.渲染()
        return 自身.根

    def __call__(自身,属性=None):
        '再次交给槽位时刷新'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()


def 应用(上下文,配置=None):
    '登记中英文案、工作区目录按钮，以及文档和投递文件的打开按钮'
    页控制器=控制器.在应用中打开控制器()
    页控制器.加载()
    路径控制器=打开路径.在应用中打开路径控制器(上下文.remote)

    def 登记词典():
        '登记中英文案表。界面显示不走英文表'
        return 上下文.locale.register(命名空间,{'zh':中文,'en':英文})

    上下文.副作用(登记词典,'open-in-app: dictionaries')

    def 命令名():
        '快捷键可见名称'
        return 中文['open.tooltip']

    def 解析():
        '正在打开就挡住。没有工作区或本地应用也挡住'
        if 页控制器.操作.getSnapshot()['phase']=='busy':
            return {'status':'blocked','reason':中文['shortcut.busy']}
        面板=上下文.layout.panelInfo.getSnapshot()
        if 面板.get('activePanelId') is not None:
            return {'status':'blocked','reason':中文['shortcut.unavailable']}
        按标识=上下文.sessions.list.getSnapshot()['byId']
        会话=None
        for 行 in 按标识.values():
            主=行['retainedBy'].get('mainView')
            if 主 is None:
                主=0
            if 主>0:
                会话=行
                break
        应用标识=页控制器.当前应用()
        目录=None if 会话 is None else 会话.get('cwd')
        if not 目录 or 应用标识 is None:
            return {'status':'blocked','reason':中文['shortcut.unavailable']}

        def 跑():
            '在记住的应用里打开当前工作区'
            try:
                页控制器.启动(应用标识,目录)
            except Exception as 错误:
                print('workspace open rejected:',错误)

        return {'status':'handled','run':跑}

    def 登记命令():
        '登记在本地打开工作区'
        return 上下文.shortcuts.register({
            'id':'workspace.openLocal',
            'label':命令名,
            'aliases':['open workspace locally','open in app'],
            'defaults':{
                'desktop:macos':{'code':'KeyO','modifiers':['primary','alt']},
                'desktop:windows':{'code':'KeyO','modifiers':['primary','alt']},
                'desktop:linux':{'code':'KeyO','modifiers':['primary','alt']},
                'web:macos':{'code':'KeyO','modifiers':['primary','shift']},
                'web:windows':{'code':'KeyO','modifiers':['primary','shift']},
            },
            'regions':['page','editable'],
            'modals':[],
            'resolve':解析,
        })

    上下文.副作用(登记命令,'open-in-app: workspace command')

    def 图标网址(应用标识):
        '已安装应用的图标地址'
        return 图标前缀+'/'+str(应用标识)

    def 目录注入():
        '会话头和文件树共用的应用表、选择和启动'
        return {
            'hooks':{
                'openInAppApps':页控制器.应用表,
                'openInAppChoice':页控制器.选择,
                'openInAppLaunch':页控制器.操作,
                'shortcuts':上下文.shortcuts.catalog,
            },
            'launch':页控制器.启动,
            'choose':页控制器.选定,
            'iconUrl':图标网址,
        }

    def 挂会话头():
        '登记会话头部的目录按钮'
        return 上下文.slots.register({
            'name':'conversation.session.header.utilities',
            'id':'open-in-app',
            'order':-10,
            'locale':命名空间,
            'inject':目录注入,
        },会话头打开动作)

    上下文.slots.inject('conversation.session.header.utilities',挂会话头)

    def 挂文件树():
        '登记文件树动作里的目录按钮'
        return 上下文.slots.register({
            'name':'sidebar.right.tab.files.actions',
            'id':'open-in-app',
            'locale':命名空间,
            'inject':目录注入,
        },在应用中打开动作.在应用中打开动作)

    上下文.slots.inject('sidebar.right.tab.files.actions',挂文件树)

    查询应用=路径控制器.查询应用
    打开这一路径=路径控制器.打开路径
    加载桌面=路径控制器.加载

    def 路径注入():
        '文档预览两处共用的桌面查询和打开'
        return {
            'hooks':{'openInAppDesktop':路径控制器.桌面},
            'loadDesktop':加载桌面,
            'openPath':打开这一路径,
            'applications':查询应用,
        }

    def 挂文档动作():
        '登记文档头上的打开按钮'
        return 上下文.slots.register({
            'name':'sidebar.right.tab.document.actions',
            'id':'open-in-app',
            'locale':命名空间,
            'inject':路径注入,
        },打开路径动作.打开路径动作)

    上下文.slots.inject('sidebar.right.tab.document.actions',挂文档动作)

    def 挂不可预览():
        '登记不能预览时的打开按钮'
        return 上下文.slots.register({
            'name':'sidebar.right.tab.document.unpreviewable',
            'id':'open-in-app',
            'locale':命名空间,
            'inject':路径注入,
        },打开路径空动作.打开路径空动作)

    上下文.slots.inject('sidebar.right.tab.document.unpreviewable',挂不可预览)

    def 挂投递文件():
        '登记投递文件上的打开按钮'
        return 上下文.slots.register({
            'name':'deliverables.file.actions',
            'id':'open-in-app',
            'locale':命名空间,
        },文件路由动作.文件路由动作)

    上下文.slots.inject('deliverables.file.actions',挂投递文件)

    def 挂审阅文件():
        '登记变更审阅文件上的打开按钮'
        return 上下文.slots.register({
            'name':'deliverables.review.file.actions',
            'id':'open-in-app',
            'locale':命名空间,
        },文件路由动作.文件路由动作)

    上下文.slots.inject('deliverables.review.file.actions',挂审阅文件)


inject=依赖
apply=应用
