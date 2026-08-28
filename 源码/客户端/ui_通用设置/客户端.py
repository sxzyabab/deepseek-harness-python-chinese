"""设置壳与无主文案插件的浏览器半边。

对齐上游 `ui-settings-general/src/client/index.ts`。公开面仅中文名。
"""
from .文案 import 命名空间,中文,英文#词典
from .文档仓库 import 设置文档仓库,已加载则刷新文档#文档仓库
from .设置根 import 设置根#壳根
from .壳层 import 触发器内容,页眉内容,关闭标签#chrome
from .通用分区 import 通用分区#通用分区
from .文档动作 import 文档动作#文档动作

__all__=[#仅中文公开名
    '注入','应用','设置根','触发器内容','页眉内容','关闭标签',
    '通用分区','文档动作','设置文档仓库','命名空间','中文','英文',
]#公开面结束

注入=['slots','locale','connection']#槽位、文案、连接

def 解析槽标签(标签):#解析槽位标签
    """字符串或 thunk。"""
    if 标签 is None:#空
        return ''#空串
    if callable(标签):#thunk
        return 标签() or ''#调用
    return str(标签)#字符串

def 应用(上下文):#安装设置壳浏览器半边
    """登记词表、chrome 与通用分区。"""
    上下文.effect(lambda:上下文.locale.register(命名空间,{'zh':中文,'en':英文}),'ui-settings-general: dictionaries')#词典
    翻译=上下文.locale.bind(命名空间)#绑定词表
    连接=上下文.get('connection')#连接句柄
    文档控制器=设置文档仓库(连接.api) if getattr(连接,'isLoopback',False) else None#本机回环才有
    文档注入=None#文档动作注入
    if 文档控制器 is not None:#有仓库
        def 文档注入面():#动作注入面
            """控制器 + 快照选择器。"""
            return {'controller':文档控制器,'useSnapshot':lambda 选:选(文档控制器.store.getSnapshot())}#注入
        文档注入=文档注入面#工厂
    上下文.effect(lambda:上下文.on('connection/reset',lambda:已加载则刷新文档(文档控制器)),'ui-settings-general: metadata invalidations')#重连失效
    分区版本=-1#分区账本版本缓存
    语言修订=-1#语言修订缓存
    分区行=[]#缓存导航行
    引导版本=-1#引导账本版本
    引导步骤=[]#缓存引导步骤
    def 壳注入():#设置根注入面
        """分区与引导两路可观察源。"""
        def 取分区快照():#账本或语言变了才重投影
            """投影导航行。"""
            nonlocal 分区版本,语言修订,分区行#缓存
            版本=上下文.slots.getVersion('settings.section')#账本版本
            修订=上下文.locale.getSnapshot().get('revision') if isinstance(上下文.locale.getSnapshot(),dict) else getattr(上下文.locale.getSnapshot(),'revision',None)#修订
            if 版本!=分区版本 or 修订!=语言修订:#失效
                分区版本=版本#记下
                语言修订=修订#记下
                分区行=[]#重建
                for 条目 in 上下文.slots.entries('settings.section'):#每条
                    选项=getattr(条目,'options',条目) if not isinstance(条目,dict) else 条目.get('options',条目)#选项
                    分区行.append({#导航行
                        'id':选项.get('id','') if isinstance(选项,dict) else getattr(选项,'id',''),#id
                        'order':选项.get('order',0) if isinstance(选项,dict) else getattr(选项,'order',0),#序
                        'label':解析槽标签(选项.get('label') if isinstance(选项,dict) else getattr(选项,'label',None)),#标签
                    })#行结束
                分区行.sort(key=lambda 行:行['order'])#升序
            return 分区行#缓存
        def 订分区(监听):#订分区账本与语言
            """两路订阅。"""
            拆账本=上下文.slots.subscribe('settings.section',监听)#账本
            拆语言=上下文.locale.subscribe(监听)#语言
            def 拆除():#拆除两路
                """取消。"""
                拆账本()#账本
                拆语言()#语言
            return 拆除#拆除器
        def 取引导快照():#账本变了才重投影
            """投影引导步骤。"""
            nonlocal 引导版本,引导步骤#缓存
            版本=上下文.slots.getVersion('settings.onboarding')#版本
            if 版本!=引导版本:#失效
                引导版本=版本#记下
                引导步骤=[]#重建
                for 条目 in 上下文.slots.entries('settings.onboarding'):#每条
                    选项=getattr(条目,'options',条目) if not isinstance(条目,dict) else 条目.get('options',条目)#选项
                    引导步骤.append({#步骤
                        'id':选项.get('id','') if isinstance(选项,dict) else getattr(选项,'id',''),#id
                        'order':选项.get('order',0) if isinstance(选项,dict) else getattr(选项,'order',0),#序
                    })#步骤结束
                引导步骤.sort(key=lambda 步:步['order'])#升序
            return 引导步骤#缓存
        return {'hooks':{#注入面
            'sections':{'getSnapshot':取分区快照,'subscribe':订分区},#分区
            'onboardingSteps':{'getSnapshot':取引导快照,'subscribe':lambda 监听:上下文.slots.subscribe('settings.onboarding',监听)},#引导
        }}#hooks 结束
    上下文.slots.inject('sidebar.settings',lambda:上下文.slots.register({#等侧栏设置洞
        'name':'sidebar.settings',#侧栏设置
        'children':{#本壳声明的设置槽
            'settings.trigger':{'kind':'single','scope':'root'},#触发器
            'settings.header':{'kind':'single','scope':'root'},#页眉
            'settings.action':{'kind':'list','scope':'root'},#动作
            'settings.close':{'kind':'single','scope':'root'},#关闭
            'settings.section':{'kind':'list','scope':'root'},#分区
            'settings.onboarding':{'kind':'list','scope':'root'},#引导
        },#子槽结束
        'inject':壳注入,#根注入
    },设置根))#设置根
    上下文.slots.inject('settings.trigger',lambda:上下文.slots.register({'name':'settings.trigger','locale':命名空间},触发器内容))#触发器
    上下文.slots.inject('settings.header',lambda:上下文.slots.register({'name':'settings.header','locale':命名空间},页眉内容))#页眉
    if 文档注入 is not None:#本机回环
        上下文.slots.inject('settings.action',lambda:上下文.slots.register({#文档动作
            'name':'settings.action',#动作槽
            'id':'open-document',#id
            'order':0,#最前
            'locale':命名空间,#文案
            'inject':文档注入,#注入
        },文档动作))#组件
    上下文.slots.inject('settings.close',lambda:上下文.slots.register({'name':'settings.close','locale':命名空间},关闭标签))#关闭
    上下文.slots.inject('settings.section',lambda:上下文.slots.register({#通用分区
        'name':'settings.section',#分区槽
        'id':'general',#通用
        'order':0,#最前
        'label':lambda:翻译('general.nav'),#导航标签
        'locale':命名空间,#文案
        'children':{'settings.general.item':{'kind':'list','scope':'root'}},#通用条目槽
    },通用分区))#组件
