import re
from ....工具输出.溢出策略 import 含溢出须知
from .文案 import 中文文案
from .详情模型共享 import 详情json,详情列表,详情记录,检视条目

__all__=['检视结果详情']

工作流完成=re.compile(r'^workflow "([\s\S]*?)" completed \(([0-9]+) agents?\)\.\nReturn value:\n([\s\S]*)$')
回合计数=re.compile(r'\b([0-9]+) rounds?\b')
检索块切=re.compile(r'\n(?=[0-9]+\. )')
检索块头=re.compile(r'^[0-9]+\. ')
片段形=re.compile(r'\n\s*Snippet: ([\s\S]*?)(?:\n\nResult cap reached\.|$)')
会话检索头=re.compile(r'^[0-9]+\. Session (\S+) — (.*)')
事件检索头=re.compile(r'^[0-9]+\. seq ([0-9]+) \| ([^|]+) \| ([^|]+) \| ([^\n]+)')
事件阅读=re.compile(r'^Session (\S+) — ([^\n]*)\nTarget event seq ([0-9]+):\n```json\n([\s\S]*?)\n```([\s\S]*)$')
追踪头=re.compile(r'^Session (\S+) — ([^\n]*)\n([\s\S]*)$')
字段行=re.compile(r'^\s*([^:]+): (.+)$')
列表前缀=re.compile(r'^(\s*)- ')
追踪字段={
    'Created':'detail.field.time',
    'Availability':'detail.field.availability',
    'Parent':'detail.field.parent',
    'Best match':'detail.field.bestMatch',
    'Target':'detail.field.target',
    'Replaced by':'detail.trace.replacedBy',
    'Replacement chain':'detail.trace.replacementChain',
    'Events replaced by target':'detail.trace.replaces',
    'Events cited directly as sources':'detail.trace.sources',
    'Direct derived events':'detail.trace.derived',
}
终结报告分隔='\nFinal report:\n'

def 日期文本(窗口,值,语言):
    '把时刻或原文格式化为当地短日期。失败则原文'
    try:
        日期=窗口.Date(值)
        毫秒=日期.getTime()
        if 毫秒!=毫秒:
            return str(值)
        return 窗口.Intl.DateTimeFormat(语言,{'dateStyle':'medium','timeStyle':'short'}).format(日期)
    except Exception:
        return str(值)

def cordis详情(名称,参数,值):
    '运行时检视 JSON'
    if not 详情记录(值):
        return None
    if 名称=='cordis_inspect_list':
        if not isinstance(值.get('providers'),list):
            return None
        return 详情列表(检视条目(值['providers']),中文文案('detail.providers.count',{'count':len(值['providers'])}))
    if 名称=='cordis_inspect_query':
        if 'data' not in 值 or not isinstance(值.get('provider'),str) or not isinstance(值.get('method'),str):
            return None
        return 详情列表(检视条目(值['data']),值['provider']+'.'+值['method'])
    if 名称=='cordis_inspect_self':
        if isinstance(值.get('plugins'),list):
            return 详情列表(检视条目(值['plugins']),中文文案('detail.plugins.count',{'count':len(值['plugins'])}))
        摘要=参数.get('pluginId')
        if 摘要 is None:
            摘要=参数.get('packageId')
        if 摘要 is None:
            摘要=值.get('mode')
        return 详情列表(检视条目(值),str(摘要))
    return None

def 工作流详情(名称,参数,文本):
    'workflow 或 ralph 文本报告'
    if 名称=='workflow':
        匹配=工作流完成.search(文本)
        if 匹配 is None:
            return None
        值=详情json(匹配.group(3))
        if 值 is None:
            return None
        头={
            'title':匹配.group(1),
            'badge':{'label':中文文案('detail.status.completed'),'tone':'success'},
            'fields':[{'label':中文文案('detail.field.agents'),'value':匹配.group(2)}],
        }
        if isinstance(参数.get('code'),str):
            头['groups']=[{
                'label':中文文案('detail.workflow.script'),
                'items':[{'fields':[],'code':{'text':参数['code'],'language':'javascript'}}],
            }]
        return 详情列表([头]+检视条目(值),匹配.group(1))
    切开=文本.find(终结报告分隔)
    if 切开<0:
        return None
    头文=文本[:切开]
    轮次=回合计数.search(头文)
    轮次数=None if 轮次 is None else 轮次.group(1)
    报告=详情json(文本[切开+len(终结报告分隔):])
    if not 详情记录(报告) or not isinstance(报告.get('summary'),str):
        return None
    if not isinstance(报告.get('evidence'),list) or not all(isinstance(项,str) for 项 in 报告['evidence']):
        return None
    if not isinstance(报告.get('nextSteps'),list) or not all(isinstance(项,str) for 项 in 报告['nextSteps']):
        return None
    if not isinstance(报告.get('blocker'),str):
        return None
    if 头文.startswith('Ralph worker reported completion '):
        徽章={'label':中文文案('detail.ralph.reportedComplete'),'tone':'success'}
    elif 头文.startswith('Ralph worker reported a blocker '):
        徽章={'label':中文文案('detail.ralph.reportedBlocker'),'tone':'warning'}
    elif 头文.startswith('Ralph reached its '):
        徽章={'label':中文文案('detail.ralph.limit'),'tone':'warning'}
    else:
        return None
    分组=[]
    if len(报告['nextSteps'])>0:
        分组.append({'label':中文文案('detail.report.nextSteps'),'items':[{'fields':[],'lines':报告['nextSteps']}]})
    if isinstance(参数.get('objective'),str):
        分组.append({'label':中文文案('detail.field.task'),'items':[{'fields':[],'description':参数['objective']}]})
    字段=[]
    if 轮次数 is not None:
        字段.append({'label':中文文案('detail.goal.rounds'),'value':轮次数})
    if 报告['blocker']!='':
        字段.append({'label':中文文案('detail.goal.reason'),'value':报告['blocker']})
    条目={'title':报告['summary'],'badge':徽章,'fields':字段,'groups':分组}
    if len(报告['evidence'])>0:
        条目['lines']=报告['evidence']
    return 详情列表([条目],报告['summary'])

def 文本字段(文本,窗口,语言):
    '追踪报告里已识别的字段行'
    字段=[]
    for 行 in 文本.split('\n'):
        匹配=字段行.search(行)
        if 匹配 is None:
            continue
        名=匹配.group(1)
        内容=匹配.group(2)
        if 名 not in 追踪字段:
            continue
        if 名=='Created':
            值=日期文本(窗口,内容,语言)
        elif 内容=='none':
            值=中文文案('detail.none')
        else:
            值=内容
        字段.append({'label':中文文案(追踪字段[名]),'value':值})
    return 字段

def 检索详情(名称,文本,窗口,语言):
    '会话或事件检索结果'
    if 文本=='No prior session matches found.' or 文本.endswith('\n\nNo prior event matches found.'):
        return 详情列表([],中文文案('detail.matches.count',{'count':0}))
    块表=[]
    for 块 in 检索块切.split(文本):
        if 检索块头.search(块) is not None:
            块表.append(块)
    if len(块表)==0:
        return None
    条目表=[]
    for 块 in 块表:
        片段=片段形.search(块)
        片段文=None if 片段 is None else 片段.group(1)
        if 名称=='session_search':
            匹配=会话检索头.search(块)
            if 匹配 is None:
                return None
            条目={'title':匹配.group(2),'subtitle':匹配.group(1),'fields':文本字段(块,窗口,语言)}
            if 片段文 is not None:
                条目['description']=片段文.rstrip()
            条目表.append(条目)
        else:
            匹配=事件检索头.search(块)
            if 匹配 is None:
                return None
            标题=匹配.group(2) if 片段文 is None else 片段文.rstrip()
            条目表.append({
                'title':标题,
                'subtitle':匹配.group(2).strip()+' · #'+匹配.group(1),
                'fields':[
                    {'label':中文文案('detail.field.time'),'value':日期文本(窗口,匹配.group(4),语言)},
                    {'label':中文文案('detail.field.surface'),'value':匹配.group(3).strip()},
                ],
            })
    模型=详情列表(条目表,中文文案('detail.matches.count',{'count':len(条目表)}))
    if 'Result cap reached.' in 文本:
        模型['caption']=中文文案('detail.matches.capped')
    return 模型

def 事件阅读详情(文本,窗口,语言):
    'session_event_read 文本'
    匹配=事件阅读.search(文本)
    if 匹配 is None:
        return None
    事件=详情json(匹配.group(4))
    if not 详情记录(事件) or not isinstance(事件.get('type'),str) or not 详情记录(事件.get('data')):
        return None
    字段=[{'label':中文文案('detail.field.seq'),'value':匹配.group(3)}]
    if isinstance(事件.get('time'),(int,float)) and not isinstance(事件.get('time'),bool):
        字段.append({'label':中文文案('detail.field.time'),'value':日期文本(窗口,事件['time'],语言)})
    分组=[]
    相邻=匹配.group(5)
    if isinstance(相邻,str) and 相邻.strip()!='':
        分组.append({'label':中文文案('detail.event.neighbors'),'items':[{'fields':[],'description':相邻.strip()}]})
    条目=[
        {'title':事件['type'],'subtitle':匹配.group(2)+' · '+匹配.group(1),'fields':字段},
    ]
    条目.extend(检视条目(事件['data']))
    if len(分组)>0:
        条目.append({'fields':[],'groups':分组})
    return 详情列表(条目,事件['type']+' · #'+匹配.group(3))

def 追踪详情(名称,文本,窗口,语言):
    'session_trace 或 session_event_trace'
    匹配=追踪头.search(文本)
    if 匹配 is None:
        return None
    if 名称=='session_event_trace':
        return 详情列表([{
            'title':匹配.group(2),
            'subtitle':匹配.group(1),
            'fields':文本字段(匹配.group(3),窗口,语言),
        }],匹配.group(2))
    节=匹配.group(3).split('\n\n')
    条目表=[{
        'title':匹配.group(2),
        'subtitle':匹配.group(1),
        'fields':文本字段(节[0] if len(节)>0 else '',窗口,语言),
    }]
    for 段 in 节[1:]:
        断=段.find('\n')
        if 段.startswith('Ancestors (nearest first):'):
            标签=中文文案('detail.trace.ancestors')
        elif 段.startswith('Descendants:'):
            标签=中文文案('detail.trace.descendants')
        else:
            return None
        if 断<0:
            return None
        体=段[断+1:]
        if 体=='- none' or 体=='- none (target is a root session)':
            条目表.append({'title':标签,'fields':[],'description':中文文案('detail.none')})
        else:
            行表=[]
            for 行 in 体.split('\n'):
                行表.append(列表前缀.sub(r'\1',行))
            条目表.append({'title':标签,'fields':[],'lines':行表})
    return 详情列表(条目表,匹配.group(2))

def 检视结果详情(名称,参数,文本,json值,窗口,语言):
    '成功的检视、查询与工作流。带溢出须知则不认'
    if 含溢出须知(文本):
        return None
    if 名称=='cordis_inspect_list' or 名称=='cordis_inspect_query' or 名称=='cordis_inspect_self':
        return cordis详情(名称,参数,json值)
    if 名称=='workflow' or 名称=='ralph':
        return 工作流详情(名称,参数,文本)
    if 名称=='session_search' or 名称=='session_event_search':
        return 检索详情(名称,文本,窗口,语言)
    if 名称=='session_event_read':
        return 事件阅读详情(文本,窗口,语言)
    if 名称=='session_trace' or 名称=='session_event_trace':
        return 追踪详情(名称,文本,窗口,语言)
    return None
