from ...模型后端.llm.标识构造 import 消息标识,调用标识
from ...模型后端.llm.消息 import 冻结消息

__all__=['工具未启动','工具结局未知','中断轮次关闭器']

工具未启动='TOOL_NOT_STARTED'#助手工具请求从未到达已记录调用开始时的恢复码
工具结局未知='TOOL_OUTCOME_UNKNOWN'#已记录工具调用但其完成结局未耐久记下时的恢复码

def 中断轮次关闭器(事件列表):
    """返回关闭打开尾轮次的确定性合成事件。"""
    打开轮次=None
    打开步骤=None
    未完成={}
    for 事件 in 事件列表:
        种类=事件['type']
        数据=事件['data']
        if 种类=='turn/start':
            打开轮次=数据['turn']
            打开步骤=None
            未完成.clear()
        elif 种类=='turn/end':
            打开轮次=None
            打开步骤=None
            未完成.clear()
        elif 种类=='step/start':
            打开步骤=数据['step']
        elif 种类=='step/end':
            未完成.clear()
            打开步骤=None
        elif 种类=='assistant/message':
            消息=数据['message']
            内容=消息['content']
            for 块 in 内容:
                if 块['type']=='tool-call':
                    未完成[块['id']]={'step':数据['step']}
        elif 种类=='tool/call':
            调用号=数据['callId']
            项=未完成[调用号] if 调用号 in 未完成 else None
            if 项 is not None:
                项['callSeq']=事件['seq']
        elif 种类=='tool/result':
            消息=数据['message']
            来源=消息['source']
            未完成.pop(来源['callId'],None)
    if len(事件列表)==0:
        return []
    最后=事件列表[-1]
    if 打开轮次 is None or 最后 is None:
        return []
    序号=最后['seq']+1
    时间=最后['time']
    关闭列表=[]
    for 调用号,项 in 未完成.items():
        步骤=项['step']
        调用序号=项['callSeq'] if 'callSeq' in 项 else None
        已启动=调用序号 is not None
        if 已启动:
            说明='工具调用在已记录后被中断，但没有耐久记下结果。结局未知。是否重试请按工具语义决定：只读或幂等才可重试；若可能有副作用，先核对外部状态或询问用户。不要盲目重试。'
            错误={'name':'ToolOutcomeUnknownError','code':工具结局未知}
        else:
            说明='工具调用在 Harness 记为已启动之前被中断。若仍需要则重试。'
            错误={'name':'ToolNotStartedError','code':工具未启动}
        消息=冻结消息({
            'id':消息标识('interrupted-tool-result-'+str(调用号)+'-'+str(序号)),
            'role':'user',#工具结果走用户角色
            'source':{'kind':'tool','callId':调用标识(调用号)},
            'content':[{
                'type':'tool-result',
                'toolCallId':调用标识(调用号),
                'isError':True,
                'content':[{'type':'text','text':说明}],
            }],
        })
        事件={
            'type':'tool/result',
            'seq':序号,
            'time':时间,
            'data':{
                'turn':打开轮次,
                'step':步骤,
                'message':消息,
                'error':错误,
            },
            'surfaceOp':'append',
        }
        if 已启动:
            事件['sourceEventSeqs']=[调用序号]
        关闭列表.append(事件)
        序号+=1
    if 打开步骤 is not None:
        关闭列表.append({
            'type':'step/end',
            'seq':序号,
            'time':时间,
            'data':{'turn':打开轮次,'step':打开步骤},
        })
        序号+=1
    关闭列表.append({
        'type':'turn/end',
        'seq':序号,
        'time':时间,
        'data':{'turn':打开轮次,'reason':{'kind':'interrupted'}},
    })
    return 关闭列表
