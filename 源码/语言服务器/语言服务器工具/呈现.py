"""`lsp` 工具的纯格式化与会话 cwd 辅助。"""
from ..语言服务器.类型 import 语言服务器操作#操作联合
from ..语言服务器 import 语言服务器错误#本缝异常基类

默认最大位置数=100#默认位置条数上限
默认最大结果字符数=16000#默认完整结果字节上限（配置键名沿用线协议 maxResultChars）

__all__=[#仅中文公开名
    '语言服务器操作列表','默认最大位置数','默认最大结果字符数',
    '解析语言服务器参数','格式化位置列表','格式化悬停','呈现语言服务器调用','会话工作目录',
]#公开面结束

语言服务器操作列表=list(语言服务器操作)#运行时操作表

def 一基坐标(值,名称):
    """模型坐标从 1 开始。排除布尔。"""
    if isinstance(值,bool) or isinstance(值,int) is False or 值<1:#非法
        raise 语言服务器错误(名称+' must be a positive integer (one-based)','LSP_INVALID_ARGUMENT')#拒绝
    return 值#合法

def 解析语言服务器参数(参数):
    """operation 必须是四种之一；line/character 为正整数。参数是工具入参 dict。"""
    if 'operation' not in 参数:#缺操作
        raise 语言服务器错误('operation must be one of '+', '.join(语言服务器操作列表),'LSP_INVALID_ARGUMENT')#拒绝
    操作=参数['operation']#操作名
    if 操作 not in 语言服务器操作:#未知操作
        raise 语言服务器错误('operation must be one of '+', '.join(语言服务器操作列表),'LSP_INVALID_ARGUMENT')#拒绝
    if 'file_path' not in 参数:#缺路径
        raise 语言服务器错误('file_path must be a non-empty string','LSP_INVALID_ARGUMENT')#拒绝
    路径=str(参数['file_path']).strip()#文件路径
    if 路径=='':#空路径
        raise 语言服务器错误('file_path must be a non-empty string','LSP_INVALID_ARGUMENT')#拒绝
    行=一基坐标(参数['line'] if 'line' in 参数 else None,'line')#一基行
    列=一基坐标(参数['character'] if 'character' in 参数 else None,'character')#一基列
    return {'operation':操作,'filePath':路径,'position':{'line':行-1,'character':列-1}}#零基

def 限制结果(文本,最大字节,种类):
    """超长时按 UTF-8 字节截断，切点落在字符边界。"""
    标记='… ['+种类+' result truncated at '+str(最大字节)+' characters]'#截断标记
    数据=文本.encode('utf-8')#UTF-8 字节
    if len(数据)<=最大字节:#未超
        return 文本#原样
    标记字节=标记.encode('utf-8')#标记字节
    预算=max(0,最大字节-len(标记字节))#正文预算
    截=数据[:预算]#按字节切
    while len(截)>0:#回退到字符边界
        try:#完整字符
            return 截.decode('utf-8')+标记#截断
        except UnicodeDecodeError:#半个字符
            截=截[:-1]#退一字节
    return 标记#只剩标记

def 渲染uri(uri,工作区uri):
    """工作区内尽量相对化，否则保留绝对路径。"""
    if str(uri).startswith('file:') is False:#非 file
        return str(uri)#原样
    路径=str(uri)[5:]#去掉 file:
    if 路径.startswith('///'):#Windows file URI
        路径=路径[2:]#去多余斜杠
    return 路径.replace('\\','/')#统一斜杠

def 格式化位置列表(位置列表,工作区uri,最大位置数,最大结果字符数):
    """按文件分组并转回一基 path:line:character。位置是 dict。"""
    if len(位置列表)==0:#无结果
        return 限制结果('No results.',最大结果字符数,'locations')#空结果
    展示=位置列表[:最大位置数]#截断
    省略=len(位置列表)-len(展示)#省略数
    行列表=[]#输出行
    for 位置 in 展示:#逐条
        路径=渲染uri(位置['uri'],工作区uri)#渲染路径
        范围=位置['range']#范围
        起点=范围['start']#起点
        行列表.append(路径+':'+str(起点['line']+1)+':'+str(起点['character']+1))#一基坐标
    if 省略>0:#有省略
        行列表.append('… '+str(省略)+' more location'+('' if 省略==1 else 's')+' omitted (limit '+str(最大位置数)+').')#省略标记
    return 限制结果('\n'.join(行列表),最大结果字符数,'locations')#合并

def 格式化悬停(悬停,最大结果字符数):
    """null 悬停给出固定文案。悬停是 dict。"""
    文本='No hover information.' if 悬停 is None else str(悬停['contents'])#正文
    return 限制结果(文本,最大结果字符数,'hover')#限长

def 呈现语言服务器调用(参数):
    """只依赖参数，不触 I/O。参数是工具入参 dict。"""
    输入=解析语言服务器参数(参数)#已校验
    位置=输入['position']#零基位置
    return 输入['operation']+' '+输入['filePath']+':'+str(位置['line']+1)+':'+str(位置['character']+1)#摘要

def 会话工作目录(执行上下文):
    """非智能体调用方返回 None。执行上下文是跨包 dict。"""
    if 'agent' not in 执行上下文:#无智能体
        return None#无 cwd
    智能体=执行上下文['agent']#调用智能体
    if 智能体 is None:#无智能体
        return None#无 cwd
    if 'session' not in 智能体:#无会话
        return None#无 cwd
    会话=智能体['session']#会话
    if 会话 is None:#无会话
        return None#无 cwd
    if 'header' not in 会话:#无头
        return None#无 cwd
    头=会话['header']#会话头
    if 头 is None or 'cwd' not in 头:#无头或无 cwd
        return None#无 cwd
    return 头['cwd']#工作目录
