from . import (
    文案,
    面,
    终端主题,
    终端光标,
    终端图标,
    终端引导,
    终端体,
    终端标题,
    终端恢复,
    终端清理,
    惰性终端体,
)
from .文案 import 命名空间,中文,英文
from .终端图标 import 终端作品
from .终端引导 import 终端引导 as 终端引导类
from .终端标题 import 终端标题 as 终端标题类
from .惰性终端体 import 惰性终端体 as 惰性终端体类

__all__=[
    '依赖','应用','命名空间','文案','面','终端主题','终端光标','终端图标',
    '终端引导','终端体','终端标题','终端恢复','终端清理','惰性终端体',
]

依赖=['slots','locale','sidebarRight','sidebarRightTabs','webTerminals','theme','shortcuts']

def 应用(上下文,配置=None):
    '登记终端类型、快捷键、可观察视图和侧栏席位'
    def 窗口持有():
        '订阅打开的页签，只保留终端'
        def 同步():
            '过滤 terminal 种类'
            打开=上下文.sidebarRight.打开标签.getSnapshot()
            终端页=[]
            for 标签 in 打开:
                if 标签['kind']=='terminal':
                    终端页.append(标签)
            上下文.webTerminals.保留标签(终端页)
        退订=上下文.sidebarRight.打开标签.subscribe(同步)
        同步()
        def 拆除():
            '退订并清空持有'
            退订()
            上下文.webTerminals.保留标签([])
        return 拆除
    上下文.副作用(窗口持有,'ui-sidebar-terminal.window-holds')

    def 目标(会话标识,键):
        '这一出现的导航参数'
        快照=上下文.sidebarRight.标签域.出现(会话标识,{'id':键})['navigation'].getSnapshot()
        if 'params' in 快照:
            return 快照['params']
        return None

    def 终端标识(会话标识,键):
        '参数里有 terminalId 才返回'
        参数=目标(会话标识,键)
        if 参数 is not None and 'terminalId' in 参数:
            return 参数['terminalId']
        return None

    def 视图(会话标识,键):
        '按出现键解析模型'
        参数=目标(会话标识,键)
        壳=None
        if 参数 is not None and 'shellPath' in 参数:
            壳=参数['shellPath']
        导航=上下文.sidebarRight.标签域.出现(会话标识,{'id':键})['navigation'].getSnapshot()
        return 上下文.webTerminals.视图(会话标识,键,导航['address'],终端标识(会话标识,键),壳)

    包标识='@deepseek-ai/dsh-client-ui-sidebar-terminal'

    def 登记快捷():
        'Ctrl+` 新建终端'
        def 标签():
            '命令名称'
            return '新建终端'

        def 解析(面):
            '没有当前会话就挡住，否则打开终端页'
            元素=面['target'] if isinstance(面,dict) and 'target' in 面 else None
            if 元素 is None:
                目标点=上下文.sidebarRight.命令目标()
            else:
                目标点=上下文.sidebarRight.命令目标(元素)
            if 目标点 is None:
                return {'status':'blocked','reason':'请先选择会话'}

            def 跑():
                '从当前目标打开终端'
                上下文.sidebarRight.从目标打开标签('terminal',目标点)

            return {'status':'handled','run':跑}

        return 上下文.shortcuts.register({
            'id':'terminal.new',
            'label':标签,
            'aliases':['new terminal','shell'],
            'defaults':{
                'desktop:macos':{'code':'Backquote','modifiers':['control']},
                'desktop:windows':{'code':'Backquote','modifiers':['control']},
                'desktop:linux':{'code':'Backquote','modifiers':['control']},
                'web:macos':{'code':'Backquote','modifiers':['control']},
                'web:windows':{'code':'Backquote','modifiers':['control']},
            },
            'regions':['page','editable','terminal'],
            'modals':[],
            'resolve':解析,
        })
    上下文.副作用(登记快捷,'ui-sidebar-terminal: shortcut')

    def 登记词典():
        '留下中英文案表。界面显示不读英文表'
        return 上下文.locale.register(命名空间,{'zh':中文,'en':英文})
    上下文.副作用(登记词典,'ui-sidebar-terminal.copy')

    def 登记类型():
        'terminal 可多开'
        def 标题文():
            '页签类型名'
            return '终端'

        def 新建文():
            '向导标题'
            return '新建终端'

        def 说明文():
            '向导说明'
            return '在会话工作区运行命令'

        return 上下文.sidebarRightTabs.登记({
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
                'icon':终端作品,
            }],
        })
    上下文.副作用(登记类型,'ui-sidebar-terminal.type')

    def 登记关闭():
        '关页时结束这一路终端'
        def 关闭(会话标识,标签):
            '同步安排清理'
            上下文.webTerminals.关闭(会话标识,标签['id'],标签['contentId'],终端标识(会话标识,标签['id']))
        return 上下文.sidebarRight.登记关闭钩('terminal',关闭)
    上下文.副作用(登记关闭,'ui-sidebar-terminal.close')

    def 注入面(会话标识):
        'view 与 keyedHooks'
        def 取视图(键):
            '该出现的模型'
            return 视图(会话标识,键)

        def 取状态(键):
            '模型状态钩'
            return 视图(会话标识,键).状态

        return {'view':取视图,'keyedHooks':{'terminal':取状态}}

    class 主题钩子:
        '主题快照源'
        def getSnapshot(自身):
            '当前主题'
            return 上下文.theme.取主题()

        def subscribe(自身,监听):
            '订 theme/change，返回退订'
            def 接到(*参数):
                '钩子不看事件参数'
                监听()
            return 上下文.监听('theme/change',接到)

    主题钩=主题钩子()

    def 挂引导():
        'guide.entry 席位'
        def 登记引导():
            '注入壳列表、偏好和快捷键目录'
            def 注入引导(会话标识):
                '发现与偏好写入'
                def 载壳(信号):
                    '读宿主壳列表'
                    return 上下文.webTerminals.启动命令解释器(会话标识,信号)

                def 选壳(路径):
                    '记下一次偏好'
                    上下文.webTerminals.选择命令解释器(路径)

                return {
                    'hooks':{'shortcuts':上下文.shortcuts.catalog},
                    'loadShells':载壳,
                    'selectShell':选壳,
                }
            return 上下文.slots.register({
                'name':'sidebar.right.tab.guide.entry',
                'key':包标识,
                'locale':命名空间,
                'inject':注入引导,
            },终端引导类)
        return 上下文.slots.inject('sidebar.right.tab.guide.entry',登记引导)
    上下文.副作用(挂引导,'ui-sidebar-terminal.guide')

    def 挂正文():
        'pane.tab 席位'
        def 登记正文():
            '注入面加主题钩'
            def 注入正文(会话标识):
                '合成 view 与 theme'
                基=注入面(会话标识)
                基['hooks']={'theme':主题钩}
                return 基
            return 上下文.slots.register({
                'name':'sidebar.right.pane.tab',
                'key':包标识,
                'locale':命名空间,
                'inject':注入正文,
            },惰性终端体类)
        return 上下文.slots.inject('sidebar.right.pane.tab',登记正文)
    上下文.副作用(挂正文,'ui-sidebar-terminal.body')

    def 挂标题():
        'pane.tab.title 席位'
        def 登记标题():
            '注入共用面'
            return 上下文.slots.register({
                'name':'sidebar.right.pane.tab.title',
                'key':包标识,
                'locale':命名空间,
                'inject':注入面,
            },终端标题类)
        return 上下文.slots.inject('sidebar.right.pane.tab.title',登记标题)
    上下文.副作用(挂标题,'ui-sidebar-terminal.title')

inject=依赖
apply=应用
