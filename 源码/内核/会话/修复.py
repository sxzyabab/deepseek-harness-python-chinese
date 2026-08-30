"""中断会话日志的崩溃恢复修补。对齐上游 `session/src/repair.ts`。公开面仅中文名。"""
from ...模型后端.llm.品牌 import 消息标识,调用标识#导入消息 id 与调用 id
from ...模型后端.llm.消息 import 冻结消息#导入冻结消息

__all__=['工具未启动','工具结局未知','中断轮次关闭器']#仅中文公开名

工具未启动='TOOL_NOT_STARTED'#助手工具请求从未到达已记录调用开始时的恢复码
工具结局未知='TOOL_OUTCOME_UNKNOWN'#已记录工具调用但其完成结局未耐久记下时的恢复码

def 取字段(对象,键):#读取字段
    """读取映射或对象上的字段。"""
    if isinstance(对象,dict):#映射
        return 对象[键]#映射键
    return getattr(对象,键)#对象属性

def 试取(对象,键):#读取可选字段
    """读取可选字段，缺席为 None。"""
    if 对象 is None:#无对象
        return None#缺席
    if isinstance(对象,dict):#映射
        return 对象.get(键)#映射键
    return getattr(对象,键,None)#对象属性

def 中断轮次关闭器(事件们):#合成中断轮次关闭事件
    """返回关闭打开尾轮次的确定性合成事件。"""
    打开轮次=None#当前打开轮次
    打开步骤=None#当前打开步骤
    未完成={}#未完成调用，按插入序
    for 事件 in 事件们:#扫描日志
        种类=取字段(事件,'type')#事件类型
        数据=取字段(事件,'data')#载荷
        if 种类=='turn/start':#轮次开始
            打开轮次=取字段(数据,'turn')#打开该轮次
            打开步骤=None#步骤尚未开始
            未完成.clear()#清掉更早调用
        elif 种类=='turn/end':#轮次结束
            打开轮次=None#关闭轮次
            打开步骤=None#关闭步骤
            未完成.clear()#清掉调用
        elif 种类=='step/start':#步骤开始
            打开步骤=取字段(数据,'step')#打开该步骤
        elif 种类=='step/end':#步骤结束
            未完成.clear()#本步调用结束
            打开步骤=None#关闭步骤
        elif 种类=='assistant/message':#助手消息
            消息=取字段(数据,'message')#助手消息
            内容=取字段(消息,'content')#内容块
            for 块 in 内容:#扫描内容块
                if 取字段(块,'type')=='tool-call':#工具调用块
                    未完成[取字段(块,'id')]={'step':取字段(数据,'step')}#登记待处理调用
        elif 种类=='tool/call':#工具调用
            调用号=取字段(数据,'callId')#调用 id
            项=未完成.get(调用号)#取出待处理项
            if 项 is not None:#已由助手块登记
                项['callSeq']=取字段(事件,'seq')#记下调用序号
        elif 种类=='tool/result':#工具结果
            消息=取字段(数据,'message')#结果消息
            来源=取字段(消息,'source')#工具来源
            未完成.pop(取字段(来源,'callId'),None)#配对完成
    if len(事件们)==0:#空日志
        return []#空日志
    最后=事件们[-1]#最后一条真实事件
    if 打开轮次 is None or 最后 is None:#无打开轮次或空日志
        return []#无打开轮次或空日志
    序号=取字段(最后,'seq')+1#下一条合成序号
    时间=取字段(最后,'time')#复用最后时间
    关闭们=[]#合成关闭事件
    for 调用号,项 in 未完成.items():#逐个未完成调用
        步骤=项['step']#所属步骤
        调用序号=项.get('callSeq')#可选 tool/call 序号
        已启动=调用序号 is not None#是否已记下 tool/call
        if 已启动:#已记下 tool/call
            说明='The tool call was interrupted after it was recorded, but no result was durably recorded. Its outcome is unknown. Decide whether to retry from the tool semantics: retry only if the operation is read-only or idempotent; if it may have side effects, first verify external state or ask the user. Do not retry blindly.'#已启动说明
            错误={'name':'ToolOutcomeUnknownError','code':工具结局未知}#结局未知
        else:#未启动
            说明='The tool call was interrupted before the Harness recorded it as started. Retry it if it is still needed.'#未启动说明
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
        关闭们.append(事件)#追加合成结果
        序号+=1#下一条
    if 打开步骤 is not None:#步骤仍打开
        关闭们.append({#合成步骤结束
            'type':'step/end',#步骤结束
            'seq':序号,#分配序号
            'time':时间,#复用时间
            'data':{'turn':打开轮次,'step':打开步骤},#打开轮次与步骤
        })#合成步骤结束
        序号+=1#下一条
    关闭们.append({#合成中断轮次结束
        'type':'turn/end',#轮次结束
        'seq':序号,#分配序号
        'time':时间,#复用时间
        'data':{'turn':打开轮次,'reason':{'kind':'interrupted'}},#中断原因
    })#合成中断轮次结束
    return 关闭们#返回关闭事件
