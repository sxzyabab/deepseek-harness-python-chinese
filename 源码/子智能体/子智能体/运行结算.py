"""把一次一次性子智能体跑结算成后台任务结局。只有一次性后台路径使用 Jobs；可续跑子体没有 Task、没有每消息结果、也没有 Task 取消。"""
from ...依赖 import cordis#外部依赖胶水
def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段。"""
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

def 最终文本(块们):#抽取文本
    """把子体最终输出块压成任务最终文本。"""
    片段=[]#文本片段
    for 块 in 块们:#逐块
        if 取字段(块,'type')=='text':#只要文本块
            片段.append(取字段(块,'text') or '')#取文本
    return ''.join(片段)#拼接

def 跑结局(结果):#映射任务结局
    """把子结果映射成任务结局：completed 携带最终文本，aborted 是 killed，其余原因失败且不含部分输出。"""
    停止原因=取字段(结果,'stopReason')#停止原因
    if 停止原因=='completed':#正常完成
        return {'status':'completed','output':最终文本(取字段(结果,'output') or [])}#带最终文本
    if 停止原因=='aborted':#已中止
        return {'status':'killed'}#映射为killed
    if 停止原因 in ('error','max-tokens','refusal'):#已知失败原因
        return {'status':'failed','detail':停止原因}#失败带原因
    # 可合并扩展的原因仍是失败，细节用原始值。
    return {'status':'failed','detail':str(停止原因)}#失败带原始细节

def 结算运行(跑):#结算一次性跑
    """等待子结果、拆除跑，然后返回其任务结局。结果与拆除失败都变成 failed；两者都失败时两边细节都存活。"""
    try:#等待子结果
        结局=跑结局(解开(取字段(跑,'result')))#映射结局
    except Exception as 错误:#结果拒绝
        结局={'status':'failed','detail':str(错误)}#基础设施失败
    try:#拆除跑
        销毁=getattr(跑,'销毁',None)#中文拆除入口
        if 销毁 is None:#缺中文入口则读映射键（旧句柄）
            销毁=取字段(跑,'拆除') or getattr(跑,'dispose',None)#兼容
        解开(销毁())#释放子资源
    except Exception as 错误:#拆除失败
        前缀='' if 取字段(结局,'detail') is None else str(取字段(结局,'detail'))+'; '#保留已有细节
        return {'status':'failed','detail':前缀+'dispose failed: '+str(错误)}#合并拆除失败
    return 结局#拆除成功则返回映射结局
