from ....客户端.存储 import 声明存储
from ....基础设施.通用工具 import 获取内部数据
from ...ui_槽位 import 解析槽标签
from . import (
    净化安装输入,
    呈现,
    插件刷新浮动提示,
    插件面板图标,
    插件装载页,
    文案,
    槽位约定,
    装载存储,
    配置账本,
)
from .呈现 import 取中文
from .文案 import 中文
from .装载存储 import 插件装载控制

__all__=[
    '净化安装输入','呈现','插件刷新浮动提示','插件面板图标','插件装载页','文案','槽位约定','装载存储','配置账本',
    '依赖','应用','命名空间','面板标识',
]

命名空间='pluginManager'
面板标识='plugins'
依赖=[
    'slots','locale','remote','remote.pluginManager','remote.pluginInventory',
    'remote.pluginRegistryProbe','configForms','layout',
]

def 应用(上下文,配置=None):
    '贡献侧栏插件入口和主栏装载页，并跟随 Host 的变更'
    def 登记词典():
        '挂上中英文案表。看得见的字不走英文表'
        return 上下文.locale.register(命名空间,{'zh':中文,'en':文案.英文})
    上下文.副作用(登记词典,'ui-plugin-manager: dictionaries')
    控制=插件装载控制(上下文)
    def 拆除控制():
        '卸下时拆掉控制器'
        def 拆():
            '停止发布'
            控制.拆除()
        return 拆
    上下文.副作用(拆除控制,'ui-plugin-manager: controller')
    def 订失效():
        '订阅安装变更、日志、进度和重连'
        def 刷新():
            '还没读过则不刷新'
            if 控制.取快照()['status']!='idle':
                控制.加载()
        def 记日志(块):
            '把日志交给控制器'
            控制.追加日志(块)
        def 记进度(进度):
            '把进度交给控制器'
            控制.安装进度(进度)
        拆除表=[
            getattr(上下文.remote,'$on')('plugin-manager/changed',刷新),
            getattr(上下文.remote,'$on')('plugin-manager/install-log',记日志),
            getattr(上下文.remote,'$on')('plugin-manager/install-state',记进度),
            上下文.on('connection/reset',刷新),
        ]
        def 退订():
            '退掉全部订阅'
            for 拆 in 拆除表:
                拆()
        return 退订
    上下文.副作用(订失效,'ui-plugin-manager: host invalidations')
    账本版本=[]
    账本修订=-1
    账本={'items':[],'bundles':set(),'rows':set()}
    席位名=('plugins.item','plugins.bundle.config','plugins.row.config')
    def 配置键(名):
        '有 key 的登记'
        键集=set()
        for 条目 in 上下文.slots.entries(名):
            选项=条目['options']
            if 选项.get('key') is not None:
                键集.add(选项['key'])
        return 键集
    def 取配置快照():
        '槽或语言变了才重算账本'
        nonlocal 账本版本,账本修订,账本
        下一=[上下文.slots.getVersion(名) for 名 in 席位名]
        当前=上下文.locale.getSnapshot()['revision']
        变了=当前!=账本修订 or len(下一)!=len(账本版本)
        if not 变了:
            序=0
            for 版本 in 下一:
                if 版本!=账本版本[序]:
                    变了=True
                序=序+1
        if 变了:
            账本版本=下一
            账本修订=当前
            条目列=[]
            for 条目 in 上下文.slots.entries('plugins.item'):
                选项=条目['options']
                身份=选项['id'] if 选项.get('id') is not None else ''
                标签=解析槽标签(选项.get('label'))
                条目列.append({'id':身份,'label':'' if 标签 is None else 标签})
            账本={
                'items':条目列,
                'bundles':配置键('plugins.bundle.config'),
                'rows':配置键('plugins.row.config'),
            }
        return 账本
    def 订配置(监听):
        '槽和语言都订上'
        退订=[上下文.slots.subscribe(名,监听) for 名 in 席位名]
        退订.append(上下文.locale.subscribe(监听))
        def 拆():
            '退订账本'
            for 项 in 退订:
                项()
        return 拆
    标签版本=-1
    标签修订=-1
    标签表=[]
    def 取标签快照():
        'plugins.tab 或语言变了才重算'
        nonlocal 标签版本,标签修订,标签表
        下一=上下文.slots.getVersion('plugins.tab')
        当前=上下文.locale.getSnapshot()['revision']
        if 下一!=标签版本 or 当前!=标签修订:
            标签版本=下一
            标签修订=当前
            列=[]
            for 条目 in 上下文.slots.entries('plugins.tab'):
                选项=条目['options']
                身份=选项['id'] if 选项.get('id') is not None else ''
                标签=解析槽标签(选项.get('label'))
                列.append({'id':身份,'label':'' if 标签 is None else 标签})
            标签表=列
        return 标签表
    def 订标签(监听):
        '订标签槽和语言'
        退订=[
            上下文.slots.subscribe('plugins.tab',监听),
            上下文.locale.subscribe(监听),
        ]
        def 拆():
            '退订标签'
            for 项 in 退订:
                项()
        return 拆
    面=控制.注入(
        {'getSnapshot':取配置快照,'subscribe':订配置},
        {'getSnapshot':取标签快照,'subscribe':订标签},
        取中文,
    )
    def 挂刷新提示():
        '离开插件页后仍显示刷新失败'
        def 注入刷新():
            '刷新失败提示只拿共享提示和关掉动作'
            return {
                'hooks':{'pluginManager':面['hooks']['pluginManager']},
                'dismissNotice':面['dismissNotice'],
            }
        return 上下文.slots.register({
            'name':'shell.overlay',
            'id':'plugin-manager.refresh-toast',
            'locale':命名空间,
            'inject':注入刷新,
        },插件刷新浮动提示.插件刷新浮动提示)
    上下文.slots.inject('shell.overlay',挂刷新提示)
    def 初值():
        '默认落在已安装列表'
        return {'view':{'kind':'list'},'tab':'installed'}
    def 设视图(草稿,视图):
        '切换列表、更多、组合包、官方条目或行'
        草稿['view']=视图
    def 设标签(草稿,标签):
        '切换已安装或贡献的页'
        草稿['tab']=标签
    def 挂主栏():
        '登记主面板，离开时收回列表，并提供打开组合包'
        句柄=声明存储({'init':初值,'actions':{'setView':设视图,'setTab':设标签}})
        实例=句柄.create()
        def 复用(作用域键=None):
            '渲染器再取仍是这一份'
            return 实例
        句柄.create=复用
        def 注入面():
            '主栏拿到装载面'
            return 面
        拆登记=上下文.slots.register({
            'name':'main',
            'key':面板标识,
            'locale':命名空间,
            'store':句柄,
            'inject':注入面,
            'children':{
                'plugins.add.actions':{'kind':'list','scope':'root'},
                'plugins.tab':{'kind':'list','scope':'root'},
                'plugins.item':{'kind':'list','scope':'root'},
                'plugins.bundle.activation':{'kind':'keyed','scope':'root'},
                'plugins.bundle.config':{'kind':'keyed','scope':'root'},
                'plugins.row.config':{'kind':'keyed','scope':'root'},
                'plugins.detail.actions':{'kind':'list','scope':'root'},
                'plugins.detail.badge':{'kind':'list','scope':'root'},
                'plugins.detail.section':{'kind':'list','scope':'root'},
            },
        },插件装载页.插件装载页)
        def 离开面板():
            '活动面板不是插件页则回到列表'
            if 上下文.layout.panelInfo.getSnapshot()['activePanelId']!=面板标识:
                实例.actions['setView']({'kind':'list'})
        拆离开=上下文.layout.panelInfo.subscribe(离开面板)
        def 打开组合包(包名):
            '选中插件主栏并打开该组合包，不改当前会话'
            上下文.layout.selectPanel(面板标识)
            实例.actions['setTab']('installed')
            实例.actions['setView']({'kind':'package','name':包名})
        拆导航=上下文.反射.提供服务('pluginNavigation',{'openBundle':打开组合包})
        yield 拆登记
        yield 拆离开
        def 卸导航():
            '卸掉跨插件导航'
            拆导航()
        yield 卸导航
    上下文.slots.inject('main',挂主栏)
    def 面板标签():
        '侧栏上显示的中文'
        return 中文['panel']
    def 挂侧栏():
        '登记侧栏入口'
        return 上下文.slots.register({
            'name':'sidebar.panellist',
            'id':面板标识,
            'order':0,
            'label':面板标签,
            'locale':命名空间,
        },插件面板图标.插件面板图标)
    上下文.slots.inject('sidebar.panellist',挂侧栏)

inject=依赖
apply=应用
