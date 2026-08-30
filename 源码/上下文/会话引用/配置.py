"""会话引用的配置与稳定诊断。"""
from ...模型后端.llm import 装备错误#导入harness错误基类

最大引用数=3#单条消息最多引用3个会话
默认候选上限=50#宿主候选列表默认上限
默认最大引用字节=65536#单个引用快照默认字节预算
会话引用配置字段=('maxReferences','candidateLimit','maxReferenceBytes')#会话引用服务配置字段名
会话引用错误码=(#会话引用稳定错误码
    'SESSION_REFERENCE_INVALID_CONFIG',#配置非法
    'SESSION_REFERENCE_INVALID_REFERENCE',#引用结构非法
    'SESSION_REFERENCE_SELF_REFERENCE',#引用自身
    'SESSION_REFERENCE_TOO_MANY',#引用数量超限
    'SESSION_REFERENCE_READ_FAILED',#读取源会话失败
    'SESSION_REFERENCE_BUDGET_EXCEEDED',#超出字节预算
    'SESSION_REFERENCE_CANCELLED',#准备被取消
)#错误码元组结束
class 会话引用错误(装备错误):#可供宿主协议错误映射的带类型会话引用失败
    """可供宿主协议错误映射的带类型会话引用失败。"""
    def __init__(自身,消息,码,选项=None):#记下稳定路由码与可选cause
        """记下给人读的诊断、稳定路由码与可选 cause。"""
        装备错误.__init__(自身,消息,码,选项)#交给装备错误基类
        自身.name='SessionReferenceError'#固定错误名
