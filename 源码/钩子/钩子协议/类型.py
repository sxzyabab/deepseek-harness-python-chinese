钩子方言=('claude-code','codex')#钩子桥接方言取值
钩子方言类型=str#运行时即字符串
匹配模式方言=('claude-code','codex')#匹配模式方言取值
匹配模式类型=str#运行时即字符串

#会话事件图并入说明（Python 侧无 declare module；权威载荷字段如下）：
# hook/invoked: turn, point, dialect, matcher?, handlerId
# hook/result: turn, point, handlerId, decision, exitCode?, stderrSummary?, durationMs

命令钩子=dict#命令钩子：command, timeoutSec?
匹配组=dict#匹配组：matcher?, hooks
钩子输出=dict#方言无关钩子结果

class 钩子协议错误(Exception):
    """钩子协议包的异常基类。"""
