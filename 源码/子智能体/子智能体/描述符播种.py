import json#编码父 id 与结构化结果
from ...模型后端.llm.消息 import 创建用户消息,截上下文摘要#用户消息与通知摘要

__all__=[#仅中文公开名
    '创建智能体消息','附可续跑返回指引','创建结算消息',
]#公开面结束

def 智能体消息来源(发送方):
    '相邻智能体消息的耐久归属'
    return {'kind':'agent-message','form':'relay','senderSessionId':发送方.id}#来源

def 创建智能体消息(发送方,内容):
    '建造一条相邻智能体消息的模型可见与耐久表示'
    return 创建用户消息({#用户消息
        'content':[{'type':'text','text':'Agent '+str(发送方.id)+' sent a message: '},*内容],#前缀加正文
        'source':智能体消息来源(发送方),#归属
    })#消息

def 附可续跑返回指引(父标识,提示):
    '在可续跑子体的初始任务后追加返回指引'
    编码父=json.dumps(父标识)#JSON 字符串
    return [*提示,{#原任务加指引
        'type':'text',#文本
        'text':(
            'Your parent agent id is '+编码父+'. Before you finish, send your result to that agent with '
            +'send_message({ agent_id: '+编码父+', message: "<self-contained result>" }). The parent shares '
            +'your workspace but does not automatically receive your transcript, tool output, or reasoning. Send '
            +'earlier messages as well when a finding changes what the parent should do next; sending a message '
            +'does not end your turn.'
        ),#指引
    }]#块列表

def 结算摘要(子标识,停止原因,可续跑):
    '用父任务的词汇说明后台子体为何结束'
    主语='Background subagent '+str(子标识)#主语
    if 停止原因=='completed':#完成
        if 可续跑:#还能再收消息
            return 主语+' finished and will do no further work unless you send it more.'#可续跑
        return 主语+' finished. It cannot receive follow-up messages.'#外部
    if 停止原因=='aborted':#中止
        return 主语+' was stopped before it finished.'#中止
    if 停止原因=='max-tokens':#上限
        return 主语+' ran out of room before it finished.'#上限
    if 停止原因=='refusal':#拒绝
        return 主语+' declined the task.'#拒绝
    if 停止原因=='error':#失败
        return 主语+' failed before it finished.'#失败
    return 主语+' ended abnormally ('+str(停止原因)+') before it finished.'#未知终态

def 创建结算消息(子标识,终态,可续跑=True):
    '用子体非空收尾文本建造运行时自己的结算通知'
    摘要=结算摘要(子标识,终态['stopReason'],可续跑)#一行说明
    收尾文本=[]#只留非空文本块
    for 块 in 终态['output']:#逐块
        if isinstance(块,dict) and 块.get('type')=='text' and isinstance(块.get('text'),str) and len(块['text'])>0:#非空文本
            收尾文本.append(块)#收下
    内容=[{'type':'text','text':摘要}]#开头
    if len(收尾文本)==0:#没有收尾
        内容.append({'type':'text','text':'It left no closing message.'})#说明没有
    else:#有收尾
        内容.append({'type':'text','text':'Its closing message:'})#引导
        内容.extend(收尾文本)#原文
    if 'structured' in 终态 and 终态['structured'] is not None:#有结构化结果
        内容.append({'type':'text','text':'Structured result: '+json.dumps(终态['structured'])})#结构化
    if 'diagnostic' in 终态 and 终态['diagnostic'] is not None:#有诊断
        内容.append({'type':'text','text':终态['diagnostic']})#诊断
    return 创建用户消息({#通知
        'content':内容,#正文
        'source':{#运行时归属
            'kind':'subagent-settled',#种类
            'form':'notice',#通知
            'summary':截上下文摘要(摘要),#一行摘要
            'senderSessionId':子标识,#子体会话
        },#来源结束
    })#消息
