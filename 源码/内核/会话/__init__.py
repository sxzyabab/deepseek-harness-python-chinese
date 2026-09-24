import time,threading,weakref
from ...依赖 import cordis
from ...依赖.工具 import 获取内部数据
服务=cordis.服务
from ...模型后端.llm.调用配置 import 结构化克隆,冻结映射,可弱引用映射
from ...工具.值 import 断言永不
from ..作用域 import 获取作用域,作用域目标
from .类型 import (
    会话标识,会话格式版本,安全整数上限,待办状态,待办条目,会话头字段,会话头,
    创建会话选项,会话种子事件状态,恢复会话选项,准备会话选项,
    智能体取消原因,轮次结束取消原因,轮次结束原因映射,轮次结束原因,
    纪元请求头,请求上下文,请求头原因,
    核心会话事件类型,表面事件类型,表面操作,表面意图,会话事件信封字段,
)
from .json值 import 快照json值,是否json值,冻结树,冻结记录
from .表面 import (
    事件派生消息,
    表面视图,
    折叠表面,
    是否表面事件,
    是否追加表面事件,
    是否替换表面事件,
    是否可进表面类型,
    校验会话事件数据,
    校验表面元数据,
)
from .请求头 import 归一请求头,请求头是否相等,折叠请求头
from .块行 import 解码存储记录,打包块游程#历史读；追踪已删 chunk-rows
from .准备 import 会话准备
from .修复 import 打开轮次关闭器,中断轮次关闭器,工具未启动,工具结局未知
from .分叉 import 构建分叉种子
from .已知事件类型 import 已知会话事件类型,消息投影事件类型
from .序号范围 import 编码序号范围,解码序号范围

__all__=[
    '会话','会话存储','会话分叉错误','会话准备','会话标识','会话格式版本','会话头字段','会话头',
    '创建会话选项','会话种子事件状态','恢复会话选项','准备会话选项',
    '智能体取消原因','轮次结束取消原因','轮次结束原因映射','轮次结束原因',
    '待办状态','待办条目','纪元请求头','请求上下文','请求头原因',
    '核心会话事件类型','表面事件类型','表面操作','表面意图','会话事件信封字段',
    '安全整数上限','快照json值','是否json值','冻结树','冻结记录',
    '事件派生消息','表面视图','折叠表面','是否表面事件','是否追加表面事件','是否替换表面事件','是否可进表面类型',
    '校验会话事件数据','校验表面元数据',
    '归一请求头','请求头是否相等','折叠请求头','解码存储记录','打包块游程',
    '打开轮次关闭器','中断轮次关闭器','工具未启动','工具结局未知','构建分叉种子','已知会话事件类型','消息投影事件类型',
    '编码序号范围','解码序号范围',
    '收养会话事件','快照会话事件','快照会话头','校验会话头','校验恢复会话头',
]

允许适配器键=frozenset(('reasoningEffort','maxTokens'))
附着表=weakref.WeakKeyDictionary()
允许恢复头类型=(dict,冻结映射,冻结记录,可弱引用映射)

class 会话错误(Exception):
    """内核会话包的异常基类。"""

def 外来安全整数(值):
    """外来 JSON 序号与时间是否落在安全整数范围。"""
    if isinstance(值,bool):
        return False#布尔不是整数
    if isinstance(值,int):
        return abs(值)<=安全整数上限
    if isinstance(值,float) and 值.is_integer():
        return abs(值)<=安全整数上限
    return False

def 是否绝对路径(路径):
    """对齐 Node path.isAbsolute 的 POSIX 与 Windows 形态。"""
    if not isinstance(路径,str) or 路径=='':
        return False
    首=路径[0]
    if 首=='/' or 首=='\\':
        return True
    if len(路径)>2 and (('A'<=首<='Z') or ('a'<=首<='z')) and 路径[1]==':' and (路径[2]=='/' or 路径[2]=='\\'):
        return True
    return False

def 当前毫秒():
    """Unix 纪元毫秒。"""
    return int(time.time()*1000)

def 是否普通记录(值):
    """值是否为普通 JSON 记录，不是数组。"""
    return isinstance(值,dict)

def 收集会话回调(上下文,参数):
    """解析一份监听器快照，含 Cordis 内部派发检查。"""
    副本=list(参数)
    事件总线=获取内部数据(上下文,'属性链')['事件']
    return list(获取内部数据(事件总线,'解析监听器')(事件总线,'emit',副本))

def 收住会话观察者(上下文,名称,标识,参数,回调列表):
    """调用一份已解析的只观察监听器快照，按监听器收住失败。"""
    for 回调 in 回调列表:
        try:
            回调(*参数)
        except Exception as 错误:
            上下文.日志.警告('session "'+str(标识)+'": '+名称+' 监听器抛错: '+str(错误))

def 是否有提供方模型(值):
    """未知值是否携带当前的提供方/模型对。"""
    if not 是否普通记录(值):
        return False
    提供方=值['provider'] if 'provider' in 值 else None
    模型=值['model'] if 'model' in 值 else None
    return isinstance(提供方,str) and len(提供方)>0 and isinstance(模型,str) and len(模型)>0

def 断言支持的请求头(类型,数据,位置):
    """拒绝随旧增量编码一起移除的请求头词汇。"""
    if 类型=='request/header-delta':
        raise 会话错误(位置+' 使用了已不支持的旧版 request/header-delta 格式')
    if 类型=='request/header' and 是否普通记录(数据) and 'reason' in 数据 and 数据['reason']=='fallback':
        raise 会话错误(位置+' 使用了已不支持的旧版 request/header 原因 "fallback"')

消息角色按类型={
    'system/message':'system',
    'developer/message':'developer',
    'user/message':'user',
    'assistant/message':'assistant',
    'tool/result':'tool',
}

def 是否消息事件类型(类型):
    """四种表面事件类型，其载荷携带已标识消息。"""
    return (类型=='developer/message' or 类型=='system/message' or 类型=='user/message'
        or 类型=='assistant/message' or 类型=='tool/result')

def 断言消息事件形(事件,主题):
    """只校验安全回放一条消息所需的事件特有不变量。"""
    类型=事件['type'] if 'type' in 事件 else None
    if not 是否消息事件类型(类型):
        return
    数据=事件['data'] if 'data' in 事件 else None
    表=数据 if 是否普通记录(数据) else None
    if 类型=='user/message':
        消息=表
    else:
        消息=表['message'] if 表 is not None and 'message' in 表 else None
    消息标识值=消息['id'] if 是否普通记录(消息) and 'id' in 消息 else None
    if (not 是否普通记录(消息)) or (not isinstance(消息标识值,str)) or 消息标识值=='':
        raise 会话错误(主题+' 缺少已标识的消息')
    期望角色=消息角色按类型[类型]
    if 消息['role']!=期望角色:
        raise 会话错误(主题+' 消息角色必须是 "'+期望角色+'"')
    来源=消息['source'] if 'source' in 消息 else None
    来源种=来源['kind'] if 是否普通记录(来源) and 'kind' in 来源 else None
    if (not 是否普通记录(来源)) or (not isinstance(来源种,str)) or 来源种=='':
        raise 会话错误(主题+' 消息来源非法')
    if not isinstance(消息['content'] if 'content' in 消息 else None,list):
        raise 会话错误(主题+' 消息内容非法')
    if 类型=='system/message':
        if 来源种!='system-prompt':
            raise 会话错误(主题+' 消息必须有 system-prompt 来源')
        return
    if 类型=='assistant/message':
        if 来源种!='model' or not 是否有提供方模型(来源):
            raise 会话错误(主题+' 消息必须有模型来源')
        return
    if 类型!='tool/result':
        return
    调用号=来源['callId'] if 来源 is not None and 'callId' in 来源 else None
    if 来源种!='tool' or (not isinstance(调用号,str)) or 调用号=='':
        raise 会话错误(主题+' 消息必须有工具来源')
    if 消息['toolCallId']!=调用号:
        raise 会话错误(主题+' 消息的工具调用 id 不一致')

def 断言适配器默认(值,配置,下标,已给出):#校验适配器默认
    """校验从耐久请求头导入的适配器默认标记。"""
    if not 已给出:#未给则跳过
        return#未给则跳过
    if 值 is None or (not 是否普通记录(值)):#必须是普通对象
        raise 会话错误('种子 request/header 下标 '+str(下标)+' 的 adapterDefaults 非法')#非法标记表
    for 键 in 值.keys():#未知键
        if 键 not in 允许适配器键:#未知键
            raise 会话错误('种子 request/header 下标 '+str(下标)+' 的 adapterDefaults 非法')#未知键
    for 标记 in 值.values():#标记必须是 true
        if 标记 is not True:#标记必须是 true
            raise 会话错误('种子 request/header 下标 '+str(下标)+' 的 adapterDefaults 非法')#标记必须是 true
    if ('reasoningEffort' in 值 and 值['reasoningEffort'] is True) and (配置 is None or 'reasoningEffort' not in 配置):#力度标记却无配置
        raise 会话错误('种子 request/header 下标 '+str(下标)+' 的 adapterDefaults 非法')#力度标记却无配置
    if ('maxTokens' in 值 and 值['maxTokens'] is True) and (配置 is None or 'maxTokens' not in 配置):#token 标记却无配置
        raise 会话错误('种子 request/header 下标 '+str(下标)+' 的 adapterDefaults 非法')#token 标记却无配置

def 断言助手落定形(数据,类型,下标):#断言助手落定形状
    """校验恢复会话生命周期逻辑直接使用的字段，不回放嵌入流。"""
    轮次=数据['turn'] if 数据 is not None and 'turn' in 数据 else None#轮次
    步骤=数据['step'] if 数据 is not None and 'step' in 数据 else None#步骤
    流=数据['stream'] if 数据 is not None and 'stream' in 数据 else None#流
    if ((not 外来安全整数(轮次)) or 轮次<0
        or (not 外来安全整数(步骤)) or 步骤<0
        or (not isinstance(流,list))):#字段非法
        raise 会话错误('种子 '+类型+' 下标 '+str(下标)+' 的落定字段非法')#拒绝

def 断言当前llm形(事件,下标):#校验当前 LLM 形
    """在种子/加载边界拒绝过时请求头与畸形消息。"""
    数据=事件['data'] if 'data' in 事件 else None#载荷
    表=数据 if 是否普通记录(数据) else None#对象载荷
    if 'type' in 事件 and 事件['type']=='request/header':#请求头快照
        头=表['header'] if 表 is not None and 'header' in 表 else None#头对象
        头表=头 if 是否普通记录(头) else None#普通对象
        配置=头表['config'] if 头表 is not None and 'config' in 头表 else None#模型配置
        if not 是否有提供方模型(配置):#缺提供方/模型
            raise 会话错误('种子 request/header 下标 '+str(下标)+' 缺少 provider/model')#缺提供方/模型
        if 配置 is not None and 'reasoningEffort' in 配置:#给了力度
            推理力度=配置['reasoningEffort']#推理力度
            if not isinstance(推理力度,str) or len(推理力度)==0:#必须是非空字符串
                raise 会话错误('种子 request/header 下标 '+str(下标)+' 的 reasoningEffort 非法')#非法力度
        已给出默认=头表 is not None and 'adapterDefaults' in 头表#是否给出适配器默认
        断言适配器默认(头表['adapterDefaults'] if 头表 is not None and 'adapterDefaults' in 头表 else None,配置,下标,已给出默认)#适配器默认标记
        原因=表['reason'] if 表 is not None and 'reason' in 表 else None#原因
        if 原因!='initial' and 原因!='resume' and 原因!='change' and 原因!='series':#非法原因
            raise 会话错误('种子 request/header 下标 '+str(下标)+' 的 reason 非法')#拒绝
        if 表 is not None and 'startsSeries' in 表 and 表['startsSeries'] is not True:#系列标记
            raise 会话错误('种子 request/header 下标 '+str(下标)+' 的 startsSeries 标记非法')#拒绝
    类型=事件['type'] if 'type' in 事件 else None#事件类型
    if 类型=='assistant/attempt':#助手尝试
        断言助手落定形(表,类型,下标)#落定字段
        return
    if not 是否消息事件类型(类型):#非消息类型跳过
        return#跳过
    断言消息事件形(事件,'种子 '+str(类型)+' 下标 '+str(下标))#校验消息形
    if 类型=='assistant/message':#助手消息
        断言助手落定形(表,类型,下标)#落定字段

def 断言会话事件信封(值,下标):#断言信封
    """在一次 JSON 物化之后校验固定事件信封。"""
    if not 是否普通记录(值):#非普通对象
        raise 会话错误('种子事件下标 '+str(下标)+' 的事件信封非法')#非法信封
    if 'type' in 值 and 值['type']=='request/header-delta':#已移除的增量编码
        raise 会话错误('种子事件下标 '+str(下标)+' 使用了已不支持的旧版 request/header-delta 格式')#旧格式
    for 键 in list(值.keys()):#信封键必须认识
        if 键 not in 会话事件信封字段:#未知键
            raise 会话错误('种子事件下标 '+str(下标)+' 的事件信封非法')#非法信封
    类型=值['type'] if 'type' in 值 else None#事件类型
    序号=值['seq'] if 'seq' in 值 else None#序号
    时间=值['time'] if 'time' in 值 else None#时间
    if (not isinstance(类型,str)
        or (not 外来安全整数(序号)) or 序号<0
        or (not 外来安全整数(时间))
        or ('data' not in 值)
        or ('ignorable' in 值 and 值['ignorable'] is not True)):#非法信封
        raise 会话错误('种子事件下标 '+str(下标)+' 的事件信封非法')#非法信封
    校验会话事件数据(值,'种子 '+str(类型)+' 下标 '+str(下标))#校验载荷
    if (类型=='request/header' or 类型=='developer/message' or 类型=='system/message' or 类型=='user/message'
        or 类型=='assistant/attempt' or 类型=='assistant/message' or 类型=='tool/result'):#需 LLM 形状
        断言当前llm形(值,下标)#当前 LLM 形

def 校验会话头(标识,输入):#校验创建头
    """就地校验并冻结一份脱离的创建头。"""
    if 输入 is None or (not 是否普通记录(输入)):#必须是普通对象
        raise 会话错误('会话头不是普通 JSON 记录')#不是普通 JSON 记录
    if ('version' not in 输入) or 输入['version']!=会话格式版本:#版本必须匹配
        raise 会话错误('会话头 version 必须是 '+str(会话格式版本)+'，实际为 '+str(输入['version'] if 'version' in 输入 else None))#版本不对
    if ('id' not in 输入) or 输入['id']!=标识:#头 id 必须贴合会话 id
        raise 会话错误('会话头 id "'+str(输入['id'] if 'id' in 输入 else None)+'" 与会话 id "'+str(标识)+'" 不一致')#id 不匹配
    创建于=输入['createdAt'] if 'createdAt' in 输入 else None#创建时间
    if (not 外来安全整数(创建于)) or 创建于<0:#必须是非负安全整数
        raise 会话错误('会话头 createdAt 必须是非负安全整数')#非法 createdAt
    if 'cwd' in 输入:#给了工作目录
        工作目录=输入['cwd']#工作目录
        if not isinstance(工作目录,str):#必须是字符串
            raise 会话错误('会话头 cwd 必须是字符串')#必须是字符串
        if not 是否绝对路径(工作目录):#必须是绝对路径
            raise 会话错误('会话头 cwd 必须是绝对路径，实际为 "'+str(工作目录)+'"')#相对路径非法
    if 'parentSession' in 输入 and not isinstance(输入['parentSession'],str):#给了父会话
        raise 会话错误('会话头 parentSession 必须是字符串')#必须是字符串
    if 'seedLength' in 输入:#废弃字段
        raise 会话错误('会话头含非法字段 "seedLength"')#拒绝
    if 'isSeeded' not in 输入 or not isinstance(输入['isSeeded'],bool):#种子标记类型
        raise 会话错误('会话头 isSeeded 必须是布尔')#拒绝
    if 'origin' in 输入 and 输入['origin']!='subagent':#给了来源
        raise 会话错误('会话头 origin 必须是 "subagent"')#只允许 subagent
    if 'delegationDepth' in 输入:#给了委托深度
        深度=输入['delegationDepth']#委托深度
        if (not 外来安全整数(深度)) or 深度<0:#必须是非负安全整数
            raise 会话错误('会话头 delegationDepth 必须是非负安全整数')#非法 delegationDepth
    if 'agentPreset' in 输入 and not isinstance(输入['agentPreset'],str):#给了预设
        raise 会话错误('会话头 agentPreset 必须是字符串')#必须是字符串
    return 冻结树(输入)#冻结后返回

def 校验恢复会话头(标识,输入):#校验恢复头
    """就地校验并冻结一份独占所有的持久化头。"""
    if 输入 is not None and 是否普通记录(输入):#看起来像对象
        if type(输入) not in 允许恢复头类型:#必须是普通对象或字典
            raise 会话错误('会话头不是普通 JSON 记录')#带自定义原型则拒
    return 校验会话头(标识,输入)#再走字段校验

def 快照会话头(标识,来源=None):#快照创建头
    """脱离、校验并冻结会话发表的创建元数据。"""
    if 来源 is None:#未供给则合成最小头
        输入={'version':会话格式版本,'id':标识,'createdAt':当前毫秒(),'isSeeded':False}#当前格式版本与时间戳
    else:#借用调用方头
        输入=来源#借用调用方头
    快照=快照json值(输入)#无损 JSON 脱离
    if 快照 is None:#不能无损序列化
        raise 会话错误('会话头无法无损 JSON 序列化')#不能无损序列化
    return 校验会话头(标识,快照)#校验并冻结

def 收养会话事件(事件):#就地收养事件
    """校验一份独占所有的事件，并深冻结其已识别消息，不复制该事件。"""
    校验会话事件数据(事件,'会话事件 seq '+str(事件['seq']))#校验载荷
    校验表面元数据(事件)#校验表面元数据
    断言消息事件形(事件,'会话事件 seq '+str(事件['seq']))#校验消息形
    类型=事件['type']#事件类型
    if 类型=='user/message':#用户消息
        冻结树(事件['data'])#整份 data 就是消息
    elif 类型=='developer/message' or 类型=='system/message' or 类型=='assistant/message' or 类型=='tool/result':
        冻结树(事件['data']['message'])#冻结内嵌消息
    return 事件#同一对象

def 快照会话事件(事件):#快照事件
    """脱离一份事件，同时为其已识别消息保住深不可变。"""
    return 收养会话事件(结构化克隆(事件))#先克隆再收养

class 会话:#事件源会话
    """一份事件源会话：会话事件的只追加日志。

    普通类（不是 Service）——经 `ctx.sessions.创建()` 铸造在线实例，经 `创建` 铸造脱离实例。
    用已有事件日志播种会回放/分叉一份会话。公开方法仅中文名；`id`/`events`/`seq`/`header`/`surface`/`firstLiveSeq`/`inheritedEventCount`
    为与耐久头与跨包读取对齐的实例字段名（载荷键字面量），不是英文方法别名。
    """
    def __init__(自身,标识,种子=None,头=None,模式='snapshot',供给继承事件数=None,投影列表=None):#铸造会话
        """铸造一份脱离会话；`snapshot` 脱离校验种子，`detached`/`shared-frozen` 采纳持久化移交值。投影列表为插件拥有的纯解释器。"""
        if 投影列表 is None:#缺省无投影
            投影列表=[]#空表
        自身.日志=[]#只追加日志
        自身.表面视图=表面视图(自身.日志,0,投影列表)#表面视图
        自身._事件快照=None#缓存的 events 快照
        自身._头折叠=None#已折叠头
        自身._头折叠序号=0#已折叠到的 seq
        自身._上下文折叠=None#已折叠路由元数据
        自身._上下文折叠序号=0#已折叠到的 seq
        自身._派生=[]#已投影消息
        自身._派生节点=0#已投影节点数
        自身._派生代数=0#内容代数
        if 模式=='snapshot':#快照模式稍后合成头
            恢复头=None#快照模式稍后合成
        else:#恢复模式就地校验头
            恢复头=校验恢复会话头(标识,头)#独占头
        if 种子 is not None:#有种子
            下标=0#种子下标
            for 源 in 种子:#逐条种子
                if 模式=='snapshot':#快照脱离
                    快照=快照json值(源)#脱离拷贝
                else:#恢复接管原件
                    快照=源#恢复接管原件
                if 快照 is None:#不能无损序列化
                    raise 会话错误('种子事件下标 '+str(下标)+' 无法无损 JSON 序列化')#非法种子
                断言会话事件信封(快照,下标)#信封
                断言支持的请求头(快照['type'],快照['data'],'种子事件下标 '+str(下标))#拒绝旧请求头
                if 快照['seq']!=下标:#必须从 0 连续
                    raise 会话错误('种子事件下标 '+str(下标)+' 的 seq 为 '+str(快照['seq'])+'（期望 '+str(下标)+'）；种子必须从 0 连续')#序号不连续
                try:#校验下一条表面转移
                    自身.表面视图.校验下一条(快照)#规划候选
                except Exception as 错误:#表面拒绝
                    消息=str(错误)#诊断
                    if isinstance(错误,Exception) and len(错误.args)>0:#有参数
                        消息=str(错误.args[0])#错误文案
                    raise 会话错误('种子事件下标 '+str(下标)+' 非法: '+消息)#包一层种子下标
                if 模式=='snapshot':#快照深冻结
                    自身.日志.append(冻结树(快照))#收下冻结事件
                else:#恢复不二次冻结
                    自身.日志.append(快照)#采纳已有图
                下标+=1#下一条
        自身.firstLiveSeq=len(自身.日志)#本进程第一条在线 seq（构造种子长度；更小 seq 从未经 session/event 发表）
        if 恢复头 is not None:#恢复头
            自身.header=恢复头#恢复头
        else:#快照头
            自身.header=快照会话头(标识,头)#快照头
        if 自身.header['isSeeded'] and 种子 is None:#带种子却无种子
            raise 会话错误('已播种会话必须显式提供构造种子')#拒绝
        if 自身.header['isSeeded'] and 供给继承事件数 is None:#缺继承条数
            raise 会话错误('已播种会话必须提供继承事件条数')#拒绝
        继承事件数=0 if 供给继承事件数 is None else 供给继承事件数#继承条数
        if (not 外来安全整数(继承事件数)) or 继承事件数<0:#非法
            raise 会话错误('会话继承事件条数必须是非负安全整数')#拒绝
        继承事件数=int(继承事件数)#归一为 int
        if (not 自身.header['isSeeded']) and 继承事件数!=0:#未种子却有继承
            raise 会话错误('未播种会话的继承事件条数必须为 0')#拒绝
        if 继承事件数>len(自身.日志):#继承超出日志
            raise 会话错误('会话继承事件条数超出其事件日志')#拒绝
        种子标记=自身.日志[继承事件数] if 继承事件数<len(自身.日志) else None
        已标种子=(种子标记 is not None and 种子标记['type']=='session/end-seed'
            and 是否普通记录(种子标记['data']) and 种子标记['data'].get('inherited') is True)
        if 模式=='snapshot' and 自身.header['isSeeded'] and 继承事件数!=len(自身.日志) and not 已标种子:
            raise 会话错误('已播种会话的构造种子必须等于其继承前缀或标出继承切断')
        if 已标种子:
            for 事件 in 自身.日志[继承事件数+1:]:
                if 事件['type']=='session/end-seed' and 是否普通记录(事件['data']) and 事件['data'].get('inherited') is True:
                    raise 会话错误('会话继承事件条数必须指向最后一条继承标记')
        自身.inheritedEventCount=继承事件数#保存继承条数
        自身.firstLifecycleSeq=继承事件数 if 模式=='snapshot' and 自身.header['isSeeded'] else 自身.firstLiveSeq
        if 种子 is not None and 模式=='snapshot' and 自身.header['isSeeded'] and not 已标种子:
            自身.追加('session/end-seed',{'inherited':True})#带继承标记
        elif 种子 is not None and not (模式=='snapshot' and 自身.header['isSeeded']):
            末=自身.日志[-1] if len(自身.日志)>0 else None#最后一条
            if 末 is None or ('type' not in 末) or 末['type']!='session/end-seed':#尚未以 end-seed 结尾
                自身.追加('session/end-seed',{})#普通种子结束

    @staticmethod#快照铸造
    def 创建(标识,种子=None,头=None,继承事件数=None,投影列表=None):#快照铸造
        """通过校验并快照借用的种子事件与存储元数据，铸造一份脱离会话。"""
        return 会话(标识,种子,头,'snapshot',继承事件数,投影列表)#默认 snapshot 模式

    @staticmethod#恢复铸造
    def 从恢复(标识,种子,头,继承事件数,事件状态,投影列表=None):#恢复铸造
        """通过采纳独立拥有或已深冻结的种子，恢复一份脱离会话。"""
        return 会话(标识,种子,头,事件状态,继承事件数,投影列表)#事件状态即构造模式

    @property#有序表面
    def surface(自身):#有序表面
        """本会话事件日志上的有序表面（表面视图实现）。"""
        return 自身.表面视图#表面视图即表面

    @property#会话 id
    def id(自身):#会话 id
        """会话身份，来自其耐久头的那一份拷贝。"""
        return 自身.header['id']#头上的那一份

    @property#不可变日志快照
    def events(自身):#不可变日志快照
        """只追加事件日志的不可变快照；复用到下一次追加。"""
        if 自身._事件快照 is None:#没有缓存
            自身._事件快照=tuple(自身.日志)#没有缓存则浅拷贝并冻结数组
        return 自身._事件快照#复用到下一次追加

    def snapshotEvents(自身,起点=0,终点排他=None):#区间事件快照
        """返回 `[起点, 终点排他)` 的冻结前缀。"""
        if 终点排他 is None:#默认到下一序号
            终点排他=自身.seq#日志长度
        if 起点==0 and 终点排他==len(自身.日志):#全快照
            return 自身.events#复用公开快照
        return tuple(自身.日志[起点:终点排他])#区间切片

    @property#下一序号
    def seq(自身):#下一序号
        """下一条事件的序号（始终等于日志长度）。"""
        return len(自身.日志)#连续性约定

    def ownEvents(自身):#自有事件后缀
        """从精确继承切口起的本包自有事件；日程等消费方用它代替读 header 种子长度。"""
        return 自身.snapshotEvents(自身.inheritedEventCount)#从继承切口起

    def 追加(自身,类型,数据,表面意图=None):#追加一条事件
        """向日志追加一条带类型的事件，并经存储拥有的发表钩子同步通知观察者。

        热路径从不阻塞 I/O。事件一旦进入日志即已提交：观察者失败按监听器收住，
        不改变返回值，也不阻止更后监听器观察同一条已接受事件。
        """
        表面元数据={}#要快照的表面字段
        if 表面意图 is not None and 'sourceEventSeqs' in 表面意图:#给了来源序号
            表面元数据['sourceEventSeqs']=表面意图['sourceEventSeqs']#来源序号
        if 表面意图 is not None and 'surfaceOp' in 表面意图:#给了表面操作
            表面元数据['surfaceOp']=表面意图['surfaceOp']#表面操作
        数据快照=快照json值(数据)#脱离载荷
        if 数据快照 is None:#不能无损序列化
            raise 会话错误('会话事件 "'+str(类型)+'" 携带了无法 JSON 序列化的 data')#非法 data
        断言支持的请求头(类型,数据快照,'会话事件 "'+str(类型)+'"')#拒绝旧请求头
        表面元数据快照=快照json值(表面元数据)#脱离表面元数据
        if 表面元数据快照 is None:#不能无损序列化
            raise 会话错误('会话事件 "'+str(类型)+'" 携带了无法 JSON 序列化的表面元数据')#非法表面元数据
        条目=附着表.get(自身)#在线附着，脱离会话为 None
        if 条目 is not None and 条目['appending']:#发表边界仍开着
            raise 会话错误('另一条追加正在发表时，会话追加不得重入')#禁止重入
        事件={#铸造不可变事件
            'type':类型,#类型
            'seq':len(自身.日志),#连续性约定
            'time':当前毫秒(),#接受时间
            'data':数据快照,#已脱离载荷
        }#铸造事件
        if 'surfaceOp' in 表面元数据快照:#可选表面操作
            事件['surfaceOp']=表面元数据快照['surfaceOp']#可选表面操作
        if 'sourceEventSeqs' in 表面元数据快照:#可选来源序号
            事件['sourceEventSeqs']=表面元数据快照['sourceEventSeqs']#可选来源序号
        事件=冻结树(事件)#不可变事件
        校验会话事件数据(事件,'会话事件 "'+str(类型)+'" seq '+str(事件['seq']))#校验载荷
        自身.表面视图.校验下一条(事件)#规划表面转移
        if 条目 is not None:#在线才打开发表边界
            条目['appending']=True#打开发表边界
        try:#提交并通知
            回调列表=None#监听器快照
            回调参数=[自身,事件]#会话与事件
            if 条目 is not None:#在线才解析监听器
                回调列表=收集会话回调(条目['emitCtx'],[条目['carrier'],'session/event']+回调参数)#push 前快照
            自身.日志.append(事件)#提交进日志
            自身._事件快照=None#作废公开快照
            if 回调列表 is not None and 条目 is not None:#有观察者
                收住会话观察者(条目['emitCtx'],'session/event',条目['id'],回调参数,回调列表)#提交后通知
            return 事件#已记下的事件
        finally:#无论成败
            if 条目 is not None:#在线才关边界
                条目['appending']=False#关闭发表边界
                if 条目['detachRequested'] and (not 条目['announcing']):#有推迟脱离且不在宣布
                    条目['detach']()#有推迟脱离且不在宣布则执行

    def 请求头(自身):#当前请求头
        """日志最后一条头事件之后生效的纪元请求头（增量折叠）。"""
        if 自身._头折叠序号<len(自身.日志):#有尚未折叠的事件
            自身._头折叠=冻结树(折叠请求头(自身.日志[自身._头折叠序号:],自身._头折叠))#增量折叠并冻结
            自身._头折叠序号=len(自身.日志)#追上日志
        return 自身._头折叠#当前头或尚未有

    def 请求上下文(自身):#当前请求上下文
        """返回最新已解析的路由元数据（每条 request/context 后写覆盖）。"""
        if 自身._上下文折叠序号<len(自身.日志):#有尚未折叠的事件
            for 事件 in 自身.日志[自身._上下文折叠序号:]:#只看新事件
                if 事件['type']=='request/context':#后写覆盖
                    自身._上下文折叠=冻结树(dict(事件['data']))#后写覆盖
            自身._上下文折叠序号=len(自身.日志)#追上日志
        return 自身._上下文折叠#当前上下文或尚未有

    def 派生消息(自身):#派生 LLM 历史
        """通过行走 surfaceOp 标记维护的产消息事件有序序列，派生 LLM 消息历史。

        每个表面节点恰好投影一次；替换或消息投影改写内容代数后重建。返回新鲜浅拷贝，消息对象共享且深冻结。
        """
        表面=自身.surface#有序表面
        节点列表=表面.nodes#产消息序号
        代数=表面.contentGeneration#内容代数
        if 代数!=自身._派生代数:#表面被 replace 改写
            自身._派生=[]#丢掉旧投影
        自身._派生节点=0#从头投影
        自身._派生代数=代数#跟上代数
        for 序号 in 节点列表[自身._派生节点:]:#只投影新节点
            消息=自身.派生事件消息(自身.日志[序号])#按节点投影
            if 消息:#有消息才收下
                自身._派生.append(消息)#有消息才收下
        自身._派生节点=len(节点列表)#追上表面
        return list(自身._派生)#新鲜浅拷贝

    def 派生事件消息(自身,事件):#投影一条事件
        """把已提交消息投影应用到一条事件。原耐久事件不变。"""
        return 自身.表面视图.派生事件消息(事件)#委托表面视图

    def 是否自有序号(自身,序号):#是否自有序号
        """一个已有事件位置是否在分叉继承前缀之外。"""
        return 序号>=自身.inheritedEventCount and 序号<自身.seq#区间判定

class 会话分叉错误(Exception):#分叉错误
    """会话分叉拒绝的带类型错误（码：SESSION_NOT_FOUND / SESSION_NOT_LIVE / SESSION_ALREADY_EXISTS / INVALID_BOUNDARY / OPEN_TURN）。"""
    def __init__(自身,消息,码):#带拒绝码
        """带拒绝码。"""
        super().__init__(消息)#错误文案
        自身.message=消息#可读消息
        自身.code=码#拒绝码
        自身.name='SessionForkError'#固定名（错误类协议名）

class 会话存储(服务):#内存会话存储
    """内存会话存储（ctx.sessions）。有意不在这里实现持久化——插件订 session/event 并在 session/flush 时冲洗。"""
    def __init__(自身,ctx):#构造存储
        """构造存储并在有 Typert 时登记查找。"""
        super().__init__(ctx,'sessions')#注册为 sessions
        自身.存储={}#id 到条目
        自身.计数=0#铸造 session-<n> 的计数器
        自身.投影列表=[]#活借用的消息投影定义
        def 挂查找(类型上下文,*位置参数):#有 Typert 时按会话 id 解析会话
            """有 Typert 时按会话 id 解析会话。"""
            def 解析(会话号):#在线查找
                """在线查找。"""
                return 自身.获取(会话号)#按 id 查找
            类型上下文.typert.lookups.register('session',{#按会话 id 解析 Session
                'parameter':'session',#参数名
                'wire':'sessionId',#线上字段
                'hostTypeSymbol':'@deepseek-ai/dsh-session#Session',#宿主类型
                'wireTypeSymbol':'@deepseek-ai/dsh-session/types#SessionId',#线类型
                'resolve':解析,#在线查找
            })#结束 register
        自身.ctx.依赖启动(['typert'],挂查找)#有 Typert 时登记查找

    @property#消息投影
    def 消息投影列表(自身):#活借用定义
        """脱离回放用的借用定义；贡献存活到登记纤程卸载。"""
        return 自身.投影列表#同一张表

    def 登记消息投影(自身,投影):#登记一条解释器
        """为在线创建、恢复与分叉登记一条事件解释器。卸下后用过它的会话拒绝继续派生。"""
        for 项 in 自身.投影列表:#已有同类型
            if 项['type']==投影['type']:#类型已被占用
                raise 会话错误('session message projection "'+str(投影['type'])+'" is already registered')#拒绝
        def 执行体():#纤程拥有的贡献
            """挂上定义，卸载时按引用摘掉。"""
            自身.投影列表.append(投影)#挂上
            def 拆除():#按引用摘掉
                """卸下本条定义。"""
                下标=0#扫描
                while 下标<len(自身.投影列表):#按引用找
                    if 自身.投影列表[下标] is 投影:#命中
                        自身.投影列表.pop(下标)#摘掉
                        return
                    下标+=1#下一条
            yield 拆除#交给纤程
        return 自身.ctx.副作用(执行体,'sessions.registerMessageProjection()')#绑到调用纤程

    def 创建(自身,标识=None,选项=None):#便捷创建
        """铸造一份由调用纤程拥有的会话（准备 → 进入 → 宣布）。"""
        会话=自身.准备(标识,选项)#先构造
        def 执行体():#组合 effect
            """组合 effect：先进入再宣布。"""
            yield 自身.进入(会话)#先进入
            自身.宣布(会话)#再宣布
        自身.ctx.副作用(执行体,'sessions.create()')#绑到调用纤程
        return 会话#已在线

    def 准备(自身,标识=None,选项=None):#构造尚未进入的会话
        """构造一份会话但不把它进入存储。带 `eventState` 时走持久化移交恢复路径。"""
        if 标识 is None:#调用方未供给
            while True:#避开已占用
                自身.计数+=1#下一个序号
                会话号=会话标识('session-'+str(自身.计数))#铸造 session-<n>
                if 会话号 not in 自身.存储:#避开已占用
                    break#避开已占用
        else:#调用方供给
            会话号=会话标识(标识)#品牌化
        if 会话号 in 自身.存储:#不得覆盖在线条目
            raise 会话错误('会话 "'+str(会话号)+'" 已存在')#不得覆盖在线条目
        if 选项 is not None and 'eventState' in 选项:#持久化移交
            事件状态=选项['eventState']#别名状态
            if 事件状态=='detached' or 事件状态=='shared-frozen':#恢复路径
                return 会话.从恢复(#恢复
                    会话号,#id
                    选项['seed'],#种子
                    选项['meta'],#请求头
                    选项['inheritedEventCount'],#继承条数
                    事件状态,#状态
                    自身.投影列表,#活投影
                )#从恢复结束
            if 事件状态 is not None:#未知状态
                断言永不(事件状态,'会话存储.准备 的事件状态')#穷尽守卫
        种子=选项['seed'] if 选项 is not None and 'seed' in 选项 else None#可选种子
        元=选项['meta'] if 选项 is not None and 'meta' in 选项 else None#可选创建元数据
        继承事件数=选项['inheritedEventCount'] if 选项 is not None and 'inheritedEventCount' in 选项 else None#可选继承
        头={'version':会话格式版本,'id':会话号}#合成头
        if 元 is not None and 'createdAt' in 元:#供给创建时间
            头['createdAt']=元['createdAt']#供给
        else:#现在
            头['createdAt']=当前毫秒()#现在
        if 元 is not None and 'cwd' in 元:#可选工作目录
            头['cwd']=元['cwd']#可选工作目录
        if 元 is not None and 'parentSession' in 元:#可选父会话
            头['parentSession']=元['parentSession']#可选父会话
        if 元 is not None and 'isSeeded' in 元:#可选种子标记
            头['isSeeded']=元['isSeeded']#可选种子标记
        else:#缺省未播种
            头['isSeeded']=False#缺省
        if 元 is not None and 'origin' in 元:#可选来源
            头['origin']=元['origin']#可选来源
        if 元 is not None and 'delegationDepth' in 元:#可选委托深度
            头['delegationDepth']=元['delegationDepth']#可选委托深度
        if 元 is not None and 'agentPreset' in 元:#可选预设
            头['agentPreset']=元['agentPreset']#可选预设
        return 会话.创建(会话号,种子,头,继承事件数,自身.投影列表)#快照铸造

    def 进入(自身,会话):#进入存储
        """把一份已准备的会话进入存储；返回幂等脱离器。"""
        标识=会话.id#会话 id
        载体=作用域目标(会话,获取作用域(自身.ctx))#本存储作用域上的载体
        if 标识 in 自身.存储:#不得覆盖
            raise 会话错误('会话 "'+str(标识)+'" 已存在')#不得覆盖
        if 会话 in 附着表:#不得重复附着
            raise 会话错误('会话 "'+str(标识)+'" 已附着到存储')#不得重复附着
        条目={#新条目
            'id':标识,#会话 id
            'session':会话,#会话
            'carrier':载体,#载体
            'emitCtx':自身.ctx,#发出上下文
            'announced':False,#尚未宣布
            'announcing':False,#未在宣布
            'appending':False,#未在追加
            'detachRequested':False,#未请求脱离
        }#新条目
        def 执行脱离():#执行脱离
            """执行脱离。"""
            自身._脱离已进入(条目)#脱离已进入条目
        条目['detach']=执行脱离#执行脱离
        自身.存储[标识]=条目#写入存储
        附着表[会话]=条目#挂上追加钩子
        仍有效=[True]#脱离是否仍有效
        def 脱离():#幂等脱离
            """幂等脱离。"""
            if not 仍有效[0]:#已脱离
                return#已脱离
            仍有效[0]=False#标为失效
            if 条目['announcing'] or 条目['appending']:#正在宣布或追加
                条目['detachRequested']=True#推迟脱离
                return#等边界释放
            条目['detach']()#立即脱离
        return 脱离#返回脱离器

    def _脱离已进入(自身,条目):#脱离已进入条目
        """移除一个精确已进入会话，并在已宣布时发出其配对拆除。"""
        条目['detachRequested']=False#清掉推迟标记
        if 自身.存储.get(条目['id']) is not 条目:#不是当前条目
            return#不是当前条目
        自身.存储.pop(条目['id'],None)#从存储删掉
        附着表.pop(条目['session'],None)#摘掉追加钩子
        if 条目['announced']:#已宣布
            自身._发出拆除(条目)#已宣布才发配对拆除

    def 宣布(自身,会话):#宣布
        """对一份已进入的会话恰好发出一次 session/created。"""
        条目=自身._在线条目(会话)#必须是本存储在线条目
        if 条目['announced'] or 条目['announcing']:#已经或正在宣布
            raise 会话错误('会话 "'+str(条目['id'])+'" 已经宣布过')#不得重复宣布
        条目['announced']=True#已宣布（部分投递也算）
        回调参数=[会话]#回调实参
        条目['announcing']=True#正在宣布
        try:#派发创建
            回调列表=收集会话回调(自身.ctx,[条目['carrier'],'session/created',会话])#解析快照
            for 回调 in 回调列表:#逐个监听器
                回调(*回调参数)#监听器已是同步回调
        finally:#无论成败
            条目['announcing']=False#宣布结束
            if 条目['detachRequested'] and (not 条目['appending']):#有推迟脱离且不在追加
                条目['detach']()#有推迟脱离且不在追加则执行

    def _发出拆除(自身,条目):#发出 session/disposed
        """发出配对拆除通知，按监听器收住失败。"""
        回调参数=[条目['session']]#回调实参
        try:#派发拆除
            回调列表=收集会话回调(自身.ctx,[条目['carrier'],'session/disposed',条目['session']])#解析快照
            收住会话观察者(自身.ctx,'session/disposed',条目['id'],回调参数,回调列表)#收住地调用
        except Exception as 错误:#派发本身抛错
            自身.ctx.日志.警告('session "'+str(条目['id'])+'": session/disposed 派发抛错: '+str(错误))#记派发失败

    def 冲洗(自身,会话):#耐久检查点
        """为会话派发被等待的 session/flush 耐久检查点；全部落定后抛第一个失败。"""
        条目=自身._在线条目(会话)#必须在线
        载体=条目['carrier']#载体
        回调参数=[会话]#回调实参
        回调列表=收集会话回调(自身.ctx,[载体,'session/flush',会话])#解析快照
        失败列表=[None]*len(回调列表)#按下标收拒绝
        下标=0#回调下标
        for 回调 in 回调列表:#逐个监听器
            try:#把同步抛错收成拒绝
                回调(*回调参数)#监听器已是同步回调
            except Exception as 错误:#同步抛错
                失败列表[下标]=错误#保住精确拒绝值
            下标+=1#下一回调
        for 错误 in 失败列表:#按监听器顺序
            if 错误 is not None:#第一个失败
                raise 错误#全部落定后抛第一个失败
        return len(回调列表)>0#是否有人参与

    def _在线条目(自身,会话):#取在线条目
        """返回精确在线条目；脱离/已准备对象拒绝。"""
        if 会话 not in 附着表:#未附着
            raise 会话错误('会话 "'+str(会话.id)+'" 不在本存储中在线')#必须在线
        条目=附着表[会话]#附着
        if 自身.存储.get(条目['id']) is not 条目:#不是本存储当前条目
            raise 会话错误('会话 "'+str(会话.id)+'" 不在本存储中在线')#必须在线
        return 条目#精确条目

    def 获取(自身,标识):#按 id 查找
        """查找一份在线会话。"""
        if 标识 not in 自身.存储:#没有
            return None#没有
        条目=自身.存储[标识]#按 id
        return 条目['session']#在线会话

    def 列出(自身):#列在线会话
        """全部在线会话，按创建顺序。"""
        结果=[]#新鲜数组
        for 条目 in 自身.存储.values():#按插入序
            结果.append(条目['session'])#按插入序
        return 结果#不影响存储

    def 分叉(自身,源,边界=None,子会话号=None):#分叉
        """从一份在线源的稳定前缀铸造一份在线子会话（前缀不得结束在打开轮次内）。"""
        if 子会话号 is not None and 自身.获取(子会话号) is not None:#子 id 已被占用
            raise 会话分叉错误('会话 "'+str(子会话号)+'" 已存在','SESSION_ALREADY_EXISTS')#已存在
        在线源=自身._解析分叉源(源)#解析在线源
        事件列表=在线源.events#不可变快照
        边界=自身._分叉边界(在线源.id,事件列表,边界)#切稳定前缀
        种子=[] if 边界 is None else 构建分叉种子(事件列表,边界)
        元={'parentSession':在线源.id,'isSeeded':True}#子头
        if 'cwd' in 在线源.header:#继承工作目录
            元['cwd']=在线源.header['cwd']#有则带
        继承条数=0 if 边界 is None else 边界+1
        return 自身.创建(子会话号,{'seed':种子,'meta':元,'inheritedEventCount':继承条数})#便捷创建子会话

    def _分叉边界(自身,会话号,事件列表,请求边界):
        """解析含端边界；打开尾交给构建分叉种子关闭。"""
        最后=事件列表[-1] if len(事件列表)>0 else None
        if 请求边界 is not None:
            边界=请求边界
        else:
            if 最后 is None:
                return None
            边界=最后['seq']
        if (not 外来安全整数(边界)) or 边界<0:
            raise 会话分叉错误(
                '会话 "'+str(会话号)+'" 的分叉边界必须是非负安全整数，实际为 '+str(边界),
                'INVALID_BOUNDARY',
            )
        if 边界>=len(事件列表):
            最后序号=最后['seq'] if 最后 is not None else None
            最后文本='无' if 最后序号 is None else str(最后序号)
            raise 会话分叉错误(
                '分叉边界 '+str(边界)+' 在会话 "'+str(会话号)+'" 中不存在（最后 seq: '+最后文本+'）',
                'INVALID_BOUNDARY',
            )
        边界事件=事件列表[边界]
        if 边界事件 is None or 边界事件['seq']!=边界:
            raise 会话分叉错误(
                '分叉边界 '+str(边界)+' 与会话 "'+str(会话号)+'" 中的连续事件 seq 不匹配',
                'INVALID_BOUNDARY',
            )
        return 边界

    def _解析分叉源(自身,源):#解析分叉源
        """解析分叉源：会话 id 字符串或本存储在线会话实例。"""
        if isinstance(源,str):#按 id
            会话=自身.获取(源)#查找在线
            if 会话 is None:#未知
                raise 会话分叉错误('会话 "'+str(源)+'" 未找到','SESSION_NOT_FOUND')#未知
            return 会话#在线会话
        在线=自身.获取(源.id)#按对象 id 查找
        if 在线 is None:#存储里没有
            raise 会话分叉错误('会话 "'+str(源.id)+'" 未找到','SESSION_NOT_FOUND')#未知
        if 在线 is not 源:#必须是在线实例
            raise 会话分叉错误('会话 "'+str(源.id)+'" 不是本存储的在线实例','SESSION_NOT_LIVE')#必须是在线实例
        return 源#就是在线对象

# 会话头字段权威在 .类型，本模块再导出供持久化等消费方。
default=会话存储#Cordis 默认导出槽
