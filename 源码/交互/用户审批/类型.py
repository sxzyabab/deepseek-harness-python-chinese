"""线路安全的审批标识与结果词汇，不含 cordis/服务导入，好让浏览器类型链（apiproxy api → client）消费它们而不加载本包的 Context 扩增。"""

def 审批请求标识(标识):#把字符串打成审批请求配对品牌 id
    """把字符串打成审批请求标识。把一条 approval/asked 审计事件与其 approval/decided 配对。由服务发放（每次 ApprovalService.request 调用一个新 id）。不做校验，原样打品牌。"""
    return 标识#运行时值不变，仅打品牌

审批请求标识值=审批请求标识#中文短别名

审批结果=('allowed-once','rejected','cancelled','unavailable')#封闭审批结果：一次性授予、显式拒绝、撤回的请求、或不可用的回答者
"""封闭的审批结果：一次性授予、显式拒绝、撤回的请求、或不可用的回答者。调用方对 unavailable 失败闭合。"""
