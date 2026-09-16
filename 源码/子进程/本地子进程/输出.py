"""有界输出尾与私有溢出文件，供进程提供方共用。"""
import atexit,os,tempfile#退出收尾、路径与临时目录
from threading import Lock as 互斥锁#推入与读取互斥
from secrets import token_hex#溢出文件名随机后缀

__all__=('准备受管进程绑定','输出收集器')#仅中文公开名

溢出计数=0#本进程溢出文件序号
默认溢出目录=None#惰性私有溢出目录
溢出锁=互斥锁()#保护溢出计数与默认目录

def 私有溢出目录():#0700溢出根
    """默认溢出位置：OS tmpdir 下按进程私有的目录，惰性创建。"""
    global 默认溢出目录#惰性目录
    with 溢出锁:#保护创建
        if 默认溢出目录 is None:#首次创建
            默认溢出目录=tempfile.mkdtemp(prefix='dsh-subprocess-')#私有目录
            try:#尽量收紧权限
                os.chmod(默认溢出目录,0o700)#仅属主
            except OSError:#Windows等可能无chmod语义；目录仍在
                pass#保留已创建目录
        return 默认溢出目录#之后复用

def 退出时摘空溢出目录():#无完成溢出自文件时删除目录
    """进程退出时：目录从未溢出则删除；有完成溢出文件则保留。"""
    if 默认溢出目录 is None:#从未创建
        return#空操作
    try:#尽力删空目录
        os.rmdir(默认溢出目录)#非空则失败
    except OSError:#ENOENT/ENOTEMPTY/EBUSY/EPERM 不得改退出码
        pass#容忍

atexit.register(退出时摘空溢出目录)#可观察退出时跑

def 准备受管进程绑定(内部=None):#启动前准备溢出根
    """在启动受管原生进程前准备可失败的输出存储。"""
    if 内部 is None:#缺省
        内部={}#空
    if 'spillDir' in 内部 and 内部['spillDir'] is not None:#调用方目录
        return {'spillDir':内部['spillDir']}#已就绪
    return {'spillDir':私有溢出目录()}#默认私有目录

class 输出收集器:#一路流的有界尾+可选溢出
    """用有界内存尾收集一路流；有溢出上限时第一次溢出就创建溢出文件。"""
    def __init__(自身,最大字节,最大溢出字节,标签,溢出目录):#按是否配置溢出关掉溢出
        """构造有界收集器。"""
        自身.块列表=[]#当前内存尾块
        自身.字节=0#当前尾合计字节
        自身.已丢=False#是否丢过更早字节
        自身.溢出fd=None#溢出文件描述符
        自身.溢出文件=None#溢出路径；不可靠时清掉
        自身.溢出已关=最大溢出字节 is None#未配置spill则永不写文件
        自身.总量=0#整路流总字节
        自身.最大字节=最大字节#内存尾上限
        自身.最大溢出字节=最大溢出字节#完整文件上限
        自身.标签=标签#stdout/stderr，写入文件名
        自身.溢出目录=溢出目录#溢出目录
        自身.锁=互斥锁()#推入与读取互斥

    def 推入(自身,块):#吞下一块流数据
        """吞下一块流数据，计入整路流总量并维护内存尾/溢出。"""
        if isinstance(块,str):#文本则按utf-8
            块=块.encode('utf-8')#转字节
        elif not isinstance(块,bytes):#其它缓冲
            块=bytes(块)#收成bytes
        with 自身.锁:#互斥
            自身.总量+=len(块)#累计总量
            会撑破=自身.字节+len(块)>自身.最大字节#本块是否会撑破内存尾
            if not 自身.溢出已关 and (会撑破 or 自身.溢出fd is not None):#该写溢出则写
                自身.全部溢出(块)#写溢出
            自身.块列表.append(块)#先整块收下
            自身.字节+=len(块)#尾合计增加
            while 自身.字节>自身.最大字节:#超内存尾则丢头
                头=自身.块列表[0]#最旧一块
                超额=自身.字节-自身.最大字节#需要丢掉的字节
                if len(头)<=超额:#整块都在超额内
                    自身.块列表.pop(0)#丢掉整块
                    自身.字节-=len(头)#尾合计减少
                else:#只切掉块头
                    自身.块列表[0]=头[超额:]#保留块尾
                    自身.字节-=超额#刚好压到上限
                自身.已丢=True#记截断

    def 全部溢出(自身,块):#写溢出
        """惰性打开溢出文件并追加 chunk（以及此前各块，仅一次）。"""
        global 溢出计数#本进程序号
        if 自身.最大溢出字节 is not None and 自身.总量>自身.最大溢出字节:#整路流已超完整文件上限
            自身.作废溢出()#文件再也装不下完整流
            return#不再溢出
        if 自身.溢出fd is None:#第一次溢出
            with 溢出锁:#保护计数
                溢出计数+=1#递增
                序号=溢出计数#本文件序号
            自身.溢出文件=os.path.join(自身.溢出目录,'dsh-subprocess-'+str(os.getpid())+'-'+str(序号)+'-'+token_hex(6)+'-'+自身.标签+'.log')#私有文件名
            自身.溢出fd=os.open(自身.溢出文件,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)#O_EXCL创建，0600
            for 先前 in 自身.块列表:#先把已收块写进去
                os.write(自身.溢出fd,先前)#写出
        os.write(自身.溢出fd,块)#追加本块

    def 作废溢出(自身):#作废溢出
        """一旦文件再也装不下完整流，就停止溢出并删掉文件。"""
        fd=自身.溢出fd#当前描述符
        文件=自身.溢出文件#当前路径
        自身.溢出fd=None#先摘掉
        自身.溢出文件=None#不再广告
        自身.溢出已关=True#从此只留内存尾
        if fd is not None:#曾经打开过
            try:#尝试关掉
                os.close(fd)#关描述符
            except OSError:#关掉失败；留给finalize再试
                自身.溢出fd=fd#还给字段
        if 文件 is not None:#曾经有路径
            try:#尝试删除
                os.unlink(文件)#删文件
            except OSError:#unlink失败；最多留下maxSpillBytes
                pass#容忍

    def 自偏移读取(自身,起始字节):#从偏移读尾
        """按整路流字节坐标做增量读取：返回自起始字节起推入的全部内容。"""
        with 自身.锁:#互斥
            窗口起点=自身.总量-自身.字节#尾起点在总流中的偏移
            缓冲=b''.join(自身.块列表)#拼当前尾
            有损=起始字节<窗口起点#请求点已掉出内存尾
            切片=缓冲 if 有损 else 缓冲[起始字节-窗口起点:]#lossy则整段尾，否则从窗口内切
            结果={'text':切片.decode('utf-8','replace'),'nextOffset':自身.总量,'lossy':有损}#读取结果
            if 自身.溢出文件 is not None:#有完整溢出才广告路径
                结果['spillPath']=自身.溢出文件#带路径
            return 结果#结束返回

    def 快照(自身):#拷贝保留尾
        """拷贝保留的原始尾及其在完整观察流中的位置。"""
        with 自身.锁:#互斥
            return {'bytes':b''.join(自身.块列表),'totalBytes':自身.总量}#独立尾

    def 封上(自身):#关溢出
        """流结束后关掉溢出文件；失败的 close 停止广告溢出路径。"""
        with 自身.锁:#互斥
            if 自身.溢出fd is None:#没打开过或已关
                return#空操作
            try:#尝试关掉
                os.close(自身.溢出fd)#关描述符
            except OSError:#延迟回写失败；保住内存结果
                自身.溢出文件=None#不再带spillPath
            自身.溢出fd=None#无论成败都摘掉fd

    def 结算(自身):#结算快照
        """封上溢出文件并返回最终输出。"""
        自身.封上()#先关文件
        with 自身.锁:#互斥
            结果={'text':b''.join(自身.块列表).decode('utf-8','replace'),'truncated':自身.已丢}#最终输出
            if 自身.溢出文件 is not None:#完整溢出才带路径
                结果['spillPath']=自身.溢出文件#带路径
            return 结果#结束返回
