"""设置壳与无主文案插件的浏览器半边。

对齐上游 `ui-settings-general/src/client/index.ts`。公开面仅中文名。
"""
from .文案 import 命名空间,中文,英文#词典
from .文档存储 import 设置文档存储,已加载则刷新文档#文档存储
from .设置根 import 设置根#壳根
from .壳层 import 触发器内容,页眉内容,关闭标签#chrome
from .常规条目分区 import 常规条目分区#常规条目分区
from .文档动作 import 文档动作#文档动作

__all__=[#仅中文公开名
    '注入','应用','设置根','触发器内容','页眉内容','关闭标签',
    '常规条目分区','文档动作','设置文档存储','命名空间','中文','英文',
]#公开面结束

注入=['slots','locale','connection']#槽位、文案、连接

def 解析槽标签(标签):
    """字符串或 thunk。"""
    if 标签 is None:#空
        return ''#空串
    if callable(标签):#thunk
        文本=标签()#调用
        if 文本 is None:#无返回
            return ''#空串
        return str(文本)#字符串
    return str(标签)#字符串

def 按序(行):
    """导航行按 order 升序。"""
    return 行['order']#序

def 应用(上下文):
    """登记词表、chrome 与常规条目分区。"""
    def 登记词典():
        """登记外壳词典。"""
        return 上下文.locale.register(命名空间,{'zh':中文,'en':英文})#词典
    上下文.副作用(登记词典,'ui-settings-general: dictionaries')#词典
    翻译=上下文.locale.bind(命名空间)#绑定词表
    连接=上下文.获取服务('connection')#连接句柄
    文档控制器=设置文档存储(连接.api) if 连接.isLoopback else None#本机回环才有
    文档注入=None#文档动作注入
    if 文档控制器 is not None:#有仓库
        def 文档注入面():
            """控制器 + 快照选择器。useSnapshot 是注入面键名。"""
            def 选快照(选):
                """对当前快照跑选择器。"""
                return 选(文档控制器.存储.getSnapshot())#选择
            return {'controller':文档控制器,'useSnapshot':选快照}#注入
        文档注入=文档注入面#工厂
    def 订重置():
        """连接重置时刷新文档。"""
        def 刷新():
            """已加载则重拉。"""
            已加载则刷新文档(文档控制器)#刷新
        return 上下文.监听('connection/reset',刷新)#订阅
    上下文.副作用(订重置,'ui-settings-general: metadata invalidations')#重连失效
    分区版本=-1#分区账本版本缓存
    语言修订=-1#语言修订缓存
    分区行=[]#缓存导航行
    引导版本=-1#引导账本版本
    引导步骤=[]#缓存引导步骤
    def 壳注入():
        """分区与引导两路可观察源。"""
        def 取分区快照():
            """账本或语言变了才重投影。槽位条目是 dict。"""
            nonlocal 分区版本,语言修订,分区行#缓存
            版本=上下文.slots.getVersion('settings.section')#账本版本
            修订=上下文.locale.getSnapshot()['revision']#语言修订
            if 版本!=分区版本 or 修订!=语言修订:#失效
                分区版本=版本#记下
                语言修订=修订#记下
                分区行=[]#重建
                for 条目 in 上下文.slots.entries('settings.section'):#每条
                    选项=条目['options'] if 'options' in 条目 else 条目#选项
                    分区行.append({#导航行
                        'id':选项['id'] if 'id' in 选项 else '',#id
                        'order':选项['order'] if 'order' in 选项 else 0,#序；缺键才 0，0 合法
                        'label':解析槽标签(选项['label'] if 'label' in 选项 else None),#标签
                    })#行结束
                分区行.sort(key=按序)#升序
            return 分区行#缓存
        def 订分区(监听):
            """两路订阅。"""
            拆除账本=上下文.slots.subscribe('settings.section',监听)#账本
            拆除语言=上下文.locale.subscribe(监听)#语言
            def 拆除():
                """取消。"""
                拆除账本()#账本
                拆除语言()#语言
            return 拆除#拆除器
        def 取引导快照():
            """账本变了才重投影。"""
            nonlocal 引导版本,引导步骤#缓存
            版本=上下文.slots.getVersion('settings.onboarding')#版本
            if 版本!=引导版本:#失效
                引导版本=版本#记下
                引导步骤=[]#重建
                for 条目 in 上下文.slots.entries('settings.onboarding'):#每条
                    选项=条目['options'] if 'options' in 条目 else 条目#选项
                    引导步骤.append({#步骤
                        'id':选项['id'] if 'id' in 选项 else '',#id
                        'order':选项['order'] if 'order' in 选项 else 0,#序；缺键才 0
                    })#步骤结束
                引导步骤.sort(key=按序)#升序
            return 引导步骤#缓存
        def 订引导(监听):
            """订引导账本。"""
            return 上下文.slots.subscribe('settings.onboarding',监听)#引导
        return {'hooks':{#注入面
            'sections':{'getSnapshot':取分区快照,'subscribe':订分区},#分区
            'onboardingSteps':{'getSnapshot':取引导快照,'subscribe':订引导},#引导
        }}#hooks 结束
    def 登记壳():
        """等侧栏设置洞。"""
        return 上下文.slots.register({#登记
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
        },设置根)#设置根
    上下文.slots.inject('sidebar.settings',登记壳)#等侧栏设置洞
    def 登记触发器():
        """登记触发器。"""
        return 上下文.slots.register({'name':'settings.trigger','locale':命名空间},触发器内容)#触发器
    上下文.slots.inject('settings.trigger',登记触发器)#触发器
    def 登记页眉():
        """登记页眉。"""
        return 上下文.slots.register({'name':'settings.header','locale':命名空间},页眉内容)#页眉
    上下文.slots.inject('settings.header',登记页眉)#页眉
    if 文档注入 is not None:#本机回环
        def 登记文档动作():
            """登记打开配置文件动作。"""
            return 上下文.slots.register({#文档动作
                'name':'settings.action',#动作槽
                'id':'open-document',#id
                'order':0,#最前
                'locale':命名空间,#文案
                'inject':文档注入,#注入
            },文档动作)#组件
        上下文.slots.inject('settings.action',登记文档动作)#文档动作
    def 登记关闭():
        """登记关闭标签。"""
        return 上下文.slots.register({'name':'settings.close','locale':命名空间},关闭标签)#关闭
    上下文.slots.inject('settings.close',登记关闭)#关闭
    def 常规导航标签():
        """常规分区导航标签。"""
        return 翻译('general.nav')#标签
    def 登记常规条目分区():
        """登记常规条目分区。"""
        return 上下文.slots.register({#常规条目分区
            'name':'settings.section',#分区槽
            'id':'general',#常规
            'order':0,#最前
            'label':常规导航标签,#导航标签
            'locale':命名空间,#文案
            'children':{'settings.general.item':{'kind':'list','scope':'root'}},#常规条目槽
        },常规条目分区)#组件
    上下文.slots.inject('settings.section',登记常规条目分区)#常规条目分区

inject=注入#框架槽
apply=应用#框架槽
