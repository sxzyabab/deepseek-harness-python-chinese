"""默认一次性摘要与耐久检查点装帧。"""
from ...依赖 import cordis#外部依赖胶水
是否thenable=cordis.工具.是否thenable#可等待判定
from ..llm import (#导入 LLM 词汇
    内容含图片,#图像判断
    创建用户消息,#用户消息工厂
    块组装器,#流式块组装
    语言模型错误,#LLM 错误
)#LLM 包

摘要开标签='<compacted-summary>'#落地检查点节点里包裹结构化摘要的开标签
摘要闭标签='</compacted-summary>'#落地检查点节点里包裹结构化摘要的闭标签

压缩指令='\n'.join([#摘要指令各行；作为重放对话之后的最后一条用户消息投递
    'You are now acting as a compaction engine for this AI coding assistant. Condense the conversation ABOVE into a structured checkpoint that lets another model resume the work with no loss of essential context.',#角色与目标
    '',#空行
    'Output EXACTLY the Markdown structure below: keep every section, in order. Use terse bullets, not prose paragraphs. Write "(none)" for an empty section — never drop a section.',#强制结构
    '',#空行
    '## Primary Request and Intent',#主请求标题
    "- [the user's original and evolving goals; quote verbatim where the exact wording matters]",#主请求条目
    '',#空行
    '## Key Technical Concepts',#技术概念标题
    '- [technologies, frameworks, patterns, and conventions in play]',#技术概念条目
    '',#空行
    '## Files and Code',#文件与代码标题
    '- [exact path: why it matters, key changes or snippets]',#文件条目
    '',#空行
    '## Errors and Fixes',#错误与修复标题
    '- [error: how it was resolved, plus any related user feedback]',#错误条目
    '',#空行
    '## Pending Jobs',#未完成工作标题
    '- [explicitly requested work not yet completed]',#未完成条目
    '',#空行
    '## Current Work',#当前工作标题
    '- [precisely what was in progress at this checkpoint]',#当前工作条目
    '',#空行
    '## Next Step',#下一步标题
    '- [the single next action, directly in line with the most recent request, or "(none)"]',#下一步条目
    '',#空行
    '## Critical Context',#关键上下文标题
    '- [decisions and their rationale, constraints, user preferences, open questions, data needed to continue]',#关键上下文条目
    '',#空行
    'Rules:',#规则标题
    '- Write concise English engineering prose. Preserve exact file paths, commands, error strings, identifiers, numeric values, function signatures, and syntax fragments.',#保留精确字面量
    '- Capture user feedback and explicit instructions faithfully, especially corrections.',#忠实记录反馈
    '- Do NOT mention this summarization request or that the context was compacted.',#禁止提及摘要请求
    '- Output only the checkpoint text: do not call any tool or take any other action.',#只输出检查点文本
    '- If the conversation already contains a '+摘要开标签+' block, it is a PRIOR checkpoint. Do not copy it forward verbatim: preserve still-true facts, drop stale ones, and merge newer information into a single consolidated summary under the same structure.',#合并先前检查点
])#拼成单条指令

检查点前言=(#使替换用户消息成为既定上下文的装帧前言
    'This is an automatically generated checkpoint condensing an earlier span of the conversation to free up context. '
    'Treat the captured context as established background and build on it without restating it. '
    'Continue the task directly from the messages that follow, without acknowledging this checkpoint.'
)#前言正文

摘要输入字段=('system','tools','messages')#摘要器所压缩的重放对话表面字段
摘要结果字段=('summary','provider','model','maxTokens','usage','rawOutput','llmStreamCall')#安全摘要内容加上随它记录的精确辅助调用信封

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段，缺席为缺省。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 解开(值):#承诺则等待否则原样
    """承诺则等待，否则原样返回。"""
    if 是否thenable(值):#可等待
        return 值.等待()#等待承诺
    return 值#同步值

def 结束错误(结束):#把终端摘要结束原因映成失败关闭错误
    """结束原因 → 错误；正常完成则无。"""
    种类=取字段(结束,'kind')#结束类别
    if 种类=='error' or 种类=='aborted':#提供方错误或已取消
        失败=取字段(结束,'failure')#失败事实
        错误=Exception(取字段(失败,'message'))#带 message 的 Error
        错误.code=取字段(失败,'code')#保留失败码
        return 错误#返回错误
    if 种类=='max-tokens':#触达 token 上限
        错误=Exception('summarization truncated at the token cap (incomplete checkpoint)')#截断错误
        错误.code='MAX_TOKENS'#截断码
        return 错误#返回错误
    return None#正常完成无错误

def 摘要文本(块们):#拒绝视觉输出，合成用户消息前只保留文本
    """投影为纯文本块。"""
    if 内容含图片(块们):#含图像
        raise 语言模型错误('compaction summary cannot contain image output','UNSUPPORTED_CONTENT')#不支持图像摘要
    文本们=[]#仅 text 块
    for 块 in 块们:#逐块
        if 取字段(块,'type')=='text':#文本块
            文本们.append(块)#收下
    return 文本们#只留 text

def 装帧摘要(摘要):#把原始摘要块包进耐久检查点装帧
    """返回合成替换用户消息的内容：前言、开标签、摘要、闭标签。"""
    return [#前言、开标签、摘要、闭标签
        {'type':'text','text':检查点前言+'\n\n'+摘要开标签},#前言与开标签
        *摘要,#模型摘要块
        {'type':'text','text':摘要闭标签},#闭标签
    ]#装帧结束

def 经语言模型摘要(上下文,配置,输入,智能体,信号=None):#经 LLM 一次性摘要
    """跑默认的复用缓存 ctx.llm.stream() 摘要调用：重放对话前缀，再把压缩指令追加为最后一条用户消息。"""
    会话=取字段(智能体,'session')#目标会话
    请求头=会话.requestHeader() if hasattr(会话,'requestHeader') else 会话.请求头()#最近请求头
    最近头=取字段(请求头,'config')#最近一次已路由请求配置
    if len(取字段(配置,'summarizationProvider') or '')==0:#未配置摘要提供方
        已配置=None#则不强制覆盖
    else:#成对覆盖
        已配置={'provider':取字段(配置,'summarizationProvider'),'model':取字段(配置,'summarizationModel')}#成对
    选项=取字段(智能体,'options') or {}#智能体选项
    选项提供方=取字段(选项,'provider')#选项提供方
    选项模型=取字段(选项,'model')#选项模型
    if (选项提供方 is not None and len(选项提供方)>0#智能体选项有提供方
            and 选项模型 is not None and len(选项模型)>0):#有模型
        智能体目标={'provider':选项提供方,'model':选项模型}#用智能体选项
    else:#否则没有回退目标
        智能体目标=None#无
    目标=已配置 if 已配置 is not None else (最近头 if 最近头 is not None else 智能体目标)#配置优先，其次最近请求，再次智能体选项
    if 目标 is None:#三处都没有路由
        raise Exception(#无法摘要
            'no provider/model available for summarization: set both BasicCompactionConfig summarization fields, '
            +'route one request, or set both AgentOptions fields'#缺路由诊断
        )#抛出结束
    组装器=块组装器()#组装流式块
    消息们=list(取字段(输入,'messages') or [])+[创建用户消息({#重放消息加指令
        'content':[{'type':'text','text':压缩指令}],#指令文本
        'source':{'kind':'plugin','plugin':'dsh-compaction-basic'},#插件出处
    })]#messages 结束
    选项表={#一次性生成选项
        'provider':取字段(目标,'provider'),#提供方
        'model':取字段(目标,'model'),#模型
        'messages':消息们,#含指令的消息
        'maxTokens':取字段(配置,'maxTokens'),#生成上限
        'sessionId':取字段(取字段(智能体,'session'),'id'),#会话 id
        'purpose':'compaction',#调用目的
    }#options 基础
    if 取字段(输入,'system') is not None:#复用系统提示
        选项表['system']=取字段(输入,'system')#系统提示
    if 取字段(输入,'tools') is not None:#复用工具模式
        选项表['tools']=list(取字段(输入,'tools'))#工具模式副本
    if 信号 is not None:#转发取消
        选项表['signal']=信号#取消信号
    流=解开(上下文.llm.stream(选项表))#打开流；瀑布可能返回承诺
    for 块 in 流:#把流块推进组装器
        组装器.推入(块)#推进
    错误=结束错误(组装器.结束)#把结束原因映成错误
    if 错误 is not None:#失败则抛
        raise 错误#抛出
    原始输出=组装器.块列表()#完整提供方输出
    摘要=摘要文本(原始输出)#只留文本块
    if not any(len(取字段(块,'text','').strip())>0 for 块 in 摘要):#没有任何非空白文本
        raise Exception('summarization produced no text summary content')#空摘要失败
    结果={#已标记 LLM 调用结果
        'summary':摘要,#安全文本
        'rawOutput':原始输出,#完整输出
        'llmStreamCall':True,#走了 llm.stream
        'provider':选项表['provider'],#实际提供方
        'model':选项表['model'],#实际模型
        'maxTokens':取字段(配置,'maxTokens'),#生成上限
    }#结果基础
    if 组装器.用量 is not None:#有用量才写入
        结果['usage']=组装器.用量#用量
    return 结果#返回结束
