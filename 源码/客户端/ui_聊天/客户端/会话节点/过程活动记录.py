from ..约定.聊天节点 import 是运行中工具

__all__=['过程活动']

细节上限=160
前缀上限=512
细节键=(
    'title','description','objective','task','task_name','name','question','questions','prompt','message',
    'command','cmd','queries','query','pattern','url','uri','file_path','path','target','action','status',
)


def 活动种类(名称):
    '工具名归到过程活动类别'
    if 名称=='read':
        return 'read'
    if 名称=='read_image':
        return 'readImage'
    if 名称=='grep' or 名称=='glob' or (isinstance(名称,str) and 名称.endswith('_inspect')):
        return 'search'
    if 名称=='write':
        return 'write'
    if 名称=='edit' or 名称=='apply_patch':
        return 'edit'
    if 名称 in ('bash','pwsh','exec_command','write_stdin') or (isinstance(名称,str) and 名称.startswith('terminal_')):
        return 'commands'
    if 名称=='run_code':
        return 'code'
    if 名称=='web_search':
        return 'webSearch'
    if 名称=='web_fetch':
        return 'webFetch'
    if 名称=='subagent' or (isinstance(名称,str) and 名称.startswith('subagent_')):
        return 'subagents'
    if 名称 in ('todo_write','create_goal','update_goal','get_goal'):
        return 'plan'
    if 名称=='ask_user_question' or 名称=='request_user_input':
        return 'questions'
    return 'tools'


def 规范化文本(文):
    '压空白。超过上限按字符截断并加省略号'
    规范=' '.join(文.split())
    if len(规范)<=细节上限:
        return 规范
    return 规范[:细节上限-1].rstrip()+'…'


def 规范化细节(值):
    '字符串或全字符串列表才做成一行细节'
    if isinstance(值,str):
        文=值
    elif isinstance(值,list) and all(isinstance(项,str) for 项 in 值):
        文=', '.join(值)
    else:
        文=''
    return 规范化文本(文)


def 问题细节(值):
    '提问列表里第一条有字的问题'
    if not isinstance(值,list):
        return ''
    for 项 in 值:
        if not isinstance(项,dict):
            continue
        细节=规范化细节(项.get('question'))
        if 细节!='':
            return 细节
    return ''


def 参数文本细节(参数,键):
    '按参数视图读这个键已经到达的文本'
    上限=前缀上限
    while True:
        前缀=参数.textPrefix(键,上限)
        if 前缀 is None:
            return None
        if len(前缀)>0:
            末=ord(前缀[-1])
            if 0xD800<=末<=0xDBFF:
                延伸=参数.textPrefix(键,上限+1)
                if isinstance(延伸,str) and len(延伸)>len(前缀):
                    下=ord(延伸[len(前缀)])
                    if 0xDC00<=下<=0xDFFF:
                        前缀=延伸
                        上限+=1
                elif isinstance(延伸,str) and len(延伸)==len(前缀) and not 参数.isSealed and not 参数.complete(键):
                    前缀=前缀[:-1]
        细节=规范化文本(前缀)
        超了=参数.stringExceeds(键,上限)
        if 细节.endswith('…') or not 超了:
            return 细节
        上限*=2


def 推理细节(节点表):
    '从后往前找正在跑的推理，取最后一段非空文字'
    下标=len(节点表)-1
    while 下标>=0:
        节点=节点表[下标]
        数据=节点.get('data') if isinstance(节点,dict) else None
        if isinstance(节点,dict) and 节点.get('kind')=='assistant-step' and isinstance(数据,dict) and 数据.get('status')=='running':
            块表=数据.get('blocks') if isinstance(数据.get('blocks'),list) else []
            块下标=len(块表)-1
            while 块下标>=0:
                块=块表[块下标]
                if isinstance(块,dict) and 块.get('kind')=='reasoning' and isinstance(块.get('text'),str):
                    段=块['text'].replace('\r\n','\n').split('\n')
                    段下标=len(段)-1
                    while 段下标>=0:
                        细节=规范化细节(段[段下标].replace('**','').strip())
                        if 细节!='':
                            return 细节
                        段下标-=1
                块下标-=1
        下标-=1
    return ''


def 工具细节(名称,参数):
    '第一个已经有字的细节键。没有且参数已关闭时用工具名'
    for 键 in 细节键:
        if not 参数.has(键):
            continue
        if 键=='questions':
            细节=问题细节(参数.value(键))
        else:
            文本=参数文本细节(参数,键)
            细节=文本 if 文本 is not None else 规范化细节(参数.value(键))
        if 细节!='':
            return 细节
    if 参数.closed():
        return 规范化细节(名称)
    return ''


def 过程活动(节点表):
    '按互不相同的调用次数给类别排序，并给出最新正在跑的任务细节'
    计数={}
    顺序=[]
    已见=set()
    正在=None
    正在细节=''
    正在时间=None
    准备中=None

    def 访问(工具):
        '深度优先看这次调用和它的子调用'
        nonlocal 正在,正在细节,正在时间,准备中
        if not isinstance(工具,dict) or 工具.get('callId') in 已见:
            return
        已见.add(工具.get('callId'))
        调用=工具 if 是运行中工具(工具) else 工具.get('call')
        if isinstance(调用,dict):
            种类=活动种类(调用.get('name'))
            if 是运行中工具(工具) and (正在时间 is None or 工具.get('time')>=正在时间):
                正在=种类
                准备中=工具.get('phase')=='preparing'
                正在细节=工具细节(工具.get('name'),工具.get('args'))
                正在时间=工具.get('time')
            计数[种类]=计数.get(种类,0)+1
            if 种类 not in 顺序:
                顺序.append(种类)
        子表=工具.get('subCalls') if isinstance(工具.get('subCalls'),list) else []
        for 子 in 子表:
            访问(子)

    for 节点 in 节点表:
        if isinstance(节点,dict) and 节点.get('kind')=='tool-call':
            数据=节点.get('data') if isinstance(节点.get('data'),dict) else {}
            访问(数据.get('root'))
    if 正在 is None:
        正在细节=推理细节(节点表)
    计数表=[{'kind':种类,'count':计数[种类]} for 种类 in 顺序]
    计数表.sort(key=按次数)
    结果={'counts':计数表,'running':正在,'runningDetail':正在细节}
    if 准备中:
        结果['preparing']=True
    return 结果


def 按次数(项):
    '次数多的排前面'
    return -项['count']
