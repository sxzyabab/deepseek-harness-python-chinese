"""每个已发布 v0 事件类型冻结的精确顶层载荷处置。"""
from ...工具.值 import 深冻结#深冻结

def 定义已发布载荷处置(必填,可选=None,不透明=None):#定义已发布载荷处置
    """为相邻格式校验器冻结一个精确已发布载荷成员处置。"""
    if 可选 is None:#默认无可选
        可选=[]#空可选
    if 不透明 is None:#默认无不透明
        不透明=[]#空不透明
    return 深冻结({#冻结
        'required':tuple(必填),#必填副本
        'optional':tuple(可选),#可选副本
        'opaque':tuple(不透明),#不透明副本
    })#freeze结束

处置=定义已发布载荷处置#处置别名

#冻结的已发布 v0 事件与载荷成员清单。
已发布v0事件处置表=深冻结({#v0事件处置表
    'agent-preset/selected':处置(['agentPreset']),#智能体预设已选
    'agent/inbox/spliced':处置(#收件箱拼接
        ['target','start','inserted'],#必填
        ['removedCount','outcome'],#可选
    ),#inbox/spliced结束
    'approval/asked':处置(['id','toolName'],['callId','reason']),#审批询问
    'approval/decided':处置(['id','outcome']),#审批决定
    'approval/policy':处置(['policy'],['source']),#审批策略
    'assistant/chunk':处置(['turn','step','chunk']),#助手块
    'assistant/message':处置(#助手消息
        ['turn','step','message'],#必填
        ['usage','interrupted'],#可选
    ),#assistant/message结束
    'command/done':处置(['commandId','kind'],['text','sourceEventSeq']),#命令完成
    'command/run':处置(['commandId','name','source'],['args']),#命令运行
    'compaction/end':处置(['compactionId','turn'],['sourceCommandId','error']),#压缩结束
    'compaction/prune':处置(['shadowedRange','shadowedSeqs','shadowedTokenCount']),#压缩裁剪
    'compaction/start':处置(['compactionId','turn'],['sourceCommandId']),#压缩开始
    'compaction/summary':处置(#压缩摘要
        ['compactionId','summary','shadowedRange','shadowedSeqs','shadowedTokenCount','provider','model'],#必填
        ['sourceCommandId','maxTokens','usage','rawOutput','llmStreamCall'],#可选
    ),#compaction/summary结束
    'feedback/record':处置(['text']),#反馈记录
    'goal/change':处置(#目标变更
        ['kind','version','operation'],#必填
        ['goal','roundsStarted','createdAt','updatedAt','cleared','clearedAt'],#可选
    ),#goal/change结束
    'hook/invoked':处置(['turn','point','dialect','handlerId'],['matcher']),#钩子调用
    'hook/result':处置(#钩子结果
        ['turn','point','handlerId','decision','durationMs'],#必填
        ['exitCode','stderrSummary'],#可选
    ),#hook/result结束
    'llm/retry':处置(#LLM重试
        ['retryId','turn','step','provider','mode','policyKey','retry','delayMs','failure'],#必填
        ['maxRetries'],#可选
    ),#llm/retry结束
    'llm/retry-started':处置(['retryId','turn','step','retry']),#LLM重试已开始
    'model/selection':处置(['provider','model'],['reasoningEffort']),#模型选择
    'permission/preset':处置(['preset']),#权限预设
    'plan/mode':处置(['active']),#计划模式
    'request/context':处置(['provider','model'],['contextWindow']),#请求上下文
    'request/header':处置(['header','reason'],['startsSeries']),#请求头
    'sandbox/mode':处置(['mode'],['source']),#沙盒模式
    'schedule/change':处置(['version','operation'],['schedule','id','acceptedAt']),#日程变更
    'session-log-deepseek/delivery-accepted':处置(#会话日志投递已接受
        ['sessionId','throughSeq'],#必填
    ),#delivery-accepted结束
    'session/end-seed':处置([]),#会话结束种子
    'session/title':处置(['title','messageSeqs','source']),#会话标题
    'session/title-llm-request':处置(#会话标题LLM请求
        ['titleProvider','messageSeqs','route','system','messages','maxTokens'],#必填
    ),#title-llm-request结束
    'step/end':处置(['turn','step']),#步骤结束
    'step/start':处置(['turn','step']),#步骤开始
    'subagent/descriptor':处置(#子智能体描述符
        ['mode','version','provider'],#必填
        ['label','agentProvider','agentModel','agentReasoningEffort','persona','toolFilter'],#可选
    ),#descriptor结束
    'subagent/model-selection-policy':处置(['allowedModels']),#子智能体模型选择策略
    'team/member':处置(['version','teamId','member']),#团队成员
    'team/message/delivered':处置(['version','teamId','messageId','targetId']),#团队消息已投递
    'team/message/queued':处置(['version','teamId','message']),#团队消息已排队
    'team/task':处置(['version','teamId','task']),#团队任务
    'todo/write':处置(['todos']),#待办写入
    'tool-workflow/agent-end':处置(['runId','seq','outcome']),#工具工作流智能体结束
    'tool-workflow/agent-start':处置(['runId','seq','label','childId'],['phase']),#工具工作流智能体开始
    'tool-workflow/run-end':处置(['runId','stopReason']),#工具工作流运行结束
    'tool-workflow/run-start':处置(['runId','name']),#工具工作流运行开始
    'tool/call':处置(['turn','step','callId','name','arguments']),#工具调用
    'tool/code-dispatch':处置(#工具代码分发
        ['rootCallId','parentCallId','subCallId','name','arguments','isError','content'],#必填
        [],#可选空
        ['arguments'],#不透明
    ),#code-dispatch结束
    'tool/code-dispatch-start':处置(#工具代码分发开始
        ['rootCallId','parentCallId','subCallId','name','arguments'],#必填
        [],#可选空
        ['arguments'],#不透明
    ),#code-dispatch-start结束
    'tool/result':处置(#工具结果
        ['turn','step','message'],#必填
        ['error','meta'],#可选
        ['meta'],#不透明
    ),#tool/result结束
    'turn/end':处置(['turn','reason']),#回合结束
    'turn/start':处置(['turn']),#回合开始
    'user/message':处置(['role','id','content','source']),#用户消息
    'web/deepseek-search-llm-request':处置(['endpoint','apiVersion','body']),#web搜索LLM请求
})#已发布v0事件处置表结束

#稳定排序的已发布 v0 事件清单。
已发布v0事件类型们=tuple(sorted(已发布v0事件处置表.keys()))#按默认字典序（对齐 en）
