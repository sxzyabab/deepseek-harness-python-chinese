"""最小原生思考元数据；耐久 harness 块拥有全部响应文本。"""
from ....llm import 大模型错误#LLM 错误

__all__=('校验对象','回放状态','读取回放')#仅中文公开名

def 校验对象(值,码='MALFORMED_RESPONSE'):
    """在提供方与耐久数据读取处拒绝畸形 JSON 对象。"""
    if not isinstance(值,dict):#非对象
        raise 大模型错误('DeepSeek Messages expected a JSON object',码)#畸形
    return 值#对象

def 回放状态(模型,块列表):
    """构造不重复助手文本的响应元数据。"""
    return {'response':{'kind':'deepseek-messages','version':1,'model':模型},'blocks':块列表}#信封

def 读取回放(消息,模型,降级=None):
    """校验原生回放，丢弃不可用元数据后再序列化耐久内容。"""
    try:#校验
        源=消息.get('source') or {}#来源
        if 源.get('kind')!='model' or 'replayState' not in 源:#无回放
            return None#缺席
        def 失败(细节):#失败
            """不可用回放状态。"""
            raise 大模型错误('DeepSeek Messages replay: '+细节,'INVALID_REPLAY_STATE')#失败
        信封=校验对象(源['replayState'],'INVALID_REPLAY_STATE')#信封
        响应=校验对象(信封.get('response'),'INVALID_REPLAY_STATE')#响应
        if 响应.get('kind')!='deepseek-messages' or 响应.get('version')!=1:#种类或版本
            return 失败('unsupported kind or version')#失败
        if 响应.get('model')!=源.get('model'):#与助手来源模型不一致
            return 失败('model does not match assistant source model')#失败
        块表=信封.get('blocks')#块表
        内容=消息.get('content') or []#内容
        if not isinstance(块表,list) or len(块表)!=len(内容):#数量
            return 失败('block count mismatch')#失败
        结果=[]#对齐元数据
        for 下标,值 in enumerate(块表):#逐块
            块=校验对象(值,'INVALID_REPLAY_STATE')#对象
            种类=块.get('type')#种类
            if 种类!=内容[下标].get('type') or 种类 not in ('text','reasoning','tool-call'):#类型
                return 失败('block type mismatch')#失败
            if 块.get('signature') is not None and (种类!='reasoning' or not isinstance(块.get('signature'),str)):#签名
                return 失败('invalid signature')#失败
            结果.append(块)#收下
        if 响应.get('model')!=模型:#跨模型不可移植
            return None#丢弃
        return 结果#对齐元数据
    except 大模型错误 as 错误:#回放失败
        if 错误.code!='INVALID_REPLAY_STATE':#非回放
            raise 错误#原样
        if 降级 is not None:#有诊断
            降级(错误.message)#报告
        return None#丢弃
