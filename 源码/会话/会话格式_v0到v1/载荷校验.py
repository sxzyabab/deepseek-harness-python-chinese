"""已发布事件嵌套载荷语义校验。"""
import json,math,re#诊断、有限数、瞬时正则
from datetime import datetime,timezone#UTC瞬时
from ..会话格式 import 会话格式错误,会话格式计数,会话格式安全整数#格式错误与计数
from ..会话格式.json import 是否负零#负零判定
from .校验辅助 import 断言已发布v0键,已发布v0记录#记录与精确键

UTC瞬时正则=re.compile(#规范UTC瞬时
    r'^(?!0000)\d{4}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12]\d|3[01])T(?:[01]\d|2[0-3]):[0-5]\d:[0-5]\d\.\d{3}Z$'
)#正则结束

def 断言已发布载荷语义(事件,版本):#断言已发布载荷语义
    """校验一个已知事件的嵌套已发布载荷语义。"""
    数据=已发布v0记录(事件['data'],f"{事件['type']} {事件['seq']} data")#data
    标签=f"{事件['type']} {事件['seq']}"#标签
    类型=事件['type']#类型
    if 类型=='agent-preset/selected':#智能体预设已选
        字符串值(数据['agentPreset'],f'{标签} agentPreset')#预设
        return#结束
    if 类型=='agent/inbox/spliced':#收件箱拼接
        字面值(数据['target'],['next-turn','next-step'],f'{标签} target')#目标
        计数值(数据['start'],f'{标签} start')#起点
        if 'removedCount' in 数据:#有移除数
            计数值(数据['removedCount'],f'{标签} removedCount')#移除数
        def 校验插入(值,项标签):#校验插入消息
            消息值(值,f'{标签} inserted message',版本,'user')#用户消息
        数组值(数据['inserted'],f'{标签} inserted',校验插入)#插入
        if 'outcome' in 数据:#有结果
            字面值(数据['outcome'],['canceled'],f'{标签} outcome')#结果
        return#结束
    if 类型=='approval/asked':#审批询问
        非空串(数据['id'],f'{标签} id')#id
        非空串(数据['toolName'],f'{标签} toolName')#工具名
        if 'callId' in 数据:#有调用id
            非空串(数据['callId'],f'{标签} callId')#调用id
        if 'reason' in 数据:#有原因
            字符串值(数据['reason'],f'{标签} reason')#原因
        return#结束
    if 类型=='approval/decided':#审批决定
        非空串(数据['id'],f'{标签} id')#id
        字面值(数据['outcome'],['allowed-once','rejected','cancelled','unavailable'],f'{标签} outcome')#结果
        return#结束
    if 类型=='approval/policy':#审批策略
        字面值(数据['policy'],['ask','never'],f'{标签} policy')#策略
        if 'source' in 数据:#有来源
            字面值(数据['source'],['delegation'],f'{标签} source')#来源
        return#结束
    if 类型=='assistant/chunk':#助手块
        坐标对(数据,标签)#坐标
        流块值(数据['chunk'],f'{标签} chunk')#块
        return#结束
    if 类型=='assistant/message':#助手消息
        坐标对(数据,标签)#坐标
        消息值(数据['message'],f'{标签} message',版本,'assistant')#消息
        if 'usage' in 数据:#有用量
            令牌用量值(数据['usage'],f'{标签} usage')#用量
        if 'interrupted' in 数据:#有中断
            字面值(数据['interrupted'],[True],f'{标签} interrupted')#中断
        return#结束
    if 类型=='command/done':#命令完成
        非空串(数据['commandId'],f'{标签} commandId')#命令id
        字面值(数据['kind'],['success','error'],f'{标签} kind')#种
        if 'text' in 数据:#有文本
            字符串值(数据['text'],f'{标签} text')#文本
        if 'sourceEventSeq' in 数据:#有出处序号
            更早序号(数据['sourceEventSeq'],事件['seq'],f'{标签} sourceEventSeq')#出处
        return#结束
    if 类型=='command/run':#命令运行
        非空串(数据['commandId'],f'{标签} commandId')#命令id
        非空串(数据['name'],f'{标签} name')#名
        if 'args' in 数据:#有参数
            字符串值(数据['args'],f'{标签} args')#参数
        源=精确记录(数据['source'],f'{标签} source',['kind'])#源
        字面值(源['kind'],['user'],f'{标签} source kind')#源种
        return#结束
    if 类型 in ('compaction/start','compaction/end'):#压缩起止
        非空串(数据['compactionId'],f'{标签} compactionId')#压缩id
        if 'sourceCommandId' in 数据:#有源命令
            非空串(数据['sourceCommandId'],f'{标签} sourceCommandId')#源命令
        可空值(数据['turn'],f'{标签} turn',计数值)#回合可空
        if 'error' in 数据:#有错误
            字符串值(数据['error'],f'{标签} error')#错误
        return#结束
    if 类型=='compaction/prune':#压缩裁剪
        遮蔽值(数据,事件['seq'],标签)#遮蔽
        return#结束
    if 类型=='compaction/summary':#压缩摘要
        if 数据.get('llmStreamCall') is True and 'rawOutput' not in 数据:#缺rawOutput
            raise 会话格式错误(f'{标签} llmStreamCall requires rawOutput')#错误
        非空串(数据['compactionId'],f'{标签} compactionId')#压缩id
        if 'sourceCommandId' in 数据:#有源命令
            非空串(数据['sourceCommandId'],f'{标签} sourceCommandId')#源命令
        内容块们值(数据['summary'],f'{标签} summary',版本)#摘要
        遮蔽值(数据,事件['seq'],标签)#遮蔽
        非空串(数据['provider'],f'{标签} provider')#提供方
        非空串(数据['model'],f'{标签} model')#模型
        if 'maxTokens' in 数据:#有上限
            计数值(数据['maxTokens'],f'{标签} maxTokens')#上限
        if 'usage' in 数据:#有用量
            令牌用量值(数据['usage'],f'{标签} usage')#用量
        if 'rawOutput' in 数据:#有原始输出
            内容块们值(数据['rawOutput'],f'{标签} rawOutput',版本)#原始输出
        if 'llmStreamCall' in 数据:#有流调用
            字面值(数据['llmStreamCall'],[True],f'{标签} llmStreamCall')#流调用
        return#结束
    if 类型=='feedback/record':#反馈记录
        非空串(数据['text'],f'{标签} text')#文本
        return#结束
    if 类型=='goal/change':#目标变更
        目标变更值(数据,标签)#目标
        return#结束
    if 类型=='hook/invoked':#钩子调用
        计数值(数据['turn'],f'{标签} turn')#回合
        非空串(数据['point'],f'{标签} point')#点
        字面值(数据['dialect'],['claude-code','codex'],f'{标签} dialect')#方言
        if 'matcher' in 数据:#有匹配器
            字符串值(数据['matcher'],f'{标签} matcher')#匹配器
        非空串(数据['handlerId'],f'{标签} handlerId')#处理器
        return#结束
    if 类型=='hook/result':#钩子结果
        计数值(数据['turn'],f'{标签} turn')#回合
        非空串(数据['point'],f'{标签} point')#点
        非空串(数据['handlerId'],f'{标签} handlerId')#处理器
        非空串(数据['decision'],f'{标签} decision')#决定
        if 'exitCode' in 数据:#有退出码
            安全整数值(数据['exitCode'],f'{标签} exitCode')#退出码
        if 'stderrSummary' in 数据:#有stderr摘要
            字符串值(数据['stderrSummary'],f'{标签} stderrSummary')#stderr
        if 有限数值(数据['durationMs'],f'{标签} durationMs')<0:#负时长
            raise 会话格式错误(f'{标签} durationMs must be non-negative')#错误
        return#结束
    if 类型=='llm/retry':#LLM重试
        非空串(数据['retryId'],f'{标签} retryId')#重试id
        坐标对(数据,标签)#坐标
        非空串(数据['provider'],f'{标签} provider')#提供方
        字面值(数据['mode'],['normal','always'],f'{标签} mode')#模式
        非空串(数据['policyKey'],f'{标签} policyKey')#策略键
        正整数值(数据['retry'],f'{标签} retry')#重试次数
        if 数据['mode']=='normal':#普通模式
            最大重试=正整数值(数据['maxRetries'],f'{标签} maxRetries')#最大重试
            if 数据['retry']>最大重试:#超限
                raise 会话格式错误(f'{标签} retry exceeds maxRetries')#错误
        elif 'maxRetries' in 数据:#always却有maxRetries
            raise 会话格式错误(f'{标签} always mode must omit maxRetries')#错误
        延迟毫秒=有限数值(数据['delayMs'],f'{标签} delayMs')#延迟
        if 延迟毫秒<0:#负延迟
            raise 会话格式错误(f'{标签} delayMs must be non-negative')#错误
        if 延迟毫秒>2147483647:#超定时器范围
            raise 会话格式错误(f'{标签} delayMs exceeds the timer range')#错误
        llm失败值(数据['failure'],f'{标签} failure')#失败
        return#结束
    if 类型=='llm/retry-started':#LLM重试已开始
        非空串(数据['retryId'],f'{标签} retryId')#重试id
        坐标对(数据,标签)#坐标
        正整数值(数据['retry'],f'{标签} retry')#重试次数
        return#结束
    if 类型=='model/selection':#模型选择
        非空串(数据['provider'],f'{标签} provider')#提供方
        非空串(数据['model'],f'{标签} model')#模型
        if 'reasoningEffort' in 数据:#有推理力度
            非空串(数据['reasoningEffort'],f'{标签} reasoningEffort')#推理力度
        return#结束
    if 类型=='permission/preset':#权限预设
        非空串(数据['preset'],f'{标签} preset')#预设
        return#结束
    if 类型=='plan/mode':#计划模式
        布尔值(数据['active'],f'{标签} active')#激活
        return#结束
    if 类型=='request/context':#请求上下文
        非空串(数据['provider'],f'{标签} provider')#提供方
        非空串(数据['model'],f'{标签} model')#模型
        if 'contextWindow' in 数据:#有上下文窗
            正整数值(数据['contextWindow'],f'{标签} contextWindow')#上下文窗
        return#结束
    if 类型=='request/header':#请求头
        请求头值(数据['header'],f'{标签} header')#头
        字面值(数据['reason'],['initial','resume','change','series'],f'{标签} reason')#原因
        if 'startsSeries' in 数据:#有开系列
            字面值(数据['startsSeries'],[True],f'{标签} startsSeries')#开系列
        return#结束
    if 类型=='sandbox/mode':#沙盒模式
        字面值(数据['mode'],['read-only','workspace-write','danger-full-access'],f'{标签} mode')#模式
        if 'source' in 数据:#有来源
            字面值(数据['source'],['delegation'],f'{标签} source')#来源
        return#结束
    if 类型=='schedule/change':#日程变更
        日程变更值(数据,标签)#日程
        return#结束
    if 类型=='session-log-deepseek/delivery-accepted':#投递已接受
        接受版本=0 if 'sessionFormatVersion' not in 数据 else 计数值(数据['sessionFormatVersion'],f'{标签} sessionFormatVersion')#接受版本
        if 接受版本!=版本:#版本不符则跳过
            return#跳过
        非空串(数据['sessionId'],f'{标签} sessionId')#会话id
        更早序号(数据['throughSeq'],事件['seq'],f'{标签} throughSeq')#截止序号
        return#结束
    if 类型=='session/end-seed':#结束种子
        return#无载荷
    if 类型=='session/title':#会话标题
        非空串(数据['title'],f'{标签} title')#标题
        序号数组(数据['messageSeqs'],事件['seq'],f'{标签} messageSeqs',False)#消息序号
        标题源值(数据['source'],f'{标签} source')#源
        return#结束
    if 类型=='session/title-llm-request':#标题LLM请求
        非空串(数据['titleProvider'],f'{标签} titleProvider')#标题提供方
        序号数组(数据['messageSeqs'],事件['seq'],f'{标签} messageSeqs',True)#消息序号
        模型路由值(数据['route'],f'{标签} route')#路由
        字符串值(数据['system'],f'{标签} system')#系统
        def 校验标题消息(值,项标签):#校验标题请求消息
            消息值(值,f'{标签} message',版本)#消息
        数组值(数据['messages'],f'{标签} messages',校验标题消息)#消息
        正整数值(数据['maxTokens'],f'{标签} maxTokens')#上限
        return#结束
    if 类型 in ('step/end','step/start'):#步骤起止
        坐标对(数据,标签)#坐标
        return#结束
    if 类型=='subagent/descriptor':#子智能体描述符
        子智能体描述符值(数据,标签)#描述符
        return#结束
    if 类型=='subagent/model-selection-policy':#子智能体模型策略
        允许模型们值(数据['allowedModels'],f'{标签} allowedModels')#允许模型
        return#结束
    if 类型=='team/member':#团队成员
        团队选择器(数据,标签)#选择器
        团队成员值(数据['member'],f'{标签} member')#成员
        return#结束
    if 类型=='team/message/delivered':#团队消息已投递
        团队选择器(数据,标签)#选择器
        非空串(数据['messageId'],f'{标签} messageId')#消息id
        非空串(数据['targetId'],f'{标签} targetId')#目标id
        return#结束
    if 类型=='team/message/queued':#团队消息已排队
        团队选择器(数据,标签)#选择器
        团队消息值(数据['message'],f'{标签} message',版本)#消息
        return#结束
    if 类型=='team/task':#团队任务
        团队选择器(数据,标签)#选择器
        团队任务值(数据['task'],f'{标签} task')#任务
        return#结束
    if 类型=='todo/write':#待办写入
        def 校验待办(值,项标签):#校验待办项
            项=精确记录(值,项标签,['content','status'])#项
            字符串值(项['content'],f'{项标签} content')#内容
            字面值(项['status'],['pending','in_progress','completed'],f'{项标签} status')#状态
        数组值(数据['todos'],f'{标签} todos',校验待办)#待办
        return#结束
    if 类型=='tool-workflow/agent-end':#工具工作流智能体结束
        工作流身份(数据,标签)#身份
        字面值(数据['outcome'],['completed','failed','cancelled'],f'{标签} outcome')#结果
        return#结束
    if 类型=='tool-workflow/agent-start':#工具工作流智能体开始
        工作流身份(数据,标签)#身份
        字符串值(数据['label'],f'{标签} label')#标签字段
        if 'phase' in 数据:#有阶段
            字符串值(数据['phase'],f'{标签} phase')#阶段
        非空串(数据['childId'],f'{标签} childId')#子id
        return#结束
    if 类型=='tool-workflow/run-end':#工具工作流运行结束
        非空串(数据['runId'],f'{标签} runId')#运行id
        字面值(数据['stopReason'],['completed','cancelled','error'],f'{标签} stopReason')#停止原因
        return#结束
    if 类型=='tool-workflow/run-start':#工具工作流运行开始
        非空串(数据['runId'],f'{标签} runId')#运行id
        非空串(数据['name'],f'{标签} name')#名
        return#结束
    if 类型=='tool/call':#工具调用
        坐标对(数据,标签)#坐标
        非空串(数据['callId'],f'{标签} callId')#调用id
        非空串(数据['name'],f'{标签} name')#名
        字符串值(数据['arguments'],f'{标签} arguments')#参数
        return#结束
    if 类型 in ('tool/code-dispatch','tool/code-dispatch-start'):#工具代码分发
        非空串(数据['rootCallId'],f'{标签} rootCallId')#根调用
        非空串(数据['parentCallId'],f'{标签} parentCallId')#父调用
        非空串(数据['subCallId'],f'{标签} subCallId')#子调用
        非空串(数据['name'],f'{标签} name')#名
        if 类型=='tool/code-dispatch':#完整分发
            布尔值(数据['isError'],f'{标签} isError')#是否错误
            内容块们值(数据['content'],f'{标签} content',版本)#内容
        return#结束
    if 类型=='tool/result':#工具结果
        坐标对(数据,标签)#坐标
        消息值(数据['message'],f'{标签} message',版本,'tool')#消息
        if 'error' in 数据:#有错误
            错误=精确记录(数据['error'],f'{标签} error',['name','code'])#错误
            非空串(错误['name'],f'{标签} error name')#名
            非空串(错误['code'],f'{标签} error code')#码
        return#结束
    if 类型=='turn/end':#回合结束
        计数值(数据['turn'],f'{标签} turn')#回合
        回合结束原因值(数据['reason'],f'{标签} reason')#原因
        return#结束
    if 类型=='turn/start':#回合开始
        计数值(数据['turn'],f'{标签} turn')#回合
        return#结束
    if 类型=='user/message':#用户消息
        消息值(数据,标签,版本,'user')#消息
        return#结束
    if 类型=='web/deepseek-search-llm-request':#web搜索LLM请求
        非空串(数据['endpoint'],f'{标签} endpoint')#端点
        非空串(数据['apiVersion'],f'{标签} apiVersion')#api版本
        深搜请求体值(数据['body'],f'{标签} body')#体
        return#结束
    raise 会话格式错误(f'released payload validator is missing event {json.dumps(类型,ensure_ascii=False)}')#未知类型

def 精确记录(值,标签,必填,可选=None):#精确记录
    """要求普通对象且键精确。"""
    if 可选 is None:#默认无可选
        可选=[]#空
    记录=已发布v0记录(值,标签)#记录
    断言已发布v0键(记录,必填,可选,标签)#精确键
    return 记录#返回

def 字符串值(值,标签):#字符串值
    """要求字符串。"""
    if not isinstance(值,str):#非串
        raise 会话格式错误(f'{标签} must be a string')#错误

def 非空串(值,标签):#非空串
    """要求非空字符串。"""
    if not isinstance(值,str) or len(值)==0:#空或非串
        raise 会话格式错误(f'{标签} must be a non-empty string')#错误

def 布尔值(值,标签):#布尔值
    """要求布尔。"""
    if not isinstance(值,bool):#非布尔
        raise 会话格式错误(f'{标签} must be a boolean')#错误

def 安全整数值(值,标签):#安全整数值
    """要求安全整数。"""
    return 会话格式安全整数(值,标签)#委托

def 计数值(值,标签):#计数值
    """要求非负安全整数。"""
    return 会话格式计数(值,标签)#委托

def 正整数值(值,标签):#正整数值
    """要求正计数。"""
    结果=计数值(值,标签)#计数
    if 结果==0:#非正
        raise 会话格式错误(f'{标签} must be positive')#错误
    return 结果#返回

def 有限数值(值,标签):#有限数值
    """要求有限数且排除负零。"""
    if (isinstance(值,bool) or not isinstance(值,(int,float))
            or not math.isfinite(值) or 是否负零(值)):#非法
        raise 会话格式错误(f'{标签} must be a finite number')#错误
    return 值#返回

def 字面值(值,允许,标签):#字面值
    """要求值落在允许集合。"""
    if not any(候选 is 值 or 候选==值 for 候选 in 允许):#不在集合
        raise 会话格式错误(f'{标签} must be one of {", ".join(map(str,允许))}')#错误

def 可空值(值,标签,校验):#可空值
    """null 放行，否则校验。"""
    if 值 is not None:#非null
        校验(值,标签)#校验

def 数组值(值,标签,校验):#数组值
    """要求数组并对每项校验。"""
    if not isinstance(值,list):#非数组
        raise 会话格式错误(f'{标签} must be an array')#错误
    for 下标,成员 in enumerate(值):#遍历
        校验(成员,f'{标签}[{下标}]')#校验成员
    return 值#返回

def 坐标对(数据,标签):#坐标对
    """要求 turn/step 计数。"""
    计数值(数据['turn'],f'{标签} turn')#回合
    计数值(数据['step'],f'{标签} step')#步骤

def 更早序号(值,事件序号,标签):#更早序号
    """要求严格早于当前事件的序号。"""
    序号=计数值(值,标签)#序号
    if 序号>=事件序号:#非更早
        raise 会话格式错误(f'{标签} must identify an earlier event')#错误
    return 序号#返回

def 序号数组(值,事件序号,标签,要求非空):#序号数组
    """要求互异的更早序号数组。"""
    已见=set()#已见
    def 校验成员(成员,成员标签):#校验成员
        序号=更早序号(成员,事件序号,成员标签)#更早
        if 序号 in 已见:#重复
            raise 会话格式错误(f'{标签} repeats seq {序号}')#错误
        已见.add(序号)#记入
    值们=数组值(值,标签,校验成员)#数组
    if 要求非空 and len(值们)==0:#须非空
        raise 会话格式错误(f'{标签} must be non-empty')#错误
    return 值们#返回

def llm失败值(值,标签):#llm失败值
    """校验 LLM 失败对象。"""
    失败=精确记录(值,标签,['message','code'],['status','providerRetryAfterMs','requestId'])#失败
    非空串(失败['message'],f'{标签} message')#消息
    非空串(失败['code'],f'{标签} code')#码
    if 'status' in 失败:#有状态
        状态=安全整数值(失败['status'],f'{标签} status')#状态
        if 状态<100 or 状态>599:#越界
            raise 会话格式错误(f'{标签} status must be 100 through 599')#错误
    if 'providerRetryAfterMs' in 失败 and 有限数值(失败['providerRetryAfterMs'],f'{标签} providerRetryAfterMs')<=0:#非正
        raise 会话格式错误(f'{标签} providerRetryAfterMs must be positive')#错误
    if 'requestId' in 失败:#有请求id
        非空串(失败['requestId'],f'{标签} requestId')#请求id

def 令牌用量值(值,标签):#令牌用量值
    """校验令牌用量对象。"""
    用量=精确记录(#用量
        值,#值
        标签,#标签
        ['inputTokens','outputTokens'],#必填
        ['totalTokens','cacheReadTokens','cacheWriteTokens','reasoningTokens'],#可选
    )#精确记录结束
    for 键 in 用量.keys():#各字段
        计数值(用量[键],f'{标签} {键}')#计数

def 内容块们值(值,标签,版本):#内容块们值
    """校验内容块数组。"""
    def 校验块(成员,成员标签):#校验内容块
        内容块值(成员,成员标签,版本)#内容块
    数组值(值,标签,校验块)#逐块

def 内容块值(值,标签,版本):#内容块值
    """校验单个内容块。"""
    块=已发布v0记录(值,标签)#块
    块类型=块.get('type')#块类型
    if 块类型 in ('text','reasoning'):#文本或推理
        断言已发布v0键(块,['type','text'],[],标签)#键
        字符串值(块['text'],f'{标签} text')#文本
        return#结束
    if 块类型=='image':#图像
        断言已发布v0键(块,['type','attachment'],[],标签)#键
        图像附件值(块['attachment'],f'{标签} attachment')#附件
        return#结束
    if 块类型=='tool-call':#工具调用
        断言已发布v0键(块,['type','id','name','arguments'],[],标签)#键
        非空串(块['id'],f'{标签} id')#id
        非空串(块['name'],f'{标签} name')#名
        字符串值(块['arguments'],f'{标签} arguments')#参数
        return#结束
    if 块类型=='tool-result':#工具结果
        断言已发布v0键(块,['type','toolCallId','content'],['isError'],标签)#键
        非空串(块['toolCallId'],f'{标签} toolCallId')#调用id
        内容块们值(块['content'],f'{标签} content',版本)#内容
        if 'isError' in 块:#有错误旗标
            布尔值(块['isError'],f'{标签} isError')#旗标
        return#结束
    非空串(块.get('type'),f'{标签} type')#未知类型仅要求非空type

def 图像附件值(值,标签):#图像附件值
    """校验图像附件引用。"""
    附件=精确记录(#附件
        值,#值
        标签,#标签
        ['attachmentId','mediaType','bytes','width','height'],#必填
        ['name','originalDimensions'],#可选
    )#精确记录结束
    非空串(附件['attachmentId'],f'{标签} attachmentId')#附件id
    字面值(附件['mediaType'],['image/png','image/jpeg','image/webp','image/gif'],f'{标签} mediaType')#媒体类型
    计数值(附件['bytes'],f'{标签} bytes')#字节
    正整数值(附件['width'],f'{标签} width')#宽
    正整数值(附件['height'],f'{标签} height')#高
    if 'name' in 附件:#有名
        字符串值(附件['name'],f'{标签} name')#名
    if 'originalDimensions' in 附件:#有原尺寸
        尺寸=精确记录(附件['originalDimensions'],f'{标签} originalDimensions',['width','height'])#尺寸
        正整数值(尺寸['width'],f'{标签} original width')#原宽
        正整数值(尺寸['height'],f'{标签} original height')#原高

def 消息值(值,标签,版本,期望=None):#消息值
    """校验消息信封。"""
    消息=精确记录(值,标签,['id','role','content','source'])#消息
    非空串(消息['id'],f'{标签} id')#id
    if 期望=='assistant':#助手
        角色='assistant'#角色
    elif 期望 in ('user','tool'):#用户或工具
        角色='user'#角色
    else:#任意
        角色=None#任意
    if 角色 is None:#任意角色
        字面值(消息['role'],['system','user','assistant'],f'{标签} role')#角色
    else:#固定角色
        字面值(消息['role'],[角色],f'{标签} role')#角色
    内容块们值(消息['content'],f'{标签} content',版本)#内容
    消息源值(消息['source'],f'{标签} source',版本,期望)#源
    if 期望=='tool':#工具消息
        内容=消息['content']#内容
        块=已发布v0记录(内容[0],f'{标签} tool result') if isinstance(内容,list) and len(内容)==1 else None#单块
        源=已发布v0记录(消息['source'],f'{标签} source')#源
        if 块 is None or 块.get('type')!='tool-result' or 块.get('toolCallId')!=源.get('callId'):#形态不符
            raise 会话格式错误(f'{标签} must contain exactly one tool-result block')#错误

def 消息源值(值,标签,版本,期望=None):#消息源值
    """校验消息出处。"""
    源=已发布v0记录(值,标签)#源
    if 期望=='assistant' and 源.get('kind')!='model':#须模型源
        raise 会话格式错误(f'{标签} must be model source')#错误
    if 期望=='tool' and 源.get('kind')!='tool':#须工具源
        raise 会话格式错误(f'{标签} must be tool source')#错误
    种=源.get('kind')#种
    if 种=='user':#用户
        断言已发布v0键(源,['kind'],['rpcId','clientTimeZone'],标签)#键
        if 'rpcId' in 源:#有rpc
            非空串(源['rpcId'],f'{标签} rpcId')#rpc
        if 'clientTimeZone' in 源:#有时区
            非空串(源['clientTimeZone'],f'{标签} clientTimeZone')#时区
        return#结束
    if 种=='plugin':#插件
        插件源值(源,标签)#插件
        return#结束
    if 种=='model':#模型
        断言已发布v0键(源,['kind','provider','model'],['replayState'],标签)#键
        非空串(源['provider'],f'{标签} provider')#提供方
        非空串(源['model'],f'{标签} model')#模型
        return#结束
    if 种=='tool':#工具
        断言已发布v0键(源,['kind','callId'],[],标签)#键
        非空串(源['callId'],f'{标签} callId')#调用id
        return#结束
    if 种=='agent-instructions':#智能体指令
        断言已发布v0键(源,['kind','form','changes'],['baseline','baselineIdentity'],标签)#键
        字面值(源['form'],['instructions'],f'{标签} form')#形态
        if 'baseline' in 源:#有基线
            字面值(源['baseline'],[True],f'{标签} baseline')#基线
        if 'baselineIdentity' in 源:#有基线身份
            非空串(源['baselineIdentity'],f'{标签} baselineIdentity')#基线身份
        def 校验变更(成员,成员标签):#校验变更
            变更=精确记录(成员,成员标签,['action','scope','path'],['digest'])#变更
            字面值(变更['action'],['set','replace','remove'],f'{成员标签} action')#动作
            字符串值(变更['scope'],f'{成员标签} scope')#作用域
            字符串值(变更['path'],f'{成员标签} path')#路径
            if 'digest' in 变更:#有摘要
                字符串值(变更['digest'],f'{成员标签} digest')#摘要
        数组值(源['changes'],f'{标签} changes',校验变更)#变更
        return#结束
    if 种=='session-reference':#会话引用
        会话引用源值(源,标签,版本)#引用
        return#结束
    if 种=='team-message':#团队消息
        断言已发布v0键(源,['kind','teamId','messageId','senderId','senderName'],[],标签)#键
        for 键 in ('teamId','messageId','senderId'):#必填串
            非空串(源[键],f'{标签} {键}')#串
        字符串值(源['senderName'],f'{标签} senderName')#发送者名
        return#结束
    if 种=='goal':#目标
        断言已发布v0键(源,['kind','goalId','revision','round'],[],标签)#键
        非空串(源['goalId'],f'{标签} goalId')#目标id
        正整数值(源['revision'],f'{标签} revision')#修订
        正整数值(源['round'],f'{标签} round')#轮次
        return#结束
    if 种=='skill-invocation':#技能调用
        断言已发布v0键(源,['kind','name','form'],[],标签)#键
        非空串(源['name'],f'{标签} name')#名
        字面值(源['form'],['instructions'],f'{标签} form')#形态
        return#结束
    if 种=='skill-catalog':#技能目录
        断言已发布v0键(源,['kind','form','entries'],['update'],标签)#键
        字面值(源['form'],['catalog'],f'{标签} form')#形态
        if 'update' in 源:#有更新
            字面值(源['update'],[True],f'{标签} update')#更新
        def 校验条目(成员,成员标签):#校验条目
            条目=精确记录(成员,成员标签,['name','description'])#条目
            非空串(条目['name'],f'{成员标签} name')#名
            字符串值(条目['description'],f'{成员标签} description')#描述
        数组值(源['entries'],f'{标签} entries',校验条目)#条目
        return#结束
    if 种 in ('coordinator','subagent-report'):#协调器或子智能体报告
        断言已发布v0键(源,['kind','form','senderSessionId'],[],标签)#键
        字面值(源['form'],['relay'],f'{标签} form')#形态
        非空串(源['senderSessionId'],f'{标签} senderSessionId')#发送会话
        return#结束
    if 种=='subagent-settled':#子智能体已结算
        断言已发布v0键(源,['kind','form','summary','senderSessionId'],[],标签)#键
        字面值(源['form'],['notice'],f'{标签} form')#形态
        字符串值(源['summary'],f'{标签} summary')#摘要
        非空串(源['senderSessionId'],f'{标签} senderSessionId')#发送会话
        return#结束
    if 种=='webhook':#webhook
        断言已发布v0键(源,['kind','provider','source','deliveryId','ruleId','form','summary'],[],标签)#键
        for 键 in ('provider','source','deliveryId','ruleId'):#必填串
            非空串(源[键],f'{标签} {键}')#串
        字面值(源['form'],['notice'],f'{标签} form')#形态
        字符串值(源['summary'],f'{标签} summary')#摘要
        return#结束
    非空串(源.get('kind'),f'{标签} kind')#未知种仅要求非空

def 插件源值(源,标签):#插件源值
    """校验插件出处。"""
    可选=['form','sections','summary']#可选
    if 源.get('plugin')=='compact':#压缩插件
        可选=可选+['compactionId','sourceCommandId']#追加
    断言已发布v0键(源,['kind','plugin'],可选,标签)#键
    非空串(源['plugin'],f'{标签} plugin')#插件
    if 源.get('plugin')=='compact':#压缩
        非空串(源['compactionId'],f'{标签} compactionId')#压缩id
        if 'sourceCommandId' in 源:#有源命令
            非空串(源['sourceCommandId'],f'{标签} sourceCommandId')#源命令
    if 'form' not in 源:#无形态
        return#结束
    形态=源['form']#形态
    字面值(形态,['instructions','catalog','snapshot','notice','relay','recall'],f'{标签} form')#形态
    if 形态=='snapshot':#快照
        def 校验节(成员,成员标签):#校验节
            节=精确记录(成员,成员标签,['name','text'])#节
            非空串(节['name'],f'{成员标签} name')#名
            字符串值(节['text'],f'{成员标签} text')#文本
        数组值(源['sections'],f'{标签} sections',校验节)#节
    elif 'sections' in 源:#非快照却有节
        raise 会话格式错误(f'{标签} sections require snapshot form')#错误
    if 形态=='notice':#通知
        字符串值(源['summary'],f'{标签} summary')#摘要
    elif 'summary' in 源:#非通知却有摘要
        raise 会话格式错误(f'{标签} summary requires notice form')#错误

def 会话引用源值(源,标签,版本):#会话引用源值
    """校验会话引用出处。"""
    断言已发布v0键(源,['kind','form','version','references'],[],标签)#键
    字面值(源['form'],['recall'],f'{标签} form')#形态
    字面值(源['version'],[1],f'{标签} version')#版本
    期望输入下标=0#期望下标
    会话ids=set()#会话id集
    def 校验引用(成员,成员标签):#校验引用
        nonlocal 期望输入下标#可变
        引用=精确记录(#引用
            成员,#成员
            成员标签,#标签
            ['sessionId','label','capturedThroughSeq','compacted','originalMessages',
             'retainedMessages','omittedMessages','omittedBytes','truncated','inputIndex'],#必填
            ['capturedFormatVersion'] if 版本>=1 else [],#可选
        )#精确记录结束
        非空串(引用['sessionId'],f'{成员标签} sessionId')#会话id
        字符串值(引用['label'],f'{成员标签} label')#标签
        if 引用['capturedThroughSeq'] is not None:#有截止序号
            计数值(引用['capturedThroughSeq'],f'{成员标签} capturedThroughSeq')#截止
        if 'capturedFormatVersion' in 引用:#有捕获格式版本
            捕获版本=计数值(引用['capturedFormatVersion'],f'{成员标签} capturedFormatVersion')#捕获版本
            if 捕获版本<1 or 捕获版本>版本:#越界
                raise 会话格式错误(f'{成员标签} capturedFormatVersion must be between 1 and {版本}')#错误
        布尔值(引用['compacted'],f'{成员标签} compacted')#已压缩
        原始=计数值(引用['originalMessages'],f'{成员标签} originalMessages')#原始
        保留=计数值(引用['retainedMessages'],f'{成员标签} retainedMessages')#保留
        省略=计数值(引用['omittedMessages'],f'{成员标签} omittedMessages')#省略
        省略字节=计数值(引用['omittedBytes'],f'{成员标签} omittedBytes')#省略字节
        输入下标=计数值(引用['inputIndex'],f'{成员标签} inputIndex')#输入下标
        截断=引用['truncated']#截断
        布尔值(截断,f'{成员标签} truncated')#截断
        if 保留>原始 or 省略!=原始-保留:#计数不一致
            raise 会话格式错误(f'{成员标签} message counts are inconsistent')#错误
        if 截断!=(省略>0 or 省略字节>0):#截断不一致
            raise 会话格式错误(f'{成员标签} truncated disagrees with omitted content')#错误
        if 输入下标!=期望输入下标:#下标不符
            raise 会话格式错误(f'{标签} inputIndex must match reference position')#错误
        期望输入下标+=1#前进
        会话id=引用['sessionId']#会话id
        if 会话id in 会话ids:#重复
            raise 会话格式错误(f'{标签} repeats sessionId {会话id}')#错误
        会话ids.add(会话id)#记入
    引用们=数组值(源['references'],f'{标签} references',校验引用)#引用
    if len(引用们)==0:#须非空
        raise 会话格式错误(f'{标签} references must be non-empty')#错误

def 流块值(值,标签):#流块值
    """校验助手流块。"""
    块=已发布v0记录(值,标签)#块
    块类型=块.get('type')#类型
    if 块类型=='block-start':#块开始
        断言已发布v0键(块,['type','index','blockType'],[],标签)#键
        计数值(块['index'],f'{标签} index')#索引
        非空串(块['blockType'],f'{标签} blockType')#块类型
        return#结束
    if 块类型 in ('text-delta','reasoning-delta'):#文本或推理增量
        断言已发布v0键(块,['type','index','text'],[],标签)#键
        计数值(块['index'],f'{标签} index')#索引
        字符串值(块['text'],f'{标签} text')#文本
        return#结束
    if 块类型=='tool-call-delta':#工具调用增量
        断言已发布v0键(块,['type','index','id','argumentsDelta'],['name'],标签)#键
        计数值(块['index'],f'{标签} index')#索引
        非空串(块['id'],f'{标签} id')#id
        if 'name' in 块:#有名
            字符串值(块['name'],f'{标签} name')#名
        字符串值(块['argumentsDelta'],f'{标签} argumentsDelta')#参数增量
        return#结束
    if 块类型=='block-end':#块结束
        断言已发布v0键(块,['type','index','block'],[],标签)#键
        计数值(块['index'],f'{标签} index')#索引
        内容块值(块['block'],f'{标签} block',1)#块
        return#结束
    if 块类型=='usage':#用量
        断言已发布v0键(块,['type','usage'],[],标签)#键
        令牌用量值(块['usage'],f'{标签} usage')#用量
        return#结束
    if 块类型=='finish':#结束
        断言已发布v0键(块,['type','reason'],['replayState'],标签)#键
        结束原因值(块['reason'],f'{标签} reason')#原因
        if 'replayState' in 块:#有重放状态
            重放信封值(块['replayState'],f'{标签} replayState')#重放
        return#结束
    raise 会话格式错误(f'{标签} has unknown stream chunk type {json.dumps(块.get("type"),ensure_ascii=False)}')#未知

def 结束原因值(值,标签):#结束原因值
    """校验流结束原因。"""
    原因=已发布v0记录(值,标签)#原因
    if 原因.get('kind') in ('aborted','error'):#中止或错误
        断言已发布v0键(原因,['kind','failure'],[],标签)#键
        llm失败值(原因['failure'],f'{标签} failure')#失败
        return#结束
    if 原因.get('kind') in ('stop','tool-calls','max-tokens'):#简单种
        断言已发布v0键(原因,['kind'],[],标签)#仅kind
    非空串(原因.get('kind'),f'{标签} kind')#种

def 重放信封值(值,标签):#重放信封值
    """校验重放状态信封。"""
    重放=精确记录(值,标签,['response'],['blocks'])#重放
    if 'blocks' in 重放 and not isinstance(重放['blocks'],list):#blocks非数组
        raise 会话格式错误(f'{标签} blocks must be an array')#错误

def 回合结束原因值(值,标签):#回合结束原因值
    """校验 turn/end 原因。"""
    原因=已发布v0记录(值,标签)#原因
    种=原因.get('kind')#种
    if 种 in ('completed','blocked','max-tokens','interrupted'):#简单种
        断言已发布v0键(原因,['kind'],[],标签)#仅kind
        return#结束
    if 种=='aborted':#中止
        断言已发布v0键(原因,['kind','reason'],[],标签)#键
        起因=已发布v0记录(原因['reason'],f'{标签} abort cause')#起因
        if 起因.get('kind')=='hook':#钩子
            断言已发布v0键(起因,['kind','reason'],[],f'{标签} abort cause')#键
            字符串值(起因['reason'],f'{标签} abort reason')#原因
        else:#其它
            断言已发布v0键(起因,['kind'],[],f'{标签} abort cause')#键
            字面值(起因['kind'],['user','parent','disposed','legacy'],f'{标签} abort kind')#种
        return#结束
    if 种=='error':#错误
        断言已发布v0键(原因,['kind','error'],[],标签)#键
        llm失败值(原因['error'],f'{标签} error')#错误
        return#结束
    非空串(原因.get('kind'),f'{标签} kind')#未知种

def 请求头值(值,标签):#请求头值
    """校验 request/header 内层头。"""
    头=精确记录(值,标签,['config'],['adapterDefaults','system','tools'])#头
    配置=精确记录(#配置
        头['config'],#配置
        f'{标签} config',#标签
        ['provider','model'],#必填
        ['reasoningEffort','temperature','maxTokens','stop'],#可选
    )#精确记录结束
    非空串(配置['provider'],f'{标签} provider')#提供方
    非空串(配置['model'],f'{标签} model')#模型
    if 'reasoningEffort' in 配置:#有推理力度
        非空串(配置['reasoningEffort'],f'{标签} reasoningEffort')#推理力度
    if 'temperature' in 配置:#有温度
        有限数值(配置['temperature'],f'{标签} temperature')#温度
    if 'maxTokens' in 配置:#有上限
        正整数值(配置['maxTokens'],f'{标签} maxTokens')#上限
    if 'stop' in 配置:#有停止
        数组值(配置['stop'],f'{标签} stop',字符串值)#停止
    if 'adapterDefaults' in 头:#有适配器默认
        默认=精确记录(头['adapterDefaults'],f'{标签} adapterDefaults',[],['reasoningEffort','maxTokens'])#默认
        for 键,标记 in 默认.items():#逐项
            字面值(标记,[True],f'{标签} adapterDefaults {键}')#标记
            if 键 not in 配置:#缺配置值
                raise 会话格式错误(f'{标签} adapter default {键} lacks config value')#错误
    if 'system' in 头:#有系统
        字符串值(头['system'],f'{标签} system')#系统
    if 'tools' in 头:#有工具
        数组值(头['tools'],f'{标签} tools',工具模式值)#工具

def 工具模式值(值,标签):#工具模式值
    """校验工具 schema。"""
    模式=精确记录(值,标签,['name','description','parameters'])#模式
    非空串(模式['name'],f'{标签} name')#名
    字符串值(模式['description'],f'{标签} description')#描述
    已发布v0记录(模式['parameters'],f'{标签} parameters')#参数对象

def 遮蔽值(数据,事件序号,标签):#遮蔽值
    """校验压缩遮蔽范围与序号。"""
    范围=精确记录(数据['shadowedRange'],f'{标签} shadowedRange',['start','end'])#范围
    起点=更早序号(范围['start'],事件序号,f'{标签} shadowedRange start')#起点
    终点=更早序号(范围['end'],事件序号,f'{标签} shadowedRange end')#终点
    序号们=序号数组(数据['shadowedSeqs'],事件序号,f'{标签} shadowedSeqs',True)#序号
    if 序号们[0]!=起点 or 序号们[-1]!=终点:#端点不符
        raise 会话格式错误(f'{标签} shadowedRange must match shadowedSeqs endpoints')#错误
    计数值(数据['shadowedTokenCount'],f'{标签} shadowedTokenCount')#令牌数

def 目标变更值(数据,标签):#目标变更值
    """校验 goal/change 载荷。"""
    字面值(数据['kind'],['goal/change'],f'{标签} kind')#种
    字面值(数据['version'],[1],f'{标签} version')#版本
    if 数据.get('operation')=='clear':#清除
        断言已发布v0键(数据,['kind','version','operation','cleared','clearedAt'],[],f'{标签} data')#键
        目标引用值(数据['cleared'],f'{标签} cleared')#已清
        计数值(数据['clearedAt'],f'{标签} clearedAt')#清除时
        return#结束
    断言已发布v0键(#键
        数据,#数据
        ['kind','version','operation','goal','roundsStarted','createdAt','updatedAt'],#必填
        [],#可选空
        f'{标签} data',#标签
    )#断言结束
    字面值(数据['operation'],['create','edit','pause','resume','complete','block'],f'{标签} operation')#操作
    目标快照值(数据['goal'],f'{标签} goal')#目标
    计数值(数据['roundsStarted'],f'{标签} roundsStarted')#已开轮
    计数值(数据['createdAt'],f'{标签} createdAt')#创建
    计数值(数据['updatedAt'],f'{标签} updatedAt')#更新

def 目标引用值(值,标签):#目标引用值
    """校验目标引用。"""
    引用=精确记录(值,标签,['id','revision'])#引用
    非空串(引用['id'],f'{标签} id')#id
    正整数值(引用['revision'],f'{标签} revision')#修订

def 目标快照值(值,标签):#目标快照值
    """校验目标快照。"""
    目标=精确记录(值,标签,['id','revision','objective','phase','maxGoalRounds'],['blockedReason'])#目标
    非空串(目标['id'],f'{标签} id')#id
    正整数值(目标['revision'],f'{标签} revision')#修订
    非空串(目标['objective'],f'{标签} objective')#目标文本
    字面值(目标['phase'],['active','paused','blocked','complete'],f'{标签} phase')#阶段
    正整数值(目标['maxGoalRounds'],f'{标签} maxGoalRounds')#最大轮
    if 目标.get('phase')=='blocked':#阻塞
        原因=精确记录(目标['blockedReason'],f'{标签} blockedReason',['code','message'])#原因
        非空串(原因['code'],f'{标签} blocked code')#码
        非空串(原因['message'],f'{标签} blocked message')#消息
    elif 'blockedReason' in 目标:#非阻塞却有原因
        raise 会话格式错误(f'{标签} blockedReason requires blocked phase')#错误

def 日程变更值(数据,标签):#日程变更值
    """校验 schedule/change 载荷。"""
    字面值(数据['version'],[1],f'{标签} version')#版本
    if 数据.get('operation')=='create':#创建
        断言已发布v0键(数据,['version','operation','schedule'],[],f'{标签} data')#键
        日程记录值(数据['schedule'],f'{标签} schedule')#日程
        return#结束
    断言已发布v0键(#键
        数据,#数据
        ['version','operation','id'],#必填
        ['acceptedAt'] if 数据.get('operation')=='dispatch' else [],#可选
        f'{标签} data',#标签
    )#断言结束
    字面值(数据['operation'],['delete','dispatch'],f'{标签} operation')#操作
    日程id值(数据['id'],f'{标签} id')#id
    if 'acceptedAt' in 数据:#有接受时
        瞬时值(数据['acceptedAt'],f'{标签} acceptedAt')#瞬时

def 日程记录值(值,标签):#日程记录值
    """校验日程记录。"""
    记录=已发布v0记录(值,标签)#记录
    if 记录.get('kind')=='after':#延后
        断言已发布v0键(记录,['id','kind','prompt','afterSeconds','scheduledAt'],[],标签)#键
        正整数值(记录['afterSeconds'],f'{标签} afterSeconds')#秒
    elif 记录.get('kind')=='at':#定点
        断言已发布v0键(记录,['id','kind','prompt','scheduledAt'],[],标签)#键
    elif 记录.get('kind')=='every':#周期
        断言已发布v0键(记录,['id','kind','prompt','everySeconds','scheduledAt'],[],标签)#键
        秒=正整数值(记录['everySeconds'],f'{标签} everySeconds')#秒
        if 秒<300:#过短
            raise 会话格式错误(f'{标签} everySeconds must be at least 300')#错误
    else:#未知种
        raise 会话格式错误(f'{标签} has unknown schedule kind')#错误
    日程id值(记录['id'],f'{标签} id')#id
    非空串(记录['prompt'],f'{标签} prompt')#提示
    瞬时值(记录['scheduledAt'],f'{标签} scheduledAt')#计划时

def 日程id值(值,标签):#日程id值
    """校验日程id无首尾空白。"""
    非空串(值,标签)#非空
    if 值.strip()!=值:#有空白
        raise 会话格式错误(f'{标签} must not have surrounding whitespace')#错误

def 瞬时值(值,标签):#瞬时值
    """要求规范 UTC 瞬时字符串。"""
    if not isinstance(值,str) or UTC瞬时正则.fullmatch(值) is None:#形态不符
        raise 会话格式错误(f'{标签} must be a canonical UTC instant')#错误
    try:#解析
        解析=datetime.fromisoformat(值.replace('Z','+00:00'))#解析
    except ValueError:#解析失败
        raise 会话格式错误(f'{标签} must be a canonical UTC instant')#错误
    try:#时间戳
        if not math.isfinite(解析.timestamp()):#非有限
            raise 会话格式错误(f'{标签} must be a canonical UTC instant')#错误
    except (OverflowError,OSError,ValueError):#平台溢出
        raise 会话格式错误(f'{标签} must be a canonical UTC instant')#错误
    规范=解析.astimezone(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00','Z')#规范
    if 规范!=值:#非规范
        raise 会话格式错误(f'{标签} must be a canonical UTC instant')#错误

def 标题源值(值,标签):#标题源值
    """校验标题出处。"""
    源=已发布v0记录(值,标签)#源
    if 源.get('kind')=='provider':#提供方
        断言已发布v0键(源,['kind','provider'],['model'],标签)#键
        非空串(源['provider'],f'{标签} provider')#提供方
        if 'model' in 源:#有模型
            模型路由值(源['model'],f'{标签} model')#模型
        return#结束
    断言已发布v0键(源,['kind'],[],标签)#仅kind
    字面值(源['kind'],['fallback','user'],f'{标签} kind')#种

def 模型路由值(值,标签):#模型路由值
    """校验模型路由。"""
    路由=精确记录(值,标签,['provider','model'])#路由
    非空串(路由['provider'],f'{标签} provider')#提供方
    非空串(路由['model'],f'{标签} model')#模型

def 子智能体描述符值(数据,标签):#子智能体描述符值
    """校验子智能体描述符。"""
    字面值(数据['version'],[3],f'{标签} version')#版本
    非空串(数据['provider'],f'{标签} provider')#提供方
    if 数据.get('mode')=='one-shot':#一次性
        断言已发布v0键(数据,['mode','version','provider'],['label'],f'{标签} data')#键
        if 'label' in 数据:#有标签
            字符串值(数据['label'],f'{标签} label')#标签
        return#结束
    字面值(数据['mode'],['continuable'],f'{标签} mode')#模式
    非空串(数据['label'],f'{标签} label')#标签
    for 键 in ('agentProvider','agentModel','agentReasoningEffort','persona'):#可选串
        if 键 in 数据:#有该键
            非空串(数据[键],f'{标签} {键}')#串
    if ('agentProvider' in 数据)!=('agentModel' in 数据):#须成对
        raise 会话格式错误(f'{标签} agentProvider and agentModel must be paired')#错误
    if 'toolFilter' in 数据:#有工具过滤
        过滤=精确记录(数据['toolFilter'],f'{标签} toolFilter',[],['allow','deny'])#过滤
        if 'allow' not in 过滤 and 'deny' not in 过滤:#缺一边
            raise 会话格式错误(f'{标签} toolFilter requires allow or deny')#错误
        if 'allow' in 过滤:#有允许
            数组值(过滤['allow'],f'{标签} allow',非空串)#允许
        if 'deny' in 过滤:#有拒绝
            数组值(过滤['deny'],f'{标签} deny',非空串)#拒绝

def 允许模型们值(值,标签):#允许模型们值
    """校验允许模型路由表。"""
    已见=set()#已见
    def 校验路由(成员,成员标签):#校验路由
        路由=精确记录(成员,成员标签,['provider','model'])#路由
        非空串(路由['provider'],f'{成员标签} provider')#提供方
        非空串(路由['model'],f'{成员标签} model')#模型
        键=f"{路由['provider']}\0{路由['model']}"#键
        if 键 in 已见:#重复
            raise 会话格式错误(f'{标签} repeats route {键}')#错误
        已见.add(键)#记入
    路由们=数组值(值,标签,校验路由)#路由
    if len(路由们)==0:#须非空
        raise 会话格式错误(f'{标签} must be non-empty')#错误

def 团队选择器(数据,标签):#团队选择器
    """校验团队选择字段。"""
    字面值(数据['version'],[1],f'{标签} version')#版本
    非空串(数据['teamId'],f'{标签} teamId')#团队id

def 团队成员值(值,标签):#团队成员值
    """校验团队成员。"""
    成员=精确记录(值,标签,['id','name','description','provider','context','phase'],['error'])#成员
    非空串(成员['id'],f'{标签} id')#id
    字符串值(成员['name'],f'{标签} name')#名
    字符串值(成员['description'],f'{标签} description')#描述
    字符串值(成员['provider'],f'{标签} provider')#提供方
    字面值(成员['context'],['fresh','fork'],f'{标签} context')#上下文
    字面值(成员['phase'],['provisioning','active','failed'],f'{标签} phase')#阶段
    if 'error' in 成员:#有错误
        字符串值(成员['error'],f'{标签} error')#错误

def 团队任务值(值,标签):#团队任务值
    """校验团队任务。"""
    任务=精确记录(#任务
        值,#值
        标签,#标签
        ['id','revision','subject','description','status','blockedBy','writeScopes'],#必填
        ['ownerId'],#可选
    )#精确记录结束
    非空串(任务['id'],f'{标签} id')#id
    正整数值(任务['revision'],f'{标签} revision')#修订
    字符串值(任务['subject'],f'{标签} subject')#主题
    字符串值(任务['description'],f'{标签} description')#描述
    字面值(任务['status'],['pending','in_progress','completed','deleted'],f'{标签} status')#状态
    if 'ownerId' in 任务:#有所有者
        非空串(任务['ownerId'],f'{标签} ownerId')#所有者
    数组值(任务['blockedBy'],f'{标签} blockedBy',非空串)#阻塞
    数组值(任务['writeScopes'],f'{标签} writeScopes',字符串值)#写作用域

def 团队消息值(值,标签,版本):#团队消息值
    """校验团队消息。"""
    消息=精确记录(值,标签,['id','senderId','senderName','targetId','delivery','content'])#消息
    for 键 in ('id','senderId','targetId'):#必填串
        非空串(消息[键],f'{标签} {键}')#串
    字符串值(消息['senderName'],f'{标签} senderName')#发送者名
    字面值(消息['delivery'],['quiet','wakeup'],f'{标签} delivery')#投递
    内容块们值(消息['content'],f'{标签} content',版本)#内容

def 工作流身份(数据,标签):#工作流身份
    """校验工具工作流身份字段。"""
    非空串(数据['runId'],f'{标签} runId')#运行id
    正整数值(数据['seq'],f'{标签} seq')#序号

def 深搜请求体值(值,标签):#深搜请求体值
    """校验 DeepSeek 搜索 LLM 请求体。"""
    体=精确记录(值,标签,['model','max_tokens','messages','tools'])#体
    非空串(体['model'],f'{标签} model')#模型
    正整数值(体['max_tokens'],f'{标签} max_tokens')#上限
    def 校验消息(成员,成员标签):#校验消息
        消息=精确记录(成员,成员标签,['role','content'])#消息
        字面值(消息['role'],['user'],f'{成员标签} role')#角色
        def 校验块(块,块标签):#校验块
            文本=精确记录(块,块标签,['type','text'])#文本
            字面值(文本['type'],['text'],f'{块标签} type')#类型
            字符串值(文本['text'],f'{块标签} text')#文本
        内容=数组值(消息['content'],f'{成员标签} content',校验块)#内容
        if len(内容)!=1:#须单块
            raise 会话格式错误(f'{成员标签} content must contain one text block')#错误
    消息们=数组值(体['messages'],f'{标签} messages',校验消息)#消息
    if len(消息们)!=1:#须单消息
        raise 会话格式错误(f'{标签} messages must contain one user message')#错误
    def 校验工具(成员,成员标签):#校验工具
        工具=精确记录(成员,成员标签,['type','name','max_uses'])#工具
        字面值(工具['type'],['web_search_20250305'],f'{成员标签} type')#类型
        字面值(工具['name'],['web_search'],f'{成员标签} name')#名
        正整数值(工具['max_uses'],f'{成员标签} max_uses')#最大使用
    工具们=数组值(体['tools'],f'{标签} tools',校验工具)#工具
    if len(工具们)!=1:#须单工具
        raise 会话格式错误(f'{标签} tools must contain one web search tool')#错误
