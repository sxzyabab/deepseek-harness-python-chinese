"""盖在独立沙盒模式与审批策略旋钮上的面向用户权限预设。一次切换先记下所选预设，再经各自权威 setter 写入已变旋钮。执行、提示词叙述和回放继续读各自的旋钮折叠。当两个预设共享同一捆旋钮时，预设事件保住用户意图。读侧作为 `permissions` 会话投影交付；写侧作为 `/permission` 命令交付——两者都是同一服务上的可选子件。"""
from ...依赖 import cordis#外部依赖胶水
from ...依赖.schemastery import 字符串字段,枚举字段,常量字段,复合类型字段#配置字段
服务=cordis.服务#Cordis 服务基类
from ...配置.配置 import 安装设置段,设置命名空间#设置段安装与命名空间
from ...交互.命令.标识构造 import 命令定义标识#命令定义身份
from ...沙盒.沙盒策略 import 沙盒模式表,生效沙盒模式,设沙盒模式#沙盒模式表、折叠与写入
from ..用户审批 import 审批策略表,生效审批策略,设审批策略#审批策略表、折叠与写入
from .类型 import (#再导出权限域纯类型
    预设选项字段,#预设选项字段
    权限目录字段,#进程目录字段
    权限选择字段,#权限选择字段
)#类型再导出结束

自定义预设='custom'#派生的非预设状态名
自动预设='auto'#实验性按次审查预设名
自动预设捆={#在线 Auto 集成的固定执行捆
    'sandbox':'danger-full-access',#全开
    'approval':'never',#不问
}#自动预设捆结束
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
预设捆模式={#单条预设的旋钮捆
    'sandbox':枚举字段(*list(沙盒模式表),可空=False),#必填沙盒模式
    'approval':枚举字段(*list(审批策略表),可空=False),#必填审批策略
    'name':字符串字段(),#可选展示名
    'description':字符串字段(),#可选说明
}#预设捆模式结束
配置模式={#插件配置：预设表与组合默认
    'defaultPreset':字符串字段(),#可选组合默认预设名
}#配置模式结束
空旋钮={'preset':None,'sandbox':None,'approval':None}#空日志的旋钮状态
权限选择投影模式={#`permissions` 投影的线上载荷模式
    'type':'object',#对象
    'additionalProperties':False,#禁多余键
    'properties':{#字段
        'currentValue':{'type':'string','minLength':1},#非空当前值
    },#字段结束
    'required':['currentValue'],#当前值必填
}#投影模式结束

class 权限预设错误(Exception):#本包配置与解析失败
    """权限预设配置或名解析非法。"""
    def __init__(自身,消息):#记下英文消息
        """用原样英文消息构造。"""
        super().__init__(消息)#英文消息

def 生效权限预设(事件列表):#从日志折叠所选预设
    """从持久日志折叠最后一次所选预设。事件是 dict。"""
    if 事件列表 is None:#无日志
        return None#从未选择
    for 下标 in range(len(事件列表)-1,-1,-1):#从后往前找
        事件=事件列表[下标]#取该条事件
        if 事件['type']=='permission/preset':#命中最后一次选择
            return 事件['data']['preset']#返回所选预设
    return None#从未选择

def 应用旋钮事件(状态,事件):#应用一条旋钮事件
    """单事件旋钮转移。状态与事件都是 dict。"""
    种类=事件['type']#事件类型
    数据=事件['data'] if 'data' in 事件 else None#事件载荷
    if 种类=='permission/preset':#预设意图
        return {'preset':数据['preset'],'sandbox':状态['sandbox'],'approval':状态['approval']}#记下所选预设
    if 种类=='sandbox/mode':#沙盒模式
        return {'preset':状态['preset'],'sandbox':数据['mode'],'approval':状态['approval']}#记下沙盒覆盖
    if 种类=='approval/policy':#审批策略
        return {'preset':状态['preset'],'sandbox':状态['sandbox'],'approval':数据['policy']}#记下审批覆盖
    return 状态#无关事件保持同一引用

def 折叠旋钮(事件列表):#冷读折叠全部旋钮
    """整份日志的旋钮折叠。"""
    状态=空旋钮#从空状态起
    if 事件列表 is None:#无日志
        return 状态#空
    for 事件 in 事件列表:#逐事件转移
        状态=应用旋钮事件(状态,事件)#转移
    return 状态#返回折叠结果

def 空设置变更():#设置段变更空操作
    """源 thunk 在会话创建时读最新作用域快照。"""
    return None#空操作

class 权限预设服务(服务):#权限预设服务：拥有部署的权限预设及其写路径
    """拥有部署的权限预设及其写路径。要求有约束的 `ctx.shell` 执行器与 `ctx.approval`；不匹配的旋钮值报成 CUSTOM_PRESET，不是错误。"""
    Config=配置模式#插件配置模式
    inject=['shell','approval','sessions']#依赖沙盒执行器、审批与会话
    def __init__(自身,ctx,配置=None):#构造预设服务
        """以 permissionPresets 名安装服务。配置是 dict。"""
        if 配置 is None:#缺省空配置
            配置={}#空
        super().__init__(ctx,'permissionPresets')#以 permissionPresets 名安装服务
        预设表=配置['presets'] if 'presets' in 配置 else None#取已默认的表
        if 预设表 is None:#模式应已填默认
            预设表=默认预设表#回落默认表
        自身.预设表=dict(预设表)#运行时预设表（脱离副本）
        自身.自动准入=None#在线 Auto 准入
        if 自定义预设 in 自身.预设表:#custom 不得当表键
            raise 权限预设错误('permission: "'+自定义预设+'" is reserved for the derived not-a-preset state and cannot name a table entry')#拒绝占用保留名
        if 自动预设 in 自身.预设表:#auto 不得当表键
            raise 权限预设错误('permission: "'+自动预设+'" is reserved and cannot name a configured preset')#拒绝占用保留名
        if 自身.ctx.shell.sandboxMode is None:#执行器不约束
            raise 权限预设错误('permission: the mounted bash executor does not confine (no sandboxMode) — presets bundle a sandbox mode, so composing this plugin over an unconfined executor is a misconfiguration')#拒绝无沙盒组合
        推导默认=自身.派生(空旋钮)#从组合默认推导预设
        显式默认=配置['defaultPreset'] if 'defaultPreset' in 配置 else None#显式默认优先
        默认预设名=推导默认 if 显式默认 is None else 显式默认#解析默认
        if 默认预设名==自定义预设:#推导落到 custom 则必须显式配置
            raise 权限预设错误('permission: composed sandbox and approval defaults match no preset; configure defaultPreset explicitly')#拒绝含糊默认
        自身.解析(默认预设名)#启动时就证明默认可解析
        基础设置={'defaultPreset':默认预设名}#基础设置快照
        def 取基础设置():#尚无设置提供方时用基础
            """返回基础设置快照。"""
            return 基础设置#基础
        自身.默认设置源=取基础设置#当前设置源
        预设选项=[]#设置模式的预设选项
        for 名 in 自身.名表:#按表序
            捆=自身.预设表[名]#该档捆
            标签=捆['name'] if 'name' in 捆 else None#可选展示名
            if 标签 is not None:#有标签
                选项=常量字段(名,描述=标签)#带上标签
            else:#无标签
                选项=常量字段(名)#字面量选项
            预设选项.append(选项)#收下
        设置模式={#用户设置模式
            'defaultPreset':复合类型字段(*预设选项,可空=False),#必填默认预设
        }#settingsSchema 结束
        def 设源(当前):#设置源更新
            """换成最新作用域快照 thunk。"""
            自身.默认设置源=当前#换成最新
        安装设置段(ctx,权限设置命名空间,设置模式,基础设置,{#安装设置段
            'setSource':设源,#源更新
            'onChange':空设置变更,#变更空操作
        })#设置段结束
        def 会话已创建(会话,*位置参数):#新会话钉初始权限
            """补齐缺失事实。"""
            自身.钉初始权限(会话)#补齐
        ctx.监听('session/created',会话已创建)#created 监听
        for 会话 in ctx.sessions.列出():#已加载会话同样钉
            自身.钉初始权限(会话)#补齐缺失事实
        def 投影初态():#空日志初态
            """空日志初态（脱离副本）。"""
            return dict(空旋钮)#脱离副本
        def 投影视图(状态):#只看当前值
            """线路只看当前值。"""
            return {'currentValue':自身.派生(状态)}#当前值
        def 投影安装(投影上下文,*位置参数):#有投影注册表才登记
            """权限投影单元。"""
            投影上下文.sessionProjections.register({#登记 permissions 单元
                'key':'permissions',#投影键
                'schema':权限选择投影模式,#载荷模式
                'init':投影初态,#空日志初态
                'apply':应用旋钮事件,#单事件转移
                'view':投影视图,#派生选择
                'stateVersion':1,#状态版本
            })#register 结束
        ctx.依赖启动(['sessionProjections'],投影安装)#依赖启动投影结束
        def 命令安装(命令上下文,*位置参数):#有命令注册表才登记
            """/permission 命令。"""
            def 处理(调用):#直接切换或报告当前
                """无参报告当前；有参则切换。调用是 dict。"""
                智能体=调用['agent']#调用方智能体
                原文=调用['rawInput'] if 'rawInput' in 调用 else ''#原始输入
                if 原文 is None:#缺席
                    原文=''#空
                名=原文.strip()#去掉两端空白
                if 名=='':#无参数则报告当前
                    return {'kind':'success','text':'current preset '+自身.当前(智能体.session.events)+' (available: '+', '.join(自身.名表)+')'}#当前与可用列表
                if 名 not in 自身.名表:#未知预设
                    return {'kind':'error','text':'unknown preset "'+名+'" (available: '+', '.join(自身.名表)+')'}#报告未知
                def 写审批(策略):#存活路径走审批服务切换
                    """经审批服务切策略。"""
                    自身.ctx.approval.设策略(智能体,策略)#带叙述的切换
                自身.应用(智能体.session,名,写审批)#共享写路径
                return {'kind':'success','text':'preset '+名}#简短结算
            命令上下文.commands.登记({#登记 /permission
                'definitionId':命令定义标识('@deepseek-ai/dsh-permission-presets'),#稳定定义身份
                'name':'permission',#命令名
                'description':'Switch the permission preset (sandbox mode + approval policy)',#发现摘要，字面量不翻译
                'input':{'hint':'<preset>'},#输入占位
                'handler':处理,#处理函数
            })#register 结束
        ctx.依赖启动(['commands'],命令安装)#依赖启动命令结束

    @property#只读属性
    def 名表(自身):#公布的预设名
        """公布的预设名：配置表按声明顺序，Auto 在其集成在线时跟在后面。"""
        名列表=list(自身.预设表.keys())#声明顺序的键
        if 自身.自动准入 is not None:#Auto 在线
            名列表=名列表+[自动预设]#跟上 Auto
        return 名列表#可切换名

    def 目录(自身):#进程目录
        """读出现在会话 UI 所用的完整进程级目录。"""
        选项=[]#可选项
        for 名 in 自身.名表:#按贡献顺序
            选项.append(自身.选项于(名))#收下
        return {'options':选项}#目录

    def 登记自动(自身,准入):#登记 Auto
        """在调用方集成寿命内公布固定的当前会话 Auto 预设。准入是同步门。"""
        def 安装():
            """挂上 Auto 并在拆除时摘掉。"""
            if 自身.自动准入 is not None:#已经登记
                raise 权限预设错误('permission: preset "auto" is already registered')#重复登记
            自身.自动准入=准入#记下准入
            自身.发出目录已变()#目录已变
            def 拆除():
                """去掉 Auto。"""
                自身.自动准入=None#清掉
                自身.发出目录已变()#目录已变
            return 拆除#拆除器
        return 自身.ctx.副作用(安装,'permissionPresets.registerAuto()')#effect 寿命

    @property#只读属性
    def 默认预设(自身):#未来会话默认
        """当前选为未来会话默认的预设。"""
        快照=自身.默认设置源()#读当前设置源
        return 快照['defaultPreset']#已解析的设置值

    def 当前(自身,事件列表):#当前生效预设
        """解析匹配生效旋钮值的预设。"""
        return 自身.派生(折叠旋钮(事件列表))#先折叠再派生

    def 派生(自身,状态):#从旋钮状态派生预设名
        """为一份已折叠旋钮状态解析预设。状态是 dict。"""
        沙盒=状态['sandbox']#覆盖
        if 沙盒 is None:#无覆盖
            沙盒=自身.ctx.shell.sandboxMode#组合默认
        审批=状态['approval']#覆盖
        if 审批 is None:#无覆盖
            审批配置=自身.ctx.approval.配置#审批插件配置
            审批=审批配置['policy'] if 'policy' in 审批配置 else None#配置默认
            if 审批 is None:#再缺
                审批='ask'#ask
        def 匹配(规格):#捆是否匹配
            """沙盒与审批是否同时相等。规格是 dict。"""
            return 规格['sandbox']==沙盒 and 规格['approval']==审批#捆匹配
        上次=状态['preset']#有上次选择
        if 上次 is not None:#有上次选择
            规格=自身.规格于(上次)#查表或在线 Auto
            if 规格 is not None and 匹配(规格):#仍匹配则保住意图
                return 上次#保住
        for 名,规格 in 自身.预设表.items():#按表序找第一匹配
            if 匹配(规格):#第一匹配胜出
                return 名#胜出
        return 自定义预设#无匹配则派生 custom

    def 解析(自身,名):#按名解析捆
        """解析一条预设的旋钮捆。名不在表里则抛出。"""
        规格=自身.规格于(名)#查表或在线 Auto
        if 规格 is None:#未知名
            raise 权限预设错误('permission: unknown preset "'+名+'" (known: '+', '.join(自身.名表)+')')#大声失败
        return 规格#返回捆

    def 选项于(自身,名):#构建展示选项
        """为可用预设或 CUSTOM_PRESET 构建客户端选项。"""
        if 名==自定义预设:#派生状态
            return {'value':自定义预设,'name':'Custom','description':'Current sandbox and approval settings do not match a preset.'}#固定 custom 选项
        规格=自身.解析(名)#未知名在此抛
        展示=规格['name'] if 'name' in 规格 else None#可选展示名
        if 展示 is None:#缺标签
            展示=名#回退表键
        结果={'value':名,'name':展示}#表键加展示名
        if 'description' in 规格 and 规格['description'] is not None:#有说明
            结果['description']=规格['description']#带上
        return 结果#客户端渲染的选项

    def 设(自身,会话,名):#初始化路径切换
        """记下已变预设，再经各自 setter 更新每个已变旋钮。"""
        def 写审批(策略):#直接写审批覆盖事件
            """初始化路径：无先前可见策略可改。"""
            设审批策略(会话,策略)#直接写事件
        自身.应用(会话,名,写审批)#共享写路径

    def 应用(自身,会话,名,设审批):#共享写路径
        """用调用方选定的存活或初始化策略写入器应用一条预设。"""
        规格=自身.解析(名)#先证明可解析
        if 名==自动预设 and 自身.自动准入 is not None:#在线 Auto 先过准入
            自身.自动准入()#准入
        当前=自身.当前(会话.events)#当前生效
        事件列表=会话.events#追加前的日志
        生效沙盒=生效沙盒模式(事件列表)#当前沙盒覆盖
        if 生效沙盒 is None:#无覆盖
            生效沙盒=自身.ctx.shell.sandboxMode#组合默认
        生效审批=生效审批策略(事件列表)#当前审批覆盖
        if 生效审批 is None:#无覆盖
            审批配置=自身.ctx.approval.配置#审批插件配置
            生效审批=审批配置['policy'] if 'policy' in 审批配置 else None#配置
            if 生效审批 is None:#再缺
                生效审批='ask'#ask
        if 当前!=名:#与当前不同才记意图
            会话.追加('permission/preset',{'preset':名})#写下所选预设
        if 规格['sandbox']!=生效沙盒:#沙盒已变
            设沙盒模式(会话,规格['sandbox'])#经权威 setter 写
        if 规格['approval']!=生效审批:#审批已变
            设审批(规格['approval'])#经调用方选定的写入器

    def 钉初始权限(自身,会话):#钉初始权限事实
        """在会话被发布之前补齐每条缺失的权限事实。"""
        事件列表=会话.events#当前日志
        已选=生效权限预设(事件列表)#已记预设
        沙盒=生效沙盒模式(事件列表)#已记沙盒
        审批=生效审批策略(事件列表)#已记审批
        已播种=False#是否播种会话
        扫描=事件列表 if 事件列表 is not None else []#可扫描日志
        for 事件 in 扫描:#扫描种子边界
            if 事件['type']=='session/end-seed':#命中
                已播种=True#已播种
                break#停
        if 已选==自动预设:#日志里是 Auto
            if 自身.自动准入 is None:#集成不在线
                raise 权限预设错误('permission: cannot restore preset "auto" without its active integration')#拒绝恢复
            自身.自动准入()#过准入
        if 已选 is None and 沙盒 is None and 审批 is None and (not 已播种):#真正全新
            名=自身.默认预设#用户默认
            规格=自身.解析(名)#解析捆
            会话.追加('permission/preset',{'preset':名})#写下预设
            设沙盒模式(会话,规格['sandbox'])#写下沙盒
            设审批策略(会话,规格['approval'])#写下审批
            return#全新路径结束
        状态={#从已有覆盖建状态
            'preset':已选,#已记或无
            'sandbox':沙盒,#已记或无
            'approval':审批,#已记或无
        }#state 结束
        生效=自身.派生(状态)#派生当前预设
        if 已选 is None and 生效!=自定义预设:#缺预设意图但能对上表
            会话.追加('permission/preset',{'preset':生效})#补记意图
        if 沙盒 is None:#缺沙盒覆盖
            设沙盒模式(会话,自身.ctx.shell.sandboxMode)#用组合默认钉上
        if 审批 is None:#缺审批覆盖
            审批配置=自身.ctx.approval.配置#配置
            配置策略=审批配置['policy'] if 'policy' in 审批配置 else None#配置或 ask
            if 配置策略 is None:#再缺
                配置策略='ask'#ask
            设审批策略(会话,配置策略)#用配置或 ask 钉上

    def 发出目录已变(自身):#目录失效
        """发出无载荷、不可否决的目录失效通知。"""
        派发=自身.ctx.events.dispatch#事件派发
        监听器列表=派发('emit',['permission-presets/catalog-changed'])#取出监听器
        for 监听器 in 监听器列表:#逐个
            try:#监听器可能抛
                监听器()#同步调用
            except Exception as 错误:#失败只警告
                自身.ctx.日志.警告('permission: catalog-changed listener failed: '+str(错误))#记日志

    def 规格于(自身,名):#查表或 Auto
        """解析一条已配置或当前在线的固定预设，不抛。"""
        if 名 in 自身.预设表:#表内
            return 自身.预设表[名]#已配置捆
        if 名==自动预设 and 自身.自动准入 is not None:#在线 Auto
            return 自动预设捆#固定捆
        return None#未知

__all__=[#仅中文公开名
    '自定义预设','自动预设','权限设置命名空间','默认预设表','配置模式','空旋钮',
    '权限选择投影模式','生效权限预设','应用旋钮事件','折叠旋钮',
    '权限预设错误','权限预设服务','预设选项字段','权限目录字段','权限选择字段',
]#公开面结束
name='permission-presets'#Cordis插件名
Config=配置模式#Cordis配置模式
default=权限预设服务#Cordis默认导出
