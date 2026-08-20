"""模型设置与产品引导插件的浏览器半边。



对齐上游 `ui-settings-models/src/client/index.ts`。公开面仅中文名。

"""

from .文案 import 命名空间,中文,英文#词典

from .引导文案 import 欢迎通知设置命名空间#欢迎 ns

from .仓库 import 模型设置仓库,已加载则刷新#模型仓库

from .欢迎仓库 import 欢迎通知仓库,已加载则刷新欢迎#欢迎仓库

from .模型分区 import 模型分区#模型分区

from .引导对话框 import 欢迎通知,官方引导对话框#引导

from .提供方编辑器 import 提供方编辑器#提供方编辑器

from .自定义提供方卡片 import 自定义提供方卡片#自定义卡

from .DeepSeek模型编辑器 import DeepSeek模型编辑器#DeepSeek 目录

from .模型列表编辑器 import 模型列表编辑器#模型列表

from .编辑器页脚 import 编辑器页脚#页脚

from .引导模态 import 引导模态#引导模态

from .密钥判定 import 密钥失败#密钥判定



__all__=[#仅中文公开名

    '注入','应用','模型设置仓库','欢迎通知仓库','模型分区','欢迎通知','官方引导对话框',

    '提供方编辑器','自定义提供方卡片','DeepSeek模型编辑器','模型列表编辑器','编辑器页脚','引导模态','密钥失败',

    '命名空间','中文','英文','已加载则刷新',

]#公开面结束



注入=['slots','locale','connection','remote']#依赖



def 应用(上下文):#安装模型设置浏览器半边

    """登记模型分区与引导步骤，接到连接失效。"""

    上下文.effect(lambda:上下文.locale.register(命名空间,{'zh':中文,'en':英文}),'ui-settings-models: copy dictionaries')#词典

    连接=上下文.get('connection')#连接句柄

    接口=getattr(连接,'api',连接)#API

    控制器=模型设置仓库(接口)#模型页仓库

    翻译=上下文.locale.bind(命名空间)#绑定词表

    欢迎=欢迎通知仓库(接口,'host' if getattr(连接,'isLoopback',False) else 'memory')#欢迎仓库

    def 推送失效():#设置/凭证/拓扑与重连

        """已加载过才刷新。"""

        def 刷模型():#刷模型页

            """已加载才重拉。"""

            已加载则刷新(控制器)#刷新

        def 刷全部():#模型与欢迎

            """一并刷新。"""

            刷模型()#模型

            已加载则刷新欢迎(欢迎)#欢迎

        def 文档更新(命名空间名):#设置文档更新

            """模型总刷；欢迎 ns 才刷欢迎。"""

            刷模型()#模型

            if 命名空间名==欢迎通知设置命名空间:#欢迎

                已加载则刷新欢迎(欢迎)#欢迎

        拆表=[#拆除器

            上下文.remote.$on('settings/document-updated',文档更新),#文档更新

            上下文.remote.$on('credentials/updated',刷模型),#凭证

            上下文.remote.$on('llm/adapters-updated',刷模型),#拓扑

            上下文.on('connection/reset',刷全部),#重连

        ]#拆表结束

        def 拆除():#拆除

            """逐个取消。"""

            for 拆 in 拆表:#每个

                拆()#取消

        return 拆除#拆除器

    上下文.effect(推送失效,'ui-settings-models: pushed invalidations')#推送失效

    def 模型注入():#模型分区注入面

        """仓库 + 快照选择器 + API + 翻译。"""

        return {'controller':控制器,'useSnapshot':lambda 选:选(控制器.store.getSnapshot()),'api':接口,'t':翻译}#注入

    def 欢迎注入():#欢迎通知注入面

        """欢迎仓库 + 钩子 + 翻译。"""

        return {'controller':欢迎,'hooks':{'welcome':欢迎.store},'t':翻译}#注入

    def 官方引导注入():#官方 DeepSeek 引导注入面

        """模型仓库 + 钩子 + API + 翻译。"""

        return {'controller':控制器,'hooks':{'models':控制器.store},'api':接口,'t':翻译}#注入

    上下文.slots.inject('settings.section',lambda:上下文.slots.register({#模型分区

        'name':'settings.section','id':'models','order':10,'label':lambda:翻译('nav'),'inject':模型注入,

    },模型分区))#组件

    上下文.slots.inject('settings.onboarding',lambda:上下文.slots.register({#欢迎通知

        'name':'settings.onboarding','id':'welcome-notice','order':-100,'inject':欢迎注入,

    },欢迎通知))#组件

    上下文.slots.inject('settings.onboarding',lambda:上下文.slots.register({#官方 DeepSeek

        'name':'settings.onboarding','id':'deepseek-official','order':0,'inject':官方引导注入,

    },官方引导对话框))#组件

