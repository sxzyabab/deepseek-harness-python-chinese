"""宿主原生操作系统集成共用的无 shell 文件执行运行器（原生目录选择器、用默认应用打开的交接）：utf8 标准输入输出捕获、中止传播、Windows 隐藏控制台。这是库而不是插件——无 ctx、无状态、无事件。"""
import os,subprocess,threading,errno#平台判定、无shell拉起、中止监视与系统错误码
__all__=['已中止','挂失败','运行原生命令','原生命令运行器','原生命令错误']#仅中文公开名

class 原生命令错误(Exception):#本包异常基类
    """宿主原生命令失败，附加码与捕获输出。"""
    def __init__(自身,消息,码,标准输出,标准错误,原因):#记下失败面
        """把退出/系统码与两路捕获输出挂到异常上。"""
        super().__init__(消息)#英文消息
        自身.code=码#退出码或系统码
        自身.stdout=标准输出#失败仍带标准输出
        自身.stderr=标准错误#失败仍带标准错误
        自身.cause=原因#cause为原始错误

def 已中止(信号):#读中止信号
    """信号按 threading.Event 定死。"""
    if 信号 is None:#无信号
        return False#未中止
    return 信号.is_set()#事件已置位

def 挂失败(消息,码,标准输出,标准错误,原因):#构造带code与捕获输出的失败
    """把退出/系统码与两路捕获输出挂到异常上，对齐上游 Object.assign(new Error(...), { code, stdout, stderr })。"""
    return 原生命令错误(消息,码,标准输出,标准错误,原因)#本包异常

def 运行原生命令(命令,参数列表,信号):#以utf8捕获、中止传播和Windows隐藏跑宿主命令
    """以 utf8 标准输入输出、中止传播和 Windows 隐藏方式运行宿主命令。

    命令是可执行路径或 PATH 名；参数列表是 argv（绝不是 shell 字符串）；信号是调用方/连接寿命，中止则终止子进程。
    退出码为 0 时返回捕获的 stdout/stderr（映射 `{'stdout','stderr'}`）。
    """
    if 已中止(信号):#拉起前信号已中止
        底层=原生命令错误('The operation was aborted','ABORT_ERR','','',None)#中止底层错误，字面量不翻译
        raise 挂失败(str(底层),'ABORT_ERR','','',底层)#立刻拒绝，对齐Node AbortError
    参数表=list(参数列表)#复制参数向量交给子进程
    关键字={'stdout':subprocess.PIPE,'stderr':subprocess.PIPE,'shell':False,'text':True,'encoding':'utf-8'}#utf8捕获且不经shell
    if os.name=='nt':#Windows隐藏瞬时控制台
        关键字['creationflags']=subprocess.CREATE_NO_WINDOW#对应windowsHide:true
    try:#不经shell执行文件
        进程=subprocess.Popen([命令]+参数表,**关键字)#拉起宿主命令
    except FileNotFoundError as 错误:#可执行缺失
        raise 挂失败(str(错误),'ENOENT','','',错误)#与Node spawn ENOENT对齐
    except OSError as 错误:#其它启动失败
        if 错误.errno==errno.ENOENT:#系统层文件不存在
            码='ENOENT'#与Node码对齐
        else:#其它系统错误
            码=错误.errno#保留数值errno
        raise 挂失败(str(错误),码,'','',错误)#交给调用方
    因中止杀掉=threading.Event()#监视线程是否因中止杀了进程

    def 监视():#信号中止时终止仍在跑的子进程
        """轮询中止与进程结束：避免只阻塞在信号.等待上导致进程已退后监视线程僵死。"""
        while 进程.poll() is None:#子进程仍在跑
            if 已中止(信号):#调用方/连接已中止
                因中止杀掉.set()#标记因中止杀掉
                进程.kill()#对应signal终止子进程
                return#结束监视
            threading.Event().wait(0.01)#短暂让出，对齐轮询间隔

    监视线程=threading.Thread(target=监视,daemon=True)#后台监视中止
    监视线程.start()#开始监视
    标准输出,标准错误=进程.communicate()#阻塞收齐两路utf8输出
    if 标准输出 is None:#管道未给出文本
        标准输出=''#空标准输出
    if 标准错误 is None:#管道未给出文本
        标准错误=''#空标准错误
    if 进程.returncode==0:#退出码0
        return {'stdout':标准输出,'stderr':标准错误}#成功交回捕获输出
    if 因中止杀掉.is_set():#因调用方中止而终止
        底层=原生命令错误('The operation was aborted','ABORT_ERR',标准输出,标准错误,None)#中止底层错误，字面量不翻译
        raise 挂失败(str(底层),'ABORT_ERR',标准输出,标准错误,底层)#拒绝，仍带已捕获输出
    底层=原生命令错误('Command failed','FAILED',标准输出,标准错误,None)#非零退出，不夹带命令路径
    raise 挂失败(str(底层),进程.returncode,标准输出,标准错误,底层)#拒绝，code为数字退出码

原生命令运行器=运行原生命令#可注入命令边界的运行器（中文名）
