"""经原生编解码器校验产物，不做词表感知恢复。"""
from ...会话格式 import 会话格式事件收集器#事件收集器
from ..编解码 import 已发布v4会话格式编解码器#v4编解码器

def 断言已发布v4产物(产物):#断言已发布v4产物
    """把当代产物编码再严格解码，以校验分帧。"""
    编解码器=已发布v4会话格式编解码器#编解码器
    解码器=编解码器.createDecoder(编解码器.encodeHeader(产物['header'],产物['inheritedEventCount']),'strict')#严格解码器
    输出=会话格式事件收集器()#收集器
    for 事件 in 产物['events']:#逐事件
        解码器.decodeRow(编解码器.encodeEvent(事件),输出)#编码再解码
    解码器.finish(输出)#收口
