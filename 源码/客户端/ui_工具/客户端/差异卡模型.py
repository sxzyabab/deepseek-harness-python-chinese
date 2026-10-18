from .原始工具调用 import 解析工具调用
from .已记录路径 import 已记录绝对路径

__all__=['聊天差异最大行数','差异卡模型']

聊天差异最大行数=9

def 收窄差异(差异列表):
    '非数组、空或畸形则 None'
    if not isinstance(差异列表,list) or len(差异列表)==0:
        return None
    结果=[]
    for 块 in 差异列表:
        if not isinstance(块,dict):
            return None
        路径=块.get('path')
        旧文=块.get('oldText',None)
        新文=块.get('newText',None)
        if not isinstance(路径,str):
            return None
        if 旧文 is not None and not isinstance(旧文,str):
            return None
        if not isinstance(新文,str):
            return None
        结果.append({'path':路径,'oldText':旧文,'newText':新文})
    return 结果

def 意图差异(块):
    'write、edit，以及 str_replace_editor 的 create 与 str_replace'
    已解析=解析工具调用(块)
    if 已解析 is None:
        return None
    参数=已解析['args']
    if 已解析['name']=='str_replace_editor':
        命令=参数.get('command')
        路径=参数.get('path')
        if not isinstance(路径,str) or 路径.strip()=='':
            return None
        if 命令=='create':
            文件文本=参数.get('file_text',None)
            if 'file_text' in 参数 and not isinstance(文件文本,str):
                return None
            新文=文件文本 if isinstance(文件文本,str) else ''
            return {'tool':'str_replace_editor','diff':{'path':路径,'oldText':None,'newText':新文}}
        if 命令=='str_replace':
            旧文=参数.get('old_str',None)
            新文=参数.get('new_str',None)
            if 'old_str' in 参数 and not isinstance(旧文,str):
                return None
            if 'new_str' in 参数 and not isinstance(新文,str):
                return None
            return {
                'tool':'str_replace_editor',
                'diff':{
                    'path':路径,
                    'oldText':旧文 if isinstance(旧文,str) else None,
                    'newText':新文 if isinstance(新文,str) else '',
                },
            }
        return None
    路径=参数.get('file_path')
    if not isinstance(路径,str) or 路径.strip()=='':
        return None
    if 已解析['name']=='write':
        内容=参数.get('content')
        if not isinstance(内容,str):
            return None
        return {'tool':'write','diff':{'path':路径,'oldText':None,'newText':内容}}
    if 已解析['name']!='edit':
        return None
    旧文=参数.get('old_string')
    新文=参数.get('new_string')
    if not isinstance(旧文,str) or not isinstance(新文,str):
        return None
    if 'replace_all' in 参数 and not isinstance(参数.get('replace_all'),bool):
        return None
    return {'tool':'edit','diff':{'path':路径,'oldText':旧文 if 旧文!='' else None,'newText':新文}}

def 已应用差异(元数据):
    '合法 hunk、空数组标记 empty，或不可用 None'
    if not isinstance(元数据,dict):
        return None
    差异=元数据.get('diffs')
    if not isinstance(差异,list):
        return None
    if len(差异)==0:
        return 'empty'
    return 收窄差异(差异)

def 差异卡模型(块):
    '根 write、edit 与 str_replace_editor 的 create、replace。子调用走通用'
    if 块.get('parentCallId') is not None:
        return None
    意图=意图差异(块)
    if 意图 is None:
        return None
    if 'kind' not in 块:
        return {'card':{'diffs':[意图['diff']]}}
    if 意图['tool']=='str_replace_editor':
        return None
    if 块.get('isError') is True:
        return None
    已应用=已应用差异(块.get('meta'))
    if 已应用 is None or 已应用=='empty':
        if 意图['tool']=='write':
            return {'card':{'diffs':[意图['diff']]}}
        return None
    路径=已记录绝对路径(块.get('meta'),'path')
    差异列表=[]
    for 差异 in 已应用:
        if 差异['path']==路径:
            改过=dict(差异)
            改过['path']=意图['diff']['path']
            差异列表.append(改过)
        else:
            差异列表.append(差异)
    return {'card':{'diffs':差异列表}}
