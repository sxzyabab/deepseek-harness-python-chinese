import json,math,threading#JSON相等、安全整数、后台串行
from threading import Lock as 锁#每会话互斥
from ...依赖 import cordis#外部依赖胶水
聚合错误=cordis.聚合错误#后端拆除失败聚合
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
from .预备 import (#本包预备池与并发/中止原语
    会话预备池,#预备池
    观察排队取消,#带取消观察共享任务
    操作任务,#单次操作任务
    持久化错误,#包异常基类
    若已中止则抛出,#已中止则抛
    已中止,#是否已中止
)#从预备导入
from .写后 import 会话写后#写后控制器
from .句柄 import 会话句柄,会话已有写主错误,会话持久化未找到错误#句柄与所有权错误

默认预备会话缓存大小=5#默认预备缓存大小
默认写批最大延迟毫秒=200#默认写批延迟毫秒
写批延迟上限毫秒=定时器延迟上限毫秒#写批延迟上限
安全整数上限=9007199254740991#Number.MAX_SAFE_INTEGER

持久化协调器选项字段=('preparedSessionCacheSize','writeBatchMaxDelayMs')#具体持久化后端供给协调器的策略字段
已存前缀字段=('meta','inheritedEventCount','events','eventState','revision','tornMarker')#已存会话头、继承切点、有效连续事件前缀、别名状态、带源限定修订与可选撕裂尾巴标记
已存后缀字段=('meta','inheritedEventCount','events','eventState')#已存会话头外加处于或越过所请求 seq 的事件（可寻址后缀读返回形态）
持久化后端字段=('name','loadStored','readStoredRevision','loadStoredFrom','appendBatch','commitRepair','list','locate','close')#协调器与具体后端之间的最小耐久原语约定（含可选钩子）
会话状态字段=('meta','cursor','materialized','owner','inheritedEventCount')#协调器内存记账持有的每会话写入状态
活会话状态字段=('init','writes')#一个活会话的初始化与有界写后控制器
预备会话源字段=('inspection','session','revision','sessionLength','tornMarker','closers')#已校验冷源以及从它建成的精确未发布 Session

def 外来安全整数(值):
    """外来 JSON 入口的安全整数校验，排除布尔。"""
    if isinstance(值,bool):#布尔不是整数
        return False#布尔不是安全整数
    if isinstance(值,int):#整数
        return abs(值)<=安全整数上限#在安全范围内
    if isinstance(值,float):#浮点
        if not math.isfinite(值) or 值!=int(值):#非有限或非整
            return False#不是安全整数
        return abs(值)<=安全整数上限#在安全范围内
    return False#其它类型

def 冻结视图(元,事件列表,继承事件数=0,事件状态='detached'):#冻结逻辑视图
    """返回不可变检查视图字典，含继承切点与别名状态。"""
    return {'meta':元,'inheritedEventCount':继承事件数,'events':事件列表,'eventState':事件状态}#头、继承、事件与状态

class 会话持久化损坏错误(持久化错误):#持久化损坏错误
    """后端读取成功后，耐久会话内容未通过校验。"""
    def __init__(自身,消息,原因=None):#构造损坏错误
        """记下稳定损坏上下文与原始校验失败。"""
        if 原因 is not None:#有cause
            super().__init__(消息)#消息
            自身.__cause__=原因#挂cause
        else:#无cause
            super().__init__(消息)#消息
        自身.name='SessionPersistenceCorruptionError'#固定错误名

class 会话格式不支持错误(持久化错误):#格式不支持错误
    """已存日志完好，但本运行时无法忠实解释。"""
    def __init__(自身,消息,位置=None):#构造拒绝错误
        """记下无法解释原因与可选产物位置。"""
        super().__init__(消息)#消息
        自身.name='SessionFormatUnsupportedError'#固定错误名
        自身.位置=位置#产物位置

def 会话格式版本拒绝文案(标识,版本):#格式版本拒绝文案
    """本构建不读取的已存会话格式版本的、带方向的拒绝文案。"""
    if 版本>会话格式版本:#比本构建新
        return '会话 "'+str(标识)+'" 使用日志格式 v'+str(版本)+'，但本 harness 只读取 v'+str(会话格式版本)+'：日志由更新的 harness 写出 — 请升级 harness 再打开'#更新的harness写出
    return '会话 "'+str(标识)+'" 使用日志格式 v'+str(版本)+'，比受支持的 v'+str(会话格式版本)+' 更旧，且本构建没有升级路径'#更旧且无升级路径

def 结算错误列表(任务列表):#收集已拒绝原因
    """从一组任务收集拒绝原因（不抛）。"""
    错误列表=[]#拒绝原因
    for 项 in 任务列表:#遍历
        try:#等结算
            项.等待()#成败都等
        except BaseException as 原因:#拒绝
            错误列表.append(原因)#记下拒绝
    return 错误列表#返回原因列表

def 种子覆盖前缀(种子,前缀):#种子是否覆盖前缀
    """活会话种子是否精确再现一份已持久前缀。"""
    if len(前缀)>len(种子):#前缀长于种子
        return False#不覆盖
    下标=0#前缀下标
    for 事件 in 前缀:#每条前缀事件
        种子事件=种子[下标]#对应种子事件
        if 种子事件 is None:#不存在
            return False#不覆盖
        if json.dumps(种子事件,ensure_ascii=False,separators=(',',':'),allow_nan=False,sort_keys=True)!=json.dumps(事件,ensure_ascii=False,separators=(',',':'),allow_nan=False,sort_keys=True):#JSON不等
            return False#不覆盖
        下标+=1#下一条
    return True#全部相等

def 断言受支持事件(事件列表,标识):#断言事件受支持
    """拒绝本构建无法回放的过时 v0 词汇事件。"""
    遗留类型='request/header-delta'#遗留头增量类型
    for 事件 in 事件列表:#找遗留头增量
        if 事件['type']==遗留类型:#有遗留头增量
            raise 持久化错误('会话 "'+str(标识)+'" 在 seq '+str(事件['seq'])+' 含有已不支持的旧版 request/header-delta 事件')#拒绝
    遗留模式类型='mode/set'#遗留模式类型
    for 事件 in 事件列表:#找遗留模式
        if 事件['type']==遗留模式类型:#有遗留模式
            raise 持久化错误('会话 "'+str(标识)+'" 在 seq '+str(事件['seq'])+' 含有已不支持的旧版 mode/set 事件')#拒绝
    for 事件 in 事件列表:#找遗留fallback原因
        if 事件['type']=='request/header':#请求头
            数据=(事件['data'] if 'data' in 事件 else None)#载荷
            if isinstance(数据,dict) and 数据.get('reason')=='fallback':#原因是fallback
                raise 持久化错误('会话 "'+str(标识)+'" 在 seq '+str(事件['seq'])+' 含有已不支持的旧版 request/header 原因 "fallback"')#拒绝

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
    操作=当作记录(事件['surfaceOp'] if 'surfaceOp' in 事件 else None)#表面操作记录
    if 操作 is not None and 操作.get('op')=='replace' and isinstance(操作.get('startSeq'),(int,float)):#是replace且startSeq是数字
        return 操作['startSeq']#返回起点
    return None#否则没有

def 需要遗留前缀(事件):#是否需要遗留前缀
    """一条后缀事件是否需要只能从前面已存前缀得到的事实。"""
    数据=当作记录((事件['data'] if 'data' in 事件 else None))#事件载荷记录
    遗留转向类型='steering/message'#遗留转向类型
    if 事件['type']==遗留转向类型:#转向事件总需要前缀
        return True#需要
    if 数据 is None:#无记录则不需要
        return False#不需要
    类型=事件['type']#事件类型
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
    if 事件['type']!=遗留类型:#不是转向则原样
        return 事件#原样
    数据=当作记录((事件['data'] if 'data' in 事件 else None))#载荷记录
    if 数据 is None:#不是记录
        raise 持久化错误('会话 "'+str(标识)+'" 在 seq '+str(事件['seq'])+' 含有畸形的 react 循环前 steering/message')#畸形拒绝
    包装=当作记录(数据.get('message'))#已包装消息
    if 包装 is not None and 外来安全整数(数据.get('turn')) and 仅有键(数据,['turn','message']):#已有message包装
        升级=dict(事件)#拷贝信封
        升级['type']='user/message'#改为用户消息
        升级['data']=包装#拆包成用户消息
        return 升级#升级结果
    if (not 外来安全整数(数据.get('turn'))) or (not 仅有键(数据,['turn','content','source'])):#旧信封畸形
        raise 持久化错误('会话 "'+str(标识)+'" 在 seq '+str(事件['seq'])+' 含有畸形的 react 循环前 steering/message')#畸形拒绝
    消息={键:值 for 键,值 in 数据.items() if 键!='turn'}#去掉turn留下消息字段
    消息['id']=遗留消息标识(标识,事件['seq'])#补遗留id
    消息['role']='user'#角色
    升级=dict(事件)#拷贝信封
    升级['type']='user/message'#改为用户消息
    升级['data']=消息#当前载荷
    return 升级#升级结果

def 迁移遗留回合开始事件(事件,标识):#迁移遗留回合开始
    """在核实完整旧回合开始信封后去掉过时的 trigger。"""
    if 事件['type']!='turn/start':#不是回合开始
        return 事件#原样
    数据=当作记录((事件['data'] if 'data' in 事件 else None))#载荷记录
    if 数据 is None or 'trigger' not in 数据:#无trigger则已是当前形态
        return 事件#原样
    触发=当作记录(数据.get('trigger'))#trigger记录
    轮次=数据.get('turn')#turn
    if (not 外来安全整数(轮次)) or 轮次<1 or (not 仅有键(数据,['turn','trigger'])) or 触发 is None or not isinstance(触发.get('kind'),str) or len(触发['kind'])==0:#畸形
        raise 持久化错误('会话 "'+str(标识)+'" 在 seq '+str(事件['seq'])+' 含有畸形的 react 循环前 turn/start')#畸形拒绝
    升级=dict(事件)#拷贝信封
    升级['data']={'turn':轮次}#只保留turn
    return 升级#升级结果

def 迁移遗留回合结束事件(事件,标识):#迁移遗留回合结束
    """升级过时的回合结束，同时保留最新主线信封。"""
    if 事件['type']!='turn/end':#不是回合结束
        return 事件#原样
    数据=当作记录((事件['data'] if 'data' in 事件 else None))#载荷记录
    if 数据 is None:#非记录则原样
        return 事件#原样
    def 畸形():#畸形拒绝
        """抛出畸形拒绝。"""
        raise 持久化错误('会话 "'+str(标识)+'" 在 seq '+str(事件['seq'])+' 含有畸形的 react 循环前 turn/end')#抛出
    原因=当作记录(数据.get('reason'))#原因记录
    轮次=数据.get('turn')#turn
    if (not 外来安全整数(轮次)) or 轮次<1 or (not 仅有键(数据,['turn','reason'])) or 原因 is None or not isinstance(原因.get('kind'),str):#reason畸形
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
        if (not 外来安全整数(步骤)) or 步骤<0:#step非法
            return 畸形()#拒绝
        失败=当作记录(原因.get('failure'))#failure记录
        if 失败 is not None and 仅有键(原因,['kind','step','failure']) and 仅有键(失败,['message','code'],['status','providerRetryAfterMs','requestId']) and isinstance(失败.get('message'),str) and isinstance(失败.get('code'),str) and ('status' not in 失败 or isinstance(失败['status'],(int,float))) and ('providerRetryAfterMs' not in 失败 or isinstance(失败['providerRetryAfterMs'],(int,float))) and ('requestId' not in 失败 or isinstance(失败['requestId'],str)):#带failure的旧形态
            当前原因={'kind':'error','error':失败}#升到error字段
        else:#message形态
            消息键=['kind','step','message'] if 'code' not in 原因 else ['kind','step','message','code']#按有无code选键
            if (not 仅有键(原因,消息键)) or (not isinstance(原因.get('message'),str)) or ('code' in 原因 and not isinstance(原因['code'],str)):#键不对
                return 畸形()#拒绝
            当前原因={'kind':'error','error':{'message':原因['message'],'code':原因['code'] if isinstance(原因.get('code'),str) else 'UNKNOWN'}}#升到error对象
    else:#未知种类
        return 事件#原样留给校验
    新数据=dict(数据)#其余字段
    新数据['reason']=当前原因#升级后的原因
    升级=dict(事件)#拷贝信封
    升级['data']=新数据#写回载荷
    return 升级#升级结果

def 迁移遗留消息事件(事件,标识,消息标识表):#迁移遗留消息事件
    """把一条身份出现前的消息事件升级成当前包装形态。"""
    数据=当作记录((事件['data'] if 'data' in 事件 else None))#载荷记录
    if 数据 is None:#非记录则原样
        return 事件#原样
    类型=事件['type']#事件类型
    if 类型=='user/message':#用户消息
        if ('id' in 数据) or ('role' in 数据) or ('message' in 数据) or ('content' not in 数据) or ('source' not in 数据):#不是旧形态
            return 事件#原样
        新数据=dict(数据)#旧content/source
        新数据['id']=遗留消息标识(标识,事件['seq'])#遗留id
        新数据['role']='user'#角色
        升级=dict(事件)#拷贝信封
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
        其余['message']={'id':遗留消息标识(标识,事件['seq']),'role':'assistant','content':内容,'source':来源}#包装消息
        升级=dict(事件)#拷贝信封
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
        消息标识值=遗留消息标识(标识,事件['seq']) if 继承起点 is None else 消息标识表.get(继承起点)#自铸或继承
        其余['message']={'id':消息标识值,'role':'user','content':[{'type':'tool-result','toolCallId':调用标识,'content':内容,'isError':是否错误}],'source':{'kind':'tool','callId':调用标识}}#包装消息
        升级=dict(事件)#拷贝信封
        升级['data']=其余#当前载荷
        return 升级#升级结果
    return 事件#其余类型原样

def 事件消息标识(事件):#取消息id
    """读取一条已校验当前事件所携带的已标识消息。"""
    数据=当作记录((事件['data'] if 'data' in 事件 else None))#载荷记录
    if 事件['type']=='user/message':#用户消息在顶层
        消息=数据#顶层即消息
    else:#其余在message
        消息=当作记录(None if 数据 is None else 数据.get('message'))#内嵌消息
    if 消息 is not None and isinstance(消息.get('id'),str):#字符串id才算
        return 消息['id']#消息id
    return None#无消息id

def 快照已存事件(事件列表,标识):#快照已存事件
    """把已存事件物化为已升级、已校验、消息不可变的快照。"""
    断言受支持事件(事件列表,标识)#先拒绝无法回放的遗留
    消息标识表={}#seq到消息id
    结果=[]#快照列表
    for 事件 in 事件列表:#逐条升级并快照
        已升开始=迁移遗留回合开始事件(事件,标识)#升级回合开始
        已升回合=迁移遗留回合结束事件(已升开始,标识)#升级回合结束
        已升转向=迁移遗留转向事件(已升回合,标识)#升级转向
        快照=快照会话事件(迁移遗留消息事件(已升转向,标识,消息标识表))#升级消息并快照
        消息标识值=事件消息标识(快照)#取出消息id
        if 消息标识值 is not None:#有消息id
            消息标识表[快照['seq']]=消息标识值#记下供后续继承
        结果.append(快照)#返回快照
    return 结果#快照列表

def 收养已存事件(事件列表,标识):#收养已存事件
    """升级并校验一份独占拥有的后端结果，不复制它。"""
    断言受支持事件(事件列表,标识)#先拒绝无法回放的遗留
    消息标识表={}#seq到消息id
    下标=0#数组下标
    while 下标<len(事件列表):#就地替换
        事件=事件列表[下标]#当前事件
        已升开始=迁移遗留回合开始事件(事件,标识)#升级回合开始
        已升回合=迁移遗留回合结束事件(已升开始,标识)#升级回合结束
        已升转向=迁移遗留转向事件(已升回合,标识)#升级转向
        已收养=收养会话事件(迁移遗留消息事件(已升转向,标识,消息标识表))#升级消息并收养
        事件列表[下标]=已收养#写回数组
        消息标识值=事件消息标识(已收养)#取出消息id
        if 消息标识值 is not None:#有消息id
            消息标识表[已收养['seq']]=消息标识值#记下供后续继承
        下标+=1#下一条
    return 事件列表#返回同一数组

class 持久化协调器:#持久化协调器
    """拥有与后端无关的会话写路径编排。后端构造一个，实现持久化后端约定，并把其写/读服务方法委托给对应的协调器方法。"""
    def __init__(自身,上下文,后端,选项=None):#构造协调器
        """安装写路径监听器、每会话退役，以及后端拆除 effect。"""
        if 选项 is None:#缺省选项
            选项={}#空选项
        预备缓存=选项['preparedSessionCacheSize'] if 'preparedSessionCacheSize' in 选项 else 默认预备会话缓存大小#预备缓存大小
        写批延迟=选项['writeBatchMaxDelayMs'] if 'writeBatchMaxDelayMs' in 选项 else 默认写批最大延迟毫秒#写批最大延迟
        if (not 外来安全整数(预备缓存)) or 预备缓存<1:#预备缓存非法
            raise TypeError('preparedSessionCacheSize 必须是正安全整数')#拒绝
        if (not 外来安全整数(写批延迟)) or 写批延迟<1 or 写批延迟>写批延迟上限毫秒:#写批延迟非法
            raise TypeError('writeBatchMaxDelayMs 必须是 1 到 '+str(写批延迟上限毫秒)+' 之间的整数')#拒绝
        自身.上下文=上下文#插件上下文
        自身.后端=后端#具体后端
        自身.写批最大延迟毫秒=写批延迟#记下延迟
        自身.状态表={}#id到会话状态
        自身.活表={}#活会话控制器
        自身.退役表={}#退役任务
        自身.锁表={}#每id互斥锁
        自身.表锁=锁()#保护锁表与进行中集合
        自身.进行中=set()#在途操作任务
        自身.活写句柄表={}#id到可入队活写的打开写句柄
        自身.预备池=会话预备池(预备缓存)#建预备池
        自身.安装写路径()#安装写路径

    def 后端名(自身):#人类可读后端名
        """人类可读的后端名，用于拆除失败的聚合错误。"""
        return 自身.后端.name#后端契约名

    def 创建(自身,头):#创建会话意图
        """登记分离的会话元数据，供第一次追加时惰性创建。"""
        快照=快照json值(头)#无损快照头
        if 快照 is None:#无法JSON序列化
            raise TypeError('会话元数据必须能无损 JSON 序列化')#拒绝
        if (not 外来安全整数(快照['createdAt'])) or 快照['createdAt']<0:#创建时刻非法
            raise TypeError('会话元数据 createdAt 必须是非负安全整数')#拒绝
        def 后台创建():
            """串行创建核心。"""
            return 自身.创建核心(快照)#惰性登记
        return 自身.串行化(快照['id'],后台创建).等待()#串行创建

    def 创建核心(自身,头):#创建核心
        """纯惰性：只记录意图。直到第一次追加才有产物。"""
        标识=头['id']#会话id
        if 标识 in 自身.状态表 or 自身.预备池.有(标识):#内存已有
            raise 持久化错误('会话 "'+str(标识)+'" 在本后端已存在')#拒绝重复
        if 自身.后端.loadStored(标识) is not None:#磁盘已有日志
            raise 持久化错误('会话 "'+str(标识)+'" 磁盘上已有持久化日志；请 load/resume 而不是创建')#应load/resume
        自身.状态表[标识]={'meta':头,'cursor':0,'materialized':False,'inheritedEventCount':0}#记下未物化状态

    def 追加(自身,标识,事件列表):#追加事件
        """耐久持久化一批事件。遵守只追加与连续 seq 约定。"""
        批次=快照json值(事件列表)#无损快照批次
        if 批次 is None:#无法JSON序列化
            raise TypeError('会话事件批次无法无损 JSON 序列化，因其含有无法 JSON 序列化的数据')#拒绝
        def 后台追加():
            """串行追加核心。"""
            return 自身.追加核心(标识,批次)#耐久追加
        return 自身.串行化(标识,后台追加).等待()#串行追加

    def 追加核心(自身,标识,事件列表):#追加核心
        """每条追加路径都汇到这里。"""
        断言受支持事件(事件列表,标识)#拒绝无法回放的遗留
        if len(事件列表)==0:#空批无操作
            return#无事
        自身.预备池.断言可写(标识)#预备占用时不可写
        if 标识 not in 自身.状态表:#未跟踪则从存储收养
            自身.状态表[标识]=自身.收养(标识)#收养
        状态=自身.状态表[标识]#已有状态
        下标=0#批次下标
        for 事件 in 事件列表:#检查每条
            期望=状态['cursor']+下标#期望seq
            if 事件['seq']!=期望:#seq对不上游标
                raise 持久化错误('会话 "'+str(标识)+'" 追加 seq 不匹配：下标 '+str(下标)+' 期望 '+str(期望)+'，实际 '+str(事件['seq']))#拒绝缺口
            下标+=1#下一条
        自身.后端.appendBatch(状态['meta'],事件列表,状态['materialized'])#耐久追加
        状态['materialized']=True#已物化
        状态['cursor']+=len(事件列表)#推进游标
        自身.预备池.使失效(标识)#使该id的预备失效

    def 预备(自身,标识,信号=None):#预备会话
        """预备并预留恢复所用的精确未发布 Session。"""
        while True:#修订重试循环
            自身.等待退役(标识,信号)#先等退役排空
            if 自身.上下文.sessions.get(标识) is not None:#已经活着
                raise 持久化错误('会话 "'+str(标识)+'" 仍在线时不能预备')#活着不能预备
            def 冷加载():#冷加载
                """串行冷加载。"""
                def 后台预备():
                    """串行预备核心。"""
                    return 自身.预备核心(标识)#冷预备
                return 自身.串行化(标识,后台预备).等待()#冷加载
            def 提交修复(源):#提交修复
                """串行提交修复。"""
                def 后台提交():
                    """串行提交已预备。"""
                    return 自身.提交已预备(源)#提交修复
                return 自身.串行化(标识,后台提交,信号).等待()#提交修复
            预留=自身.预备池.预留(标识,冷加载,提交修复,信号)#独占预留
            if 预留 is None:#修订变了则重试
                continue#重试
            if 自身.上下文.sessions.get(标识) is not None:#预留期间变成活的
                自身.预备池.释放(预留,False)#释放预留
                raise 持久化错误('会话 "'+str(标识)+'" 仍在线时不能预备')#活着不能预备
            def 释放回调():#释放时
                """还回预备池。"""
                源=预留['source']#预备源
                状态=预留['state']#会话状态
                活会话=源['session']#未发布会话
                可复用='owner' not in 状态 and len(活会话.events)==源['sessionLength']#无活拥有方且长度未变
                自身.预备池.释放(预留,可复用)#还回预备池
            return 会话准备.创建(预留['source']['session'],{'release':释放回调})#包装预备

    def 加载(自身,标识):#加载会话
        """提交恢复并返回其不可变逻辑视图，不发布。"""
        while True:#修订重试循环
            自身.等待退役(标识)#先等退役
            活着=自身.上下文.sessions.get(标识)#是否已活
            if 活着 is not None:#活的则快照活会话
                return 自身.加载活快照(活着)#返回活快照
            def 冷加载():#冷加载
                """串行冷加载。"""
                def 后台预备():
                    """串行预备核心。"""
                    return 自身.预备核心(标识)#冷预备
                return 自身.串行化(标识,后台预备).等待()#冷加载
            def 提交修复(源):#提交修复
                """串行提交修复。"""
                def 后台提交():
                    """串行提交已预备。"""
                    return 自身.提交已预备(源)#提交修复
                return 自身.串行化(标识,后台提交).等待()#提交修复
            预留=自身.预备池.预留(标识,冷加载,提交修复)#独占预留
            if 预留 is None:#修订变了则重试
                continue#重试
            已附着=自身.上下文.sessions.get(标识)#预留期间是否已附着
            if 已附着 is not None:#已活
                自身.预备池.丢弃(预留)#丢掉预留
                return 自身.加载活快照(已附着)#返回活快照
            自身.预备池.丢弃(预留)#检查完丢掉预留
            return 预留['source']['inspection']#返回冷视图

    def 检查(自身,标识,信号=None):#检查会话
        """检查一个逻辑会话，不发布也不提交恢复。"""
        while True:#修订重试循环
            若已中止则抛出(信号)#已取消则抛
            if 标识 in 自身.退役表:#有退役则等待
                自身.等待退役(标识,信号)#等待
            活着=自身.上下文.sessions.get(标识)#是否已活
            if 活着 is not None:#活的则借活视图
                return 自身.检查活会话(活着)#借活视图
            try:#尝试冷检查
                def 冷加载():#冷加载
                    """串行冷加载。"""
                    def 后台预备():
                        """串行预备核心。"""
                        return 自身.预备核心(标识)#冷预备
                    return 自身.串行化(标识,后台预备).等待()#冷加载
                源=自身.预备池.检查(标识,冷加载,信号)#共享观察预备源
                已附着=自身.上下文.sessions.get(标识)#观察期间是否已附着
                if 已附着 is not None:#已活则借活视图
                    return 自身.检查活会话(已附着)#借活视图
                def 后台核对():
                    """串行核对预备源修订。"""
                    return 自身.预备源是否当前(源,信号)#修订是否仍当前
                仍当前=自身.串行化(标识,后台核对,信号).等待()#串行核对修订
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
        if (not 外来安全整数(起始序号)) or 起始序号<0:#fromSeq非法
            raise TypeError('readFrom 的 fromSeq 必须是非负安全整数，实际为 '+str(起始序号))#拒绝
        退役=自身.退役表.get(标识)#可能的退役
        if 退役 is not None:#有退役
            if 信号 is None:#无取消
                退役.等待()#直接等
            else:
                观察排队取消(退役,信号).等待()#带取消
        def 后台读后缀():
            """串行读后缀。"""
            return 自身.从序号读核心(标识,起始序号,信号)#读后缀
        return 自身.串行化(标识,后台读后缀,信号).等待()#串行读后缀

    def 从序号读核心(自身,标识,起始序号,信号=None):#从seq读核心
        """返回头与后缀事件。"""
        若已中止则抛出(信号)#已取消则抛
        if hasattr(自身.后端,'loadStoredFrom'):#后端可寻址
            try:
                后缀=自身.后端.loadStoredFrom(标识,起始序号,信号)#寻址读
            except BaseException as 错误:#读取失败
                if 已中止(信号):#取消优先
                    若已中止则抛出(信号)#取消优先
                raise 错误#其余上抛
            若已中止则抛出(信号)#读后检查取消
            if 后缀 is None:#没有产物
                raise 会话持久化未找到错误(标识)#没有产物
            头=后缀['meta']#头
            事件列表=后缀['events']#事件
            继承=后缀['inheritedEventCount'] if 'inheritedEventCount' in 后缀 else 0#继承切点
            自身.断言已存标识(标识,头)#头必须绑定该id
            自身.断言版本(头)#格式版本必须认识
            if any(需要遗留前缀(事件) for 事件 in 事件列表):#后缀需要更早前缀事实
                整份=自身.读已存前缀(标识,信号)#改读完整前缀
                return {#再切后缀
                    'meta':整份['meta'],#头
                    'inheritedEventCount':整份['inheritedEventCount'],#继承
                    'events':[事件 for 事件 in 整份['events'] if 事件['seq']>=起始序号],#后缀事件
                    'eventState':整份['eventState'],#别名状态
                }#返回
            事件列表=快照已存事件(事件列表,标识)#升级并快照
            自身.断言事件受支持(头,事件列表)#拒绝未知必填类型
            return {'meta':结构化克隆(头),'inheritedEventCount':继承,'events':事件列表,'eventState':'detached'}#分离结果
        整份=自身.读已存前缀(标识,信号)#顺序回退读完整前缀
        return {#切后缀
            'meta':整份['meta'],#头
            'inheritedEventCount':整份['inheritedEventCount'],#继承
            'events':整份['events'][起始序号:],#后缀
            'eventState':整份['eventState'],#别名状态
        }#返回

    def 读已存前缀(自身,标识,信号=None):#读已存前缀
        """读一份分离的物理前缀，不做逻辑恢复或缓存；携带 eventState 与 inheritedEventCount。"""
        若已中止则抛出(信号)#已取消则抛
        已存=自身.后端.loadStored(标识,信号)#加载物理前缀
        若已中止则抛出(信号)#读后检查取消
        if 已存 is None:#没有产物
            raise 会话持久化未找到错误(标识)#没有产物
        头=已存['meta']#头
        事件列表=已存['events']#事件
        继承=已存['inheritedEventCount'] if 'inheritedEventCount' in 已存 else 0#继承切点
        事件状态=已存['eventState'] if 'eventState' in 已存 else 'detached'#后端可直接给出共享冻结
        自身.断言已存标识(标识,头)#头必须绑定该id
        自身.断言版本(头)#格式版本必须认识
        if 事件状态=='shared-frozen':#已共享冻结则就地收养校验
            事件列表=收养已存事件(list(事件列表),标识)#就地收养
        else:#否则快照脱离
            事件列表=快照已存事件(事件列表,标识)#升级并快照
            事件状态='detached'#调用方拥有拷贝
        自身.断言事件受支持(头,事件列表)#拒绝未知必填类型
        return {'meta':结构化克隆(头),'inheritedEventCount':继承,'events':事件列表,'eventState':事件状态}#分离结果

    def 打开(自身,标识,访问,选项=None):#打开句柄
        """打开已存会话并返回写或读句柄。选项为 `{signal}` 或裸取消信号。"""
        if isinstance(选项,dict):#服务定义选项
            信号=选项['signal'] if 'signal' in 选项 else None#可选取消
        else:#裸信号兼容
            信号=选项#信号或 None
        若已中止则抛出(信号)#已取消则抛
        if 访问!='read' and 访问!='write':#非法访问
            raise TypeError('会话访问必须是 "read" 或 "write"')#拒绝
        前缀=自身.读已存前缀(标识,信号)#冷读前缀元数据与事件源
        若已中止则抛出(信号)#读后再检查
        if 访问=='write':#写打开
            状态=自身.状态表.get(标识)#已有状态
            if 状态 is not None and 状态.get('owner') is not None:#已有活拥有方
                raise 会话已有写主错误(标识)#拒绝
            if 标识 not in 自身.状态表:#新建记账
                自身.状态表[标识]={#写入记账
                    'meta':前缀['meta'],#头
                    'cursor':len(前缀['events']),#游标
                    'materialized':True,#已物化
                    'inheritedEventCount':前缀['inheritedEventCount'],#继承
                }#状态
            自身.状态表[标识]['owner']='handle'#声明写主
        持有=自身#协调器
        缓存事件=[前缀['events']]#句柄私有事件缓存（单元素可变槽）
        缓存状态=[前缀['eventState']]#别名状态槽
        def 读回调(偏移,长度,读信号):#句柄读
            """从缓存或存储读切片。"""
            若已中止则抛出(读信号)#取消
            事件列表=缓存事件[0]#当前缓存
            if 访问=='write':#写句柄用缓存（含自身追加）
                切片=事件列表[偏移:偏移+长度]#切片
                return {'eventState':缓存状态[0],'events':切片}#返回
            最新=持有.读已存前缀(标识,读信号)#读句柄再读存储
            缓存事件[0]=最新['events']#刷新缓存
            缓存状态[0]=最新['eventState']#刷新状态
            return {'eventState':最新['eventState'],'events':最新['events'][偏移:偏移+长度]}#切片
        def 追加回调(批次,写信号):#句柄追加
            """经协调器追加并刷新缓存。"""
            若已中止则抛出(写信号)#取消
            持有.追加(标识,批次)#耐久追加
            缓存事件[0]=list(缓存事件[0])+list(批次)#本地可见
            缓存状态[0]='detached'#追加批为脱离拥有
        def 关闭回调():#句柄关闭
            """释放写声明。"""
            if 访问=='write':#写句柄
                状态=持有.状态表.get(标识)#状态
                if 状态 is not None and 状态.get('owner')=='handle':#本句柄声明
                    状态.pop('owner',None)#释放写主
        return 会话句柄(标识,前缀['meta'],访问,前缀['inheritedEventCount'],{#构造句柄
            'read':读回调,#读
            'append':追加回调,#追加
            'close':关闭回调,#关闭
        })#句柄结束

    def 预备核心(自身,标识):#预备核心
        """读取、在内存中修复、校验并经 eventState 移交一份冷源一次（不再使用 seedSource）。"""
        已存=自身.后端.loadStored(标识)#加载物理前缀
        if 已存 is None:#没有产物
            raise 会话持久化未找到错误(标识)#没有产物
        try:#收养并平衡
            头=已存['meta']#头
            事件列表=已存['events']#事件
            继承=已存['inheritedEventCount'] if 'inheritedEventCount' in 已存 else 0#继承切点
            事件状态=已存['eventState'] if 'eventState' in 已存 else 'detached'#别名状态
            修订=已存['revision'] if 'revision' in 已存 else None#修订
            撕裂=已存['tornMarker'] if 'tornMarker' in 已存 else None#撕裂标记
            自身.断言已存标识(标识,头)#头必须绑定该id
            自身.断言版本(头)#格式版本必须认识
            if 事件状态=='shared-frozen':#共享冻结就地收养
                已存事件=收养已存事件(list(事件列表),标识)#就地升级收养
            else:#否则快照脱离
                已存事件=快照已存事件(事件列表,标识)#脱离拷贝
                事件状态='detached'#调用方拥有
            自身.断言事件受支持(头,已存事件)#拒绝未知必填类型
            关闭列表=[收养会话事件(项) for 项 in 中断轮次关闭器(已存事件)]#合成关闭事件
            平衡=list(已存事件)+关闭列表#平衡后的日志
            if len(关闭列表)>0:#合成关闭器使图脱离
                事件状态='detached'#关闭器为新脱离值
            会话服务=自身.上下文.sessions#会话存储
            活会话=会话服务.准备(标识,{#预备未发布会话
                'seed':平衡,#种子
                'meta':头,#头
                'inheritedEventCount':继承,#继承切点
                'eventState':事件状态,#别名状态
            })#prepare结束
            检查视图=冻结视图(活会话.header,tuple(平衡),继承,事件状态)#冻结逻辑视图
            return {'inspection':检查视图,'session':活会话,'revision':修订,'sessionLength':len(活会话.events),'tornMarker':撕裂,'closers':关闭列表}#预备源
        except 会话格式不支持错误:#格式拒绝原样抛
            raise#不加包装
        except BaseException as 错误:#校验失败
            raise 会话持久化损坏错误('已存会话 "'+str(标识)+'" 校验失败: '+str(错误),错误)#其余包成损坏

    def 提交已预备(自身,源):#提交已预备源
        """提交一次已预备修复，并建立其无拥有方的耐久游标。"""
        标识=源['inspection']['meta']['id']#会话id
        游标=len(源['inspection']['events'])#平衡后长度
        已有=自身.状态表.get(标识)#已有状态
        if 已有 is not None and 已有.get('owner') is not None:#已有活拥有方
            raise 持久化错误('会话 "'+str(标识)+'" 已有活持久化拥有方')#不能提交
        if not 自身.预备源是否当前(源):#修订变了则放弃
            return None#放弃
        if (源['tornMarker'] if 'tornMarker' in 源 else None) is not None or len(源['closers'])>0:#需要物理修复
            自身.后端.commitRepair(源['inspection']['meta'],源['tornMarker'] if 'tornMarker' in 源 else None,源['closers'])#耐久修复
            return None#让调用方重试
        状态=已有 if 已有 is not None else {'meta':源['inspection']['meta'],'cursor':游标,'materialized':True}#已有或新建
        状态['meta']=源['inspection']['meta']#更新头
        状态['cursor']=游标#更新游标
        状态['materialized']=True#已物化
        自身.状态表[标识]=状态#写入记账
        return {'source':源,'state':状态}#提交成功

    def 预备源是否当前(自身,源,信号=None):#预备源是否仍当前
        """一份缓存源是否仍点名当前耐久日志修订。"""
        标识=源['inspection']['meta']['id']#会话id
        return 自身.后端.readStoredRevision(标识,信号)==源['revision']#修订相等

    def 加载活快照(自身,活会话):#加载活快照
        """返回一份已经活着的 Session 的耐久不可变视图。"""
        事件列表=活会话.events#活事件数组
        自身.冲洗(活会话).等待()#先刷耐久
        if 活会话.id not in 自身.状态表:#丢状态
            raise 持久化错误('会话 "'+str(活会话.id)+'" 在加载期间丢失了持久化状态')#丢状态
        状态=自身.状态表[活会话.id]#刷后的状态
        if len(事件列表)==0:#空日志当找不到
            raise 持久化错误('会话 "'+str(活会话.id)+'" 未找到')#找不到
        if len(中断轮次关闭器(事件列表))>0:#活回合仍打开
            raise 持久化错误('会话 "'+str(活会话.id)+'" 的活轮次仍打开时不能加载；请用活 Session 或等轮次关闭')#打开回合不能load
        return 冻结视图(状态['meta'],事件列表,getattr(活会话,'inheritedEventCount',0),'shared-frozen')#冻结视图

    def 检查活会话(自身,活会话):#检查活会话
        """从已经活着的 Session 借用一份不可变视图。"""
        return 冻结视图(活会话.header,活会话.events,getattr(活会话,'inheritedEventCount',0),'shared-frozen')#冻结借用视图

    def 等待退役(自身,标识,信号=None):#等待退役
        """带着调用方取消等待一个正在退役的生命周期。"""
        if 标识 not in 自身.退役表:#无退役
            return#已结束
        退役=自身.退役表[标识]#可能的退役任务
        if 信号 is None:#无取消
            退役.等待()#直接等
            return
        观察排队取消(退役,信号).等待()#排队期间可取消

    def 串行化(自身,标识,操作,信号=None):#按id串行化
        """同一会话 id 用锁串行，使写入永不交错。"""
        with 自身.表锁:#取或建互斥
            if 标识 not in 自身.锁表:#尚无
                自身.锁表[标识]=锁()#新建
            会话锁=自身.锁表[标识]#本会话锁
        已开始=[False]#本操作是否已开始
        下一=操作任务()#本操作任务
        with 自身.表锁:#登记在途
            自身.进行中.add(下一)#记下
        def 后台执行():
            """持锁执行本操作；失败原样结算。"""
            try:
                with 会话锁:#串行互斥
                    若已中止则抛出(信号)#开始前检查取消
                    已开始[0]=True#标记已开始
                    结果=操作()#执行操作
                    下一.兑现(结果)#成功
            except BaseException as 错误:#本操作失败
                下一.拒绝(错误)#拒绝
            finally:
                with 自身.表锁:#离途
                    自身.进行中.discard(下一)#摘掉
        threading.Thread(target=后台执行,daemon=True).start()#后台执行本操作
        if 信号 is None:#无取消
            return 下一#返回本操作
        def 已越过截止():
            """本操作是否已开始。"""
            return 已开始[0]#已开始则越过截止
        return 观察排队取消(下一,信号,已越过截止)#带取消观察排队

    def 收养(自身,标识):#从存储收养
        """为已在存储中发现、但尚未在内存中的会话构建状态。"""
        while True:#修订重试
            源=自身.预备池.取走就绪(标识)#就绪源
            if 源 is None:#无就绪
                源=自身.预备核心(标识)#新预备
            已提交=自身.提交已预备(源)#提交修复
            if 已提交 is not None:#成功则返回状态
                return 已提交['state']#返回状态

    def 断言版本(自身,头):#断言格式版本
        """格式版本必须认识（委托存储契约）。"""
        from .存储契约 import 断言版本 as 契约断言版本#延迟导入避环
        位置=自身.后端.locate(头) if hasattr(自身.后端,'locate') else None#位置
        契约断言版本(头,位置)#契约

    def 断言事件受支持(自身,头,事件列表):#断言事件类型受支持
        """拒绝含有本构建不认识的事件类型的日志，除非标为可忽略（委托存储契约词汇门，不重收养）。"""
        from .存储契约 import 校验已存事件#延迟导入避环
        #校验已存事件会就地收养；此处事件可能已快照/收养，再执行一遍保证词汇门与契约一致
        位置=自身.后端.locate(头) if hasattr(自身.后端,'locate') else None#位置
        校验已存事件(头,事件列表,位置)#契约（含未知类型与遗留 fallback）

    def 不支持(自身,头,原因):#构造格式拒绝
        """构造指向原始产物（后端有的话）的格式拒绝。"""
        位置=自身.后端.locate(头) if hasattr(自身.后端,'locate') else None#位置
        if 位置 is None:#无路径
            return 会话格式不支持错误(原因)#格式错误
        路径=位置['path']#绝对路径
        return 会话格式不支持错误(原因+'（原始日志: '+str(路径)+'）',位置)#有路径则附上

    def 断言已存标识(自身,标识,头):#断言已存id
        """拒绝未绑定到所请求会话 id 的后端元数据（委托存储契约）。"""
        from .存储契约 import 断言已存标识 as 契约断言已存标识#延迟导入避环
        契约断言已存标识(标识,头)#契约

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
                    错误列表=结算错误列表([自身.冲洗(活会话) for 活会话 in list(自身.活表.keys())])#收集flush失败
                    while True:#排空在途串行操作
                        with 自身.表锁:#快照在途
                            待等=list(自身.进行中)#拷贝
                        if len(待等)==0:#已空
                            break
                        结算错误列表(待等)#等这批
                    if len(错误列表)>0:#有flush失败
                        raise 聚合错误(错误列表,名+' 拆除失败')#聚合拆除失败
                except BaseException as 错误:#排空失败
                    拆除错误=错误#记下主失败
                    raise#继续抛
                finally:#无论排空成败
                    try:#关闭后端
                        if hasattr(自身.后端,'close'):#有关闭
                            自身.后端.close()#关闭
                    except BaseException as 关闭错误:#关闭失败
                        if 拆除错误 is None:#排空成功则抛关闭错误
                            raise 关闭错误#抛关闭错误
            return 拆除#返回拆除器
        上下文.副作用(装拆除,名+' write path')#effect名
        def 会话已创建(活会话):#会话创建
            """创建时捕获头，并持久化分叉的种子一次。"""
            自身.取或建活控制器(活会话)#启动该会话写路径
        上下文.监听('session/created',会话已创建)#created监听结束
        def 会话事件(活会话,事件):#会话事件
            """有登记活写句柄则入队句柄；否则走写后有界窗口。"""
            句柄=自身.活写句柄表.get(活会话.id)#可入队活写句柄
            if 句柄 is not None and hasattr(句柄,'入队活写'):#接到写句柄
                def 报告后台失败(错误):#后台失败
                    """警告并保留缓冲。"""
                    自身.上下文.日志.警告(自身.后端名()+': 会话 "'+str(活会话.id)+'" 的后台写入失败（已保留缓冲事件）: '+str(错误))#警告
                句柄.入队活写(事件,报告后台失败)#入队句柄
                return#不双写
            活=自身.取或建活控制器(活会话)#取得活控制器
            活['writes'].入队(事件)#入队写后
        上下文.监听('session/event',会话事件)#event监听结束
        def 会话冲洗(活会话):#flush监听
            """调用方把flush当作缓冲写入的立即耐久屏障。"""
            return 自身.冲洗(活会话)#冲洗
        上下文.监听('session/flush',会话冲洗)#flush监听
        def 会话已拆除(活会话):#disposed监听
            """会话拆除只观察，因此退役自己包含失败。"""
            自身.退役(活会话)#退役
        上下文.监听('session/disposed',会话已拆除)#disposed监听
        for 活会话 in 上下文.sessions.list():#播种已有活会话
            自身.取或建活控制器(活会话)#HMR播种

    def 退役(自身,活会话):#退役会话
        """启动并观察一个已拆除会话的最终排空。"""
        if 活会话 not in 自身.活表:#从未初始化则忽略
            return#忽略
        退役任务=操作任务()#退役任务
        def 执行退役():#后台退役
            """执行退役核心。"""
            try:#退役
                自身.退役核心(活会话)#退役核心
                退役任务.兑现(None)#成功
            except BaseException as 错误:#退役失败
                退役任务.拒绝(错误)#拒绝
        自身.退役表[活会话.id]=退役任务#记下退役任务
        def 忘掉():#结算后忘掉
            """结算后忘掉退役任务。"""
            if 自身.退役表.get(活会话.id) is 退役任务:#仍是本任务才删
                del 自身.退役表[活会话.id]#删除
        def 警告失败(错误):#退役失败警告
            """退役失败警告。"""
            忘掉()#忘掉
            自身.上下文.日志.警告(自身.后端名()+': 会话 "'+str(活会话.id)+'" 退役失败: '+str(错误))#警告
        def 观察退役结算():#成败都忘掉
            """成败都忘掉；失败警告。"""
            try:#等退役
                退役任务.等待()#成功
                忘掉()#忘掉
            except BaseException as 错误:
                警告失败(错误)#警告并忘掉
        threading.Thread(target=执行退役,daemon=True).start()#后台退役
        threading.Thread(target=观察退役结算,daemon=True).start()#观察结算

    def 退役核心(自身,活会话):#退役核心
        """排空并释放一个精确已拆除 Session 生命周期拥有的状态。"""
        自身.冲洗(活会话).等待()#先刷耐久
        句柄=自身.活写句柄表.get(活会话.id)#活写句柄
        if 句柄 is not None and hasattr(句柄,'关闭'):#有打开写句柄
            try:#关闭句柄（再排空一次也无害）
                句柄.关闭()#关闭并释锁
            except BaseException:#关闭失败上抛
                raise#上抛
        标识=活会话.header['id']#会话id
        def 释放():#串行释放
            """丢掉活控制器与可选状态。"""
            if 活会话 in 自身.活表:#有活控制器
                del 自身.活表[活会话]#丢掉活控制器
            状态=自身.状态表.get(标识)#当前状态
            if 状态 is not None and 状态.get('owner') is 活会话:#本生命周期拥有则丢掉状态
                del 自身.状态表[标识]#丢掉状态
        return 自身.串行化(标识,释放).等待()#串行释放

    def 取或建活控制器(自身,活会话):#取得或创建活控制器
        """返回一个活会话的那一个生命周期控制器，需要时创建。"""
        已有=自身.活表.get(活会话)#已有控制器
        if 已有 is not None:#复用
            return 已有#复用
        预留=自身.预备池.按会话取预留(活会话)#是否有预备预留
        if 预留 is not None:#从预备附着
            已恢复=自身.附着已预备(活会话,预留)#绑定预备
            自身.活表[活会话]=已恢复#记下控制器
            return 已恢复#返回附着后的控制器
        种子=[结构化克隆(事件) for 事件 in 活会话.events]#拷贝创建时种子
        已完成=操作任务()#占位已完成任务
        已完成.兑现(None)#立刻成功
        活={'init':已完成,'writes':None}#新活控制器占位
        def 取初始化():
            """写后所依赖的初始化任务。"""
            return 活['init']#当前初始化任务
        活['writes']=自身.创建写后(活会话,取初始化)#写后依赖init
        自身.活表[活会话]=活#先挂上以免重入
        def 后台已创建():
            """串行 onCreated。"""
            return 自身.已创建时(活会话,种子)#创建时同步
        活['init']=自身.串行化(活会话.header['id'],后台已创建)#串行onCreated
        return 活#返回新控制器

    def 附着已预备(自身,活会话,预留):#附着已预备会话
        """绑定一份精确已预备 Session，并只持久化其未发布后缀。"""
        源=预留['source']#预备源
        状态=预留['state']#会话状态
        if 源['session'] is not 活会话 or 状态.get('owner') is not None or 状态['cursor']!=len(源['inspection']['events']) or 活会话.firstLiveSeq!=状态['cursor']:#预备与状态不一致
            raise 持久化错误('会话 "'+str(活会话.id)+'" 的预备已不再匹配其持久化状态')#预备与状态不一致
        后缀=[结构化克隆(事件) for 事件 in 活会话.events[状态['cursor']:]]#未发布后缀
        自身.预备池.附着(预留)#标记已附着
        状态['owner']=活会话#绑定拥有方
        已完成=操作任务()#占位已完成任务
        已完成.兑现(None)#立刻成功
        活={'init':已完成,'writes':None}#活控制器
        def 取初始化():
            """写后所依赖的初始化任务。"""
            return 活['init']#当前初始化任务
        活['writes']=自身.创建写后(活会话,取初始化)#写后依赖init
        if len(后缀)>0:#有未发布后缀
            def 后台追加后缀():
                """串行追加未发布后缀。"""
                return 自身.追加核心(活会话.id,后缀)#追加后缀
            活['init']=自身.串行化(活会话.id,后台追加后缀)#串行追加后缀
        return 活#返回控制器

    def 种子匹配已持久(自身,标识,种子,游标):#种子是否匹配已持久
        """活会话的 seed 是否再现前 cursor 条已持久事件。"""
        if 游标==0:#尚未持久化则匹配
            return True#匹配
        已存=自身.后端.loadStored(标识)#加载已存前缀
        if 已存 is None:#没有产物则不匹配
            return False#不匹配
        头=已存['meta']#头
        事件列表=已存['events']#事件
        自身.断言已存标识(标识,头)#头必须绑定该id
        return 种子覆盖前缀(种子,快照已存事件(事件列表,标识)[:游标])#种子覆盖前cursor条

    def 已创建时(自身,活会话,种子):#会话创建处理
        """在 session/created 上：把后端的内存状态同步到一个活 Session。"""
        标识=活会话.header['id']#会话id
        已跟踪=自身.状态表.get(标识)#已跟踪状态
        if 已跟踪 is not None:#情形1：已跟踪
            if 已跟踪.get('owner') is 活会话:#已是本会话则空操作
                return#空操作
            if 'owner' not in 已跟踪:#无拥有方状态来自公开create()/load()
                已存工作目录=已跟踪['meta']['cwd'] if 'cwd' in 已跟踪['meta'] else None#已存cwd
                活工作目录=活会话.header['cwd'] if 'cwd' in 活会话.header else None#活cwd
                if 已存工作目录!=活工作目录:#cwd不一致
                    raise 持久化错误('会话 "'+str(标识)+'" 已在不同 cwd 持久化（已存: '+str(已存工作目录)+'，在线: '+str(活工作目录)+'）（id 碰撞）')#碰撞
                if not 自身.种子匹配已持久(标识,种子,已跟踪['cursor']):#种子对不上已持久前缀
                    raise 持久化错误('会话 "'+str(标识)+'" 已持久化 '+str(已跟踪['cursor'])+' 条事件，且与本次在线会话不匹配（id 碰撞）')#碰撞
                已跟踪['owner']=活会话#认领拥有方
                后缀=种子[已跟踪['cursor']:]#种子后缀
                if len(后缀)>0:#有后缀则追加
                    自身.追加核心(标识,后缀)#追加
                return#认领完成
            拥有方活=自身.活表.get(已跟踪['owner'])#当前拥有方的活控制器
            有在途写=拥有方活 is not None and 拥有方活['writes'].有工作#是否有在途写
            if (not 已跟踪['materialized']) and (not 有在途写):#真正废弃：未物化且无在途写
                del 自身.状态表[标识]#回收该id
            else:#仍绑着另一个活会话
                raise 持久化错误('会话 "'+str(标识)+'" 已绑定到本后端另一个在线会话（id 碰撞）')#碰撞
        已存=自身.后端.loadStored(标识)#跨存储解析一次id
        if 已存 is not None:#有已存前缀
            自身.收养活前缀(活会话,种子,已存)#按活前缀收养
            return#收养完成
        头=结构化克隆(活会话.header)#拷贝头
        自身.创建核心(头)#惰性登记
        已创建=自身.状态表.get(标识)#刚登记的状态
        if 已创建 is not None:#绑定拥有方
            已创建['owner']=活会话#绑定拥有方
        if len(种子)>0:#有种子则追加
            自身.追加核心(标识,种子)#追加

    def 收养活前缀(自身,活会话,种子,已存):#收养活前缀
        """把一份已存前缀收养为活会话的历史（HMR/重载）。"""
        头=已存['meta']#头
        事件列表=已存['events']#事件
        撕裂=已存['tornMarker'] if 'tornMarker' in 已存 else None#撕裂标记
        自身.断言已存标识(活会话.header['id'],头)#头必须绑定该id
        头工作目录=头['cwd'] if 'cwd' in 头 else None#已存cwd
        活工作目录=活会话.header['cwd'] if 'cwd' in 活会话.header else None#活cwd
        if 头工作目录!=活工作目录:#cwd不一致
            raise 持久化错误('会话 "'+str(活会话.header['id'])+'" 已在不同 cwd 持久化（已存: '+str(头工作目录)+'，在线: '+str(活工作目录)+'）（id 碰撞）')#碰撞
        自身.断言版本(头)#格式版本必须认识
        已存事件=快照已存事件(事件列表,活会话.header['id'])#升级并快照
        自身.断言事件受支持(头,已存事件)#拒绝未知必填类型
        if not 种子覆盖前缀(种子,已存事件):#种子盖不住已存前缀
            raise 持久化错误('会话 "'+str(活会话.header['id'])+'" 磁盘上已有持久化日志，且与本次在线会话不匹配（id 碰撞）')#碰撞
        if 撕裂 is not None:#只截断修复
            自身.后端.commitRepair(头,撕裂,[])#截断撕裂尾巴
        自身.状态表[活会话.header['id']]={'meta':结构化克隆(头),'cursor':len(已存事件),'materialized':True,'owner':活会话}#绑定已物化状态
        后缀=种子[len(已存事件):]#活种子超出已存前缀的部分
        if len(后缀)>0:#有后缀则追加
            自身.追加核心(活会话.header['id'],后缀)#追加

    def 登记活写句柄(自身,句柄):#登记可入队活写句柄
        """把 create/open 返回的写句柄接到协调器活写路由。"""
        if getattr(句柄,'access',None)!='write':#非写
            return#忽略
        自身.活写句柄表[句柄.id]=句柄#登记

    def 注销活写句柄(自身,句柄):#注销活写句柄
        """句柄关闭时去掉活写路由。"""
        标识=getattr(句柄,'id',None)#id
        if 标识 is None:#无
            return#忽略
        if 自身.活写句柄表.get(标识) is 句柄:#本句柄
            del 自身.活写句柄表[标识]#删除

    def 冲洗(自身,活会话):#刷耐久
        """排空写后或活写句柄到静止。"""
        句柄=自身.活写句柄表.get(活会话.id)#活写句柄
        if 句柄 is not None and hasattr(句柄,'排空活写'):#接到写句柄
            已完成=操作任务()#任务
            try:#排空并刷
                句柄.排空活写()#排空活缓冲
                if hasattr(句柄,'刷盘'):#有刷盘
                    句柄.刷盘()#刷盘
                已完成.兑现(None)#成功
            except BaseException as 错误:
                已完成.拒绝(错误)#拒绝
            return 已完成#返回任务
        活=自身.取或建活控制器(活会话)#取得活控制器
        活['writes'].取消自动等待()#取消自动批窗
        try:#等待初始化
            活['init'].等待()#等onCreated/附着完成
        except BaseException as 错误:#初始化失败
            活['writes'].取消自动等待()#再次取消自动窗
            raise 错误#上抛初始化失败
        return 活['writes'].排空()#排空写后到静止

    def 创建写后(自身,活会话,就绪):#创建写后控制器
        """围绕初始化与 id 串行化构建一个包私有写控制器。"""
        def 写批次(批次):#耐久一批
            """先等初始化再串行追加活批次。"""
            就绪().等待()#先等初始化
            def 后台追加活():
                """串行追加活批次。"""
                return 自身.追加活批次(活会话.header['id'],批次)#追加活批次
            自身.串行化(活会话.header['id'],后台追加活).等待()#串行追加活批次
        def 报告后台失败(错误):#后台失败
            """警告并保留缓冲。"""
            自身.上下文.日志.警告(自身.后端名()+': 会话 "'+str(活会话.id)+'" 的后台写入失败（已保留缓冲事件）: '+str(错误))#警告并保留缓冲
        return 会话写后({'maxDelayMs':自身.写批最大延迟毫秒,'write':写批次,'reportBackgroundFailure':报告后台失败})#写后选项

    def 追加活批次(自身,标识,批次):#追加活批次
        """在过滤掉初始化已经存过的事件之后，追加一份控制器拥有的前缀。"""
        状态=自身.状态表.get(标识)#当前状态
        游标=0 if 状态 is None else 状态['cursor']#已存长度
        新鲜=[事件 for 事件 in 批次 if 事件['seq']>=游标]#丢掉初始化已存过的
        自身.追加核心(标识,新鲜)#追加新鲜前缀
