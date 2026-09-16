import json#解析参数 JSON

__all__=['聊天差异最大行数','收窄差异','差异卡模型']#仅中文公开名

聊天差异最大行数=9#聊天行折叠前的 diff 最大行数

def 收窄差异(差异列表):#收窄 diffs 为合法 hunk 或 None
    """非数组或空或畸形则 None。"""
    if not isinstance(差异列表,list) or len(差异列表)==0:#不可用
        return None#None
    输出=[]#已校验
    for 块 in 差异列表:#逐项
        if not isinstance(块,dict):#非对象
            return None#整份不可用
        if 'path' not in 块:#缺 path
            return None#不可用
        路径=块['path']#path
        旧=块['oldText'] if 'oldText' in 块 else None#oldText
        if 'newText' not in 块:#缺 newText
            return None#不可用
        新=块['newText']#newText
        if not isinstance(路径,str):#path 必须字符串
            return None#不可用
        if 旧 is not None and not isinstance(旧,str):#oldText 只能 null 或字符串
            return None#不可用
        if not isinstance(新,str):#newText 必须字符串
            return None#不可用
        输出.append({'path':路径,'oldText':旧,'newText':新})#收下
    return 输出#全部通过

def 解析工具调用(块):#解析与一块工具块配对的调用头
    """工具名与对象参数；调用头或合法 JSON 对象不可用时为 None。"""
    调用=块['call'] if 'kind' in 块 else 块#结算块取 call，在跑块即自身
    if 调用 is None or not isinstance(调用,dict):#无调用头
        return None#无
    原文=调用['argsRaw'] if 'argsRaw' in 调用 else None#参数原文
    if not isinstance(原文,str):#非串
        return None#无
    try:#解析 JSON
        值=json.loads(原文)#解析
    except (TypeError,ValueError,json.JSONDecodeError):#非法 JSON
        return None#无
    if not isinstance(值,dict):#非对象
        return None#无
    名=调用['name'] if 'name' in 调用 else None#工具名
    if not isinstance(名,str):#无名
        return None#无
    return {'name':名,'args':值}#解析结果

def 升级字段合法(参数):#校验可选升级对
    """声明的升级字段是否构成合法对。"""
    权限=参数['sandbox_permissions'] if 'sandbox_permissions' in 参数 else None#沙盒权限
    理由=参数['justification'] if 'justification' in 参数 else None#理由
    if 权限 is None and 理由 is None:#皆缺席
        return True#合法
    if 权限!='workspace-write' and 权限!='danger-full-access':#权限非法
        return False#否
    return isinstance(理由,str) and 理由.strip()!=''#理由非空串

def 意图差异(块):#从参数派生意图 diff
    """write/edit 与 str_replace_editor 的 create/replace。"""
    已解析=解析工具调用(块)#解析调用
    if 已解析 is None:#解析失败
        return None#无
    参数=已解析['args']#对象参数
    if 已解析['name']=='str_replace_editor':#字符串替换编辑器
        命令=参数['command'] if 'command' in 参数 else None#command
        路径=参数['path'] if 'path' in 参数 else None#path
        if not isinstance(路径,str) or 路径.strip()=='':#路径须非空
            return None#无
        if 命令=='create':#创建文件
            文件文本=参数['file_text'] if 'file_text' in 参数 else None#file_text
            if 文件文本 is not None and not isinstance(文件文本,str):#若有须串
                return None#无
            return {'tool':'str_replace_editor','diff':{'path':路径,'oldText':None,'newText':'' if 文件文本 is None else 文件文本}}#整文件
        if 命令=='str_replace':#替换
            旧=参数['old_str'] if 'old_str' in 参数 else None#old_str
            新=参数['new_str'] if 'new_str' in 参数 else None#new_str
            if 旧 is not None and not isinstance(旧,str):#若有须串
                return None#无
            if 新 is not None and not isinstance(新,str):#若有须串
                return None#无
            return {'tool':'str_replace_editor','diff':{'path':路径,'oldText':None if 旧 is None else 旧,'newText':'' if 新 is None else 新}}#替换 hunk
        return None#其他 command 不支持
    路径=参数['file_path'] if 'file_path' in 参数 else None#write/edit 路径
    if not isinstance(路径,str) or 路径.strip()=='':#路径须非空
        return None#无
    if not 升级字段合法(参数):#升级字段非法
        return None#无
    if 已解析['name']=='write':#写文件
        内容=参数['content'] if 'content' in 参数 else None#文件内容
        if not isinstance(内容,str):#内容非法
            return None#无
        return {'tool':'write','diff':{'path':路径,'oldText':None,'newText':内容}}#整文件写入
    if 已解析['name']!='edit':#非 edit
        return None#无
    旧=参数['old_string'] if 'old_string' in 参数 else None#old_string
    新=参数['new_string'] if 'new_string' in 参数 else None#new_string
    全替=参数['replace_all'] if 'replace_all' in 参数 else None#replace_all
    if not isinstance(旧,str) or not isinstance(新,str):#新旧须串
        return None#无
    if 全替 is not None and not isinstance(全替,bool):#若有须布尔
        return None#无
    return {'tool':'edit','diff':{'path':路径,'oldText':None if 旧=='' else 旧,'newText':新}}#编辑意图

def 已应用差异(元数据):#从结果 meta 取已应用 diffs
    """合法 hunk 列表、空数组标记 'empty'、或不可用 None。"""
    if not isinstance(元数据,dict):#meta 须对象
        return None#无
    if 'diffs' not in 元数据:#无 diffs
        return None#无
    差异=元数据['diffs']#diffs 字段
    if not isinstance(差异,list):#须数组
        return None#无
    if len(差异)==0:#空数组
        return 'empty'#单独标记
    return 收窄差异(差异)#收窄非空

def 差异卡模型(块):#从调用块推导 diff 卡片或走通用路径
    """根 write/edit 与 str_replace_editor 的 create/replace；子调用走通用。"""
    if 'parentCallId' in 块 and 块['parentCallId'] is not None:#子调用
        return None#通用
    意图=意图差异(块)#意图 diff
    if 意图 is None:#无法派生
        return None#通用
    if 'kind' not in 块:#进行中
        return {'card':{'diffs':[意图['diff']]}}#展示意图
    if 意图['tool']=='str_replace_editor':#结算后走 Generic
        return None#通用
    if 'isError' in 块 and 块['isError']:#错误
        return None#通用
    已应用=已应用差异(块['meta'] if 'meta' in 块 else None)#已应用 diffs
    if 已应用 is None or 已应用=='empty':#无有效已应用
        if 意图['tool']=='write':#write 回退意图
            return {'card':{'diffs':[意图['diff']]}}#整文件
        return None#其余走通用
    return {'card':{'diffs':已应用}}#展示已应用
