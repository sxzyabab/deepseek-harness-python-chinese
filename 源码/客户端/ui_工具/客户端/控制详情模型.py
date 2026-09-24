import re
from .详情模型共享 import 详情徽章,详情列表,详情记录,检视条目

__all__=['控制详情']

输出截断='\n[output truncated]'
智能体行=re.compile(r'^(\S+) \[([^\]]+)\](?: parent=(\S+) depth=([0-9]+))?(?: — (.*))?\Z',re.ASCII)
后台行=re.compile(r'^(\S+) \[([^\]]+)\] (\S+) — (.*)\Z',re.ASCII)
终端行=re.compile(r'^(\S+)(?: \((.*?)\))? \[([^\]]+)\] (running|exited code=(\S+) signal=(\S+))(?: pid=([0-9]+))?\Z',re.ASCII)
位置行=re.compile(r'^(.*):([0-9]+):([0-9]+)\Z',re.ASCII)
网址形=re.compile(r'^[a-z][a-z0-9+.-]*:',re.ASCII|re.IGNORECASE)
盘符形=re.compile(r'^[a-z]:[\\/]',re.ASCII|re.IGNORECASE)
子智能体启动=re.compile(r'^started (background subagent job|subagent) (\S+)\Z',re.ASCII)
后台状态=re.compile(r'\n\[status: ([^,\]\n]+)(?:, ([^\]\n]+))?\]\Z')
终端打开=re.compile(r'^started terminal session (\S+)(?: \((.*?)\))? \[type: ([^\]]+)\]\n([\s\S]*)\Z')
终端读取=re.compile(r'\n\[lines: ([0-9]+)-([0-9]+) of ([0-9]+)\](\n\[output truncated\])?\Z',re.ASCII)
终端信号=re.compile(r'^delivered (\S+) to foreground process group ([0-9]+)\Z',re.ASCII)

def 参数串(参数,键):
    """取字符串参数。"""
    if 键 not in 参数:
        return ''
    值=参数[键]
    return 值 if isinstance(值,str) else ''

def 回执(标题,徽章,翻译,字段=None,说明=None):
    """带展开摘要的回执模型。"""
    if 字段 is None:
        字段=[]
    项={'title':标题,'badge':徽章,'fields':字段}
    if 说明 is not None:
        项['description']=说明
    模型=详情列表([项],标题+' · '+徽章['label'],翻译)
    模型['expandedSummary']=标题
    return 模型

def 智能体列表(文本,json值,翻译):
    """list_agents 文本或 JSON。"""
    if isinstance(json值,list):
        return 详情列表(检视条目(json值,翻译),翻译('detail.agents.count',{'count':len(json值)}),翻译)
    if 文本=='(no subagents)':
        return 详情列表([],翻译('detail.agents.count',{'count':0}),翻译)
    条目=[]
    for 行 in 文本.split('\n'):
        匹配=智能体行.match(行)
        if 匹配 is None:
            return None
        标识=匹配.group(1)
        状态=匹配.group(2)
        父=匹配.group(3)
        深度=匹配.group(4)
        标题=匹配.group(5)
        项={'title':标识 if 标题 is None else 标题,'badge':详情徽章(状态,翻译),'fields':[]}
        if 标题 is not None:
            项['subtitle']=标识
        if 父 is not None:
            项['fields']=[
                {'label':翻译('detail.field.parent'),'value':父},
                {'label':翻译('detail.field.depth'),'value':'' if 深度 is None else 深度},
            ]
        条目.append(项)
    return 详情列表(条目,翻译('detail.agents.count',{'count':len(条目)}),翻译)

def 后台列表(文本,翻译):
    """job_list 文本。"""
    if 文本=='(no background jobs)':
        return 详情列表([],翻译('detail.jobs.count',{'count':0}),翻译)
    条目=[]
    for 行 in 文本.split('\n'):
        匹配=后台行.match(行)
        if 匹配 is None:
            return None
        标识=匹配.group(1)
        种类=匹配.group(2)
        状态=匹配.group(3)
        标题=匹配.group(4)
        条目.append({'title':标题,'subtitle':标识,'badge':详情徽章(状态,翻译),'fields':[{'label':翻译('detail.field.type'),'value':种类}]})
    return 详情列表(条目,翻译('detail.jobs.count',{'count':len(条目)}),翻译)

def 终端列表(文本,翻译):
    """terminal_list 文本。"""
    if 文本=='(no terminal sessions)':
        return 详情列表([],翻译('detail.terminals.count',{'count':0}),翻译)
    条目=[]
    for 行 in 文本.split('\n'):
        匹配=终端行.match(行)
        if 匹配 is None:
            return None
        标识=匹配.group(1)
        名=匹配.group(2)
        类型=匹配.group(3)
        状态=匹配.group(4)
        退出码=匹配.group(5)
        信号=匹配.group(6)
        进程号=匹配.group(7)
        字段=[{'label':翻译('detail.field.type'),'value':类型}]
        if 进程号 is not None:
            字段.append({'label':翻译('detail.field.pid'),'value':进程号})
        if 退出码 is not None:
            字段.append({'label':翻译('detail.field.exitCode'),'value':退出码})
        if 信号 is not None and 信号!='null':
            字段.append({'label':翻译('detail.field.signal'),'value':信号})
        项={
            'title':标识 if 名 is None else 名,
            'badge':详情徽章('running',翻译) if 状态=='running' else {'label':翻译('detail.status.exited'),'tone':'success' if 退出码=='0' else 'neutral'},
            'fields':字段,
        }
        if 名 is not None:
            项['subtitle']=标识
        条目.append(项)
    return 详情列表(条目,翻译('detail.terminals.count',{'count':len(条目)}),翻译)

def 语言服务详情(参数,文本,翻译):
    """lsp 悬停或位置列表。"""
    文件=参数串(参数,'file_path')
    操作=参数串(参数,'operation')
    行号=参数['line'] if 'line' in 参数 else None
    列号=参数['character'] if 'character' in 参数 else None
    if 文件=='' or not isinstance(行号,(int,float)) or isinstance(行号,bool) or not isinstance(列号,(int,float)) or isinstance(列号,bool):
        return None
    源=文件+':'+str(行号)+':'+str(列号)
    if 操作=='hover':
        return 详情列表([{'title':源,'location':{'path':文件,'line':行号},'markdown':文本,'fields':[]}],源,翻译)
    if 文本=='No results.':
        return 详情列表([],翻译('detail.locations.count',{'count':0}),翻译)
    条目=[]
    for 行 in 文本.split('\n'):
        if 行.startswith('… '):
            条目.append({'description':行,'fields':[]})
            continue
        匹配=位置行.match(行)
        if 匹配 is None:
            return None
        路径=匹配.group(1)
        行文=匹配.group(2)
        列文=匹配.group(3)
        是网址=网址形.match(路径) is not None and 盘符形.match(路径) is None
        项={'title':路径,'subtitle':翻译('detail.location',{'line':行文,'column':列文}),'fields':[]}
        if not 是网址:
            项['location']={'path':路径,'line':int(行文)}
        条目.append(项)
    计数=0
    for 项 in 条目:
        if 'title' in 项:
            计数+=1
    return 详情列表(条目,文件+' · '+翻译('detail.locations.count',{'count':计数}),翻译)

def 控制详情(名称,参数,文本,json值,翻译):
    """从已记录输出格式派生实体列表与操作回执。"""
    目标=参数串(参数,'target') or 参数串(参数,'agent_id') or 参数串(参数,'sessionId') or 参数串(参数,'job_id')
    if 名称=='list_agents':
        return 智能体列表(文本,json值,翻译)
    if 名称=='job_list':
        return 后台列表(文本,翻译)
    if 名称=='terminal_list':
        return 终端列表(文本,翻译)
    if 名称=='lsp':
        return 语言服务详情(参数,文本,翻译)
    if 名称=='spawn_teammate':
        if not 详情记录(json值) or 'member' not in json值 or not 详情记录(json值['member']):
            return None
        return 详情列表(检视条目(json值['member'],翻译),参数串(参数,'name'),翻译)
    if 名称=='team_task_create' or 名称=='team_task_get' or 名称=='team_task_update':
        if not 详情记录(json值) or 'subject' not in json值 or not isinstance(json值['subject'],str):
            return None
        return 详情列表(检视条目(json值,翻译),json值['subject'],翻译)
    if 名称=='team_task_list':
        if not 详情记录(json值) or 'tasks' not in json值 or not isinstance(json值['tasks'],list):
            return None
        if 'nextCursor' in json值 and not isinstance(json值['nextCursor'],(int,float)):
            return None
        if 'nextCursor' in json值 and isinstance(json值['nextCursor'],bool):
            return None
        模型=详情列表(检视条目(json值['tasks'],翻译),翻译('detail.tasks.count',{'count':len(json值['tasks'])}),翻译)
        if 'nextCursor' in json值:
            模型['caption']=翻译('detail.tasks.nextPage',{'cursor':str(json值['nextCursor'])})
        return 模型
    if 名称=='send_message':
        状态=json值['status'] if 详情记录(json值) and 'status' in json值 else None
        if 状态=='accepted' or 状态=='queued':
            return 回执(目标,{
                'label':翻译('detail.status.queued' if 状态=='queued' else 'detail.receipt.delivered'),
                'tone':'warning' if 状态=='queued' else 'success',
            },翻译,[],参数串(参数,'message'))
        if 文本=='message delivered to agent '+目标:
            return 回执(目标,{'label':翻译('detail.receipt.delivered'),'tone':'success'},翻译,[],参数串(参数,'message'))
        return None
    if 名称=='interrupt_agent':
        if 详情记录(json值) and 'previousStatus' in json值 and isinstance(json值['previousStatus'],str):
            return 回执(目标,{'label':翻译('detail.receipt.interrupt'),'tone':'warning'},翻译,[{'label':翻译('detail.field.previousStatus'),'value':详情徽章(json值['previousStatus'],翻译)['label']}])
        if 文本=='interrupt requested for agent '+目标:
            return 回执(目标,{'label':翻译('detail.receipt.interrupt'),'tone':'warning'},翻译)
        return None
    if 名称=='wait_agent':
        if not 详情记录(json值) or 'timedOut' not in json值 or not isinstance(json值['timedOut'],bool):
            return None
        无进展=json值['noProgress'] if 'noProgress' in json值 else None
        if 详情记录(无进展) and 'message' in 无进展 and isinstance(无进展['message'],str):
            return 详情列表([{'title':翻译('detail.wait.noProgress'),'description':无进展['message'],'fields':[]}],翻译('detail.wait.noProgress'),翻译)
        return 回执(翻译('detail.wait.title'),{'label':翻译('detail.wait.timeout' if json值['timedOut'] else 'detail.wait.changed'),'tone':'neutral'},翻译)
    if 名称=='subagent':
        启动=子智能体启动.match(文本)
        if 启动 is not None:
            字段键='detail.field.agent' if 启动.group(1)=='subagent' else 'detail.field.job'
            return 回执(参数串(参数,'prompt'),{'label':翻译('detail.receipt.started'),'tone':'info'},翻译,[{'label':翻译(字段键),'value':启动.group(2)}])
        return 详情列表([{
            'title':翻译('detail.agent.reply'),'markdown':文本,'fields':[],
            'groups':[{'label':翻译('detail.field.task'),'items':[{'description':参数串(参数,'prompt'),'fields':[]}]}],
        }],翻译('detail.agent.reply'),翻译)
    if 名称=='list_subagent_models':
        条目=[]
        for 行 in 文本.split('\n'):
            切开=行.find(' — ')
            if 切开<0:
                条目.append({'description':行,'fields':[]})
            else:
                条目.append({'title':行[:切开],'description':行[切开+3:],'fields':[]})
        return 详情列表(条目,参数串(参数,'model') or 参数串(参数,'provider') or 翻译('detail.models.title'),翻译)
    if 名称=='job_output':
        匹配=后台状态.search(文本)
        if 匹配 is None:
            return None
        输出=文本[:匹配.start()]
        截断=输出.endswith(输出截断)
        代码=输出[:-len(输出截断)] if 截断 else 输出
        说明段=[]
        if 匹配.group(2) is not None:
            说明段.append(匹配.group(2))
        if 截断:
            说明段.append(翻译('detail.output.truncated'))
        说明=' · '.join(说明段)
        徽章=详情徽章(匹配.group(1),翻译)
        项={'title':目标,'badge':徽章,'fields':[],'code':{'text':代码}}
        if 说明!='':
            项['description']=说明
        模型=详情列表([项],目标+' · '+徽章['label'],翻译)
        模型['expandedSummary']=目标
        return 模型
    if 名称=='job_kill':
        if 文本=='requested cancellation of job '+目标:
            return 回执(目标,{'label':翻译('detail.receipt.cancel'),'tone':'warning'},翻译,[],参数串(参数,'reason'))
        if 文本.startswith('job '+目标+' had already finished '):
            return 回执(目标,{'label':翻译('detail.receipt.alreadyFinished'),'tone':'neutral'},翻译)
        return None
    if 名称=='terminal_open':
        匹配=终端打开.match(文本)
        if 匹配 is None:
            return None
        标识=匹配.group(1)
        名=匹配.group(2)
        项={'title':标识 if 名 is None else 名,'badge':{'label':翻译('detail.receipt.started'),'tone':'info'},'fields':[{'label':翻译('detail.field.type'),'value':匹配.group(3)}],'code':{'text':匹配.group(4)}}
        if 名 is not None:
            项['subtitle']=标识
        return 详情列表([项],标识 if 名 is None else 名,翻译)
    if 名称=='terminal_read':
        匹配=终端读取.search(文本)
        if 匹配 is None:
            return None
        项={'title':目标,'subtitle':翻译('detail.output.lines',{'begin':匹配.group(1),'end':匹配.group(2),'total':匹配.group(3)}),'fields':[],'code':{'text':文本[:匹配.start()]}}
        if 匹配.group(4) is not None:
            项['description']=翻译('detail.output.truncated')
        return 详情列表([项],目标,翻译)
    if 名称=='terminal_signal':
        匹配=终端信号.match(文本)
        if 匹配 is None:
            return None
        return 回执(目标,{'label':翻译('detail.receipt.signal'),'tone':'success'},翻译,[{'label':翻译('detail.field.signal'),'value':匹配.group(1)},{'label':翻译('detail.field.processGroup'),'value':匹配.group(2)}])
    if 名称=='terminal_close':
        if 文本=='closed terminal session '+目标:
            return 回执(目标,{'label':翻译('detail.receipt.closed'),'tone':'neutral'},翻译)
        if 文本=='terminal session '+目标+' was already closing':
            return 回执(目标,{'label':翻译('detail.receipt.closing'),'tone':'neutral'},翻译)
        return None
    return None
