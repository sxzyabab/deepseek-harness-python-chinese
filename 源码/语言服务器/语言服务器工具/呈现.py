'`lsp` 工具的纯格式化与坐标转换'
import ntpath#视窗路径
import posixpath#正斜杠路径
import re#盘符判断
from urllib.parse import unquote,urlparse#文件 URI 解码
from ..语言服务器.类型 import 语言服务器操作#操作联合

默认最大位置数=100#默认位置条数上限
默认最大结果字符数=16000#默认完整结果字符上限

__all__=[#仅中文公开名
    '语言服务器操作列表','默认最大位置数','默认最大结果字符数',
    '解析语言服务器参数','格式化位置列表','格式化悬停','呈现语言服务器调用','渲染uri',
]#公开面结束

语言服务器操作列表=list(语言服务器操作)#运行时操作表
盘符路径=re.compile(r'^/[a-z](?::|%3A)',re.IGNORECASE)#file URI 路径里的视窗盘符

def 一基坐标(值,名称):
    '模型坐标从 1 开始。排除布尔'
    if isinstance(值,bool) or isinstance(值,int) is False or 值<1:#非法
        raise Exception(名称+' must be a positive integer (one-based)')#拒绝
    return 值#合法

def 解析语言服务器参数(参数):
    'operation 必须是四种之一；line/character 为正整数。参数是工具入参 dict'
    if 'operation' not in 参数:#缺操作
        raise Exception('operation must be one of '+', '.join(语言服务器操作列表))#拒绝
    操作=参数['operation']#操作名
    if 操作 not in 语言服务器操作:#未知操作
        raise Exception('operation must be one of '+', '.join(语言服务器操作列表))#拒绝
    if 'file_path' not in 参数:#缺路径
        raise Exception('file_path must be a non-empty string')#拒绝
    路径=str(参数['file_path']).strip()#文件路径
    if 路径=='':#空路径
        raise Exception('file_path must be a non-empty string')#拒绝
    行=一基坐标(参数['line'] if 'line' in 参数 else None,'line')#一基行
    列=一基坐标(参数['character'] if 'character' in 参数 else None,'character')#一基列
    return {'operation':操作,'filePath':路径,'position':{'line':行-1,'character':列-1}}#零基

def 限制结果(文本,最大字符,种类):
    '完整结果含截断说明本身，按字符计'
    if len(文本)<=最大字符:#未超
        return 文本#原样
    标记='\n… '+种类+' truncated (limit '+str(最大字符)+' characters).'#截断说明
    if len(标记)>=最大字符:#说明自身超限
        return 标记[:最大字符]#只留说明前缀
    return 文本[:最大字符-len(标记)]+标记#正文加说明

def 含编码分隔(路径名,含反斜杠):
    '编码后的路径分隔符按文件 URL 规则拒绝'
    小写=路径名.lower()#比较用
    位置=0#扫描起点
    while 位置<len(小写):#逐段
        位置=小写.find('%',位置)#百分号
        if 位置<0 or 位置+2>=len(小写):#没有完整转义
            return False#无编码分隔
        片段=小写[位置:位置+3]#三位
        if 片段=='%2f' or (含反斜杠 and 片段=='%5c'):#编码斜杠
            return True#拒绝
        位置+=1#继续
    return False#无

def 域名转unicode(主机名):
    '把 punycode 主机名转回 Unicode'
    try:#idna
        return 主机名.encode('ascii').decode('idna')#解码
    except Exception:#不是 punycode
        return 主机名#原样

def 视窗文件路径(地址):
    '视窗世界的 file URL 转绝对路径'
    路径名=地址.path or ''#原始路径
    if 含编码分隔(路径名,True):#编码分隔
        raise ValueError('encoded separator')#拒绝
    解码=unquote(路径名)#解码
    主机=地址.hostname or ''#主机
    if 主机!='':#UNC
        return '\\\\'+域名转unicode(主机)+解码.replace('/','\\')#共享路径
    if len(解码)<3 or 解码[2]!=':' or not 解码[1].isalpha():#无盘符
        raise ValueError('not absolute')#拒绝
    return 解码[1:].replace('/','\\')#去掉前导斜杠

def 正斜杠文件路径(地址):
    'POSIX 世界的 file URL 转绝对路径'
    if (地址.hostname or '')!='':#带主机
        raise ValueError('host')#拒绝
    路径名=地址.path or ''#原始路径
    if 含编码分隔(路径名,False):#编码斜杠
        raise ValueError('encoded separator')#拒绝
    return unquote(路径名)#解码路径

def 文件路径(地址,视窗):
    '按执行世界解码 file URL，畸形则没有路径'
    try:#解码可能拒绝
        路径=视窗文件路径(地址) if 视窗 else 正斜杠文件路径(地址)#按世界
    except Exception:#畸形转义或权限段
        return None#没有路径
    if '\0' in 路径:#空字节
        return None#没有路径
    return 路径#可用

def 解析网址(文本):
    '非法 URL 没有地址'
    try:#解析
        地址=urlparse(文本)#地址
    except ValueError:#非法
        return None#没有
    if 地址.scheme=='':#相对或非法
        return None#没有
    return 地址#地址

def 相对路径(基,目标,视窗):
    '同一位置为空串；不同盘返回目标绝对路径'
    if 视窗:#视窗
        基规范=ntpath.normpath(基)#基
        目规范=ntpath.normpath(目标)#目标
        基盘,基余=ntpath.splitdrive(基规范)#基盘
        目盘,目余=ntpath.splitdrive(目规范)#目盘
        if 基盘.lower()!=目盘.lower():#不同盘
            return 目规范#绝对
        基段=[段 for 段 in 基余.split('\\') if 段!='']#基段
        目段=[段 for 段 in 目余.split('\\') if 段!='']#目段
        公共=0#公共前缀
        while 公共<len(基段) and 公共<len(目段) and 基段[公共].lower()==目段[公共].lower():#忽略大小写
            公共+=1#前进
        下段=['..']*(len(基段)-公共)+目段[公共:]#上溯加剩余
        if len(下段)==0:#同一位置
            return ''#空
        return '\\'.join(下段)#视窗相对
    规范基=posixpath.normpath(基)#基
    规范目=posixpath.normpath(目标)#目标
    if 规范基==规范目:#同一位置
        return ''#空
    return posixpath.relpath(规范目,规范基)#正斜杠相对

def 渲染uri(uri,工作区uri):
    '工作区内的 file URI 变成相对路径，其余保留 URI 或绝对路径'
    文本=str(uri)#目标
    if 文本.startswith('file:') is False:#非 file
        return 文本#原样
    目标=解析网址(文本)#目标地址
    工作区=解析网址(str(工作区uri))#工作区地址
    if 目标 is None or 工作区 is None:#非法 URL
        return 文本#原样
    if 工作区.scheme!='file':#工作区不是 file
        return 文本#原样
    工作区路径名=工作区.path or ''#工作区路径
    目标路径名=目标.path or ''#目标路径
    视窗世界=(工作区.hostname or '')!='' or 盘符路径.match(工作区路径名) is not None#工作区世界
    目标视窗=视窗世界 and ((目标.hostname or '')!='' or 盘符路径.match(目标路径名) is not None)#目标世界
    工作区路径=文件路径(工作区,视窗世界)#工作区文件路径
    目标路径=文件路径(目标,目标视窗)#目标文件路径
    if 工作区路径 is None or 目标路径 is None:#解不出
        return 文本#原样
    if 视窗世界!=目标视窗:#世界不同
        return 目标路径#目标绝对路径
    分隔='\\' if 视窗世界 else '/'#分隔
    相对=相对路径(工作区路径,目标路径,视窗世界)#相对
    绝对=ntpath.isabs(相对) if 视窗世界 else posixpath.isabs(相对)#是否绝对
    在外=相对=='..' or 相对.startswith('..'+分隔) or 绝对#跑出工作区
    if 相对=='':#同一位置
        渲染='.'#当前目录
    elif 在外:#外部
        渲染=目标路径#绝对
    else:#内部
        渲染=相对#相对
    if 视窗世界:#统一成模型可见斜杠
        return 渲染.replace('\\','/')#正斜杠
    return 渲染#POSIX

def 格式化位置列表(位置列表,工作区uri,最大位置数,最大结果字符数):
    '按文件分组并转回一基 path:line:character。位置是 dict'
    if len(位置列表)==0:#无结果
        return 限制结果('No results.',最大结果字符数,'locations')#空结果
    展示=位置列表[:最大位置数]#截断
    省略=len(位置列表)-len(展示)#省略数
    分组={}#路径 → 条目
    for 位置 in 展示:#逐条
        路径=渲染uri(位置['uri'],工作区uri)#渲染路径
        起点=位置['range']['start']#起点
        if 路径 not in 分组:#首次见到
            分组[路径]=[]#新组
        分组[路径].append(路径+':'+str(起点['line']+1)+':'+str(起点['character']+1))#一基坐标
    行列表=[]#输出行
    for 条目 in 分组.values():#按首次出现的文件
        行列表.extend(条目)#该文件的位置
    if 省略>0:#有省略
        行列表.append('… '+str(省略)+' more location'+('' if 省略==1 else 's')+' omitted (limit '+str(最大位置数)+').')#省略标记
    return 限制结果('\n'.join(行列表),最大结果字符数,'locations')#合并

def 格式化悬停(悬停,最大结果字符数):
    'null 悬停给出固定文案。悬停是 dict'
    文本='No hover information.' if 悬停 is None else str(悬停['contents'])#正文
    return 限制结果(文本,最大结果字符数,'hover')#限长

def 呈现语言服务器调用(参数):
    '只依赖原始参数，不校验、不触 I/O。参数是工具入参 dict'
    return {#通用搜索卡
        'card':'generic',#卡片
        'kind':'search',#种类
        'title':'LSP '+str(参数['operation'])+' '+str(参数['file_path'])+':'+str(参数['line'])+':'+str(参数['character']),#操作与一基光标
        'locations':[{'path':参数['file_path'],'line':参数['line']}],#聚焦查询行
    }#视图
