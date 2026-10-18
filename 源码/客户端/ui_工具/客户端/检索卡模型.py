from .原始工具调用 import 解析工具调用

__all__=['聊天检索最大行数','检索卡模型']

聊天检索最大行数=8

def 合法包含(包含):
    '空、以 ! 开头，或花括号外的逗号都不合法'
    if 包含.strip()=='' or 包含.startswith('!'):
        return False
    深度=0
    for 字符 in 包含:
        if 字符=='{':
            深度=深度+1
        elif 字符=='}':
            深度=max(0,深度-1)
        elif 字符==',' and 深度==0:
            return False
    return True

def 合法检索调用(块):
    'grep 或 glob。pattern 为空则拒绝'
    已解析=解析工具调用(块)
    if 已解析 is None:
        return None
    参数=已解析['args']
    模式=参数.get('pattern')
    if not isinstance(模式,str):
        return None
    if 已解析['name']=='grep' and 模式=='':
        return None
    if 已解析['name']=='glob' and 模式.strip()=='':
        return None
    if 已解析['name']!='grep' and 已解析['name']!='glob':
        return None
    if 'path' in 参数:
        路径=参数.get('path')
        if not isinstance(路径,str) or 路径.strip()=='':
            return None
    if 已解析['name']=='grep' and 'include' in 参数:
        包含=参数.get('include')
        if not isinstance(包含,str) or not 合法包含(包含):
            return None
    return 已解析['name']

def 检索文件(值):
    '每个分组的 path 与 matches 都合法'
    if not isinstance(值,list):
        return None
    文件表=[]
    for 文件 in 值:
        if not isinstance(文件,dict):
            return None
        路径=文件.get('path')
        匹配表=文件.get('matches')
        if not isinstance(路径,str) or not isinstance(匹配表,list):
            return None
        收窄=[]
        for 匹配 in 匹配表:
            if not isinstance(匹配,dict):
                return None
            行号=匹配.get('lineNumber')
            行=匹配.get('line')
            if isinstance(行号,bool) or not isinstance(行号,int) or 行号<1 or not isinstance(行,str):
                return None
            收窄.append({'lineNumber':行号,'line':行})
        文件表.append({'path':路径,'matches':收窄})
    return 文件表

def 展平内容(内容):
    '空则 None'
    段=[]
    for 块 in 内容:
        if isinstance(块,dict) and 块.get('type')=='text' and isinstance(块.get('text'),str):
            段.append(块['text'])
    文本='\n'.join(段)
    if 文本=='':
        return None
    return 文本

def 检索卡模型(块):
    '非根 grep 或 glob，或元数据不合法，则 None'
    if 块.get('parentCallId') is not None or 'kind' not in 块 or 块.get('isError') is True:
        return None
    工具=合法检索调用(块)
    元数据=块.get('meta')
    if 工具 is None or not isinstance(元数据,dict):
        return None
    if not isinstance(元数据.get('truncated'),bool):
        return None
    总计=元数据.get('total')
    if isinstance(总计,bool) or not isinstance(总计,int) or 总计<0:
        return None
    公共={'truncated':元数据['truncated'],'total':总计}
    恢复=展平内容(块['content']) if 元数据['truncated'] else None
    if 工具=='grep':
        if 元数据.get('shape')!='matches':
            return None
        文件表=检索文件(元数据.get('files'))
        if 文件表 is None:
            return None
        return {'recovery':恢复,'card':{'kind':'matches','files':文件表,**公共}}
    if 元数据.get('shape')!='paths' or not isinstance(元数据.get('paths'),list):
        return None
    for 路径 in 元数据['paths']:
        if not isinstance(路径,str):
            return None
    return {'recovery':恢复,'card':{'kind':'paths','paths':list(元数据['paths']),**公共}}
