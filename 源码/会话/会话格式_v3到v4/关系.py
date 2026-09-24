"""强制的原生 V4 关系；不完整尾部保留其开放事务。"""
import json,re#重试键与未启动标识后缀
from ..会话格式 import 会话格式错误,是否会话格式json对象,会话格式计数#从会话格式导入

表面类型=frozenset(['system/message','user/message','developer/message','assistant/message','tool/result'])#表面类型
步骤事件类型=frozenset(['system/message','developer/message','assistant/attempt'])#步骤事件类型
关系类型=frozenset([#关系事件类型
    *表面类型,*步骤事件类型,'turn/start','turn/end','step/start','step/end',
    'tool/call','request/header','request/context','tool/ptc-dispatch-start','tool/ptc-dispatch',
    'llm/retry','llm/retry-started','session/title','session/title-llm-request','command/run',
    'command/done','compaction/start','compaction/summary','compaction/end','compaction/prune','session/end-seed',
])#关系类型结束
十进制序号=re.compile(r'0|[1-9]\d*',re.ASCII)#十进制安全整数字符串
安全整数上限=9007199254740991#外来JSON安全整数上限
未启动文本='The tool call was interrupted before the Harness recorded it as started. Retry it if it is still needed.'#未启动修复文本

def 记录(值,主语):#记录对象
    """要求值为对象。"""
    if not 是否会话格式json对象(值):#须对象
        raise 会话格式错误(主语+' requires an object')#错误
    return 值#返回

def 文本(值,主语):#非空字符串
    """要求非空字符串。"""
    if not isinstance(值,str) or len(值)==0:#非法
        raise 会话格式错误(主语+' requires a nonempty string')#错误
    return 值#返回

def 数组(值,主语):#数组
    """要求值为数组。"""
    if not isinstance(值,list):#须数组
        raise 会话格式错误(主语+' requires an array')#错误
    return 值#返回

def 更早(值,序号,主语):#更早序号
    """要求引用更早事件。"""
    坐标=会话格式计数(值,主语)#计数
    if 坐标>=序号:#须更早
        raise 会话格式错误(主语+' must name an earlier event')#错误
    return 坐标#返回

class 关系状态:#关系状态
    """一份原生产物的生命周期状态；各次读取互不保留。"""
    def __init__(自身,产物,已知事件类型):#构造
        """记下产物并预计算被结束种子切断的压缩。"""
        自身.产物=产物#产物
        自身.已知事件类型=已知事件类型#已知类型
        自身.回合=None#开放回合
        自身.步骤=None#开放步骤
        自身.下一回合=1#下一回合
        自身.下一步骤=1#下一步骤
        自身.提供方=None#当前provider
        自身.表面=[]#表面序号
        自身.受保护头=None#受保护系统头
        自身.压缩=None#开放压缩
        自身.工具={}#待结算工具
        自身.分发={}#PTC分发
        自身.重试=[]#已调度重试
        自身.已启动重试=set()#已启动重试键
        自身.命令=set()#命令标识
        自身.孤儿压缩=set()#被结束种子切断的压缩起点
        起点=None#开放压缩起点
        for 事件 in 产物['events']:#预扫描
            if 事件['type'] not in 已知事件类型:#未知跳过
                continue#继续
            if 事件['type']=='compaction/start':#压缩开始
                起点=事件['seq']#记下
            if 事件['type']=='compaction/end':#压缩结束
                起点=None#关闭
            if 事件['type']=='session/end-seed':#结束种子切断
                if 起点 is not None:#有开放压缩
                    自身.孤儿压缩.add(起点)#记孤儿
                起点=None#关闭

    def 要求回合(自身,类型):#要求开放回合
        """当前须有开放回合。"""
        if 自身.回合 is None:#无回合
            raise 会话格式错误(类型+' is outside an open turn')#错误

    def 要求步骤(自身,事件,数据):#要求开放步骤
        """事件须匹配当前开放回合与步骤。"""
        if 自身.回合 is None or 自身.步骤 is None or 数据.get('turn')!=自身.回合 or 数据.get('step')!=自身.步骤:#不符
            raise 会话格式错误(事件['type']+' does not match an open turn and step')#错误

    def 关闭工具(自身,类型):#关闭未结算工具
        """步骤或回合结束时不得留下未结算工具调用。"""
        if len(自身.工具)!=0:#还有未结算
            raise 会话格式错误(类型+' leaves unresolved tool call '+str(next(iter(自身.工具))))#错误
        自身.工具.clear()#清空

    def 开发者(自身,事件,数据):#开发者关系
        """校验 tool-addition 指向先前请求头中恰好一条完整工具定义。"""
        if 'headerSeq' not in 数据:#无头引用
            return#返回
        头序号=更早(数据['headerSeq'],事件['seq'],'developer/message headerSeq')#头序号
        头事件=自身.产物['events'][头序号] if 头序号<len(自身.产物['events']) else None#头事件
        if 头事件 is None or 头事件.get('type')!='request/header':#须请求头
            raise 会话格式错误('developer/message headerSeq must reference an earlier request/header')#错误
        if 头事件['type'] not in 自身.已知事件类型:#须已知
            raise 会话格式错误('developer/message headerSeq must reference a known request/header')#错误
        工具列表=记录(记录(头事件.get('data'),'request/header data').get('header'),'request header').get('tools')#工具定义
        内容=数组(记录(数据.get('message'),'developer message').get('content'),'developer content')#内容
        for 值 in 内容:#逐块
            if not 是否会话格式json对象(值) or 值.get('type')!='tool-addition':#非追加
                continue#继续
            工具名=值.get('toolName')#工具名
            定义列表=[工具 for 工具 in 工具列表 if 是否会话格式json对象(工具) and 工具.get('name')==工具名] if isinstance(工具列表,list) else []#匹配定义
            if len(定义列表)!=1:#须恰好一条
                raise 会话格式错误('developer/message tool-addition "'+str(工具名)+'" must name exactly one tool in headerSeq '+str(头序号))#错误
            定义=定义列表[0]#定义
            if not isinstance(定义.get('description'),str) or not 是否会话格式json对象(定义.get('parameters')):#须完整
                raise 会话格式错误('developer/message tool-addition "'+str(工具名)+'" requires a complete tool definition in headerSeq '+str(头序号))#错误

    def 折叠表面(自身,事件):#折叠表面
        """按 append/replace 维护当前表面。"""
        if 事件['type'] not in 表面类型:#非表面
            return#返回
        if 事件['type']=='system/message' and len(自身.表面)>0 and 自身.受保护头 is None:#需受保护头
            raise 会话格式错误('system/message requires a protected first surface head')#错误
        if 事件.get('surfaceOp')=='append':#追加
            if 事件['type']=='system/message' and len(自身.表面)==0:#首次系统头
                自身.受保护头=事件['seq']#记头
            自身.表面.append(事件['seq'])#追加
            return#返回
        操作=记录(事件.get('surfaceOp'),事件['type']+' surfaceOp')#替换操作
        起序号=更早(操作.get('startSeq'),事件['seq'],'replacement start')#起点序号
        止序号=更早(操作.get('endSeq'),事件['seq'],'replacement end')#终点序号
        起=自身.表面.index(起序号) if 起序号 in 自身.表面 else -1#起点下标
        止=自身.表面.index(止序号) if 止序号 in 自身.表面 else -1#终点下标
        if 起<0 or 止<起:#范围不在当前表面
            raise 会话格式错误(事件['type']+' replacement range is not on the current surface')#错误
        移除=自身.表面[起:止+1]#被替换节点
        溯源=数组(事件.get('sourceEventSeqs'),'replacement sourceEventSeqs')#溯源
        if any(序号 not in 溯源 for 序号 in 移除):#须覆盖全部遮蔽节点
            raise 会话格式错误('replacement sourceEventSeqs omit a shadowed surface node')#错误
        if 自身.受保护头 is not None and 自身.受保护头 in 移除:#触及受保护头
            if 事件['type']!='system/message' or len(移除)!=1:#须恰好系统头
                raise 会话格式错误('surface replacement cannot shadow the protected system head')#错误
            自身.受保护头=事件['seq']#更新头
        自身.表面[起:止+1]=[事件['seq']]#替换为当前

    def 工具(自身,事件,数据):#工具生命周期
        """校验 tool-call / tool/result 与已公布调用的对应。"""
        if 事件['type']=='tool/result' and 事件.get('surfaceOp')!='append':#替换结果只要求回合
            自身.要求回合(事件['type'])#要求回合
            return#返回
        自身.要求步骤(事件,数据)#要求步骤
        if 事件['type']=='assistant/message':#助手公布调用
            消息=记录(数据.get('message'),'assistant message')#消息
            for 值 in 数组(消息.get('content'),'assistant content'):#内容
                块=记录(值,'assistant content block')#块
                if 块.get('type')!='tool-call':#非调用
                    continue#继续
                标识=文本(块.get('id'),'tool call id')#调用标识
                if 标识 in 自身.工具:#重复
                    raise 会话格式错误('assistant/message repeats advertised tool call '+标识)#错误
                自身.工具[标识]={'name':块.get('name'),'arguments':块.get('arguments'),'started':False}#登记
            return#返回
        消息=记录(数据.get('message'),'tool result message') if 事件['type']=='tool/result' else None#结果消息
        标识=文本(数据.get('callId') if 消息 is None else 消息.get('toolCallId'),'tool call id')#调用标识
        待定=自身.工具.get(标识)#待结算
        if 待定 is None:#未公布
            raise 会话格式错误(事件['type']+' '+标识+' has no advertised tool lifecycle')#错误
        if 消息 is None:#tool/call
            if 待定['started'] or 待定['name']!=数据.get('name') or 待定['arguments']!=数据.get('arguments'):#须匹配未启动
                raise 会话格式错误('tool/call '+标识+' does not match one advertised tool call')#错误
            待定['started']=True#已启动
        else:#tool/result
            if (not 待定['started']) and (not 未启动修复(事件,数据,消息,标识)):#须已启动或规范修复
                raise 会话格式错误('tool/result '+标识+' is not the exact TOOL_NOT_STARTED repair')#错误
            del 自身.工具[标识]#结算

    def 派发(自身,事件,数据):#PTC派发
        """校验 PTC 分发起止与根/父调用标识。"""
        自身.要求回合(事件['type'])#要求回合
        标识=文本(数据.get('subCallId'),'PTC subCallId')#子调用
        根=文本(数据.get('rootCallId'),'PTC rootCallId')#根调用
        父=文本(数据.get('parentCallId'),'PTC parentCallId')#父调用
        已有=自身.分发.get(标识)#已有分发
        if 已有 is not None and 已有['data'].get('rootCallId')!=根:#根不得变
            raise 会话格式错误('PTC dispatch changes its rootCallId')#错误
        if 父!=根:#父须属同一根
            父项=自身.分发.get(父)#父分发
            if 父项 is None or 父项['data'].get('rootCallId')!=根:#不符
                raise 会话格式错误('PTC parentCallId does not belong to rootCallId')#错误
        if 事件['type']=='tool/ptc-dispatch-start':#开始
            if 已有 is not None:#重复
                raise 会话格式错误('PTC dispatch repeats subCallId')#错误
            自身.分发[标识]={'data':数据,'settled':False}#登记
            return#返回
        if 已有 is None or 已有['settled']:#无唯一开始
            raise 会话格式错误('PTC dispatch has no unique start')#错误
        for 键 in ('rootCallId','parentCallId','name','arguments'):#须与开始一致
            if 已有['data'].get(键)!=数据.get(键):#不符
                raise 会话格式错误('PTC dispatch does not match its start')#错误
        已有['settled']=True#已结算

    def 重试关系(自身,事件,数据):#llm重试
        """校验调度与已启动重试的坐标与序号。"""
        标识=文本(数据.get('retryId'),'retryId')#重试标识
        次数=会话格式计数(数据.get('retry'),'retry')#次数
        if 事件['type']=='llm/retry-started':#已启动
            已调度=None#匹配项
            for 项 in 自身.重试:#找先前调度
                if 项.get('retryId')==标识 and 项.get('retry')==次数:#匹配
                    已调度=项#记下
                    break#找到
            if 已调度 is None:#无调度
                raise 会话格式错误('llm/retry-started pairs no prior scheduled attempt')#错误
            if 已调度.get('turn')!=数据.get('turn') or 已调度.get('step')!=数据.get('step'):#坐标变了
                raise 会话格式错误('llm/retry-started changes scheduled coordinates')#错误
            键=json.dumps([标识,次数],ensure_ascii=False,separators=(',',':'),allow_nan=False)#键
            if 键 in 自身.已启动重试:#重复
                raise 会话格式错误('llm/retry-started repeats one scheduled attempt')#错误
            自身.已启动重试.add(键)#记入
            return#返回
        if 自身.回合 is None or 数据.get('turn')!=自身.回合 or 数据.get('step')!=(自身.步骤 if 自身.步骤 is not None else 自身.下一步骤-1):#坐标
            raise 会话格式错误('llm/retry does not match the current turn and step')#错误
        if 数据.get('provider')!=自身.提供方:#提供方
            raise 会话格式错误('llm/retry provider does not match the open request/header')#错误
        先前=None#同策略链上一项
        for 项 in reversed(自身.重试):#从后找
            if all(项.get(键)==数据.get(键) for 键 in ('turn','step','provider','policyKey')):#同链
                先前=项#记下
                break#找到
        期望=1 if 先前 is None else 会话格式计数(先前.get('retry'),'prior retry')+1#期望次数
        if 次数!=期望:#跳号
            raise 会话格式错误('llm/retry skips its policy attempt sequence')#错误
        if (先前 is None and any(项.get('retryId')==标识 for 项 in 自身.重试)) or (先前 is not None and 先前.get('retryId')!=标识):#retryId须稳定
            raise 会话格式错误('llm/retry must keep one retryId per policy chain')#错误
        自身.重试.append(数据)#登记

    def 压缩关系(自身,事件,数据):#压缩关系
        """校验压缩起止、摘要与遮蔽跨度。"""
        if 事件['type']=='compaction/prune' or 事件['type']=='compaction/summary':#遮蔽
            自身.跨度(事件,数据)#跨度
        if 事件['type']=='compaction/prune':#裁剪至此
            return#返回
        if 事件['type']=='compaction/start':#开始
            if 自身.压缩 is not None:#重叠
                raise 会话格式错误('compaction/start overlaps an open compaction')#错误
            所有者=None if ('turn' in 数据 and 数据['turn'] is None) else 会话格式计数(数据.get('turn'),'compaction turn')#所有者回合
            if 所有者!=自身.回合:#须匹配开放回合
                raise 会话格式错误('compaction/start does not match the open turn')#错误
            自身.压缩={'id':文本(数据.get('compactionId'),'compactionId'),'command':数据.get('sourceCommandId'),
                'turn':所有者,'seq':事件['seq'],'summarized':False}#开放
            return#返回
        当前=自身.压缩所有者(数据,事件['type'])#当前压缩
        if 当前['turn']!=自身.回合:#须匹配开放回合
            raise 会话格式错误(事件['type']+' does not match the open turn')#错误
        if 事件['type']=='compaction/summary':#摘要
            if 当前['summarized']:#重复
                raise 会话格式错误('compaction/summary repeats')#错误
            当前['summarized']=True#已摘要
        else:#结束
            if 数据.get('turn')!=当前['turn']:#所有者变了
                raise 会话格式错误('compaction/end changes its owner turn')#错误
            if 'error' not in 数据 and not 当前['summarized']:#成功结束须摘要
                raise 会话格式错误('successful compaction/end requires one summary')#错误
            自身.压缩=None#关闭

    def 压缩所有者(自身,数据,主语):#压缩所有者
        """要求存在匹配的 compaction/start。"""
        if 自身.压缩 is None or 自身.压缩['id']!=数据.get('compactionId') or 自身.压缩['command']!=数据.get('sourceCommandId'):#不匹配
            raise 会话格式错误(主语+' has no matching compaction/start')#错误
        return 自身.压缩#返回

    def 跨度(自身,事件,数据):#压缩遮蔽跨度
        """遮蔽序号须恰好为当前表面一段。"""
        范围=记录(数据.get('shadowedRange'),'compaction shadowedRange')#范围
        起序号=更早(范围.get('start'),事件['seq'],'compaction range start')#起点序号
        止序号=更早(范围.get('end'),事件['seq'],'compaction range end')#终点序号
        起=自身.表面.index(起序号) if 起序号 in 自身.表面 else -1#起点下标
        止=自身.表面.index(止序号) if 止序号 in 自身.表面 else -1#终点下标
        序号列表=数组(数据.get('shadowedSeqs'),'compaction shadowedSeqs')#遮蔽序号
        if 起<0 or 止<起 or 自身.表面[起:止+1]!=序号列表:#须恰好一段
            raise 会话格式错误(事件['type']+' shadowedSeqs do not name an exact current surface span')#错误
        if 自身.受保护头 is not None and 自身.受保护头 in 序号列表:#不得遮蔽头
            raise 会话格式错误('compaction cannot shadow the protected system head')#错误

    def 接纳(自身,事件):#接纳事件
        """按类型折叠生命周期事实。"""
        if 事件['type'] not in 自身.已知事件类型 or 事件['type'] not in 关系类型:#不解释
            return#返回
        数据=记录(事件.get('data'),事件['type'])#载荷
        if 事件['type'] in 步骤事件类型:#步骤事件
            自身.要求步骤(事件,数据)#要求步骤
        if 事件['type'].startswith('turn/') and 自身.压缩 is not None and 自身.压缩['seq'] not in 自身.孤儿压缩:#跨开放压缩
            raise 会话格式错误(事件['type']+' crosses an open compaction')#错误
        自身.折叠表面(事件)#表面
        类型=事件['type']#类型
        if 类型=='turn/start':#回合开始
            if 自身.回合 is not None or 数据.get('turn')!=自身.下一回合:#须打开期望回合
                raise 会话格式错误('turn/start does not open the expected turn')#错误
            自身.回合=自身.下一回合#打开
            自身.下一步骤=1#重置步骤
            自身.工具.clear()#清空工具
        elif 类型=='turn/end':#回合结束
            if 自身.回合 is None or 数据.get('turn')!=自身.回合 or 自身.步骤 is not None:#须匹配且无开放步骤
                raise 会话格式错误('turn/end does not match the open turn with no open step')#错误
            自身.关闭工具(类型)#关闭工具
            自身.回合=None#关闭
            自身.下一回合+=1#推进
        elif 类型=='step/start':#步骤开始
            if 自身.回合 is None or 数据.get('turn')!=自身.回合 or 自身.步骤 is not None or 数据.get('step')!=自身.下一步骤:#须匹配
                raise 会话格式错误('step/start does not match the open turn and next step')#错误
            自身.步骤=自身.下一步骤#打开
        elif 类型=='step/end':#步骤结束
            自身.要求步骤(事件,数据)#要求步骤
            自身.关闭工具(类型)#关闭工具
            自身.步骤=None#关闭
            自身.下一步骤+=1#推进
        elif 类型 in ('assistant/message','tool/call','tool/result'):#工具
            自身.工具(事件,数据)#工具
        elif 类型=='developer/message':#开发者
            自身.开发者(事件,数据)#开发者
        elif 类型=='request/header':#请求头
            自身.要求回合(类型)#要求回合
            自身.提供方=记录(记录(数据.get('header'),'request header').get('config'),'request config').get('provider')#提供方
        elif 类型=='request/context':#请求上下文
            自身.要求回合(类型)#要求回合
        elif 类型 in ('tool/ptc-dispatch-start','tool/ptc-dispatch'):#PTC
            自身.派发(事件,数据)#派发
        elif 类型 in ('llm/retry','llm/retry-started'):#重试
            自身.重试关系(事件,数据)#重试
        elif 类型 in ('session/title','session/title-llm-request'):#标题
            标题来源(自身.产物['events'],事件,数据,自身.已知事件类型)#标题来源
        elif 类型=='command/run':#命令运行
            标识=文本(数据.get('commandId'),'commandId')#命令标识
            if 标识 in 自身.命令:#重复
                raise 会话格式错误('command/run repeats commandId '+标识)#错误
            自身.命令.add(标识)#记入
        elif 类型=='command/done':#命令完成
            if 文本(数据.get('commandId'),'commandId') not in 自身.命令:#无先运行
                raise 会话格式错误('command/done has no prior command/run')#错误
            if 'sourceEventSeq' in 数据:#有源序号
                源序号=更早(数据['sourceEventSeq'],事件['seq'],'command sourceEventSeq')#源序号
                源=自身.产物['events'][源序号] if 源序号<len(自身.产物['events']) else None#源事件
                if 数据.get('kind')!='success' or (源 is not None and 源.get('type') in ('command/run','command/done')):#非法源
                    raise 会话格式错误('command/done has invalid sourceEventSeq')#错误
        elif 类型 in ('compaction/start','compaction/summary','compaction/end','compaction/prune'):#压缩
            自身.压缩关系(事件,数据)#压缩
        elif 类型=='user/message':#用户消息
            来源=记录(数据.get('source'),'user message source')#来源
            if 事件.get('surfaceOp')!='append' and 来源.get('kind')=='compact-checkpoint':#压缩检查点
                自身.压缩所有者(来源,'compaction checkpoint')#所有者
        elif 类型=='session/end-seed':#结束种子
            自身.压缩=None#关闭压缩

def 未启动修复(事件,数据,消息,调用标识):#未启动修复
    """识别规范的 TOOL_NOT_STARTED 修复。"""
    错误=记录(数据.get('error'),'not-started error')#错误
    if 错误.get('name')!='ToolNotStartedError' or 错误.get('code')!='TOOL_NOT_STARTED' or 消息.get('isError') is not True or 'sourceEventSeqs' in 事件:#非该修复
        return False#否
    标识=文本(消息.get('id'),'not-started message id')#消息标识
    if 标识.startswith('forked-tool-result-'+调用标识+'-'):#分叉身份由断言v4分叉结果检查
        return True#是
    前缀='interrupted-tool-result-'+调用标识+'-'#前缀
    后缀=标识[len(前缀):]#后缀
    内容=数组(消息.get('content'),'not-started content')#内容
    块=内容[0] if len(内容)>0 else None#首块
    匹配=十进制序号.fullmatch(后缀)#十进制
    return (标识.startswith(前缀) and 匹配 is not None and abs(int(后缀))<=安全整数上限
        and len(内容)==1 and 是否会话格式json对象(块) and 块.get('type')=='text'
        and 块.get('text')==未启动文本)#规范修复

def 标题来源(事件列表,事件,数据,已知事件类型):#标题来源
    """标题消息序号须引用更早的人类 user/message。"""
    引用=数组(数据.get('messageSeqs'),'title messageSeqs')#引用
    if 事件['type']=='session/title' and (len(引用)==0)!=(记录(数据.get('source'),'title source').get('kind')=='user'):#用户标题须空引用
        raise 会话格式错误('session/title messageSeqs must be empty exactly for a user title')#错误
    已见=set()#已见序号
    for 值 in 引用:#逐项
        序号=更早(值,事件['seq'],'title messageSeqs')#序号
        源=事件列表[序号] if 序号<len(事件列表) else None#源事件
        if (序号 in 已见 or 源 is None or 源.get('type')!='user/message' or 源['type'] not in 已知事件类型
            or 记录(记录(源.get('data'),'title input').get('source'),'title input source').get('kind')!='user'):#须互异更早人类消息
            raise 会话格式错误(事件['type']+' messageSeqs must cite distinct earlier human user/message events')#错误
        已见.add(序号)#记入
    if 事件['type']!='session/title-llm-request':#非llm请求
        return#返回
    消息列表=数组(数据.get('messages'),'title messages')#消息
    消息=记录(消息列表[0] if len(消息列表)>0 else None,'title message')#首条
    内容=数组(消息.get('content'),'title content')#内容
    块=内容[0] if len(内容)>0 else None#首块
    if (len(引用)==0 or len(消息列表)!=1 or 消息.get('role')!='user'
        or 记录(消息.get('source'),'title source').get('kind')!='dsh-session-title-llm'
        or len(内容)!=1 or not 是否会话格式json对象(块) or 块.get('type')!='text'):#须表示messageSeqs
        raise 会话格式错误('session/title-llm-request messages do not represent messageSeqs')#错误

def 断言v4生命周期关系(产物,已知事件类型):#断言v4生命周期关系
    """校验原生 V4 生命周期与归属事实，不改写任何事件。"""
    状态=关系状态(产物,已知事件类型)#状态
    for 事件 in 产物['events']:#逐事件
        状态.接纳(事件)#接纳
