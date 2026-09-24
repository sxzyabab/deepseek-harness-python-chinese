"""最小原生思考元数据；耐久 Harness 块拥有全部响应文本。"""
from ..llm import 大模型错误

__all__=['对象','回放状态','读回放']

def 对象(值,码='MALFORMED_RESPONSE'):
    """在提供方与耐久读取处拒绝畸形 JSON 对象。"""
    if not isinstance(值,dict):
        raise 大模型错误('DeepSeek Messages expected a JSON object',码)
    return 值

def 回放状态(模型,块列表):
    """构造响应元数据，不复制助手文本。"""
    return {'response':{'kind':'deepseek-messages','version':1,'model':模型},'blocks':块列表}

def 读回放(消息,模型,降级=None):
    """校验原生回放，序列化耐久内容前丢掉不可用元数据。"""
    try:
        return 校验回放(消息,模型)
    except 大模型错误 as 错误:
        if 错误.code!='INVALID_REPLAY_STATE':
            raise 错误
        if 降级 is not None:
            降级(str(错误))
        return None

def 校验回放(消息,模型):
    """校验耐久回放信封。"""
    来源=消息['source']
    if 来源.get('kind')!='model' or 'replayState' not in 来源 or 来源['replayState'] is None:
        return None
    def 失败(细节):
        """不可用回放。"""
        raise 大模型错误('DeepSeek Messages replay: '+细节,'INVALID_REPLAY_STATE')
    信封=对象(来源['replayState'],'INVALID_REPLAY_STATE')
    响应=对象(信封.get('response'),'INVALID_REPLAY_STATE')
    if 响应.get('kind')!='deepseek-messages' or 响应.get('version')!=1:
        失败('unsupported kind or version')
    if 响应.get('model')!=来源.get('model'):
        失败('model does not match assistant source model')
    块列表=信封.get('blocks')
    if (not isinstance(块列表,list)) or len(块列表)!=len(消息['content']):
        失败('block count mismatch')
    结果=[]
    下标=0
    for 值 in 块列表:
        块=对象(值,'INVALID_REPLAY_STATE')
        内容块=消息['content'][下标] if 下标<len(消息['content']) else None
        类型=块.get('type')
        if 内容块 is None or 类型!=内容块.get('type') or 类型 not in ('text','reasoning','tool-call'):
            失败('block type mismatch')
        if 'signature' in 块 and 块['signature'] is not None and (类型!='reasoning' or not isinstance(块['signature'],str)):
            失败('invalid signature')
        条目={'type':类型}
        if isinstance(块.get('signature'),str):
            条目['signature']=块['signature']
        结果.append(条目)
        下标+=1
    if 响应.get('model')!=模型:
        return None
    return 结果
