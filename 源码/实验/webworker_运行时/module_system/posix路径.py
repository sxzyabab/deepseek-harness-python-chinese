from ..node.未实现失败 import 运行时错误
from urllib.parse import quote as 百分号编码,unquote as 百分号解码

__all__=[
    '分隔符','规范化','拼接','解析','目录名','基名','扩展名','是否绝对',
    '相对路径','拆分','转命名空间路径','路径转文件url','文件url转路径',
]

分隔符='/'

def 规范化(路径):
    """折叠 `.` 与 `..` 段。

    参数:
        路径: 任意数量分隔符的路径。
    返回:
        规范化路径；相对输入保留前导 `..` 段。
    """
    绝对=路径.startswith(分隔符)
    保留尾=len(路径)>1 and 路径.endswith(分隔符)
    输出=[]
    for 段 in 路径.split(分隔符):
        if 段=='' or 段=='.':
            continue
        if 段=='..' and len(输出)>0 and 输出[-1]!='..':
            输出.pop()
            continue
        if 段=='..' and 绝对:#绝对路径上忽略根外的..
            continue
        输出.append(段)
    主体=分隔符.join(输出)
    if 绝对:
        return 分隔符+主体+(分隔符 if 保留尾 and 主体!='' else '')
    if 主体=='':
        return './' if 保留尾 else '.'
    return 主体+(分隔符 if 保留尾 else '')

def 拼接(*段列表):
    """拼接各段并规范化结果。"""
    已拼=分隔符.join(段 for 段 in 段列表 if 段!='')
    return '.' if 已拼=='' else 规范化(已拼)

def 解析(*段列表):
    """自右向左相对基目录解析各段。"""
    路径=''
    for 段 in reversed(段列表):
        if 段=='':
            continue
        路径=段 if 路径=='' else f'{段}{分隔符}{路径}'
        if 段.startswith(分隔符):
            break
    return 规范化(路径 if 路径.startswith(分隔符) else f'{分隔符}{路径}')

def 目录名(路径):
    """路径的目录部分，经规范化后（见模块说明）。"""
    已规范=规范化(路径).rstrip('/')
    索引=已规范.rfind(分隔符)
    if 索引<0:
        return '.'
    if 索引==0:
        return 分隔符
    return 已规范[:索引]

def 基名(路径,后缀=None):
    """路径最后一段，经规范化后（见模块说明）。"""
    已规范=规范化(路径).rstrip('/')
    名称=已规范[已规范.rfind(分隔符)+1:]
    if 后缀 is not None and 后缀!=名称 and 名称.endswith(后缀):
        return 名称[:-len(后缀)]
    return 名称

def 扩展名(路径):
    """最后一段的扩展名，含点。"""
    名称=基名(路径)
    索引=名称.rfind('.')
    return '' if 索引<=0 else 名称[索引:]

def 是否绝对(路径):
    """报告路径是否从根开始。"""
    return 路径.startswith(分隔符)

def 相对路径(源,目标):
    """从一个绝对路径到另一绝对路径的相对路径。"""
    源段=[段 for 段 in 解析(源).split(分隔符) if 段!='']
    目标段=[段 for 段 in 解析(目标).split(分隔符) if 段!='']
    共享=0
    while 共享<len(源段) and 共享<len(目标段) and 源段[共享]==目标段[共享]:
        共享+=1
    上溯=['..']*(len(源段)-共享)
    return 分隔符.join(上溯+目标段[共享:])

def 拆分(路径):
    """将路径拆成各组件，经规范化后（见模块说明）。"""
    根=分隔符 if 是否绝对(路径) else ''
    底=基名(路径)
    扩=扩展名(路径)
    return {'root':根,'dir':目录名(路径),'base':底,'ext':扩,'name':底 if 扩=='' else 底[:-len(扩)]}

def 转命名空间路径(路径):
    """Node 仅 Windows 的命名空间路径转换；POSIX 下原样返回。"""
    return 路径

def 路径转文件url(路径):
    """将 VFS 路径转为 `file:` URL 字符串。"""
    绝对=解析(路径)
    return 'file://'+分隔符.join(百分号编码(段) for 段 in 绝对.split(分隔符))

def 文件url转路径(网址):
    """将 `file:` URL 转回 VFS 路径。"""
    文本=网址 if isinstance(网址,str) else getattr(网址,'href',str(网址))
    if not 文本.startswith('file://'):
        raise 运行时错误(f'webworker vfs: not a file URL: {文本}')
    去查询=文本[len('file://'):].split('?',1)[0].split('#',1)[0]
    return 百分号解码(去查询) or 分隔符
