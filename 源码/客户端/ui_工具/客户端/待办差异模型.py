from .文案 import 中文文案
from .详情卡片模型 import 待办详情
from .原始工具调用 import 解析工具调用

__all__=['待办差异模型']

def 待办差异模型(块,基线,还有更早):
    '与已加载历史中前一次写入比较。错误或不是 todo_write 则 None'
    if 'kind' not in 块 or 块.get('isError') is True:
        return None
    调用=解析工具调用(块)
    当前=None
    if 调用 is not None and 调用['name']=='todo_write':
        当前=待办详情(调用['args'])
    if 当前 is None:
        return None
    先前=None
    if 基线 is not None and 基线.get('todos') is not None:
        先前条目=[]
        for 待办 in 基线['todos']:
            先前条目.append({
                'title':待办['content'],
                'status':{'value':待办['status'],'label':中文文案('detail.todo.'+待办['status'])},
                'fields':[],
            })
        先前={'items':先前条目}
    if 基线 is None or (先前 is None and 还有更早):
        详情=dict(当前)
        详情['caption']=中文文案('todo.diff.unavailable')
        return {'details':详情,'summary':None}
    先前按标题={}
    if 先前 is not None:
        for 条目 in 先前['items']:
            先前按标题[条目['title']]=条目
    当前标题=set()
    for 条目 in 当前['items']:
        当前标题.add(条目['title'])
    保留位置={}
    序=0
    if 先前 is not None:
        for 条目 in 先前['items']:
            if 条目['title'] in 当前标题:
                保留位置[条目['title']]=序
                序=序+1
    保留下标=0
    条目表=[]
    未变=[]
    新增=0
    更新=0
    for 条目 in 当前['items']:
        之前=先前按标题.get(条目['title'])
        if 条目['title'] in 先前按标题:
            del 先前按标题[条目['title']]
        if 之前 is None:
            新增=新增+1
            改过=dict(条目)
            改过['change']={'value':'added','label':中文文案('todo.diff.addedItem')}
            条目表.append(改过)
        else:
            移动=保留位置.get(条目['title'])!=保留下标
            保留下标=保留下标+1
            之前状态=之前.get('status')
            当前状态=条目.get('status')
            状态变了=None
            if isinstance(之前状态,dict) or isinstance(当前状态,dict):
                前值=之前状态.get('value') if isinstance(之前状态,dict) else None
                后值=当前状态.get('value') if isinstance(当前状态,dict) else None
                状态变了=前值!=后值
            else:
                状态变了=False
            if 状态变了 or 移动:
                更新=更新+1
                改过=dict(条目)
                if 状态变了 and isinstance(之前状态,dict):
                    改过['previousStatus']=之前状态['label']
                if 状态变了:
                    变更文=中文文案('todo.diff.updatedItem')
                else:
                    变更文=中文文案('todo.diff.movedItem')
                改过['change']={'value':'updated','label':变更文}
                条目表.append(改过)
            else:
                未变.append(条目)
    for 条目 in 先前按标题.values():
        改过=dict(条目)
        改过['change']={'value':'removed','label':中文文案('todo.diff.removedItem')}
        条目表.append(改过)
    摘要段=[]
    if 新增>0:
        摘要段.append(中文文案('todo.diff.added',{'count':新增}))
    if 更新>0:
        摘要段.append(中文文案('todo.diff.updated',{'count':更新}))
    if len(先前按标题)>0:
        摘要段.append(中文文案('todo.diff.removed',{'count':len(先前按标题)}))
    摘要=' · '.join(摘要段)
    if 摘要=='':
        摘要=中文文案('todo.diff.noChanges')
    if 先前 is None:
        说明=中文文案('todo.diff.initial')
    else:
        说明=中文文案('todo.diff.compare')
    if len(当前['items'])==0 and 先前 is None:
        空文=中文文案('detail.todo.empty')
    else:
        空文=中文文案('todo.diff.noChanges')
    详情={'items':条目表,'caption':说明,'empty':空文}
    if len(未变)>0:
        详情['unchanged']={'label':中文文案('todo.diff.unchanged',{'count':len(未变)}),'items':未变}
    return {'summary':摘要,'details':详情}
