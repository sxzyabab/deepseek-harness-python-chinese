import json
from .详情卡片模型 import 待办详情

__all__=['待办差异模型']

def 解析工具调用(块):
    """解析调用头的 JSON 对象参数；准备中或非法则 None。块为 dict。"""
    if 'kind' not in 块 and 块['phase']=='preparing':
        return None
    调用=块['call'] if 'kind' in 块 else 块
    if 调用 is None:
        return None
    try:
        值=json.loads(调用['argsRaw'])
    except (TypeError,ValueError,json.JSONDecodeError):
        return None
    if not isinstance(值,dict):
        return None
    return {'name':调用['name'],'args':值}

def 待办差异模型(块,基线,还有更早,翻译):
    """与已加载历史中前一次写入比较。块为 dict。"""
    if 'kind' not in 块 or ('isError' in 块 and 块['isError']):
        return None
    调用=解析工具调用(块)
    当前=待办详情(调用['args'],翻译) if 调用 is not None and 调用['name']=='todo_write' else None
    if 当前 is None:
        return None
    if 基线 is None or 'todos' not in 基线:
        先前=None
    else:
        待办表=基线['todos']
        if 待办表 is None:
            先前=None
        else:
            先前={'items':[{'title':项['content'],'status':{'value':项['status'],'label':翻译('detail.todo.'+项['status'])},'fields':[]} for 项 in 待办表]}
    if 基线 is None or (先前 is None and 还有更早):
        详情=dict(当前)
        详情['caption']=翻译('todo.diff.unavailable')
        return {'details':详情,'summary':None}
    先前按标题={}
    if 先前 is not None:
        for 项 in 先前['items']:
            先前按标题[项['title']]=项
    当前标题=set(项['title'] for 项 in 当前['items'])
    保留位置={}
    保留下标=0
    if 先前 is not None:
        for 项 in 先前['items']:
            if 项['title'] in 当前标题:
                保留位置[项['title']]=保留下标
                保留下标+=1
    条目=[]
    未变=[]
    新增=0
    更新=0
    保留游标=0
    for 项 in 当前['items']:
        之前=先前按标题[项['title']] if 项['title'] in 先前按标题 else None
        先前按标题.pop(项['title'],None)
        if 之前 is None:
            新增+=1
            下=dict(项)
            下['change']={'value':'added','label':翻译('todo.diff.addedItem')}
            条目.append(下)
        else:
            移动=保留位置[项['title']]!=保留游标
            保留游标+=1
            前态=之前['status']['value'] if 'status' in 之前 else None
            现态=项['status']['value'] if 'status' in 项 else None
            状态变=前态!=现态
            if 状态变 or 移动:
                更新+=1
                下=dict(项)
                if 状态变 and 'status' in 之前:
                    下['previousStatus']=之前['status']['label']
                下['change']={'value':'updated','label':翻译('todo.diff.updatedItem' if 状态变 else 'todo.diff.movedItem')}
                条目.append(下)
            else:
                未变.append(项)
    for 项 in 先前按标题.values():
        下=dict(项)
        下['change']={'value':'removed','label':翻译('todo.diff.removedItem')}
        条目.append(下)
    段=[]
    if 新增>0:
        段.append(翻译('todo.diff.added',{'count':新增}))
    if 更新>0:
        段.append(翻译('todo.diff.updated',{'count':更新}))
    if len(先前按标题)>0:
        段.append(翻译('todo.diff.removed',{'count':len(先前按标题)}))
    摘要=' · '.join(段) if len(段)>0 else 翻译('todo.diff.noChanges')
    详情={
        'items':条目,
        'caption':翻译('todo.diff.initial' if 先前 is None else 'todo.diff.compare'),
        'empty':翻译('detail.todo.empty') if len(当前['items'])==0 and 先前 is None else 翻译('todo.diff.noChanges'),
    }
    if len(未变)>0:
        详情['unchanged']={'label':翻译('todo.diff.unchanged',{'count':len(未变)}),'items':未变}
    return {'summary':摘要,'details':详情}
