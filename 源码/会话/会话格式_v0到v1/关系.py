"""跨事件关系校验：构造一份当代 Session 所需的已发布关系。"""
import json#诊断序列化
from ...工具.值 import 深相等json#深相等JSON
from ..会话格式 import 会话格式错误#格式错误
from .校验辅助 import 已发布v0记录#记录辅助
from .处置 import 已发布v0事件处置表#处置表

表面类型=frozenset(['user/message','assistant/message','tool/result'])#表面类型

def 断言已发布产物关系(产物,扩展=None):#断言已发布产物关系
    """校验跨事件关系，保证可安全构造一份当代 Session。"""
    if 扩展 is None:#默认无扩展
        扩展={}#空扩展
    打开回合=None#打开回合
    打开步骤=None#打开步骤
    打开步骤提供方=None#打开步骤提供方
    下一回合=1#下一回合
    下一步骤=1#下一步骤
    表面=[]#表面序号
    打开压缩=None#打开压缩
    陈旧压缩起点=继承孤儿压缩起点(产物['events'])#陈旧压缩
    重试们=[]#重试事件
    重试起点=set()#重试起点键
    ptc根={}#ptc根
    ptc起点={}#ptc起点
    工具生命周期={}#工具生命周期
    命令运行=set()#命令运行
    步骤事件扩展=扩展.get('stepEvents')#扩展步骤事件
    for 事件 in 产物['events']:#遍历事件
        扩展步骤事件=步骤事件扩展 is not None and 事件['type'] in 步骤事件扩展#扩展步骤
        if 事件['type'] not in 已发布v0事件处置表 and not 扩展步骤事件:#未知且非扩展
            continue#跳过
        数据=已发布v0记录(事件['data'],f'{事件["type"]} {事件["seq"]} data')#data
        if 事件['type'] in 表面类型:#表面
            表面=应用表面(表面,事件)#应用表面
        if (事件['type']=='turn/start' or 事件['type']=='turn/end') and 打开压缩 is not None and 打开压缩['startSeq'] not in 陈旧压缩起点:#跨压缩
            raise 会话格式错误(f'{事件["type"]} crosses an open compaction')#错误
        if 扩展步骤事件:#扩展步骤事件
            要求打开步骤(事件,数据,打开回合,打开步骤)#要求打开步骤
            continue#继续
        类型=事件['type']#类型
        if 类型=='turn/start':#回合开始
            if 打开回合 is not None or 数据['turn']!=下一回合:#不符
                raise 会话格式错误(f'turn/start {json.dumps(数据["turn"],ensure_ascii=False)} does not open expected turn {下一回合}')#错误
            打开回合=数据['turn']#打开
            打开步骤=None#清步骤
            工具生命周期.clear()#清工具
            下一步骤=1#重置步骤
        elif 类型=='turn/end':#回合结束
            if 打开回合!=数据['turn']:#无匹配
                raise 会话格式错误(f'turn/end {json.dumps(数据["turn"],ensure_ascii=False)} has no matching open turn')#错误
            断言无未解决工具(工具生命周期,'turn/end')#无未解决
            if 打开步骤 is not None:#跨步骤
                raise 会话格式错误(f'turn/end {json.dumps(数据["turn"],ensure_ascii=False)} crosses an open step')#错误
            打开回合=None#关闭
            下一回合+=1#下一回合
        elif 类型=='step/start':#步骤开始
            if 打开回合!=数据['turn'] or 打开步骤 is not None or 数据['step']!=下一步骤:#不符
                raise 会话格式错误(f'{事件["type"]} does not match the open turn and next step')#错误
            打开步骤=数据['step']#打开
        elif 类型=='step/end':#步骤结束
            要求打开步骤(事件,数据,打开回合,打开步骤)#要求打开
            断言无未解决工具(工具生命周期,'step/end')#无未解决
            工具生命周期.clear()#清工具
            打开步骤=None#关闭
            下一步骤+=1#下一步骤
        elif 类型=='assistant/chunk':#助手块
            要求打开步骤(事件,数据,打开回合,打开步骤)#要求打开
        elif 类型=='assistant/message':#助手消息
            要求打开步骤(事件,数据,打开回合,打开步骤)#要求打开
            消息=已发布v0记录(数据['message'],f'assistant/message {事件["seq"]} message')#消息
            内容=消息['content']#内容
            for 块 in 内容:#遍历块
                if 块.get('type')!='tool-call':#非工具调用
                    continue#跳过
                调用id=块['id']#id
                if 调用id in 工具生命周期:#重复
                    raise 会话格式错误(f'assistant/message repeats advertised tool call {调用id}')#错误
                工具生命周期[调用id]={#登记
                    'name':块['name'],#名称
                    'arguments':块['arguments'],#参数
                    'state':'advertised',#状态
                }#登记结束
        elif 类型=='tool/call':#工具调用
            要求打开步骤(事件,数据,打开回合,打开步骤)#要求打开
            调用id=数据['callId']#callId
            生命周期=工具生命周期.get(调用id)#生命周期
            if 生命周期 is None or 生命周期['state']!='advertised' or 生命周期['name']!=数据['name'] or 生命周期['arguments']!=数据['arguments']:#不符
                raise 会话格式错误(f'tool/call {调用id} does not match one advertised tool call')#错误
            生命周期['state']='started'#已开始
        elif 类型=='tool/result':#工具结果
            if 事件.get('surfaceOp')=='append':#追加
                要求打开步骤(事件,数据,打开回合,打开步骤)#要求打开
                消息=已发布v0记录(数据['message'],f'tool/result {事件["seq"]} message')#消息
                源=已发布v0记录(消息['source'],f'tool/result {事件["seq"]} source')#源
                调用id=源['callId']#callId
                内容=消息['content']#内容
                错误=None if 'error' not in 数据 else 已发布v0记录(数据['error'],f'tool/result {事件["seq"]} error')#错误
                生命周期=工具生命周期.get(调用id)#生命周期
                if 生命周期 is None:#无生命周期
                    raise 会话格式错误(f'tool/result {调用id} has no advertised tool lifecycle')#错误
                if 生命周期['state']=='advertised' and not 是精确工具未开始修复(事件,内容,错误):#非精确修复
                    raise 会话格式错误(f'tool/result {调用id} is not the exact TOOL_NOT_STARTED repair')#错误
                del 工具生命周期[调用id]#删除
            elif 打开回合 is None:#替换在回合外
                raise 会话格式错误('tool/result replacement is outside an open turn')#错误
        elif 类型=='request/header':#请求头
            if 打开回合 is None:#回合外
                raise 会话格式错误(f'{事件["type"]} is outside an open turn')#错误
            打开步骤提供方=数据['header']['config']['provider']#提供方
        elif 类型=='request/context':#请求上下文
            if 打开回合 is None:#回合外
                raise 会话格式错误(f'{事件["type"]} is outside an open turn')#错误
        elif 类型=='tool/code-dispatch-start' or 类型=='tool/code-dispatch':#代码分发
            if 打开回合 is None:#回合外
                raise 会话格式错误(f'{事件["type"]} is outside an open turn')#错误
            根=数据['rootCallId']#根
            父=数据['parentCallId']#父
            子=数据['subCallId']#子
            已知=ptc根.get(子)#已知根
            if 已知 is not None and 已知!=根:#改根
                raise 会话格式错误(f'{事件["type"]} changes its rootCallId')#错误
            if 父!=根 and ptc根.get(父)!=根:#父不属于根
                raise 会话格式错误(f'{事件["type"]} parentCallId does not belong to rootCallId')#错误
            if 类型=='tool/code-dispatch-start':#开始
                if 子 in ptc起点:#重复
                    raise 会话格式错误('tool/code-dispatch-start repeats subCallId')#错误
                ptc起点[子]={#登记
                    'root':根,#根
                    'parent':父,#父
                    'name':数据['name'],#名称
                    'arguments':数据['arguments'],#参数
                    'settled':False,#未结算
                }#登记结束
            else:#结算
                起点=ptc起点.get(子)#起点
                if 起点 is None or 起点['settled']:#无唯一起点
                    raise 会话格式错误('tool/code-dispatch has no unique start')#错误
                if 起点['root']!=根 or 起点['parent']!=父 or 起点['name']!=数据['name'] or not 深相等json(起点['arguments'],数据['arguments']):#不符
                    raise 会话格式错误('tool/code-dispatch does not match its start')#错误
                起点['settled']=True#已结算
            ptc根[子]=根#记根
        elif 类型=='llm/retry':#LLM重试
            要求打开步骤(事件,数据,打开回合,打开步骤)#要求打开
            if 数据['provider']!=打开步骤提供方:#提供方不符
                raise 会话格式错误('llm/retry provider does not match the open request/header')#错误
            断言重试链(重试们,数据)#断言链
            重试们.append(事件)#推入
        elif 类型=='llm/retry-started':#LLM重试已开始
            已排=None#已排
            for 候选 in 重试们:#查找
                先前=候选['data']#先前数据
                if 先前['retryId']==数据['retryId'] and 先前['retry']==数据['retry']:#匹配
                    已排=候选#记下
                    break#找到
            if 已排 is None:#无配对
                raise 会话格式错误('llm/retry-started pairs no prior scheduled attempt')#错误
            先前=已排['data']#先前数据
            if 先前['turn']!=数据['turn'] or 先前['step']!=数据['step']:#坐标不符
                raise 会话格式错误('llm/retry-started does not match its scheduled turn and step')#错误
            键=f'{json.dumps(数据["retryId"],ensure_ascii=False)}\0{json.dumps(数据["retry"],ensure_ascii=False)}'#键
            if 键 in 重试起点:#重复
                raise 会话格式错误('llm/retry-started repeats one scheduled attempt')#错误
            重试起点.add(键)#记入
        elif 类型=='session/title' or 类型=='session/title-llm-request':#标题
            断言标题出处(#断言标题
                产物['events'],#事件
                事件,#当前
                数据,#数据
                扩展.get('preservedSourceTitleRequestText') is not True,#校验框定文本
            )#断言结束
        elif 类型=='command/run':#命令运行
            标识=数据['commandId']#id
            if 标识 in 命令运行:#重复
                raise 会话格式错误(f'command/run repeats commandId {标识}')#错误
            命令运行.add(标识)#记入
        elif 类型=='command/done':#命令完成
            标识=数据['commandId']#id
            if 标识 not in 命令运行:#无先验
                raise 会话格式错误(f'command/done {标识} has no prior command/run')#错误
            if 'sourceEventSeq' in 数据:#有出处序号
                源序号=数据['sourceEventSeq']#序号
                if isinstance(源序号,int) and 0<=源序号<len(产物['events']):#在范围内
                    源=产物['events'][源序号]#源事件
                    源类型=源.get('type')#源类型
                else:#越界或非整数
                    源类型=None#无类型
                if 数据['kind']!='success' or 源类型=='command/run' or 源类型=='command/done':#非法
                    raise 会话格式错误(f'command/done {标识} has invalid sourceEventSeq')#错误
        elif 类型=='session-log-deepseek/delivery-accepted':#投递已接受
            接受版本=数据.get('sessionFormatVersion')#接受版本
            if 接受版本 is None:#缺省为0
                接受版本=0#默认0
            if 接受版本==产物['header']['version']:#当代代际
                继承=('parentSession' in 产物['header']) and 事件['seq']<产物['inheritedEventCount']#继承段
                if not 继承 and 数据.get('sessionId')!=产物['header']['id']:#错会话
                    raise 会话格式错误('current-generation delivery marker names the wrong Session')#错误
        elif 类型=='compaction/start':#压缩开始
            if 打开压缩 is not None:#重叠
                raise 会话格式错误('compaction/start overlaps an open compaction')#错误
            断言压缩回合(数据['turn'],打开回合,'compaction/start')#断言回合
            打开压缩={#打开
                'id':数据['compactionId'],#id
                'turn':数据['turn'],#回合
                'startSeq':事件['seq'],#起点
                'summarized':False,#未摘要
            }#打开结束
            if 'sourceCommandId' in 数据:#有源命令
                打开压缩['sourceCommandId']=数据['sourceCommandId']#源命令
        elif 类型=='compaction/summary':#压缩摘要
            断言压缩所有者(打开压缩,数据,'compaction/summary')#所有者
            断言压缩回合(打开压缩['turn'] if 打开压缩 is not None else None,打开回合,'compaction/summary')#回合
            if 打开压缩 is not None and 打开压缩.get('summarized') is True:#重复
                raise 会话格式错误('compaction/summary repeats')#错误
            断言当前表面跨度(表面,数据,'compaction/summary')#表面跨度
            打开压缩={**(打开压缩 or {}),'summarized':True}#标记摘要
        elif 类型=='compaction/end':#压缩结束
            断言压缩所有者(打开压缩,数据,'compaction/end')#所有者
            if 打开压缩 is not None and 数据['turn']!=打开压缩['turn']:#改回合
                raise 会话格式错误('compaction/end changes its owner turn')#错误
            断言压缩回合(打开压缩['turn'] if 打开压缩 is not None else None,打开回合,'compaction/end')#回合
            if 'error' not in 数据 and (打开压缩 is None or 打开压缩.get('summarized') is not True):#缺摘要
                raise 会话格式错误('successful compaction/end requires one summary')#错误
            打开压缩=None#关闭
        elif 类型=='compaction/prune':#压缩裁剪
            断言当前表面跨度(表面,数据,'compaction/prune')#表面跨度
        elif 类型=='user/message':#用户消息
            源=已发布v0记录(数据['source'],f'user/message {事件["seq"]} source')#源
            if 事件.get('surfaceOp')!='append' and 源.get('kind')=='plugin' and 源.get('plugin')=='compact':#压缩检查点
                断言压缩所有者(打开压缩,源,f'compaction checkpoint at seq {事件["seq"]}')#所有者
        elif 类型=='session/end-seed':#会话结束种子
            打开压缩=None#结束源生命周期

def 继承孤儿压缩起点(事件们):#继承孤儿压缩起点
    """收集被 session/end-seed 截断的压缩起点。"""
    陈旧=set()#陈旧
    打开=None#打开序号
    for 事件 in 事件们:#遍历
        if 事件['type']=='compaction/start':#开始
            打开=事件['seq']#记下
        elif 事件['type']=='compaction/end':#结束
            打开=None#关闭
        elif 事件['type']=='session/end-seed':#结束种子
            if 打开 is not None:#有打开
                陈旧.add(打开)#陈旧
            打开=None#关闭
    return 陈旧#返回

def 断言重试链(重试们,数据):#断言重试链
    """校验同策略链上的重试序号与 retryId。"""
    先前=None#先前
    for 候选 in reversed(重试们):#逆序找
        值=候选['data']#数据
        if 值['turn']==数据['turn'] and 值['step']==数据['step'] and 值['provider']==数据['provider'] and 值['policyKey']==数据['policyKey']:#同链
            先前=候选#记下
            break#找到
    期望=((先前['data']['retry'] if 先前 is not None else 0)+1)#期望retry
    if 数据['retry']!=期望:#不符
        raise 会话格式错误(f'llm/retry must use retry {期望}')#错误
    if 先前 is not None and 先前['data']['retryId']!=数据['retryId']:#retryId变了
        raise 会话格式错误('llm/retry must preserve retryId across one policy chain')#错误
    if 先前 is None:#新链
        for 候选 in 重试们:#查复用
            if 候选['data']['retryId']==数据['retryId']:#复用
                raise 会话格式错误(f'llm/retry reuses retryId {json.dumps(数据["retryId"],ensure_ascii=False)} across policy chains')#错误

def 要求打开步骤(事件,数据,打开回合,打开步骤):#要求打开步骤
    """要求事件落在打开的回合与步骤内。"""
    if 数据['turn']!=打开回合 or 数据['step']!=打开步骤 or 打开回合 is None or 打开步骤 is None:#不符
        raise 会话格式错误(f'{事件["type"]} does not match an open turn and step')#错误

def 断言无未解决工具(生命周期们,边界):#断言无未解决工具
    """边界处不得留下未解决工具调用。"""
    未解决=next(iter(生命周期们.keys()),None)#首个未解决
    if 未解决 is not None:#有未解决
        raise 会话格式错误(f'{边界} leaves unresolved tool call {未解决}')#错误

def 是精确工具未开始修复(事件,内容,错误):#是精确工具未开始修复
    """判定是否为精确 TOOL_NOT_STARTED 修复。"""
    数据=事件['data']#数据
    消息=数据['message']#消息
    源=消息['source']#源
    调用id=源['callId']#callId
    块=内容[0] if len(内容)>0 else None#首块
    修复内容=块.get('content') if isinstance(块,dict) else None#修复内容
    return (#全部精确匹配
        isinstance(错误,dict)
        and 错误.get('name')=='ToolNotStartedError'
        and 错误.get('code')=='TOOL_NOT_STARTED'
        and 'sourceEventSeqs' not in 事件
        and 消息.get('id')==f'interrupted-tool-result-{调用id}-{事件["seq"]}'
        and 块 is not None
        and 块.get('isError') is True
        and isinstance(修复内容,list)
        and len(修复内容)==1
        and 修复内容[0].get('type')=='text'
        and 修复内容[0].get('text')
            =='The tool call was interrupted before the Harness recorded it as started. Retry it if it is still needed.'
    )#判定结束

def 应用表面(表面,事件):#应用表面
    """按 surfaceOp 更新当前表面序号列表。"""
    操作=事件.get('surfaceOp')#表面操作
    if 操作 is None:#缺标记
        raise 会话格式错误(f'{事件["type"]} requires a surfaceOp marker')#错误
    if 操作=='append':#追加
        return [*表面,事件['seq']]#追加
    起点=表面.index(操作['start']) if 操作['start'] in 表面 else -1#起点
    终点=表面.index(操作['end']) if 操作['end'] in 表面 else -1#终点
    if 起点<0 or 终点<起点:#非法范围
        raise 会话格式错误(f'{事件["type"]} replacement range is not on the current surface')#错误
    被遮=表面[起点:终点+1]#被遮序号
    出处源=事件.get('sourceEventSeqs')#出处
    出处集=set(出处源) if isinstance(出处源,list) else set()#出处集
    for 序号 in 被遮:#检查出处
        if 序号 not in 出处集:#遗漏
            raise 会话格式错误(f'{事件["type"]} replacement sourceEventSeqs omit a shadowed surface node')#错误
    return [*表面[:起点],事件['seq'],*表面[终点+1:]]#替换

def 断言标题出处(事件们,事件,数据,校验框定文本):#断言标题出处
    """校验标题事件对人类用户消息的引用。"""
    序号们=数据['messageSeqs']#消息序号
    if 事件['type']=='session/title':#会话标题
        标题源=已发布v0记录(数据['source'],f'session/title {事件["seq"]} source')#标题源
        if (len(序号们)==0)!=(标题源.get('kind')=='user'):#空性不符
            raise 会话格式错误(f'session/title {事件["seq"]} messageSeqs must be empty exactly for a user title')#错误
    已选=[]#已选
    for 序号 in 序号们:#遍历序号
        源=事件们[序号] if isinstance(序号,int) and 0<=序号<len(事件们) else None#源事件
        if 源 is None or 源.get('type')!='user/message':#非用户消息
            raise 会话格式错误(f'{事件["type"]} {事件["seq"]} messageSeqs must cite earlier human user/message events')#错误
        源数据=已发布v0记录(源['data'],f'{源["type"]} {序号} data')#源数据
        出处=已发布v0记录(源数据['source'],f'{源["type"]} {序号} source')#出处
        if 出处.get('kind')!='user':#非人类
            raise 会话格式错误(f'{事件["type"]} {事件["seq"]} messageSeqs must cite earlier human user/message events')#错误
        内容=源数据['content']#内容
        文本='\n'.join([块['text'] for 块 in 内容 if 块.get('type')=='text' and isinstance(块.get('text'),str)])#拼接文本
        已选.append({'seq':序号,'text':文本})#推入
    if 事件['type']=='session/title-llm-request':#标题LLM请求
        消息们=数据['messages']#消息
        期望='Generate the session title from this JSON array of human messages:\n'+json.dumps(已选,ensure_ascii=False,separators=(',',':'))#期望
        #TS JSON.stringify 对对象默认无空格；Python ensure separators
        消息=消息们[0] if isinstance(消息们,list) and len(消息们)>0 else None#首消息
        内容=消息.get('content') if isinstance(消息,dict) else None#内容
        源=已发布v0记录(消息['source'],'session/title-llm-request message source') if isinstance(消息,dict) else None#源
        if (not isinstance(消息们,list)) or len(消息们)!=1 or (消息 is None) or 消息.get('role')!='user' or (not isinstance(内容,list)) or len(内容)!=1 or 源 is None or 源.get('kind')!='plugin' or 源.get('plugin')!='dsh-session-title-llm':#不符
            raise 会话格式错误('session/title-llm-request messages do not represent messageSeqs')#错误
        框定=内容[0]#框定块
        if 框定 is None or 框定.get('type')!='text' or (校验框定文本 and 框定.get('text')!=期望):#文本不符
            raise 会话格式错误('session/title-llm-request messages do not represent messageSeqs')#错误

def 断言压缩所有者(打开,数据,类型):#断言压缩所有者
    """压缩事件必须匹配打开的 compaction/start。"""
    if 打开 is None or 数据.get('compactionId')!=打开.get('id') or 数据.get('sourceCommandId')!=打开.get('sourceCommandId'):#不符
        raise 会话格式错误(f'{类型} has no matching compaction/start')#错误

def 断言压缩回合(所有者,打开回合,类型):#断言压缩回合
    """压缩所有者回合必须匹配打开回合。"""
    if (打开回合 is not None) if 所有者 is None else (所有者!=打开回合):#不符
        raise 会话格式错误(f'{类型} does not match the open turn')#错误

def 断言当前表面跨度(表面,数据,类型):#断言当前表面跨度
    """shadowedSeqs 必须精确命名当前表面跨度。"""
    范围=数据['shadowedRange']#范围
    序号们=数据['shadowedSeqs']#序号
    起点=表面.index(范围['start']) if 范围['start'] in 表面 else -1#起点
    终点=表面.index(范围['end']) if 范围['end'] in 表面 else -1#终点
    期望=[] if 起点<0 or 终点<起点 else 表面[起点:终点+1]#期望
    if len(期望)!=len(序号们) or any(期望[下标]!=序号们[下标] for 下标 in range(len(期望))):#不符
        raise 会话格式错误(f'{类型} shadowedSeqs do not name an exact current surface span')#错误
