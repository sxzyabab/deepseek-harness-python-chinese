"""智能体预设界面浏览器半边（芯片 / 页眉标签 / 管理分区）。

对齐上游 `ui-agent-preset/src/client/index.ts`。公开面仅中文名。
三面共用一名册：新会话芯片、会话页眉只读标签、设置管理分区。
"""
from .文案 import 命名空间,中文,英文#词典
from .预设芯片 import 预设芯片#新会话芯片
from .预设标签 import 预设标签#页眉只读标签
from .预设分区 import 预设分区#管理分区组件
from .设置存储 import 设置命名空间,预设设置控制器#设置存储
from .芯片存储 import 芯片控制器#主界面芯片
from .分区存储 import 分区控制器,草稿阻挡#管理分区

__all__=[#仅中文公开名
    '注入','应用','预设芯片','预设标签','预设分区',
    '预设设置控制器','芯片控制器','分区控制器','草稿阻挡',
    '命名空间','中文','英文','设置命名空间',
]#公开面结束

注入=['slots','locale','remote','remote.agentPresets','remote.settings']#依赖

def 应用(上下文):#安装浏览器半边预设界面
    """登记词典与三面：芯片、页眉标签、管理分区。"""
    接口=上下文.remote#远程面
    控制器=预设设置控制器(接口)#展示面控制器
    名册读者=set()#名册读者集合
    def 名册变动():#分区改名册时通知
        """刷新展示面并喊读者。"""
        控制器.load()#刷新展示面
        for 读 in list(名册读者):#通知
            读()#回调
    分区=分区控制器(接口,名册变动)#分区控制器
    def 登记词典():
        """登记预设词表。"""
        return 上下文.locale.register(命名空间,{'zh':中文,'en':英文})#词典
    上下文.副作用(登记词典,'ui-agent-preset: settings row dictionaries')#词典
    def 刷新监听():#设置刷新
        """外部改设置或重连都推动这一行。"""
        def 刷新():#重载
            """拉名册；分区已加载过则一并。"""
            控制器.load()#加载
            if 分区.存储.getSnapshot()['status']!='idle':#分区已用
                分区.load()#刷新分区
        def 文档更新(ns):#设置文档更新
            """仅本命名空间。"""
            if ns!=设置命名空间:#不是本 ns
                return#忽略
            刷新()#刷新
        def 连接重置():#重连
            """刷新两面并让名册读者重读。"""
            刷新()#刷新两面
            for 读 in list(名册读者):#名册读者也重读
                读()#回调
        拆列表=[#两路
            上下文.remote.$on('settings/document-updated',文档更新),#设置
            上下文.监听('connection/reset',连接重置),#重连
        ]#结束
        def 拆除():#拆除
            """逐个取消。"""
            for 拆 in 拆列表:#逐个
                拆()#取消
        return 拆除#拆除器
    上下文.副作用(刷新监听,'ui-agent-preset: settings refresh')#刷新
    编写入口=[None]#可变格：会话作用域绑定
    活动芯片=[None]#当前会话作用域芯片
    def 挂会话面(作用域):#芯片与页眉：同一控制器
        """暂存选择属于流而不是某一会话。"""
        本接口=作用域.remote#本作用域远程
        def 读摘要():#当前会话摘要
            """芯片所需字段。"""
            态=作用域.sessions.list.getSnapshot()#列表对象
            当前=态.current#当前 id
            if 当前 is None:#无
                return None#空
            表=态.byId#会话表 dict
            if 表 is None or 当前 not in 表:#无
                return None#空
            摘要=表[当前]#摘要 dict
            出={'id':摘要['id'],'blank':摘要['blank']}#基础
            if 'agentPreset' in 摘要 and 摘要['agentPreset'] is not None:#有预设
                出['agentPreset']=摘要['agentPreset']#带上
            return 出#摘要
        def 记下预设(会话标识,预设):#RPC 回声
            """写入会话行。"""
            作用域.sessions.noteAgentPreset(会话标识,预设)#写
        芯片控=芯片控制器(本接口,读摘要,记下预设)#芯片控制器
        活动芯片[0]=芯片控#记下当前芯片
        def 芯片注入():#芯片注入面
            """hooks/load/select/introduced。"""
            return {#注入
                'hooks':{'agentPresetSeat':芯片控.存储},#存储
                'load':芯片控.load,#加载
                'select':芯片控.select,#暂存
                'introduced':芯片控.introduced,#消提示
            }#结束
        def 标签注入():#页眉标签注入面
            """读展示面同一 store。"""
            return {#注入
                'hooks':{'agentPresets':控制器.存储},#名册
                'load':控制器.load,#加载
            }#结束
        def 生命周期():#芯片、页眉、名册读者与编写入口
            """会话列表变动则应用暂存。"""
            def 应用暂存():
                """把暂存预设落到当前会话。"""
                芯片控.apply()#应用暂存
            停=作用域.sessions.list.subscribe(应用暂存)#应用暂存
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
                if not 分区.存储.getSnapshot()['showPicker']:#选择器关闭则不起草
                    return#忽略
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
                活动芯片[0]=None#解绑芯片
                芯片()#注销芯片
                标签()#注销标签
            return 拆除#拆除器
        作用域.副作用(生命周期,'ui-agent-preset: new-session chip and header label')#生命周期
    上下文.依赖启动(['slots','conversation','sessions','workspaces'],挂会话面)#会话作用域
    def 捕获空白会话同步():#记下本次设置动作可能更新的那一场空白会话
        """只在仍是同一芯片、同一空白会话时同步。"""
        芯片=活动芯片[0]#捕获时的芯片
        会话标识=芯片.blankSessionId() if 芯片 is not None else None#当时空白会话
        def 同步(标识):#同步器
            """同一芯片且同一空白会话才套用。"""
            if 芯片 is None or 会话标识 is None or 活动芯片[0] is not 芯片:#已换芯片或无空白会话
                return None#无关
            return 芯片.syncBlankSession(会话标识,标识)#同步空白会话预设
        return 同步#同步器
    def 设为默认(标识):#设为默认并可选同步空白会话
        """分区 makeDefault 带同步器。"""
        分区.makeDefault(标识,捕获空白会话同步())#写入
    def 设置选择器可见(露出):#写出选择器开关
        """分区 setPickerVisible 带同步器。"""
        分区.setPickerVisible(露出,捕获空白会话同步())#写入
    def 分区注入():#设置分区注入面
        """hooks 与分区动词。"""
        面={#注入
            'hooks':{'agentPresetSection':分区.存储},#store
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
            'makeDefault':设为默认,#设默认
            'setPickerVisible':设置选择器可见,#选择器开关
        }#结束
        if 编写入口[0] is not None:#有绑定
            面['startCreatorDraft']=编写入口[0]#编写按钮
        return 面#注入
    def 登记分区():#登记设置分区
        """settings.section；排在 Models 之后。"""
        def 分区导航标签():
            """分区导航标签。"""
            return 上下文.locale.bind(命名空间)('nav')#导航
        return 上下文.slots.register({#登记
            'name':'settings.section',#分区槽
            'id':'agent-presets',#id
            'order':20,#顺序
            'label':分区导航标签,#导航
            'locale':命名空间,#词表
            'inject':分区注入,#注入
        },预设分区)#组件
    上下文.slots.inject('settings.section',登记分区)#等槽

inject=注入#框架槽
apply=应用#框架槽
