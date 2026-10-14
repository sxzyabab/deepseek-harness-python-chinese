from .文案 import 中文,英文,插件装载文案键#词典
from ....基础设施.通用工具 import 获取内部数据
from .配置账本 import 行配置键,配置账本源#账本
from .装载存储 import 插件装载控制,是否安装待决,行键,包视图,排序包表#装载存储
from .呈现 import 装载文案,短名,包文案,提示文案#呈现
from .插件装载页 import 插件装载页#装载页
from .插件面板图标 import 插件面板图标,插件刷新提示#面板图标与刷新失败提示
from . import (
    导航存储,
    槽位约定,
)

__all__=[#仅中文公开名
    '依赖','应用','命名空间','面板标识',
    '中文','英文','插件装载文案键',
    '行配置键','配置账本源',
    '插件装载控制','是否安装待决','行键','包视图','排序包表',
    '装载文案','短名','包文案','提示文案',
    '插件装载页','插件面板图标','插件刷新提示',
]

命名空间='pluginManager'#本包文案命名空间（线路字面量）
面板标识='plugins'#侧栏入口与主面板共享 id（线路字面量）
依赖=['slots','locale','remote','remote.pluginManager','remote.pluginInventory','layout']#槽、文案、远程、布局

def 应用(上下文):
    '贡献侧栏插件入口与主栏装载页，并跟随 Host 变更事件'
    def 登记词典():
        '挂载中英文案'
        return 上下文.locale.register(命名空间,{'zh':中文,'en':英文})#登记

    上下文.副作用(登记词典,'ui-plugin-manager: dictionaries')#词典
    翻译=上下文.locale.bind(命名空间)#绑定
    控制=插件装载控制(上下文)#控制器

    def 拆除控制():
        '返回拆除控制器的拆除器'
        def 拆():
            '拆除'
            控制.dispose()#拆除
        return 拆#拆除器

    上下文.副作用(拆除控制,'ui-plugin-manager: controller')#控制器寿命

    def 订失效():
        '订阅 Host 变更与安装日志'
        def 刷新():
            '非 idle 则重读'
            if 控制.getSnapshot()['status']!='idle':#非空闲
                控制.加载()#加载
        拆除表=[#订阅
            获取内部数据(上下文.remote,'on')('plugin-manager/changed',刷新),#变更
            获取内部数据(上下文.remote,'on')('plugin-manager/install-log',控制.追加日志),#日志
            获取内部数据(上下文.remote,'on')('plugin-manager/install-state',控制.安装进度),#进度
            上下文.on('connection/reset',刷新),#重连
        ]#拆除表
        def 退订():
            '退订全部'
            for 拆 in 拆除表:#逐个
                拆()#退
        return 退订#拆除器

    上下文.副作用(订失效,'ui-plugin-manager: host invalidations')#失效
    账本=配置账本源(上下文)#账本

    def 解析包文案(文本):
        '当前语言下的包内文案；没有解析器时字符串原样'
        方法=getattr(上下文.locale,'resolveText',None)#语言服务若已提供
        if callable(方法):
            return 方法(文本)#解析
        if isinstance(文本,str):
            return 文本#原样
        return ''#空

    def 注入面():
        '装载页注入面，附上包内文案解析'
        面=控制.注入(账本)#控制器面
        面['resolveText']=解析包文案#包内标题与说明
        return 面#注入

    def 订离开(实例):
        '离开插件主栏时把导航收回列表'
        钩=getattr(上下文.layout,'panelInfo',None)#布局若直接挂着面板源
        if 钩 is None or not hasattr(钩,'getSnapshot'):
            绑定=getattr(上下文.slots,'_rootBinding',None)#根标准源
            钩子=绑定.get('hooks') if isinstance(绑定,dict) else None#钩子表
            钩=钩子.get('panelInfo') if isinstance(钩子,dict) else None#面板源
        if 钩 is None or not hasattr(钩,'subscribe') or not hasattr(钩,'getSnapshot'):
            return None#没有可订的源
        def 离开():
            '活动面板不是插件页则回到列表'
            快照=钩.getSnapshot()#面板快照
            活动=快照.get('activePanelId') if isinstance(快照,dict) else None#活动面板
            if 活动!=面板标识:
                实例.actions['setView']({'kind':'list'})#收回列表
        return 钩.subscribe(离开)#退订

    def 挂主栏():
        '登记主面板装载页，并提供跨插件打开组合包'
        句柄=导航存储.创建导航存储()#导航句柄
        实例=句柄.create()#与页面共用一份
        句柄.create=lambda: 实例#渲染器再取仍是这一份
        拆登记=上下文.slots.register({#席位
            'name':'main',#主栏
            'key':面板标识,#键
            'locale':命名空间,#文案
            'store':句柄,#导航
            'inject':注入面,#注入
            'children':{#子槽
                'plugins.add.actions':{'kind':'list','scope':'root'},#添加方式
                'plugins.item':{'kind':'list','scope':'root'},#官方条目
                'plugins.bundle.activation':{'kind':'keyed','scope':'root'},#启用后
                'plugins.bundle.config':{'kind':'keyed','scope':'root'},#组合包配置
                'plugins.row.config':{'kind':'keyed','scope':'root'},#行配置
                'plugins.detail.actions':{'kind':'list','scope':'root'},#详情动作
                'plugins.detail.badge':{'kind':'list','scope':'root'},#详情徽章
                'plugins.detail.section':{'kind':'list','scope':'root'},#详情分区
            },#子槽结束
        },插件装载页)#页面
        拆离开=订离开(实例)#离开主栏
        def 打开组合包(包名):
            '选中插件主栏并打开该组合包，不改当前会话'
            布局=上下文.layout#布局服务
            选=getattr(布局,'selectPanel',None)#英文名
            if not callable(选):
                选=getattr(布局,'选择面板',None)#中文名
            if callable(选):
                选(面板标识)#选面板
            实例.actions['setView']({'kind':'package','name':包名})#打开包
        拆导航=上下文.反射.提供服务('pluginNavigation',{'openBundle':打开组合包})#跨插件导航
        def 拆除():
            '卸主栏、面板订阅和导航服务'
            拆登记()#卸槽
            if callable(拆离开):
                拆离开()#退订
            if callable(拆导航):
                拆导航()#卸服务
        return 拆除#拆除器

    上下文.slots.inject('main',挂主栏)#主栏

    def 挂侧栏():
        '登记侧栏入口'
        return 上下文.slots.register({#席位
            'name':'sidebar.panellist',#面板列表
            'id':面板标识,#id
            'order':0,#序
            'label':lambda:翻译('panel'),#标签
            'locale':命名空间,#文案
        },插件面板图标)#图标

    上下文.slots.inject('sidebar.panellist',挂侧栏)#侧栏

    def 挂刷新提示():
        '离开插件页后仍显示刷新失败'
        面=控制.注入(账本)
        return 上下文.slots.register({
            'name':'shell.overlay','id':'plugin-manager.refresh-toast','locale':命名空间,
            'inject':lambda:{'hooks':{'pluginManager':面['hooks']['pluginManager']},'dismissNotice':面['dismissNotice']},
        },插件刷新提示)

    上下文.slots.inject('shell.overlay',挂刷新提示)#刷新失败

inject=依赖#框架槽
apply=应用#框架槽
