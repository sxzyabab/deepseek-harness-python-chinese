import re
from .文案 import 中文文案
from .详情模型共享 import 详情徽章,详情列表,详情记录,检视条目

__all__=['控制详情']

输出截断='\n[output truncated]'
智能体行=re.compile(r'^(\S+) \[([^\]]+)\](?: parent=(\S+) depth=([0-9]+))?(?: — (.*))?$')
后台行=re.compile(r'^(\S+) \[([^\]]+)\] (\S+) — (.*)$')
终端行=re.compile(r'^(\S+)(?: \((.*?)\))? \[([^\]]+)\] (running|exited code=(\S+) signal=(\S+))(?: pid=([0-9]+))?$')
位置行=re.compile(r'^(.*):([0-9]+):([0-9]+)$')
网址形=re.compile(r'^[a-z][a-z0-9+.-]*:',re.IGNORECASE)
盘符形=re.compile(r'^[a-z]:[\\/]',re.IGNORECASE)
子智能体启动=re.compile(r'^started (background subagent job|subagent) (\S+)$')
后台状态=re.compile(r'\n\[status: ([^,\]\n]+)(?:, ([^\]\n]+))?\]$')
终端打开=re.compile(r'^started terminal session (\S+)(?: \((.*?)\))? \[type: ([^\]]+)\]\n([\s\S]*)$')
终端读取=re.compile(r'\n\[lines: ([0-9]+)-([0-9]+) of ([0-9]+)\](\n\[output truncated\])?$')
终端信号=re.compile(r'^delivered (\S+) to foreground process group ([0-9]+)$')

def 参数串(参数,键):
    '取字符串参数。没有则空串'
    值=参数.get(键)
    if isinstance(值,str):
        return 值
    return ''

def 回执(标题,徽章,字段=None,说明=None):
    '带展开摘要的回执'
    if 字段 is None:
        字段=[]
    条目={'title':标题,'badge':徽章,'fields':字段}
    if 说明 is not None:
        条目['description']=说明
    模型=详情列表([条目],标题+' · '+徽章['label'])
    模型['expandedSummary']=标题
    return 模型

def 智能体列表(文本,json值):
    'list_agents 文本或 JSON'
    if isinstance(json值,list):
        return 详情列表(检视条目(json值),中文文案('detail.agents.count',{'count':len(json值)}))
    if 文本=='(no subagents)':
        return 详情列表([],中文文案('detail.agents.count',{'count':0}))
    条目表=[]
    for 行 in 文本.split('\n'):
        匹配=智能体行.search(行)
        if 匹配 is None:
            return None
        标识,状态,父级,深度,标题=匹配.group(1),匹配.group(2),匹配.group(3),匹配.group(4),匹配.group(5)
        if 标识 is None or 状态 is None:
            return None
        条目={'title':标识 if 标题 is None else 标题,'badge':详情徽章(状态),'fields':[]}
        if 标题 is not None:
            条目['subtitle']=标识
        if 父级 is not None:
            条目['fields']=[
                {'label':中文文案('detail.field.parent'),'value':父级},
                {'label':中文文案('detail.field.depth'),'value':'' if 深度 is None else 深度},
            ]
        条目表.append(条目)
    return 详情列表(条目表,中文文案('detail.agents.count',{'count':len(条目表)}))

def 后台列表(文本):
    'job_list 文本'
    if 文本=='(no background jobs)':
        return 详情列表([],中文文案('detail.jobs.count',{'count':0}))
    条目表=[]
    for 行 in 文本.split('\n'):
        匹配=后台行.search(行)
        if 匹配 is None:
            return None
        标识,种类,状态,标题=匹配.group(1),匹配.group(2),匹配.group(3),匹配.group(4)
        if 标识 is None or 种类 is None or 状态 is None or 标题 is None:
            return None
        条目表.append({
            'title':标题,
            'subtitle':标识,
            'badge':详情徽章(状态),
            'fields':[{'label':中文文案('detail.field.type'),'value':种类}],
        })
    return 详情列表(条目表,中文文案('detail.jobs.count',{'count':len(条目表)}))

def 终端列表(文本):
    'terminal_list 文本'
    if 文本=='(no terminal sessions)':
        return 详情列表([],中文文案('detail.terminals.count',{'count':0}))
    条目表=[]
    for 行 in 文本.split('\n'):
        匹配=终端行.search(行)
        if 匹配 is None:
            return None
        标识,名称,类型,状态=匹配.group(1),匹配.group(2),匹配.group(3),匹配.group(4)
        退出码,信号,进程=匹配.group(5),匹配.group(6),匹配.group(7)
        if 标识 is None or 类型 is None or 状态 is None:
            return None
        字段=[{'label':中文文案('detail.field.type'),'value':类型}]
        if 进程 is not None:
            字段.append({'label':中文文案('detail.field.pid'),'value':进程})
        if 退出码 is not None:
            字段.append({'label':中文文案('detail.field.exitCode'),'value':退出码})
        if 信号 is not None and 信号!='null':
            字段.append({'label':中文文案('detail.field.signal'),'value':信号})
        if 状态=='running':
            徽章=详情徽章('running')
        else:
            徽章={'label':中文文案('detail.status.exited'),'tone':'success' if 退出码=='0' else 'neutral'}
        条目={'title':标识 if 名称 is None else 名称,'badge':徽章,'fields':字段}
        if 名称 is not None:
            条目['subtitle']=标识
        条目表.append(条目)
    return 详情列表(条目表,中文文案('detail.terminals.count',{'count':len(条目表)}))

def 语言服务详情(参数,文本):
    'lsp 悬停或位置列表'
    文件=参数串(参数,'file_path')
    操作=参数串(参数,'operation')
    if 文件=='' or not isinstance(参数.get('line'),(int,float)) or isinstance(参数.get('line'),bool):
        return None
    if not isinstance(参数.get('character'),(int,float)) or isinstance(参数.get('character'),bool):
        return None
    来源=文件+':'+str(参数['line'])+':'+str(参数['character'])
    if 操作=='hover':
        return 详情列表([{
            'title':来源,
            'location':{'path':文件,'line':参数['line']},
            'markdown':文本,
            'fields':[],
        }],来源)
    if 文本=='No results.':
        return 详情列表([],中文文案('detail.locations.count',{'count':0}))
    条目表=[]
    for 行 in 文本.split('\n'):
        if 行.startswith('… '):
            条目表.append({'description':行,'fields':[]})
            continue
        匹配=位置行.search(行)
        if 匹配 is None:
            return None
        路径,行号,列=匹配.group(1),匹配.group(2),匹配.group(3)
        if 路径 is None or 行号 is None or 列 is None:
            return None
        是网址=网址形.search(路径) is not None and 盘符形.search(路径) is None
        条目={'title':路径,'subtitle':中文文案('detail.location',{'line':行号,'column':列}),'fields':[]}
        if not 是网址:
            条目['location']={'path':路径,'line':int(行号)}
        条目表.append(条目)
    计数=0
    for 条目 in 条目表:
        if 'title' in 条目:
            计数=计数+1
    return 详情列表(条目表,文件+' · '+中文文案('detail.locations.count',{'count':计数}))

def 控制详情(名称,参数,文本,json值):
    '从已记录输出格式派生实体列表与操作回执'
    目标=参数串(参数,'target') or 参数串(参数,'agent_id') or 参数串(参数,'sessionId') or 参数串(参数,'job_id')
    if 名称=='list_agents':
        return 智能体列表(文本,json值)
    if 名称=='job_list':
        return 后台列表(文本)
    if 名称=='terminal_list':
        return 终端列表(文本)
    if 名称=='lsp':
        return 语言服务详情(参数,文本)
    if 名称=='spawn_teammate':
        if not 详情记录(json值) or not 详情记录(json值.get('member')):
            return None
        return 详情列表(检视条目(json值['member']),参数串(参数,'name'))
    if 名称=='team_task_create' or 名称=='team_task_get' or 名称=='team_task_update':
        if not 详情记录(json值) or not isinstance(json值.get('subject'),str):
            return None
        return 详情列表(检视条目(json值),json值['subject'])
    if 名称=='team_task_list':
        if not 详情记录(json值) or not isinstance(json值.get('tasks'),list):
            return None
        if 'nextCursor' in json值 and not isinstance(json值.get('nextCursor'),(int,float)):
            return None
        if 'nextCursor' in json值 and isinstance(json值.get('nextCursor'),bool):
            return None
        模型=详情列表(检视条目(json值['tasks']),中文文案('detail.tasks.count',{'count':len(json值['tasks'])}))
        if 'nextCursor' in json值:
            模型['caption']=中文文案('detail.tasks.nextPage',{'cursor':str(json值['nextCursor'])})
        return 模型
    if 名称=='send_message':
        状态=json值.get('status') if 详情记录(json值) else None
        if 状态=='accepted' or 状态=='queued':
            if 状态=='queued':
                徽章={'label':中文文案('detail.status.queued'),'tone':'warning'}
            else:
                徽章={'label':中文文案('detail.receipt.delivered'),'tone':'success'}
            return 回执(目标,徽章,[],参数串(参数,'message'))
        if 文本=='message delivered to agent '+目标:
            return 回执(目标,{'label':中文文案('detail.receipt.delivered'),'tone':'success'},[],参数串(参数,'message'))
        return None
    if 名称=='interrupt_agent':
        if 详情记录(json值) and isinstance(json值.get('previousStatus'),str):
            return 回执(目标,{'label':中文文案('detail.receipt.interrupt'),'tone':'warning'},[{
                'label':中文文案('detail.field.previousStatus'),
                'value':详情徽章(json值['previousStatus'])['label'],
            }])
        if 文本=='interrupt requested for agent '+目标:
            return 回执(目标,{'label':中文文案('detail.receipt.interrupt'),'tone':'warning'})
        return None
    if 名称=='wait_agent':
        if not 详情记录(json值) or not isinstance(json值.get('timedOut'),bool):
            return None
        无进展=json值.get('noProgress')
        if 详情记录(无进展) and isinstance(无进展.get('message'),str):
            return 详情列表([{
                'title':中文文案('detail.wait.noProgress'),
                'description':无进展['message'],
                'fields':[],
            }],中文文案('detail.wait.noProgress'))
        if json值['timedOut']:
            徽章={'label':中文文案('detail.wait.timeout'),'tone':'neutral'}
        else:
            徽章={'label':中文文案('detail.wait.changed'),'tone':'neutral'}
        return 回执(中文文案('detail.wait.title'),徽章)
    if 名称=='subagent':
        启动=子智能体启动.search(文本)
        if 启动 is not None:
            if 启动.group(1)=='subagent':
                字段名=中文文案('detail.field.agent')
            else:
                字段名=中文文案('detail.field.job')
            return 回执(参数串(参数,'prompt'),{'label':中文文案('detail.receipt.started'),'tone':'info'},[{
                'label':字段名,
                'value':'' if 启动.group(2) is None else 启动.group(2),
            }])
        return 详情列表([{
            'title':中文文案('detail.agent.reply'),
            'markdown':文本,
            'fields':[],
            'groups':[{'label':中文文案('detail.field.task'),'items':[{'description':参数串(参数,'prompt'),'fields':[]}]}],
        }],中文文案('detail.agent.reply'))
    if 名称=='list_subagent_models':
        条目表=[]
        for 行 in 文本.split('\n'):
            切开=行.find(' — ')
            if 切开<0:
                条目表.append({'description':行,'fields':[]})
            else:
                条目表.append({'title':行[:切开],'description':行[切开+3:],'fields':[]})
        摘要=参数串(参数,'model') or 参数串(参数,'provider') or 中文文案('detail.models.title')
        return 详情列表(条目表,摘要)
    if 名称=='job_output':
        匹配=后台状态.search(文本)
        if 匹配 is None or 匹配.group(1) is None:
            return None
        输出=文本[:匹配.start()]
        截断=输出.endswith(输出截断)
        代码=输出[:-len(输出截断)] if 截断 else 输出
        说明段=[]
        if 匹配.group(2) is not None:
            说明段.append(匹配.group(2))
        if 截断:
            说明段.append(中文文案('detail.output.truncated'))
        说明=' · '.join(说明段)
        徽章=详情徽章(匹配.group(1))
        条目={'title':目标,'badge':徽章,'fields':[],'code':{'text':代码}}
        if 说明!='':
            条目['description']=说明
        模型=详情列表([条目],目标+' · '+徽章['label'])
        模型['expandedSummary']=目标
        return 模型
    if 名称=='job_kill':
        if 文本=='requested cancellation of job '+目标:
            return 回执(目标,{'label':中文文案('detail.receipt.cancel'),'tone':'warning'},[],参数串(参数,'reason'))
        if 文本.startswith('job '+目标+' had already finished '):
            return 回执(目标,{'label':中文文案('detail.receipt.alreadyFinished'),'tone':'neutral'})
        return None
    if 名称=='terminal_open':
        匹配=终端打开.search(文本)
        if 匹配 is None or 匹配.group(1) is None or 匹配.group(3) is None or 匹配.group(4) is None:
            return None
        标题=匹配.group(1) if 匹配.group(2) is None else 匹配.group(2)
        条目={
            'title':标题,
            'badge':{'label':中文文案('detail.receipt.started'),'tone':'info'},
            'fields':[{'label':中文文案('detail.field.type'),'value':匹配.group(3)}],
            'code':{'text':匹配.group(4)},
        }
        if 匹配.group(2) is not None:
            条目['subtitle']=匹配.group(1)
        return 详情列表([条目],标题)
    if 名称=='terminal_read':
        匹配=终端读取.search(文本)
        if 匹配 is None:
            return None
        条目={
            'title':目标,
            'subtitle':中文文案('detail.output.lines',{
                'begin':'' if 匹配.group(1) is None else 匹配.group(1),
                'end':'' if 匹配.group(2) is None else 匹配.group(2),
                'total':'' if 匹配.group(3) is None else 匹配.group(3),
            }),
            'fields':[],
            'code':{'text':文本[:匹配.start()]},
        }
        if 匹配.group(4) is not None:
            条目['description']=中文文案('detail.output.truncated')
        return 详情列表([条目],目标)
    if 名称=='terminal_signal':
        匹配=终端信号.search(文本)
        if 匹配 is None or 匹配.group(1) is None or 匹配.group(2) is None:
            return None
        return 回执(目标,{'label':中文文案('detail.receipt.signal'),'tone':'success'},[
            {'label':中文文案('detail.field.signal'),'value':匹配.group(1)},
            {'label':中文文案('detail.field.processGroup'),'value':匹配.group(2)},
        ])
    if 名称=='terminal_close':
        if 文本=='closed terminal session '+目标:
            return 回执(目标,{'label':中文文案('detail.receipt.closed'),'tone':'neutral'})
        if 文本=='terminal session '+目标+' was already closing':
            return 回执(目标,{'label':中文文案('detail.receipt.closing'),'tone':'neutral'})
        return None
    return None
