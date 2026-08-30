"""第一方后端共用的缓冲、序列化、收养、修复与拆除编排。第三方后端可直接实现公开持久化接缝。"""
import json,math,threading#JSON相等、安全整数、后台串行链
from concurrent.futures import Future as _原生Future#单次操作结果
from ...依赖 import cordis#外部依赖胶水
from ...内核.会话 import (#会话包运行时原语
    收养会话事件,#收养会话事件
    中断轮次关闭器,#被打断回合的合成关闭事件
    已知会话事件类型,#本构建认识的事件类型
    会话格式版本,#本构建读取的日志格式版本
    会话准备,#会话预备
    快照json值,#JSON无损快照
    快照会话事件,#事件快照
)#从会话包导入
from ...工具.超时 import 定时器延迟上限毫秒#导入定时器上限
from ...模型后端.llm import 结构化克隆#深拷贝
from .预备 import 会话预备池,观察排队取消#取消观察与预备池
from .写后 import 会话写后#写后控制器

默认预备会话缓存大小=5#默认预备缓存大小
默认写批最大延迟毫秒=200#默认写批延迟毫秒
写批延迟上限毫秒=定时器延迟上限毫秒#写批延迟上限
安全整数上限=9007199254740991#Number.MAX_SAFE_INTEGER

持久化协调器选项字段=('preparedSessionCacheSize','writeBatchMaxDelayMs')#具体持久化后端供给协调器的策略字段
已存前缀字段=('meta','events','revision','tornMarker')#已存会话头、有效连续事件前缀、带源限定修订与可选撕裂尾巴标记
已存后缀字段=('meta','events')#已存会话头外加处于或越过所请求 seq 的事件（可寻址后缀读返回形态）
持久化后端字段=('name','loadStored','readStoredRevision','loadStoredFrom','appendBatch','commitRepair','list','locate','close')#协调器与具体后端之间的最小耐久原语约定（含可选钩子）
会话状态字段=('meta','cursor','materialized','owner')#协调器内存记账持有的每会话写入状态
活会话状态字段=('init','writes')#一个活会话的初始化与有界写后控制器
预备会话源字段=('inspection','session','revision','sessionLength','tornMarker','closers')#已校验冷源以及从它建成的精确未发布 Session

def _是否thenable(值):#判定可等待对象
    """对象是否可 wait 或 等待。"""
    if 值 is None:#空不是
        return False#不是
    if callable(getattr(值,'wait',None)):#Future 风格
        return True#可等待
    return callable(getattr(值,'等待',None))#外来 thenable

class 操作任务:#单次异步结果
    """单次操作的 Future 包装。"""
    def __init__(自身):#构造未决任务
        """构造未决任务。"""
        自身._future=_原生Future()#底层 Future
    def 兑现(自身,值=None):#成功结算
        """成功结算。"""
        if not 自身._future.done():#尚未结算
            自身._future.set_result(值)#写入结果
        return 值#返回兑现值
    def 拒绝(自身,错误):#失败结算
        """失败结算。"""
        if not 自身._future.done():#尚未结算
            if isinstance(错误,BaseException):#已是异常
                自身._future.set_exception(错误)#原样拒绝
            else:#非异常
                自身._future.set_exception(Exception(错误))#包装拒绝
    def wait(自身,超时=None):#阻塞等待
        """阻塞等到结算。"""
        return 自身._future.result(timeout=超时)#取结果或抛错
    def 等待(自身,超时=None):#兼容外来调用
        """wait 别名。"""
        return 自身.wait(超时)#转发

def _等待(值):#统一阻塞到结算
    """wait 或 等待。"""
    if callable(getattr(值,'wait',None)):#Future 风格
        return 值.wait()#等待
    return 值.等待()#外来 thenable

def 已兑现(值=None):#立刻兑现的操作任务
    """立刻兑现的操作任务。"""
    任务=操作任务()#新任务
    任务.兑现(值)#立刻成功
    return 任务#已完成

def 解开(值):#可等待则等待否则原样
    """可等待则等待，否则原样返回。"""
    if _是否thenable(值):#可等待
        return _等待(值)#等待
    return 值#同步值

def 若已中止则抛出(信号):#取消优先抛出
    """已取消则抛出。"""
    if 信号 is None:#无信号
        return#放过
    方法=getattr(信号,'throwIfAborted',None)#Node风格
    if callable(方法):#有方法
        方法()#抛出
        return#已检查
    if getattr(信号,'aborted',False) is True:#已中止
        raise Exception('aborted')#取消
    if getattr(信号,'已中止',False) is True:#中文旗标
        raise Exception('aborted')#取消

def 是否安全整数(值):#对齐 Number.isSafeInteger
    """对齐 JS Number.isSafeInteger，排除布尔。"""
    if isinstance(值,bool):#布尔不是整数
        return False#布尔不是安全整数
    if isinstance(值,int):#整数
        return abs(值)<=安全整数上限#在安全范围内
    if isinstance(值,float):#浮点
        if not math.isfinite(值) or 值!=int(值):#非有限或非整
            return False#不是安全整数
        return abs(值)<=安全整数上限#在安全范围内
    return False#其它类型

def 取字段(对象,键):#读取字段
    """读取映射或对象上的字段。"""
    if isinstance(对象,dict):#映射
        return 对象[键]#映射键
    return getattr(对象,键)#对象属性

def 试取(对象,键,默认=None):#读取可选字段
    """读取可选字段，缺席为默认。"""
    if 对象 is None:#无对象
        return 默认#缺席
    if isinstance(对象,dict):#映射
        return 对象.get(键,默认)#映射键
    return getattr(对象,键,默认)#对象属性

def 冻结视图(元,事件们):#冻结逻辑视图
    """返回不可变检查视图字典。"""
    return {'meta':元,'events':事件们}#头与事件

class 会话持久化损坏错误(Exception):#持久化损坏错误
    """后端读取成功后，耐久会话内容未通过校验。"""
    def __init__(自身,消息,原因=None):#构造损坏错误
        """记下稳定损坏上下文与原始校验失败。"""
        if 原因 is not None:#有cause
            super().__init__(消息)#消息
            自身.__cause__=原因#挂cause
        else:#无cause
            super().__init__(消息)#消息
        自身.name='SessionPersistenceCorruptionError'#固定错误名

class 会话格式不支持错误(Exception):#格式不支持错误
    """已存日志完好，但本运行时无法忠实解释。"""
    def __init__(自身,消息,位置=None):#构造拒绝错误
        """记下无法解释原因与可选产物位置。"""
        super().__init__(消息)#消息
        自身.name='SessionFormatUnsupportedError'#固定错误名
        自身.location=位置#位置
        自身.位置=位置#中文别名

def 会话格式版本拒绝文案(标识,版本):#格式版本拒绝文案
    """本构建不读取的已存会话格式版本的、带方向的拒绝文案。"""
    if 版本>会话格式版本:#比本构建新
        return 'session "'+str(标识)+'" uses log format v'+str(版本)+', but this harness reads only v'+str(会话格式版本)+': the log was written by a newer harness — upgrade the harness to open it'#更新的harness写出
    return 'session "'+str(标识)+'" uses log format v'+str(版本)+', older than the supported v'+str(会话格式版本)+', and this build ships no upgrade path for it'#更旧且无升级路径

def 结算错误们(承诺们):#收集已拒绝原因
    """从一组承诺收集拒绝原因（不抛）。"""
    错误们=[]#拒绝原因
    for 项 in 承诺们:#遍历
        try:#等结算
            解开(项)#成败都等
        except BaseException as 原因:#拒绝
            错误们.append(原因)#记下拒绝
    return 错误们#返回原因列表

def 种子覆盖前缀(种子,前缀):#种子是否覆盖前缀
    """活会话种子是否精确再现一份已持久前缀。"""
    if len(前缀)>len(种子):#前缀长于种子
        return False#不覆盖
    下标=0#前缀下标
    for 事件 in 前缀:#每条前缀事件
        种子事件=种子[下标]#对应种子事件
        if 种子事件 is None:#不存在
            return False#不覆盖
        if json.dumps(种子事件,ensure_ascii=False,sort_keys=True,default=str)!=json.dumps(事件,ensure_ascii=False,sort_keys=True,default=str):#JSON不等
            return False#不覆盖
        下标+=1#下一条
    return True#全部相等

def 断言受支持事件(事件们,标识):#断言事件受支持
    """拒绝本构建无法回放的过时 v0 词汇事件。"""
    遗留类型='request/header-delta'#遗留头增量类型
    for 事件 in 事件们:#找遗留头增量
        if 取字段(事件,'type')==遗留类型:#有遗留头增量
            raise Exception('session "'+str(标识)+'" contains unsupported legacy request/header-delta event at seq '+str(取字段(事件,'seq')))#拒绝
    遗留模式类型='mode/set'#遗留模式类型
    for 事件 in 事件们:#找遗留模式
        if 取字段(事件,'type')==遗留模式类型:#有遗留模式
            raise Exception('session "'+str(标识)+'" contains unsupported legacy mode/set event at seq '+str(取字段(事件,'seq')))#拒绝
    for 事件 in 事件们:#找遗留fallback原因
        if 取字段(事件,'type')=='request/header':#请求头
            数据=试取(事件,'data')#载荷
            if isinstance(数据,dict) and 数据.get('reason')=='fallback':#原因是fallback
                raise Exception('session "'+str(标识)+'" contains unsupported legacy request/header reason "fallback" at seq '+str(取字段(事件,'seq')))#拒绝

def 当作记录(值):#当作字段表
    """返回对象记录，不把数组放宽成消息载荷。"""
    if isinstance(值,dict) and not isinstance(值,list):#是非数组对象
        return 值#收成记录
    if 值 is not None and not isinstance(值,(list,tuple,str,bytes,int,float,bool)) and hasattr(值,'__dict__'):#普通对象
        return vars(值)#收成记录
    return None#否则不是记录

def 仅有键(记录,必填,可选=None):#键集合守卫
    """记录是否含全部必填键，且没有可选扩展集合之外的键。"""
    if 可选 is None:#缺省无可选
        可选=[]#空可选
    允许=list(必填)+list(可选)#允许的键
    for 键 in 记录.keys():#没有额外键
        if 键 not in 允许:#额外键
            return False#不合法
    for 键 in 必填:#必填都在
        if 键 not in 记录:#缺必填
            return False#不合法
    return True#恰好这些键

def 遗留消息标识(标识,序号):#遗留消息id
    """为身份出现之前持久化的消息铸造稳定导入身份。"""
    return 'legacy-message:'+str(标识)+':'+str(序号)#按会话与seq铸造

def 替换起点(事件):#替换起点seq
    """读取替换起点，把畸形表面元数据留给会话校验器。"""
    操作=当作记录(试取(事件,'surfaceOp'))#表面操作记录
    if 操作 is not None and 操作.get('op')=='replace' and isinstance(操作.get('start'),(int,float)):#是replace且start是数字
        return 操作['start']#返回起点
    return None#否则没有

def 需要遗留前缀(事件):#是否需要遗留前缀
    """一条后缀事件是否需要只能从前面已存前缀得到的事实。"""
    数据=当作记录(试取(事件,'data'))#事件载荷记录
    遗留转向类型='steering/message'#遗留转向类型
    if 取字段(事件,'type')==遗留转向类型:#转向事件总需要前缀
        return True#需要
    if 数据 is None:#无记录则不需要
        return False#不需要
    类型=取字段(事件,'type')#事件类型
    if 类型=='user/message':#用户消息
        return ('id' not in 数据) and ('content' in 数据)#旧形态无id有content
    if 类型=='assistant/message':#助手消息
        return ('message' not in 数据) and ('content' in 数据)#旧形态无message有content
    if 类型=='tool/result':#工具结果
        return ('message' not in 数据) and ('callId' in 数据)#旧形态无message有callId
    return False#其余不需要前缀

def 迁移遗留转向事件(事件,标识):#迁移遗留转向事件
    """把已移除的转向表面事件升级成当前的用户消息等价物。"""
    遗留类型='steering/message'#遗留类型名
    if 取字段(事件,'type')!=遗留类型:#不是转向则原样
        return 事件#原样
    数据=当作记录(试取(事件,'data'))#载荷记录
    if 数据 is None:#不是记录
        raise Exception('session "'+str(标识)+'" contains malformed pre-react-loop steering/message at seq '+str(取字段(事件,'seq')))#畸形拒绝
    包装=当作记录(数据.get('message'))#已包装消息
    if 包装 is not None and 是否安全整数(数据.get('turn')) and 仅有键(数据,['turn','message']):#已有message包装
        升级=dict(事件) if isinstance(事件,dict) else dict(vars(事件))#拷贝信封
        升级['type']='user/message'#改为用户消息
        升级['data']=包装#拆包成用户消息
        return 升级#升级结果
    if (not 是否安全整数(数据.get('turn'))) or (not 仅有键(数据,['turn','content','source'])):#旧信封畸形
        raise Exception('session "'+str(标识)+'" contains malformed pre-react-loop steering/message at seq '+str(取字段(事件,'seq')))#畸形拒绝
    消息={键:值 for 键,值 in 数据.items() if 键!='turn'}#去掉turn留下消息字段
    消息['id']=遗留消息标识(标识,取字段(事件,'seq'))#补遗留id
    消息['role']='user'#角色
    升级=dict(事件) if isinstance(事件,dict) else dict(vars(事件))#拷贝信封
    升级['type']='user/message'#改为用户消息
    升级['data']=消息#当前载荷
    return 升级#升级结果

def 迁移遗留回合开始事件(事件,标识):#迁移遗留回合开始
    """在核实完整旧回合开始信封后去掉过时的 trigger。"""
    if 取字段(事件,'type')!='turn/start':#不是回合开始
        return 事件#原样
    数据=当作记录(试取(事件,'data'))#载荷记录
    if 数据 is None or 'trigger' not in 数据:#无trigger则已是当前形态
        return 事件#原样
    触发=当作记录(数据.get('trigger'))#trigger记录
    轮次=数据.get('turn')#turn
    if (not 是否安全整数(轮次)) or 轮次<1 or (not 仅有键(数据,['turn','trigger'])) or 触发 is None or not isinstance(触发.get('kind'),str) or len(触发['kind'])==0:#畸形
        raise Exception('session "'+str(标识)+'" contains malformed pre-react-loop turn/start at seq '+str(取字段(事件,'seq')))#畸形拒绝
    升级=dict(事件) if isinstance(事件,dict) else dict(vars(事件))#拷贝信封
    升级['data']={'turn':轮次}#只保留turn
    return 升级#升级结果

def 迁移遗留回合结束事件(事件,标识):#迁移遗留回合结束
    """升级过时的回合结束，同时保留最新主线信封。"""
    if 取字段(事件,'type')!='turn/end':#不是回合结束
        return 事件#原样
    数据=当作记录(试取(事件,'data'))#载荷记录
    if 数据 is None:#非记录则原样
        return 事件#原样
    def 畸形():#畸形拒绝
        """抛出畸形拒绝。"""
        raise Exception('session "'+str(标识)+'" contains malformed pre-react-loop turn/end at seq '+str(取字段(事件,'seq')))#抛出
    原因=当作记录(数据.get('reason'))#原因记录
    轮次=数据.get('turn')#turn
    if (not 是否安全整数(轮次)) or 轮次<1 or (not 仅有键(数据,['turn','reason'])) or 原因 is None or not isinstance(原因.get('kind'),str):#reason畸形
        return 畸形()#拒绝
    当前原因=None#升级后的原因
    种类=原因['kind']#原因种类
    if 种类 in ('completed','blocked','max-tokens','interrupted'):#已是当前形态族
        if not 仅有键(原因,['kind']):#只能有kind
            return 畸形()#拒绝
        return 事件#已是当前形态
    if 种类=='aborted':#中止
        if 'reason' in 原因:#已有嵌套reason则当前形态
            return 事件#原样
        if not 仅有键(原因,['kind']):#旧形态只能有kind
            return 畸形()#拒绝
        当前原因={'kind':'aborted','reason':{'kind':'legacy'}}#补遗留原因
    elif 种类=='disposed':#拆除
        if not 仅有键(原因,['kind']):#只能有kind
            return 畸形()#拒绝
        当前原因={'kind':'aborted','reason':{'kind':'disposed'}}#映射为aborted/disposed
    elif 种类=='error':#错误
        if 'error' in 原因:#已有error字段则当前形态
            return 事件#原样
        步骤=原因.get('step')#step
        if (not 是否安全整数(步骤)) or 步骤<0:#step非法
            return 畸形()#拒绝
        失败=当作记录(原因.get('failure'))#failure记录
        if 失败 is not None and 仅有键(原因,['kind','step','failure']) and 仅有键(失败,['message','code'],['status','providerRetryAfterMs','requestId']) and isinstance(失败.get('message'),str) and isinstance(失败.get('code'),str) and (失败.get('status') is None or isinstance(失败.get('status'),(int,float))) and (失败.get('providerRetryAfterMs') is None or isinstance(失败.get('providerRetryAfterMs'),(int,float))) and (失败.get('requestId') is None or isinstance(失败.get('requestId'),str)):#带failure的旧形态
            当前原因={'kind':'error','error':失败}#升到error字段
        else:#message形态
            消息键=['kind','step','message'] if 原因.get('code') is None else ['kind','step','message','code']#按有无code选键
            if (not 仅有键(原因,消息键)) or (not isinstance(原因.get('message'),str)) or (原因.get('code') is not None and not isinstance(原因.get('code'),str)):#键不对
                return 畸形()#拒绝
            当前原因={'kind':'error','error':{'message':原因['message'],'code':原因['code'] if isinstance(原因.get('code'),str) else 'UNKNOWN'}}#升到error对象
    else:#未知种类
        return 事件#原样留给校验
    新数据=dict(数据)#其余字段
    新数据['reason']=当前原因#升级后的原因
    升级=dict(事件) if isinstance(事件,dict) else dict(vars(事件))#拷贝信封
    升级['data']=新数据#写回载荷
    return 升级#升级结果

def 迁移遗留消息事件(事件,标识,消息标识表):#迁移遗留消息事件
    """把一条身份出现前的消息事件升级成当前包装形态。"""
    数据=当作记录(试取(事件,'data'))#载荷记录
    if 数据 is None:#非记录则原样
        return 事件#原样
    类型=取字段(事件,'type')#事件类型
    if 类型=='user/message':#用户消息
        if ('id' in 数据) or ('role' in 数据) or ('message' in 数据) or ('content' not in 数据) or ('source' not in 数据):#不是旧形态
            return 事件#原样
        新数据=dict(数据)#旧content/source
        新数据['id']=遗留消息标识(标识,取字段(事件,'seq'))#遗留id
        新数据['role']='user'#角色
        升级=dict(事件) if isinstance(事件,dict) else dict(vars(事件))#拷贝信封
        升级['data']=新数据#当前载荷
        return 升级#升级结果
    if 类型=='assistant/message':#助手消息
        if ('message' in 数据) or ('content' not in 数据) or ('provenance' not in 数据):#不是旧形态
            return 事件#原样
        内容=数据['content']#内容
        出处=数据['provenance']#provenance
        其余={键:值 for 键,值 in 数据.items() if 键 not in ('content','provenance')}#其余字段
        来源=dict(当作记录(出处) or {})#旧provenance字段
        来源['kind']='model'#模型来源
        其余['message']={'id':遗留消息标识(标识,取字段(事件,'seq')),'role':'assistant','content':内容,'source':来源}#包装消息
        升级=dict(事件) if isinstance(事件,dict) else dict(vars(事件))#拷贝信封
        升级['data']=其余#当前载荷
        return 升级#升级结果
    if 类型=='tool/result':#工具结果
        if ('message' in 数据) or ('callId' not in 数据) or ('content' not in 数据) or ('isError' not in 数据):#不是旧形态
            return 事件#原样
        调用标识=数据['callId']#调用id
        内容=数据['content']#结果内容
        是否错误=数据['isError']#是否错误
        其余={键:值 for 键,值 in 数据.items() if 键 not in ('callId','content','isError')}#其余字段
        继承起点=替换起点(事件)#替换时继承的起点
        消息标识值=遗留消息标识(标识,取字段(事件,'seq')) if 继承起点 is None else 消息标识表.get(继承起点)#自铸或继承
        其余['message']={'id':消息标识值,'role':'user','content':[{'type':'tool-result','toolCallId':调用标识,'content':内容,'isError':是否错误}],'source':{'kind':'tool','callId':调用标识}}#包装消息
        升级=dict(事件) if isinstance(事件,dict) else dict(vars(事件))#拷贝信封
        升级['data']=其余#当前载荷
        return 升级#升级结果
    return 事件#其余类型原样

def 事件消息标识(事件):#取消息id
    """读取一条已校验当前事件所携带的已标识消息。"""
    数据=当作记录(试取(事件,'data'))#载荷记录
    if 取字段(事件,'type')=='user/message':#用户消息在顶层
        消息=数据#顶层即消息
    else:#其余在message
        消息=当作记录(None if 数据 is None else 数据.get('message'))#内嵌消息
    if 消息 is not None and isinstance(消息.get('id'),str):#字符串id才算
        return 消息['id']#消息id
    return None#无消息id

def 快照已存事件(事件们,标识):#快照已存事件
    """把已存事件物化为已升级、已校验、消息不可变的快照。"""
    断言受支持事件(事件们,标识)#先拒绝无法回放的遗留
    消息标识表={}#seq到消息id
    结果=[]#快照列表
    for 事件 in 事件们:#逐条升级并快照
        已升开始=迁移遗留回合开始事件(事件,标识)#升级回合开始
        已升回合=迁移遗留回合结束事件(已升开始,标识)#升级回合结束
        已升转向=迁移遗留转向事件(已升回合,标识)#升级转向
        快照=快照会话事件(迁移遗留消息事件(已升转向,标识,消息标识表))#升级消息并快照
        消息标识值=事件消息标识(快照)#取出消息id
        if 消息标识值 is not None:#有消息id
            消息标识表[取字段(快照,'seq')]=消息标识值#记下供后续继承
        结果.append(快照)#返回快照
    return 结果#快照列表

def 收养已存事件(事件们,标识):#收养已存事件
    """升级并校验一份独占拥有的后端结果，不复制它。"""
    断言受支持事件(事件们,标识)#先拒绝无法回放的遗留
    消息标识表={}#seq到消息id
    下标=0#数组下标
    while 下标<len(事件们):#就地替换
        事件=事件们[下标]#当前事件
        已升开始=迁移遗留回合开始事件(事件,标识)#升级回合开始
        已升回合=迁移遗留回合结束事件(已升开始,标识)#升级回合结束
        已升转向=迁移遗留转向事件(已升回合,标识)#升级转向
        已收养=收养会话事件(迁移遗留消息事件(已升转向,标识,消息标识表))#升级消息并收养
        事件们[下标]=已收养#写回数组
        消息标识值=事件消息标识(已收养)#取出消息id
        if 消息标识值 is not None:#有消息id
            消息标识表[取字段(已收养,'seq')]=消息标识值#记下供后续继承
        下标+=1#下一条
    return 事件们#返回同一数组

class 持久化协调器:#持久化协调器
    """拥有与后端无关的会话写路径编排。后端构造一个，实现持久化后端约定，并把其写/读服务方法委托给对应的协调器方法。"""
    def __init__(自身,上下文,后端,选项=None):#构造协调器
        """安装写路径监听器、每会话退役，以及后端拆除 effect。"""
        if 选项 is None:#缺省选项
            选项={}#空选项
        预备缓存=选项.get('preparedSessionCacheSize',默认预备会话缓存大小)#预备缓存大小
        写批延迟=选项.get('writeBatchMaxDelayMs',默认写批最大延迟毫秒)#写批最大延迟
        if (not 是否安全整数(预备缓存)) or 预备缓存<1:#预备缓存非法
            raise TypeError('preparedSessionCacheSize must be a positive safe integer')#拒绝
        if (not 是否安全整数(写批延迟)) or 写批延迟<1 or 写批延迟>写批延迟上限毫秒:#写批延迟非法
            raise TypeError('writeBatchMaxDelayMs must be an integer between 1 and '+str(写批延迟上限毫秒))#拒绝
        自身.ctx=上下文#插件上下文
        自身.上下文=上下文#中文别名
        自身.backend=后端#具体后端
        自身.后端=后端#中文别名
        自身.写批最大延迟毫秒=写批延迟#记下延迟
        自身.状态表={}#id到会话状态
        自身.活表={}#活会话控制器
        自身.退役表={}#退役承诺
        自身.链={}#每id承诺链
        自身.预备池=会话预备池(预备缓存)#建预备池
        自身.安装写路径()#安装写路径

    def 后端名(自身):#人类可读后端名
        """人类可读的后端名，用于拆除失败的聚合错误。"""
        return getattr(自身.后端,'name',None) or getattr(自身.后端,'名称','persistence')#后端名

    def 创建(自身,头):#创建会话意图
        """登记分离的会话元数据，供第一次追加时惰性创建。"""
        快照=快照json值(头)#无损快照头
        if 快照 is None:#无法JSON序列化
            raise TypeError('session metadata must be losslessly JSON-serializable')#拒绝
        if (not 是否安全整数(取字段(快照,'createdAt'))) or 取字段(快照,'createdAt')<0:#创建时刻非法
            raise TypeError('session metadata createdAt must be a non-negative safe integer')#拒绝
        return 解开(自身.串行化(取字段(快照,'id'),lambda:自身.创建核心(快照)))#串行创建

    def 创建核心(自身,头):#创建核心
        """纯惰性：只记录意图。直到第一次追加才有产物。"""
        标识=取字段(头,'id')#会话id
        if 标识 in 自身.状态表 or 自身.预备池.有(标识):#内存已有
            raise Exception('session "'+str(标识)+'" already exists in this backend')#拒绝重复
        if 解开(自身.后端.loadStored(标识) if hasattr(自身.后端,'loadStored') else 自身.后端.加载已存(标识)) is not None:#磁盘已有日志
            raise Exception('session "'+str(标识)+'" already has a persisted log on disk; load/resume it instead of creating')#应load/resume
        自身.状态表[标识]={'meta':头,'cursor':0,'materialized':False}#记下未物化状态

    def 追加(自身,标识,事件们):#追加事件
        """耐久持久化一批事件。遵守只追加与连续 seq 约定。"""
        批次=快照json值(事件们)#无损快照批次
        if 批次 is None:#无法JSON序列化
            raise TypeError('session event batch is not losslessly JSON-serializable because it contains non-JSON-serializable data')#拒绝
        return 解开(自身.串行化(标识,lambda:自身.追加核心(标识,批次)))#串行追加

    def 追加核心(自身,标识,事件们):#追加核心
        """每条追加路径都汇到这里。"""
        断言受支持事件(事件们,标识)#拒绝无法回放的遗留
        if len(事件们)==0:#空批无操作
            return#无事
        自身.预备池.断言可写(标识)#预备占用时不可写
        状态=自身.状态表.get(标识)#已有状态
        if 状态 is None:#未跟踪则从存储收养
            状态=解开(自身.收养(标识))#收养
        下标=0#批次下标
        for 事件 in 事件们:#检查每条
            期望=状态['cursor']+下标#期望seq
            if 取字段(事件,'seq')!=期望:#seq对不上游标
                raise Exception('append seq mismatch for "'+str(标识)+'": expected '+str(期望)+' at index '+str(下标)+', got '+str(取字段(事件,'seq')))#拒绝缺口
            下标+=1#下一条
        追加批=getattr(自身.后端,'appendBatch',None) or getattr(自身.后端,'追加批次')#耐久追加
        解开(追加批(状态['meta'],事件们,状态['materialized']))#耐久追加
        状态['materialized']=True#已物化
        状态['cursor']+=len(事件们)#推进游标
        自身.预备池.使失效(标识)#使该id的预备失效

    def 预备(自身,标识,信号=None):#预备会话
        """预备并预留恢复所用的精确未发布 Session。"""
        while True:#修订重试循环
            解开(自身.等待退役(标识,信号))#先等退役排空
            if 自身.上下文.sessions.get(标识) is not None:#已经活着
                raise Exception('cannot prepare session "'+str(标识)+'" while it is live')#活着不能预备
            def 冷加载():#冷加载
                """串行冷加载。"""
                return 解开(自身.串行化(标识,lambda:自身.预备核心(标识)))#冷加载
            def 提交修复(源):#提交修复
                """串行提交修复。"""
                return 解开(自身.串行化(标识,lambda:自身.提交已预备(源),信号))#提交修复
            预留=解开(自身.预备池.预留(标识,冷加载,提交修复,信号))#独占预留
            if 预留 is None:#修订变了则重试
                continue#重试
            if 自身.上下文.sessions.get(标识) is not None:#预留期间变成活的
                自身.预备池.释放(预留,False)#释放预留
                raise Exception('cannot prepare session "'+str(标识)+'" while it is live')#活着不能预备
            def 释放回调():#释放时
                """还回预备池。"""
                源=预留['source']#预备源
                状态=预留['state']#会话状态
                会话对象=源['session']#未发布会话
                可复用=状态.get('owner') is None and len(会话对象.events)==源['sessionLength']#无活拥有方且长度未变
                自身.预备池.释放(预留,可复用)#还回预备池
            return 会话准备.创建(预留['source']['session'],{'release':释放回调})#包装预备

    def 加载(自身,标识):#加载会话
        """提交恢复并返回其不可变逻辑视图，不发布。"""
        while True:#修订重试循环
            解开(自身.等待退役(标识))#先等退役
            活着=自身.上下文.sessions.get(标识)#是否已活
            if 活着 is not None:#活的则快照活会话
                return 解开(自身.加载活快照(活着))#返回活快照
            def 冷加载():#冷加载
                """串行冷加载。"""
                return 解开(自身.串行化(标识,lambda:自身.预备核心(标识)))#冷加载
            def 提交修复(源):#提交修复
                """串行提交修复。"""
                return 解开(自身.串行化(标识,lambda:自身.提交已预备(源)))#提交修复
            预留=解开(自身.预备池.预留(标识,冷加载,提交修复))#独占预留
            if 预留 is None:#修订变了则重试
                continue#重试
            已附着=自身.上下文.sessions.get(标识)#预留期间是否已附着
            if 已附着 is not None:#已活
                自身.预备池.丢弃(预留)#丢掉预留
                return 解开(自身.加载活快照(已附着))#返回活快照
            自身.预备池.丢弃(预留)#检查完丢掉预留
            return 预留['source']['inspection']#返回冷视图

    def 检查(自身,标识,信号=None):#检查会话
        """检查一个逻辑会话，不发布也不提交恢复。"""
        while True:#修订重试循环
            若已中止则抛出(信号)#已取消则抛
            if 标识 in 自身.退役表:#有退役则等待
                解开(自身.等待退役(标识,信号))#等待
            活着=自身.上下文.sessions.get(标识)#是否已活
            if 活着 is not None:#活的则借活视图
                return 自身.检查活会话(活着)#借活视图
            try:#尝试冷检查
                def 冷加载():#冷加载
                    """串行冷加载。"""
                    return 解开(自身.串行化(标识,lambda:自身.预备核心(标识)))#冷加载
                源=解开(自身.预备池.检查(标识,冷加载,信号))#共享观察预备源
                已附着=自身.上下文.sessions.get(标识)#观察期间是否已附着
                if 已附着 is not None:#已活则借活视图
                    return 自身.检查活会话(已附着)#借活视图
                仍当前=解开(自身.串行化(标识,lambda:自身.预备源是否当前(源,信号),信号))#串行核对修订
                已发布=自身.上下文.sessions.get(标识)#核对期间是否已发布
                if 已发布 is not None:#已活则借活视图
                    return 自身.检查活会话(已发布)#借活视图
                if 仍当前:#仍当前则返回冷视图
                    return 源['inspection']#冷视图
                if 自身.预备池.丢弃就绪(标识,源)=='retained':#陈旧但被独占保留
                    return 源['inspection']#仍借用该视图
            except BaseException as 错误:#冷检查失败
                若已中止则抛出(信号)#取消优先
                已附着=自身.上下文.sessions.get(标识)#失败期间是否已附着
                if 已附着 is not None:#已活则借活视图
                    return 自身.检查活会话(已附着)#借活视图
                raise 错误#否则上抛

    def 从序号读(自身,标识,起始序号,信号=None):#从seq读
        """从起始序号起读取已存事件，分离且非变更。"""
        if (not 是否安全整数(起始序号)) or 起始序号<0:#fromSeq非法
            raise TypeError('readFrom fromSeq must be a non-negative safe integer, got '+str(起始序号))#拒绝
        退役=自身.退役表.get(标识)#可能的退役
        已退役=已兑现(None) if 退役 is None else 退役#退役承诺
        if 信号 is None:#无取消
            解开(已退役)#直接等
        else:#带取消等待退役
            解开(观察排队取消(已退役,信号,lambda:False))#带取消
        return 解开(自身.串行化(标识,lambda:自身.从序号读核心(标识,起始序号,信号),信号))#串行读后缀

    def 从序号读核心(自身,标识,起始序号,信号=None):#从seq读核心
        """返回头与后缀事件。"""
        若已中止则抛出(信号)#已取消则抛
        寻址读=getattr(自身.后端,'loadStoredFrom',None) or getattr(自身.后端,'从已存加载',None)#可选后缀读
        if 寻址读 is not None:#后端可寻址
            try:#读后缀
                后缀=解开(寻址读(标识,起始序号,信号))#寻址读
            except BaseException as 错误:#读取失败
                if 信号 is not None and (getattr(信号,'aborted',False) is True or getattr(信号,'已中止',False) is True):#取消优先
                    若已中止则抛出(信号)#取消优先
                raise 错误#其余上抛
            若已中止则抛出(信号)#读后检查取消
            if 后缀 is None:#没有产物
                raise Exception('session "'+str(标识)+'" not found')#没有产物
            头=后缀['meta'] if isinstance(后缀,dict) else 取字段(后缀,'meta')#头
            事件列表=后缀['events'] if isinstance(后缀,dict) else 取字段(后缀,'events')#事件
            自身.断言已存标识(标识,头)#头必须绑定该id
            自身.断言版本(头)#格式版本必须认识
            if any(需要遗留前缀(事件) for 事件 in 事件列表):#后缀需要更早前缀事实
                整份=解开(自身.读已存前缀(标识,信号))#改读完整前缀
                return {'meta':整份['meta'],'events':[事件 for 事件 in 整份['events'] if 取字段(事件,'seq')>=起始序号]}#再切后缀
            事件们=快照已存事件(事件列表,标识)#升级并快照
            自身.断言事件受支持(头,事件们)#拒绝未知必填类型
            return {'meta':结构化克隆(头),'events':事件们}#返回分离头与事件
        整份=解开(自身.读已存前缀(标识,信号))#顺序回退读完整前缀
        return {'meta':整份['meta'],'events':整份['events'][起始序号:]}#切后缀

    def 读已存前缀(自身,标识,信号=None):#读已存前缀
        """读一份分离的物理前缀，不做逻辑恢复或缓存。"""
        若已中止则抛出(信号)#已取消则抛
        加载=getattr(自身.后端,'loadStored',None) or getattr(自身.后端,'加载已存')#加载物理前缀
        已存=解开(加载(标识,信号))#加载物理前缀
        若已中止则抛出(信号)#读后检查取消
        if 已存 is None:#没有产物
            raise Exception('session "'+str(标识)+'" not found')#没有产物
        头=已存['meta'] if isinstance(已存,dict) else 取字段(已存,'meta')#头
        事件列表=已存['events'] if isinstance(已存,dict) else 取字段(已存,'events')#事件
        自身.断言已存标识(标识,头)#头必须绑定该id
        自身.断言版本(头)#格式版本必须认识
        事件们=快照已存事件(事件列表,标识)#升级并快照
        自身.断言事件受支持(头,事件们)#拒绝未知必填类型
        return {'meta':结构化克隆(头),'events':事件们}#分离结果

    def 预备核心(自身,标识):#预备核心
        """读取、在内存中修复、校验并冻结一份冷源一次。"""
        加载=getattr(自身.后端,'loadStored',None) or getattr(自身.后端,'加载已存')#加载物理前缀
        已存=解开(加载(标识))#加载物理前缀
        if 已存 is None:#没有产物
            raise Exception('session "'+str(标识)+'" not found')#没有产物
        try:#收养并平衡
            头=已存['meta'] if isinstance(已存,dict) else 取字段(已存,'meta')#头
            事件列表=已存['events'] if isinstance(已存,dict) else 取字段(已存,'events')#事件
            修订=已存['revision'] if isinstance(已存,dict) else 取字段(已存,'revision')#修订
            撕裂=已存.get('tornMarker') if isinstance(已存,dict) else getattr(已存,'tornMarker',None)#撕裂标记
            自身.断言已存标识(标识,头)#头必须绑定该id
            自身.断言版本(头)#格式版本必须认识
            已存事件=收养已存事件(list(事件列表),标识)#就地升级收养
            自身.断言事件受支持(头,已存事件)#拒绝未知必填类型
            关闭们=[收养会话事件(项) for 项 in 中断轮次关闭器(已存事件)]#合成关闭事件
            平衡=list(已存事件)+关闭们#平衡后的日志
            会话对象=自身.上下文.sessions.prepare(标识,{'seed':平衡,'meta':头,'seedSource':'persistence'})#预备未发布会话
            检查视图=冻结视图(会话对象.header,tuple(平衡))#冻结逻辑视图
            return {'inspection':检查视图,'session':会话对象,'revision':修订,'sessionLength':len(会话对象.events),'tornMarker':撕裂,'closers':关闭们}#预备源
        except 会话格式不支持错误:#格式拒绝原样抛
            raise#不加包装
        except BaseException as 错误:#校验失败
            raise 会话持久化损坏错误('stored session "'+str(标识)+'" failed validation: '+str(错误),错误)#其余包成损坏

    def 提交已预备(自身,源):#提交已预备源
        """提交一次已预备修复，并建立其无拥有方的耐久游标。"""
        标识=源['inspection']['meta']['id'] if isinstance(源['inspection']['meta'],dict) else 取字段(源['inspection']['meta'],'id')#会话id
        游标=len(源['inspection']['events'])#平衡后长度
        已有=自身.状态表.get(标识)#已有状态
        if 已有 is not None and 已有.get('owner') is not None:#已有活拥有方
            raise Exception('session "'+str(标识)+'" already has a live persistence owner')#不能提交
        if not 解开(自身.预备源是否当前(源)):#修订变了则放弃
            return None#放弃
        if 源.get('tornMarker') is not None or len(源['closers'])>0:#需要物理修复
            提交修复=getattr(自身.后端,'commitRepair',None) or getattr(自身.后端,'提交修复')#耐久修复
            解开(提交修复(源['inspection']['meta'],源.get('tornMarker'),源['closers']))#耐久修复
            return None#让调用方重试
        状态=已有 if 已有 is not None else {'meta':源['inspection']['meta'],'cursor':游标,'materialized':True}#已有或新建
        状态['meta']=源['inspection']['meta']#更新头
        状态['cursor']=游标#更新游标
        状态['materialized']=True#已物化
        自身.状态表[标识]=状态#写入记账
        return {'source':源,'state':状态}#提交成功

    def 预备源是否当前(自身,源,信号=None):#预备源是否仍当前
        """一份缓存源是否仍点名当前耐久日志修订。"""
        标识=源['inspection']['meta']['id'] if isinstance(源['inspection']['meta'],dict) else 取字段(源['inspection']['meta'],'id')#会话id
        读修订=getattr(自身.后端,'readStoredRevision',None) or getattr(自身.后端,'读已存修订')#读已存修订
        return 解开(读修订(标识,信号))==源['revision']#修订相等

    def 加载活快照(自身,会话对象):#加载活快照
        """返回一份已经活着的 Session 的耐久不可变视图。"""
        事件们=会话对象.events#活事件数组
        解开(自身.冲洗(会话对象))#先刷耐久
        状态=自身.状态表.get(会话对象.id)#刷后的状态
        if 状态 is None:#丢状态
            raise Exception('session "'+str(会话对象.id)+'" lost persistence state during load')#丢状态
        if len(事件们)==0:#空日志当找不到
            raise Exception('session "'+str(会话对象.id)+'" not found')#找不到
        if len(中断轮次关闭器(事件们))>0:#活回合仍打开
            raise Exception('cannot load session "'+str(会话对象.id)+'" while its live turn is open; use the live Session or wait for the turn to close')#打开回合不能load
        return 冻结视图(状态['meta'],事件们)#冻结视图

    def 检查活会话(自身,会话对象):#检查活会话
        """从已经活着的 Session 借用一份不可变视图。"""
        return 冻结视图(会话对象.header,会话对象.events)#冻结借用视图

    def 等待退役(自身,标识,信号=None):#等待退役
        """带着调用方取消等待一个正在退役的生命周期。"""
        退役=自身.退役表.get(标识)#可能的退役承诺
        已退役=已兑现(None) if 退役 is None else 退役#退役承诺
        if 信号 is None:#无取消
            return 已退役#直接等
        return 观察排队取消(已退役,信号,lambda:False)#排队期间可取消

    def 串行化(自身,标识,操作,信号=None):#按id串行化
        """在同一会话 id 的任何在途操作之后跑操作，使一个会话的写入永不交错。"""
        先前=自身.链.get(标识)#前一操作
        if 先前 is None:#无前一操作
            先前=已兑现(None)#已决议
        已开始=[False]#本操作是否已开始
        下一=操作任务()#本操作任务
        def 跑():#真正启动
            """前一成败都跑本操作。"""
            try:#等前一
                try:#成败都继续
                    解开(先前)#等前一
                except BaseException:#前一拒绝不毒化
                    pass#吞掉前一拒绝
                若已中止则抛出(信号)#开始前检查取消
                已开始[0]=True#标记已开始
                结果=解开(操作())#跑操作
                下一.兑现(结果)#成功
            except BaseException as 错误:#本操作失败
                下一.拒绝(错误)#拒绝
        尾巴=操作任务()#吞掉拒绝的尾巴
        def 收尾():#尾巴结算
            """让链条活着，但为本操作的拒绝给下一等待者吞掉。"""
            try:#等本操作
                解开(下一)#成败都等
            except BaseException:#吞掉拒绝
                pass#吞掉
            尾巴.兑现(None)#尾巴决议
            if 自身.链.get(标识) is 尾巴:#仍是本尾巴才删
                del 自身.链[标识]#删除
        自身.链[标识]=尾巴#安装尾巴
        threading.Thread(target=跑,daemon=True).start()#后台跑本操作
        threading.Thread(target=收尾,daemon=True).start()#后台收尾
        if 信号 is None:#无取消
            return 下一#返回本操作
        return 观察排队取消(下一,信号,lambda:已开始[0])#带取消观察排队

    def 收养(自身,标识):#从存储收养
        """为已在存储中发现、但尚未在内存中的会话构建状态。"""
        while True:#修订重试
            源=自身.预备池.取走就绪(标识)#就绪源
            if 源 is None:#无就绪
                源=解开(自身.预备核心(标识))#新预备
            已提交=解开(自身.提交已预备(源))#提交修复
            if 已提交 is not None:#成功则返回状态
                return 已提交['state']#返回状态

    def 断言版本(自身,头):#断言格式版本
        """格式版本必须认识。"""
        if 取字段(头,'version')==会话格式版本:#正是本构建版本
            return#放过
        raise 自身.不支持(头,会话格式版本拒绝文案(取字段(头,'id'),取字段(头,'version')))#外版本拒绝

    def 断言事件受支持(自身,头,事件们):#断言事件类型受支持
        """拒绝含有本构建不认识的事件类型的日志，除非标为可忽略。"""
        for 事件 in 事件们:#逐条检查
            类型=取字段(事件,'type')#事件类型
            if 类型 in 已知会话事件类型 or 试取(事件,'ignorable') is True:#认识或可忽略
                continue#放过
            raise 自身.不支持(头,'session "'+str(取字段(头,'id'))+'" contains event type "'+str(类型)+'" (seq '+str(取字段(事件,'seq'))+') unknown to this harness and not marked ignorable; refusing to interpret the log — it was likely written by a newer harness')#未知必填类型拒绝

    def 不支持(自身,头,原因):#构造格式拒绝
        """构造指向原始产物（后端有的话）的格式拒绝。"""
        定位=getattr(自身.后端,'locate',None) or getattr(自身.后端,'定位',None)#可选产物位置
        位置=定位(头) if callable(定位) else None#位置
        if 位置 is None:#无路径
            return 会话格式不支持错误(原因)#格式错误
        路径=位置['path'] if isinstance(位置,dict) else 取字段(位置,'path')#绝对路径
        return 会话格式不支持错误(原因+' (raw log: '+str(路径)+')',位置)#有路径则附上

    def 断言已存标识(自身,标识,头):#断言已存id
        """拒绝未绑定到所请求会话 id 的后端元数据。"""
        if 取字段(头,'id')!=标识:#头id对不上
            raise Exception('stored session identity mismatch: requested "'+str(标识)+'", header contains "'+str(取字段(头,'id'))+'"')#身份不匹配

    def 安装写路径(自身):#安装写路径
        """安装写路径监听器与拆除 effect。"""
        上下文=自身.上下文#插件上下文
        名=自身.后端名()#后端名
        def 装拆除():#登记拆除
            """登记拆除副作用。"""
            def 拆除():#拆除副作用
                """排空活会话并关闭后端。"""
                拆除错误=None#排空失败
                try:#排空活会话
                    错误们=结算错误们([自身.冲洗(会话对象) for 会话对象 in list(自身.活表.keys())])#收集flush失败
                    while len(自身.链)>0:#排空串行链
                        结算错误们(list(自身.链.values()))#等链空
                    if len(错误们)>0:#有flush失败
                        raise 聚合错误(错误们,名+' dispose failed')#聚合拆除失败
                except BaseException as 错误:#排空失败
                    拆除错误=错误#记下主失败
                    raise#继续抛
                finally:#无论排空成败
                    try:#关闭后端
                        关闭=getattr(自身.后端,'close',None) or getattr(自身.后端,'关闭',None)#可选关闭
                        if callable(关闭):#有关闭
                            解开(关闭())#关闭
                    except BaseException as 关闭错误:#关闭失败
                        if 拆除错误 is None:#排空成功则抛关闭错误
                            raise 关闭错误#抛关闭错误
            return 拆除#返回拆除器
        上下文.effect(装拆除,名+' write path')#effect名
        def 会话已创建(会话对象):#会话创建
            """创建时捕获头，并持久化分叉的种子一次。"""
            自身.取或建活控制器(会话对象)#启动该会话写路径
        上下文.on('session/created',会话已创建)#created监听结束
        def 会话事件(会话对象,事件):#会话事件
            """保留每条冻结事件的持久化拥有副本，并启动其有界窗口。"""
            活=自身.取或建活控制器(会话对象)#取得活控制器
            活['writes'].入队(事件)#入队写后
        上下文.on('session/event',会话事件)#event监听结束
        def 会话冲洗(会话对象):#flush监听
            """调用方把flush当作缓冲写入的立即耐久屏障。"""
            return 自身.冲洗(会话对象)#冲洗
        上下文.on('session/flush',会话冲洗)#flush监听
        def 会话已拆除(会话对象):#disposed监听
            """会话拆除只观察，因此退役自己包含失败。"""
            自身.退役(会话对象)#退役
        上下文.on('session/disposed',会话已拆除)#disposed监听
        for 会话对象 in 上下文.sessions.list():#播种已有活会话
            自身.取或建活控制器(会话对象)#HMR播种

    def 退役(自身,会话对象):#退役会话
        """启动并观察一个已拆除会话的最终排空。"""
        if 会话对象 not in 自身.活表:#从未初始化则忽略
            return#忽略
        退役任务=操作任务()#退役任务
        def 跑退役():#后台退役
            """跑退役核心。"""
            try:#退役
                解开(自身.退役核心(会话对象))#退役核心
                退役任务.兑现(None)#成功
            except BaseException as 错误:#退役失败
                退役任务.拒绝(错误)#拒绝
        自身.退役表[会话对象.id]=退役任务#记下退役任务
        def 忘掉():#结算后忘掉
            """结算后忘掉退役任务。"""
            if 自身.退役表.get(会话对象.id) is 退役任务:#仍是本任务才删
                del 自身.退役表[会话对象.id]#删除
        def 警告失败(错误):#退役失败警告
            """退役失败警告。"""
            忘掉()#忘掉
            自身.上下文.logger.warn(自身.后端名()+': session "'+str(会话对象.id)+'" retirement failed: '+str(错误))#警告
        def 盯退役():#成败都忘掉
            """成败都忘掉；失败警告。"""
            try:#等退役
                退役任务.wait()#成功
                忘掉()#忘掉
            except BaseException as 错误:#失败
                警告失败(错误)#警告并忘掉
        threading.Thread(target=跑退役,daemon=True).start()#后台退役
        threading.Thread(target=盯退役,daemon=True).start()#观察结算

    def 退役核心(自身,会话对象):#退役核心
        """排空并释放一个精确已拆除 Session 生命周期拥有的状态。"""
        解开(自身.冲洗(会话对象))#先刷耐久
        标识=取字段(会话对象.header,'id')#会话id
        def 释放():#串行释放
            """丢掉活控制器与可选状态。"""
            if 会话对象 in 自身.活表:#有活控制器
                del 自身.活表[会话对象]#丢掉活控制器
            状态=自身.状态表.get(标识)#当前状态
            if 状态 is not None and 状态.get('owner') is 会话对象:#本生命周期拥有则丢掉状态
                del 自身.状态表[标识]#丢掉状态
        return 解开(自身.串行化(标识,释放))#串行释放

    def 取或建活控制器(自身,会话对象):#取得或创建活控制器
        """返回一个活会话的那一个生命周期控制器，需要时创建。"""
        已有=自身.活表.get(会话对象)#已有控制器
        if 已有 is not None:#复用
            return 已有#复用
        预留=自身.预备池.按会话取预留(会话对象)#是否有预备预留
        if 预留 is not None:#从预备附着
            已恢复=自身.附着已预备(会话对象,预留)#绑定预备
            自身.活表[会话对象]=已恢复#记下控制器
            return 已恢复#返回附着后的控制器
        种子=[结构化克隆(事件) for 事件 in 会话对象.events]#拷贝创建时种子
        活={'init':已兑现(None),'writes':None}#新活控制器占位
        活['writes']=自身.创建写后(会话对象,lambda:活['init'])#写后依赖init
        自身.活表[会话对象]=活#先挂上以免重入
        活['init']=自身.串行化(取字段(会话对象.header,'id'),lambda:自身.已创建时(会话对象,种子))#串行onCreated
        活['init'].catch(lambda _错误:None)#失败由flush/拆除经控制器观察
        return 活#返回新控制器

    def 附着已预备(自身,会话对象,预留):#附着已预备会话
        """绑定一份精确已预备 Session，并只持久化其未发布后缀。"""
        源=预留['source']#预备源
        状态=预留['state']#会话状态
        if 源['session'] is not 会话对象 or 状态.get('owner') is not None or 状态['cursor']!=len(源['inspection']['events']) or 会话对象.firstLiveSeq!=状态['cursor']:#预备与状态不一致
            raise Exception('session "'+str(会话对象.id)+'" preparation no longer matches its persistence state')#预备与状态不一致
        后缀=[结构化克隆(事件) for 事件 in 会话对象.events[状态['cursor']:]]#未发布后缀
        自身.预备池.附着(预留)#标记已附着
        状态['owner']=会话对象#绑定拥有方
        活={'init':已兑现(None),'writes':None}#活控制器
        活['writes']=自身.创建写后(会话对象,lambda:活['init'])#写后依赖init
        if len(后缀)>0:#有未发布后缀
            活['init']=自身.串行化(会话对象.id,lambda:自身.追加核心(会话对象.id,后缀))#串行追加后缀
            活['init'].catch(lambda _错误:None)#失败由flush/拆除观察
        return 活#返回控制器

    def 种子匹配已持久(自身,标识,种子,游标):#种子是否匹配已持久
        """活会话的 seed 是否再现前 cursor 条已持久事件。"""
        if 游标==0:#尚未持久化则匹配
            return True#匹配
        加载=getattr(自身.后端,'loadStored',None) or getattr(自身.后端,'加载已存')#加载已存前缀
        已存=解开(加载(标识))#加载已存前缀
        if 已存 is None:#没有产物则不匹配
            return False#不匹配
        头=已存['meta'] if isinstance(已存,dict) else 取字段(已存,'meta')#头
        事件列表=已存['events'] if isinstance(已存,dict) else 取字段(已存,'events')#事件
        自身.断言已存标识(标识,头)#头必须绑定该id
        return 种子覆盖前缀(种子,快照已存事件(事件列表,标识)[:游标])#种子覆盖前cursor条

    def 已创建时(自身,会话对象,种子):#会话创建处理
        """在 session/created 上：把后端的内存状态同步到一个活 Session。"""
        标识=取字段(会话对象.header,'id')#会话id
        已跟踪=自身.状态表.get(标识)#已跟踪状态
        if 已跟踪 is not None:#情形1：已跟踪
            if 已跟踪.get('owner') is 会话对象:#已是本会话则空操作
                return#空操作
            if 已跟踪.get('owner') is None:#无拥有方状态来自公开create()/load()
                已存工作目录=试取(已跟踪['meta'],'cwd')#已存cwd
                活工作目录=试取(会话对象.header,'cwd')#活cwd
                if 已存工作目录!=活工作目录:#cwd不一致
                    raise Exception('session "'+str(标识)+'" is already persisted at a different cwd (persisted: '+str(已存工作目录)+', live: '+str(活工作目录)+') (id collision)')#碰撞
                if not 解开(自身.种子匹配已持久(标识,种子,已跟踪['cursor'])):#种子对不上已持久前缀
                    raise Exception('session "'+str(标识)+'" is already persisted with '+str(已跟踪['cursor'])+' event(s) that do not match this live session (id collision)')#碰撞
                已跟踪['owner']=会话对象#认领拥有方
                后缀=种子[已跟踪['cursor']:]#种子后缀
                if len(后缀)>0:#有后缀则追加
                    解开(自身.追加核心(标识,后缀))#追加
                return#认领完成
            拥有方活=自身.活表.get(已跟踪['owner'])#当前拥有方的活控制器
            有在途写=拥有方活 is not None and 拥有方活['writes'].有工作#是否有在途写
            if (not 已跟踪['materialized']) and (not 有在途写):#真正废弃：未物化且无在途写
                del 自身.状态表[标识]#回收该id
            else:#仍绑着另一个活会话
                raise Exception('session "'+str(标识)+'" is already bound to a different live session in this backend (id collision)')#碰撞
        加载=getattr(自身.后端,'loadStored',None) or getattr(自身.后端,'加载已存')#磁盘上是否有产物
        已存=解开(加载(标识))#跨存储解析一次id
        if 已存 is not None:#有已存前缀
            解开(自身.收养活前缀(会话对象,种子,已存))#按活前缀收养
            return#收养完成
        头=结构化克隆(会话对象.header)#拷贝头
        解开(自身.创建核心(头))#惰性登记
        已创建=自身.状态表.get(标识)#刚登记的状态
        if 已创建 is not None:#绑定拥有方
            已创建['owner']=会话对象#绑定拥有方
        if len(种子)>0:#有种子则追加
            解开(自身.追加核心(标识,种子))#追加

    def 收养活前缀(自身,会话对象,种子,已存):#收养活前缀
        """把一份已存前缀收养为活会话的历史（HMR/重载）。"""
        头=已存['meta'] if isinstance(已存,dict) else 取字段(已存,'meta')#头
        事件列表=已存['events'] if isinstance(已存,dict) else 取字段(已存,'events')#事件
        撕裂=已存.get('tornMarker') if isinstance(已存,dict) else getattr(已存,'tornMarker',None)#撕裂标记
        自身.断言已存标识(取字段(会话对象.header,'id'),头)#头必须绑定该id
        if 试取(头,'cwd')!=试取(会话对象.header,'cwd'):#cwd不一致
            raise Exception('session "'+str(取字段(会话对象.header,'id'))+'" is already persisted at a different cwd (persisted: '+str(试取(头,'cwd'))+', live: '+str(试取(会话对象.header,'cwd'))+') (id collision)')#碰撞
        自身.断言版本(头)#格式版本必须认识
        已存事件=快照已存事件(事件列表,取字段(会话对象.header,'id'))#升级并快照
        自身.断言事件受支持(头,已存事件)#拒绝未知必填类型
        if not 种子覆盖前缀(种子,已存事件):#种子盖不住已存前缀
            raise Exception('session "'+str(取字段(会话对象.header,'id'))+'" already has a persisted log on disk that does not match this live session (id collision)')#碰撞
        if 撕裂 is not None:#只截断修复
            提交修复=getattr(自身.后端,'commitRepair',None) or getattr(自身.后端,'提交修复')#截断撕裂尾巴
            解开(提交修复(头,撕裂,[]))#截断撕裂尾巴
        自身.状态表[取字段(会话对象.header,'id')]={'meta':结构化克隆(头),'cursor':len(已存事件),'materialized':True,'owner':会话对象}#绑定已物化状态
        后缀=种子[len(已存事件):]#活种子超出已存前缀的部分
        if len(后缀)>0:#有后缀则追加
            解开(自身.追加核心(取字段(会话对象.header,'id'),后缀))#追加

    def 冲洗(自身,会话对象):#刷耐久
        """排空写后到静止。"""
        活=自身.取或建活控制器(会话对象)#取得活控制器
        活['writes'].取消自动等待()#取消自动批窗
        try:#等待初始化
            解开(活['init'])#等onCreated/附着完成
        except BaseException as 错误:#初始化失败
            活['writes'].取消自动等待()#再次取消自动窗
            raise 错误#上抛初始化失败
        return 活['writes'].排空()#排空写后到静止

    def 创建写后(自身,会话对象,就绪):#创建写后控制器
        """围绕初始化与 id 串行化构建一个包私有写控制器。"""
        def 写批次(批次):#耐久一批
            """先等初始化再串行追加活批次。"""
            解开(就绪())#先等初始化
            解开(自身.串行化(取字段(会话对象.header,'id'),lambda:自身.追加活批次(取字段(会话对象.header,'id'),批次)))#串行追加活批次
        def 报告后台失败(错误):#后台失败
            """警告并保留缓冲。"""
            自身.上下文.logger.warn(自身.后端名()+': background write for session "'+str(会话对象.id)+'" failed (buffered events retained): '+str(错误))#警告并保留缓冲
        return 会话写后({'maxDelayMs':自身.写批最大延迟毫秒,'write':写批次,'reportBackgroundFailure':报告后台失败})#写后选项

    def 追加活批次(自身,标识,批次):#追加活批次
        """在过滤掉初始化已经存过的事件之后，追加一份控制器拥有的前缀。"""
        状态=自身.状态表.get(标识)#当前状态
        游标=0 if 状态 is None else 状态['cursor']#已存长度
        新鲜=[事件 for 事件 in 批次 if 取字段(事件,'seq')>=游标]#丢掉初始化已存过的
        解开(自身.追加核心(标识,新鲜))#追加新鲜前缀
