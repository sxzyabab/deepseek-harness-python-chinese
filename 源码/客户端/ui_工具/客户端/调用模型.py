import json
import os
from ....基础设施.通用工具 import 紧凑json编码

__all__=['变体标题','分类工具','结果文本','相对化到工作区','派生工具行']

变体标题={
    'search':'Search','read':'Read','bash':'Bash',
    'write':'Write','edit':'Edit','code':'Code','others':'Tool call',
}

工具变体={
    'bash':'bash','pwsh':'bash','read':'read','read_image':'read','web_fetch':'read',
    'web_search':'search','grep':'search','glob':'search',
    'write':'write','edit':'edit','run_code':'code',
    'cordis_package_inspect':'read','cordis_runtime_inspect':'read',
    'cordis_run':'others','cordis_stop':'others','cordis_undefine':'others',
}

工具标题={
    'cordis_package_inspect':'Inspect','cordis_runtime_inspect':'Inspect',
    'cordis_run':'Run Cordis Plugin','cordis_stop':'Stop Cordis Plugin',
    'cordis_undefine':'Remove Cordis Plugin','pwsh':'Pwsh',
    'read_image':'Read Image',
}

摘要键={
    'bash':('description','command'),'read':('path','file_path','url'),
    'search':('query','pattern','url'),'write':('path','file_path'),
    'edit':('path','file_path'),'code':('description',),'others':(),
}

文件路径键=('path','file_path')
文件路径变体=frozenset(['read','write','edit'])

def 分类工具(工具名):
    '匹配的变体；未知时为 others'
    return 工具变体[工具名] if 工具名 in 工具变体 else 'others'

def 结果文本(节点):
    '把已结算结果的内容块展平为展示文本'
    段列表=[]
    内容=节点['content'] if 'content' in 节点 and 节点['content'] is not None else []
    for 块 in 内容:
        if isinstance(块,dict) and 'type' in 块 and 块['type']=='text':
            段列表.append(块['text'] if 'text' in 块 and 块['text'] is not None else '')
        else:
            段列表.append(json.dumps(块,ensure_ascii=False,separators=(',',':'),allow_nan=False,indent=2))
    if len(段列表)==0 and 'error' in 节点 and 节点['error'] is not None:
        错误=节点['error']
        错名=错误['name'] if isinstance(错误,dict) and 'name' in 错误 else None
        错码=错误['code'] if isinstance(错误,dict) and 'code' in 错误 else None
        段列表.append(str(错名)+': '+str(错码))
    return '\n'.join(段列表)

def 相对化到工作区(文本,工作区):
    '缺席或空则路径不变；不以该根为前缀时原样返回'
    if 工作区 is None or 工作区=='':
        return 文本
    根=工作区.rstrip('/\\')
    if 文本.startswith(根+'/') or 文本.startswith(根+'\\'):
        return 文本[len(根)+1:]
    return 文本

def 缩写主目录(文本,主目录):
    '缺席或空则路径不变；整段等于主目录时为 ~'
    if 主目录 is None or 主目录=='':
        return 文本
    根=主目录.rstrip('/\\')
    if 文本==根:
        return '~'
    if 文本.startswith(根+'/') or 文本.startswith(根+'\\'):
        return '~/'+文本[len(根)+1:]
    return 文本

def 解析参数(参数原文):
    '非 JSON 则 None'
    try:
        return json.loads(参数原文)
    except (TypeError,ValueError,json.JSONDecodeError):
        return None

def 首行(文本):
    '无换行则全文'
    位置=文本.find('\n')
    return 文本 if 位置==-1 else 文本[:位置]

def 去掉绝对路径(文本):
    '失败文案按空白切开后丢掉绝对路径、用户名和环境变量，其余原样留下'
    if not isinstance(文本,str):
        return 文本
    屏蔽名=set(os.environ)
    屏蔽值=set()
    for 键 in ('USERNAME','USER','LOGNAME','USERPROFILE','HOME'):
        值=os.environ.get(键)
        if isinstance(值,str) and 值!='':
            屏蔽值.add(值)
            基=os.path.basename(值.rstrip('\\/'))
            if 基!='':
                屏蔽值.add(基)
    for 值 in os.environ.values():
        if isinstance(值,str) and (len(值)>=8 or '\\' in 值 or '/' in 值):
            屏蔽值.add(值)
    留下=[]
    for 词 in 文本.split():
        去引=词.strip('\'"()[]{}<>')
        统一=去引.replace('\\','/')
        if 统一.startswith('/') or 统一.startswith('~') or (len(统一)>2 and 统一[0].isalpha() and 统一[1]==':' and 统一[2]=='/'):
            continue
        if 去引.startswith('$') and len(去引)>1:
            continue
        if len(去引)>2 and 去引.startswith('%') and 去引.endswith('%'):
            continue
        if '=' in 去引 and 去引.split('=',1)[0] in 屏蔽名:
            continue
        if 去引 in 屏蔽名 or 去引 in 屏蔽值 or 统一 in 屏蔽值:
            continue
        含敏感=False
        for 项 in 屏蔽值:
            if len(项)>=3 and 项 in 去引:
                含敏感=True
                break
        if 含敏感:
            continue
        留下.append(词)
    return ' '.join(留下).strip()

def 挑字符串(参数,键列表):
    '无一命中则 None'
    for 键 in 键列表:
        if 键 not in 参数:
            continue
        值=参数[键]
        if isinstance(值,str) and 值!='':
            return 值
    return None

def 派生摘要(变体,参数原文):
    '非对象则用原文首行'
    已解析=解析参数(参数原文)
    if not isinstance(已解析,dict):
        return 首行(参数原文)
    if 变体=='search' and 'queries' in 已解析 and isinstance(已解析['queries'],list):
        查询列表=[首行(项) for 项 in 已解析['queries'] if isinstance(项,str) and 项!='']
        if len(查询列表)>0:
            return ', '.join(查询列表)
    键列表=摘要键[变体] if 变体 in 摘要键 else ()
    挑中=挑字符串(已解析,键列表)
    if 挑中 is not None:
        return 首行(挑中)
    for 值 in 已解析.values():
        if isinstance(值,str) and 值!='':
            return 首行(值)
    return 首行(参数原文)

def 派生文件路径(变体,参数原文):
    '非文件工具变体则无路径'
    if 变体 not in 文件路径变体:
        return None
    已解析=解析参数(参数原文)
    if not isinstance(已解析,dict):
        return None
    挑中=挑字符串(已解析,文件路径键)
    return None if 挑中 is None else 首行(挑中)

def 派生正文(变体,参数原文):
    '无参数则无输入段'
    if 参数原文=='':
        return None
    已解析=解析参数(参数原文)
    if 已解析 is None:
        return 参数原文
    if 变体=='code' and isinstance(已解析,dict) and 'code' in 已解析:
        代码=已解析['code']
        if isinstance(代码,str) and 代码!='':
            return 代码
    return json.dumps(已解析,ensure_ascii=False,separators=(',',':'),allow_nan=False,indent=2)

def 派生工具行(工具名或块,块=None,工作区=None,主目录=None):
    '行模型所需字段。可 (工具名,块) 或单参块（块内带 toolName 或 name）'
    if 块 is None and not isinstance(工具名或块,str):
        块=工具名或块
        if 'toolName' in 块 and 块['toolName']:
            工具名=块['toolName']
        elif 'name' in 块 and 块['name']:
            工具名=块['name']
        else:
            工具名=''
    else:
        工具名=工具名或块 if isinstance(工具名或块,str) else ''
        if 块 is None:
            块={}
    变体=分类工具(工具名)
    已结算='kind' in 块
    if 已结算:
        调用=块['call'] if 'call' in 块 else None
        参数原文=调用['argsRaw'] if 调用 is not None and 'argsRaw' in 调用 else None
        if 参数原文 is None:
            if 'argsRaw' in 块 and 块['argsRaw'] is not None:
                参数原文=块['argsRaw']
            elif 'arguments' in 块 and 块['arguments'] is not None:
                参数原文=块['arguments']
            else:
                参数原文=''
    else:
        if 'argsRaw' in 块 and 块['argsRaw'] is not None:
            参数原文=块['argsRaw']
        elif 'arguments' in 块 and 块['arguments'] is not None:
            参数原文=块['arguments']
        else:
            参数原文=''
    if not isinstance(参数原文,str):
        参数原文=紧凑json编码(参数原文) if 参数原文 is not None else ''
    错误=块['error'] if 'error' in 块 else None
    错误码=错误['code'] if 错误 is not None and 'code' in 错误 else None
    if not 已结算:
        状态='running'
    elif 错误码=='interrupted':
        状态='stopped'
    elif 'isError' in 块 and 块['isError']:
        状态='error'
    else:
        状态='ok'
    if 参数原文=='':
        基底=块['callId'] if 'callId' in 块 and 块['callId'] is not None else ''
    else:
        基底=缩写主目录(相对化到工作区(派生摘要(变体,参数原文),工作区),主目录)
    工具自有标题=工具标题[工具名] if 工具名 in 工具标题 else None
    if 变体=='others' and 工具名!='' and 工具自有标题 is None:
        摘要=工具名+' · '+str(基底)
    else:
        摘要=str(基底)
    输出=结果文本(块) if 已结算 else None
    if 输出=='':
        输出=None
    错误摘要=首行(输出) if 状态=='error' and 输出 is not None else None
    if isinstance(错误摘要,str):
        错误摘要=去掉绝对路径(错误摘要)
        if 错误摘要=='':
            错误摘要=None
    自动拒绝=None
    if 已结算 and 'isError' in 块 and 块['isError'] and 错误 is not None:
        错名=错误['name'] if 'name' in 错误 else None
        if 错名=='AutoReviewDeniedError' and 错误码=='AUTO_REVIEW_DENIED':
            原因=错误['reason'] if 'reason' in 错误 else None
            自动拒绝={'reason':原因 if isinstance(原因,str) else None}
    return {
        'variant':变体,'title':工具自有标题 if 工具自有标题 is not None else 变体标题[变体],
        'summary':摘要,'filePath':派生文件路径(变体,参数原文),
        'body':派生正文(变体,参数原文),'output':输出,
        'errorSummary':错误摘要,'autoReviewDenial':自动拒绝,'state':状态,
    }
