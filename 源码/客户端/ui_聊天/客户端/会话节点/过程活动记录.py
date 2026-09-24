import json,re
from ..约定.聊天节点 import 是运行中工具

__all__=['过程活动记录']

空白折叠=re.compile(r'\s+',re.ASCII)
段落切开=re.compile(r'\r?\n[\t ]*\r?\n')

现场工具详情最大字=160
现场工具详情键=(
    'title','description','objective','task','task_name','name','question','questions','prompt','message',
    'command','cmd','queries','query','pattern','url','uri','file_path','path','target','action','status',
)
命令名表=frozenset(['bash','pwsh','exec_command','write_stdin'])
计划名表=frozenset(['todo_write','create_goal','update_goal','get_goal'])

def 活动种类(名称):
    """工具名 → 过程活动类别。"""
    if 名称=='read':
        return 'read'
    if 名称=='read_image':
        return 'readImage'
    if 名称=='grep' or 名称=='glob' or 名称.endswith('_inspect'):
        return 'search'
    if 名称=='write':
        return 'write'
    if 名称=='edit' or 名称=='apply_patch':
        return 'edit'
    if 名称 in 命令名表 or 名称.startswith('terminal_'):
        return 'commands'
    if 名称=='run_code':
        return 'code'
    if 名称=='web_search':
        return 'webSearch'
    if 名称=='web_fetch':
        return 'webFetch'
    if 名称=='subagent' or 名称.startswith('subagent_'):
        return 'subagents'
    if 名称 in 计划名表:
        return 'plan'
    if 名称=='ask_user_question' or 名称=='request_user_input':
        return 'questions'
    return 'tools'

def 规范现场工具详情(值):
    """压空白并按码点截到上限。"""
    if isinstance(值,str):
        文本=值
    elif isinstance(值,list) and all(isinstance(项,str) for 项 in 值):
        文本=', '.join(值)
    else:
        文本=''
    规范化=空白折叠.sub(' ',文本,count=0).strip()
    字列表=list(规范化)
    if len(字列表)<=现场工具详情最大字:
        return 规范化
    return ''.join(字列表[:现场工具详情最大字-1]).rstrip()+'…'

def 提问详情(值):
    """问题列表里第一条非空 question。"""
    if not isinstance(值,list):
        return ''
    for 项 in 值:
        if not isinstance(项,dict):
            continue
        详情=规范现场工具详情(项['question'] if 'question' in 项 else None)
        if 详情!='':
            return 详情
    return ''

def 现场推理详情(节点列表):
    """自后向前取运行中助手步骤的推理段。"""
    下标=len(节点列表)-1
    while 下标>=0:
        节点=节点列表[下标]
        下标-=1
        if 节点['kind']!='assistant-step':
            continue
        数据=节点['data']
        if 数据['status']!='running':
            continue
        块列表=数据['blocks']
        块下=len(块列表)-1
        while 块下>=0:
            块=块列表[块下]
            块下-=1
            if 块['kind']!='reasoning':
                continue
            段落表=段落切开.split(块['text'])
            段下=len(段落表)-1
            while 段下>=0:
                段=段落表[段下].replace('**','')
                段下-=1
                详情=规范现场工具详情(段)
                if 详情!='':
                    return 详情
    return ''

def 现场工具详情(名称,参数原文):
    """从参数对象按键序抽出一行任务详情。"""
    try:
        参数=json.loads(参数原文)
    except (TypeError,ValueError,json.JSONDecodeError):
        return 规范现场工具详情(名称)
    if not isinstance(参数,dict):
        return 规范现场工具详情(名称)
    for 键 in 现场工具详情键:
        if 键 not in 参数:
            continue
        值=参数[键]
        详情=提问详情(值) if 键=='questions' else 规范现场工具详情(值)
        if 详情!='':
            return 详情
    return 规范现场工具详情(名称)

def 过程活动记录(节点列表):
    """按不同调用计数排名，并列按首次出现；并给出最近运行中工具类别与有界任务详情。"""
    计数表={}
    已见=set()
    运行中=None
    运行详情=''
    运行时刻=float('-inf')
    准备中=None
    def 访问(工具):
        """递归计入一次调用。"""
        nonlocal 运行中,运行详情,运行时刻,准备中
        调用标识=工具['callId']
        if 调用标识 in 已见:
            return
        已见.add(调用标识)
        调用=工具 if 是运行中工具(工具) else 工具['call']
        if 调用 is not None:
            种=活动种类(调用['name'])
            if 是运行中工具(工具) and 工具['time']>=运行时刻:
                运行中=种
                准备中=工具['phase']=='preparing'
                if 工具['phase']=='preparing':
                    运行详情=工具['name'] if 种=='tools' else ''
                else:
                    运行详情=现场工具详情(工具['name'],工具['argsRaw'])
                运行时刻=工具['time']
            计数表[种]=(计数表[种] if 种 in 计数表 else 0)+1
        for 子 in 工具['subCalls']:
            访问(子)
    for 节点 in 节点列表:
        if 节点['kind']=='tool-call':
            访问(节点['data']['root'])
    if 运行中 is None:
        运行详情=现场推理详情(节点列表)
    def 按计数(项):
        """排名键：调用次数。"""
        return 项['count']
    排名=[{'kind':种,'count':计数表[种]} for 种 in 计数表]
    排名.sort(key=按计数,reverse=True)
    结果={'counts':排名,'running':运行中,'runningDetail':运行详情}
    if 准备中 is True:
        结果['preparing']=True
    return 结果
