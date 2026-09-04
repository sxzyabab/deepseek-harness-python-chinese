"""worker VFS 的 POSIX 路径辅助：单一绝对根、无盘符、无符号链接。

**不是 `node:path` 替代品。** dirname、basename 与 parse 会先规范化，
因为此处每个调用方把结果交给 VFS，而 VFS 用规范化绝对路径做键。

对齐上游 `webworker-runtime/src/module-system/posix-path.ts`。公开面仅中文名。
"""
from urllib.parse import quote as 百分号编码,unquote as 百分号解码#URL编解码

__all__=[#仅中文公开名
    '分隔符','规范化','拼接','解析','目录名','基名','扩展名','是否绝对',
    '相对路径','拆分','转命名空间路径','路径转文件url','文件url转路径',
]#公开面结束

分隔符='/'#虚拟文件系统的路径分隔符

def 规范化(路径):#规范化路径
    """折叠 `.` 与 `..` 段。

    参数:
        路径: 任意数量分隔符的路径。
    返回:
        规范化路径；相对输入保留前导 `..` 段。
    """
    绝对=路径.startswith(分隔符)#是否绝对路径
    保留尾=len(路径)>1 and 路径.endswith(分隔符)#是否保留尾部分隔符
    输出=[]#输出段列表
    for 段 in 路径.split(分隔符):#按分隔符拆段
        if 段=='' or 段=='.':#跳过空段与当前目录
            continue#下一段
        if 段=='..' and len(输出)>0 and 输出[-1]!='..':#可上溯父段
            输出.pop()#弹出父段
            continue#处理下一段
        if 段=='..' and 绝对:#绝对路径上忽略根外的..
            continue#跳过
        输出.append(段)#保留本段
    主体=分隔符.join(输出)#拼接主体
    if 绝对:#绝对路径结果
        return 分隔符+主体+(分隔符 if 保留尾 and 主体!='' else '')#绝对
    if 主体=='':#空相对路径
        return './' if 保留尾 else '.'#点路径
    return 主体+(分隔符 if 保留尾 else '')#相对路径结果

def 拼接(*段们):#拼接路径段
    """拼接各段并规范化结果。"""
    已拼=分隔符.join(段 for 段 in 段们 if 段!='')#过滤空段后拼接
    return '.' if 已拼=='' else 规范化(已拼)#空则点，否则规范化

def 解析(*段们):#解析为绝对路径
    """自右向左相对基目录解析各段。"""
    路径=''#累积路径
    for 段 in reversed(段们):#自右向左扫描
        if 段=='':#跳过空段
            continue#下一段
        路径=段 if 路径=='' else f'{段}{分隔符}{路径}'#前置拼接
        if 段.startswith(分隔符):#遇绝对段则停
            break#停止
    return 规范化(路径 if 路径.startswith(分隔符) else f'{分隔符}{路径}')#补根后规范化

def 目录名(路径):#取目录部分
    """路径的目录部分，经规范化后（见模块说明）。"""
    已规范=规范化(路径).rstrip('/')#规范化并去尾斜杠
    索引=已规范.rfind(分隔符)#最后一个分隔符位置
    if 索引<0:#无分隔符则当前目录
        return '.'#当前目录
    if 索引==0:#根下子项返回根
        return 分隔符#根
    return 已规范[:索引]#截到父目录

def 基名(路径,后缀=None):#取基名
    """路径最后一段，经规范化后（见模块说明）。"""
    已规范=规范化(路径).rstrip('/')#规范化并去尾斜杠
    名称=已规范[已规范.rfind(分隔符)+1:]#截取最后一段
    if 后缀 is not None and 后缀!=名称 and 名称.endswith(后缀):#剥后缀
        return 名称[:-len(后缀)]#剥后
    return 名称#返回基名

def 扩展名(路径):#取扩展名
    """最后一段的扩展名，含点。"""
    名称=基名(路径)#先取基名
    索引=名称.rfind('.')#最后一个点位置
    return '' if 索引<=0 else 名称[索引:]#无有效扩展则空串

def 是否绝对(路径):#是否绝对路径
    """报告路径是否从根开始。"""
    return 路径.startswith(分隔符)#以分隔符开头即绝对

def 相对路径(源,目标):#计算相对路径
    """从一个绝对路径到另一绝对路径的相对路径。"""
    源段=[段 for 段 in 解析(源).split(分隔符) if 段!='']#源路径段
    目标段=[段 for 段 in 解析(目标).split(分隔符) if 段!='']#目标路径段
    共享=0#公共前缀长度
    while 共享<len(源段) and 共享<len(目标段) and 源段[共享]==目标段[共享]:#统计公共前缀
        共享+=1#推进
    上溯=['..']*(len(源段)-共享)#上溯段
    return 分隔符.join(上溯+目标段[共享:])#拼接相对路径

def 拆分(路径):#解析路径组件
    """将路径拆成各组件，经规范化后（见模块说明）。"""
    根=分隔符 if 是否绝对(路径) else ''#根前缀
    底=基名(路径)#基名
    扩=扩展名(路径)#扩展名
    return {'root':根,'dir':目录名(路径),'base':底,'ext':扩,'name':底 if 扩=='' else 底[:-len(扩)]}#组装

def 转命名空间路径(路径):#命名空间路径透传
    """Node 仅 Windows 的命名空间路径转换；POSIX 下原样返回。"""
    return 路径#POSIX下不变

def 路径转文件url(路径):#路径转file URL
    """将 VFS 路径转为 `file:` URL 字符串。"""
    绝对=解析(路径)#先解析为绝对
    return 'file://'+分隔符.join(百分号编码(段) for 段 in 绝对.split(分隔符))#编码各段并拼接

def 文件url转路径(网址):#file URL转路径
    """将 `file:` URL 转回 VFS 路径。"""
    文本=网址 if isinstance(网址,str) else getattr(网址,'href',str(网址))#统一为文本
    if not 文本.startswith('file://'):#非file协议则抛错
        raise Exception(f'webworker vfs: not a file URL: {文本}')#拒绝
    去查询=文本[len('file://'):].split('?',1)[0].split('#',1)[0]#去查询/片段
    return 百分号解码(去查询) or 分隔符#解码
