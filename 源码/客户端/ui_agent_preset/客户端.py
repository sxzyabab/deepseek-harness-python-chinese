"""智能体预设界面浏览器半边（通用行 / 芯片 / 页眉标签 / 管理分区）。



对齐上游 `ui-agent-preset/src/client/index.ts`。公开面仅中文名。

四面共用一名册：通用默认行、新会话芯片、会话页眉只读标签、设置管理分区。

"""

from .文案 import 命名空间,中文,英文#词典

from .预设行 import 预设行#设置行

from .预设芯片 import 预设芯片#新会话芯片

from .预设标签 import 预设标签#页眉只读标签

from .预设分区 import 预设分区#管理分区组件

from .设置仓库 import 设置命名空间,预设设置控制器#设置仓

from .芯片仓库 import 芯片控制器#主界面芯片

from .分区仓库 import 分区控制器,草稿阻挡#管理分区



__all__=[#仅中文公开名

    '注入','应用','预设行','预设芯片','预设标签','预设分区',

    '预设设置控制器','芯片控制器','分区控制器','草稿阻挡',

    '命名空间','中文','英文','设置命名空间',

]#公开面结束



注入=['slots','locale','connection','remote']#依赖



def 应用(上下文):#安装浏览器半边预设界面

    """登记词典与四面：通用行、芯片、页眉标签、管理分区。"""

    连接=上下文.get('connection')#连接

    接口=连接.api#API

    控制器=预设设置控制器(接口)#设置控制器

    名册读者=set()#名册读者集合

    def 名册变动():#分区改名册时通知

        """刷新通用行并喊读者。"""

        控制器.load()#刷新通用行

        for 读 in list(名册读者):#通知

            读()#回调

    分区=分区控制器(接口,名册变动)#分区控制器

    上下文.effect(lambda:上下文.locale.register(命名空间,{'zh':中文,'en':英文}),'ui-agent-preset: settings row dictionaries')#词典

    编写入口=[None]#可变格：会话作用域绑定



    def 刷新监听():#设置刷新

        """外部改设置或重连都推动这一行。"""

        def 刷新():#重载

            """拉名册；分区已加载过则一并。"""

            控制器.load()#加载

            if 分区.store.getSnapshot().get('status')!='idle':#分区已用

                分区.load()#刷新分区

        def 文档更新(ns):#设置文档更新

            """仅本命名空间。"""

            if ns!=设置命名空间:#不是本 ns

                return#忽略

            刷新()#刷新

        拆们=[#两路

            上下文.remote.$on('settings/document-updated',文档更新),#设置

            上下文.on('connection/reset',刷新),#重连

        ]#结束

        def 拆除():#拆除

            """逐个取消。"""

            for 拆 in 拆们:#逐个

                拆()#取消

        return 拆除#拆除器

    上下文.effect(刷新监听,'ui-agent-preset: settings refresh')#刷新



    def 注入行():#通用行注入

        """hooks/load/select 经设置控制器。"""

        return {#注入面

            'hooks':{'agentPreset':控制器.store},#store

            'load':控制器.load,#加载

            'select':控制器.select,#选定

        }#结束



    def 挂会话面(作用域):#芯片与页眉：同一控制器

        """暂存选择属于流而不是某一会话。"""

        本接口=(作用域.get('connection')).api#本作用域 API

        def 读摘要():#当前会话摘要

            """芯片所需字段。"""

            态=作用域.sessions.list.getSnapshot()#列表

            当前=读字段(态,'current')#当前 id

            if 当前 is None:#无

                return None#空

            摘要=(读字段(态,'byId') or {}).get(当前)#摘要

            if 摘要 is None:#无

                return None#空

            出={'id':读字段(摘要,'id'),'blank':读字段(摘要,'blank')}#基础

            预设=读字段(摘要,'agentPreset')#预设

            if 预设 is not None:#有

                出['agentPreset']=预设#带上

            return 出#摘要

        def 记下预设(会话标识,预设):#RPC 回声

            """写入会话行。"""

            作用域.sessions.noteAgentPreset(会话标识,预设)#写

        芯片控=芯片控制器(本接口,读摘要,记下预设)#芯片控制器

        def 芯片注入():#芯片注入面

            """hooks/load/select/introduced。"""

            return {#注入

                'hooks':{'agentPresetSeat':芯片控.store},#store

                'load':芯片控.load,#加载

                'select':芯片控.select,#暂存

                'introduced':芯片控.introduced,#消提示

            }#结束

        def 标签注入():#页眉标签注入面

            """读通用行同一 store。"""

            return {#注入

                'hooks':{'agentPresets':控制器.store},#名册

                'load':控制器.load,#加载

            }#结束

        def 生命周期():#芯片、页眉、名册读者与编写入口

            """会话列表变动则应用暂存。"""

            停=作用域.sessions.list.subscribe(lambda:芯片控.apply())#应用暂存

            def 设置动(ns):#设置文档更新

                """改默认也带动芯片。"""

                if ns!=设置命名空间:#不是本 ns

                    return#忽略

                芯片控.load()#重载

            设置拆=作用域.remote.$on('settings/document-updated',设置动)#设置

            def 他处选定(会话标识,预设):#他处选定

                """写入会话行。"""

                作用域.sessions.noteAgentPreset(会话标识,预设)#写

            选定拆=作用域.remote.$on('agent-preset/selected',他处选定)#选定

            def 读名册():#名册读者

                """刷新芯片。"""

                芯片控.load()#加载

            名册读者.add(读名册)#登记

            def 启动编写():#从设置分区启动自指预设会话

                """暂存 cordis 并开新会话。"""

                芯片控.stage('cordis',True)#暂存并 introduce

                作用域.workspaces.startSession()#开新

            编写入口[0]=启动编写#绑定

            芯片=作用域.slots.register({#登记芯片

                'name':'conversation.hero.agentPreset',#主屏芯片槽

                'locale':命名空间,#词表

                'inject':芯片注入,#注入

            },预设芯片)#组件

            标签=作用域.slots.register({#登记页眉只读标签

                'name':'conversation.session.header.actions',#页眉操作槽

                'id':'agent-preset',#条目 id

                'order':-10,#负序带

                'locale':命名空间,#词表

                'inject':标签注入,#注入

            },预设标签)#组件

            def 拆除():#拆除

                """解绑一切。"""

                停()#取消订阅

                设置拆()#取消设置

                选定拆()#取消选定

                名册读者.discard(读名册)#去掉读者

                编写入口[0]=None#解绑编写

                芯片()#注销芯片

                标签()#注销标签

            return 拆除#拆除器

        作用域.effect(生命周期,'ui-agent-preset: new-session chip and header label')#生命周期



    上下文.inject(['slots','conversation','sessions','workspaces'],挂会话面)#会话作用域



    def 分区注入():#设置分区注入面

        """hooks 与分区动词。"""

        面={#注入

            'hooks':{'agentPresetSection':分区.store},#store

            'load':分区.load,#加载

            'view':分区.view,#查看

            'closeView':分区.closeView,#关查看

            'beginCopy':分区.beginCopy,#开始复制

            'cancelCopy':分区.cancelCopy,#取消

            'setCopyId':分区.setCopyId,#改 id

            'setCopyName':分区.setCopyName,#改名

            'confirmCopy':分区.confirmCopy,#确认复制

            'openLocation':分区.openLocation,#打开目录

            'confirmDelete':分区.confirmDelete,#确认删除

            'remove':分区.remove,#删除

            'makeDefault':分区.makeDefault,#设默认

        }#结束

        if 编写入口[0] is not None:#有绑定

            面['startCreatorDraft']=编写入口[0]#编写按钮

        return 面#注入



    def 登记行():#登记通用设置行

        """settings.general.item。"""

        return 上下文.slots.register({#登记

            'name':'settings.general.item',#条目槽

            'id':'agent-preset',#id

            'order':-25,#顺序

            'locale':命名空间,#词表

            'inject':注入行,#注入

        },预设行)#组件

    上下文.slots.inject('settings.general.item',登记行)#等槽



    def 登记分区():#登记设置分区

        """settings.section；排在 Models 之后。"""

        分区组件=预设分区#分区组件

        return 上下文.slots.register({#登记

            'name':'settings.section',#分区槽

            'id':'agent-presets',#id

            'order':20,#顺序

            'label':lambda:上下文.locale.bind(命名空间)('nav'),#导航

            'locale':命名空间,#词表

            'inject':分区注入,#注入

        },分区组件)#组件

    上下文.slots.inject('settings.section',登记分区)#等槽



def 读字段(对象,键,缺省=None):#读字段

    """映射或对象。"""

    if 对象 is None:#空

        return 缺省#缺

    if isinstance(对象,dict):#映射

        return 对象[键] if 键 in 对象 else 缺省#键

    return getattr(对象,键,缺省)#属性


