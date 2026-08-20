"""Claude Code 与 Codex 钩子桥接层共用的方言无关词表和仅日志事件。载荷组装、匹配差异、环境和扩展点专属判定映射仍由各桥自己拥有。"""

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
