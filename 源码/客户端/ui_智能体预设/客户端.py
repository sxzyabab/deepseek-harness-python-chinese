from ...工具.值 import 带值弱映射#按座位绑定弱缓存芯片
from .文案 import 命名空间,中文,英文#词典
from .预设芯片 import 预设芯片#新会话芯片
from .预设标签 import 预设标签#页眉只读标签
from .预设分区 import 预设分区#管理分区组件
from .设置存储 import 设置命名空间,预设设置控制器#设置存储
from .芯片存储 import 芯片控制器,共享暂存初始#主界面芯片与共享暂存
from .分区存储 import 分区控制器,草稿阻挡#管理分区

__all__=[#仅中文公开名
    '依赖','应用','预设芯片','预设标签','预设分区',
    '预设设置控制器','芯片控制器','分区控制器','草稿阻挡',
    '命名空间','中文','英文','设置命名空间',
]

依赖=['slots','sessions','locale','remote','remote.agentPresets','remote.settings']#依赖

def 应用(上下文):#安装浏览器半边预设界面
    """登记词典与三面：芯片、页眉标签、管理分区。"""
    接口=上下文.remote#远程面
    控制器=预设设置控制器(接口)#呈现面控制器
    共享暂存=dict(共享暂存初始)#Provider 间共享的一次性暂存
    座位表=带值弱映射()#按座位绑定上下文弱缓存芯片控制器
    无绑定芯片=芯片控制器(接口,lambda:None,共享暂存)#无绑定时的芯片（新会话屏）
    def 座位为(作用域,绑定):#按绑定取或造芯片
        """代际绑定 → 芯片控制器。"""
        键=绑定['ctx']#作用域上下文作弱键（绑定 dict 不可弱引用）
        已有=座位表.get(键)#已有则复用
        if 已有 is not None:#命中
            return 已有#复用
        会话标识=绑定['sessionId']#该绑定会话 id
        本接口=作用域.remote#本作用域远程
        def 读摘要():#该绑定下的当前会话摘要
            """代际匹配且主视图持有才交给芯片。"""
            if 作用域.sessions.binding(会话标识) is not 绑定:#代际不匹配
                return None#空
            表=作用域.sessions.list.getSnapshot().byId#列表
            摘要=表[会话标识] if 会话标识 in 表 else None#行
            if 摘要 is None:#无行
                return None#空
            持有=作用域.sessions.retainInfo(会话标识).getSnapshot().get('retainedBy',{})#持有图
            if (持有.get('mainView',0) or 0)<=0:#非主视图
                return None#空
            return 摘要#摘要
        芯片控=芯片控制器(本接口,读摘要,共享暂存)#该绑定芯片
        座位表.set(键,芯片控)#写入弱缓存
        def 绑定位寿命():#绑定退役时摘掉缓存
            """返回拆除器。"""
            def 拆除():#拆除
                """删除座位缓存。"""
                座位表.delete(键)#删除
            return 拆除#拆除器
        绑定['ctx'].副作用(绑定位寿命,'ui-agent-preset: Provider binding')#诊断名
        return 芯片控#返回控制器
    def 名册变动():#分区改名册时通知
        """刷新呈现面与全部芯片。"""
        控制器.load()#刷新呈现面
        无绑定芯片.load()#刷新无绑定芯片
        for 芯片 in 座位表.values:#刷新各绑定芯片
            芯片.load()#加载
    分区=分区控制器(接口,名册变动)#分区控制器
    def 主空白座位(作用域):#主视图持有的空白会话芯片
        """有绑定则取芯片。"""
        表=作用域.sessions.list.getSnapshot().byId#列表
        摘要=None#候选
        for 会话 in 表.values():#扫
            if 会话.get('blank') and (会话.get('retainedBy',{}).get('mainView',0) or 0)>0:#主视图空白
                摘要=会话#记下
                break#停
        if 摘要 is None:#无
            return None#空
        绑定=作用域.sessions.binding(摘要['id'])#取绑定
        return None if 绑定 is None else 座位为(作用域,绑定)#有绑定则取芯片
    def 登记词典():
        """登记预设词表。"""
        return 上下文.locale.register(命名空间,{'zh':中文,'en':英文})#词典
    上下文.副作用(登记词典,'ui-agent-preset: settings row dictionaries')#词典
    def 刷新监听():#设置刷新
        """外部改设置或重连都推动这一行。"""
        def 刷新():#重载
            """拉名册与全部芯片；分区已加载过则一并。"""
            控制器.load()#加载
            if 分区.存储.getSnapshot()['status']!='idle':#分区已用
                分区.load()#刷新分区
            无绑定芯片.load()#刷新无绑定芯片
            for 芯片 in 座位表.values:#刷新各绑定芯片
                芯片.load()#加载
        def 文档更新(ns):#设置文档更新
            """仅本命名空间。"""
            if ns!=设置命名空间:#不是本 ns
                return#忽略
            刷新()#刷新
        def 连接重置():#重连
            """刷新呈现面与全部芯片。"""
            刷新()#刷新
        拆列表=[#两路
            上下文.remote.$on('settings/document-updated',文档更新),#设置
            上下文.监听('connection/reset',连接重置),#重连
        ]
        def 拆除():#拆除
            """逐个取消。"""
            for 拆 in 拆列表:#逐个
                拆()#取消
        return 拆除#拆除器
    上下文.副作用(刷新监听,'ui-agent-preset: settings refresh')#刷新
    编写入口=[None]#可变格：会话作用域绑定
    def 挂会话面(作用域):#芯片与页眉
        """按会话绑定解析芯片注入面。"""
        def 芯片注入(会话标识=None):#芯片注入面
            """hooks/load/select/introduced。"""
            绑定=None if 会话标识 is None else 作用域.sessions.binding(会话标识)#取绑定
            芯片控=无绑定芯片 if 绑定 is None else 座位为(作用域,绑定)#无绑定用共享空座位
            return {#注入
                'hooks':{'agentPresetSeat':芯片控.存储},#存储
                'load':芯片控.load,#加载
                'select':芯片控.select,#暂存
                'introduced':芯片控.introduced,#消提示
            }
        def 标签注入():#页眉标签注入面
            """读呈现面同一 store。"""
            return {#注入
                'hooks':{'agentPresets':控制器.存储},#名册
                'load':控制器.load,#加载
            }
        def 生命周期():#芯片、页眉与编写入口
            """登记槽位并绑定编写入口。"""
            def 启动编写():#从设置分区启动自指预设会话
                """暂存 cordis 并开新会话。"""
                if not 分区.存储.getSnapshot()['showPicker']:#选择器关闭则不起草
                    return#忽略
                芯片控=主空白座位(作用域)#主视图空白
                if 芯片控 is None:#无
                    芯片控=无绑定芯片#回落
                芯片控.stage('cordis',True)#暂存并 introduce
                作用域.workspaces.startSession()#开新
                芯片控.apply()#立刻套到落地的空白会话
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
                """解绑编写并注销槽。"""
                编写入口[0]=None#解绑编写
                芯片()#注销芯片
                标签()#注销标签
            return 拆除#拆除器
        作用域.副作用(生命周期,'ui-agent-preset: new-session chip and header label')#生命周期
    上下文.依赖启动(['slots','conversation','sessions','workspaces'],挂会话面)#会话作用域
    def 捕获空白会话同步():#记下本次设置动作可能更新的那一场空白会话
        """只在仍是同一绑定芯片、同一空白会话时同步。"""
        表=上下文.sessions.list.getSnapshot().byId#列表
        摘要=None#候选
        for 会话 in 表.values():#扫
            if 会话.get('blank') and (会话.get('retainedBy',{}).get('mainView',0) or 0)>0:#主视图空白
                摘要=会话#记下
                break#停
        绑定=None if 摘要 is None else 上下文.sessions.binding(摘要['id'])#取绑定
        芯片=None if 绑定 is None else 座位表.get(绑定['ctx'])#取已缓存芯片
        会话标识=芯片.blankSessionId() if 芯片 is not None else None#当时空白会话
        def 同步(标识):#同步器
            """同一绑定芯片且同一空白会话才套用。"""
            if 芯片 is None or 会话标识 is None or 绑定 is None:#无
                return None#无关
            if 座位表.get(绑定['ctx']) is not 芯片:#已换芯片
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
        }
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

inject=依赖#框架槽
apply=应用#框架槽
