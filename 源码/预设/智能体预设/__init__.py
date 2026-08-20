"""智能体预设：每个会话从一份预设组合其面向模型的插件集。

对齐上游 `@deepseek-ai/dsh-agent-presets`。公开面仅中文名。服务键 `agentPresets`、配置键与诊断字面量保持上游。
"""
import os#文件戳
from cordis import 服务#Cordis 服务基类
from schemastery import 模式#配置模式
from scope import 绑定作用域父,创建作用域,获取作用域,弱身份表#作用域
from settings import 设置命名空间#设置命名空间
from home_paths import 主目录路径#harness 主目录路径
from .发现 import 组合文件,用户预设目录,发现预设,扫描根#发现
from .编写 import (#编写
    复制组合,删除组合,读组合,可写根,
    非法预设标识错误,预设已存在错误,预设不可写错误,
)#编写结束
from .挂载 import (#挂载
    挂载预设,智能体服务,常驻挂载于,活预设挂载,泄漏服务,未激活行,
)#挂载结束
from .元数据 import 元数据文件,读预设元数据,渲染预设元数据#元数据
from .会话 import 解析会话预设#会话预设
from .预设 import 预设挂载错误,未知预设错误#预设错误
from . import 类型 as _类型#触发客户端安全事件声明

__all__=[#仅中文公开名
    '设置空间名','智能体预设设置模式','智能体预设名册',
    '组合文件','发现预设','扫描根','用户预设目录',
    '元数据文件','读预设元数据','渲染预设元数据',
    '未激活行','泄漏服务','活预设挂载','挂载预设','智能体服务','常驻挂载于',
    '复制组合','删除组合','非法预设标识错误','预设已存在错误','预设不可写错误','读组合','可写根',
    '解析会话预设','预设挂载错误','未知预设错误',
]#公开面结束

设置空间名='agent-presets'#设置命名空间
智能体预设设置模式=模式.对象({#用户可写设置
    'default':模式.字符串(),#默认预设 id
})#设置模式结束

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段，缺席为缺席。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        return 对象.get(键,缺省)#映射
    return getattr(对象,键,缺省)#属性

def 组合戳(路径):#读文件戳
    """读一个组合文件的戳；无法 stat 时为 None。"""
    try:#stat
        信息=os.stat(路径)#取出
        return {'mtimeMs':信息.st_mtime*1000.0,'size':信息.st_size}#文件身份
    except OSError:#无法 stat
        return None#无戳

def 同戳(甲,乙):#比较文件戳
    """两个戳是否命名同一文件状态。"""
    return 甲['mtimeMs']==乙['mtimeMs'] and 甲['size']==乙['size']#时间与大小

class 智能体预设名册(服务):#智能体预设名册服务
    """部署的智能体预设上的注册表。发现不做记忆化。"""
    inject=['loader']#依赖加载器
    注入=inject#中文别名
    Config=模式.对象({#插件配置模式
        'default':模式.字符串().必填(),#必填默认预设 id
        'roots':模式.数组(模式.对象({#扫描根
            'path':模式.字符串().必填(),#根路径
            'trust':模式.联合(['system','user']).默认('user'),#默认用户信任
        })).默认([]),#默认无已配置根
        'includeUserRoot':模式.布尔().默认(True),#默认追加用户根
    })#配置模式结束

    def __init__(自身,ctx,配置=None):#构造名册服务
        """登记服务、派生扫描根、接线设置与咨询性监听。"""
        if 配置 is None:#缺省
            配置={}#空
        super().__init__(ctx,'agentPresets')#注册为 agentPresets
        自身.config=配置#配置
        自身.selfCtx=ctx#未追踪的本服务上下文
        自身.自身上下文=ctx#中文别名
        根们=list(取字段(配置,'roots') or [])#已配置根
        if 取字段(配置,'includeUserRoot') is not False:#追加用户根
            根们=根们+[{'path':主目录路径(用户预设目录),'trust':'user'}]#追加 harness 用户根
        自身.resolvedRoots=根们#解析后的扫描根
        自身.已解析根=根们#中文别名
        自身.settings=None#用户设置作用域
        自身.settingsService=None#设置服务
        自身.standing={}#按 id 的常驻挂载单飞表
        自身.bindings=弱身份表()#智能体键 → 父绑定
        def 设置接线(设置上下文,*其余):#有设置服务时注册用户切片
            """登记用户默认预设切片。"""
            自身.settings=设置上下文.settings.登记(#注册命名空间
                设置命名空间(设置空间名),#agent-presets
                智能体预设设置模式,#用户切片模式
                {'base':{'default':取字段(配置,'default')}},#组合层默认
            )#结束登记
            自身.settingsService=设置上下文.settings#保住写入面
            def 挂拆():#拆除时丢掉句柄
                """清掉设置句柄。"""
                def 拆除():#拆除器
                    """清掉。"""
                    自身.settings=None#清掉作用域
                    自身.settingsService=None#清掉服务
                return 拆除#拆除器
            设置上下文.effect(挂拆,'agentPresets.settings()')#effect 名
        ctx.inject(['settings'],设置接线)#有设置才接线
        def 智能体已创建(载荷,*其余):#智能体发布时咨询性检查
            """未加入预设的智能体警告一次。"""
            智能体=取字段(载荷,'agent')#智能体
            if len(自身.resolvedRoots)==0:#无名册
                return#不过问
            if 自身.已组合预设(取字段(智能体,'ctx')) is not None:#已加入
                return#过
            ctx.logger.warn(
                'agent "'+取字段(智能体,'id')+'" was published without joining an agent preset; '
                +'its tools, prompt sections, and skill catalog resolve against the empty global layer '
                +'(join through AgentPresets.mount() or composeFrom() in the agent factory setup)'
            )#警告
        ctx.on('agent/created',智能体已创建)#咨询性检查
        def 会话事件(会话,事件,*其余):#会话事件投影到公开通知
            """耐久记录提交后发出公开事件。"""
            if 取字段(事件,'type')!='agent-preset/selected':#只关心预设选定
                return#放过
            ctx.emit('agent-preset/selected',取字段(会话,'id'),取字段(取字段(事件,'data'),'agentPreset'))#公开事件
        ctx.on('session/event',会话事件)#投影

    @property#只读
    def defaultId(自身):#未点名时的预设 id
        """调用方未点名时挂载的预设 id。"""
        if 自身.settings is not None:#有用户层
            return 取字段(自身.settings.get(),'default') or 取字段(自身.config,'default')#用户覆盖
        return 取字段(自身.config,'default')#配置默认

    @property#只读
    def roots(自身):#实际扫描根
        """本名册扫描的根。"""
        return 自身.resolvedRoots#派生一次的根集

    @property#只读
    def authorable(自身):#是否可编写
        """本部署是否有本地编写预设去往的根。"""
        for 根 in 自身.resolvedRoots:#有用户根即可写
            if 取字段(根,'trust')=='user':#用户根
                return True#可写
        return False#不可写

    def list(自身):#列名册
        """已配置根当前提供的每个预设。"""
        return 发现预设(自身.resolvedRoots)#重扫根

    def resolve(自身,标识=None):#按 id 解析预设
        """按 id 解析一个预设。损坏的也能解析。"""
        想要=自身.defaultId if 标识 is None else 标识#缺省用默认
        预设们=自身.list()#当前名册
        for 预设 in 预设们:#按 id 查找
            if 取字段(预设,'id')==想要:#命中
                return 预设#已解析行
        raise 未知预设错误(想要,[取字段(项,'id') for 项 in 预设们])#未知预设

    def _解析可挂载(自身,标识=None):#解析可挂载预设
        """解析即将组合智能体的一个预设，用发现报告的原因拒绝损坏的。"""
        预设=自身.resolve(标识)#先解析行
        损坏=取字段(预设,'broken')#损坏原因
        if 损坏 is not None:#发现已报损坏
            raise 预设挂载错误(取字段(预设,'id'),损坏)#用发现原因拒绝
        return 预设#可挂载

    def mount(自身,智能体上下文,标识=None):#把智能体加入预设
        """从一个预设组合一个智能体。"""
        智能体键=获取作用域(智能体上下文)#智能体作用域键
        if 智能体键 is None:#无作用域无法加入
            raise Exception('agent-presets: refusing to compose an unscoped context; the scope key is what joins an agent to its preset')#拒绝
        预设=自身._解析可挂载(标识)#可挂载预设
        常驻=自身._确保常驻(预设)#确保常驻挂载
        自身.bindings.设(智能体键,绑定作用域父(智能体键,常驻['key']))#挂到常驻键下
        return 预设#供调用方记录

    def composeFrom(自身,智能体上下文,父上下文):#加入父的常驻组合
        """把一个智能体加入另一个已经在跑的同一份常驻组合。"""
        智能体键=获取作用域(智能体上下文)#子的作用域键
        if 智能体键 is None:#无作用域
            raise Exception('agent-presets: refusing to compose an unscoped context; the scope key is what joins an agent to its preset')#拒绝
        常驻=常驻挂载于(父上下文)#父已加入的常驻挂载
        if 常驻 is None:#父未加入
            return None#子也不加入
        绑定=绑定作用域父(智能体键,取字段(常驻,'key'))#挂到同一常驻键
        自身.bindings.设(智能体键,绑定)#记下
        return 取字段(常驻,'presetId')#加入的预设 id

    def composedPreset(自身,智能体上下文):#读智能体已加入的预设
        """一个活智能体所跑的预设。"""
        常驻=常驻挂载于(智能体上下文)#常驻挂载
        return None if 常驻 is None else 取字段(常驻,'presetId')#预设 id

    def 已组合预设(自身,智能体上下文):#中文别名
        """composedPreset 的中文名。"""
        return 自身.composedPreset(智能体上下文)#委托

    def read(自身,标识):#读组合文本
        """读一个预设的组合文本。"""
        return 读组合(自身.resolve(标识))#先解析再读

    def copy(自身,来源,标识,名称=None):#复制出新预设
        """通过整份复制已有预设来创建本地编写的预设。"""
        源=自身.resolve(来源)#解析源
        for 预设 in 自身.list():#名册已有该 id
            if 取字段(预设,'id')==标识:#占用
                raise 预设已存在错误(标识)#拒绝覆盖
        复制组合(自身.resolvedRoots,源,标识,名称)#整目录复制
        自身.standing.pop(标识,None)#丢掉过期常驻指针

    def remove(自身,标识):#删除本地预设
        """删除本地编写的预设。"""
        删除组合(自身.resolvedRoots,自身.resolve(标识))#解析后删除
        自身.standing.pop(标识,None)#丢掉常驻指针
        if 自身.settings is None:#无用户设置
            return#不用清
        if 取字段(自身.settings.get(),'default')!=标识:#用户默认不是这个
            return#不用清
        if 自身.settingsService is not None:#清掉用户默认
            自身.settingsService.改写(设置命名空间(设置空间名),[{'op':'unset','path':['default']}])#unset

    def serviceFor(自身,智能体,名):#按智能体取预设内服务
        """一个智能体对其预设所挂服务的实例。"""
        return 智能体服务(自身.ctx,智能体,名)#委托

    def recompose(自身,智能体上下文,标识):#再链接到另一预设
        """把一个智能体再链接到不同预设的常驻组合。"""
        智能体键=获取作用域(智能体上下文)#智能体作用域键
        if 智能体键 is None:#无作用域
            raise Exception('agent-presets: refusing to recompose an unscoped context')#拒绝
        预设=自身._解析可挂载(标识)#可挂载目标
        常驻=自身._确保常驻(预设)#确保新常驻挂载
        绑定=自身.bindings.取(智能体键)#已有父绑定
        if 绑定 is None:#从未组合过
            自身.bindings.设(智能体键,绑定作用域父(智能体键,常驻['key']))#初次挂上
        else:#已有绑定则再链接
            绑定.改接(常驻['key'])#改父到新常驻键
        return 预设#现在安装的预设

    def standingKeyFor(自身,标识=None):#冷读用的常驻作用域键
        """一个预设的常驻作用域键，供没有智能体的宿主读取方。"""
        预设=自身._解析可挂载(标识)#可挂载预设
        return 自身._确保常驻(预设)['key']#常驻键

    def _确保常驻(自身,预设):#确保常驻挂载
        """解析（或创建，单飞）一个预设的常驻挂载。"""
        标识=取字段(预设,'id')#预设 id
        进行中=自身.standing.get(标识)#进行中或已结算
        if 进行中 is not None:#已有指针
            已挂=进行中() if callable(进行中) else 进行中#等这一代（同步化）
            当前=组合戳(取字段(预设,'path'))#当前文件戳
            if 当前 is None or 同戳(已挂['stamp'],当前):#戳相同或不可读
                return 已挂#沿用
            if 自身.standing.get(标识) is 进行中:#仍是同一指针
                自身.standing.pop(标识,None)#丢掉
            return 自身._确保常驻(预设)#启动下一代
        def 创建():#单飞创建本代
            """创建本代常驻挂载。"""
            键=常驻作用域键(标识)#常驻作用域键（可弱引用对象）
            作用域=创建作用域(自身.selfCtx,键)#从未追踪上下文铸造
            try:#挂载组合
                戳=组合戳(取字段(预设,'path'))#盖文件戳
                if 戳 is None:#文件不可 stat
                    raise 预设挂载错误(标识,'composition file is unreadable: '+取字段(预设,'path'))#无法挂载
                挂载预设(作用域.上下文,预设)#挂载并审计
                return {'key':键,'scope':作用域,'stamp':戳}#本代
            except Exception as 错误:#挂载失败
                自身.standing.pop(标识,None)#丢掉失败指针
                作用域.拆除()#拆除半成品
                raise 错误#原错上抛
        已创建=创建()#同步创建（Python 文件 IO 同步）
        自身.standing[标识]=已创建#登记
        return 已创建#交给调用方

class 常驻作用域键:#常驻挂载作用域键
    """一代常驻挂载的作用域键；按对象身份比较，可弱引用。"""
    def __init__(自身,预设标识):#记下预设 id
        """记下本代所组合自的预设 id。"""
        自身.agentPreset=预设标识#预设 id

默认=智能体预设名册#中文默认导出
default=智能体预设名册#Cordis 默认导出
