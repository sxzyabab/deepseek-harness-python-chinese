import os#文件戳
from ...依赖 import cordis#外部依赖胶水
from ...依赖.schemastery import 字符串字段,枚举字段,布尔字段,列表字段#配置字段
服务=cordis.服务#Cordis 服务基类
from ...内核.作用域 import 绑定作用域父,创建作用域,获取作用域,弱身份表#作用域
from ...配置.配置 import 设置命名空间#设置命名空间
from ...工具.工作区路径 import 主目录路径#harness 主目录路径
from .发现 import 组合文件,用户预设目录,发现预设,扫描根,条目列表问题#发现
from .编写 import (#编写
    复制组合,删除组合,读组合,可写根,
    非法预设标识错误,预设已存在错误,预设不可写错误,
)#编写结束
from .挂载 import (#挂载
    挂载预设,智能体服务,常驻挂载于,活预设挂载,泄漏服务,未激活行,
)#挂载结束
from .元数据 import 元数据文件,读预设元数据,渲染预设元数据#元数据
from .会话 import 解析会话预设#会话预设
from .预设 import 预设错误,预设挂载错误,未知预设错误#预设错误
from . import 类型 as _类型#触发客户端安全事件声明
import yaml#组合 YAML
from threading import Lock as 锁#选择串行

设置空间名='agent-presets'#设置命名空间
附带预设根=os.path.join(os.path.dirname(__file__),'presets')#包内附带预设根
智能体预设设置模式={#用户可写设置
    'default':字符串字段(),#默认预设 id
    'modeSelectionEnabled':布尔字段(),#是否启用模式选择
}#设置模式结束

def 组合戳(路径):
    """读一个组合文件的戳；无法 stat 时为 None。mtime 为纪元毫秒 float，size 为 int。"""
    try:#stat
        信息=os.stat(路径)#取出
        return {'mtimeMs':信息.st_mtime*1000.0,'size':信息.st_size}#文件身份
    except OSError:#无法 stat
        return None#无戳

def 同戳(甲,乙):
    """两个戳是否命名同一文件状态。"""
    return 甲['mtimeMs']==乙['mtimeMs'] and 甲['size']==乙['size']#时间与大小

def 校验预设标识(值,字段):
    """空 id 在点名域操作前拒绝。"""
    if 值=='':#空
        raise 预设错误(字段+' must be a non-empty string')#拒绝

def 初始化预设投影(头):
    """从会话头取出创建时预设。"""
    if 头 is None:#无头
        return None#空
    return 头['agentPreset'] if 'agentPreset' in 头 else None#创建时值

def 应用预设投影(状态,事件):
    """选定事件推进当前预设。"""
    if 事件['type']=='agent-preset/selected':#选定
        载荷=事件['data'] if 'data' in 事件 else {}#载荷
        return 载荷['agentPreset'] if 'agentPreset' in 载荷 else 状态#新值
    return 状态#原样

def 查看预设投影(状态):
    """投影对外视图。"""
    return 状态#原样

智能体预设投影定义={#会话投影
    'key':'agentPreset',#键
    'init':初始化预设投影,#初始化
    'apply':应用预设投影,#应用事件
    'wire':{'view':查看预设投影},#对外
    'stateVersion':1,#世代
}#投影结束

def 是否js表达式(值):
    """加载器 !!js 节点。"""
    if isinstance(值,dict) and '__jsExpr' in 值:#映射
        return True#是
    return getattr(值,'__jsExpr',None) is not None#对象

def 禁用贡献(值,求值):
    """一行 disabled 对有效启用的贡献。"""
    if 是否js表达式(值):#表达式
        表达式=值['__jsExpr'] if isinstance(值,dict) else 值.__jsExpr#原文
        try:#求值
            return bool(求值(表达式))#布尔
        except Exception:#拒绝猜测
            return 'conditional'#留给挂载
    return bool(值)#字面

def 合并禁用(外层,自身禁用):
    """祖先组与本行禁用，任意字面 true 即禁用。"""
    if 外层 is True or 自身禁用 is True:#字面禁用
        return True#禁用
    if 外层=='conditional' or 自身禁用=='conditional':#表达式
        return 'conditional'#条件
    return False#启用

def 展平行列表(行列表,外层禁用,求值,已收):
    """组行只结构，子行才进清单。"""
    for 行 in 行列表:#逐行
        禁用=合并禁用(外层禁用,禁用贡献(行.get('disabled') if isinstance(行,dict) else None,求值))#有效禁用
        if isinstance(行,dict) and 行.get('group') is True:#组
            展平行列表(行.get('config') or [],禁用,求值,已收)#子行
            continue#下一
        条件={}#可选条件
        本禁用=行.get('disabled') if isinstance(行,dict) else None#本行 disabled
        if 是否js表达式(本禁用):#带表达式
            条件['condition']=本禁用['__jsExpr'] if isinstance(本禁用,dict) else 本禁用.__jsExpr#原文
        标识=行.get('id') if isinstance(行,dict) else None#条目 id
        已收.append({#一行
            'entryId':标识 if isinstance(标识,str) and 标识!='' else None,#id
            'moduleName':行.get('name') if isinstance(行,dict) else None,#模块
            'enabled':False if 禁用 is True else ('conditional' if 禁用=='conditional' else True),#启用
            **条件,#条件
        })#结束

class 智能体预设名册(服务):
    """部署的智能体预设上的注册表。发现不做记忆化。"""
    inject=['loader','sessionProjections']#Cordis 依赖声明
    Config={#插件配置模式
        'default':字符串字段(可空=False),#必填默认预设 id
        'roots':列表字段(({#扫描根
            'path':字符串字段(可空=False),#根路径
            'trust':枚举字段('system','user',默认值='user'),#默认用户信任
        }),默认值=[]),#默认无已配置根
        'includeShippedRoot':布尔字段(默认值=True),#默认前置附带根
        'includeUserRoot':布尔字段(默认值=True),#默认追加用户根
    }#配置模式结束

    def __init__(自身,ctx,配置=None):
        """登记服务、派生扫描根、接线设置与咨询性监听。配置是 dict。"""
        if 配置 is None:#缺省
            配置={}#空
        super().__init__(ctx,'agentPresets')#注册为 agentPresets
        自身.config=配置#配置
        自身.selfCtx=ctx#未追踪的本服务上下文
        基础地址=getattr(ctx,'基础地址',None) or getattr(ctx,'baseUrl',None) or getattr(ctx,'基准网址',None)#harness 基址
        if 基础地址 is None:#无名册解析锚
            raise 预设错误(
                'agent-presets: the roster needs `ctx.baseUrl` to resolve the plugins a composition names; '
                +'compose it under a Loader, or set the base on the context this plugin is applied to'
            )#拒绝
        自身.harnessBase=基础地址#解析包名的基址
        根列表=[]#扫描根
        if 'includeShippedRoot' not in 配置 or 配置['includeShippedRoot'] is not False:#缺键或非 False 则前置附带根
            根列表=根列表+[{'path':附带预设根,'trust':'system'}]#附带根最先
        根列表=根列表+list(配置['roots'] if 'roots' in 配置 and 配置['roots'] is not None else [])#已配置根
        if 'includeUserRoot' not in 配置 or 配置['includeUserRoot'] is not False:#缺键或非 False 则追加用户根
            根列表=根列表+[{'path':主目录路径(用户预设目录),'trust':'user'}]#追加 harness 用户根
        自身.resolvedRoots=根列表#解析后的扫描根
        自身.settings=None#用户设置作用域
        自身.settingsService=None#设置服务
        自身.standing={}#按 id 的常驻挂载单飞表
        自身.bindings=弱身份表()#智能体键 → 父绑定
        自身.switches={}#会话 id → 选择锁
        def 设置接线(设置上下文,*其余):
            """登记用户默认预设切片。"""
            配置默认=配置['default'] if 'default' in 配置 else None#组合层默认
            自身.settings=设置上下文.settings.登记(#注册命名空间
                设置命名空间(设置空间名),#agent-presets
                智能体预设设置模式,#用户切片模式
                {'base':{'default':配置默认,'modeSelectionEnabled':True}},#组合层默认
            )#结束登记
            自身.settingsService=设置上下文.settings#保住写入面
            def 挂拆():
                """清掉设置句柄。"""
                def 拆除():
                    """清掉。"""
                    自身.settings=None#清掉作用域
                    自身.settingsService=None#清掉服务
                return 拆除#拆除器
            设置上下文.副作用(挂拆,'agentPresets.settings()')#effect 名
        ctx.注册表.依赖启动(['settings'],设置接线)#有设置才接线
        投影服务=getattr(ctx,'sessionProjections',None) or getattr(ctx,'会话投影',None)#会话投影
        登记投影=getattr(投影服务,'register',None) or getattr(投影服务,'登记',None)#登记
        登记投影(智能体预设投影定义)#登记预设投影
        def 智能体已创建(载荷,*其余):
            """未加入预设的智能体警告一次。载荷是 dict。"""
            if 'agent' not in 载荷:#无智能体
                return#不过问
            智能体=载荷['agent']#智能体对象
            if len(自身.resolvedRoots)==0:#无名册
                return#不过问
            if 自身.composedPreset(智能体.ctx) is not None:#已加入
                return#过
            ctx.日志.警告(
                'agent "'+智能体.id+'" was published without joining an agent preset; '
                +'its tools, prompt sections, and skill catalog resolve against the empty global layer '
                +'(join through AgentPresets.mount() or composeFrom() in the agent factory setup)'
            )#警告
        ctx.监听('agent/created',智能体已创建)#咨询性检查
        def 会话事件(会话,事件,*其余):
            """耐久记录提交后发出公开事件。事件是 dict，会话是对象。"""
            if 事件['type']!='agent-preset/selected':#只关心预设选定
                return#放过
            载荷=事件['data']#事件载荷
            选定=载荷['agentPreset'] if 'agentPreset' in 载荷 else None#选定 id
            ctx.广播('agent-preset/selected',会话.id,选定)#公开事件
        ctx.监听('session/event',会话事件)#投影

    @property
    def defaultId(自身):
        """调用方未点名时挂载的预设 id。隐藏选择器时忽略陈旧用户默认。"""
        return 自身._选择策略()['defaultId']#策略有效默认

    def _选择策略(自身):
        """读一份内部一致的选择策略快照。"""
        if 自身.settings is None:#无用户层
            配置默认=自身.config['default'] if 'default' in 自身.config else None#配置默认
            return {'enabled':True,'defaultId':配置默认}#开选择、用配置默认
        切片=自身.settings.get()#用户切片 dict
        启用=切片['modeSelectionEnabled'] if 'modeSelectionEnabled' in 切片 else True#缺席则开
        配置默认=自身.config['default'] if 'default' in 自身.config else None#配置默认
        用户默认=切片['default'] if 'default' in 切片 else None#用户覆盖
        if 启用 is True:#启用模式选择
            if 用户默认 is not None and 用户默认!='':#有非空用户默认
                return {'enabled':True,'defaultId':用户默认}#用户覆盖
            return {'enabled':True,'defaultId':配置默认}#回落配置
        return {'enabled':False,'defaultId':配置默认}#关闭选择则忽略用户默认

    @property
    def roots(自身):
        """本名册扫描的根。"""
        return 自身.resolvedRoots#派生一次的根集

    @property
    def authorable(自身):
        """本部署是否有本地编写预设去往的根。"""
        for 根 in 自身.resolvedRoots:#有用户根即可写
            if 根['trust']=='user':#用户根
                return True#可写
        return False#不可写

    def list(自身):
        """已配置根当前提供的每个预设。"""
        包=自身.ctx.get('pluginPackages')#运行时包查找
        if 包 is None:#无名册解析器
            return 发现预设(自身.resolvedRoots)#重扫根
        def 解析(说明符,基址=None):
            """当前运行时包是否存在。"""
            return 包.packageOf(说明符,基址) is not None#有解析结果则在
        return 发现预设(自身.resolvedRoots,解析)#带运行时包查找

    def resolve(自身,标识=None):
        """按 id 解析一个预设。损坏的也能解析。"""
        想要=自身.defaultId if 标识 is None else 标识#缺省用默认
        预设列表=自身.list()#当前名册
        for 预设 in 预设列表:#按 id 查找
            if 预设['id']==想要:#命中
                return 预设#已解析行
        raise 未知预设错误(想要,[项['id'] for 项 in 预设列表])#未知预设

    def _解析可挂载(自身,标识=None):
        """解析即将组合智能体的一个预设，用发现报告的原因拒绝损坏的。"""
        预设=自身.resolve(标识)#先解析行
        损坏=预设['broken'] if 'broken' in 预设 else None#损坏原因
        if 损坏 is not None:#发现已报损坏
            raise 预设挂载错误(预设['id'],损坏)#用发现原因拒绝
        return 预设#可挂载

    def mount(自身,智能体上下文,标识=None):
        """从一个预设组合一个智能体。"""
        智能体键=获取作用域(智能体上下文)#智能体作用域键
        if 智能体键 is None:#无作用域无法加入
            raise 预设错误('agent-presets: refusing to compose an unscoped context; the scope key is what joins an agent to its preset')#拒绝
        预设=自身._解析可挂载(标识)#可挂载预设
        常驻=自身._确保常驻(预设)#确保常驻挂载
        自身.bindings.设(智能体键,绑定作用域父(智能体键,常驻['key']))#挂到常驻键下
        return 预设#供调用方记录

    def composeFrom(自身,智能体上下文,父上下文):
        """把一个智能体加入另一个已经在跑的同一份常驻组合。"""
        智能体键=获取作用域(智能体上下文)#子的作用域键
        if 智能体键 is None:#无作用域
            raise 预设错误('agent-presets: refusing to compose an unscoped context; the scope key is what joins an agent to its preset')#拒绝
        常驻=常驻挂载于(父上下文)#父已加入的常驻挂载
        if 常驻 is None:#父未加入
            return None#子也不加入
        绑定=绑定作用域父(智能体键,常驻['key'])#挂到同一常驻键
        自身.bindings.设(智能体键,绑定)#记下
        return 常驻['presetId']#加入的预设 id

    def composedPreset(自身,智能体上下文):
        """一个活智能体所跑的预设。"""
        常驻=常驻挂载于(智能体上下文)#常驻挂载
        return None if 常驻 is None else 常驻['presetId']#预设 id

    def read(自身,标识):
        """读一个预设的组合文本。"""
        return 读组合(自身.resolve(标识))#先解析再读

    def copy(自身,来源,标识,名称=None):
        """通过整份复制已有预设来创建本地编写的预设。"""
        源=自身.resolve(来源)#解析源
        for 预设 in 自身.list():#名册已有该 id
            if 预设['id']==标识:#占用
                raise 预设已存在错误(标识)#拒绝覆盖
        复制组合(自身.resolvedRoots,源,标识,名称)#整目录复制
        自身.standing.pop(标识,None)#丢掉过期常驻指针

    def remove(自身,标识):
        """删除本地编写的预设。"""
        删除组合(自身.resolvedRoots,自身.resolve(标识))#解析后删除
        自身.standing.pop(标识,None)#丢掉常驻指针
        if 自身.settings is None:#无用户设置
            return#不用清
        切片=自身.settings.get()#用户切片 dict
        if ('default' not in 切片) or 切片['default']!=标识:#用户默认不是这个
            return#不用清
        if 自身.settingsService is not None:#清掉用户默认
            自身.settingsService.改写(设置命名空间(设置空间名),[{'op':'unset','path':['default']}])#unset

    def serviceFor(自身,智能体,名):
        """一个智能体对其预设所挂服务的实例。"""
        return 智能体服务(自身.所属上下文,智能体,名)#委托

    def recompose(自身,智能体上下文,标识):
        """把一个智能体再链接到不同预设的常驻组合。"""
        智能体键=获取作用域(智能体上下文)#智能体作用域键
        if 智能体键 is None:#无作用域
            raise 预设错误('agent-presets: refusing to recompose an unscoped context')#拒绝
        预设=自身._解析可挂载(标识)#可挂载目标
        常驻=自身._确保常驻(预设)#确保新常驻挂载
        绑定=自身.bindings.取(智能体键)#已有父绑定
        if 绑定 is None:#从未组合过
            自身.bindings.设(智能体键,绑定作用域父(智能体键,常驻['key']))#初次挂上
        else:#已有绑定则再链接
            绑定.改接(常驻['key'])#改父到新常驻键
        try:#监听器可能抛
            自身.所属上下文.广播('tools/change')#通知工具集变更
        except BaseException as 错误:#监听失败只记日志
            自身.所属上下文.日志.警告('agent-presets: tools/change listener failed after recomposing an Agent: '+str(错误))#不阻断再组合
        return 预设#现在安装的预设

    def standingKeyFor(自身,标识=None):
        """一个预设的常驻作用域键，供没有智能体的宿主读取方。"""
        预设=自身._解析可挂载(标识)#可挂载预设
        return 自身._确保常驻(预设)['key']#常驻键

    def _确保常驻(自身,预设):
        """解析（或创建，单飞）一个预设的常驻挂载。预设是 dict。"""
        标识=预设['id']#预设 id
        if 标识 in 自身.standing:#已有指针
            已挂=自身.standing[标识]#本代已结算的挂载
            当前=组合戳(预设['path'])#当前文件戳
            if 当前 is None or 同戳(已挂['stamp'],当前):#戳相同或不可读
                return 已挂#沿用
            自身.standing.pop(标识,None)#丢掉过期
            return 自身._确保常驻(预设)#启动下一代
        def 创建():
            """创建本代常驻挂载。"""
            键=常驻作用域键(标识)#常驻作用域键（可弱引用对象）
            作用域=创建作用域(自身.selfCtx,键)#从未追踪上下文铸造
            try:#挂载组合
                戳=组合戳(预设['path'])#盖文件戳
                if 戳 is None:#文件不可 stat
                    raise 预设挂载错误(标识,'composition file is unreadable')#无法挂载，不夹路径
                挂载预设(作用域.上下文,预设)#挂载并审计
                return {'key':键,'scope':作用域,'stamp':戳}#本代
            except Exception as 错误:#挂载失败须丢掉指针并拆除，类型含预设挂载错误与加载器错误
                自身.standing.pop(标识,None)#丢掉失败指针
                作用域.拆除()#拆除半成品
                raise 错误#原错上抛
        已创建=创建()#同步创建（Python 文件 IO 同步）
        自身.standing[标识]=已创建#登记
        return 已创建#交给调用方

class 常驻作用域键:
    """一代常驻挂载的作用域键；按对象身份比较，可弱引用。"""
    def __init__(自身,预设标识):
        """记下本代所组合自的预设 id。"""
        自身.agentPreset=预设标识#预设 id

__all__=[#仅中文公开名
    '设置空间名','智能体预设设置模式','智能体预设名册',
    '组合文件','发现预设','扫描根','用户预设目录',
    '元数据文件','读预设元数据','渲染预设元数据',
    '未激活行','泄漏服务','活预设挂载','挂载预设','智能体服务','常驻挂载于',
    '复制组合','删除组合','非法预设标识错误','预设已存在错误','预设不可写错误','读组合','可写根',
    '解析会话预设','预设错误','预设挂载错误','未知预设错误',
]#公开面结束
default=智能体预设名册#Cordis 默认导出
