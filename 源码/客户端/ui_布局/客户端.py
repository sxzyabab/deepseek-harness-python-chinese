from .存储 import 创建布局存储,布局存储对象#布局存储工厂
from .服务 import 布局控制器
from .异常 import 布局错误
from .主题呈现 import 主题呈现器#主题呈现
from .应用帧 import 根帧#根槽页面
from .快捷键文案 import 中文 as 快捷键中文,英文 as 快捷键英文#侧栏命令文案

__all__=['依赖','应用','布局控制器','布局错误','创建布局存储','主题呈现器']

依赖=['slots','theme','locale','shortcuts']#槽位、主题、文案、快捷键

def 应用(上下文):#安装布局界面浏览器半边
    '提供 ctx.layout，把三栏帧登记进 root，并落座主题呈现器'
    上下文.副作用(lambda: 上下文.locale.register('shortcuts.layout',{'zh':快捷键中文,'en':快捷键英文}),'layout: command labels')#命令文案
    def 装服务与根():#提供 layout
        '挂 layout 服务并把根帧登记进 root'
        句柄=布局存储对象()#共享根实例
        实例={'getSnapshot':句柄.getSnapshot,'subscribe':句柄.subscribe,'actions':句柄.actions}#控制器仍用字典面
        def 有主面板(标识):#检查主槽登记
            '条目 options.key 是否匹配'
            for 条目 in 上下文.slots.entries('main'):#主槽条目
                选项=条目['options'] if isinstance(条目,dict) and 'options' in 条目 else getattr(条目,'options',None)#选项
                键=选项['key'] if isinstance(选项,dict) and 'key' in 选项 else getattr(选项,'key',None) if 选项 is not None else None#键
                if 键==标识:#命中
                    return True#已登记
            return False#未登记
        布局=布局控制器(实例['actions'],有主面板)#控制器
        def 保留主面板():#主槽撤登记时清活动面板
            '收集仍在的键'
            键列表=[]#累积
            for 条目 in 上下文.slots.entries('main'):#主槽
                选项=条目['options'] if isinstance(条目,dict) and 'options' in 条目 else getattr(条目,'options',None)#选项
                键=选项['key'] if isinstance(选项,dict) and 'key' in 选项 else getattr(选项,'key',None) if 选项 is not None else None#键
                if 键 is not None:#有键
                    键列表.append(键)#收下
            实例['actions']['retainMainPanels'](键列表)#清理
        def 取面板信息():#读面板信息快照
            '从共享实例取 panelInfo'
            return 实例['getSnapshot']()['panelInfo']#面板信息
        class 面板信息源:#钩子按属性调用 getSnapshot 和 subscribe
            '把字典面收成对象，供 usePanelInfo 读取'
            def getSnapshot(自身):
                '读 panelInfo'
                return 取面板信息()#面板信息
            def subscribe(自身,回调):
                '订布局变更'
                return 实例['subscribe'](回调)#转发
        面板信息=面板信息源()#宿主可观察
        拆面板信息=上下文.slots.provideRoot({'hooks':{'panelInfo':面板信息}})#提供根钩
        拆服务=上下文.反射.提供服务('layout',布局)#挂 layout
        拆面板=上下文.slots.subscribe('main',保留主面板)#主槽变更
        保留主面板()#首次对齐
        拆登记=上下文.slots.register({#root 槽
            'name':'root',#根
            'locale':'common',#产品文案
            'children':{#子槽
                'sidebar':{'kind':'single','scope':'root'},#左栏
                'main':{'kind':'keyed','scope':'root'},#主面
                'rightbar':{'kind':'single','scope':'root'},#右栏
                'shell.bottom':{'kind':'single','scope':'root'},#底栏
                'shell.overlay':{'kind':'list','scope':'root'},#罩层
                'shell.leading':{'kind':'single','scope':'root'},#窗口控件席
            },#子槽结束
            'store':句柄,#共享布局存储
        },根帧)#三栏帧
        译=上下文.locale.bind('shortcuts.layout')#命令标签
        def 切侧栏():
            '快捷键收起或展开左栏'
            布局.切换侧栏()#转发
        拆快捷键=上下文.shortcuts.register({#左栏开关
            'id':'sidebar.left.toggle',#命令
            'label':lambda: 译('toggle'),#标签
            'aliases':['sidebar','toggle left sidebar'],#别名
            'defaults':{#各平台
                'desktop:macos':{'code':'KeyB','modifiers':['primary']},
                'desktop:windows':{'code':'KeyB','modifiers':['primary']},
                'desktop:linux':{'code':'KeyB','modifiers':['primary']},
                'web:macos':{'code':'KeyB','modifiers':['primary','alt']},
                'web:windows':{'code':'KeyB','modifiers':['primary','alt']},
            },#默认结束
            'regions':['page','editable'],#区域
            'modals':[],#模态
            'resolve':lambda: {'status':'handled','run':切侧栏},#执行
        })#登记结束
        def 拆除():#拆除服务与订阅
            '先撤导航、快捷键和订阅再撤服务'
            拆快捷键()#撤命令
            布局.拆除()#作废导航
            拆面板()#取消订阅
            拆登记()#撤根槽
            拆面板信息()#撤钩
            拆服务()#撤服务
        return 拆除#拆除器
    上下文.副作用(装服务与根,'ui-layout: service + root registration')#服务与 root
    def 装主题呈现():#落座主题呈现器
        '从已解析快照做纯 DOM 写入'
        呈现=主题呈现器()#实例
        呈现.施加(上下文.theme.getTheme())#先投影
        def 变更(快照):#主题变更
            '投影快照'
            呈现.施加(快照)#投影
        关=上下文.监听('theme/change',变更)#监听
        def 拆除():#拆除呈现
            '取消监听并收回写入'
            关()#取消
            呈现.拆除()#收回
        return 拆除#拆除器
    上下文.副作用(装主题呈现,'ui-layout: theme presenter')#主题呈现

inject=依赖#框架槽
apply=应用#框架槽
