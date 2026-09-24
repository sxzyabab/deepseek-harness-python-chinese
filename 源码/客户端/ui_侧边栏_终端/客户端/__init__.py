from .文案 import 命名空间,中文,英文#词表
from .终端图标 import 终端引导图标#开始页图标
from .终端引导 import 终端引导#开始页卡片
from .终端体 import 终端体#正文
from .终端标题 import 终端标题#页签标题

__all__=['依赖','应用','终端引导','终端体','终端标题','命名空间','中文','英文']

依赖=['slots','locale','sidebarRight','sidebarRightTabs','webTerminals','theme']#槽、文案、侧栏、终端、主题

def 应用(上下文):
    """登记终端类型、可观察视图；恢复与清理席位已从本包卸下。"""
    def 窗口持有():
        """订阅 openTabs 并 retainTabs。"""
        def 同步():
            """过滤 terminal 种类。"""
            打开=上下文.sidebarRight.openTabs.getSnapshot()
            上下文.webTerminals.retainTabs([标签 for 标签 in 打开 if 标签.get('kind')=='terminal' or getattr(标签,'kind',None)=='terminal'])
        退订=上下文.sidebarRight.openTabs.subscribe(同步)
        同步()
        def 拆除():
            """退订并清空持有。"""
            退订()
            上下文.webTerminals.retainTabs([])
        return 拆除
    上下文.副作用(窗口持有,'ui-sidebar-terminal.window-holds')
    def 目标(会话标识,键):
        """terminal 出现域的 params。"""
        return 上下文.sidebarRight.tabDomain.occurrence(会话标识,{'id':键}).navigation.getSnapshot()['params']
    def 终端标识(会话标识,键):
        """params 含 terminalId 才返回。"""
        参数=目标(会话标识,键)
        if 参数 is not None and 'terminalId' in 参数:
            return 参数['terminalId']
        return None
    def 视图(会话标识,键):
        """按出现键解析模型。"""
        参数=目标(会话标识,键)
        壳路径=参数['shellPath'] if 参数 is not None and 'shellPath' in 参数 else None
        导航=上下文.sidebarRight.tabDomain.occurrence(会话标识,{'id':键}).navigation.getSnapshot()
        内容标识=导航['address'] if 'address' in 导航 else None
        return 上下文.webTerminals.view(会话标识,键,内容标识,终端标识(会话标识,键),壳路径)
    包标识='@deepseek-ai/dsh-client-ui-sidebar-terminal'
    翻译=上下文.locale.bind(命名空间)
    def 登记词典():
        """写 locale。"""
        return 上下文.locale.register(命名空间,{'zh':中文,'en':英文})
    上下文.副作用(登记词典,'ui-sidebar-terminal.copy')
    def 登记类型():
        """terminal 可多开。"""
        def 标题文():
            """终端。"""
            return 翻译('title')
        def 新建文():
            """新建终端。"""
            return 翻译('new')
        def 说明文():
            """工作区命令。"""
            return 翻译('description')
        return 上下文.sidebarRightTabs.register({
            'id':包标识,
            'kind':'terminal',
            'multiple':True,
            'priority':'builtin',
            'title':标题文,
            'guide':[{
                'id':'new',
                'order':20,
                'title':新建文,
                'description':说明文,
                'icon':终端引导图标,
            }],
        })
    上下文.副作用(登记类型,'ui-sidebar-terminal.type')
    def 登记关闭():
        """关标签即关进程。"""
        def 关闭(会话标识,标签):
            """同步安排清理。"""
            上下文.webTerminals.close(会话标识,标签['id'],标签.get('contentId'),终端标识(会话标识,标签['id']))
        return 上下文.sidebarRight.registerCloseHandler('terminal',关闭)
    上下文.副作用(登记关闭,'ui-sidebar-terminal.close')
    def 注入面(会话标识):
        """view 与 keyedHooks。"""
        def 取视图(键):
            """该出现的模型。"""
            return 视图(会话标识,键)
        def 取状态(键):
            """模型 state 钩。"""
            return 视图(会话标识,键).state
        return {'view':取视图,'keyedHooks':{'terminal':取状态}}
    def 取主题快照():
        """当前主题。"""
        return 上下文.theme.getTheme()
    def 订主题(监听):
        """订 theme/change。"""
        return 上下文.on('theme/change',监听)
    主题钩={'getSnapshot':取主题快照,'subscribe':订主题}
    def 挂引导():
        """guide.entry 席位。"""
        def 登记引导():
            """注入 loadShells 与 selectShell。"""
            def 注入引导(会话标识):
                """发现与偏好写入。"""
                def 载壳(信号):
                    """读宿主壳列表。"""
                    return 上下文.webTerminals.launchShells(会话标识,信号)
                def 选壳(路径):
                    """写下一次偏好。"""
                    上下文.webTerminals.selectShell(路径)
                return {'loadShells':载壳,'selectShell':选壳}
            return 上下文.slots.register({
                'name':'sidebar.right.tab.guide.entry',
                'key':包标识,
                'locale':命名空间,
                'inject':注入引导,
            },终端引导)
        return 上下文.slots.inject('sidebar.right.tab.guide.entry',登记引导)
    上下文.副作用(挂引导,'ui-sidebar-terminal.guide')
    def 挂正文():
        """pane.tab 席位。"""
        def 登记正文():
            """注入面加主题钩。"""
            def 注入正文(会话标识):
                """合成 view 与 theme。"""
                基=注入面(会话标识)
                基['hooks']={'theme':主题钩}
                return 基
            return 上下文.slots.register({
                'name':'sidebar.right.pane.tab',
                'key':包标识,
                'locale':命名空间,
                'inject':注入正文,
            },终端体)
        return 上下文.slots.inject('sidebar.right.pane.tab',登记正文)
    上下文.副作用(挂正文,'ui-sidebar-terminal.body')
    def 挂标题():
        """pane.tab.title 席位。"""
        def 登记标题():
            """注入共用面。"""
            return 上下文.slots.register({
                'name':'sidebar.right.pane.tab.title',
                'key':包标识,
                'locale':命名空间,
                'inject':注入面,
            },终端标题)
        return 上下文.slots.inject('sidebar.right.pane.tab.title',登记标题)
    上下文.副作用(挂标题,'ui-sidebar-terminal.title')

inject=依赖
apply=应用
