from .文案 import 中文,英文,插件装载文案键#词典
from .配置账本 import 行配置键,配置账本源#账本
from .装载存储 import 插件装载控制,是否安装待决,行键,包视图,排序包表#装载存储
from .呈现 import 装载文案,短名,包文案,提示文案#呈现
from .插件装载页 import 插件装载页#装载页
from .插件面板图标 import 插件面板图标#面板图标

__all__=[#仅中文公开名
    '注入','应用','命名空间','面板标识',
    '中文','英文','插件装载文案键',
    '行配置键','配置账本源',
    '插件装载控制','是否安装待决','行键','包视图','排序包表',
    '装载文案','短名','包文案','提示文案',
    '插件装载页','插件面板图标',
]#公开面结束

命名空间='pluginManager'#本包文案命名空间（线路字面量）
面板标识='plugins'#侧栏入口与主面板共享 id（线路字面量）
注入=['slots','locale','remote','remote.pluginManager','remote.pluginInventory']#槽、文案、远程

def 应用(上下文):
    """贡献侧栏插件入口与主栏装载页，并跟随 Host 变更事件。"""
    def 登记词典():
        """挂载中英文案。"""
        return 上下文.locale.register(命名空间,{'zh':中文,'en':英文})#登记

    上下文.副作用(登记词典,'ui-plugin-manager: dictionaries')#词典
    翻译=上下文.locale.bind(命名空间)#绑定
    控制=插件装载控制(上下文)#控制器

    def 拆除控制():
        """返回拆除控制器的拆除器。"""
        def 拆():
            """拆除。"""
            控制.拆除()#拆除
        return 拆#拆除器

    上下文.副作用(拆除控制,'ui-plugin-manager: controller')#控制器寿命

    def 订失效():
        """订阅 Host 变更与安装日志。"""
        def 刷新():
            """非 idle 则重读。"""
            if 控制.取快照()['status']!='idle':#非空闲
                控制.加载()#加载
        拆除表=[#订阅
            上下文.remote.$on('plugin-manager/changed',刷新),#变更
            上下文.remote.$on('plugin-manager/install-log',控制.追加日志),#日志
            上下文.remote.$on('plugin-manager/install-state',控制.安装进度),#进度
            上下文.on('connection/reset',刷新),#重连
        ]#拆除表
        def 退订():
            """退订全部。"""
            for 拆 in 拆除表:#逐个
                拆()#退
        return 退订#拆除器

    上下文.副作用(订失效,'ui-plugin-manager: host invalidations')#失效
    账本=配置账本源(上下文)#账本

    def 挂主栏():
        """登记主面板装载页。"""
        return 上下文.slots.register({#席位
            'name':'main',#主栏
            'key':面板标识,#键
            'locale':命名空间,#文案
            'inject':lambda:控制.注入(账本),#注入
            'children':{#子槽
                'plugins.item':{'kind':'list','scope':'root'},#官方条目
                'plugins.bundle.config':{'kind':'keyed','scope':'root'},#组合包配置
                'plugins.row.config':{'kind':'keyed','scope':'root'},#行配置
            },#子槽结束
        },插件装载页)#页面

    上下文.slots.inject('main',挂主栏)#主栏

    def 挂侧栏():
        """登记侧栏入口。"""
        return 上下文.slots.register({#席位
            'name':'sidebar.panellist',#面板列表
            'id':面板标识,#id
            'order':0,#序
            'label':lambda:翻译('panel'),#标签
            'locale':命名空间,#文案
        },插件面板图标)#图标

    上下文.slots.inject('sidebar.panellist',挂侧栏)#侧栏

inject=注入#框架槽
apply=应用#框架槽
