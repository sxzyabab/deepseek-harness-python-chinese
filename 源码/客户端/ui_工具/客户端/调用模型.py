import json
from ....工具.工作区路径 import 是否绝对工作区路径,相对化到工作目录,缩写家目录路径
from .已记录路径 import 已记录绝对路径

__all__=['分类工具','工具标题键','结果文本','格式化工具体','工具行模型']

变体标题键={
    'search':'tool.title.search',
    'read':'tool.title.read',
    'bash':'tool.title.bash',
    'write':'tool.title.write',
    'edit':'tool.title.edit',
    'code':'tool.title.code',
    'others':'tool.title.generic',
}
工具变体={
    'bash':'bash',
    'pwsh':'bash',
    'read':'read',
    'read_image':'read',
    'web_fetch':'read',
    'web_search':'search',
    'grep':'search',
    'glob':'search',
    'write':'write',
    'edit':'edit',
    'run_code':'code',
    'cordis_package_inspect':'read',
    'cordis_runtime_inspect':'read',
    'cordis_run':'others',
    'cordis_stop':'others',
    'cordis_undefine':'others',
}
工具标题键表={
    'cordis_package_inspect':'tool.title.inspect',
    'cordis_runtime_inspect':'tool.title.inspect',
    'cordis_run':'tool.title.runCordis',
    'cordis_stop':'tool.title.stopCordis',
    'cordis_undefine':'tool.title.removeCordis',
    'pwsh':'tool.title.pwsh',
    'read_image':'tool.title.readImage',
    'todo_write':'todo.rowTitle',
    'ask_user_question':'ask.rowTitle',
    'create_goal':'tool.title.createGoal',
    'get_goal':'tool.title.getGoal',
    'update_goal':'tool.title.updateGoal',
    'schedule_create':'tool.title.createSchedule',
    'schedule_list':'tool.title.listSchedules',
    'schedule_delete':'tool.title.deleteSchedule',
    'schedule_update':'tool.title.updateSchedule',
    'cordis_inspect_list':'tool.title.inspectProviders',
    'cordis_inspect_query':'tool.title.queryRuntime',
    'cordis_inspect_self':'tool.title.inspectPlugins',
    'workflow':'tool.title.workflow',
    'ralph':'tool.title.ralph',
    'session_event_read':'tool.title.readEvent',
    'session_event_search':'tool.title.searchEvents',
    'session_event_trace':'tool.title.traceEvent',
    'session_search':'tool.title.searchSessions',
    'session_trace':'tool.title.traceSession',
    'list_subagent_models':'tool.title.listModels',
    'subagent':'tool.title.subagent',
    'list_agents':'tool.title.listAgents',
    'send_message':'tool.title.sendMessage',
    'interrupt_agent':'tool.title.interruptAgent',
    'job_list':'tool.title.listJobs',
    'job_output':'tool.title.readJob',
    'job_kill':'tool.title.killJob',
    'terminal_open':'tool.title.openTerminal',
    'terminal_read':'tool.title.readTerminal',
    'terminal_list':'tool.title.listTerminals',
    'terminal_signal':'tool.title.signalTerminal',
    'terminal_close':'tool.title.closeTerminal',
    'lsp':'tool.title.lsp',
    'spawn_teammate':'tool.title.spawnTeammate',
    'team_task_create':'tool.title.createTeamTask',
    'team_task_get':'tool.title.getTeamTask',
    'team_task_update':'tool.title.updateTeamTask',
    'team_task_list':'tool.title.listTeamTasks',
    'wait_agent':'tool.title.waitAgent',
}
摘要键={
    'bash':('description','command'),
    'read':('path','file_path','url'),
    'search':('query','pattern','url'),
    'write':('path','file_path'),
    'edit':('path','file_path'),
    'code':('description',),
    'others':(),
}
文件路径键=('path','file_path')
文件路径变体=frozenset(['read','write','edit'])

def 分类工具(工具名):
    '匹配的变体。未知时为 others'
    if 工具名 in 工具变体:
        return 工具变体[工具名]
    return 'others'

def 工具标题键(工具名):
    '工具自有标题键，否则用变体标题键'
    if 工具名 in 工具标题键表:
        return 工具标题键表[工具名]
    return 变体标题键[分类工具(工具名)]

def 派生自动拒绝(块):
    '错误名为 AutoReviewDeniedError 且码为 AUTO_REVIEW_DENIED 时取出原因'
    if 'kind' not in 块 or 块.get('isError') is not True:
        return None
    错误=块.get('error')
    if not isinstance(错误,dict):
        return None
    if 错误.get('name')!='AutoReviewDeniedError' or 错误.get('code')!='AUTO_REVIEW_DENIED':
        return None
    原因=错误.get('reason')
    return {'reason':原因 if isinstance(原因,str) else None}

def 结果文本(节点):
    '文本块原样，其余块格式化成 JSON。失败且没有内容时用 name: code'
    段=[]
    for 内容块 in 节点['content']:
        if isinstance(内容块,dict) and 内容块.get('type')=='text':
            段.append(内容块.get('text') if isinstance(内容块.get('text'),str) else '')
        else:
            段.append(json.dumps(内容块,ensure_ascii=False,indent=2))
    if len(段)==0 and 'error' in 节点 and 节点['error'] is not None:
        错误=节点['error']
        段.append(str(错误.get('name'))+': '+str(错误.get('code')))
    return '\n'.join(段)

def 解析参数(参数原文):
    '非 JSON 则 None'
    try:
        return json.loads(参数原文)
    except json.JSONDecodeError:
        return None

def 首行(文本):
    '无换行则全文'
    位置=文本.find('\n')
    if 位置==-1:
        return 文本
    return 文本[:位置]

def 挑字符串(参数,键列表):
    '按顺序取第一个非空字符串'
    for 键 in 键列表:
        值=参数.get(键)
        if isinstance(值,str) and 值!='':
            return 值
    return None

def 派生摘要(变体,参数原文):
    '非对象则用原文首行。search 的 queries 用逗号接首行'
    已解析=解析参数(参数原文)
    if not isinstance(已解析,dict):
        return 首行(参数原文)
    if 变体=='search' and isinstance(已解析.get('queries'),list):
        查询=[]
        for 项 in 已解析['queries']:
            if isinstance(项,str) and 项!='':
                查询.append(首行(项))
        if len(查询)>0:
            return ', '.join(查询)
    挑中=挑字符串(已解析,摘要键[变体])
    if 挑中 is not None:
        return 首行(挑中)
    for 值 in 已解析.values():
        if isinstance(值,str) and 值!='':
            return 首行(值)
    return 首行(参数原文)

def 参数摘要(变体,参数,工作区,主目录):
    '文件工具取完整 file_path。其余取 description 首行'
    if 变体 in 文件路径变体:
        路径=参数.text('file_path') if 参数.complete('file_path') else None
        文件路径=None
        if isinstance(路径,str) and 路径!='' and 参数.complete('file_path'):
            文件路径=首行(路径)
        摘要=''
        if 文件路径 is not None:
            摘要=缩写家目录路径(相对化到工作目录(文件路径,工作区),主目录)
        return {'summary':摘要,'filePath':文件路径}
    描述=参数.text('description')
    if 描述 is None:
        return {'summary':'','filePath':None}
    return {'summary':首行(描述),'filePath':None}

def 派生文件路径(变体,参数原文):
    '非文件工具变体则无路径'
    if 变体 not in 文件路径变体:
        return None
    已解析=解析参数(参数原文)
    if not isinstance(已解析,dict):
        return None
    挑中=挑字符串(已解析,文件路径键)
    if 挑中 is None:
        return None
    return 首行(挑中)

def 格式化工具体(变体,参数原文):
    '空参数没有输入段。code 变体展开体是程序本身'
    if 参数原文=='':
        return None
    已解析=解析参数(参数原文)
    if 已解析 is None:
        return 参数原文
    if 变体=='code' and isinstance(已解析,dict):
        代码=已解析.get('code')
        if isinstance(代码,str) and 代码!='':
            return 代码
    return json.dumps(已解析,ensure_ascii=False,indent=2)

def 工具行模型(工具名,块,工作区=None,主目录=None):
    '工具行所需字段。准备中没有参数原文'
    变体=分类工具(工具名)
    标题键=工具标题键(工具名)
    已结算='kind' in 块
    if 已结算:
        调用=块.get('call')
        if isinstance(调用,dict) and isinstance(调用.get('argsRaw'),str):
            参数原文=调用['argsRaw']
        elif isinstance(调用,dict) and 调用.get('argsRaw') is None:
            参数原文=''
        else:
            参数原文=''
    elif 块.get('phase')=='start':
        参数原文=块.get('argsRaw') if isinstance(块.get('argsRaw'),str) else ''
    else:
        参数原文=None
    主摘要=参数摘要(变体,块['args'],工作区,主目录)
    if 主摘要['filePath'] is not None:
        参数路径=主摘要['filePath']
    elif 参数原文 is None:
        参数路径=None
    else:
        参数路径=派生文件路径(变体,参数原文)
    记录路径=已记录绝对路径(块.get('meta'),'path') if 已结算 else None
    可用参数路径=参数路径 is not None and (
        是否绝对工作区路径(参数路径)
        or (已结算 and 块.get('isError') is not True and 块.get('parentCallId') is None)
    )
    if 参数路径 is None:
        文件路径=None
    elif 记录路径 is not None:
        文件路径=记录路径
    elif 可用参数路径:
        文件路径=参数路径
    else:
        文件路径=None
    if not 已结算:
        状态='preparing' if 块.get('phase')=='preparing' else 'running'
    else:
        错误=块.get('error')
        错误码=错误.get('code') if isinstance(错误,dict) else None
        if 错误码=='interrupted':
            状态='stopped'
        elif 块.get('isError') is True:
            状态='error'
        else:
            状态='ok'
    if 主摘要['summary']!='' or 参数原文 is None:
        基文=主摘要['summary']
    elif 参数原文=='':
        基文=块['callId']
    else:
        基文=缩写家目录路径(相对化到工作目录(派生摘要(变体,参数原文),工作区),主目录)
    段=[]
    if 标题键=='tool.title.generic' and 工具名!='':
        段.append(工具名)
    if 基文!='':
        段.append(基文)
    摘要=' · '.join(段)
    if 已结算:
        展平=结果文本(块)
        输出=展平 if 展平!='' else None
    else:
        输出=None
    错误摘要=首行(输出) if 状态=='error' and 输出 is not None else None
    体原文=None if 参数原文=='' else 参数原文
    return {
        'variant':变体,
        'titleKey':标题键,
        'summary':摘要,
        'filePath':文件路径,
        'bodyRaw':体原文,
        'output':输出,
        'errorSummary':错误摘要,
        'autoReviewDenial':派生自动拒绝(块),
        'state':状态,
    }
