"""事件源会话服务：只追加的会话日志、内存存储，以及派生出的 LLM 消息历史。

对齐上游 `session/src/index.ts`。公开面仅中文名；Cordis 默认导出槽可保留。
"""
import time,threading,weakref#时间、线程与弱表
from cordis.服务 import 服务#导入服务基类
from cordis.工具 import 是否thenable#导入 thenable 判定
from llm.调用配置 import 结构化克隆,冻结映射,可弱引用映射#导入拆离与冻结类型
from scope import 获取作用域,作用域目标#导入作用域键与载体
from .类型 import (#导入格式版本、会话 id、头字段、事件与待办词表
    会话标识,会话格式版本,是否安全整数,待办状态,待办条目,会话头字段,会话头,
    创建会话选项,恢复会话选项,准备会话选项,
    智能体取消原因,轮次结束取消原因,轮次结束原因映射,轮次结束原因,
    纪元请求头,请求上下文,请求头原因,
    核心会话事件类型,表面事件类型,表面操作,表面意图,会话事件信封字段,
)#类型导出
from .json值 import 快照json值,是否json值,冻结树,冻结记录#导入 JSON 校验与冻结
from .表面 import (
    事件派生消息,#每节点投影
    表面管理器,#增量表面
    折叠表面,#完整折叠
    是否表面事件,#表面判定
    是否追加表面事件,#追加判定
    是否替换表面事件,#替换判定
    是否可进表面类型,#资格判定
)#表面导出
from .请求头 import 归一请求头,请求头是否相等,折叠请求头#导入请求头
from .块行 import 解码存储记录,打包块游程#导入块行编解码
from .准备 import 会话准备#导入准备句柄
from .修复 import 中断轮次关闭器,工具未启动,工具结局未知#导入修复常量
from .已知事件类型 import 已知会话事件类型#导入已知事件类型

__all__=[#仅中文公开名（再导出子模块权威符号）
    '会话','会话存储','会话分叉错误','会话准备','会话标识','会话格式版本','会话头字段','会话头',
    '创建会话选项','恢复会话选项','准备会话选项',
    '智能体取消原因','轮次结束取消原因','轮次结束原因映射','轮次结束原因',
    '待办状态','待办条目','纪元请求头','请求上下文','请求头原因',
    '核心会话事件类型','表面事件类型','表面操作','表面意图','会话事件信封字段',
    '是否安全整数','快照json值','是否json值','冻结树','冻结记录',
    '事件派生消息','表面管理器','折叠表面','是否表面事件','是否追加表面事件','是否替换表面事件','是否可进表面类型',
    '归一请求头','请求头是否相等','折叠请求头','解码存储记录','打包块游程',
    '中断轮次关闭器','工具未启动','工具结局未知','已知会话事件类型',
    '收养会话事件','快照会话事件','快照会话头','校验会话头','校验恢复会话头',
    '默认',
]#公开面结束

允许适配器键=frozenset(('reasoningEffort','maxTokens'))#适配器默认允许的键
附着表=weakref.WeakKeyDictionary()#会话到存储条目
允许恢复头类型=(dict,冻结映射,冻结记录,可弱引用映射)#恢复头允许的普通记录类型

def 取字段(对象,键):#读取字段
    """读取映射或对象上的字段。"""
    if isinstance(对象,dict):#映射
        return 对象[键]#映射键
    return getattr(对象,键)#对象属性

def 试取(对象,键):#读取可选字段
    """读取可选字段，缺席为 None。"""
    if 对象 is None:#无对象
        return None#缺席
    if isinstance(对象,dict):#映射
        return 对象.get(键)#映射键
    return getattr(对象,键,None)#对象属性

def 有自有(对象,键):#是否拥有自有键
    """对象是否拥有该自有键。"""
    if isinstance(对象,dict):#字典
        return 键 in 对象#字典键
    字典=getattr(对象,'__dict__',None)#实例字典
    if 字典 is None:#没有字典
        return False#没有字典
    return 键 in 字典#自有

def 是否绝对路径(路径):#绝对路径判定
    """对齐 Node path.isAbsolute 的 POSIX 与 Windows 形态。"""
    if not isinstance(路径,str) or 路径=='':#空则否
        return False#空则否
    首=路径[0]#首字符
    if 首=='/' or 首=='\\':#根或 UNC
        return True#根或 UNC
    if len(路径)>2 and (('A'<=首<='Z') or ('a'<=首<='z')) and 路径[1]==':' and (路径[2]=='/' or 路径[2]=='\\'):#盘符绝对路径
        return True#盘符绝对路径
    return False#相对路径

def 当前毫秒():#Unix 纪元毫秒
    """Unix 纪元毫秒。"""
    return int(time.time()*1000)#接受时间

def 是否普通记录(值):#是否普通 JSON 记录
    """值是否为普通 JSON 记录，不是数组。"""
    return isinstance(值,dict)#字典或冻结记录

def 收集会话回调(上下文对象,参数):#收集监听器
    """解析一份监听器快照，含 Cordis 内部派发检查。"""
    副本=list(参数)#派发会就地改写
    return list(上下文对象.events.dispatch('emit',副本))#快照成数组

def 收住会话观察者(上下文对象,名称,标识,参数,回调们):#收住地调用观察者
    """调用一份已解析的只观察监听器快照，按监听器收住失败。"""
    for 回调 in 回调们:#逐个监听器
        try:#收住同步抛错
            返回=回调(*参数)#调用
            if 是否thenable(返回):#返回可等待
                def 盯住(任务=返回):#收住 Promise 拒绝
                    """收住 Promise 拒绝。"""
                    try:#收住拒绝
                        任务.等待()#等待
                    except Exception as 错误:#拒绝
                        上下文对象.logger.warn('session "'+str(标识)+'": '+名称+' listener rejected: '+str(错误))#记拒绝
                threading.Thread(target=盯住).start()#提交后不阻塞
        except Exception as 错误:#同步抛错
            上下文对象.logger.warn('session "'+str(标识)+'": '+名称+' listener threw: '+str(错误))#记抛错

def 是否有提供方模型(值):#是否有提供方/模型
    """未知值是否携带当前的提供方/模型对。"""
    if not 是否普通记录(值):#非对象则无
        return False#非对象则无
    提供方=试取(值,'provider')#提供方
    模型=试取(值,'model')#模型
    return isinstance(提供方,str) and len(提供方)>0 and isinstance(模型,str) and len(模型)>0#非空对

def 断言支持的请求头(类型,数据,位置):#拒绝旧请求头
    """拒绝随旧增量编码一起移除的请求头词汇。"""
    if 类型=='request/header-delta':#已移除的增量类型
        raise Exception(位置+' uses unsupported legacy request/header-delta format')#旧格式
    if 类型=='request/header' and 是否普通记录(数据) and 试取(数据,'reason')=='fallback':#已移除的 fallback 原因
        raise Exception(位置+' uses unsupported legacy request/header reason "fallback"')#旧原因

def 断言消息事件形(事件,主题):#校验消息形
    """只校验安全回放一条消息所需的事件特有不变量。"""
    类型=试取(事件,'type')#事件类型
    if 类型!='user/message' and 类型!='assistant/message' and 类型!='tool/result':#不是消息类型
        return#跳过
    数据=试取(事件,'data')#载荷
    表=数据 if 是否普通记录(数据) else None#对象载荷
    if 类型=='user/message':#用户消息
        消息=表#用户消息就是 data
    else:#其余
        消息=试取(表,'message') if 表 is not None else None#其余在 data.message
    消息标识值=试取(消息,'id') if 是否普通记录(消息) else None#消息 id
    if (not 是否普通记录(消息)) or (not isinstance(消息标识值,str)) or 消息标识值=='':#缺已识别消息
        raise Exception(主题+' lacks an identified message')#缺已识别消息
    if 类型=='assistant/message':#助手
        期望角色='assistant'#助手
    else:#用户
        期望角色='user'#用户
    if 试取(消息,'role')!=期望角色:#角色必须贴合类型
        raise Exception(主题+' message must have role "'+期望角色+'"')#角色不对
    来源=试取(消息,'source')#来源
    来源种=试取(来源,'kind') if 是否普通记录(来源) else None#kind
    if (not 是否普通记录(来源)) or (not isinstance(来源种,str)) or 来源种=='':#非法来源
        raise Exception(主题+' message has invalid source')#非法来源
    if not isinstance(试取(消息,'content'),list):#内容必须是数组
        raise Exception(主题+' message has invalid content')#非法内容
    if 类型=='assistant/message':#助手消息
        if 来源种!='model' or not 是否有提供方模型(来源):#必须是带提供方/模型的模型来源
            raise Exception(主题+' message must have model source')#必须是模型来源
        return#助手到此
    if 类型!='tool/result':#用户消息
        return#用户消息到此
    调用号=试取(来源,'callId')#callId
    if 来源种!='tool' or (not isinstance(调用号,str)) or 调用号=='':#必须是工具来源
        raise Exception(主题+' message must have tool source')#必须是工具来源
    内容=试取(消息,'content')#内容块
    块=内容[0] if len(内容)>0 else None#唯一块
    if (len(内容)!=1 or (not 是否普通记录(块))
        or 试取(块,'type')!='tool-result'
        or (not isinstance(试取(块,'content'),list))):#必须是单块工具结果
        raise Exception(主题+' message must contain one tool-result block')#必须是单块工具结果
    if 试取(块,'toolCallId')!=调用号:#块 id 必须贴合来源
        raise Exception(主题+' message has mismatched tool call ids')#工具调用 id 不一致

def 断言适配器默认(值,配置,下标,已给出):#校验适配器默认
    """校验从耐久请求头导入的适配器默认标记。"""
    if not 已给出:#未给则跳过
        return#未给则跳过
    if 值 is None or (not 是否普通记录(值)):#必须是普通对象
        raise Exception('seed request/header at index '+str(下标)+' has invalid adapterDefaults')#非法标记表
    for 键 in 值.keys():#未知键
        if 键 not in 允许适配器键:#未知键
            raise Exception('seed request/header at index '+str(下标)+' has invalid adapterDefaults')#未知键
    for 标记 in 值.values():#标记必须是 true
        if 标记 is not True:#标记必须是 true
            raise Exception('seed request/header at index '+str(下标)+' has invalid adapterDefaults')#标记必须是 true
    if 试取(值,'reasoningEffort') is True and not 有自有(配置,'reasoningEffort'):#力度标记却无配置
        raise Exception('seed request/header at index '+str(下标)+' has invalid adapterDefaults')#力度标记却无配置
    if 试取(值,'maxTokens') is True and not 有自有(配置,'maxTokens'):#token 标记却无配置
        raise Exception('seed request/header at index '+str(下标)+' has invalid adapterDefaults')#token 标记却无配置

def 断言当前llm形(事件,下标):#校验当前 LLM 形
    """在种子/加载边界拒绝过时请求头与畸形消息。"""
    数据=试取(事件,'data')#载荷
    表=数据 if 是否普通记录(数据) else None#对象载荷
    if 试取(事件,'type')=='request/header':#请求头快照
        头=试取(表,'header') if 表 is not None else None#头对象
        头表=头 if 是否普通记录(头) else None#普通对象
        配置=试取(头表,'config') if 头表 is not None else None#模型配置
        if not 是否有提供方模型(配置):#缺提供方/模型
            raise Exception('seed request/header at index '+str(下标)+' lacks provider/model')#缺提供方/模型
        if 有自有(配置,'reasoningEffort'):#给了力度
            推理力度=试取(配置,'reasoningEffort')#推理力度
            if not isinstance(推理力度,str) or len(推理力度)==0:#必须是非空字符串
                raise Exception('seed request/header at index '+str(下标)+' has an invalid reasoningEffort')#非法力度
        已给出默认=头表 is not None and 有自有(头表,'adapterDefaults')#是否给出适配器默认
        断言适配器默认(试取(头表,'adapterDefaults') if 头表 is not None else None,配置,下标,已给出默认)#适配器默认标记
    类型=试取(事件,'type')#事件类型
    if 类型!='user/message' and 类型!='assistant/message' and 类型!='tool/result':#不是消息类型
        return#工具结果也不走消息形之外
    断言消息事件形(事件,'seed '+str(类型)+' at index '+str(下标))#校验消息形

def 断言会话事件信封(值,下标):#断言信封
    """在一次 JSON 物化之后校验固定事件信封。"""
    if 试取(值,'type')=='request/header-delta':#已移除的增量编码
        raise Exception('seed event at index '+str(下标)+' uses unsupported legacy request/header-delta format')#旧格式
    for 键 in list(值.keys()):#信封键必须认识
        if 键 not in 会话事件信封字段:#未知键
            raise Exception('seed event at index '+str(下标)+' has an invalid event envelope')#非法信封
    类型=试取(值,'type')#事件类型
    序号=试取(值,'seq')#序号
    时间=试取(值,'time')#时间
    if (not isinstance(类型,str)
        or (not 是否安全整数(序号)) or 序号<0
        or (not 是否安全整数(时间))
        or (not 有自有(值,'data'))
        or (有自有(值,'ignorable') and 试取(值,'ignorable') is not True)):#非法信封
        raise Exception('seed event at index '+str(下标)+' has an invalid event envelope')#非法信封
    if 类型=='request/header' or 类型=='user/message' or 类型=='assistant/message' or 类型=='tool/result':#核心 LLM 类型
        断言当前llm形(值,下标)#当前 LLM 形

def 校验会话头(标识,输入):#校验创建头
    """就地校验并冻结一份脱离的创建头。"""
    if 输入 is None or (not 是否普通记录(输入)):#必须是普通对象
        raise Exception('session header is not a plain JSON record')#不是普通 JSON 记录
    if 试取(输入,'version')!=会话格式版本:#版本必须匹配
        raise Exception('session header version must be '+str(会话格式版本)+', got '+str(试取(输入,'version')))#版本不对
    if 试取(输入,'id')!=标识:#头 id 必须贴合会话 id
        raise Exception('session header id "'+str(试取(输入,'id'))+'" does not match session id "'+str(标识)+'"')#id 不匹配
    创建于=试取(输入,'createdAt')#创建时间
    if (not 是否安全整数(创建于)) or 创建于<0:#必须是非负安全整数
        raise Exception('session header createdAt must be a non-negative safe integer')#非法 createdAt
    if 有自有(输入,'cwd'):#给了工作目录
        工作目录=试取(输入,'cwd')#工作目录
        if not isinstance(工作目录,str):#必须是字符串
            raise Exception('session header cwd must be a string')#必须是字符串
        if not 是否绝对路径(工作目录):#必须是绝对路径
            raise Exception('session header cwd must be an absolute path, got "'+str(工作目录)+'"')#相对路径非法
    if 有自有(输入,'parentSession') and not isinstance(试取(输入,'parentSession'),str):#给了父会话
        raise Exception('session header parentSession must be a string')#必须是字符串
    if 有自有(输入,'seedLength'):#给了种子长度
        种子长=试取(输入,'seedLength')#种子长度
        if (not 是否安全整数(种子长)) or 种子长<0:#必须是非负安全整数
            raise Exception('session header seedLength must be a non-negative safe integer')#非法 seedLength
    if 有自有(输入,'origin') and 试取(输入,'origin')!='subagent':#给了来源
        raise Exception('session header origin must be "subagent"')#只允许 subagent
    if 有自有(输入,'delegationDepth'):#给了委托深度
        深度=试取(输入,'delegationDepth')#委托深度
        if (not 是否安全整数(深度)) or 深度<0:#必须是非负安全整数
            raise Exception('session header delegationDepth must be a non-negative safe integer')#非法 delegationDepth
    if 有自有(输入,'agentPreset') and not isinstance(试取(输入,'agentPreset'),str):#给了预设
        raise Exception('session header agentPreset must be a string')#必须是字符串
    return 冻结树(输入)#冻结后返回

def 校验恢复会话头(标识,输入):#校验恢复头
    """就地校验并冻结一份独占所有的持久化头。"""
    if 输入 is not None and 是否普通记录(输入):#看起来像对象
        if type(输入) not in 允许恢复头类型:#必须是普通对象或字典
            raise Exception('session header is not a plain JSON record')#带自定义原型则拒
    return 校验会话头(标识,输入)#再走字段校验

def 快照会话头(标识,来源=None):#快照创建头
    """脱离、校验并冻结会话发表的创建元数据。"""
    if 来源 is None:#未供给则合成最小头
        输入={'version':会话格式版本,'id':标识,'createdAt':当前毫秒()}#当前格式版本与时间戳
    else:#借用调用方头
        输入=来源#借用调用方头
    快照=快照json值(输入)#无损 JSON 脱离
    if 快照 is None:#不能无损序列化
        raise Exception('session header is not losslessly JSON-serializable')#不能无损序列化
    return 校验会话头(标识,快照)#校验并冻结

def 收养会话事件(事件):#就地收养事件
    """校验一份独占所有的事件，并深冻结其已识别消息，不复制该事件。"""
    断言消息事件形(事件,'session event at seq '+str(取字段(事件,'seq')))#校验消息形
    类型=取字段(事件,'type')#事件类型
    if 类型=='user/message':#用户消息
        冻结树(取字段(事件,'data'))#整份 data 就是消息
    elif 类型=='assistant/message' or 类型=='tool/result':#助手/工具
        冻结树(取字段(取字段(事件,'data'),'message'))#冻结内嵌消息
    return 事件#同一对象

def 快照会话事件(事件):#快照事件
    """脱离一份事件，同时为其已识别消息保住深不可变。"""
    return 收养会话事件(结构化克隆(事件))#先克隆再收养

class 会话:#事件源会话
    """一份事件源会话：会话事件的只追加日志。

    普通类（不是 Service）——经 `ctx.sessions.创建()` 铸造在线实例，经 `创建` 铸造脱离实例。
    用已有事件日志播种会回放/分叉一份会话。公开方法仅中文名；`id`/`events`/`seq`/`header`/`surface`/`firstLiveSeq`
    为与耐久头与跨包读取对齐的实例字段名（载荷键字面量），不是英文方法别名。
    """
    def __init__(自身,标识,种子=None,头=None,模式='snapshot'):#铸造会话
        """铸造一份脱离会话；`snapshot` 脱离校验种子，`restore` 接管新鲜持久化值。"""
        自身.日志=[]#只追加日志
        自身.表面管理器=表面管理器(自身.日志)#表面管理器
        自身._事件快照=None#缓存的 events 快照
        自身._头折叠=None#已折叠头
        自身._头折叠序号=0#已折叠到的 seq
        自身._上下文折叠=None#已折叠路由元数据
        自身._上下文折叠序号=0#已折叠到的 seq
        自身._派生=[]#已投影消息
        自身._派生节点=0#已投影节点数
        自身._派生代数=0#替换代数
        if 模式=='restore':#恢复模式才就地校验头
            恢复头=校验恢复会话头(标识,头)#独占头
        else:#快照模式稍后合成
            恢复头=None#快照模式稍后合成
        if 种子 is not None:#有种子
            下标=0#种子下标
            for 源 in 种子:#逐条种子
                if 模式=='restore':#恢复接管原件
                    快照=源#恢复接管原件
                else:#否则快照
                    快照=快照json值(源)#否则快照
                if 快照 is None:#不能无损序列化
                    raise Exception('seed event at index '+str(下标)+' is not losslessly JSON-serializable')#非法种子
                断言会话事件信封(快照,下标)#信封
                断言支持的请求头(取字段(快照,'type'),取字段(快照,'data'),'seed event at index '+str(下标))#拒绝旧请求头
                if 取字段(快照,'seq')!=下标:#必须从 0 连续
                    raise Exception('seed event at index '+str(下标)+' has seq '+str(取字段(快照,'seq'))+' (expected '+str(下标)+'); seed must be contiguous from 0')#序号不连续
                try:#校验下一条表面转移
                    自身.表面管理器.校验下一条(快照)#规划候选
                except Exception as 错误:#表面拒绝
                    消息=str(错误)#诊断
                    if isinstance(错误,Exception) and len(错误.args)>0:#有参数
                        消息=str(错误.args[0])#错误文案
                    raise Exception('invalid seed event at index '+str(下标)+': '+消息)#包一层种子下标
                自身.日志.append(冻结树(快照))#收下冻结事件
                下标+=1#下一条
        自身.firstLiveSeq=len(自身.日志)#本进程第一条在线 seq（构造种子长度；更小 seq 从未经 session/event 发表）
        if 恢复头 is not None:#恢复头
            自身.header=恢复头#恢复头
        else:#快照头
            自身.header=快照会话头(标识,头)#快照头
        if 种子 is not None:#有种子
            末=自身.日志[-1] if len(自身.日志)>0 else None#最后一条
            if 末 is None or 试取(末,'type')!='session/end-seed':#种子尚未以 end-seed 结尾
                自身.追加('session/end-seed',{})#写下进程内种子边界

    @staticmethod#快照铸造
    def 创建(标识,种子=None,头=None):#快照铸造
        """通过校验并快照借用的种子事件与存储元数据，铸造一份脱离会话。"""
        return 会话(标识,种子,头,'snapshot')#默认 snapshot 模式

    @staticmethod#恢复铸造
    def 从恢复(标识,种子,头):#恢复铸造
        """通过接管新鲜持久化值，恢复一份脱离会话（就地校验后冻结）。"""
        return 会话(标识,种子,头,'restore')#restore 模式

    @property#有序表面
    def surface(自身):#有序表面
        """本会话事件日志上的有序表面（表面管理器实现）。"""
        return 自身.表面管理器#管理器即表面

    @property#会话 id
    def id(自身):#会话 id
        """会话身份，来自其耐久头的那一份拷贝。"""
        return 取字段(自身.header,'id')#头上的那一份

    @property#不可变日志快照
    def events(自身):#不可变日志快照
        """只追加事件日志的不可变快照；复用到下一次追加。"""
        if 自身._事件快照 is None:#没有缓存
            自身._事件快照=tuple(自身.日志)#没有缓存则浅拷贝并冻结数组
        return 自身._事件快照#复用到下一次追加

    @property#下一序号
    def seq(自身):#下一序号
        """下一条事件的序号（始终等于日志长度）。"""
        return len(自身.日志)#连续性约定

    def 追加(自身,类型,数据,表面意图=None):#追加一条事件
        """向日志追加一条带类型的事件，并经存储拥有的发表钩子同步通知观察者。

        热路径从不阻塞 I/O。事件一旦进入日志即已提交：观察者失败按监听器收住，
        不改变返回值，也不阻止更后监听器观察同一条已接受事件。
        """
        表面元数据={}#要快照的表面字段
        if 表面意图 is not None and 有自有(表面意图,'sourceEventSeqs'):#给了来源序号
            表面元数据['sourceEventSeqs']=取字段(表面意图,'sourceEventSeqs')#来源序号
        if 表面意图 is not None and 有自有(表面意图,'surfaceOp'):#给了表面操作
            表面元数据['surfaceOp']=取字段(表面意图,'surfaceOp')#表面操作
        数据快照=快照json值(数据)#脱离载荷
        if 数据快照 is None:#不能无损序列化
            raise Exception('session event "'+str(类型)+'" carries non-JSON-serializable data')#非法 data
        断言支持的请求头(类型,数据快照,'session event "'+str(类型)+'"')#拒绝旧请求头
        表面元数据快照=快照json值(表面元数据)#脱离表面元数据
        if 表面元数据快照 is None:#不能无损序列化
            raise Exception('session event "'+str(类型)+'" carries non-JSON-serializable surface metadata')#非法表面元数据
        条目=附着表.get(自身)#在线附着，脱离会话为 None
        if 条目 is not None and 条目['appending']:#发表边界仍开着
            raise Exception('session append cannot reenter while another append is being published')#禁止重入
        事件={#铸造不可变事件
            'type':类型,#类型
            'seq':len(自身.日志),#连续性约定
            'time':当前毫秒(),#接受时间
            'data':数据快照,#已脱离载荷
        }#铸造事件
        if 有自有(表面元数据快照,'surfaceOp'):#可选表面操作
            事件['surfaceOp']=表面元数据快照['surfaceOp']#可选表面操作
        if 有自有(表面元数据快照,'sourceEventSeqs'):#可选来源序号
            事件['sourceEventSeqs']=表面元数据快照['sourceEventSeqs']#可选来源序号
        事件=冻结树(事件)#不可变事件
        自身.表面管理器.校验下一条(事件)#规划表面转移
        if 条目 is not None:#在线才打开发表边界
            条目['appending']=True#打开发表边界
        try:#提交并通知
            回调们=None#监听器快照
            回调参数=[自身,事件]#会话与事件
            if 条目 is not None:#在线才解析监听器
                回调们=收集会话回调(条目['emitCtx'],[条目['carrier'],'session/event']+回调参数)#push 前快照
            自身.日志.append(事件)#提交进日志
            自身._事件快照=None#作废公开快照
            if 回调们 is not None and 条目 is not None:#有观察者
                收住会话观察者(条目['emitCtx'],'session/event',条目['id'],回调参数,回调们)#提交后通知
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
                if 取字段(事件,'type')=='request/context':#后写覆盖
                    自身._上下文折叠=冻结树(dict(取字段(事件,'data')))#后写覆盖
            自身._上下文折叠序号=len(自身.日志)#追上日志
        return 自身._上下文折叠#当前上下文或尚未有

    def 派生消息(自身):#派生 LLM 历史
        """通过行走 surfaceOp 标记维护的产消息事件有序序列，派生 LLM 消息历史。

        每个表面节点恰好投影一次；`replace` 改写代数后重建。返回新鲜浅拷贝，消息对象共享且深冻结。
        """
        表面=自身.surface#有序表面
        节点们=表面.nodes#产消息序号
        代数=表面.replaceGeneration#替换代数
        if 代数!=自身._派生代数:#表面被 replace 改写
            自身._派生=[]#丢掉旧投影
            自身._派生节点=0#从头投影
            自身._派生代数=代数#跟上代数
        for 序号 in 节点们[自身._派生节点:]:#只投影新节点
            消息=自身.派生事件消息(自身.日志[序号])#按节点投影
            if 消息:#有消息才收下
                自身._派生.append(消息)#有消息才收下
        自身._派生节点=len(节点们)#追上表面
        return list(自身._派生)#新鲜浅拷贝

    def 派生事件消息(自身,事件):#投影一条事件
        """surface 里纯每节点派生导出的实例面。"""
        return 事件派生消息(事件)#委托纯函数

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
        自身.ctx.inject(['typert'],挂查找)#有 Typert 时登记查找

    def 创建(自身,标识=None,选项=None):#便捷创建
        """铸造一份由调用光纤拥有的会话（准备 → 进入 → 宣布）。"""
        会话对象=自身.准备(标识,选项)#先构造
        def 执行体():#组合 effect
            """组合 effect：先进入再宣布。"""
            yield 自身.进入(会话对象)#先进入
            自身.宣布(会话对象)#再宣布
        自身.ctx.effect(执行体,'sessions.create()')#绑到调用光纤
        return 会话对象#已在线

    def 准备(自身,标识=None,选项=None):#构造尚未进入的会话
        """构造一份会话但不把它进入存储；持久化移交走 seedSource=persistence。"""
        if 标识 is None:#调用方未供给
            while True:#避开已占用
                自身.计数+=1#下一个序号
                会话号=会话标识('session-'+str(自身.计数))#铸造 session-<n>
                if 会话号 not in 自身.存储:#避开已占用
                    break#避开已占用
        else:#调用方供给
            会话号=会话标识(标识)#品牌化
        if 会话号 in 自身.存储:#不得覆盖在线条目
            raise Exception('session "'+str(会话号)+'" already exists')#不得覆盖在线条目
        种子来源=试取(选项,'seedSource') if 选项 is not None else None#种子来源
        if 种子来源=='persistence':#持久化移交
            return 会话.从恢复(会话号,取字段(选项,'seed'),取字段(选项,'meta'))#就地恢复
        种子=试取(选项,'seed') if 选项 is not None else None#可选种子
        元=试取(选项,'meta') if 选项 is not None else None#可选创建元数据
        头={'version':会话格式版本,'id':会话号}#合成头
        if 元 is not None and 有自有(元,'createdAt'):#供给创建时间
            头['createdAt']=取字段(元,'createdAt')#供给
        else:#现在
            头['createdAt']=当前毫秒()#现在
        if 元 is not None and 有自有(元,'cwd'):#可选工作目录
            头['cwd']=取字段(元,'cwd')#可选工作目录
        if 元 is not None and 有自有(元,'parentSession'):#可选父会话
            头['parentSession']=取字段(元,'parentSession')#可选父会话
        if 元 is not None and 有自有(元,'seedLength'):#可选种子边界
            头['seedLength']=取字段(元,'seedLength')#可选种子边界
        if 元 is not None and 有自有(元,'origin'):#可选来源
            头['origin']=取字段(元,'origin')#可选来源
        if 元 is not None and 有自有(元,'delegationDepth'):#可选委托深度
            头['delegationDepth']=取字段(元,'delegationDepth')#可选委托深度
        if 元 is not None and 有自有(元,'agentPreset'):#可选预设
            头['agentPreset']=取字段(元,'agentPreset')#可选预设
        return 会话.创建(会话号,种子,头)#快照铸造

    def 进入(自身,会话对象):#进入存储
        """把一份已准备的会话进入存储；返回幂等脱离器。"""
        标识=会话对象.id#会话 id
        载体=作用域目标(会话对象,获取作用域(自身.ctx))#本存储作用域上的载体
        if 标识 in 自身.存储:#不得覆盖
            raise Exception('session "'+str(标识)+'" already exists')#不得覆盖
        if 会话对象 in 附着表:#不得重复附着
            raise Exception('session "'+str(标识)+'" is already attached to a store')#不得重复附着
        条目={#新条目
            'id':标识,#会话 id
            'session':会话对象,#会话对象
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
        附着表[会话对象]=条目#挂上追加钩子
        仍有效=[True]#脱离是否仍有效
        def 脱离():#幂等脱离
            """幂等脱离。"""
            if not 仍有效[0]:#已脱离
                return#已脱离
            仍有效[0]=False#标为失效
            if 条目['announcing'] or 条目['appending']:#正在宣布或追加
                条目['detachRequested']=True#推迟脱离
                return#等边界解开
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

    def 宣布(自身,会话对象):#宣布
        """对一份已进入的会话恰好发出一次 session/created。"""
        条目=自身._在线条目(会话对象)#必须是本存储在线条目
        if 条目['announced'] or 条目['announcing']:#已经或正在宣布
            raise Exception('session "'+str(条目['id'])+'" was already announced')#不得重复宣布
        条目['announced']=True#已宣布（部分投递也算）
        回调参数=[会话对象]#回调实参
        条目['announcing']=True#正在宣布
        try:#派发创建
            回调们=收集会话回调(自身.ctx,[条目['carrier'],'session/created',会话对象])#解析快照
            for 回调 in 回调们:#逐个监听器
                返回=回调(*回调参数)#调用
                if 是否thenable(返回):#返回可等待
                    def 盯住(任务=返回,标识=条目['id']):#收住拒绝
                        """收住拒绝。"""
                        try:#收住拒绝
                            任务.等待()#等待
                        except Exception as 错误:#拒绝
                            自身.ctx.logger.warn('session "'+str(标识)+'": session/created listener rejected: '+str(错误))#记拒绝
                    threading.Thread(target=盯住).start()#拒绝太晚无法回滚
        finally:#无论成败
            条目['announcing']=False#宣布结束
            if 条目['detachRequested'] and (not 条目['appending']):#有推迟脱离且不在追加
                条目['detach']()#有推迟脱离且不在追加则执行

    def _发出拆除(自身,条目):#发出 session/disposed
        """发出配对拆除通知，按监听器收住失败。"""
        回调参数=[条目['session']]#回调实参
        try:#派发拆除
            回调们=收集会话回调(自身.ctx,[条目['carrier'],'session/disposed',条目['session']])#解析快照
            收住会话观察者(自身.ctx,'session/disposed',条目['id'],回调参数,回调们)#收住地调用
        except Exception as 错误:#派发本身抛错
            自身.ctx.logger.warn('session "'+str(条目['id'])+'": session/disposed dispatch threw: '+str(错误))#记派发失败

    def 冲洗(自身,会话对象):#耐久检查点
        """为会话派发被等待的 session/flush 耐久检查点；全部落定后抛第一个失败。"""
        条目=自身._在线条目(会话对象)#必须在线
        载体=条目['carrier']#载体
        回调参数=[会话对象]#回调实参
        回调们=收集会话回调(自身.ctx,[载体,'session/flush',会话对象])#解析快照
        失败们=[None]*len(回调们)#按下标收拒绝
        待等待=[]#异步结果与下标
        下标=0#回调下标
        for 回调 in 回调们:#逐个监听器
            try:#把同步抛错收成拒绝
                返回=回调(*回调参数)#调用
                if 是否thenable(返回):#返回可等待
                    待等待.append((下标,返回))#稍后等待
            except Exception as 错误:#同步抛错
                失败们[下标]=错误#保住精确拒绝值
            下标+=1#下一回调
        for 对 in 待等待:#等待全部
            等待下标,任务=对#拆开
            try:#收住拒绝
                任务.等待()#等待
            except Exception as 错误:#拒绝
                if 失败们[等待下标] is None:#尚无同步失败
                    失败们[等待下标]=错误#记下拒绝
        for 错误 in 失败们:#按监听器顺序
            if 错误 is not None:#第一个失败
                raise 错误#全部落定后抛第一个失败
        return len(回调们)>0#是否有人参与

    def _在线条目(自身,会话对象):#取在线条目
        """返回精确在线条目；脱离/已准备对象拒绝。"""
        条目=附着表.get(会话对象)#附着
        if 条目 is None or 自身.存储.get(条目['id']) is not 条目:#未附着或不是本存储当前条目
            raise Exception('session "'+str(会话对象.id)+'" is not live in this store')#必须在线
        return 条目#精确条目

    def 获取(自身,标识):#按 id 查找
        """查找一份在线会话。"""
        条目=自身.存储.get(标识)#按 id
        if 条目 is None:#没有
            return None#没有
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
            raise 会话分叉错误('session "'+str(子会话号)+'" already exists','SESSION_ALREADY_EXISTS')#已存在
        在线源=自身._解析分叉源(源)#解析在线源
        种子=自身._分叉种子(在线源,边界)#切稳定前缀
        元={'parentSession':在线源.id,'seedLength':len(种子)}#子头
        if 有自有(在线源.header,'cwd'):#继承工作目录
            元['cwd']=取字段(在线源.header,'cwd')#有则带
        return 自身.创建(子会话号,{'seed':种子,'meta':元})#便捷创建子会话

    def _分叉种子(自身,会话对象,请求边界):#切分叉种子
        """切含端稳定前缀；省略边界则切到当前末尾。"""
        事件们=会话对象.events#不可变快照
        最后=事件们[-1] if len(事件们)>0 else None#当前最后一条
        if 请求边界 is not None:#调用方指定
            边界=请求边界#用指定值
        else:#省略边界
            if 最后 is None:#空源
                return []#空源则空子
            边界=取字段(最后,'seq')#切到当前末尾
        if (not 是否安全整数(边界)) or 边界<0:#必须是非负安全整数
            raise 会话分叉错误(
                'fork boundary for session "'+str(会话对象.id)+'" must be a non-negative safe integer, got '+str(边界),
                'INVALID_BOUNDARY',
            )#非法边界
        if 边界>=len(事件们):#超出日志
            最后序号=取字段(最后,'seq') if 最后 is not None else None#当前最后 seq
            if 最后序号 is None:#无
                最后文本='none'#无
            else:#有
                最后文本=str(最后序号)#有
            raise 会话分叉错误(
                'fork boundary '+str(边界)+' does not exist in session "'+str(会话对象.id)+'" (last seq: '+最后文本+')',
                'INVALID_BOUNDARY',
            )#不存在的边界
        边界事件=事件们[边界]#边界上的事件
        if 边界事件 is None or 取字段(边界事件,'seq')!=边界:#必须贴合连续 seq
            raise 会话分叉错误(
                'fork boundary '+str(边界)+' does not match a contiguous event seq in session "'+str(会话对象.id)+'"',
                'INVALID_BOUNDARY',
            )#不连续
        最后轮次=None#最后一轮边界
        前缀=事件们[:边界+1]#含端前缀
        下标=len(前缀)-1#从后往前
        while 下标>=0:#从后往前
            种类=取字段(前缀[下标],'type')#事件类型
            if 种类=='turn/start' or 种类=='turn/end':#轮次边界
                最后轮次=前缀[下标]#命中
                break#停止
            下标-=1#继续往前
        if 最后轮次 is not None and 取字段(最后轮次,'type')=='turn/start':#结束在打开轮次内
            raise 会话分叉错误(
                'fork boundary '+str(边界)+' in session "'+str(会话对象.id)+'" ends inside open turn '+str(取字段(取字段(最后轮次,'data'),'turn')),
                'OPEN_TURN',
            )#打开轮次
        return list(事件们[:边界+1])#含端前缀

    def _解析分叉源(自身,源):#解析分叉源
        """解析分叉源：会话 id 字符串或本存储在线会话实例。"""
        if isinstance(源,str):#按 id
            会话对象=自身.获取(源)#查找在线
            if 会话对象 is None:#未知
                raise 会话分叉错误('session "'+str(源)+'" not found','SESSION_NOT_FOUND')#未知
            return 会话对象#在线会话
        在线=自身.获取(源.id)#按对象 id 查找
        if 在线 is None:#存储里没有
            raise 会话分叉错误('session "'+str(源.id)+'" not found','SESSION_NOT_FOUND')#未知
        if 在线 is not 源:#必须是在线实例
            raise 会话分叉错误('session "'+str(源.id)+'" is not the live store instance','SESSION_NOT_LIVE')#必须是在线实例
        return 源#就是在线对象

# 会话头字段权威在 .类型，本模块再导出供持久化等消费方。
默认=会话存储#中文默认导出
default=会话存储#Cordis默认导出（协议槽）
