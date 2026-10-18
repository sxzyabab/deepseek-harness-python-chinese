'已加载模块文件的磁盘身份，用来找出加载之后变过的模块'
import os#文件状态
import shutil#清掉时钟标记目录
import tempfile#时钟标记
import time#系统钟回退

时间分辨率毫秒=2000#FAT 修改时间以 2 秒为单位。上次观察前这一窗内改过的未记录文件当作可能变了

def 文件身份(地址):
    'inode、大小和修改时间。读不到则空'
    if not 地址.startswith('file:'):#只认文件地址
        路径=地址#已经是路径
    else:#file URL
        from urllib.parse import urlparse,unquote#拆文件地址
        路径=unquote(urlparse(地址).path)#本地路径
        if len(路径)>2 and 路径[0]=='/' and 路径[2]==':':#Windows 的 /C:
            路径=路径[1:]#去掉开头的斜杠
    try:#消失或不可读就不再是已加载模块
        状态=os.stat(路径)#状态
    except OSError:#没有这份文件
        return None#空
    return {'key':str(状态.st_ino)+':'+str(状态.st_size)+':'+str(状态.st_mtime_ns),'modifiedAt':状态.st_mtime*1000}#身份

class 模块文件:
    '记下已加载 file 模块的 inode、大小和修改时间。硬链接改变不记，因为内容没变'
    def __init__(自身):
        '记录表里的空值表示过期，例如上次观察之后才第一次加载的待定模块'
        自身.记录={}#地址到身份。空值是过期
        自身.观察时刻=time.time()*1000#上次观察的文件钟

    def 现在(自身):
        '用新建再删掉的标记文件读文件系统盖章用的钟。建不了就退回系统钟'
        try:#临时目录不可写
            目录=tempfile.mkdtemp(prefix='dsh-hmr-clock-')#标记目录
        except OSError:#建不了
            return time.time()*1000#系统钟
        try:#读完就删
            标记=os.path.join(目录,'now')#空文件
            with open(标记,'w',encoding='utf-8') as 文件:#创建
                文件.write('')#空
            return os.stat(标记).st_mtime*1000#文件修改时间
        finally:#无论成败都删目录
            shutil.rmtree(目录,ignore_errors=True)#清掉

    def 比较(自身,地址列表):
        '和磁盘比。返回过期地址，以及每个地址读到的身份'
        过期=set()#要重载的
        见到={}#这次读到的身份
        for 地址 in 地址列表:#逐个
            身份=文件身份(地址)#磁盘
            见到[地址]=None if 身份 is None else 身份['key']#记下
            if 身份 is None:#文件没了
                过期.add(地址)#过期
                continue#下一个
            if 地址 in 自身.记录:#有记录
                if 自身.记录[地址]!=身份['key']:#身份变了
                    过期.add(地址)#过期
            elif 身份['modifiedAt']>=自身.观察时刻-时间分辨率毫秒:#观察前这一窗内改过
                过期.add(地址)#第一次加载也可能是重装
        return {'stale':过期,'seen':见到}#结果

    def 观察(自身,地址列表,选项=None):
        '用给定已加载模块替换全部记录'
        if 选项 is None:#缺省
            选项={}#空
        见到=选项['seen'] if 'seen' in 选项 else {}#早先读过的
        保留=选项['retained'] if 'retained' in 选项 else set()#保持原记录
        时刻=选项['at'] if 'at' in 选项 else 自身.现在()#未记录模块用的观察时刻
        记录={}#新表
        for 地址 in 地址列表:#逐个
            if 地址 in 保留:#保持
                记录[地址]=自身.记录.get(地址)#原记录，没有就是过期
            elif 地址 in 见到:#用早先的身份
                记录[地址]=见到[地址]#不重读
            else:#现在读
                身份=文件身份(地址)#磁盘
                if 身份 is None or 身份['modifiedAt']>时刻:#观察之后才写的
                    记录[地址]=None#过期
                else:#观察前就在
                    记录[地址]=身份['key']#记下
        自身.记录=记录#替换
        自身.观察时刻=时刻#这次观察

    def 刷新(自身,地址列表):
        '只更新刚重新求值的模块，其它记录不动'
        for 地址 in 地址列表:#逐个
            身份=文件身份(地址)#现在的身份
            自身.记录[地址]=None if 身份 is None else 身份['key']#写回
