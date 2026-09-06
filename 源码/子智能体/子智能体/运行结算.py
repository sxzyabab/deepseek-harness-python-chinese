"""把一次一次性子智能体跑结算成后台任务结局。只有一次性后台路径使用 Jobs；可续跑子体没有 Task、没有每消息结果、也没有 Task 取消。跑为对象，result 为操作任务。"""

def 最终文本(块列表):
    """把子体最终输出块压成任务最终文本。块为 dict。"""
    片段=[]#文本片段
    for 块 in 块列表:#逐块
        if 块['type']=='text':#只要文本块
            片段.append(块['text'] if 'text' in 块 and 块['text'] is not None else '')#取文本
    return ''.join(片段)#拼接

def 跑结局(结果):
    """把子结果映射成任务结局：completed 携带最终文本，aborted 是 killed，其余原因失败且不含部分输出。结果为 dict。"""
    停止原因=结果['stopReason']#停止原因
    if 停止原因=='completed':#正常完成
        输出=结果['output'] if 'output' in 结果 else []#输出块
        return {'status':'completed','output':最终文本(输出)}#带最终文本
    if 停止原因=='aborted':#已中止
        return {'status':'killed'}#映射为killed
    if 停止原因 in ('error','max-tokens','refusal'):#已知失败原因
        return {'status':'failed','detail':停止原因}#失败带原因
    return {'status':'failed','detail':str(停止原因)}#失败带原始细节

def 结算运行(跑):
    """等待子结果、拆除跑，然后返回其任务结局。结果与拆除失败都变成 failed；两者都失败时两边细节都存活。"""
    try:#等待子结果
        结局=跑结局(跑.result.等待())#映射结局
    except Exception as 错误:#结果拒绝
        结局={'status':'failed','detail':str(错误)}#基础设施失败
    try:#拆除跑
        跑.销毁()#释放子资源
    except Exception as 错误:#拆除失败
        前缀='' if 'detail' not in 结局 or 结局['detail'] is None else str(结局['detail'])+'; '#保留已有细节
        return {'status':'failed','detail':前缀+'dispose failed: '+str(错误)}#合并拆除失败
    return 结局#拆除成功则返回映射结局
