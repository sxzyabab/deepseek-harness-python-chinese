"""原生来源准入：保留未知归属，拒绝已退役插件包装。"""
from ..会话格式 import 会话格式错误,是否会话格式json对象#从会话格式导入
from .源列表 import 映射事件消息#映射事件消息

def 断言来源(消息):#断言生产者来源
    """要求消息来源为生产者自有种类。"""
    值=消息.get('source')#来源
    if (not 是否会话格式json对象(值) or not isinstance(值.get('kind'),str)
        or len(值['kind'])==0 or 值['kind']=='plugin'):#须非空且非plugin
        raise 会话格式错误('format v4 message requires a producer-owned source kind')#错误

def 断言v4消息来源(事件):#断言v4消息来源
    """校验每个已声明耐久消息槽位上的生产者归属。"""
    def 变换(消息):#走访时断言
        断言来源(消息)#断言
        return 消息#原样返回
    映射事件消息(事件,变换)#走访

def 断言v4源行准入(行):#断言v4源行准入
    """即使行可恢复失败，也拒绝已退役来源语法。"""
    if not 是否会话格式json对象(行) or not 是否会话格式json对象(行.get('data')):#不完整则交给解码
        return#返回
    数据=行['data']#载荷
    if 行.get('type')=='user/message':#用户消息
        消息列表=[数据]#单条
    elif 行.get('type') in ('system/message','assistant/message','tool/result'):#嵌套
        消息列表=[数据.get('message')]#嵌套消息
    elif 行.get('type')=='agent/inbox/spliced':#收件箱
        消息列表=数据.get('inserted')#插入
    elif 行.get('type')=='session/title-llm-request':#标题请求
        消息列表=数据.get('messages')#消息
    else:#无消息槽
        消息列表=[]#空
    if not isinstance(消息列表,list):#非数组则交给解码
        return#返回
    for 消息 in 消息列表:#逐条
        if not 是否会话格式json对象(消息):#不完整跳过
            continue#继续
        值=消息.get('source')#来源
        if 是否会话格式json对象(值) and 值.get('kind')=='plugin':#退役plugin包装
            断言来源(消息)#拒绝
