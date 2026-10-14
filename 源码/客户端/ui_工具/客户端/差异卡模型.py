import json

__all__=['聊天差异最大行数','收窄差异','差异卡模型']

聊天差异最大行数=9

def 收窄差异(差异列表):
    '非数组或空或畸形则 None'
    if not isinstance(差异列表,list) or len(差异列表)==0:
        return None
    输出=[]
    for 块 in 差异列表:
        if not isinstance(块,dict):
            return None
        if 'path' not in 块:
            return None
        路径=块['path']
        旧=块['oldText'] if 'oldText' in 块 else None
        if 'newText' not in 块:
            return None
        新=块['newText']
        if not isinstance(路径,str):
            return None
        if 旧 is not None and not isinstance(旧,str):
            return None
        if not isinstance(新,str):
            return None
        输出.append({'path':路径,'oldText':旧,'newText':新})
    return 输出

def 解析工具调用(块):
    '工具名与对象参数；调用头或合法 JSON 对象不可用时为 None'
    调用=块['call'] if 'kind' in 块 else 块
    if 调用 is None or not isinstance(调用,dict):
        return None
    原文=调用['argsRaw'] if 'argsRaw' in 调用 else None
    if not isinstance(原文,str):
        return None
    try:
        值=json.loads(原文)
    except (TypeError,ValueError,json.JSONDecodeError):
        return None
    if not isinstance(值,dict):
        return None
    名=调用['name'] if 'name' in 调用 else None
    if not isinstance(名,str):
        return None
    return {'name':名,'args':值}

def 升级字段合法(参数):
    '声明的升级字段是否构成合法对'
    权限=参数['sandbox_permissions'] if 'sandbox_permissions' in 参数 else None
    理由=参数['justification'] if 'justification' in 参数 else None
    if 权限 is None and 理由 is None:
        return True
    if 权限!='workspace-write' and 权限!='danger-full-access':
        return False
    return isinstance(理由,str) and 理由.strip()!=''

def 意图差异(块):
    'write、edit 与 str_replace_editor 的 create、replace'
    已解析=解析工具调用(块)
    if 已解析 is None:
        return None
    参数=已解析['args']
    if 已解析['name']=='str_replace_editor':
        命令=参数['command'] if 'command' in 参数 else None
        路径=参数['path'] if 'path' in 参数 else None
        if not isinstance(路径,str) or 路径.strip()=='':
            return None
        if 命令=='create':
            文件文本=参数['file_text'] if 'file_text' in 参数 else None
            if 文件文本 is not None and not isinstance(文件文本,str):
                return None
            return {'tool':'str_replace_editor','diff':{'path':路径,'oldText':None,'newText':'' if 文件文本 is None else 文件文本}}
        if 命令=='str_replace':
            旧=参数['old_str'] if 'old_str' in 参数 else None
            新=参数['new_str'] if 'new_str' in 参数 else None
            if 旧 is not None and not isinstance(旧,str):
                return None
            if 新 is not None and not isinstance(新,str):
                return None
            return {'tool':'str_replace_editor','diff':{'path':路径,'oldText':None if 旧 is None else 旧,'newText':'' if 新 is None else 新}}
        return None
    路径=参数['file_path'] if 'file_path' in 参数 else None
    if not isinstance(路径,str) or 路径.strip()=='':
        return None
    if not 升级字段合法(参数):
        return None
    if 已解析['name']=='write':
        内容=参数['content'] if 'content' in 参数 else None
        if not isinstance(内容,str):
            return None
        return {'tool':'write','diff':{'path':路径,'oldText':None,'newText':内容}}
    if 已解析['name']!='edit':
        return None
    旧=参数['old_string'] if 'old_string' in 参数 else None
    新=参数['new_string'] if 'new_string' in 参数 else None
    全替=参数['replace_all'] if 'replace_all' in 参数 else None
    if not isinstance(旧,str) or not isinstance(新,str):
        return None
    if 全替 is not None and not isinstance(全替,bool):
        return None
    return {'tool':'edit','diff':{'path':路径,'oldText':None if 旧=='' else 旧,'newText':新}}

def 已应用差异(元数据):
    '合法 hunk 列表、空数组标记 \'empty\'、或不可用 None'
    if not isinstance(元数据,dict):
        return None
    if 'diffs' not in 元数据:
        return None
    差异=元数据['diffs']
    if not isinstance(差异,list):
        return None
    if len(差异)==0:
        return 'empty'
    return 收窄差异(差异)

def 差异卡模型(块):
    '根 write、edit 与 str_replace_editor 的 create、replace；子调用走通用'
    if 'parentCallId' in 块 and 块['parentCallId'] is not None:
        return None
    意图=意图差异(块)
    if 意图 is None:
        return None
    if 'kind' not in 块:
        return {'card':{'diffs':[意图['diff']]}}
    if 意图['tool']=='str_replace_editor':
        return None
    if 'isError' in 块 and 块['isError']:
        return None
    已应用=已应用差异(块['meta'] if 'meta' in 块 else None)
    if 已应用 is None or 已应用=='empty':
        if 意图['tool']=='write':
            return {'card':{'diffs':[意图['diff']]}}
        return None
    return {'card':{'diffs':已应用}}
