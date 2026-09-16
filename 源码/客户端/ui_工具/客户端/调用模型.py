import json#美化 JSON

__all__=['变体标题','分类工具','结果文本','相对化到工作区','派生工具行']#仅中文公开名

变体标题={#变体 → 设计标题
    'search':'Search','read':'Read','bash':'Bash',
    'write':'Write','edit':'Edit','code':'Code','others':'Tool call',
}#结束

工具变体={#工具名 → 行变体
    'bash':'bash','pwsh':'bash','read':'read','read_image':'read','web_fetch':'read',
    'web_search':'search','grep':'search','glob':'search',
    'write':'write','edit':'edit','run_code':'code',
    'cordis_package_inspect':'read','cordis_runtime_inspect':'read',
    'cordis_run':'others','cordis_stop':'others','cordis_undefine':'others',
}#结束

工具标题={#工具名 → 覆盖标题
    'cordis_package_inspect':'Inspect','cordis_runtime_inspect':'Inspect',
    'cordis_run':'Run Cordis Plugin','cordis_stop':'Stop Cordis Plugin',
    'cordis_undefine':'Remove Cordis Plugin','pwsh':'Pwsh',
    'read_image':'Read Image',
}#结束

摘要键={#变体 → 摘要键序
    'bash':('description','command'),'read':('path','file_path','url'),
    'search':('query','pattern','url'),'write':('path','file_path'),
    'edit':('path','file_path'),'code':('description',),'others':(),
}#结束

文件路径键=('path','file_path')#仅路径键
文件路径变体=frozenset(['read','write','edit'])#读/写/改才抽 filePath

def 分类工具(工具名):#工具名 → 行变体
    """匹配的变体；未知时为 others。"""
    return 工具变体[工具名] if 工具名 in 工具变体 else 'others'#表中有则用

def 结果文本(节点):#结果节点 → 展示文本
    """把已结算结果的内容块展平为展示文本。"""
    段列表=[]#按块累积
    内容=节点['content'] if 'content' in 节点 and 节点['content'] is not None else []#内容块
    for 块 in 内容:#遍历结果内容块
        if isinstance(块,dict) and 'type' in 块 and 块['type']=='text':#文本块
            段列表.append(块['text'] if 'text' in 块 and 块['text'] is not None else '')#原样
        else:#其余块形
            段列表.append(json.dumps(块,ensure_ascii=False,separators=(',',':'),allow_nan=False,indent=2))#美化 JSON
    if len(段列表)==0 and 'error' in 节点 and 节点['error'] is not None:#失败且内容为空
        错误=节点['error']#结构化错误
        错名=错误['name'] if isinstance(错误,dict) and 'name' in 错误 else None#名
        错码=错误['code'] if isinstance(错误,dict) and 'code' in 错误 else None#码
        段列表.append(str(错名)+': '+str(错码))#name: code
    return '\n'.join(段列表)#换行拼接

def 相对化到工作区(文本,工作区):#工作区绝对路径 → 相对展示
    """缺席或空则路径不变；不以该根为前缀时原样返回。"""
    if 工作区 is None or 工作区=='':#无根
        return 文本#不改
    根=工作区.rstrip('/\\')#去掉尾部分隔符
    if 文本.startswith(根+'/') or 文本.startswith(根+'\\'):#根加分隔符前缀
        return 文本[len(根)+1:]#剥掉
    return 文本#原样

def 缩写主目录(文本,主目录):#宿主主目录前缀 → ~
    """缺席或空则路径不变；整段等于主目录时为 ~。"""
    if 主目录 is None or 主目录=='':#无主目录
        return 文本#不改
    根=主目录.rstrip('/\\')#去掉尾部分隔符
    if 文本==根:#恰好主目录
        return '~'#波浪号
    if 文本.startswith(根+'/') or 文本.startswith(根+'\\'):#主目录加分隔符
        return '~/'+文本[len(根)+1:]#波浪号相对
    return 文本#原样

def 解析参数(参数原文):#把参数原文解析成值
    """非 JSON 则 None。"""
    try:#尝试 JSON
        return json.loads(参数原文)#解析成功
    except (TypeError,ValueError,json.JSONDecodeError):#非 JSON
        return None#解析失败

def 首行(文本):#取文本第一行
    """无换行则全文。"""
    位置=文本.find('\n')#第一个换行
    return 文本 if 位置==-1 else 文本[:位置]#切

def 挑字符串(参数,键列表):#按键序取第一个非空字符串
    """无一命中则 None。"""
    for 键 in 键列表:#按偏好顺序
        if 键 not in 参数:#无该键
            continue#下一
        值=参数[键]#该键
        if isinstance(值,str) and 值!='':#非空
            return 值#命中
    return None#无一

def 派生摘要(变体,参数原文):#从参数派生一行摘要
    """非对象则用原文首行。"""
    已解析=解析参数(参数原文)#尝试解析
    if not isinstance(已解析,dict):#非对象
        return 首行(参数原文)#原文首行
    if 变体=='search' and 'queries' in 已解析 and isinstance(已解析['queries'],list):#网页检索多查询
        查询列表=[首行(项) for 项 in 已解析['queries'] if isinstance(项,str) and 项!='']#非空串
        if len(查询列表)>0:#有查询
            return ', '.join(查询列表)#逗号拼接首行
    键列表=摘要键[变体] if 变体 in 摘要键 else ()#按变体键序
    挑中=挑字符串(已解析,键列表)#按变体键序
    if 挑中 is not None:#命中
        return 首行(挑中)#首行
    for 值 in 已解析.values():#扫所有参数值
        if isinstance(值,str) and 值!='':#非空字符串
            return 首行(值)#首行
    return 首行(参数原文)#仍无则原文

def 派生文件路径(变体,参数原文):#从参数抽出可打开路径
    """非文件工具变体则无路径。"""
    if 变体 not in 文件路径变体:#非文件
        return None#无
    已解析=解析参数(参数原文)#解析
    if not isinstance(已解析,dict):#非对象
        return None#无
    挑中=挑字符串(已解析,文件路径键)#只取 path/file_path
    return None if 挑中 is None else 首行(挑中)#首行

def 派生正文(变体,参数原文):#从参数派生展开正文
    """无参数则无输入段。"""
    if 参数原文=='':#无参数
        return None#无输入段
    已解析=解析参数(参数原文)#解析
    if 已解析 is None:#非 JSON
        return 参数原文#原文
    if 变体=='code' and isinstance(已解析,dict) and 'code' in 已解析:#代码行
        代码=已解析['code']#code 字段
        if isinstance(代码,str) and 代码!='':#非空程序
            return 代码#程序本身
    return json.dumps(已解析,ensure_ascii=False,separators=(',',':'),allow_nan=False,indent=2)#美化参数

def 派生工具行(工具名或块,块=None,工作区=None,主目录=None):#冻结切片 → 行模型
    """ToolRow 所需的全部字段。可 (工具名,块) 或单参块（块内带 toolName/name）。"""
    if 块 is None and not isinstance(工具名或块,str):#单参块形
        块=工具名或块#块
        if 'toolName' in 块 and 块['toolName']:#toolName
            工具名=块['toolName']#名
        elif 'name' in 块 and 块['name']:#name
            工具名=块['name']#名
        else:#空
            工具名=''#空
    else:#双参
        工具名=工具名或块 if isinstance(工具名或块,str) else ''#工具名
        if 块 is None:#缺块
            块={}#空
    变体=分类工具(工具名)#分类
    已结算='kind' in 块#有 kind 即已结算
    if 已结算:#已结算走 call.argsRaw
        调用=块['call'] if 'call' in 块 else None#调用头
        参数原文=调用['argsRaw'] if 调用 is not None and 'argsRaw' in 调用 else None#参数
        if 参数原文 is None:#回退块上
            if 'argsRaw' in 块 and 块['argsRaw'] is not None:#argsRaw
                参数原文=块['argsRaw']#原文
            elif 'arguments' in 块 and 块['arguments'] is not None:#arguments
                参数原文=块['arguments']#原文
            else:#空
                参数原文=''#空
    else:#进行中
        if 'argsRaw' in 块 and 块['argsRaw'] is not None:#argsRaw
            参数原文=块['argsRaw']#原文
        elif 'arguments' in 块 and 块['arguments'] is not None:#arguments
            参数原文=块['arguments']#原文
        else:#空
            参数原文=''#空
    if not isinstance(参数原文,str):#非串
        参数原文=json.dumps(参数原文,ensure_ascii=False,separators=(',',':'),allow_nan=False) if 参数原文 is not None else ''#串化
    错误=块['error'] if 'error' in 块 else None#错误
    错误码=错误['code'] if 错误 is not None and 'code' in 错误 else None#码
    if not 已结算:#尚未结算
        状态='running'#进行中
    elif 错误码=='interrupted':#打断
        状态='stopped'#已停止
    elif 'isError' in 块 and 块['isError']:#失败
        状态='error'#错误
    else:#成功
        状态='ok'#成功
    if 参数原文=='':#无参数
        基底=块['callId'] if 'callId' in 块 and 块['callId'] is not None else ''#callId
    else:#有参数
        基底=缩写主目录(相对化到工作区(派生摘要(变体,参数原文),工作区),主目录)#相对化后再缩写主目录
    工具自有标题=工具标题[工具名] if 工具名 in 工具标题 else None#可能没有
    if 变体=='others' and 工具名!='' and 工具自有标题 is None:#others 且无自有标题
        摘要=工具名+' · '+str(基底)#真名骑在摘要槽
    else:#否则
        摘要=str(基底)#派生摘要
    输出=结果文本(块) if 已结算 else None#已结算才展平
    if 输出=='':#空串视为无文本
        输出=None#无
    错误摘要=首行(输出) if 状态=='error' and 输出 is not None else None#仅错误行
    自动拒绝=None#普通结果无拒绝
    if 已结算 and 'isError' in 块 and 块['isError'] and 错误 is not None:#已结算失败
        错名=错误['name'] if 'name' in 错误 else None#错误名
        if 错名=='AutoReviewDeniedError' and 错误码=='AUTO_REVIEW_DENIED':#自动审查拒绝
            原因=错误['reason'] if 'reason' in 错误 else None#原始原因
            自动拒绝={'reason':原因 if isinstance(原因,str) else None}#非串当无原因
    return {#行模型
        'variant':变体,'title':工具自有标题 if 工具自有标题 is not None else 变体标题[变体],
        'summary':摘要,'filePath':派生文件路径(变体,参数原文),
        'body':派生正文(变体,参数原文),'output':输出,
        'errorSummary':错误摘要,'autoReviewDenial':自动拒绝,'state':状态,
    }#模型
