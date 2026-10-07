from ...基础设施.js特性 import PromiseEX as 期约#期约封装

def 最终文本(块列表):
    '把子体最终输出块压成任务最终文本。块为 dict'
    片段=[]#文本片段
    for 块 in 块列表:#逐块
        if 块['type']=='text':#只要文本块
            片段.append(块['text'] if 'text' in 块 and 块['text'] is not None else '')#取文本
    return ''.join(片段)#拼接

def 映射结局(结果):
    '把子结果映射成任务结局：completed 携带最终文本，aborted 是 killed，其余原因失败且不含部分输出。结果为 dict'
    停止原因=结果['stopReason']#停止原因
    if 停止原因=='completed':#正常完成
        输出=结果['output'] if 'output' in 结果 else []#输出块
        return {'status':'completed','output':最终文本(输出)}#带最终文本
    if 停止原因=='aborted':#已中止
        return {'status':'killed'}#映射为killed
    if 停止原因 in ('error','max-tokens','refusal'):#已知失败原因
        return {'status':'failed','detail':停止原因}#失败带原因
    return {'status':'failed','detail':str(停止原因)}#失败带原始细节

def 结算运行(运行):
    '返回期约：子结果落定并拆除运行后，兑现其任务结局。结果与拆除失败都变成 failed；两者都失败时两边细节都存活，期约自身不会拒绝'
    结局期约=期约()#任务结局期约，由下面的回调结算
    def 拆除并结算(结局):
        '子结果落定后拆除运行，再以结局兑现'
        def 拆除成功(拆除结果):
            '拆除成功则兑现映射结局'
            结局期约.解决(结局)#兑现映射结局
        def 拆除失败(错误):
            '拆除失败则把拆除细节并进结局'
            前缀='' if 'detail' not in 结局 or 结局['detail'] is None else str(结局['detail'])+'; '#保留已有细节
            结局期约.解决({'status':'failed','detail':前缀+'拆除失败: '+str(错误)})#合并拆除失败
        运行.销毁().然后(拆除成功,拆除失败)#拆除落定后继续
    def 结果已兑现(结果):
        '子结果兑现后映射结局'
        try:#映射结局
            结局=映射结局(结果)#结果为 dict
        except Exception as 错误:#映射失败
            结局={'status':'failed','detail':str(错误)}#基础设施失败
        拆除并结算(结局)#继续拆除
    def 结果已拒绝(错误):
        '子结果拒绝则记为基础设施失败'
        拆除并结算({'status':'failed','detail':str(错误)})#继续拆除
    运行.result.然后(结果已兑现,结果已拒绝)#等子结果落定
    return 结局期约#交给调用方继续链式
