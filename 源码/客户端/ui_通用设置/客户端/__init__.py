from ...模块.客户端.通告 import 取握手窗口
from ....基础设施.通用工具 import 获取内部数据
from ...存储 import 声明存储
from ...ui_槽位 import 解析槽标签
from ...ui_基础界面组件.模态层 import 关栈顶模态
from . import 文案
from . import 壳层约定
from . import 壳层
from . import 常规条目分区
from . import 开发者工具行
from . import 当前版本行
from . import 文档存储
from . import 文档动作
from . import 桌面更新
from . import 桌面更新指示器
from . import 宿主版本提示
from . import 设置根

__all__=[
    '文案','壳层约定','壳层','常规条目分区','开发者工具行','当前版本行',
    '文档存储','文档动作','桌面更新','桌面更新指示器','宿主版本提示','设置根',
    '命名空间','依赖','应用',
]

命名空间='settings'
依赖=['slots','locale','connection','remote','remote.settings','configForms','shortcuts','modules']

def 按序(行):
    '分区和引导按 order 升序'
    return 行['order']

def 应用(上下文,配置=None):
    '登记设置词典、壳层、通用分区、桌面更新和宿主发行确认'
    def 登记开发者工具():
        '通用区里的代码工作视图开关'
        def 注入():
            '已接受值和写入'
            return {
                'hooks':{'developerTools':上下文.configForms.developerTools.enabled},
                'setEnabled':上下文.configForms.developerTools.setEnabled,
            }
        return 上下文.slots.register({
            'name':'settings.general.item',
            'id':'developer-tools',
            'order':15,
            'locale':命名空间,
            'inject':注入,
        },开发者工具行.开发者工具行)
    上下文.slots.inject('settings.general.item',登记开发者工具)
    def 登记版本():
        '版本信息跟在核心偏好后面'
        return 上下文.slots.register({
            'name':'settings.general.item',
            'id':'current-version',
            'order':100,
            'locale':命名空间,
        },当前版本行.当前版本行)
    上下文.slots.inject('settings.general.item',登记版本)
    def 登记词典():
        '登记本壳中英文案表。页面显示不走英文表'
        return 上下文.locale.register(命名空间,{'zh':文案.中文,'en':文案.英文})
    上下文.副作用(登记词典,'ui-settings-general: dictionaries')
    连接=上下文.获取服务('connection')
    窗口=取握手窗口()
    载体=getattr(窗口,'dshDesktop',None)
    桥=None
    if 载体 is not None and getattr(载体,'protocolVersion',None)==1:
        桥=getattr(载体,'updates',None)
    桌面=桌面更新.桌面更新源(桥)
    def 挂桌面():
        '拆除时拆掉载体订阅'
        def 拆():
            '忽略之后到达的状态'
            桌面.拆除()
        return 拆
    上下文.副作用(挂桌面,'ui-settings-general: desktop update carrier')
    def 登记角标():
        '折叠侧栏上的更新点'
        def 注入():
            '桌面更新和连接'
            return {
                'hooks':{
                    'desktopUpdate':桌面.存储,
                    'connectionState':连接.state,
                },
            }
        return 上下文.slots.register({
            'name':'sidebar.toggle.badge',
            'locale':命名空间,
            'inject':注入,
        },桌面更新指示器.桌面更新角标)
    上下文.slots.inject('sidebar.toggle.badge',登记角标)
    宿主=获取内部数据(上下文.remote,'host')
    if isinstance(宿主,dict):
        回环=宿主['isLoopback'] is True
    else:
        回环=宿主.isLoopback is True
    文档控制器=None
    if 回环:
        文档控制器=文档存储.设置文档存储(上下文,上下文.configForms.describe())
    文档注入=None
    if 文档控制器 is not None:
        def 文档注入面():
            '控制器和快照'
            return {
                'controller':文档控制器,
                'hooks':{'snapshot':文档控制器.存储},
            }
        文档注入=文档注入面
    def 挂文档():
        '拆除时停止跟随镜像'
        def 拆():
            '没有控制器就不用拆'
            if 文档控制器 is not None:
                文档控制器.拆除()
        return 拆
    上下文.副作用(挂文档,'ui-settings-general: document action directory')
    分区版本=-1
    语言修订=-1
    分区行=[]
    引导版本=-1
    引导步骤=[]
    def 取分区快照():
        '账本或语言变了才重投影'
        nonlocal 分区版本,语言修订,分区行
        版本=上下文.slots.getVersion('settings.section')
        修订=上下文.locale.getSnapshot()['revision']
        if 版本!=分区版本 or 修订!=语言修订:
            分区版本=版本
            语言修订=修订
            行表=[]
            for 条目 in 上下文.slots.entries('settings.section'):
                选项=条目['options']
                if 'id' in 选项 and 选项['id'] is not None:
                    标识=选项['id']
                else:
                    标识=''
                if 'order' in 选项 and 选项['order'] is not None:
                    序=选项['order']
                else:
                    序=0
                标签=解析槽标签(选项['label'] if 'label' in 选项 else None)
                if 标签 is None:
                    标签=''
                行表.append({'id':标识,'order':序,'label':标签})
            行表.sort(key=按序)
            分区行=行表
        return 分区行
    def 订分区(监听):
        '账本和语言都变就通知'
        卸账本=上下文.slots.subscribe('settings.section',监听)
        卸语言=上下文.locale.subscribe(监听)
        def 卸():
            '取消两路'
            卸账本()
            卸语言()
        return 卸
    def 取引导快照():
        '引导账本变了才重投影'
        nonlocal 引导版本,引导步骤
        版本=上下文.slots.getVersion('settings.onboarding')
        if 版本!=引导版本:
            引导版本=版本
            步表=[]
            for 条目 in 上下文.slots.entries('settings.onboarding'):
                选项=条目['options']
                if 'id' in 选项 and 选项['id'] is not None:
                    标识=选项['id']
                else:
                    标识=''
                if 'order' in 选项 and 选项['order'] is not None:
                    序=选项['order']
                else:
                    序=0
                步表.append({'id':标识,'order':序})
            步表.sort(key=按序)
            引导步骤=步表
        return 引导步骤
    def 订引导(监听):
        '引导账本变了就通知'
        return 上下文.slots.subscribe('settings.onboarding',监听)
    def 壳注入():
        '重连、打开更新，以及分区和引导'
        def 打开更新():
            '请求壳层拥有的更新动作'
            桌面.打开()
        def 重连():
            '立刻换一代连接'
            连接.reconnect()
        return {
            'openDesktopUpdate':打开更新,
            'reconnect':重连,
            'hooks':{
                'shortcuts':上下文.shortcuts.catalog,
                'desktopUpdate':桌面.存储,
                'connectionState':连接.state,
                'sections':{'getSnapshot':取分区快照,'subscribe':订分区},
                'onboardingSteps':{'getSnapshot':取引导快照,'subscribe':订引导},
            },
        }
    def 登记设置():
        '占住 sidebar.settings，并登记打开设置命令'
        def 初始():
            '对话框起初关掉，没有选中分区'
            return {'open':False,'activeId':None}
        def 打开(草稿):
            '打开设置'
            草稿['open']=True
        def 关闭(草稿):
            '关掉并清掉当前分区'
            草稿['open']=False
            草稿['activeId']=None
        def 选择(草稿,标识):
            '选中分区'
            草稿['activeId']=标识
        def 打开分区(草稿,标识):
            '打开并选中分区'
            草稿['activeId']=标识
            草稿['open']=True
        壳句柄=声明存储({
            'init':初始,
            'actions':{
                'open':打开,
                'close':关闭,
                'select':选择,
                'openSection':打开分区,
            },
        })
        壳实例=壳句柄.create()
        def 复用(作用域键=None):
            '解析存储时交回同一份壳实例'
            return 壳实例
        壳句柄.create=复用
        def 快捷标签():
            '命令上的打开设置'
            return 文案.中文['shortcut.open']
        def 解析(命令上下文):
            '别的模态挡住时不处理。设置已开则关栈顶，否则打开'
            模态=命令上下文['modal']
            if 模态 is not None and 模态!='settings':
                return {'status':'blocked','reason':'modal'}
            def 执行():
                '关掉设置模态或打开设置'
                if 模态=='settings':
                    关栈顶模态(取握手窗口().document)
                else:
                    壳实例.actions['open']()
            return {'status':'handled','run':执行}
        卸命令=上下文.shortcuts.register({
            'id':'settings.open',
            'label':快捷标签,
            'aliases':['settings','preferences'],
            'defaults':{
                'desktop:macos':{'code':'Comma','modifiers':['primary']},
                'desktop:windows':{'code':'Comma','modifiers':['primary']},
                'desktop:linux':{'code':'Comma','modifiers':['primary']},
                'web:macos':{'code':'Comma','modifiers':['primary','alt']},
                'web:windows':{'code':'Comma','modifiers':['primary','alt']},
            },
            'regions':['page','editable','terminal'],
            'modals':['settings'],
            'resolve':解析,
        })
        卸槽=上下文.slots.register({
            'name':'sidebar.settings',
            'locale':命名空间,
            'store':壳句柄,
            'children':{
                'settings.launcher':{'kind':'single','scope':'root'},
                'settings.trigger':{'kind':'single','scope':'root'},
                'settings.header':{'kind':'single','scope':'root'},
                'settings.action':{'kind':'list','scope':'root'},
                'settings.close':{'kind':'single','scope':'root'},
                'settings.section':{'kind':'list','scope':'root'},
                'settings.onboarding':{'kind':'list','scope':'root'},
            },
            'inject':壳注入,
        },设置根.设置根)
        def 卸():
            '卸命令和设置槽'
            卸命令()
            卸槽()
        return 卸
    上下文.slots.inject('sidebar.settings',登记设置)
    def 登记触发():
        '触发器里的图标和文字'
        return 上下文.slots.register({
            'name':'settings.trigger',
            'locale':命名空间,
        },壳层.触发内容)
    上下文.slots.inject('settings.trigger',登记触发)
    def 登记页眉():
        '面板标题'
        return 上下文.slots.register({
            'name':'settings.header',
            'locale':命名空间,
        },壳层.页眉内容)
    上下文.slots.inject('settings.header',登记页眉)
    if 文档注入 is not None:
        def 登记文档():
            '打开配置文件'
            return 上下文.slots.register({
                'name':'settings.action',
                'id':'open-document',
                'order':0,
                'locale':命名空间,
                'inject':文档注入,
            },文档动作.文档动作)
        上下文.slots.inject('settings.action',登记文档)
    def 登记关闭():
        '关闭按钮的隐藏名字'
        return 上下文.slots.register({
            'name':'settings.close',
            'locale':命名空间,
        },壳层.关闭标签)
    上下文.slots.inject('settings.close',登记关闭)
    def 登记通用():
        '通用设置这一节'
        def 导航名():
            '导航上的通用设置'
            return 文案.中文['general.nav']
        return 上下文.slots.register({
            'name':'settings.section',
            'id':'general',
            'order':0,
            'label':导航名,
            'locale':命名空间,
            'children':{'settings.general.item':{'kind':'list','scope':'root'}},
        },常规条目分区.常规条目分区)
    上下文.slots.inject('settings.section',登记通用)
    def 发行注入():
        '放下这次版本差，或刷新页面'
        def 放下():
            '本页留在启动时的版本'
            上下文.modules.entries.dismissRelease()
        def 刷新页():
            '从宿主重新加载页面'
            取握手窗口().location.reload()
        return {
            'dismissRelease':放下,
            'reloadPage':刷新页,
            'hooks':{'releaseChange':上下文.modules.entries.releaseChange},
        }
    def 登记发行():
        '壳层罩上的版本变化确认'
        return 上下文.slots.register({
            'name':'shell.overlay',
            'id':'host-release-change',
            'locale':命名空间,
            'inject':发行注入,
        },宿主版本提示.宿主版本提示)
    上下文.slots.inject('shell.overlay',登记发行)

inject=依赖
apply=应用
