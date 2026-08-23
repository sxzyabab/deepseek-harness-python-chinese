"""盖在独立沙盒模式与审批策略旋钮上的面向用户权限预设。一次切换先记下所选预设，再经各自权威 setter 写入已变旋钮。执行、提示词叙述和回放继续读各自的旋钮折叠。当两个预设共享同一捆旋钮时，预设事件保住用户意图。读侧作为 `permissions` 会话投影交付；写侧作为 `/permission` 命令交付——两者都是同一服务上的可选子件。"""
from ...依赖 import cordis,schemastery#外部依赖胶水
服务=cordis.服务#Cordis 服务基类
模式=schemastery.模式#配置校验
from ..配置 import 安装设置段,设置命名空间#设置段安装与命名空间
from ..沙盒策略 import 沙盒模式表,生效沙盒模式,设沙盒模式#沙盒模式表、折叠与写入
from ..用户审批 import 审批策略表,生效审批策略,设审批策略#审批策略表、折叠与写入
from .类型 import (#再导出权限域纯类型
    预设选项字段,#预设选项字段
    权限选择字段,#权限选择字段
)#类型再导出结束

__all__=[#仅中文公开名；Cordis 槽英文别名不入表
    '名称','自定义预设','权限设置命名空间','默认预设表','配置模式','空旋钮',
    '权限选择投影模式','取字段','生效权限预设','应用旋钮事件','折叠旋钮',
    '权限预设服务','预设选项字段','权限选择字段','默认',
]#公开面结束

名称='permission-presets'#Cordis 插件短名（包目录用下划线，插件名保留上游连字符）
name=名称#Cordis 插件名
自定义预设='custom'#派生的非预设状态名；生效旋钮与任何表条目都不匹配时返回；客户端可显示为当前值，但从不是切换目标或事件载荷
权限设置命名空间=设置命名空间('permission')#携带未来会话默认值的设置命名空间

默认预设表={#默认两档预设：名 → 旋钮捆
    'workspace-write':{#工作区写入档
        'sandbox':'workspace-write',#沙盒模式
        'approval':'ask',#审批询问
        'name':'workspace-write',#展示名
        'description':'Write inside the workspace and permitted temporary directories; wider retries require approval.',#展示文案，字面量不翻译
    },#workspace-write 结束
    'danger-full-access':{#全开档
        'sandbox':'danger-full-access',#全开沙盒
        'approval':'never',#不问
        'name':'danger-full-access',#展示名
        'description':'Full file access without approval prompts.',#展示文案，字面量不翻译
    },#danger-full-access 结束
}#默认预设表结束

配置模式=模式.对象({#插件配置：预设表与组合默认
    'presets':模式.字典(模式.对象({#预设表：名 → 旋钮捆
        'sandbox':模式.联合(list(沙盒模式表)).必填(),#必填沙盒模式
        'approval':模式.联合(list(审批策略表)).必填(),#必填审批策略
        'name':模式.字符串(),#可选展示名
        'description':模式.字符串(),#可选说明
    })).默认(默认预设表),#默认两档
    'defaultPreset':模式.字符串(),#可选组合默认预设名
})#配置模式结束
Config=配置模式#Cordis 配置模式

空旋钮={'preset':None,'sandbox':None,'approval':None}#空日志的旋钮状态：每个旋钮都在其组合默认

权限选择投影模式={#`permissions` 投影的线上载荷模式
    'type':'object',#对象
    'additionalProperties':False,#禁多余键
    'properties':{#字段
        'options':{#选项数组
            'type':'array',#数组
            'items':{#选项对象
                'type':'object',#对象
                'additionalProperties':False,#禁多余键
                'properties':{#选项字段
                    'value':{'type':'string','minLength':1},#非空选项值
                    'name':{'type':'string','minLength':1},#非空展示名
                    'description':{'type':'string'},#可选说明
                },#选项字段结束
                'required':['value','name'],#值与名必填
            },#选项对象结束
        },#options 结束
        'currentValue':{'type':'string','minLength':1},#非空当前值
    },#字段结束
    'required':['options','currentValue'],#两字段必填
}#投影模式结束

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段，缺席为缺省。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 生效权限预设(事件们):#从日志折叠所选预设
    """从持久日志折叠最后一次所选预设；回放不需要追赶状态。按日志顺序的会话事件；其他事件类型被忽略。返回最后一次所选预设；从未记录时为 None。"""
    if 事件们 is None:#无日志
        return None#从未选择
    for 下标 in range(len(事件们)-1,-1,-1):#从后往前找
        事件=事件们[下标]#取该条事件
        if 取字段(事件,'type')=='permission/preset':#命中最后一次选择
            return 取字段(取字段(事件,'data'),'preset')#返回所选预设
    return None#从未选择

def 应用旋钮事件(状态,事件):#应用一条旋钮事件
    """单事件旋钮转移（投影单元的 apply）。不关心的事件返回同一引用——注册表的变更门。"""
    种类=取字段(事件,'type')#事件类型
    数据=取字段(事件,'data')#事件载荷
    if 种类=='permission/preset':#预设意图
        return {'preset':取字段(数据,'preset'),'sandbox':取字段(状态,'sandbox'),'approval':取字段(状态,'approval')}#记下所选预设
    if 种类=='sandbox/mode':#沙盒模式
        return {'preset':取字段(状态,'preset'),'sandbox':取字段(数据,'mode'),'approval':取字段(状态,'approval')}#记下沙盒覆盖
    if 种类=='approval/policy':#审批策略
        return {'preset':取字段(状态,'preset'),'sandbox':取字段(状态,'sandbox'),'approval':取字段(数据,'policy')}#记下审批覆盖
    return 状态#无关事件保持同一引用

def 折叠旋钮(事件们):#冷读折叠全部旋钮
    """整份日志的旋钮折叠（应用旋钮事件的冷读平行）。"""
    状态=空旋钮#从空状态起
    if 事件们 is None:#无日志
        return 状态#空
    for 事件 in 事件们:#逐事件转移
        状态=应用旋钮事件(状态,事件)#转移
    return 状态#返回折叠结果

class 权限预设服务(服务):#权限预设服务：拥有部署的权限预设及其写路径
    """拥有部署的权限预设及其写路径。要求有约束的 `ctx.shell` 执行器与 `ctx.approval`；不匹配的旋钮值报成 CUSTOM_PRESET，不是错误。"""
    Config=配置模式#插件配置模式
    inject=['shell','approval','sessions']#依赖沙盒执行器、审批与会话
    注入=inject#中文别名

    def __init__(自身,ctx,配置=None):#构造预设服务
        """以 permissionPresets 名安装服务，钉初始权限，并可选挂投影与命令子件。"""
        if 配置 is None:#缺省空配置
            配置={}#空
        super().__init__(ctx,'permissionPresets')#以 permissionPresets 名安装服务
        预设表=取字段(配置,'presets')#取已默认的表
        if 预设表 is None:#模式应已填默认
            预设表=默认预设表#回落默认表
        自身.presets=dict(预设表)#运行时预设表（脱离副本）
        自身.预设表=自身.presets#中文别名槽
        if 自定义预设 in 自身.presets:#custom 不得当表键
            raise Exception('permission: "'+自定义预设+'" is reserved for the derived not-a-preset state and cannot name a table entry')#拒绝占用保留名
        if 取字段(ctx.shell,'sandboxMode') is None:#执行器不约束
            raise Exception('permission: the mounted bash executor does not confine (no sandboxMode) — presets bundle a sandbox mode, so composing this plugin over an unconfined executor is a misconfiguration')#拒绝无沙盒组合
        推导默认=自身.派生(空旋钮)#从组合默认推导预设
        显式默认=取字段(配置,'defaultPreset')#显式默认优先
        默认预设名=推导默认 if 显式默认 is None else 显式默认#解析默认
        if 默认预设名==自定义预设:#推导落到 custom 则必须显式配置
            raise Exception('permission: composed sandbox and approval defaults match no preset; configure defaultPreset explicitly')#拒绝含糊默认
        自身.解析(默认预设名)#启动时就证明默认可解析
        基础设置={'defaultPreset':默认预设名}#基础设置快照
        自身.defaultSettings=lambda:基础设置#尚无设置提供方时用基础
        自身.默认设置源=自身.defaultSettings#中文别名槽
        预设选项=[]#设置模式的预设选项
        for 名 in 自身.names:#按表序
            选项=模式.常量(名)#字面量选项
            标签=取字段(取字段(自身.presets,名),'name')#可选展示名
            if 标签 is not None:#有标签
                选项=选项.描述(标签)#带上标签
            预设选项.append(选项)#收下
        设置模式=模式.对象({#用户设置模式
            'defaultPreset':模式.联合(预设选项).必填(),#必填默认预设
        })#settingsSchema 结束
        def 设源(当前):#设置源更新
            """换成最新作用域快照 thunk。"""
            自身.defaultSettings=当前#换成最新
            自身.默认设置源=当前#同步中文别名槽
        安装设置段(ctx,权限设置命名空间,设置模式,基础设置,{#安装设置段
            'setSource':设源,#源更新
            'onChange':lambda:None,#变更空操作；源 thunk 在会话创建时读最新作用域快照
        })#设置段结束
        def 会话已创建(会话,*其余):#新会话钉初始权限
            """补齐缺失事实。"""
            自身.钉初始权限(会话)#补齐
        ctx.on('session/created',会话已创建)#created 监听
        for 会话 in ctx.sessions.list():#已加载会话同样钉
            自身.钉初始权限(会话)#补齐缺失事实
        def 投影安装(投影上下文,*其余):#有投影注册表才登记
            """权限投影单元：折叠三条整值旋钮事件；视图在本服务已拥有的组合默认上派生选择。仅在组合了投影注册表时激活该子件。"""
            投影上下文.sessionProjections.register({#登记 permissions 单元
                'key':'permissions',#投影键
                'schema':权限选择投影模式,#载荷模式
                'init':lambda:dict(空旋钮),#空日志初态（脱离副本）
                'apply':应用旋钮事件,#单事件转移
                'view':lambda 状态:自身.选择于(状态),#派生选择
                'stateVersion':1,#状态版本
            })#register 结束
        ctx.inject(['sessionProjections'],投影安装)#inject 投影结束
        def 命令安装(命令上下文,*其余):#有命令注册表才登记
            """/permission 命令：web 客户端使用的唯一写路径。仅在组合了命令注册表时激活该子件。"""
            def 处理(调用):#直接切换或报告当前
                """无参报告当前；有参则切换。"""
                智能体=取字段(调用,'agent')#调用方智能体
                原文=取字段(调用,'rawInput')#原始输入
                if 原文 is None:#缺席
                    原文=''#空
                名=原文.strip()#去掉两端空白
                if 名=='':#无参数则报告当前
                    return {'kind':'success','text':'current preset '+自身.当前(取字段(取字段(智能体,'session'),'events'))+' (available: '+', '.join(自身.names)+')'}#当前与可用列表
                if 名 not in 自身.names:#未知预设
                    return {'kind':'error','text':'unknown preset "'+名+'" (available: '+', '.join(自身.names)+')'}#报告未知
                def 写审批(策略):#存活路径走审批服务切换
                    """经审批服务切策略。"""
                    自身.ctx.approval.设策略(智能体,策略)#带叙述的切换
                自身.应用(取字段(智能体,'session'),名,写审批)#共享写路径
                return {'kind':'success','text':'preset '+名}#简短结算
            命令上下文.commands.register({#登记 /permission
                'name':'permission',#命令名
                'description':'Switch the permission preset (sandbox mode + approval policy)',#发现摘要，字面量不翻译
                'input':{'hint':'<preset>'},#输入占位
                'handler':处理,#处理函数
            })#register 结束
        ctx.inject(['commands'],命令安装)#inject 命令结束

    @property#只读属性
    def names(自身):#公布的预设名
        """公布的预设名，按预设表声明顺序。"""
        return list(自身.presets.keys())#声明顺序的键

    @property#只读属性
    def 名表(自身):#中文别名
        """中文别名。"""
        return 自身.names#委托

    @property#只读属性
    def defaultPreset(自身):#未来会话默认
        """当前选为未来会话默认的预设。已解析的设置值；没有挂载设置提供方时为组合默认。"""
        return 取字段(自身.defaultSettings(),'defaultPreset')#读当前设置源

    @property#只读属性
    def 默认预设(自身):#中文别名
        """中文别名。"""
        return 自身.defaultPreset#委托

    def 当前(自身,事件们):#当前生效预设
        """解析匹配生效旋钮值的预设。仍匹配的上次选择在共享捆平局时胜出；否则第一个表匹配胜出；没有条目匹配则为 CUSTOM_PRESET。"""
        return 自身.派生(折叠旋钮(事件们))#先折叠再派生

    def 派生(自身,状态):#从旋钮状态派生预设名
        """为一份已折叠旋钮状态解析预设（current 与投影单元的共享数学）。"""
        沙盒=取字段(状态,'sandbox')#覆盖
        if 沙盒 is None:#无覆盖
            沙盒=取字段(自身.ctx.shell,'sandboxMode')#组合默认
        审批=取字段(状态,'approval')#覆盖
        if 审批 is None:#无覆盖
            审批=取字段(取字段(自身.ctx.approval,'config'),'policy')#配置默认
            if 审批 is None:#再缺
                审批='ask'#ask
        def 匹配(规格):#捆是否匹配
            """沙盒与审批是否同时相等。"""
            return 取字段(规格,'sandbox')==沙盒 and 取字段(规格,'approval')==审批#捆匹配
        上次=取字段(状态,'preset')#有上次选择
        if 上次 is not None:#有上次选择
            规格=取字段(自身.presets,上次)#查表
            if 规格 is not None and 匹配(规格):#仍匹配则保住意图
                return 上次#保住
        for 名,规格 in 自身.presets.items():#按表序找第一匹配
            if 匹配(规格):#第一匹配胜出
                return 名#胜出
        return 自定义预设#无匹配则派生 custom

    def 选择于(自身,状态):#构建选择投影
        """为一份已折叠旋钮状态构建完整选择值：按声明顺序的每个表选项；恰好在派生成 custom 时追加它。"""
        当前值=自身.派生(状态)#当前值
        选项=[自身.选项于(名) for 名 in 自身.names]#表内选项
        if 当前值==自定义预设:#仅当前是 custom 时追加
            选项=选项+[自身.选项于(自定义预设)]#追加 custom
        return {'options':选项,'currentValue':当前值}#完整选择

    def 解析(自身,名):#按名解析捆
        """解析一条预设的旋钮捆。名不在表里则抛出。"""
        规格=取字段(自身.presets,名)#查表
        if 规格 is None:#未知名
            raise Exception('permission: unknown preset "'+名+'" (known: '+', '.join(自身.presets.keys())+')')#大声失败
        return 规格#返回捆

    def 选项于(自身,名):#构建展示选项
        """为表条目或 CUSTOM_PRESET 构建客户端选项。缺标签则回退到表键。名既不是表键也不是 custom 则抛出。"""
        if 名==自定义预设:#派生状态
            return {'value':自定义预设,'name':'Custom','description':'Current sandbox and approval settings do not match a preset.'}#固定 custom 选项，字面量不翻译
        规格=自身.解析(名)#未知名在此抛
        展示=取字段(规格,'name')#可选展示名
        if 展示 is None:#缺标签
            展示=名#回退表键
        结果={'value':名,'name':展示}#表键加展示名
        说明=取字段(规格,'description')#可选说明
        if 说明 is not None:#有说明
            结果['description']=说明#带上
        return 结果#客户端渲染的选项

    def 设(自身,会话,名):#初始化路径切换
        """记下已变预设，再经各自 setter 更新每个已变旋钮。再次选择生效预设则什么也不追加。"""
        def 写审批(策略):#直接写审批覆盖事件
            """初始化路径：无先前可见策略可改。"""
            设审批策略(会话,策略)#直接写事件
        自身.应用(会话,名,写审批)#共享写路径

    def 应用(自身,会话,名,设审批):#共享写路径
        """用调用方选定的存活或初始化策略写入器应用一条预设。"""
        规格=自身.解析(名)#先证明可解析
        if 自身.当前(取字段(会话,'events'))!=名:#与当前不同才记意图
            会话.追加('permission/preset',{'preset':名})#写下所选预设
        事件们=取字段(会话,'events')#追加后的日志
        生效沙盒=生效沙盒模式(事件们)#当前沙盒覆盖
        if 生效沙盒 is None:#无覆盖
            生效沙盒=取字段(自身.ctx.shell,'sandboxMode')#组合默认
        if 取字段(规格,'sandbox')!=生效沙盒:#沙盒已变
            设沙盒模式(会话,取字段(规格,'sandbox'))#经权威 setter 写
        生效审批=生效审批策略(事件们)#当前审批覆盖
        if 生效审批 is None:#无覆盖
            生效审批=取字段(取字段(自身.ctx.approval,'config'),'policy')#配置
            if 生效审批 is None:#再缺
                生效审批='ask'#ask
        if 取字段(规格,'approval')!=生效审批:#审批已变
            设审批(取字段(规格,'approval'))#经调用方选定的写入器

    def 钉初始权限(自身,会话):#钉初始权限事实
        """在会话被发布之前补齐每条缺失的权限事实。真正全新的会话使用当前用户默认；已播种或部分初始化的会话保住其生效旋钮值，只补上缺失的持久事实。"""
        事件们=取字段(会话,'events')#当前日志
        已选=生效权限预设(事件们)#已记预设
        沙盒=生效沙盒模式(事件们)#已记沙盒
        审批=生效审批策略(事件们)#已记审批
        已播种=False#是否播种会话
        for 事件 in 事件们 or []:#扫描种子边界
            if 取字段(事件,'type')=='session/end-seed':#命中
                已播种=True#已播种
                break#停
        if 已选 is None and 沙盒 is None and 审批 is None and (not 已播种):#真正全新
            名=自身.defaultPreset#用户默认
            规格=自身.解析(名)#解析捆
            会话.追加('permission/preset',{'preset':名})#写下预设
            设沙盒模式(会话,取字段(规格,'sandbox'))#写下沙盒
            设审批策略(会话,取字段(规格,'approval'))#写下审批
            return#全新路径结束
        状态={#从已有覆盖建状态
            'preset':已选,#已记或无（None）
            'sandbox':沙盒,#已记或无
            'approval':审批,#已记或无
        }#state 结束
        生效=自身.派生(状态)#派生当前预设
        if 已选 is None and 生效!=自定义预设:#缺预设意图但能对上表
            会话.追加('permission/preset',{'preset':生效})#补记意图
        if 沙盒 is None:#缺沙盒覆盖
            设沙盒模式(会话,取字段(自身.ctx.shell,'sandboxMode'))#用组合默认钉上
        if 审批 is None:#缺审批覆盖
            配置策略=取字段(取字段(自身.ctx.approval,'config'),'policy')#配置或 ask
            if 配置策略 is None:#再缺
                配置策略='ask'#ask
            设审批策略(会话,配置策略)#用配置或 ask 钉上

default=权限预设服务#Cordis 默认导出
默认=权限预设服务#中文默认导出
