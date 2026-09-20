"""把已发布 v0 提升为已发布 v1 的身份格式边。"""
import json#诊断序列化
from ..会话格式 import (#从会话格式导入
    会话格式错误,#格式错误
    会话格式不支持迁移错误,#不支持迁移错误
    定义会话格式迁移,#定义迁移
    会话格式计数,#格式计数
)#从会话格式导入
from .编解码 import 是否已发布助手块游程#从编解码导入
from .校验 import (#从校验导入
    断言已发布事件载荷,#断言事件载荷
    断言已发布v1头,#断言v1头
)#从校验导入
from .记录与精确键 import 校验已发布v0键,已发布v0记录#记录与精确键

def 断言头版本(头,版本):#断言头版本
    """断言逻辑头精确版本。"""
    if 头['version']!=版本:#版本不符
        raise 会话格式错误(f'expected format v{版本} header')#版本不符

def 迁移头(头):#迁移头
    """把已发布 v0 头提升为 v1。"""
    断言头版本(头,0)#断言v0头
    return {**头,'version':1}#提升版本

def 创建阶段(输入):#创建阶段
    """创建已发布 v0 到 v1 迁移阶段。"""
    return 已发布v0到v1阶段(输入)#阶段实例

#把已发布 v0 提升为已发布 v1 的身份格式边。
会话格式v0到v1=定义会话格式迁移({#v0到v1迁移
    'name':'@deepseek-ai/dsh-session-format-v0-to-v1',#迁移名
    'fromVersion':0,#源版本
    'toVersion':1,#目标版本
    'migrateHeader':迁移头,#迁移头
    'createStage':创建阶段,#创建阶段
    'validateTargetHeader':断言已发布v1头,#校验目标头
})#会话格式v0到v1结束

class 已发布v0到v1阶段:#v0到v1阶段
    """有状态体阶段：逐事件规范化遗留形状。"""
    def __init__(自身,输入):#构造
        """记下输入并初始化规范化状态。"""
        断言头版本(输入['sourceHeader'],0)#断言源头
        自身.输入=输入#输入
        自身.headerInheritedEventCount=会话格式计数(输入['sourceInheritedEventCount'],'format v0 inherited event count')#校验继承数
        自身.状态={'messageIds':{},'retryIds':{}}#规范化状态

    def transformEvent(自身,事件,上下文):#转换事件
        """规范化一条源事件并同步发出。"""
        规范化=规范化已发布v0事件(事件,自身.输入['sourceHeader']['id'],自身.状态)#规范化
        断言源投递标记(规范化,自身.输入)#断言投递标记
        上下文.emitEvent(规范化)#发出

    def transformRun(自身,游程,上下文):#转换游程
        """助手块游程原样发出，其它展开转换。"""
        if 是否已发布助手块游程(游程):#助手块游程
            上下文.emitRun(游程)#原样发出
            return#返回
        for 事件 in 游程.expand():#展开
            自身.transformEvent(事件,上下文)#转换

    def finish(自身,上下文):#完成
        """返回头继承切口。"""
        return 自身.headerInheritedEventCount#头继承数

def 规范化已发布v0事件(事件,会话id,状态):#规范化已发布v0事件
    """规范化一条已发布 v0 事件。"""
    命名=规范化遗留压缩类型(事件)#规范化压缩类型名
    断言受支持遗留类型(命名,会话id)#断言受支持遗留类型
    起始=规范化遗留回合开始(命名,会话id)#规范化turn/start
    结束=规范化遗留回合结束(起始,会话id)#规范化turn/end
    头=规范化遗留请求头(结束,会话id)#规范化request/header
    转向=规范化遗留转向(头,会话id)#规范化steering
    重试=规范化遗留重试(转向,会话id,状态['retryIds'])#规范化retry
    压缩=规范化遗留压缩(重试,会话id,状态)#规范化压缩
    消息=规范化遗留消息(压缩,会话id,状态['messageIds'])#规范化消息
    if 消息['type']!='assistant/chunk':#非块则断言载荷
        断言已发布事件载荷(消息,0)#断言载荷
    消息id=事件消息id(消息)#取消息id
    if 消息id is not None:#有id
        状态['messageIds'][消息['seq']]=消息id#记入映射
    return 消息#返回

def 规范化遗留压缩类型(事件):#规范化遗留压缩类型
    """把 compact/* 改名为 compaction/*。"""
    类型=事件['type']#类型
    if 类型=='compact/start':#旧开始
        return {**事件,'type':'compaction/start'}#新名
    if 类型=='compact/summary':#旧摘要
        return {**事件,'type':'compaction/summary'}#新名
    if 类型=='compact/end':#旧结束
        return {**事件,'type':'compaction/end'}#新名
    if 类型=='compact/prune':#旧剪枝
        return {**事件,'type':'compaction/prune'}#新名
    return 事件#原样

def 断言源投递标记(事件,输入):#断言源投递标记
    """拒绝错会话的当代投递标记。"""
    if 事件['type']!='session-log-deepseek/delivery-accepted':#非该类型
        return#返回
    数据=已发布v0记录(事件['data'],f"{事件['type']} {事件['seq']} data")#data
    接纳版本=数据['sessionFormatVersion'] if 'sessionFormatVersion' in 数据 else 0#接纳版本
    继承=(输入['sourceHeader'].get('parentSession') is not None
        and 事件['seq']<会话格式计数(输入['sourceInheritedEventCount'],'format v0 inherited event count'))#且在切口前
    if 接纳版本==0 and not 继承 and 数据.get('sessionId')!=输入['sourceHeader']['id']:#错会话
        raise 会话格式错误('current-generation delivery marker names the wrong Session')#错误

def 规范化遗留重试(事件,会话id,重试id映射):#规范化遗留重试
    """为 llm/retry 补遗留 retryId。"""
    if 事件['type']!='llm/retry':#非该类型原样
        return 事件#原样
    数据=已发布v0记录(事件['data'],f"llm/retry {事件['seq']} data")#data
    链键='\0'.join(json.dumps(值,ensure_ascii=False,separators=(',',':'),allow_nan=False) for 值 in [数据['turn'],数据['step'],数据['provider'],数据['policyKey']])#链键
    重试id=数据.get('retryId')#重试id
    if isinstance(重试id,str) and len(重试id)>0:#已有id
        重试id映射[链键]=重试id#记入
        return 事件#原样
    if 'retryId' in 数据:#有字段但非法则原样
        return 事件#原样
    迁移id=重试id映射[链键] if 链键 in 重试id映射 else f'legacy-retry:{会话id}:{事件["seq"]}'#迁移id
    重试id映射[链键]=迁移id#记入
    return {**事件,'data':{**数据,'retryId':迁移id}}#补id

def 规范化遗留压缩(事件,会话id,状态):#规范化遗留压缩
    """为压缩事件与 compact 插件消息补遗留 compactionId。"""
    if 事件['type']=='session/end-seed':#结束种子
        状态.pop('compactionId',None)#清除压缩id
        return 事件#原样
    if 事件['type']=='compaction/start':#压缩开始
        数据=已发布v0记录(事件['data'],f"compaction/start {事件['seq']} data")#data
        已有=数据.get('compactionId')#已有id
        if isinstance(已有,str) and len(已有)>0:#有效id
            状态['compactionId']=已有#记录
            return 事件#原样
        if 'compactionId' in 数据:#有字段但非法
            return 事件#原样
        标识=f'legacy-compaction:{会话id}:{事件["seq"]}'#遗留id
        状态['compactionId']=标识#记录
        return {**事件,'data':{**数据,'compactionId':标识}}#补id
    压缩id=状态.get('compactionId')#当前压缩id
    if 压缩id is None:#无开放压缩
        return 事件#原样
    if 事件['type']=='compaction/summary' or 事件['type']=='compaction/end':#摘要或结束
        规范化=添加遗留压缩id(事件,压缩id)#补id
        if 事件['type']=='compaction/end':#结束则清除
            状态.pop('compactionId',None)#清除
        return 规范化#返回
    if 事件['type']!='user/message':#非用户消息
        return 事件#原样
    数据=已发布v0记录(事件['data'],f"user/message {事件['seq']} data")#data
    出处=数据.get('source')#出处
    if (not 已发布是记录(出处) or 出处.get('kind')!='plugin' or 出处.get('plugin')!='compact'
        or 'compactionId' in 出处):#非compact插件或已有id
        return 事件#原样
    return {#补压缩id
        **事件,#展开
        'data':{#数据
            **数据,#原字段
            'source':{#出处
                **出处,#原出处
                'compactionId':压缩id,#压缩id
            },#source结束
        },#data结束
    }#return结束

def 添加遗留压缩id(事件,压缩id):#添加遗留压缩id
    """为压缩摘要/结束补 compactionId。"""
    数据=已发布v0记录(事件['data'],f"{事件['type']} {事件['seq']} data")#data
    if 'compactionId' in 数据:#已有则原样
        return 事件#原样
    return {**事件,'data':{**数据,'compactionId':压缩id}}#补id

def 规范化遗留请求头(事件,会话id):#规范化遗留请求头
    """去掉 request/header 的遗留 messagePrefix。"""
    if 事件['type']!='request/header':#非该类型原样
        return 事件#原样
    数据=已发布v0记录(事件['data'],f"request/header {事件['seq']} data")#data记录
    头=已发布v0记录(数据['header'],f"request/header {事件['seq']} header")#内层头
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
        数据=已发布v0记录(事件['data'],f"request/header {事件['seq']} data")#data
        if 数据.get('reason')=='fallback':#遗留fallback
            raise 会话格式不支持迁移错误(#拒绝
                f'session {json.dumps(会话id,ensure_ascii=False)} contains unsupported request/header reason "fallback" at seq {事件["seq"]}',#消息
            )#Error结束

def 规范化遗留转向(事件,会话id):#规范化遗留steering
    """把 steering/message 转为 user/message。"""
    if 事件['type']!='steering/message':#非该类型原样
        return 事件#原样
    数据=已发布v0记录(事件['data'],f"steering/message {事件['seq']} data")#data
    if 'message' in 数据:#已包装
        校验已发布v0键(数据,['turn','message'],[],f"steering/message {事件['seq']} data")#断言键
        会话格式计数(数据['turn'],f"steering/message {事件['seq']} turn")#校验turn
        return {**事件,'type':'user/message','data':数据['message']}#转为user/message
    校验已发布v0键(数据,['turn','content','source'],[],f"steering/message {事件['seq']} data")#断言键
    会话格式计数(数据['turn'],f"steering/message {事件['seq']} turn")#校验turn
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
    数据=已发布v0记录(事件['data'],f"turn/start {事件['seq']} data")#data
    if 'trigger' not in 数据:#无trigger原样
        return 事件#原样
    校验已发布v0键(数据,['turn','trigger'],[],f"turn/start {事件['seq']} data")#断言键
    回合=会话格式计数(数据['turn'],f"turn/start {事件['seq']} turn")#turn
    触发=已发布v0记录(数据['trigger'],f"turn/start {事件['seq']} trigger")#trigger
    if 回合<1 or not isinstance(触发.get('kind'),str) or len(触发['kind'])==0:#畸形
        raise 畸形遗留(会话id,'turn/start',事件['seq'])#抛出
    return {**事件,'data':{'turn':回合}}#仅保留turn

def 规范化遗留回合结束(事件,会话id):#规范化遗留turn/end
    """规范化 turn/end 的遗留 reason。"""
    if 事件['type']!='turn/end':#非该类型原样
        return 事件#原样
    数据=已发布v0记录(事件['data'],f"turn/end {事件['seq']} data")#data
    校验已发布v0键(数据,['turn','reason'],[],f"turn/end {事件['seq']} data")#断言键
    回合=会话格式计数(数据['turn'],f"turn/end {事件['seq']} turn")#turn
    if 回合<1:#畸形
        raise 畸形遗留(会话id,'turn/end',事件['seq'])#畸形
    原因=已发布v0记录(数据['reason'],f"turn/end {事件['seq']} reason")#reason
    if not isinstance(原因.get('kind'),str):#畸形kind
        raise 畸形遗留(会话id,'turn/end',事件['seq'])#畸形kind
    种类=原因['kind']#kind
    if 种类 in ('completed','blocked','max-tokens','interrupted'):#简单种
        校验已发布v0键(原因,['kind'],[],f"turn/end {事件['seq']} reason")#仅kind
        return 事件#原样
    if 种类=='aborted':#中止
        if 'reason' in 原因:#已有嵌套reason
            return 事件#原样
        校验已发布v0键(原因,['kind'],[],f"turn/end {事件['seq']} reason")#仅kind
        当前={'kind':'aborted','reason':{'kind':'legacy'}}#补legacy
        return {**事件,'data':{**数据,'reason':当前}}#替换reason
    if 种类=='disposed':#已处置
        校验已发布v0键(原因,['kind'],[],f"turn/end {事件['seq']} reason")#仅kind
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
        校验已发布v0键(原因,['kind','step','failure'],[],f'turn/end {序号} reason')#断言键
        记录=已发布v0记录(失败,f'turn/end {序号} failure')#failure记录
        校验已发布v0键(#断言failure键
            记录,#记录
            ['message','code'],#必填
            ['status','providerRetryAfterMs','requestId'],#可选
            f'turn/end {序号} failure',#标签
        )#assert结束
        if not isinstance(记录.get('message'),str) or not isinstance(记录.get('code'),str):#畸形
            raise 畸形遗留(会话id,'turn/end',序号)#抛出
        return {'kind':'error','error':记录}#包装为error
    校验已发布v0键(原因,['kind','step','message'],['code'],f'turn/end {序号} reason')#断言键
    if not isinstance(原因.get('message'),str) or ('code' in 原因 and not isinstance(原因.get('code'),str)):#畸形
        raise 畸形遗留(会话id,'turn/end',序号)#抛出
    return {#返回error包装
        'kind':'error',#kind
        'error':{#error对象
            'message':原因['message'],#消息
            'code':原因['code'] if isinstance(原因.get('code'),str) else 'UNKNOWN',
        },#error结束
    }#return结束

def 规范化遗留消息(事件,会话id,消息id映射):#规范化遗留消息
    """把遗留扁平消息包装为当代 message 信封。"""
    数据=已发布v0记录(事件['data'],f"{事件['type']} {事件['seq']} data")#data
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
        源=已发布v0记录(出处,f"assistant/message {事件['seq']} provenance")#出处记录
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
            raise 会话格式错误(f"tool/result {事件['seq']} replacement cites a message without identity")#错误
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
    数据=已发布v0记录(事件['data'],f"{事件['type']} {事件['seq']} data")#data
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
