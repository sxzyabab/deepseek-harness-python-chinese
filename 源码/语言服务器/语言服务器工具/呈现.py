"""`lsp` 工具的纯格式化与会话 cwd 辅助。

对齐上游 `tool-lsp/src/render.ts` 与 `session-cwd.ts`。
"""
from ..语言服务器.类型 import 语言服务器操作#操作联合

默认最大位置数=100#默认位置条数上限
默认最大结果字符数=16000#默认完整结果字符上限

__all__=[#仅中文公开名
    '语言服务器操作列表','默认最大位置数','默认最大结果字符数',
    '解析语言服务器参数','格式化位置列表','格式化悬停','呈现语言服务器调用','会话工作目录',
]#公开面结束

语言服务器操作列表=list(语言服务器操作)#运行时操作表

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 一基坐标(值,名称):#校验正整数一基坐标
    """模型坐标从 1 开始。"""
    if not isinstance(值,int) or 值<1:#非法
        raise Exception(名称+' must be a positive integer (one-based)')#拒绝
    return 值#合法

def 解析语言服务器参数(参数):#校验并转成零基位置
    """operation 必须是四种之一；line/character 为正整数。"""
    操作=取字段(参数,'operation')#操作名
    if 操作 not in 语言服务器操作:#未知操作
        raise Exception('operation must be one of '+', '.join(语言服务器操作列表))#拒绝
    路径=str(取字段(参数,'file_path')).strip()#文件路径
    if 路径=='':#空路径
        raise Exception('file_path must be a non-empty string')#拒绝
    行=一基坐标(取字段(参数,'line'),'line')#一基行
    列=一基坐标(取字段(参数,'character'),'character')#一基列
    return {'operation':操作,'filePath':路径,'position':{'line':行-1,'character':列-1}}#零基

def 限制结果(文本,最大字符,种类):#应用完整结果字符上限
    """超长时追加截断标记。"""
    if len(文本)<=最大字符:#未超
        return 文本#原样
    标记='… ['+种类+' result truncated at '+str(最大字符)+' characters]'#截断标记
    预算=max(0,最大字符-len(标记))#正文预算
    return 文本[:预算]+标记#截断

def 渲染uri(uri,工作区uri):#把 file: URI 渲染成路径
    """工作区内尽量相对化，否则保留绝对路径。"""
    if not str(uri).startswith('file:'):#非 file
        return str(uri)#原样
    路径=str(uri)[5:]#去掉 file:
    if 路径.startswith('///'):#Windows file URI
        路径=路径[2:]#去多余斜杠
    return 路径.replace('\\','/')#统一斜杠

def 格式化位置列表(位置们,工作区uri,最大位置数,最大结果字符数):#渲染位置结果
    """按文件分组并转回一基 path:line:character。"""
    if len(位置们)==0:#无结果
        return 限制结果('No results.',最大结果字符数,'locations')#空结果
    展示=位置们[:最大位置数]#截断
    省略=len(位置们)-len(展示)#省略数
    行们=[]#输出行
    for 位置 in 展示:#逐条
        路径=渲染uri(取字段(位置,'uri'),工作区uri)#渲染路径
        范围=取字段(位置,'range')#范围
        起点=取字段(范围,'start')#起点
        行们.append(路径+':'+str(取字段(起点,'line')+1)+':'+str(取字段(起点,'character')+1))#一基坐标
    if 省略>0:#有省略
        行们.append('… '+str(省略)+' more location'+( '' if 省略==1 else 's')+' omitted (limit '+str(最大位置数)+').')#省略标记
    return 限制结果('\n'.join(行们),最大结果字符数,'locations')#合并

def 格式化悬停(悬停,最大结果字符数):#渲染悬停结果
    """null 悬停给出固定文案。"""
    文本='No hover information.' if 悬停 is None else str(取字段(悬停,'contents'))#正文
    return 限制结果(文本,最大结果字符数,'hover')#限长

def 呈现语言服务器调用(参数):#UI 呈现用摘要
    """只依赖参数，不触 I/O。"""
    输入=解析语言服务器参数(参数)#已校验
    return 取字段(输入,'operation')+' '+取字段(输入,'filePath')+':'+str(取字段(输入['position'],'line')+1)+':'+str(取字段(输入['position'],'character')+1)#摘要

def 会话工作目录(执行上下文):#从调用智能体取 cwd
    """非智能体调用方返回 None。"""
    智能体=取字段(执行上下文,'agent')#调用智能体
    if 智能体 is None:#无智能体
        return None#无 cwd
    会话=取字段(智能体,'session')#会话
    if 会话 is None:#无会话
        return None#无 cwd
    头=取字段(会话,'header')#会话头
    if 头 is None:#无头
        return None#无 cwd
    return 取字段(头,'cwd')#工作目录
