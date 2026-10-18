from ...模块.客户端.通告 import 取握手窗口
from .文案 import 中文,英文
from .约定.槽位 import (
    右侧侧栏词表命名空间,
    席名右栏,
    席名右栏会话,
    席名右侧签正文,
    席名右侧签标题,
    席名右侧向导,
    席名右侧向导条目,
    席名右侧签菜单项,
    席名头部角,
)
from .约定.种子 import 默认种子
from .存储 import 创建右侧侧栏存储
from .服务 import 创建右侧侧栏控制器
from .标签注册表 import 右侧侧栏标签注册表
from .标签信息 import 标签信息工厂,向导标签信息工厂
from .会话视图集 import 侧栏会话视图集
from .焦点 import 观察侧栏焦点
from .快捷键 import 登记右侧侧栏快捷键
from .壳.关闭焦点 import 打开并聚焦窗格,关闭并聚焦窗格
from .壳.右侧侧栏 import 右栏席
from .壳.右栏根 import 右栏根
from .壳.展开按钮 import 展开按钮
from .标签.向导.定义 import 向导标识,向导定义
from .标签.向导.向导体 import 向导体
from .标签.向导.向导标题 import 向导标题
from . import (
    会话视图,
    会话视图集,
    停靠文案,
    存储,
    快捷键,
    持久化,
    文案,
    服务,
    标签信息,
    标签域,
    标签注册表,
    标签清单,
    焦点,
    约定,
    壳,
    标签,
)

__all__=[
    '依赖','应用','命名空间',
    '文案','停靠文案','约定','壳','标签',
    '存储','服务','标签注册表','标签信息','标签清单','标签域',
    '会话视图','会话视图集','焦点','快捷键','持久化',
]

命名空间=右侧侧栏词表命名空间
依赖=['slots','layout','locale','resources','sessions','uiSession','shortcuts']


def _读快照(源):
    '字典面或对象面的 getSnapshot'
    if isinstance(源,dict):
        return 源['getSnapshot']()
    return 源.getSnapshot()


def _订阅(源,回调):
    '字典面或对象面的 subscribe'
    if isinstance(源,dict):
        return 源['subscribe'](回调)
    return 源.subscribe(回调)


def 应用(上下文,配置=None):
    '提供登记表和导航，挂右栏、展开钮和向导'
    标签表=右侧侧栏标签注册表(上下文)
    视图集=侧栏会话视图集(上下文.sessions)

    def 装视图():
        '跟当前会话选择，后台视图继续留着'
        当前=上下文.uiSession.adapter['current'] if isinstance(上下文.uiSession.adapter,dict) else 上下文.uiSession.adapter.current

        def 同步():
            '选择现在这份会话'
            快照=_读快照(当前)
            键=None
            if isinstance(快照,dict):
                键=快照.get('key')
            elif 快照 is not None:
                键=getattr(快照,'key',None)
            视图集.选择(键)

        退订=_订阅(当前,同步)
        同步()

        def 拆除():
            '退订并放掉全部视图'
            退订()
            视图集.拆除()

        return 拆除

    上下文.副作用(装视图,'ui-sidebar-right: retained Session views')
    布局=上下文.layout
    自动全屏=[False]

    def 读自动全屏():
        '席最后一次报上来的窄视口规则'
        return 自动全屏[0]

    def 打开聚焦(会话标识,打开):
        '提交打开后再聚焦窗格'
        打开并聚焦窗格(取握手窗口().document,会话标识,打开)

    def 关闭聚焦(会话标识,窗格标识,关闭):
        '提交关闭后再聚焦还在的窗'
        关闭并聚焦窗格(取握手窗口().document,会话标识,窗格标识,关闭)

    def 钉住(地址,信号):
        '出现次活着就钉住资源'
        上下文.resources.钉住(地址,信号)

    双件=创建右侧侧栏控制器(标签表,钉住,{
        'autoFullscreen':读自动全屏,
        'openWithFocus':打开聚焦,
        'closeWithFocus':关闭聚焦,
    })
    控制器=双件['controller']
    认领=双件['adopt']
    遗忘=双件['forget']
    显示=双件['show']
    测量=双件['measure']

    def 装在屏():
        '主列是对话时，选中的会话就是在屏会话'
        def 同步():
            '面板盖住主列时没有在屏会话'
            选中=None
            for 视图 in 视图集.源.getSnapshot():
                if 视图.get('selected') is True:
                    选中=视图
                    break
            面板=_读快照(布局.panelInfo)
            主列空=isinstance(面板,dict) and 面板.get('activePanelId') is None
            if 主列空 and 选中 is not None:
                显示(选中.get('sessionId'))
            else:
                显示(None)

        退视图=_订阅(视图集.源,同步)
        退面板=_订阅(布局.panelInfo,同步)
        同步()

        def 拆除():
            '卸掉订阅，并清掉在屏会话'
            退视图()
            退面板()
            显示(None)

        return 拆除

    上下文.副作用(装在屏,'ui-sidebar-right: on-screen Session')
    拆登记=上下文.反射.提供服务('sidebarRightTabs',标签表)
    拆服务=上下文.反射.提供服务('sidebarRight',控制器)

    def 装服务面():
        '席都卸了之后再拆这两张脸'
        def 拆除():
            '中止出现次，再撤服务'
            控制器.标签域.拆除()
            拆服务()
            拆登记()

        return 拆除

    上下文.副作用(装服务面,'ui-sidebar-right: service faces')

    def 登记词典():
        '中英文案都登记。界面只读中文表'
        return 上下文.locale.register(命名空间,{'zh':中文,'en':英文})

    上下文.副作用(登记词典,'ui-sidebar-right: dictionaries')

    def 装快捷键():
        '命令对着当前页面'
        def 关窗口():
            '关窗口失败只记到控制台'
            try:
                上下文.shortcuts.closeWindow()
            except Exception as 错误:
                取握手窗口().console.error('Window close failed',错误)

        return 登记右侧侧栏快捷键(上下文.shortcuts,控制器,None,关窗口)

    上下文.副作用(装快捷键,'ui-sidebar-right: shortcuts')

    def 装焦点():
        '跟着文档焦点'
        return 观察侧栏焦点(取握手窗口().document)

    上下文.副作用(装焦点,'ui-sidebar-right: focus')

    def 挂席与向导():
        '一个存储挂两席，再按公开路径登记向导'
        def 取种子():
            '现读默认页'
            return 默认种子(标签表)

        规格=创建右侧侧栏存储(取种子)
        认领表={}
        原创建=规格.create

        def 创建(作用域键=None):
            '铸出来就认领。清持久化时忘掉清单'
            实例=原创建(作用域键)
            if 作用域键 is not None:
                旧=认领表.get(作用域键)
                if 旧 is not None:
                    旧()
                认领表[作用域键]=认领(作用域键,实例)
            原清=实例.clearPersisted

            def 清持久化():
                '删布局，再忘掉这个作用域'
                原清()
                if 作用域键 is not None:
                    遗忘(作用域键)

            实例.clearPersisted=清持久化
            return 实例

        规格.create=创建

        def 同步呈现(呈现):
            '告诉框架这一栏现在怎么占位'
            if 呈现.get('shown'):
                布局.openRightbar(呈现.get('track'),呈现.get('fullscreen'))
            else:
                布局.closeRightbar()

        def 报自动全屏(值):
            '窄视口规则，给全屏命令读'
            自动全屏[0]=值

        def 分栏(窗格标识):
            '和快捷键同一条路'
            控制器.分栏(窗格标识)

        def 切换全屏():
            '有目标才切换'
            目标=控制器.命令目标()
            if 目标 is not None:
                控制器.切换全屏(目标)

        def 开标签(种类,选项=None):
            '加号走公开的打开'
            控制器.打开标签(种类,选项)

        注入={
            'syncPresentation':同步呈现,
            'reportAutoFullscreen':报自动全屏,
            'splitPane':分栏,
            'toggleFullscreen':切换全屏,
            'openTab':开标签,
            'hooks':{
                'shortcuts':上下文.shortcuts.catalog,
                'tabTypes':{
                    'subscribe':lambda 监听: 标签表.订阅(监听),
                    'getSnapshot':lambda: 标签表.条目(),
                },
            },
        }
        拆除类型=[标签表.登记(向导定义())]

        def 挂右栏():
            '根席和会话席'
            yield 上下文.slots.register({
                'name':席名右栏,
                'children':{席名右栏会话:{'kind':'single','scope':'session'}},
                'inject':lambda: {
                    'hooks':{'views':视图集.源},
                    'mountView':lambda 引用: 视图集.挂载(引用),
                },
            },右栏根)

            def 会话注入(会话标识):
                '这一会话的关闭、测量和出现次'
                def 量(能分):
                    '宽度够不够分栏'
                    测量(会话标识,能分)

                def 关签(标签标识):
                    '清理失败只记到控制台，签留着'
                    try:
                        控制器.在会话关闭(会话标识,标签标识)
                    except Exception as 错误:
                        取握手窗口().console.error('Sidebar tab close failed:',错误)

                def 导航(键):
                    '这张签的导航快照'
                    return 控制器.标签域.出现(会话标识,{'id':键})['navigation']

                def 出现(签):
                    '已提交的出现次'
                    return 控制器.标签域.出现(会话标识,签)

                面=dict(注入)
                面['measureRoom']=量
                面['closeTab']=关签
                面['keyedHooks']={'tabNavigation':导航}
                面['occurrence']=出现
                return 面

            yield 上下文.slots.register({
                'name':席名右栏会话,
                'locale':命名空间,
                'children':{
                    席名右侧签正文:{'kind':'keyed','scope':'session','inject':{'hooks':{'tabInfo':标签信息工厂}}},
                    席名右侧签标题:{'kind':'keyed','scope':'session','inject':{'hooks':{'tabInfo':标签信息工厂}}},
                    席名右侧签菜单项:{'kind':'list','scope':'session'},
                },
                'store':规格,
                'inject':会话注入,
            },右栏席)

        拆席=上下文.slots.inject(席名右栏,挂右栏)

        def 挂展开():
            '标题角上的打开按钮，用同一份存储'
            return 上下文.slots.register({
                'name':席名头部角,
                'locale':命名空间,
                'store':规格,
                'inject':lambda: {'hooks':{'shortcuts':上下文.shortcuts.catalog}},
            },展开按钮)

        拆展开=上下文.slots.inject(席名头部角,挂展开)
        向导注入={
            'hooks':{
                'shortcuts':上下文.shortcuts.catalog,
                'guideEntries':{
                    'subscribe':lambda 监听: 标签表.订阅(监听),
                    'getSnapshot':lambda: 标签表.向导(),
                },
            },
        }

        def 挂向导():
            '向导正文'
            return 上下文.slots.register({
                'name':席名右侧签正文,
                'key':向导标识,
                'children':{
                    席名右侧向导条目:{
                        'kind':'keyed','scope':'session','inject':{'hooks':{'tabInfo':向导标签信息工厂}},
                    },
                    席名右侧向导:{
                        'kind':'chain','scope':'session','inject':{'hooks':{'tabInfo':向导标签信息工厂}},
                    },
                },
                'inject':lambda: 向导注入,
            },向导体)

        拆向导=上下文.slots.inject(席名右侧签正文,挂向导)

        def 挂向导标题():
            '向导芯片'
            return 上下文.slots.register({
                'name':席名右侧签标题,
                'key':向导标识,
            },向导标题)

        拆标题=上下文.slots.inject(席名右侧签标题,挂向导标题)

        def 拆除():
            '先摘标题和向导，再摘席，最后放掉认领'
            拆标题()
            拆向导()
            拆展开()
            拆席()
            for 拆 in reversed(拆除类型):
                拆()
            for 释放 in list(认领表.values()):
                释放()
            认领表.clear()

        return 拆除

    上下文.副作用(挂席与向导,'ui-sidebar-right: seats and shipped tab type')


inject=依赖
apply=应用
