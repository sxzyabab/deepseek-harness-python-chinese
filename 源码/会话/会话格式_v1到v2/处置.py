"""已发布 v2 冻结的精确顶层事件与载荷成员清单。"""
from ..会话格式_v0到v1 import (#从v0到v1导入
    已发布v0事件处置,#v0处置表
    定义已发布载荷处置,#定义处置
)#从v0到v1导入

保留条目={}#保留条目
for 类型,处置 in 已发布v0事件处置.items():#过滤
    if (类型!='assistant/chunk'#去掉助手块
        and 类型!='assistant/message'#去掉助手消息
        and 类型!='session-log-deepseek/delivery-accepted'#去掉投递已接受
        and 类型!='session/end-seed'):#去掉结束种子
        保留条目[类型]=处置#保留

已发布v2事件处置={**保留条目,#保留的v0条目
    'assistant/attempt':定义已发布载荷处置(['turn','step','stream']),#助手尝试
    'assistant/message':定义已发布载荷处置(#助手消息
        ['turn','step','message','stream'],#必填
        ['usage','interrupted'],#可选
    ),#assistant/message结束
    'session-log-deepseek/delivery-accepted':定义已发布载荷处置(#投递已接受
        ['sessionId','throughSeq'],#必填
        ['sessionFormatVersion'],#可选
    ),#delivery-accepted结束
    'session/end-seed':定义已发布载荷处置([],['inherited']),#结束种子
}#已发布v2事件处置结束

已发布v2事件类型=tuple(#v2事件类型列表
    sorted(已发布v2事件处置.keys()),#按字典序（对齐 en localeCompare）
)#已发布v2事件类型结束
