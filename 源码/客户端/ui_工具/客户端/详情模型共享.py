import json
from .文案 import 中文文案

__all__=[
    '详情记录','非空文本','详情json','详情徽章','详情标签','检视条目','详情列表',
]

状态键={
    'running':'detail.status.running',
    'idle':'detail.status.idle',
    'ready':'detail.status.ready',
    'inactive':'detail.status.inactive',
    'provisioning':'detail.status.provisioning',
    'failed':'detail.status.failed',
    'error':'detail.status.failed',
    'completed':'detail.status.completed',
    'complete':'detail.status.completed',
    'done':'detail.status.completed',
    'pending':'detail.todo.pending',
    'in_progress':'detail.todo.in_progress',
    'deleted':'detail.status.deleted',
    'killed':'detail.status.killed',
    'blocked':'detail.goal.blocked',
    'accepted':'detail.status.accepted',
    'queued':'detail.status.queued',
}
成功态=frozenset(['completed','complete','done','accepted'])
错误态=frozenset(['failed','error'])
警告态=frozenset(['blocked','killed','pending','queued','inactive'])
信息态=frozenset(['running','in_progress','provisioning'])
字段键={
    'id':'detail.field.id',
    'revision':'detail.field.revision',
    'platform':'detail.field.platform',
    'provider':'detail.field.provider',
    'model':'detail.field.model',
    'role':'detail.field.role',
    'context':'detail.field.context',
    'ownerName':'detail.field.owner',
    'ready':'detail.field.ready',
    'blockedBy':'detail.field.dependencies',
    'writeScopes':'detail.field.writeScopes',
    'writeScopeWarnings':'detail.field.warnings',
    'diagnostics':'detail.field.diagnostics',
    'methods':'detail.field.methods',
    'inputSchema':'detail.field.inputSchema',
    'outputSchema':'detail.field.outputSchema',
    'currentPackageId':'detail.field.currentPackage',
    'nextPackageId':'detail.field.nextPackage',
    'latestRun':'detail.field.latestRun',
    'packages':'detail.field.packages',
    'registrations':'detail.field.registrations',
    'props':'detail.field.props',
    'data':'detail.field.data',
    'source':'detail.field.source',
    'arguments':'row.input',
    'content':'detail.field.content',
    'message':'detail.field.message',
    'messageId':'detail.field.messageId',
    'status':'detail.state',
    'root':'detail.field.root',
    'pid':'detail.field.pid',
    'type':'detail.field.type',
    'time':'detail.field.time',
    'seq':'detail.field.seq',
    'turn':'detail.field.turn',
    'step':'detail.field.step',
    'callId':'detail.field.callId',
    'agentsStarted':'detail.field.agents',
    'output':'row.output',
    'result':'detail.field.result',
}
检视标题键=('subject','title','name','pluginId','packageId','id','summary')
检视说明键=('description','purpose')
检视条目上限=40

def 详情记录(值):
    '解析结果是可按名读字段的对象'
    return isinstance(值,dict)

def 非空文本(值):
    '去空白后仍有可见文本'
    return isinstance(值,str) and 值.strip()!=''

def 详情json(文本):
    '整段 JSON。非 JSON 则 None'
    try:
        return json.loads(文本)
    except json.JSONDecodeError:
        return None

def 详情徽章(状态):
    '已记录状态的中文名与静态语义色。未知状态保留原文'
    键=状态键[状态] if 状态 in 状态键 else None
    if 状态 in 成功态:
        语气='success'
    elif 状态 in 错误态:
        语气='error'
    elif 状态 in 警告态:
        语气='warning'
    elif 状态 in 信息态:
        语气='info'
    else:
        语气='neutral'
    return {'label':状态 if 键 is None else 中文文案(键),'tone':语气}

def 详情标签(键):
    '已知字段走中文。扩展字段保留原名'
    if 键 in 字段键:
        return 中文文案(字段键[键])
    return 键

def 标量(值):
    '空、布尔或原文。其余格式化成 JSON'
    if 值 is None:
        return 中文文案('detail.none')
    if isinstance(值,bool):
        return 中文文案('detail.yes') if 值 else 中文文案('detail.no')
    if isinstance(值,str):
        return 值
    return json.dumps(值,ensure_ascii=False)

def 检视条目(值,深度=0):
    '把开放检视记录投影成可读字段与具名披露'
    if 深度>4 and 值 is not None and isinstance(值,(dict,list)):
        return [{'code':{'text':json.dumps(值,ensure_ascii=False,indent=2),'language':'json'},'fields':[]}]
    if isinstance(值,list):
        条目=[]
        for 项 in 值[:检视条目上限]:
            条目.extend(检视条目(项,深度+1))
        if len(值)>检视条目上限:
            条目.append({
                'description':中文文案('detail.moreInInspect',{'count':len(值)-检视条目上限}),
                'fields':[],
            })
        if len(条目)==0:
            return [{'description':中文文案('detail.empty'),'fields':[]}]
        return 条目
    if not 详情记录(值):
        return [{'description':标量(值),'fields':[]}]
    标题键=None
    for 键 in 检视标题键:
        if isinstance(值.get(键),str) and 值[键]!='':
            标题键=键
            break
    说明键=None
    for 键 in 检视说明键:
        if isinstance(值.get(键),str) and 值[键]!='':
            说明键=键
            break
    标题=None if 标题键 is None else str(值[标题键])
    字段=[]
    分组=[]
    for 键,字段值 in 值.items():
        if 键==标题键 or 键==说明键 or (键=='status' and isinstance(字段值,str)):
            continue
        if 键=='inputSchema' or 键=='outputSchema':
            分组.append({
                'label':详情标签(键),
                'items':[{'fields':[],'code':{'text':json.dumps(字段值,ensure_ascii=False,indent=2),'language':'json'}}],
            })
            continue
        if isinstance(字段值,list) and len(字段值)==0:
            continue
        if 键=='arguments' and isinstance(字段值,str):
            参数=详情json(字段值)
            if 详情记录(参数):
                分组.append({'label':详情标签(键),'items':检视条目(参数,深度+1)})
                continue
        if 字段值 is not None and isinstance(字段值,(dict,list)):
            分组.append({'label':详情标签(键),'items':检视条目(字段值,深度+1)})
        else:
            字段.append({'label':详情标签(键),'value':标量(字段值)})
    条目={'fields':字段}
    if not (标题 is None and not isinstance(值.get('status'),str)):
        条目['title']=中文文案('detail.field.result') if 标题 is None else 标题
    if 说明键 is not None:
        条目['description']=str(值[说明键])
    if isinstance(值.get('status'),str):
        条目['badge']=详情徽章(值['status'])
    if len(分组)>0:
        条目['groups']=分组
    return [条目]

def 详情列表(条目表,摘要):
    '给结果列表一致的历史上下文与空态文案'
    return {
        'items':条目表,
        'summary':摘要,
        'caption':中文文案('detail.recordedResult'),
        'empty':中文文案('detail.empty'),
    }
