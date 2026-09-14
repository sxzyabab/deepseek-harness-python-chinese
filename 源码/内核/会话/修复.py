from ...模型后端.llm.标识构造 import 消息标识,调用标识#导入消息标识与调用标识构造
from ...模型后端.llm.消息 import 冻结消息#导入冻结消息

__all__=['工具未启动','工具结局未知','中断轮次关闭器']#仅中文公开名

工具未启动='TOOL_NOT_STARTED'#助手工具请求从未到达已记录调用开始时的恢复码
工具结局未知='TOOL_OUTCOME_UNKNOWN'#已记录工具调用但其完成结局未耐久记下时的恢复码

def 中断轮次关闭器(事件列表):#合成中断轮次关闭事件
    """返回关闭打开尾轮次的确定性合成事件。"""
    打开轮次=None#当前打开轮次
    打开步骤=None#当前打开步骤
    未完成={}#未完成调用，按插入序
    for 事件 in 事件列表:#扫描日志
        种类=事件['type']#事件类型
        数据=事件['data']#载荷
        if 种类=='turn/start':#轮次开始
            打开轮次=数据['turn']#打开该轮次
            打开步骤=None#步骤尚未开始
            未完成.clear()#清掉更早调用
        elif 种类=='turn/end':#轮次结束
            打开轮次=None#关闭轮次
            打开步骤=None#关闭步骤
            未完成.clear()#清掉调用
        elif 种类=='step/start':#步骤开始
            打开步骤=数据['step']#打开该步骤
        elif 种类=='step/end':#步骤结束
            未完成.clear()#本步调用结束
            打开步骤=None#关闭步骤
        elif 种类=='assistant/message':#助手消息
            消息=数据['message']#助手消息
            内容=消息['content']#内容块
            for 块 in 内容:#扫描内容块
                if 块['type']=='tool-call':#工具调用块
                    未完成[块['id']]={'step':数据['step']}#登记待处理调用
        elif 种类=='tool/call':#工具调用
            调用号=数据['callId']#调用 id
            项=未完成[调用号] if 调用号 in 未完成 else None#取出待处理项
            if 项 is not None:#已由助手块登记
                项['callSeq']=事件['seq']#记下调用序号
        elif 种类=='tool/result':#工具结果
            消息=数据['message']#结果消息
            来源=消息['source']#工具来源
            未完成.pop(来源['callId'],None)#配对完成
    if len(事件列表)==0:#空日志
        return []#空日志
    最后=事件列表[-1]#最后一条真实事件
    if 打开轮次 is None or 最后 is None:#无打开轮次或空日志
        return []#无打开轮次或空日志
    序号=最后['seq']+1#下一条合成序号
    时间=最后['time']#复用最后时间
    关闭列表=[]#合成关闭事件
    for 调用号,项 in 未完成.items():#逐个未完成调用
        步骤=项['step']#所属步骤
        调用序号=项['callSeq'] if 'callSeq' in 项 else None#可选 tool/call 序号
        已启动=调用序号 is not None#是否已记下 tool/call
        if 已启动:#已记下 tool/call
            说明='工具调用在已记录后被中断，但没有耐久记下结果。结局未知。是否重试请按工具语义决定：只读或幂等才可重试；若可能有副作用，先核对外部状态或询问用户。不要盲目重试。'#已启动说明
            错误={'name':'ToolOutcomeUnknownError','code':工具结局未知}#结局未知
        else:#未启动
            说明='工具调用在 Harness 记为已启动之前被中断。若仍需要则重试。'#未启动说明
            错误={'name':'ToolNotStartedError','code':工具未启动}#未启动
        消息=冻结消息({#冻结合成错误结果
            'id':消息标识('interrupted-tool-result-'+str(调用号)+'-'+str(序号)),#确定性消息 id
            'role':'user',#工具结果走用户角色
            'source':{'kind':'tool','callId':调用标识(调用号)},#工具来源
            'content':[{#单块工具结果
                'type':'tool-result',#工具结果块
                'toolCallId':调用标识(调用号),#配对调用
                'isError':True,#错误结局
                'content':[{'type':'text','text':说明}],#错误文本
            }],#单块工具结果
        })#冻结合成错误结果
        事件={#合成 tool/result
            'type':'tool/result',#工具结果
            'seq':序号,#分配序号
            'time':时间,#复用时间
            'data':{#载荷
                'turn':打开轮次,#打开轮次
                'step':步骤,#所属步骤
                'message':消息,#合成消息
                'error':错误,#按是否启动选恢复码
            },#载荷
            'surfaceOp':'append',#追加到表面
        }#合成 tool/result
        if 已启动:#已启动
            事件['sourceEventSeqs']=[调用序号]#已启动则引用 tool/call
        关闭列表.append(事件)#追加合成结果
        序号+=1#下一条
    if 打开步骤 is not None:#步骤仍打开
        关闭列表.append({#合成步骤结束
            'type':'step/end',#步骤结束
            'seq':序号,#分配序号
            'time':时间,#复用时间
            'data':{'turn':打开轮次,'step':打开步骤},#打开轮次与步骤
        })#合成步骤结束
        序号+=1#下一条
    关闭列表.append({#合成中断轮次结束
        'type':'turn/end',#轮次结束
        'seq':序号,#分配序号
        'time':时间,#复用时间
        'data':{'turn':打开轮次,'reason':{'kind':'interrupted'}},#中断原因
    })#合成中断轮次结束
    return 关闭列表#返回关闭事件
