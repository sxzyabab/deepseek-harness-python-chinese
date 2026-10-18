from . import (
    主题呈现,
    列宽,
    存储,
    应用帧,
    快捷键文案,
    文档标题,
    服务,
)

__all__=[
    '依赖','应用','布局控制器',
    '主题呈现','列宽','存储','应用帧','快捷键文案','文档标题','服务',
]

依赖=['slots','theme','locale','shortcuts']#槽位、主题、文案、快捷键
布局控制器=服务.布局控制器#根上对外的布局面


def 应用(上下文,配置=None):
    '提供 layout，把三列帧登记进 root，并把主题快照写到文档上'
    def 登记词典():
        '登记布局命令的中英文案表。快捷键上显示的字不走英文表'
        return 上下文.locale.register('shortcuts.layout',{
            'zh':快捷键文案.中文,
            'en':快捷键文案.英文,
        })
    上下文.副作用(登记词典,'layout: command labels')

    def 装服务与根():
        '挂 layout，声明子槽，并把应用帧放进 root'
        句柄=存储.创建布局存储()
        实例=句柄.create()

        def 复用():
            '渲染器再取存储时仍是这一份'
            return 实例

        句柄.create=复用

        def 有主面板(标识):
            '主槽里有没有这个键'
            for 条目 in 上下文.slots.entries('main'):
                选项=条目['options']
                if 'key' in 选项 and 选项['key']==标识:
                    return True
            return False

        def 保留主面板():
            '主槽还在的键留下，已经撤掉的活动面板回到对话'
            键列表=[]
            for 条目 in 上下文.slots.entries('main'):
                选项=条目['options']
                if 'key' in 选项 and 选项['key'] is not None:
                    键列表.append(选项['key'])
            实例.actions['retainMainPanels'](键列表)

        面板信息=服务.面板信息源(实例)
        布局=服务.布局控制器(实例.actions,有主面板,面板信息)
        拆面板信息=上下文.slots.provideRoot({'hooks':{'panelInfo':布局.panelInfo}})
        拆服务=上下文.反射.提供服务('layout',布局)
        拆登记=上下文.slots.register({
            'name':'root',
            'locale':'common',
            'children':{
                'sidebar':{'kind':'single','scope':'root'},
                'main':{'kind':'keyed','scope':'root'},
                'rightbar':{'kind':'single','scope':'root'},
                'shell.bottom':{'kind':'single','scope':'root'},
                'shell.overlay':{'kind':'list','scope':'root'},
                'shell.leading':{'kind':'single','scope':'root'},
            },
            'store':句柄,
        },应用帧.应用帧)

        def 左栏开关标签():
            '左栏开关显示中文表里的原文'
            return 快捷键文案.中文['toggle']

        def 跑切换():
            '收起或展开左栏'
            布局.切换侧栏()

        def 解析切换():
            '快捷键命中后执行切换'
            return {'status':'handled','run':跑切换}

        拆快捷键=上下文.shortcuts.register({
            'id':'sidebar.left.toggle',
            'label':左栏开关标签,
            'aliases':['sidebar','toggle left sidebar'],
            'defaults':{
                'desktop:macos':{'code':'KeyB','modifiers':['primary']},
                'desktop:windows':{'code':'KeyB','modifiers':['primary']},
                'desktop:linux':{'code':'KeyB','modifiers':['primary']},
                'web:macos':{'code':'KeyB','modifiers':['primary','alt']},
                'web:windows':{'code':'KeyB','modifiers':['primary','alt']},
            },
            'regions':['page','editable'],
            'modals':[],
            'resolve':解析切换,
        })
        拆面板=上下文.slots.subscribe('main',保留主面板)
        保留主面板()

        def 拆除():
            '按登记的反序卸掉快捷键、导航、主槽订阅、根帧、面板源和 layout'
            拆快捷键()
            布局.拆除()
            拆面板()
            拆登记()
            拆面板信息()
            拆服务()

        return 拆除

    上下文.副作用(装服务与根,'ui-layout: service + root registration')

    def 装主题():
        '先写当前主题，再听 theme/change'
        呈现=主题呈现.主题呈现器()
        呈现.施加(上下文.theme.取主题())

        def 变更(快照):
            '主题变化时重写文档'
            呈现.施加(快照)

        关=上下文.监听('theme/change',变更)

        def 拆除():
            '卸掉监听，并收回这次写上的属性'
            关()
            呈现.拆除()

        return 拆除

    上下文.副作用(装主题,'ui-layout: theme presenter')


inject=依赖
apply=应用
