"""不含 Cordis 的本地文件系统机制。此提供方层返回已校验的 UTF-8 文本、流式读取大文件并拒绝二进制数据；写入在私有兄弟目录里暂存独占的仅所有者文件，并原子发布。"""
import os#路径与底层文件描述符
import errno#POSIX 错误号
import uuid#暂存目录唯一名
import stat#文件类型位判定
import shutil#递归删除暂存
import codecs#增量 UTF-8 解码
import fs#文件系统错误与品牌
from .win32 import 复制文件Dacl,替换文件#Windows DACL 复制与替换

二进制采样字节=8192#二进制探测采样字节数
diff基准读取块字节=64*1024#diff 基准每次读取块大小
是普通文件模式=stat.S_ISREG#POSIX 普通文件
是目录模式=stat.S_ISDIR#POSIX 目录
是符号链接模式=stat.S_ISLNK#POSIX 符号链接

def 取字段(对象,键):#读取映射或对象上的字段
    """读取映射或对象上的字段。"""
    if isinstance(对象,dict):#映射
        return 对象[键]#映射键
    return getattr(对象,键)#对象属性

def 试取(对象,键,缺省=None):#读取可选字段
    """读取可选字段，缺席为缺省。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        return 对象.get(键,缺省)#映射可选键
    return getattr(对象,键,缺省)#对象可选属性

def 是否已中止(信号):#信号是否已中止
    """信号是否已中止。"""
    if 信号 is None:#无信号
        return False#未中止
    if isinstance(信号,dict):#映射信号
        return bool(信号.get('aborted') or 信号.get('已中止'))#中英文字段
    return bool(getattr(信号,'aborted',False) or getattr(信号,'已中止',False))#对象属性

def 若已中止则抛(信号,动词):#已中止则抛出结构化错误
    """已中止则抛出结构化 `FS_ABORTED`。"""
    if 是否已中止(信号):#已中止
        raise fs.文件系统错误(f'{动词} aborted','FS_ABORTED')#按动词报告已中止

def 补节点错误码(错误):#给 OSError 补上 Node 风格 code
    """给逃出的 OSError 补上 Node 风格 `code`。"""
    if isinstance(错误,OSError) and getattr(错误,'code',None) is None:#尚无 code
        表={#常见 errno 映射
            errno.ENOENT:'ENOENT',#不存在
            errno.ENOTDIR:'ENOTDIR',#非目录
            errno.EEXIST:'EEXIST',#已存在
            errno.EACCES:'EACCES',#权限
            errno.EPERM:'EPERM',#操作不允许
        }#映射表结束
        错误.code=表.get(错误.errno) or (errno.errorcode.get(错误.errno) if 错误.errno else None) or 'EIO'#写入 code
    return 错误#原样返回

def 是否不存在错误(错误):#ENOENT
    """判断是否为文件不存在。"""
    if not isinstance(错误,BaseException):#非异常
        return False#否
    if getattr(错误,'code',None)=='ENOENT':#Node 风格
        return True#是
    return isinstance(错误,OSError) and 错误.errno==errno.ENOENT#POSIX errno

def 是否已存在错误(错误):#EEXIST
    """判断是否为已存在。"""
    if not isinstance(错误,BaseException):#非异常
        return False#否
    if getattr(错误,'code',None)=='EEXIST':#Node 风格
        return True#是
    return isinstance(错误,OSError) and 错误.errno==errno.EEXIST#POSIX errno

def 是否非目录错误(错误):#ENOTDIR
    """判断是否为父段不是目录。"""
    if not isinstance(错误,BaseException):#非异常
        return False#否
    if getattr(错误,'code',None)=='ENOTDIR':#Node 风格
        return True#是
    return isinstance(错误,OSError) and 错误.errno==errno.ENOTDIR#POSIX errno

def 是否中止错误(错误):#AbortError
    """判断是否为中止错误。"""
    return isinstance(错误,BaseException) and getattr(错误,'name',None)=='AbortError'#名为 AbortError

def 是否权限错误(错误):#EACCES 或 EPERM
    """判断是否为权限错误。"""
    if not isinstance(错误,BaseException):#非异常
        return False#否
    码=getattr(错误,'code',None)#Node 风格码
    if 码=='EACCES' or 码=='EPERM':#权限类
        return True#是
    return isinstance(错误,OSError) and (错误.errno==errno.EACCES or 错误.errno==errno.EPERM)#POSIX errno

def 错误消息(错误):#把未知错误收成消息字符串
    """把未知错误收成消息字符串。"""
    if isinstance(错误,BaseException):#异常
        消息=getattr(错误,'message',None)#可选 message
        if 消息 is not None:#有 message
            return str(消息)#用 message
        return str(错误) or type(错误).__name__#否则 str 或类名
    return str(错误)#非异常直接 String

def 取内部(内部,名):#读取测试钩子字段
    """读取测试钩子字段。"""
    if 内部 is None:#无钩子
        return None#缺席
    if isinstance(内部,dict):#映射钩子
        return 内部.get(名)#可选键
    return getattr(内部,名,None)#对象属性

def 版本令牌自状态(信息):#从 stat 推导版本
    """由高分辨率身份与新鲜度元数据构成的不透明版本令牌。"""
    return fs.版本令牌(f'{信息.st_dev}:{信息.st_ino}:{信息.st_size}:{信息.st_mtime_ns}:{信息.st_ctime_ns}')#设备、inode、大小、mtime、ctime

def 路径类型(信息):#跟随链接后的类型
    """从 stat 判别跟随链接后的类型。"""
    if 是普通文件模式(信息.st_mode):#普通文件
        return 'file'#文件
    if 是目录模式(信息.st_mode):#目录
        return 'directory'#目录
    return 'other'#其他

def 路径链接类型(信息):#含符号链接的类型
    """从 lstat 判别含符号链接的类型。"""
    if 是符号链接模式(信息.st_mode):#末段是符号链接
        return 'symlink'#符号链接
    return 路径类型(信息)#否则与跟随链接的类型相同

def 探测状态(绝对路径,跟随链接):#按 stat 或 lstat 探测，缺失则 None
    """按所给 stat 函数探测，缺失则 None。"""
    try:#尝试读取元数据
        if 跟随链接:#跟随链接
            return os.stat(绝对路径)#stat
        return os.lstat(绝对路径)#lstat
    except OSError as 错误:#元数据失败
        if not 是否不存在错误(错误) and not 是否非目录错误(错误):#真实故障
            raise 补节点错误码(错误)#上抛
        return None#缺失

def 解析本地目标(工作目录,路径):#解析本地稳定目标
    """把路径解析成绝对展示路径与 realpath 身份。对缺失目标，对最近已存在祖先做 realpath 并追加缺失后缀。"""
    if len(路径.strip())==0:#空路径视为未找到
        raise fs.文件系统错误('file_path must be a non-empty string','FS_NOT_FOUND')#空路径
    展示路径=os.path.abspath(os.path.join(工作目录,路径))#相对 cwd 得到绝对展示路径
    try:#优先对文件自身做 realpath
        return {'displayPath':展示路径,'targetKey':fs.目标键(os.path.realpath(展示路径))}#存在则目标键即 realpath
    except OSError as 错误:#realpath 失败
        if 是否非目录错误(错误):#父段不是目录
            raise fs.文件系统错误(f'cannot resolve "{展示路径}": a parent path segment is not a directory','FS_NOT_FOUND')#结构化未找到
        if not 是否不存在错误(错误):#其他错误
            raise 补节点错误码(错误)#原样抛出
    缺失=[os.path.basename(展示路径)]#从缺失的基名开始收集后缀
    祖先=os.path.dirname(展示路径)#从父目录向上走
    while True:#直到找到已存在祖先
        try:#尝试 realpath 当前祖先
            真实祖先=os.path.realpath(祖先)#已存在祖先的 realpath
            if os.name=='nt':#Windows 修复：非目录祖先
                父信息=os.stat(真实祖先)#stat 该祖先
                if not 是目录模式(父信息.st_mode):#祖先不是目录
                    raise fs.文件系统错误(f'cannot resolve "{展示路径}": a parent path segment is not a directory','FS_NOT_FOUND')#视为未找到
            return {'displayPath':展示路径,'targetKey':fs.目标键(os.path.join(真实祖先,*缺失))}#真实祖先加上缺失后缀
        except fs.文件系统错误:#已是结构化错误
            raise#上抛
        except OSError as 错误:#此祖先仍缺失
            if not 是否不存在错误(错误):#其他错误
                raise 补节点错误码(错误)#原样抛出
            父目录=os.path.dirname(祖先)#再上一层
            if 父目录==祖先:#已到根
                return {'displayPath':展示路径,'targetKey':fs.目标键(展示路径)}#用展示路径当键
            缺失.insert(0,os.path.basename(祖先))#把当前祖先基名插到缺失后缀前面
            祖先=父目录#继续向上

def 探测(绝对路径):#跟随链接探测路径
    """探测路径的版本、模式、类型和大小。缺失则为 None。"""
    信息=探测状态(绝对路径,True)#bigint 风格 stat
    if 信息 is None:#缺失
        return None#不存在
    return {#打包路径信息
        'version':版本令牌自状态(信息),#版本令牌
        'mode':信息.st_mode&0o777,#权限位
        'type':路径类型(信息),#类型
        'size':信息.st_size,#大小
    }#PathInfo 结束

def 不跟随探测(绝对路径):#不跟随末段链接探测
    """不跟随最后一段符号链接地探测路径。"""
    信息=探测状态(绝对路径,False)#bigint 风格 lstat
    if 信息 is None:#缺失
        return None#不存在
    return {#打包路径条目信息
        'version':版本令牌自状态(信息),#版本令牌
        'mode':信息.st_mode&0o777,#权限位
        'type':路径链接类型(信息),#类型含 symlink
        'size':信息.st_size,#大小
    }#PathLinkInfo 结束

def 列举读写错误(展示路径,错误):#把列举 I/O 失败收成结构化错误
    """把列举 I/O 失败收成结构化错误。"""
    if isinstance(错误,fs.文件系统错误):#已是 FsError
        return 错误#原样返回
    if 是否不存在错误(错误) or 是否非目录错误(错误):#缺失视为未找到
        return fs.文件系统错误(f'cannot list "{展示路径}": not found','FS_NOT_FOUND',{'cause':错误})#未找到
    if 是否权限错误(错误):#权限拒绝
        return fs.文件系统错误(f'cannot list "{展示路径}": permission denied','FS_PERMISSION_DENIED',{'cause':错误})#权限
    return fs.文件系统错误(f'cannot list "{展示路径}": {错误消息(错误)}','FS_IO_ERROR',{'cause':错误})#其余为 IO 错误

def 列目录(目标,信号=None):#列举目录直接子项
    """以稳定名称顺序列举目录的直接子项。每个子项包含已解析目标，以及仍可用时的 stat 元数据。"""
    若已中止则抛(信号,'list')#开始前检查中止
    展示路径=取字段(目标,'displayPath')#展示路径
    目标键=取字段(目标,'targetKey')#目标键
    try:#探测目录
        信息=探测(目标键)#跟随链接 stat
    except Exception as 错误:#探测失败
        raise 列举读写错误(展示路径,错误)#收成列举错误
    if 信息 is None:#目录不存在
        raise fs.文件系统错误(f'cannot list "{展示路径}": not found','FS_NOT_FOUND')#未找到
    if 信息['type']!='directory':#不是目录
        raise fs.文件系统错误(f'cannot list "{展示路径}": not a directory','FS_NOT_DIRECTORY')#非目录
    try:#读取目录项
        名称们=os.listdir(目标键)#子项基名列表
    except OSError as 错误:#readdir 失败
        raise 列举读写错误(展示路径,错误)#收成列举错误
    若已中止则抛(信号,'list')#读取后再查中止
    结果=[]#收集子项
    for 名称 in sorted(名称们):#按名称稳定排序后逐项
        若已中止则抛(信号,'list')#每项前检查中止
        try:#解析子目标并探测元数据
            身份=解析本地目标(目标键,名称)#相对父目标键解析身份
            子目标={'displayPath':os.path.join(展示路径,名称),'targetKey':身份['targetKey']}#展示路径用父展示路径拼接基名
            子信息=探测(子目标['targetKey'])#探测子项
            条目={'name':名称,'type':子信息['type'] if 子信息 is not None else 'other','target':子目标}#基础字段
            if 子信息 is not None:#有元数据则带版本
                条目['version']=子信息['version']#版本令牌
            if 子信息 is not None and 子信息['type']=='file':#普通文件带大小
                条目['size']=子信息['size']#字节大小
            结果.append(条目)#收入子项
        except Exception as 错误:#子项解析失败
            raise 列举读写错误(os.path.join(展示路径,名称),错误)#按子路径报告
        若已中止则抛(信号,'list')#每项后再查中止
    return 结果#按名称顺序返回

def 非文本错误(动词,展示路径):#非法 UTF-8
    """把非法 UTF-8 失败收成结构化 `FS_NOT_TEXT`。"""
    return fs.文件系统错误(f'cannot {动词} "{展示路径}": invalid UTF-8 text','FS_NOT_TEXT')#按动词报告不是文本

def 解码utf8(缓冲,动词,展示路径):#一次性解码整个缓冲
    """用 fatal UTF-8 把缓冲解码成字符串；非法字节变成 `FS_NOT_TEXT`。"""
    try:#fatal 解码
        return bytes(缓冲).decode('utf-8')#非法字节抛 UnicodeDecodeError
    except UnicodeDecodeError:#非法 UTF-8
        raise 非文本错误(动词,展示路径)#视为不是文本
    except TypeError:#非解码类故障
        raise#原样抛出

def 解码utf8流(解码器,块,动词,展示路径):#流式解码一块或冲刷
    """对流式解码器喂一块或冲刷尾部；非法 UTF-8 变成 `FS_NOT_TEXT`。"""
    try:#流式或冲刷解码
        if 块 is None:#冲刷
            return 解码器.decode(b'',True)#冲刷尾部
        return 解码器.decode(块,False)#有块则 stream
    except UnicodeDecodeError:#非法 UTF-8
        raise 非文本错误(动词,展示路径)#视为不是文本
    except TypeError:#非解码类故障
        raise#原样抛出

def 确认普通文件(目标,动词,信号=None):#stat 并要求普通文件
    """确认目标是普通文件；缺失或不规则则抛结构化错误。"""
    若已中止则抛(信号,动词)#开始前检查中止
    展示路径=取字段(目标,'displayPath')#展示路径
    目标键=取字段(目标,'targetKey')#目标键
    try:#跟随链接 stat
        信息=os.stat(目标键)#读取元数据
    except OSError as 错误:#stat 失败
        if not 是否不存在错误(错误):#其他错误
            raise 补节点错误码(错误)#原样抛出
        raise fs.文件系统错误(f'cannot {动词} "{展示路径}": not found','FS_NOT_FOUND')#缺失视为未找到
    if not 是普通文件模式(信息.st_mode):#不是普通文件
        raise fs.文件系统错误(f'cannot {动词} "{展示路径}": not a regular file','FS_NOT_REGULAR_FILE')#非普通文件
    return 信息#普通文件的 stat

def 可中止读文件(绝对路径,动词,信号=None):#可中止地读取整个文件
    """带所供信号的整文件读取，把中止翻译成 `FS_ABORTED`。"""
    若已中止则抛(信号,动词)#开始前检查中止
    try:#调用整文件读
        with open(绝对路径,'rb') as 文件:#二进制打开
            数据=文件.read()#读全部字节
    except OSError as 错误:#读取失败
        if 是否中止错误(错误):#中止
            raise fs.文件系统错误(f'{动词} aborted','FS_ABORTED')#结构化错误
        raise 补节点错误码(错误)#其他错误原样抛出
    若已中止则抛(信号,动词)#读完后再查中止
    return 数据#完整缓冲

def 读整文件文本(目标,信号=None):#整文件解码为字符串
    """把整个普通 UTF-8 文本文件读成单个已解码字符串。拒绝非普通文件、非法 UTF-8，以及含 NUL 字节的二进制采样。"""
    确认普通文件(目标,'read',信号)#先确认是普通文件
    原始=可中止读文件(取字段(目标,'targetKey'),'read',信号)#可中止地读全部字节
    若已中止则抛(信号,'read')#读完后再查中止
    if 0 in 原始[:二进制采样字节]:#前采样含 NUL 则视为二进制
        raise fs.文件系统错误(f'cannot read "{取字段(目标,"displayPath")}": binary file','FS_NOT_TEXT')#拒绝二进制
    return 解码utf8(原始,'read',取字段(目标,'displayPath'))#fatal 解码为 UTF-8

def 读整文件字节(目标,信号,最大字节,内部=None):#按字节上限读取原始内容
    """以原始字节读取整个普通文件。`maxBytes` 约束完整内容：stat 大小在内容 I/O 之前短路；随后最多再多读一字节。"""
    if 内部 is None:#无钩子
        内部={}#空钩子
    信息=确认普通文件(目标,'read',信号)#先确认是普通文件
    if 信息.st_size>最大字节:#stat 大小已超过上限
        raise fs.文件系统错误(f'cannot read "{取字段(目标,"displayPath")}": {信息.st_size} bytes exceeds the {最大字节}-byte limit','FS_TOO_LARGE')#短路过大文件
    观察=取内部(内部,'inspectReadBytesAfterStat')#测试钩子：stat 后注入增长竞态
    if 观察 is not None:#有钩子
        观察(目标)#调用钩子
    展示路径=取字段(目标,'displayPath')#展示路径
    try:#有界读取
        with open(取字段(目标,'targetKey'),'rb') as 文件:#二进制打开
            数据=文件.read(最大字节+1)#最多再多读一字节以检测增长
    except OSError as 错误:#读失败
        if 是否中止错误(错误) or 是否已中止(信号):#中止
            raise fs.文件系统错误('read aborted','FS_ABORTED')#结构化错误
        raise 补节点错误码(错误)#其他错误原样抛出
    if 是否已中止(信号):#读后再查中止
        raise fs.文件系统错误('read aborted','FS_ABORTED')#结构化错误
    if len(数据)>最大字节:#stat 后文件增长越过上限
        raise fs.文件系统错误(f'cannot read "{展示路径}": content exceeds the {最大字节}-byte limit','FS_TOO_LARGE')#拒绝无界缓冲
    return 数据#完整原始字节

def 流整文件文本(目标,信号=None):#流式解码整文件
    """以已解码文本块读取整个普通 UTF-8 文本文件。文本语义与读整文件文本相同，但从不把整文件放进内存。"""
    确认普通文件(目标,'read',信号)#先确认是普通文件
    展示路径=取字段(目标,'displayPath')#展示路径
    解码器=codecs.getincrementaldecoder('utf-8')('strict')#跨块 fatal 解码器
    已采样=0#已用于二进制探测的字节
    文件=open(取字段(目标,'targetKey'),'rb')#可读流
    try:#流式解码
        while True:#逐块
            若已中止则抛(信号,'read')#每块前检查中止
            块=文件.read(64*1024)#读一块
            if not 块:#EOF
                break#结束循环
            if 已采样<二进制采样字节:#采样未满
                采样=块[:min(len(块),二进制采样字节-已采样)]#本块还能采多少
                if 0 in 采样:#采样含 NUL
                    raise fs.文件系统错误(f'cannot read "{展示路径}": binary file','FS_NOT_TEXT')#拒绝二进制
                已采样+=len(采样)#累加已采样字节
            yield 解码utf8流(解码器,块,'read',展示路径)#产出本块文本
        yield 解码utf8流(解码器,None,'read',展示路径)#冲刷解码器尾部
    except fs.文件系统错误:#已结构化
        raise#上抛
    except Exception as 错误:#流或解码失败
        if 是否中止错误(错误):#中止
            raise fs.文件系统错误('read aborted','FS_ABORTED')#结构化错误
        raise#其他错误原样抛出
    finally:#无论成败都关文件
        文件.close()#释放描述符

def 默认删除暂存(路径):#递归删除暂存目录
    """默认递归删除暂存目录；仅忽略缺失。"""
    try:#删除暂存目录
        shutil.rmtree(路径)#递归删除
    except OSError as 错误:#删除失败
        if 是否不存在错误(错误):#仅忽略缺失
            return#已不存在
        raise 补节点错误码(错误)#其他错误上抛

def 默认检查发布目标(路径):#发布失败后 lstat 目标
    """发布失败后检查目标条目。"""
    return os.lstat(路径)#lstat 目标

def 抛受守卫创建失败(错误,绝对路径,展示路径,检查发布目标):#把硬链接不替换失败收成结构化错误
    """把硬链接不替换失败收成结构化错误。"""
    已有=None#失败后看到的目标
    try:#检查目标条目
        已有=检查发布目标(绝对路径)#lstat 目标
    except Exception as 元数据错误:#目标元数据失败
        if not 是否不存在错误(元数据错误) and not 是否非目录错误(元数据错误):#不是缺失
            raise fs.文件系统错误(f'cannot write "{展示路径}": {错误消息(元数据错误)}','FS_IO_ERROR',{'cause':元数据错误})#权限/IO 故障
    if 已有 is not None:#目标条目存在
        if not 是普通文件模式(已有.st_mode):#不是普通文件
            raise fs.文件系统错误(f'cannot write "{展示路径}": not a regular file','FS_NOT_REGULAR_FILE',{'cause':错误})#拒绝非普通文件
        raise fs.文件系统错误(f'cannot overwrite existing "{展示路径}" without reading it first','FS_NOT_OBSERVED',{'cause':错误})#未经观察不得覆盖
    if 是否已存在错误(错误):#errno 是已存在但检查时目标又不见了
        raise fs.文件系统错误(f'cannot overwrite existing "{展示路径}" without reading it first','FS_NOT_OBSERVED',{'cause':错误})#仍按未经观察拒绝
    raise fs.文件系统错误(f'cannot write "{展示路径}": {错误消息(错误)}','FS_IO_ERROR',{'cause':错误})#其余为 IO 错误

def 原子写文件(绝对路径,内容,模式,信号,内部=None,若缺则创建=None):#原子发布文件
    """经同目录里私有、已同步的暂存文件原子替换目标。POSIX 用 `0o700` 与 `0o600` 保护暂存；Windows 替换复制已有 DACL 并在发布时保留目标描述符。"""
    if 内部 is None:#无钩子
        内部={}#空钩子
    若已中止则抛(信号,'write')#开始前检查中止
    目录=os.path.dirname(绝对路径)#目标所在目录
    os.makedirs(目录,exist_ok=True)#确保父目录存在
    若已中止则抛(信号,'write')#mkdir 后再查中止
    暂存名生成=取内部(内部,'tempDirName')#覆盖生成的私有暂存目录名
    暂存目录名=暂存名生成(绝对路径) if 暂存名生成 is not None else f'.{os.path.basename(绝对路径)}.{os.getpid()}.{uuid.uuid4()}.tmpdir'#私有暂存目录名
    暂存目录=os.path.join(目录,暂存目录名)#暂存目录路径
    临时名生成=取内部(内部,'tempName')#覆盖生成的临时文件名
    临时名=临时名生成(绝对路径) if 临时名生成 is not None else f'{os.path.basename(绝对路径)}.tmp'#临时文件名
    临时路径=os.path.join(暂存目录,临时名)#临时文件路径
    平台=取内部(内部,'platform')#宿主或测试覆盖平台
    if 平台 is None:#未覆盖
        平台='win32' if os.name=='nt' else os.name#对齐 Node process.platform
    复制Dacl=取内部(内部,'copyFileDacl') or 复制文件Dacl#DACL 复制
    替换=取内部(内部,'replaceFile') or 替换文件#Win32 替换
    链接文件=取内部(内部,'linkFile') or os.link#硬链接发布
    检查发布目标=取内部(内部,'inspectPublicationTarget') or 默认检查发布目标#发布失败后检查目标
    删除暂存=取内部(内部,'removeStagingDir') or 默认删除暂存#删除暂存目录
    描述符=None#独占打开的临时文件句柄
    已建暂存=False#暂存目录是否已创建
    try:#暂存、写入、发布
        os.mkdir(暂存目录,0o700)#创建仅所有者暂存目录
        已建暂存=True#记下已创建，失败时要清
        os.chmod(暂存目录,0o700)#再 chmod，抵消 umask
        打开标志=os.O_CREAT|os.O_EXCL|os.O_WRONLY#独占创建写
        if os.name=='nt':#Windows 需要二进制标志
            打开标志|=os.O_BINARY#二进制模式
        描述符=os.open(临时路径,打开标志,0o600)#独占创建仅所有者临时文件
        os.chmod(临时路径,0o600)#再 chmod，抵消 umask
        if 平台=='win32' and 模式 is not None:#Windows 替换：先复制已有 DACL
            复制Dacl(绝对路径,临时路径)#把受保护 DACL 复制到空临时文件
        数据=内容.encode('utf-8')#完整 UTF-8 字节
        已写=0#已写字节
        while 已写<len(数据):#写完整文本
            已写+=os.write(描述符,数据[已写:])#累加本写
        os.fsync(描述符)#刷到磁盘
        观察暂存=取内部(内部,'inspectTemp')#测试钩子：发布前观察暂存
        if 观察暂存 is not None:#有钩子
            观察暂存({'stagingDir':暂存目录,'tempPath':临时路径})#观察暂存路径
        if 模式 is not None:#恢复已有 POSIX 模式
            os.chmod(临时路径,模式)#chmod 临时文件
        os.close(描述符)#关闭后再发布
        描述符=None#关闭成功，失败路径不必再关
        若已中止则抛(信号,'write')#发布前最后一次中止检查
        if 若缺则创建 is not None:#受守卫创建：硬链接不替换
            try:#link 到最终路径
                链接文件(临时路径,绝对路径)#已存在则失败
            except Exception as 错误:#link 失败
                抛受守卫创建失败(错误,绝对路径,取字段(若缺则创建,'displayPath'),检查发布目标)#收成结构化错误
        elif 平台=='win32' and 模式 is not None:#Windows 替换：保留目标 ACL
            try:#ReplaceFileW
                替换(绝对路径,临时路径)#保留被替换文件的描述符
            except Exception as 错误:#替换失败
                if not 是否不存在错误(错误):#非缺失则原样抛出
                    raise#上抛
                os.rename(临时路径,绝对路径)#目标已消失则 rename 重建
        else:#POSIX 替换或 Windows 新建
            os.rename(临时路径,绝对路径)#原子改名发布
        try:#发布成功后清暂存目录
            删除暂存(暂存目录)#删掉私有暂存
        except Exception:#目标已提交
            pass#仅所有者的暂存残留不能把这次写入变成失败
    except Exception as 错误:#暂存/写入/发布失败
        失败=fs.文件系统错误('write aborted','FS_ABORTED') if 是否中止错误(错误) else 错误#中止则结构化，否则原错误
        if 描述符 is not None:#句柄仍开着
            try:#关闭临时文件
                os.close(描述符)#释放句柄
            except OSError as 关闭错误:#关闭也失败
                失败=fs.文件系统错误(f'write failed ({错误消息(失败)}) and temp close failed ({错误消息(关闭错误)})','FS_NOT_FOUND',{'cause':失败})#合并关闭失败
        if not 已建暂存:#暂存目录还没建成就直接抛
            raise 补节点错误码(失败)#上抛主失败
        try:#清暂存再抛主失败
            删除暂存(暂存目录)#尽力清掉暂存
        except Exception as 清理错误:#二次清理也失败
            raise fs.文件系统错误(f'write failed ({错误消息(失败)}) and temp cleanup failed ({错误消息(清理错误)})','FS_NOT_FOUND',{'cause':失败})#合并两条失败
        raise 补节点错误码(失败)#清理成功则抛出主失败

def 规范行尾(内容):#CRLF 收成 LF
    """把 CRLF 收成 LF。单独的 `\\r` 原样留下。"""
    return 内容.replace('\r\n','\n')#只替换 CRLF 对，单独 CR 不动

def 恢复行尾(内容,行尾):#恢复读时行尾
    """把 LF 规范化内容写回读时检测到的行尾。"""
    if 行尾=='LF':#LF 原样
        return 内容#原样返回
    return '\r\n'.join(规范行尾(内容).split('\n'))#先归一再拼回 CRLF

def 为编辑读取(绝对路径,展示路径,信号=None):#为编辑读取并做 LF 规范化
    """为编辑读取并解码文件：拒绝二进制，返回 LF 规范化内容以及写回用的原行尾风格。"""
    若已中止则抛(信号,'edit')#开始前检查中止
    缓冲=可中止读文件(绝对路径,'edit',信号)#可中止地读全部字节
    若已中止则抛(信号,'edit')#读完后再查中止
    if 0 in 缓冲:#含 NUL 则拒绝
        raise fs.文件系统错误(f'cannot edit "{展示路径}": binary file','FS_NOT_TEXT')#拒绝二进制
    原始=解码utf8(缓冲,'edit',展示路径)#fatal 解码
    样=原始[:4096]#只看前 4096 字符
    crlf次数=样.count('\r\n')#CRLF 出现次数
    lf次数=样.count('\n')-crlf次数#单独 LF 次数（CRLF 里的 LF 已扣掉）
    行尾='CRLF' if crlf次数>lf次数 else 'LF'#多数为 CRLF 才报 CRLF
    return {'content':规范行尾(原始),'lineEndings':行尾}#LF 内容加检测到的行尾

def 为diff读文本(绝对路径,最大字节,信号=None):#尽力读取覆盖 diff 基准
    """尽力而为的覆盖 diff 基准。二进制、非法 UTF-8、达到或超过字节上限、或不可读时返回 None。"""
    若已中止则抛(信号,'read')#开始前检查中止
    描述符=None#只读打开的描述符
    try:#打开描述符读取
        打开标志=os.O_RDONLY#只读
        if os.name=='nt':#Windows 需要二进制标志
            打开标志|=os.O_BINARY#二进制模式
        描述符=os.open(绝对路径,打开标志)#只读打开
        try:#在已打开描述符上 stat 并读
            若已中止则抛(信号,'read')#stat 前检查中止
            信息=os.fstat(描述符)#描述符上的 stat，不是路径 stat
            若已中止则抛(信号,'read')#stat 后再查中止
            if not 是普通文件模式(信息.st_mode):#非普通文件则放弃基准
                return None#放弃
            if 信息.st_size>=最大字节:#达到/超过上限则放弃
                return None#放弃
            打开大小=信息.st_size#记下打开时大小
            缓冲=bytearray(打开大小+1)#按打开大小加一分配
            合计=0#已读字节
            while 合计<len(缓冲):#直到填满或 EOF
                若已中止则抛(信号,'read')#每块前检查中止
                长度=min(len(缓冲)-合计,diff基准读取块字节)#本块可读长度
                已读=os.read(描述符,长度)#从当前偏移读
                if len(已读)==0:#读到 EOF
                    break#结束
                缓冲[合计:合计+len(已读)]=已读#写入缓冲
                合计+=len(已读)#累加已读
        finally:#无论成败都关句柄
            os.close(描述符)#释放描述符
            描述符=None#已关闭
        若已中止则抛(信号,'read')#关闭后再查中止
        if 合计!=打开大小:#大小变了（增长或截断）则放弃基准
            return None#放弃
        基准=bytes(缓冲[:合计])#实际读到的字节
        if 0 in 基准:#含 NUL 则放弃
            return None#放弃
        try:#fatal 解码再 LF 规范化
            return 规范行尾(基准.decode('utf-8'))#非法 UTF-8 抛 UnicodeDecodeError
        except UnicodeDecodeError:#非法 UTF-8
            return None#放弃基准
        except TypeError:#非解码类故障
            raise#原样抛出
    except fs.文件系统错误:#已结构化的中止/错误上抛
        raise#上抛
    except Exception as 错误:#打开或描述符阶段失败
        if isinstance(错误,OSError) or getattr(错误,'code',None) is not None:#有 errno 则放弃基准
            return None#丢掉可选基准
        raise#其余未知失败仍上抛

def 应用字面量编辑(内容,旧串,新串,全部替换,展示路径):#对 LF 文本做字面量替换
    """对 LF 规范化内容做字面量替换。空查找抛 `FS_EDIT_NOT_FOUND`；多处匹配抛 `FS_AMBIGUOUS_EDIT`，除非全部替换为真。"""
    旧规范=规范行尾(旧串)#查找侧也收成 LF
    if len(旧规范)==0:#空查找
        raise fs.文件系统错误('old_string must be a non-empty string','FS_EDIT_NOT_FOUND')#空串视为未找到
    新规范=规范行尾(新串)#替换侧同样收成 LF
    次数=0#已找到次数
    下标=0#下一轮搜索起点
    while True:#直到找不到下一处
        找到=内容.find(旧规范,下标)#从下标起找下一处
        if 找到==-1:#没有更多命中
            break#结束
        次数+=1#计入一处
        下标=找到+len(旧规范)#从本处之后继续
    if 次数==0:#一处都没有
        raise fs.文件系统错误(f'old_string was not found in "{展示路径}"','FS_EDIT_NOT_FOUND')#未找到
    if not 全部替换 and 次数>1:#默认要求恰好一处
        raise fs.文件系统错误(f'old_string matched {次数} times in "{展示路径}"; provide a more specific old_string or set replace_all to true','FS_AMBIGUOUS_EDIT')#不唯一
    return {'content':新规范.join(内容.split(旧规范)),'replacements':次数}#按字面量全部或唯一处替换
