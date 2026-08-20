"""工具摘要行的纯行模型派生。

对齐上游 `ui-tool/src/client/tool/models/tool-call-model.ts`。公开面仅中文名。
变体分类、一行摘要、展开正文，以及从冻结调用切片展平的结果输出。
"""
import json#美化 JSON

__all__=[#仅中文公开名
    '变体标题','分类工具','结果文本','相对化到工作区','派生工具行','取字段',
    'VARIANT_TITLES','classifyTool','resultText','relativizeToCwd','toolRowModel',
]#公开面结束

变体标题={#变体 → 设计标题
    'search':'Search','read':'Read','bash':'Bash',
    'write':'Write','edit':'Edit','code':'Code','others':'Tool call',
}#结束
VARIANT_TITLES=变体标题#上游名

工具变体={#工具名 → 行变体
    'bash':'bash','pwsh':'bash','read':'read','web_fetch':'read',
    'web_search':'search','grep':'search','glob':'search',
    'write':'write','edit':'edit','run_code':'code',
    'cordis_package_inspect':'read','cordis_runtime_inspect':'read',
    'cordis_run':'others','cordis_stop':'others','cordis_undefine':'others',
}#结束

工具标题={#工具名 → 覆盖标题
    'cordis_package_inspect':'Inspect','cordis_runtime_inspect':'Inspect',
    'cordis_run':'Run Cordis Plugin','cordis_stop':'Stop Cordis Plugin',
    'cordis_undefine':'Remove Cordis Plugin','pwsh':'Pwsh',
}#结束

摘要键={#变体 → 摘要键序
    'bash':('description','command'),'read':('path','file_path','url'),
    'search':('query','pattern','url'),'write':('path','file_path'),
    'edit':('path','file_path'),'code':('description',),'others':(),
}#结束

文件路径键=('path','file_path')#仅路径键
文件路径变体=frozenset(['read','write','edit'])#读/写/改才抽 filePath

def 取字段(对象,键,缺省=None):#读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

def 分类工具(工具名):#工具名 → 行变体
    """匹配的变体；未知时为 others。"""
    return 工具变体.get(工具名,'others')#表中有则用

classifyTool=分类工具#上游名

def 结果文本(节点):#结果节点 → 展示文本
    """把已结算结果的内容块展平为展示文本。"""
    段们=[]#按块累积
    for 块 in 取字段(节点,'content') or []:#遍历结果内容块
        if 取字段(块,'type')=='text':#文本块
            段们.append(取字段(块,'text') or '')#原样
        else:#其余块形
            段们.append(json.dumps(块,ensure_ascii=False,indent=2))#美化 JSON
    if len(段们)==0 and 取字段(节点,'error') is not None:#失败且内容为空
        错误=取字段(节点,'error')#结构化错误
        段们.append(str(取字段(错误,'name'))+': '+str(取字段(错误,'code')))#name: code
    return '\n'.join(段们)#换行拼接

resultText=结果文本#上游名

def 相对化到工作区(文本,工作区):#工作区绝对路径 → 相对展示
    """缺席或空则路径不变；不以该根为前缀时原样返回。"""
    if 工作区 is None or 工作区=='':#无根
        return 文本#不改
    根=工作区.rstrip('/\\')#去掉尾部分隔符
    if 文本.startswith(根+'/') or 文本.startswith(根+'\\'):#根加分隔符前缀
        return 文本[len(根)+1:]#剥掉
    return 文本#原样

relativizeToCwd=相对化到工作区#上游名

def 解析参数(参数原文):#把参数原文解析成值
    """非 JSON 则 None。"""
    try:#尝试 JSON
        return json.loads(参数原文)#解析成功
    except Exception:#非 JSON
        return None#解析失败

def 首行(文本):#取文本第一行
    """无换行则全文。"""
    位置=文本.find('\n')#第一个换行
    return 文本 if 位置==-1 else 文本[:位置]#切

def 挑字符串(参数,键们):#按键序取第一个非空字符串
    """无一命中则 None。"""
    for 键 in 键们:#按偏好顺序
        值=参数.get(键) if isinstance(参数,dict) else None#该键
        if isinstance(值,str) and 值!='':#非空
            return 值#命中
    return None#无一

def 派生摘要(变体,参数原文):#从参数派生一行摘要
    """非对象则用原文首行。"""
    已解析=解析参数(参数原文)#尝试解析
    if not isinstance(已解析,dict) or 已解析 is None:#非对象
        return 首行(参数原文)#原文首行
    挑中=挑字符串(已解析,摘要键.get(变体,()))#按变体键序
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
    if not isinstance(已解析,dict) or 已解析 is None:#非对象
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
    if 变体=='code' and isinstance(已解析,dict):#代码行
        代码=已解析.get('code')#code 字段
        if isinstance(代码,str) and 代码!='':#非空程序
            return 代码#程序本身
    return json.dumps(已解析,ensure_ascii=False,indent=2)#美化参数

def 派生工具行(工具名或块,块=None,工作区=None):#冻结切片 → 行模型
    """ToolRow 所需的全部字段。可 (工具名,块) 或单参块（块内带 toolName/name）。"""
    if 块 is None and not isinstance(工具名或块,str):#单参块形
        块=工具名或块#块
        工具名=取字段(块,'toolName') or 取字段(块,'name') or ''#工具名
    else:#双参
        工具名=工具名或块 if isinstance(工具名或块,str) else ''#工具名
        if 块 is None:#缺块
            块={}#空
    变体=分类工具(工具名)#分类
    已结算=取字段(块,'kind') is not None or (isinstance(块,dict) and 'kind' in 块)#有 kind 即已结算
    if 已结算:#已结算走 call.argsRaw
        调用=取字段(块,'call')#调用头
        参数原文=取字段(调用,'argsRaw') if 调用 is not None else None#参数
        if 参数原文 is None:#回退块上
            参数原文=取字段(块,'argsRaw') or 取字段(块,'arguments') or ''#原文
    else:#进行中
        参数原文=取字段(块,'argsRaw') or 取字段(块,'arguments') or ''#原文
    if not isinstance(参数原文,str):#非串
        参数原文=json.dumps(参数原文,ensure_ascii=False) if 参数原文 is not None else ''#串化
    错误=取字段(块,'error')#错误
    错误码=取字段(错误,'code') if 错误 is not None else None#码
    if not 已结算:#尚未结算
        状态='running'#进行中
    elif 错误码=='interrupted':#打断
        状态='stopped'#已停止
    elif 取字段(块,'isError'):#失败
        状态='error'#错误
    else:#成功
        状态='ok'#成功
    if 参数原文=='':#无参数
        基底=取字段(块,'callId') or ''#callId
    else:#有参数
        基底=相对化到工作区(派生摘要(变体,参数原文),工作区)#相对化摘要
    工具自有标题=工具标题.get(工具名)#可能没有
    if 变体=='others' and 工具名!='' and 工具自有标题 is None:#others 且无自有标题
        摘要=工具名+' · '+str(基底)#真名骑在摘要槽
    else:#否则
        摘要=str(基底)#派生摘要
    输出=结果文本(块) if 已结算 else None#已结算才展平
    if 输出=='':#空串视为无文本
        输出=None#无
    错误摘要=首行(输出) if 状态=='error' and 输出 is not None else None#仅错误行
    return {#行模型
        'variant':变体,'title':工具自有标题 or 变体标题[变体],
        'summary':摘要,'filePath':派生文件路径(变体,参数原文),
        'body':派生正文(变体,参数原文),'output':输出,
        'errorSummary':错误摘要,'state':状态,
    }#模型

toolRowModel=派生工具行#上游名
