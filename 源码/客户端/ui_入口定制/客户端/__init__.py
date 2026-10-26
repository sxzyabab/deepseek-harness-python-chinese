from ....客户端.存储 import 创建快照存储
from . import 入口菜单内容,文案
from .入口菜单内容 import 入口菜单内容 as 入口菜单内容类
from .文案 import 中文,中文句,俄文,德文,日文,法文,英文,西班牙文,葡萄牙文

__all__=['入口菜单内容','文案','名称','依赖','应用']

名称='ui-entry-customization'
命名空间='entryCustomization'
依赖=['slots','locale','uiWorkspace']

def 应用(上下文,配置=None):
    '把同一组菜单行登记进三个区域的更多菜单'
    def 登记词典():
        '挂上各语言文案。看得见的字走中文表'
        return 上下文.locale.register(命名空间,{
            'en':英文,'zh':中文,'ja':日文,'es':西班牙文,'fr':法文,'de':德文,'ru':俄文,'pt':葡萄牙文,
        })
    上下文.副作用(登记词典)
    导航在场=创建快照存储(False)
    def 跟随导航(作用域):
        '插件页提供导航时才显示浏览一行'
        def 登记():
            '在场时为真，卸下时为假'
            导航在场.set(True)
            def 离开():
                '导航服务离开'
                导航在场.set(False)
            return 离开
        作用域.副作用(登记,'entry-customization: plugin navigation presence')
    上下文.inject(['pluginNavigation'],跟随导航)
    def 注入(区域):
        '这一区域的身份和两个动作'
        def 浏览插件():
            '打开插件页主列表。有埋点才上报'
            埋点=上下文.get('productAnalytics')
            if 埋点 is not None:
                埋点.track('more_menu_item_click',{'region':区域,'action':'browse_plugins'})
            导航=上下文.get('pluginNavigation')
            if 导航 is not None:
                导航.openList()
        def 创造插件():
            '用这一区域的中文提示准备草稿，不发送'
            埋点=上下文.get('productAnalytics')
            if 埋点 is not None:
                埋点.track('more_menu_item_click',{'region':区域,'action':'create_plugin'})
            上下文.uiWorkspace.startSession(None,{
                'agentPreset':'cordis',
                'prompt':中文句('createPrompt.'+区域),
                'whenDraftExists':'append',
            })
        return {
            'region':区域,
            'hooks':{'pluginNavigation':导航在场},
            'browsePlugins':浏览插件,
            'createPlugin':创造插件,
        }
    def 注入侧栏():
        '侧栏区域'
        return 注入('sidebar')
    def 挂侧栏():
        '左侧栏更多菜单'
        return 上下文.slots.register({
            'name':'sidebar.panellist.actions',
            'id':'entry-customization',
            'locale':命名空间,
            'inject':注入侧栏,
        },入口菜单内容类)
    def 注入会话():
        '会话区域'
        return 注入('conversation')
    def 挂会话():
        '会话视图更多菜单'
        return 上下文.slots.register({
            'name':'conversation.session.header.views.actions',
            'id':'entry-customization',
            'locale':命名空间,
            'inject':注入会话,
        },入口菜单内容类)
    def 注入右栏():
        '右栏区域'
        return 注入('rightbar')
    def 挂右栏():
        '右栏起始页更多菜单'
        return 上下文.slots.register({
            'name':'sidebar.right.tab.guide.actions',
            'id':'entry-customization',
            'locale':命名空间,
            'inject':注入右栏,
        },入口菜单内容类)
    上下文.slots.inject('sidebar.panellist.actions',挂侧栏)
    上下文.slots.inject('conversation.session.header.views.actions',挂会话)
    上下文.slots.inject('sidebar.right.tab.guide.actions',挂右栏)

inject=依赖
name=名称
apply=应用
default=应用
