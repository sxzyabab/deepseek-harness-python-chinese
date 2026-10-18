from ...存储 import 创建快照存储
from ...ui_槽位 import 解析槽标签
from . import 约定,文案,侧栏根,头部前置控件

__all__=['依赖','应用','命名空间','约定','文案','侧栏根','头部前置控件']

命名空间='sidebar'
依赖=['slots','layout','uiWorkspace','locale','shortcuts']

def 应用(上下文,配置=None):
    '登记侧栏文案、同步全局面板，并注入侧栏列和窗框左上控件'
    def 登记词典():
        '登记本包中英文案'
        return 上下文.locale.register(命名空间,{'zh':文案.中文,'en':文案.英文})
    上下文.副作用(登记词典,'ui-sidebar: dictionaries')
    面板=创建快照存储([])
    def 同步面板():
        '从 sidebar.panellist 的胜出条目重建元数据'
        下一批=[]
        for 条目 in 上下文.slots.entriesOfSlot('sidebar.panellist'):
            选项=条目['options']
            身份=选项['id']
            序=选项['order'] if 'order' in 选项 else None
            if 序 is None:
                序=0
            标签源=选项['label'] if 'label' in 选项 else None
            标签=解析槽标签(标签源)
            if 标签 is None:
                标签=身份
            下一批.append({'id':身份,'order':序,'label':标签})
        def 行序(行):
            '按 order 升序，平局保持登记顺序'
            return 行['order']
        下一批.sort(key=行序)
        上一=面板.getSnapshot()
        if len(上一)==len(下一批):
            相同=True
            下标=0
            while 下标<len(上一):
                旧=上一[下标]
                新=下一批[下标]
                if 旧['id']!=新['id'] or 旧['order']!=新['order'] or 旧['label']!=新['label']:
                    相同=False
                    break
                下标=下标+1
            if 相同 is True:
                return
        面板.set(下一批)
    def 订面板条目():
        '面板登记变化时重算'
        return 上下文.slots.subscribe('sidebar.panellist',同步面板)
    上下文.副作用(订面板条目,'ui-sidebar: panel entries')
    def 订面板文案():
        '语言切换时重算面板标签'
        return 上下文.locale.subscribe(同步面板)
    上下文.副作用(订面板文案,'ui-sidebar: panel labels')
    def 注入面():
        '开新会话、切换侧栏、选面板，以及面板和快捷键两个钩子'
        def 开新会话(工作区标识=None):
            '交给工作区 UI。不传工作区时沿用当前会话，再退到最近的'
            上下文.uiWorkspace.startSession(工作区标识)
        def 切换侧栏():
            '交给布局服务折叠或展开'
            上下文.layout.toggleSidebar()
        def 选面板(身份):
            '插件和日程各记一次点击，然后交给布局选中主面板'
            if 身份=='plugins' or 身份=='schedules':
                分析=上下文.获取服务('productAnalytics',False)
                if 分析 is not None:
                    菜单名='plugin' if 身份=='plugins' else 'cron'
                    分析.track('sidebar_menu_click',{'menu_name':菜单名})
            上下文.layout.selectPanel(身份)
        return {
            'startSession':开新会话,
            'toggleSidebar':切换侧栏,
            'selectPanel':选面板,
            'hooks':{
                'panels':面板,
                'shortcuts':上下文.shortcuts.catalog,
            },
        }
    def 挂槽():
        '声明侧栏子槽并登记侧栏根'
        return 上下文.slots.register({
            'name':'sidebar',
            'locale':命名空间,
            'children':约定.槽位.子槽,
            'inject':注入面,
        },侧栏根.侧栏根)
    上下文.slots.inject('sidebar',挂槽)
    def 挂前置():
        '侧栏完全藏起时，把打开和新建放到窗框左上'
        return 上下文.slots.register({
            'name':'shell.leading',
            'locale':命名空间,
            'inject':注入面,
        },头部前置控件.头部前置控件)
    上下文.slots.inject('shell.leading',挂前置)
    同步面板()

inject=依赖
apply=应用
