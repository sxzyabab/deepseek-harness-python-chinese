'有上限、可取消的固定操作系统元数据命令'
import subprocess,sys,time#子进程、平台与截止
from ...基础设施.通用工具 import 启动守护线程#两路输出同时读

__all__=['查询环境','信号已中止']#仅中文公开名

def 信号已中止(信号):
    'AbortSignal、网关中止信号或 threading.Event 是否已取消'
    if 信号 is None:#无信号
        return False#未取消
    if getattr(信号,'aborted',False):#浏览器取消标志
        return True#已取消
    内部事件=getattr(信号,'_事件',None)#网关中止信号的内部事件
    if 内部事件 is not None and 内部事件.is_set():#已置位
        return True#已取消
    置位=getattr(信号,'is_set',None)#threading.Event
    if callable(置位) and 置位():#已置位
        return True#已取消
    return False#仍活着

def 查询环境(命令,参数,选项):
    '不经 shell 执行固定参数。失败只留下原因，并等到子进程关闭'
    上限=选项['maxOutputBytes']#单路输出字节上限
    超时秒=选项['timeoutMillis']/1000#毫秒改秒
    信号=选项['signal']#拥有者寿命
    if 信号已中止(信号):#调用时已经取消
        return {'kind':'missing','reason':'query-failed'}#不创建子进程
    启动参数={'stdout':subprocess.PIPE,'stderr':subprocess.PIPE,'stdin':subprocess.DEVNULL}#两路分开收
    if sys.platform=='win32':#隐藏控制台
        启动参数['creationflags']=subprocess.CREATE_NO_WINDOW#不弹窗
    try:#同步拉起失败则没有子进程
        进程=subprocess.Popen([命令,*list(参数)],**启动参数)#固定 argv
    except Exception:#拉起失败
        return {'kind':'missing','reason':'query-failed'}#其他查询仍归调用方
    输出=bytearray()#标准输出
    错误输出=bytearray()#标准错误
    读失败=[]#读取本身失败
    def 读取(流,缓冲):
        '读到结束或超过上限。超过后不再继续读'
        try:#管道可能已关
            while True:#一块一块读
                块=流.read(65536)#一块
                if not 块:#结束
                    return#读完
                缓冲.extend(块)#拼上
                if len(缓冲)>上限:#这一路超了
                    return#停读
        except Exception as 读取错误:#管道错误
            读失败.append(读取错误)#留给主流程收成查询失败
    读出=启动守护线程(读取,进程.stdout,输出)#标准输出
    读错=启动守护线程(读取,进程.stderr,错误输出)#标准错误
    开始=time.monotonic()#从拉起开始算截止
    原因=None#尚未失败
    while 进程.poll() is None:#还在跑
        if len(输出)>上限 or len(错误输出)>上限:#任一路超限
            原因='output-limit'#超限优先
            break#去结束进程
        if 信号已中止(信号):#拥有者取消
            原因='query-failed'#取消不是超时
            break#去结束进程
        if time.monotonic()-开始>=超时秒:#到点
            原因='timeout'#超时
            break#去结束进程
        time.sleep(0.01)#让出，下一轮再看取消和截止
    if 原因 is not None:#需要杀掉才等得到关闭
        try:#可能刚好自己退出
            进程.kill()#强制结束
        except OSError as 杀死失败:#已经不在
            读失败.append(杀死失败)#进程已退出，下面仍等到关闭
    进程.wait()#等到关闭再返回
    读出.join()#标准输出读完
    读错.join()#标准错误读完
    if 原因 is None and (len(输出)>上限 or len(错误输出)>上限):#退出后才发现超限
        原因='output-limit'#不把截断内容当成功
    if 读失败 and 原因 is None:#读取失败
        原因='query-failed'#不带原文
    if 原因 is None and 进程.returncode!=0:#非零退出
        原因='query-failed'#丢掉输出和原始错误
    if 原因 is not None:#失败
        return {'kind':'missing','reason':原因}#只有原因
    return {'kind':'value','stdout':bytes(输出).decode('utf-8','replace')}#成功的标准输出
