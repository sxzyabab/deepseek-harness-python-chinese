"""文件工具编辑前后的整文件捕获：首次变更前与轮次结束时各存一份，按字节 SHA-1 内容寻址。"""
import hashlib,os,stat#哈希、文件与类型位
__all__=['捕获文件','相同捕获','变更路径']#仅中文公开名

#常量
二进制探测字节=8000#git探测NUL的前缀字节数

class 捕获错误(Exception):#本模块异常
    """捕获读写失败。"""
    def __init__(自身,消息):#记下英文消息
        """用原样英文消息构造。"""
        super().__init__(消息)#英文消息

def 是否不存在错误(错误):#是否ENOENT
    """文件系统错误是否表示路径不存在。"""
    if isinstance(错误,FileNotFoundError):#Python专用
        return True#缺失
    return isinstance(错误,OSError) and 错误.errno==2#ENOENT

def 捕获文件(绝对路径,目录,最大字节):#读入并按哈希落盘
    """把路径当前内容存进内容寻址目录；最多读 maxBytes+1；非缺失且非普通文件返回 None。"""
    try:#打开只读
        句柄=open(绝对路径,'rb')#二进制读
    except OSError as 错误:#打开失败
        if not 是否不存在错误(错误):#非缺失
            raise 错误#上抛
        return {'kind':'absent'}#缺失侧
    try:#读内容
        信息=os.fstat(句柄.fileno())#元数据
        if not stat.S_ISREG(信息.st_mode):#非普通文件
            return None#忽略
        探针=bytearray(最大字节+1)#多读一字节判超限
        长度=0#已读
        while 长度<len(探针):#填满或EOF
            块=句柄.read(len(探针)-长度)#继续读
            if len(块)==0:#EOF
                break#停
            探针[长度:长度+len(块)]=块#写入
            长度+=len(块)#累加
        if 长度>最大字节:#超限
            return {'kind':'oversized'}#超限侧
        字节=bytes(探针[0:长度])#定长副本
    finally:#关闭
        句柄.close()#关
    文件=os.path.join(目录,hashlib.sha1(字节).hexdigest())#内容寻址名
    os.makedirs(目录,exist_ok=True)#确保目录
    try:#独占写入
        with open(文件,'xb') as 写出:#wx
            写出.write(字节)#写入
    except FileExistsError:#已有相同内容
        pass#共享副本
    二进制=0 in 字节[0:二进制探测字节]#前缀含NUL
    return {'kind':'file','file':文件,'binary':二进制}#已存侧

def 相同捕获(甲,乙):#两侧是否已知相同
    """两侧是否已知内容相同；超限侧永不匹配。"""
    if 甲['kind']=='absent' or 乙['kind']=='absent':#任一缺失
        return 甲['kind']==乙['kind']#同为缺失
    return 甲['kind']=='file' and 乙['kind']=='file' and 甲['file']==乙['file']#同哈希文件

def 文本路径(值):#非空白字符串
    """非空白字符串，否则 None。"""
    return 值 if isinstance(值,str) and 值.strip()!='' else None#有效路径

def 变更路径(名称,参数):#文件工具将改的路径
    """write/edit/变更型 str_replace_editor 将改的模型侧路径；其余返回 None。"""
    if not isinstance(参数,dict):#须对象
        return None#无法解析
    if 名称=='write':#写入工具
        if 'content' in 参数 and isinstance(参数['content'],str):#有内容字符串
            return 文本路径(参数['file_path'] if 'file_path' in 参数 else None)#路径
        return None#参数不全
    if 名称=='edit':#编辑工具
        if 'old_string' in 参数 and isinstance(参数['old_string'],str) and 'new_string' in 参数 and isinstance(参数['new_string'],str):#两边字符串
            return 文本路径(参数['file_path'] if 'file_path' in 参数 else None)#路径
        return None#参数不全
    if 名称=='str_replace_editor':#替换编辑器
        命令=参数['command'] if 'command' in 参数 else None#子命令
        if 命令=='create' or 命令=='str_replace' or 命令=='insert':#变更型
            return 文本路径(参数['path'] if 'path' in 参数 else None)#path字段
        return None#只读等
    return None#其他工具
