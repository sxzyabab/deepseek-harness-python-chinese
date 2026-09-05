"""把已发布 v0 提升为已发布 v1 的身份格式边。"""
import json#诊断序列化
from ..会话格式 import (#从会话格式导入
    会话格式错误,#格式错误
    会话格式不支持迁移错误,#不支持迁移错误
    定义会话格式迁移,#定义迁移
    会话格式计数,#格式计数
    快照会话格式产物,#快照产物
)#从会话格式导入
from .校验 import (#从校验导入
    断言已发布事件载荷,#断言事件载荷
    断言规范化已发布v0产物,#断言规范化v0产物
    断言已发布v0源产物,#断言v0源产物
    断言已发布v1产物,#断言v1产物
    断言已发布v1头,#断言v1头
)#从校验导入
from .校验辅助 import 断言已发布v0键,已发布v0记录#从辅助导入

def 断言头版本(头,版本):#断言头版本
    """断言逻辑头精确版本。"""
    if 头['version']!=版本:#版本不符
        raise 会话格式错误(f'expected format v{版本} header')#版本不符

def 迁移头(头):#迁移头
    """把已发布 v0 头提升为 v1。"""
    断言头版本(头,0)#断言v0头
    return {**头,'version':1}#提升版本

def 迁移产物(源):#迁移产物
    """规范化 v0 事件并产出已发布 v1 产物。"""
    断言已发布v0源产物(源)#断言源
    事件们=规范化已发布v0事件(源['events'],源['header']['id'])#规范化事件
    断言规范化已发布v0产物({**源,'events':事件们})#断言规范化
    目标=快照会话格式产物({#快照目标
        'header':{**源['header'],'version':1},#v1头
        'inheritedEventCount':源['inheritedEventCount'],#继承数
        'events':事件们,#事件
    },'released v0-to-v1 target')#标签
    断言已发布v1产物(目标)#断言v1
    return 目标#返回目标

#把已发布 v0 提升为已发布 v1 的身份格式边。
会话格式v0到v1=定义会话格式迁移({#v0到v1迁移
    'name':'@deepseek-ai/dsh-session-format-v0-to-v1',#迁移名
    'fromVersion':0,#源版本
    'toVersion':1,#目标版本
    'migrateHeader':迁移头,#迁移头
    'migrate':迁移产物,#迁移产物
    'validateTarget':断言已发布v1产物,#校验目标
    'validateTargetHeader':断言已发布v1头,#校验目标头
})#会话格式v0到v1结束

def 规范化已发布v0事件(事件们,会话id):#规范化已发布v0事件
    """规范化已发布 v0 事件列表。"""
    消息id映射={}#消息id映射
    输出=[]#输出
    for 事件 in 事件们:#遍历事件
        断言受支持遗留类型(事件,会话id)#断言受支持遗留类型
        起始=规范化遗留回合开始(事件,会话id)#规范化turn/start
        结束=规范化遗留回合结束(起始,会话id)#规范化turn/end
        头=规范化遗留请求头(结束,会话id)#规范化request/header
        转向=规范化遗留转向(头,会话id)#规范化steering
        消息=规范化遗留消息(转向,会话id,消息id映射)#规范化消息
        断言已发布事件载荷(消息,0)#断言载荷
        输出.append(消息)#推入输出
        消息id=事件消息id(消息)#取消息id
        if 消息id is not None:#有id
            消息id映射[消息['seq']]=消息id#记入映射
    return tuple(输出)#冻结返回

def 规范化遗留请求头(事件,会话id):#规范化遗留请求头
    """去掉 request/header 的遗留 messagePrefix。"""
    if 事件['type']!='request/header':#非该类型原样
        return 事件#原样
    数据=已发布v0记录(事件['data'],f'request/header {事件["seq"]} data')#data记录
    头=已发布v0记录(数据['header'],f'request/header {事件["seq"]} header')#内层头
    if 'messagePrefix' not in 头:#无前缀原样
        return 事件#原样
    if not isinstance(头['messagePrefix'],list):#前缀畸形
        raise 会话格式错误(#错误
            f'session {json.dumps(会话id,ensure_ascii=False)} contains malformed request/header messagePrefix at seq {事件["seq"]}',#消息
        )#Error结束
    当前头={键:值 for 键,值 in 头.items() if 键!='messagePrefix'}#去掉前缀
    return {**事件,'data':{**数据,'header':当前头}}#返回去前缀事件

def 断言受支持遗留类型(事件,会话id):#断言受支持遗留类型
    """拒绝不受支持的遗留事件类型。"""
    if 事件['type']=='request/header-delta' or 事件['type']=='mode/set':#不支持类型
        raise 会话格式不支持迁移错误(#拒绝
            f'session {json.dumps(会话id,ensure_ascii=False)} contains unsupported legacy {事件["type"]} event at seq {事件["seq"]}',#消息
        )#Error结束
    if 事件['type']=='request/header':#请求头
        数据=已发布v0记录(事件['data'],f'request/header {事件["seq"]} data')#data
        if 数据.get('reason')=='fallback':#遗留fallback
            raise 会话格式不支持迁移错误(#拒绝
                f'session {json.dumps(会话id,ensure_ascii=False)} contains unsupported request/header reason "fallback" at seq {事件["seq"]}',#消息
            )#Error结束

def 规范化遗留转向(事件,会话id):#规范化遗留steering
    """把 steering/message 转为 user/message。"""
    if 事件['type']!='steering/message':#非该类型原样
        return 事件#原样
    数据=已发布v0记录(事件['data'],f'steering/message {事件["seq"]} data')#data
    if 'message' in 数据:#已包装
        断言已发布v0键(数据,['turn','message'],[],f'steering/message {事件["seq"]} data')#断言键
        会话格式计数(数据['turn'],f'steering/message {事件["seq"]} turn')#校验turn
        return {**事件,'type':'user/message','data':数据['message']}#转为user/message
    断言已发布v0键(数据,['turn','content','source'],[],f'steering/message {事件["seq"]} data')#断言键
    会话格式计数(数据['turn'],f'steering/message {事件["seq"]} turn')#校验turn
    消息={键:值 for 键,值 in 数据.items() if 键!='turn'}#去掉turn
    return {#返回用户消息
        **事件,#展开事件
        'type':'user/message',#类型
        'data':{#数据
            **消息,#消息字段
            'id':遗留消息id(会话id,事件['seq']),#遗留id
            'role':'user',#角色
        },#data结束
    }#return结束

def 规范化遗留回合开始(事件,会话id):#规范化遗留turn/start
    """去掉 turn/start 的遗留 trigger。"""
    if 事件['type']!='turn/start':#非该类型原样
        return 事件#原样
    数据=已发布v0记录(事件['data'],f'turn/start {事件["seq"]} data')#data
    if 'trigger' not in 数据:#无trigger原样
        return 事件#原样
    断言已发布v0键(数据,['turn','trigger'],[],f'turn/start {事件["seq"]} data')#断言键
    回合=会话格式计数(数据['turn'],f'turn/start {事件["seq"]} turn')#turn
    触发=已发布v0记录(数据['trigger'],f'turn/start {事件["seq"]} trigger')#trigger
    if 回合<1 or not isinstance(触发.get('kind'),str) or len(触发['kind'])==0:#畸形
        raise 畸形遗留(会话id,'turn/start',事件['seq'])#抛出
    return {**事件,'data':{'turn':回合}}#仅保留turn

def 规范化遗留回合结束(事件,会话id):#规范化遗留turn/end
    """规范化 turn/end 的遗留 reason。"""
    if 事件['type']!='turn/end':#非该类型原样
        return 事件#原样
    数据=已发布v0记录(事件['data'],f'turn/end {事件["seq"]} data')#data
    断言已发布v0键(数据,['turn','reason'],[],f'turn/end {事件["seq"]} data')#断言键
    回合=会话格式计数(数据['turn'],f'turn/end {事件["seq"]} turn')#turn
    if 回合<1:#畸形
        raise 畸形遗留(会话id,'turn/end',事件['seq'])#畸形
    原因=已发布v0记录(数据['reason'],f'turn/end {事件["seq"]} reason')#reason
    if not isinstance(原因.get('kind'),str):#畸形kind
        raise 畸形遗留(会话id,'turn/end',事件['seq'])#畸形kind
    种类=原因['kind']#kind
    if 种类 in ('completed','blocked','max-tokens','interrupted'):#简单种
        断言已发布v0键(原因,['kind'],[],f'turn/end {事件["seq"]} reason')#仅kind
        return 事件#原样
    if 种类=='aborted':#中止
        if 'reason' in 原因:#已有嵌套reason
            return 事件#原样
        断言已发布v0键(原因,['kind'],[],f'turn/end {事件["seq"]} reason')#仅kind
        当前={'kind':'aborted','reason':{'kind':'legacy'}}#补legacy
        return {**事件,'data':{**数据,'reason':当前}}#替换reason
    if 种类=='disposed':#已处置
        断言已发布v0键(原因,['kind'],[],f'turn/end {事件["seq"]} reason')#仅kind
        当前={'kind':'aborted','reason':{'kind':'disposed'}}#映射为aborted
        return {**事件,'data':{**数据,'reason':当前}}#替换reason
    if 种类=='error':#错误
        if 'error' in 原因:#已有error
            return 事件#原样
        当前=规范化遗留错误原因(原因,事件['seq'],会话id)#规范化错误
        return {**事件,'data':{**数据,'reason':当前}}#替换reason
    return 事件#其他原样

def 规范化遗留错误原因(原因,序号,会话id):#规范化遗留错误reason
    """把遗留 error reason 规范为当代 error 包装。"""
    会话格式计数(原因['step'],f'turn/end {序号} error step')#校验step
    失败=原因.get('failure') if 'failure' in 原因 else None#failure字段
    if 'failure' in 原因:#有failure
        断言已发布v0键(原因,['kind','step','failure'],[],f'turn/end {序号} reason')#断言键
        记录=已发布v0记录(失败,f'turn/end {序号} failure')#failure记录
        断言已发布v0键(#断言failure键
            记录,#记录
            ['message','code'],#必填
            ['status','providerRetryAfterMs','requestId'],#可选
            f'turn/end {序号} failure',#标签
        )#assert结束
        if not isinstance(记录.get('message'),str) or not isinstance(记录.get('code'),str):#畸形
            raise 畸形遗留(会话id,'turn/end',序号)#抛出
        return {'kind':'error','error':记录}#包装为error
    断言已发布v0键(原因,['kind','step','message'],['code'],f'turn/end {序号} reason')#断言键
    if not isinstance(原因.get('message'),str) or ('code' in 原因 and not isinstance(原因.get('code'),str)):#畸形
        raise 畸形遗留(会话id,'turn/end',序号)#抛出
    return {#返回error包装
        'kind':'error',#kind
        'error':{#error对象
            'message':原因['message'],#消息
            'code':原因['code'] if isinstance(原因.get('code'),str) else 'UNKNOWN',#码
        },#error结束
    }#return结束

def 规范化遗留消息(事件,会话id,消息id映射):#规范化遗留消息
    """把遗留扁平消息包装为当代 message 信封。"""
    数据=已发布v0记录(事件['data'],f'{事件["type"]} {事件["seq"]} data')#data
    if 事件['type']=='user/message':#用户消息
        if ('id' in 数据) or ('role' in 数据) or ('message' in 数据) or ('content' not in 数据) or ('source' not in 数据):#已有新形或缺字段
            return 事件#原样
        return {#补id与role
            **事件,#展开
            'data':{#数据
                **数据,#原字段
                'id':遗留消息id(会话id,事件['seq']),#遗留id
                'role':'user',#角色
            },#data结束
        }#return结束
    if 事件['type']=='assistant/message':#助手消息
        if ('message' in 数据) or ('content' not in 数据) or ('provenance' not in 数据):#已有或缺字段
            return 事件#原样
        内容=数据['content']#内容
        出处=数据['provenance']#出处
        事件数据={键:值 for 键,值 in 数据.items() if 键 not in ('content','provenance')}#其余字段
        源=已发布v0记录(出处,f'assistant/message {事件["seq"]} provenance')#出处记录
        return {#包装为message
            **事件,#展开
            'data':{#数据
                **事件数据,#其余字段
                'message':{#消息
                    'id':遗留消息id(会话id,事件['seq']),#遗留id
                    'role':'assistant',#角色
                    'content':内容,#内容
                    'source':{**源,'kind':'model'},#模型出处
                },#message结束
            },#data结束
        }#return结束
    if 事件['type']=='tool/result':#工具结果
        if ('message' in 数据) or ('callId' not in 数据) or ('content' not in 数据) or ('isError' not in 数据):#已有或缺
            return 事件#原样
        调用id=数据['callId']#callId
        内容=数据['content']#content
        是否错误=数据['isError']#isError
        事件数据={键:值 for 键,值 in 数据.items() if 键 not in ('callId','content','isError')}#其余
        if not isinstance(调用id,str) or not isinstance(是否错误,bool) or 内容 is None:#类型不符
            return 事件#原样
        继承id=替换起点(事件)#替换起点
        if 继承id is None:#无继承
            消息id=遗留消息id(会话id,事件['seq'])#新遗留id
        else:#查映射
            消息id=消息id映射.get(继承id)#查映射
        if 消息id is None:#无身份
            raise 会话格式错误(f'tool/result {事件["seq"]} replacement cites a message without identity')#错误
        return {#包装为message
            **事件,#展开
            'data':{#数据
                **事件数据,#其余
                'message':{#消息
                    'id':消息id,#消息id
                    'role':'user',#角色
                    'content':[{'type':'tool-result','toolCallId':调用id,'content':内容,'isError':是否错误}],#工具结果块
                    'source':{'kind':'tool','callId':调用id},#工具出处
                },#message结束
            },#data结束
        }#return结束
    return 事件#其他原样

def 替换起点(事件):#替换起点
    """读取 surfaceOp 替换起点。"""
    操作=事件.get('surfaceOp')#表面操作
    if 操作 is None or not 已发布是记录(操作) or 操作.get('op')!='replace':#非替换
        return None#非替换
    return 操作['start']#返回start

def 事件消息id(事件):#事件消息id
    """读取事件消息身份。"""
    数据=已发布v0记录(事件['data'],f'{事件["type"]} {事件["seq"]} data')#data
    if 事件['type']=='user/message':#用户消息
        消息=数据#data即消息
    elif 已发布是记录(数据.get('message')):#否则取message
        消息=数据['message']#message
    else:#无
        消息=None#无
    return 消息['id'] if isinstance(消息,dict) and isinstance(消息.get('id'),str) else None#返回id

def 已发布是记录(值):#是否记录
    """测试值是否为非 null、非数组对象。"""
    return isinstance(值,dict)#对象判定

def 遗留消息id(会话id,序号):#遗留消息id
    """拼遗留消息身份。"""
    return f'legacy-message:{会话id}:{序号}'#拼id

def 畸形遗留(会话id,类型,序号):#畸形遗留错误
    """构造畸形遗留错误。"""
    return 会话格式错误(#错误
        f'session {json.dumps(会话id,ensure_ascii=False)} contains malformed pre-react-loop {类型} at seq {序号}',#消息
    )#Error结束
