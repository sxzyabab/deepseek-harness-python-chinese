"""模型可见的注册表读取渲染：消费增量、[status: …] 行，以及工具模式暴露的公开任务投影。"""

def 任务细节(任务):
    """模型读到的一行限定语：运行中用进度，结算后用终态原因。"""
    if 'progress' in 任务 and 任务['progress'] is not None:
        return 任务['progress']
    if 'detail' in 任务 and 任务['detail'] is not None:
        return 任务['detail']
    return None

def 公开任务(任务):
    """去掉所有权、偏移与上限。"""
    细节=任务细节(任务)
    结果={
        'id':任务['id'],
        'kind':任务['kind'],
        'label':任务['label'],
        'status':任务['status'],
        'startedAt':任务['startedAt'],
    }
    if 细节 is not None:
        结果['detail']=细节
    if 'finishedAt' in 任务 and 任务['finishedAt'] is not None:
        结果['finishedAt']=任务['finishedAt']
    return 结果

def 状态行(快照):
    """带可选细节的方括号状态行。"""
    if 'detail' in 快照 and 快照['detail'] is not None:
        return '[status: '+str(快照['status'])+', '+str(快照['detail'])+']'
    return '[status: '+str(快照['status'])+']'

def 渲染模型增量(分块列表,有损,溢出路径列表):
    """stdout 与无标签分块按序，stderr 收进一段 [stderr]；log 分块不达模型。"""
    可见=[块 for 块 in 分块列表 if 块.get('channel')!='log']
    出=''.join(块['text'] for 块 in 可见 if 块.get('channel')!='stderr')
    错=''.join(块['text'] for 块 in 可见 if 块.get('channel')=='stderr')
    分隔='\n' if len(出)>0 and (not 出.endswith('\n')) else ''
    正文=出+(分隔+'[stderr]\n'+错 if len(错)>0 else '')
    有缺口=有损 or any(块.get('gapBefore') is True for 块 in 可见)
    if not 有缺口:
        return 正文
    路径文=', '.join(溢出路径列表) if len(溢出路径列表)>0 else '(unavailable)'
    通知='[some output was dropped from memory; full output: '+路径文+']'
    连接='\n' if len(正文)>0 and (not 正文.endswith('\n')) else ''
    return 正文+连接+通知

__all__=['任务细节','公开任务','状态行','渲染模型增量']
