import re
from ....工具.工作区路径 import 相对化到工作目录,缩写家目录路径
from .原始工具调用 import 解析工具调用,单结果文本

__all__=['聊天读最大行数','读调用行','读卡模型']

聊天读最大行数=8
读信封=re.compile(r'^<path>[^\n]*</path>\n<type>file</type>\n<content>\n([\s\S]*)\n</content>$')

def 正整数(值):
    '至少为 1 的整数'
    return isinstance(值,int) and not isinstance(值,bool) and 值>=1

def 合法读调用(块):
    'read，且 path 非空，offset 与 limit 若有则是正整数'
    已解析=解析工具调用(块)
    if 已解析 is None or 已解析['name']!='read':
        return False
    参数=已解析['args']
    路径=参数.get('file_path')
    if not isinstance(路径,str) or 路径.strip()=='':
        return False
    if 'offset' in 参数 and not 正整数(参数.get('offset')):
        return False
    if 'limit' in 参数 and not 正整数(参数.get('limit')):
        return False
    return True

def 读元数据(元数据):
    '行号递增且不超过总行数'
    if not isinstance(元数据,dict):
        return None
    路径=元数据.get('path')
    偏移=元数据.get('offset')
    行列表=元数据.get('lines')
    总行=元数据.get('totalLines')
    语言=元数据.get('lang',None)
    if not isinstance(路径,str) or isinstance(偏移,bool) or not isinstance(偏移,int) or 偏移<1:
        return None
    if isinstance(总行,bool) or not isinstance(总行,int) or 总行<0 or not isinstance(行列表,list):
        return None
    if 'lang' in 元数据 and not isinstance(语言,str):
        return None
    收窄=[]
    上一=偏移-1
    for 行 in 行列表:
        if not isinstance(行,dict):
            return None
        号=行.get('number')
        文=行.get('text')
        if isinstance(号,bool) or not isinstance(号,int) or 号<1 or 号<=上一:
            return None
        if 号>总行 or not isinstance(文,str):
            return None
        上一=号
        收窄.append({'number':号,'text':文})
    结果={'path':路径,'offset':偏移,'lines':收窄,'totalLines':总行}
    if isinstance(语言,str):
        结果['lang']=语言
    return 结果

def 读调用行(块):
    '参数里至少为 1 的 offset。没有则为 None'
    if not 合法读调用(块):
        return None
    已解析=解析工具调用(块)
    偏移=已解析['args'].get('offset') if 已解析 is not None else None
    if 正整数(偏移):
        return 偏移
    return None

def 读卡模型(块,会话工作区=None,主目录=None):
    '进行中或非读卡返回 None'
    if 块.get('parentCallId') is not None or 'kind' not in 块 or 块.get('isError') is True:
        return None
    if not 合法读调用(块):
        return None
    元数据=读元数据(块.get('meta'))
    if 元数据 is None:
        return None
    文本=单结果文本(块)
    if 文本 is None:
        return None
    匹配=读信封.search(文本)
    if 匹配 is None:
        return None
    结果={
        'label':缩写家目录路径(相对化到工作目录(元数据['path'],会话工作区),主目录),
        'lines':元数据['lines'],
        'totalLines':元数据['totalLines'],
    }
    if 'lang' in 元数据:
        结果['lang']=元数据['lang']
    return 结果
