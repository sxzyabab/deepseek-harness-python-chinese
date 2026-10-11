'交给目标自己的 Chat 定位使用的原始日志坐标'

__all__=['会话日志聊天目标']

def 片段部位(分片):
    '推理或回复分片对应的 group 部位'
    if 分片 is None:
        return None
    类型=分片.get('type')
    if 类型=='reasoning-delta':
        return 'reasoning'
    if 类型=='text-delta':
        return 'response'
    块类型=None
    if 类型=='block-start':
        块类型=分片.get('blockType')
    elif 类型=='block-end':
        块=分片.get('block') or {}
        块类型=块.get('type')
    if 块类型=='reasoning':
        return 'reasoning'
    if 块类型=='text':
        return 'response'
    return None

def 会话日志聊天目标(锚):
    '描述一条日志记录，不读取另一个视图的模型或 DOM'
    事件=锚['event']
    分片=锚.get('chunk')
    数据=事件['data'] if isinstance(事件,dict) else 事件.data
    if not isinstance(数据,dict):
        数据={}
    回合=数据['turn'] if 'turn' in 数据 and isinstance(数据['turn'],(int,float)) and not isinstance(数据['turn'],bool) else None
    步=数据['step'] if 'step' in 数据 and isinstance(数据['step'],(int,float)) and not isinstance(数据['step'],bool) else None
    类型=事件['type'] if isinstance(事件,dict) else 事件.type
    调用=None
    if 类型=='tool/call':
        调用=数据.get('callId')
    elif 类型=='tool/result':
        消息=数据.get('message') or {}
        调用=消息.get('source',{}).get('callId') if isinstance(消息,dict) else None
    elif 'subCallId' in 数据 and isinstance(数据['subCallId'],str):
        调用=数据['subCallId']
    elif 分片 is not None and 分片.get('type')=='tool-call-delta':
        调用=分片.get('id')
    elif 分片 is not None and 分片.get('type')=='block-end':
        块=分片.get('block') or {}
        if 块.get('type')=='tool-call':
            调用=块.get('id')
    根调用=数据['rootCallId'] if 'rootCallId' in 数据 and isinstance(数据['rootCallId'],str) else 调用
    部位=片段部位(分片)
    结果={'anchorSeq':事件['seq'] if isinstance(事件,dict) else 事件.seq}
    if 类型 in ('assistant/message','assistant/attempt','assistant/live-chunk'):
        结果['nodeKind']='assistant-step'
    if 回合 is not None:
        结果['turn']=回合
    if 步 is not None:
        结果['step']=步
    if 调用 is not None:
        结果['callId']=调用
    if 根调用 is not None and 根调用!=调用:
        结果['rootCallId']=根调用
    if 部位 is not None:
        结果['groupPart']=部位
    return 结果
