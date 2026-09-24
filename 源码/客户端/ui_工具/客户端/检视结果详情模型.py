import re
from datetime import datetime as 日期时间,timezone as 时区
from ....工具输出.溢出策略.须知 import 含溢出须知
from .详情模型共享 import 详情json,详情列表,详情记录,检视条目

__all__=['检视结果详情']

工作流完成=re.compile(r'^workflow "([\s\S]*?)" completed \(([0-9]+) agents?\)\.\nReturn value:\n([\s\S]*)\Z',re.ASCII)
回合计数=re.compile(r'\b([0-9]+) rounds?\b',re.ASCII)
检索块切=re.compile(r'\n(?=[0-9]+\. )')
检索块头=re.compile(r'^[0-9]+\. ')
片段形=re.compile(r'\n\s*Snippet: ([\s\S]*?)(?:\n\nResult cap reached\.|\Z)')
会话检索头=re.compile(r'^[0-9]+\. Session (\S+) — (.*)')
事件检索头=re.compile(r'^[0-9]+\. seq ([0-9]+) \| ([^|]+) \| ([^|]+) \| ([^\n]+)',re.ASCII)
事件阅读=re.compile(r'^Session (\S+) — ([^\n]*)\nTarget event seq ([0-9]+):\n```json\n([\s\S]*?)\n```([\s\S]*)\Z',re.ASCII)
追踪头=re.compile(r'^Session (\S+) — ([^\n]*)\n([\s\S]*)\Z')
字段行=re.compile(r'^\s*([^:]+): (.+)\Z')
列表前缀=re.compile(r'^(\s*)- ')

追踪字段={
    'Created':'detail.field.time','Availability':'detail.field.availability','Parent':'detail.field.parent',
    'Best match':'detail.field.bestMatch','Target':'detail.field.target',
    'Replaced by':'detail.trace.replacedBy','Replacement chain':'detail.trace.replacementChain',
    'Events replaced by target':'detail.trace.replaces','Events cited directly as sources':'detail.trace.sources',
    'Direct derived events':'detail.trace.derived',
}
终结报告分隔='\nFinal report:\n'

def 日期文本(值,语言):
    """把时刻或原文格式化为当地短日期。"""
    if isinstance(值,bool):
        return str(值)
    if isinstance(值,(int,float)):
        时刻=日期时间.fromtimestamp(值/1000,tz=时区.utc)
    elif isinstance(值,str):
        try:
            时刻=日期时间.strptime(值,'%Y-%m-%dT%H:%M:%S.%fZ').replace(tzinfo=时区.utc)
        except ValueError:
            try:
                时刻=日期时间.strptime(值,'%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=时区.utc)
            except ValueError:
                return str(值)
    else:
        return str(值)
    try:
        return 时刻.astimezone().strftime('%Y-%m-%d %H:%M')
    except (OSError,ValueError,OverflowError):
        return str(值)

def cordis详情(名称,参数,值,翻译):
    """运行时检视 JSON。"""
    if not 详情记录(值):
        return None
    if 名称=='cordis_inspect_list':
        if 'providers' not in 值 or not isinstance(值['providers'],list):
            return None
        return 详情列表(检视条目(值['providers'],翻译),翻译('detail.providers.count',{'count':len(值['providers'])}),翻译)
    if 名称=='cordis_inspect_query':
        if 'data' not in 值 or not isinstance(值['provider'],str) or not isinstance(值['method'],str):
            return None
        return 详情列表(检视条目(值['data'],翻译),值['provider']+'.'+值['method'],翻译)
    if 名称=='cordis_inspect_self':
        if 'plugins' in 值 and isinstance(值['plugins'],list):
            return 详情列表(检视条目(值['plugins'],翻译),翻译('detail.plugins.count',{'count':len(值['plugins'])}),翻译)
        标识=参数['pluginId'] if 'pluginId' in 参数 else (参数['packageId'] if 'packageId' in 参数 else (值['mode'] if 'mode' in 值 else ''))
        return 详情列表(检视条目(值,翻译),str(标识),翻译)
    return None

def 工作流详情(名称,参数,文本,翻译):
    """workflow / ralph 文本报告。"""
    if 名称=='workflow':
        匹配=工作流完成.match(文本)
        if 匹配 is None:
            return None
        值=详情json(匹配.group(3))
        if 值 is None:
            return None
        头={'title':匹配.group(1),'badge':{'label':翻译('detail.status.completed'),'tone':'success'},'fields':[{'label':翻译('detail.field.agents'),'value':匹配.group(2)}]}
        if 'code' in 参数 and isinstance(参数['code'],str):
            头['groups']=[{'label':翻译('detail.workflow.script'),'items':[{'fields':[],'code':{'text':参数['code'],'language':'javascript'}}]}]
        return 详情列表([头]+检视条目(值,翻译),匹配.group(1),翻译)
    切开=文本.find(终结报告分隔)
    if 切开<0:
        return None
    头=文本[:切开]
    回合匹配=回合计数.search(头)
    回合=None if 回合匹配 is None else 回合匹配.group(1)
    报告=详情json(文本[切开+len(终结报告分隔):])
    if not 详情记录(报告) or 'summary' not in 报告 or not isinstance(报告['summary'],str):
        return None
    if 'evidence' not in 报告 or not isinstance(报告['evidence'],list):
        return None
    for 证 in 报告['evidence']:
        if not isinstance(证,str):
            return None
    if 'nextSteps' not in 报告 or not isinstance(报告['nextSteps'],list):
        return None
    for 步 in 报告['nextSteps']:
        if not isinstance(步,str):
            return None
    if 'blocker' not in 报告 or not isinstance(报告['blocker'],str):
        return None
    if 头.startswith('Ralph worker reported completion '):
        徽章={'label':翻译('detail.ralph.reportedComplete'),'tone':'success'}
    elif 头.startswith('Ralph worker reported a blocker '):
        徽章={'label':翻译('detail.ralph.reportedBlocker'),'tone':'warning'}
    elif 头.startswith('Ralph reached its '):
        徽章={'label':翻译('detail.ralph.limit'),'tone':'warning'}
    else:
        return None
    分组=[]
    if len(报告['nextSteps'])>0:
        分组.append({'label':翻译('detail.report.nextSteps'),'items':[{'fields':[],'lines':报告['nextSteps']}]})
    if 'objective' in 参数 and isinstance(参数['objective'],str):
        分组.append({'label':翻译('detail.field.task'),'items':[{'fields':[],'description':参数['objective']}]})
    字段=[] if 回合 is None else [{'label':翻译('detail.goal.rounds'),'value':回合}]
    if 报告['blocker']!='':
        字段.append({'label':翻译('detail.goal.reason'),'value':报告['blocker']})
    项={'title':报告['summary'],'badge':徽章,'fields':字段}
    if len(报告['evidence'])>0:
        项['lines']=报告['evidence']
    if len(分组)>0:
        项['groups']=分组
    return 详情列表([项],报告['summary'],翻译)

def 文本字段(文本,翻译,语言):
    """追踪报告里已识别的字段行。"""
    字段=[]
    for 行 in 文本.split('\n'):
        匹配=字段行.match(行)
        if 匹配 is None:
            continue
        名=匹配.group(1)
        值=匹配.group(2)
        if 名 not in 追踪字段:
            continue
        if 名=='Created':
            展示=日期文本(值,语言)
        elif 值=='none':
            展示=翻译('detail.none')
        else:
            展示=值
        字段.append({'label':翻译(追踪字段[名]),'value':展示})
    return 字段

def 检索详情(名称,文本,翻译,语言):
    """会话或事件检索结果。"""
    if 文本=='No prior session matches found.' or 文本.endswith('\n\nNo prior event matches found.'):
        return 详情列表([],翻译('detail.matches.count',{'count':0}),翻译)
    块表=[块 for 块 in 检索块切.split(文本) if 检索块头.match(块) is not None]
    if len(块表)==0:
        return None
    条目=[]
    for 块 in 块表:
        片段匹配=片段形.search(块)
        片段=None if 片段匹配 is None else 片段匹配.group(1)
        if 名称=='session_search':
            匹配=会话检索头.match(块)
            if 匹配 is None:
                return None
            项={'title':匹配.group(2),'subtitle':匹配.group(1),'fields':文本字段(块,翻译,语言)}
            if 片段 is not None:
                项['description']=片段.rstrip()
            条目.append(项)
        else:
            匹配=事件检索头.match(块)
            if 匹配 is None:
                return None
            标题=片段.rstrip() if 片段 is not None else 匹配.group(2)
            条目.append({'title':标题,'subtitle':匹配.group(2).strip()+' · #'+匹配.group(1),'fields':[{'label':翻译('detail.field.time'),'value':日期文本(匹配.group(4),语言)},{'label':翻译('detail.field.surface'),'value':匹配.group(3).strip()}]})
    模型=详情列表(条目,翻译('detail.matches.count',{'count':len(条目)}),翻译)
    if 'Result cap reached.' in 文本:
        模型['caption']=翻译('detail.matches.capped')
    return 模型

def 事件阅读详情(文本,翻译,语言):
    """session_event_read 文本。"""
    匹配=事件阅读.match(文本)
    if 匹配 is None:
        return None
    事件=详情json(匹配.group(4))
    if not 详情记录(事件) or 'type' not in 事件 or not isinstance(事件['type'],str):
        return None
    if 'data' not in 事件 or not 详情记录(事件['data']):
        return None
    字段=[{'label':翻译('detail.field.seq'),'value':匹配.group(3)}]
    if 'time' in 事件 and isinstance(事件['time'],(int,float)) and not isinstance(事件['time'],bool):
        字段.append({'label':翻译('detail.field.time'),'value':日期文本(事件['time'],语言)})
    分组=[]
    邻=匹配.group(5).strip() if 匹配.group(5) is not None else ''
    if 邻!='':
        分组.append({'label':翻译('detail.event.neighbors'),'items':[{'fields':[],'description':邻}]})
    列表=[{'title':事件['type'],'subtitle':匹配.group(2)+' · '+匹配.group(1),'fields':字段}]
    列表.extend(检视条目(事件['data'],翻译))
    if len(分组)>0:
        列表.append({'fields':[],'groups':分组})
    return 详情列表(列表,事件['type']+' · #'+匹配.group(3),翻译)

def 追踪详情(名称,文本,翻译,语言):
    """session_trace / session_event_trace。"""
    匹配=追踪头.match(文本)
    if 匹配 is None:
        return None
    if 名称=='session_event_trace':
        return 详情列表([{'title':匹配.group(2),'subtitle':匹配.group(1),'fields':文本字段(匹配.group(3),翻译,语言)}],匹配.group(2),翻译)
    段表=匹配.group(3).split('\n\n')
    条目=[{'title':匹配.group(2),'subtitle':匹配.group(1),'fields':文本字段(段表[0] if len(段表)>0 else '',翻译,语言)}]
    for 段 in 段表[1:]:
        首换=段.find('\n')
        if 段.startswith('Ancestors (nearest first):'):
            标签=翻译('detail.trace.ancestors')
        elif 段.startswith('Descendants:'):
            标签=翻译('detail.trace.descendants')
        else:
            return None
        if 首换<0:
            return None
        体=段[首换+1:]
        项={'title':标签,'fields':[]}
        if 体=='- none' or 体=='- none (target is a root session)':
            项['description']=翻译('detail.none')
        else:
            项['lines']=[列表前缀.sub(r'\1',行,count=1) for 行 in 体.split('\n')]
        条目.append(项)
    return 详情列表(条目,匹配.group(2),翻译)

def 检视结果详情(名称,参数,文本,json值,翻译,语言):
    """把成功的检视、查询与工作流文本呈现为具名记录。"""
    if 含溢出须知(文本):
        return None
    if 名称=='cordis_inspect_list' or 名称=='cordis_inspect_query' or 名称=='cordis_inspect_self':
        return cordis详情(名称,参数,json值,翻译)
    if 名称=='workflow' or 名称=='ralph':
        return 工作流详情(名称,参数,文本,翻译)
    if 名称=='session_search' or 名称=='session_event_search':
        return 检索详情(名称,文本,翻译,语言)
    if 名称=='session_event_read':
        return 事件阅读详情(文本,翻译,语言)
    if 名称=='session_trace' or 名称=='session_event_trace':
        return 追踪详情(名称,文本,翻译,语言)
    return None
