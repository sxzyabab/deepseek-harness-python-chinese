"""本地文件系统技能提供方。

本包是 ctx.skills 提供方注册表的一种实现。它从项目、自定义与用户根
发现目录包和扁平 Markdown 技能，解析 YAML frontmatter，并在存在文件系统服务时
经 ctx.fs 加载正文。对应上游 @deepseek-ai/dsh-skill-filesystem。
"""
import os,stat,threading,time#路径、文件状态、监视线程与稳定计时
from concurrent.futures import Future as _原生Future#单次操作结果
from ...依赖 import cordis#外部依赖胶水
from ...依赖.schemastery import 字符串字段,布尔字段,列表字段,数字字段#配置字段
from .发现 import (
    项目dsh排名,#项目 .dsh/skills 排名
    项目agents排名,#项目 .agents/skills 排名
    自定义排名,#自定义根排名
    用户dsh排名,#用户 .dsh/skills 排名
    用户agents排名,#用户 .agents/skills 排名
    捆绑技能排名,#捆绑技能排名
    解析dsh家目录,#解析 dsh 家目录
    规范化监视路径,#监视路径规范化
    发现根,#扫描一个技能根
    解析技能文件,#读并解析技能文件
    可选文件系统,#上下文上可选的 fs 服务
    查找项目根,#向上找含 .git 的目录
    断言正整数,#配置正整数断言
    变更工具名,#第一方变更工具名
    错误消息,#任意失败→消息
    是否缺失路径错误,#路径不存在或不是目录
    取字段,#从映射或对象读字段
    试取,#读取可选字段
    听中止,#登记一次性 abort 回调
    抛若中止,#已中止则抛出
    已中止,#信号是否已中止
    中止原因,#取出中止原因
)#发现层已有符号，禁止在此重写
__all__=[#仅中文公开名；Cordis 英文槽不入表
    '默认监视稳定阈值毫秒','默认监视轮询间隔毫秒','默认监视项目上限',
    '名称','注入','配置','解开','等待全部','应用','默认',
]#公开面结束

默认监视稳定阈值毫秒=200#写入稳定阈值默认毫秒
默认监视轮询间隔毫秒=100#轮询/稳定探测默认间隔
默认监视项目上限=128#同时监视的项目根上限
名称='skill-filesystem'#Cordis插件名
注入=['skills']#依赖 skills 服务
name=名称#Cordis插件名
inject=注入#Cordis依赖声明

配置模式={
    'providerName':字符串字段(默认值='filesystem'),#默认提供方名 filesystem
    'includeDefaultRoots':布尔字段(默认值=True),#默认包含项目/用户根
    'dshHome':字符串字段(),#dsh 家目录
    'agentsHome':字符串字段(),#agents 家目录
    'customSkillDirs':列表字段(字符串字段(),默认值=[]),#默认可选自定义根为空
    'watch':布尔字段(默认值=True),#默认开监视
    'watchUsePolling':布尔字段(默认值=False),#默认原生事件；对齐 TS chokidar.watch 的 usePolling，打开根监视器时真正切换后端
    'watchStabilityThresholdMs':数字字段(默认值=默认监视稳定阈值毫秒),#稳定阈值
    'watchPollIntervalMs':数字字段(默认值=默认监视轮询间隔毫秒),#探测间隔
    'watchMaxProjects':数字字段(默认值=默认监视项目上限),#项目上限
    'watchFollowSymlinks':布尔字段(默认值=True),#默认跟随符号链接
    'bundledSkillDir':字符串字段(),#捆绑根
}#配置模式，缺省在此显式给出
配置=配置模式#中文配置模式
Config=配置模式#Cordis配置模式

class 操作任务:#单次异步结果
    def __init__(自身):#构造未决任务
        自身._future=_原生Future()#底层 Future
    def 兑现(自身,值=None):#成功结算
        if not 自身._future.done():#尚未结算
            自身._future.set_result(值)#写入结果
        return 值#返回兑现值
    def 拒绝(自身,错误):#失败结算
        if not 自身._future.done():#尚未结算
            if isinstance(错误,BaseException):#已是异常
                自身._future.set_exception(错误)#原样拒绝
            else:#非异常
                自身._future.set_exception(Exception(错误))#包装拒绝
    def wait(自身,超时=None):#阻塞等待
        return 自身._future.result(timeout=超时)#取结果或抛错
    def 等待(自身,超时=None):#兼容外来调用
        return 自身.wait(超时)#转发

def _是否thenable(值):#判定可等待对象
    if 值 is None:#空不是
        return False#不是
    if callable(getattr(值,'wait',None)):#Future 风格
        return True#可等待
    return callable(getattr(值,'等待',None))#外来 thenable

def _等待(值):#统一阻塞到结算
    if callable(getattr(值,'wait',None)):#Future 风格
        return 值.wait()#等待
    return 值.等待()#外来 thenable

def 已兑现(值=None):#立刻兑现的操作任务
    任务=操作任务()#新任务
    任务.兑现(值)#立刻成功
    return 任务#已完成

def 解开(值):#可等待则等待否则原样
    """可等待则等待，否则原样返回。"""
    if _是否thenable(值):#可等待
        return _等待(值)#等待
    return 值#同步值

def 等待全部(任务们):#等全部任务
    """等全部承诺；先拒绝的错误在全部落定后上抛。"""
    错误=None#先拒绝的错误
    for 任务 in 任务们:#逐个结算
        try:#一路失败不打断其余
            解开(任务)#等待承诺或同步值
        except BaseException as 当前:#本路失败
            if 错误 is None:#只保留第一份
                错误=当前#记下
    if 错误 is not None:#有失败
        raise 错误#上抛第一份

def 摘中止(信号,回调):#去掉 abort 回调
    """去掉 abort 回调。"""
    if 信号 is None:#无信号
        return#不摘
    if hasattr(信号,'removeEventListener'):#Web API
        信号.removeEventListener('abort',回调)#摘掉
        return#已摘
    if hasattr(信号,'移除监听'):#中文 API
        信号.移除监听('abort',回调)#摘掉

class 中止信号:#可监听的取消通道
    """管理器生命周期取消通道。"""
    def __init__(自身,已中止旗=False):#创建一条取消通道
        """创建一条取消通道。"""
        自身.aborted=已中止旗#英文旗标
        自身.已中止=已中止旗#中文旗标
        自身.reason=None#英文原因
        自身.原因=None#中文原因
        自身._监听=[]#回调表
        自身._锁=threading.Lock()#并发锁
    def 触发(自身,原因=None):#标记中止并通知
        """标记中止并通知。"""
        with 自身._锁:#只触发一次
            if 自身.aborted:#已经中止
                return#忽略
            自身.aborted=True#英文旗标
            自身.已中止=True#中文旗标
            自身.reason=原因#英文原因
            自身.原因=原因#中文原因
            回调们=list(自身._监听)#拷贝
            自身._监听=[]#清空
        for 回调 in 回调们:#逐个通知
            回调()#通知
    def 加入监听(自身,事件名,回调,选项=None):#登记 abort 回调
        """登记 abort 回调。"""
        if 事件名!='abort':#只支持 abort
            return#忽略其它事件
        立刻=False#是否已中止
        一次=False#once
        if isinstance(选项,dict) and 选项.get('once'):#只听一次
            一次=True#once
        with 自身._锁:#回调表锁
            if 自身.aborted:#已经中止
                立刻=True#锁外调用
            else:#仍活着
                自身._监听.append((回调,一次))#登记
        if 立刻:#立刻通知
            回调()#通知
    def 移除监听(自身,事件名,回调):#去掉 abort 回调
        """去掉 abort 回调。"""
        if 事件名!='abort':#只支持 abort
            return#忽略
        with 自身._锁:#按引用删除
            自身._监听=[项 for 项 in 自身._监听 if 项[0] is not 回调]#按引用删除
    def addEventListener(自身,事件名,回调,选项=None):#Web API 别名
        """Web API 别名。"""
        自身.加入监听(事件名,回调,选项)#委托
    def removeEventListener(自身,事件名,回调,选项=None):#Web API 别名
        """Web API 别名。"""
        自身.移除监听(事件名,回调)#委托
    def throwIfAborted(自身):#已中止则抛出原因
        """已中止则抛出原因。"""
        自身.抛若中止()#委托
    def 抛若中止(自身):#已中止则抛出原因
        """已中止则抛出原因。"""
        if not 自身.aborted:#仍活着
            return#不抛
        原因=自身.reason#中止原因
        if isinstance(原因,BaseException):#已是异常
            raise 原因#原样抛
        错=Exception('aborted')#非异常则包装
        错.cause=原因#挂上原因
        raise 错#抛出

class 中止控制器:#发出中止的控制器
    """发出中止的控制器。"""
    def __init__(自身):#创建配套信号
        """创建配套信号。"""
        自身.信号=中止信号()#本控制器的信号
    def 中止(自身,原因=None):#中止配套信号
        """中止配套信号。"""
        自身.信号.触发(原因)#触发一次

def 解析监视配置(配置):#解析并校验监视配置
    """解析并校验监视配置。"""
    稳定阈值毫秒=试取(配置,'watchStabilityThresholdMs')#稳定阈值
    if 稳定阈值毫秒 is None:#省略
        稳定阈值毫秒=默认监视稳定阈值毫秒#默认
    探测间隔毫秒=试取(配置,'watchPollIntervalMs')#探测间隔
    if 探测间隔毫秒 is None:#省略
        探测间隔毫秒=默认监视轮询间隔毫秒#默认
    项目上限=试取(配置,'watchMaxProjects')#项目上限
    if 项目上限 is None:#省略
        项目上限=默认监视项目上限#默认
    断言正整数('watchStabilityThresholdMs',稳定阈值毫秒)#正整数
    断言正整数('watchPollIntervalMs',探测间隔毫秒)#正整数
    断言正整数('watchMaxProjects',项目上限)#正整数
    开监视=试取(配置,'watch')#是否开监视
    if 开监视 is None:#省略
        开监视=True#默认开
    用轮询=试取(配置,'watchUsePolling')#是否轮询
    if 用轮询 is None:#省略
        用轮询=False#默认原生事件
    跟随=试取(配置,'watchFollowSymlinks')#是否跟随符号链接
    if 跟随 is None:#省略
        跟随=True#默认跟随
    return {'enabled':开监视,'usePolling':用轮询,'stabilityThresholdMs':稳定阈值毫秒,'pollIntervalMs':探测间隔毫秒,'maxProjects':项目上限,'followSymlinks':跟随}#已解析配置

def 解析根监视模式(根,跟随符号链接):#根存在则 root，否则祖先
    """根存在则 root，否则祖先。"""
    候选=根#从目标根向上走
    while True:#直到找到存在的目录或文件系统根
        try:#stat 缺失则继续向上
            信息=os.stat(候选)#跟随符号链接的 stat
            if stat.S_ISDIR(信息.st_mode):#找到目录
                保住根链接=候选==根 and (not 跟随符号链接) and stat.S_ISLNK(os.lstat(候选).st_mode)#根本身是符号链接且不跟随
                if 保住根链接:#监视符号链接节点
                    锚点=os.path.abspath(候选)#绝对化，不 realpath
                else:#规范现存祖先
                    锚点=规范化监视路径(候选)#监视锚点
                if 候选==根:#根存在
                    return {'kind':'root','anchor':锚点}#根模式
                try:#祖先到根的相对段
                    相对=os.path.relpath(根,候选)#从祖先到根
                except ValueError:#不在同一盘
                    return {'kind':'root','anchor':锚点}#相对路径异常则当根
                第一段=相对.split(os.sep)[0] if 相对 not in ('','.') else ''#祖先到根的第一段
                if 第一段=='' or 第一段 is None:#相对路径异常则当根
                    return {'kind':'root','anchor':锚点}#当根
                return {'kind':'ancestor','anchor':锚点,'nextPath':os.path.join(锚点,第一段)}#监视下一路径出现
        except OSError as 错误:#stat 失败
            if not 是否缺失路径错误(错误):#非缺失则上抛
                raise 错误#原样抛
        父路径=os.path.dirname(候选)#上一层
        if 父路径==候选:#文件系统根
            return {'kind':'ancestor','anchor':候选,'nextPath':根}#监视原根出现
        候选=父路径#继续向上

def 同一监视模式(左,右):#两次探测是否同一模式
    """两次探测是否同一模式。"""
    if 取字段(左,'kind')!=取字段(右,'kind'):#种类不同
        return False#不同
    if 取字段(左,'anchor')!=取字段(右,'anchor'):#锚点不同
        return False#不同
    if 取字段(左,'kind')=='root':#根模式不比下一路径
        return True#相同
    return 取字段(右,'kind')=='ancestor' and 取字段(左,'nextPath')==取字段(右,'nextPath')#祖先则下一路径也相同

def 包含段(根,路径):#path 相对 root 的段，越界则 None
    """path 相对 root 的段，越界则 None。"""
    try:#不同盘会抛
        相对=os.path.relpath(路径,根)#相对路径
    except ValueError:#不在根下
        return None#越界
    if 相对=='' or 相对=='.':#就是根
        return []#空段
    if 相对=='..' or 相对.startswith('..'+os.sep) or os.path.isabs(相对):#不在根下
        return None#越界
    return 相对.split(os.sep)#段数组

def 是否相关监视事件(根,事件,路径):#事件是否可能改变技能目录
    """事件是否可能改变技能目录。"""
    段们=包含段(根['path'],路径)#相对段
    if 段们 is None:#不在根下
        return False#无关
    if len(段们)==0:#根自身
        return 事件=='addDir' or 事件=='unlinkDir'#只关心目录增删
    if 根.get('skipSystem')==True and 段们[0]=='.system':#跳过 .system
        return False#无关
    if len(段们)==1:#根下直接子项
        if 事件=='addDir' or 事件=='unlinkDir':#目录包增删
            return True#相关
        return 段们[0].endswith('.md')#扁平 md 文件
    return len(段们)==2 and 段们[1]=='SKILL.md' and 事件!='addDir' and 事件!='unlinkDir'#目录包内 SKILL.md

def 是否潜在技能路径(根,路径):#宿主变更路径是否可能是技能
    """宿主变更路径是否可能是技能。"""
    段们=包含段(根['path'],路径)#相对段
    if 段们 is None or len(段们)==0 or len(段们)>2:#不在技能布局内
        return False#不是
    if 根.get('skipSystem')==True and 段们[0]=='.system':#跳过 .system
        return False#不是
    if len(段们)==1:#扁平 md 或目录包文件
        return 段们[0].endswith('.md')#一层须是 md
    return 段们[1]=='SKILL.md'#两层须是 SKILL.md

def 等待监视器打开(打开):#等待打开并吞掉失败
    """等待打开并吞掉失败。"""
    if 打开 is None:#没有进行中的打开
        return#无事
    try:#打开可能已失败
        解开(打开)#等待结算
    except BaseException:#打开失败
        return#监视启动已记下底层失败；拆除只收容它

class 祖先路径监视器:#缺失根的下一路径轮询
    """对齐 Node watchFile：轮询下一路径出现，不拖住进程。"""
    def __init__(自身,路径,间隔毫秒,回调):#记下路径与回调
        """用路径、轮询间隔与变化回调构造监视器。"""
        自身.路径=路径#下一路径
        自身.间隔毫秒=间隔毫秒#轮询间隔
        自身.回调=回调#stat 变化回调
        自身._停止=threading.Event()#拆除旗标
        自身._线程=threading.Thread(target=自身._运行)#监视线程
        自身._线程.daemon=True#不拖住进程
        自身._线程.start()#启动
    def close(自身):#摘掉该监听
        """停止接事件并等待监视线程退出。"""
        自身._停止.set()#请求停止
        if 自身._线程.is_alive() and threading.current_thread() is not 自身._线程:#不能 join 自己
            自身._线程.join()#等到退出
    def 关闭(自身):#中文别名
        """中文别名。"""
        自身.close()#委托
    def _快照(自身):#当前存在性与身份
        """读取目标的存在性、mtime、大小与模式；缺席为 missing。"""
        try:#跟随链接
            信息=os.stat(自身.路径)#取状态
            return ('exists',信息.st_mtime_ns,信息.st_size,信息.st_mode)#存在快照
        except OSError:#缺席
            return ('missing',None,None,None)#缺席
    def _运行(自身):#监视循环
        """初扫不回调；之后 stat 变化则通知。"""
        上次=自身._快照()#初扫快照
        while not 自身._停止.is_set():#直到拆除
            间隔=max(float(自身.间隔毫秒),1.0)/1000.0#至少 1ms
            if 自身._停止.wait(间隔):#等到停止或超时
                break#已拆除
            现在=自身._快照()#当前快照
            if 现在==上次:#未变
                continue#继续轮询
            上次=现在#接受新快照
            自身.回调()#异步处理，不阻塞 fs 回调

def 建原生目录等待(路径):#按平台打开原生目录事件等待
    """打开对齐 chokidar 非轮询后端的目录事件等待；不支持的平台返回 None。"""
    系统=os.name#nt / posix
    if 系统=='nt':#Windows ReadDirectoryChangesW
        return _Windows目录等待(路径)#子树通知
    if 系统=='posix':#Linux inotify / 其它 posix 退回 None
        try:#仅 Linux 有 inotify
            return _Linux目录等待(路径)#根+一层子目录
        except (AttributeError,OSError,ImportError):#平台或权限不足
            return None#调用方改用轮询间隔等待
    return None#其它平台

class _Windows目录等待:#ReadDirectoryChangesW 子树等待
    """Windows 原生目录事件；bWatchSubtree 覆盖 depth 1 的 SKILL.md。"""
    def __init__(自身,路径):#打开目录句柄
        """打开可列目录句柄并准备重叠 I/O。"""
        import ctypes#Win32
        from ctypes import wintypes#Win32 类型
        自身._ctypes=ctypes#保留
        内核=ctypes.WinDLL('kernel32',use_last_error=True)#kernel32
        自身._内核=内核#API
        通用读=0x80000000#GENERIC_READ
        文件列目录=0x0001#FILE_LIST_DIRECTORY
        共享读=0x00000001#FILE_SHARE_READ
        共享写=0x00000002#FILE_SHARE_WRITE
        共享删=0x00000004#FILE_SHARE_DELETE
        打开已有=3#OPEN_EXISTING
        备份语义=0x02000000#FILE_FLAG_BACKUP_SEMANTICS
        重叠旗=0x40000000#FILE_FLAG_OVERLAPPED
        无效=wintypes.HANDLE(-1).value#INVALID_HANDLE_VALUE
        句柄=内核.CreateFileW(路径,文件列目录,共享读|共享写|共享删,None,打开已有,备份语义|重叠旗,None)#打开目录
        if 句柄==无效 or 句柄 is None:#打开失败
            raise OSError(ctypes.get_last_error(),'CreateFileW failed for watch root')#上抛
        自身._句柄=句柄#目录句柄
        自身._缓冲=ctypes.create_string_buffer(65536)#通知缓冲
        类重叠=type('OVERLAPPED',(ctypes.Structure,),{'_fields_':[('Internal',ctypes.c_ulonglong),('InternalHigh',ctypes.c_ulonglong),('Offset',wintypes.DWORD),('OffsetHigh',wintypes.DWORD),('hEvent',wintypes.HANDLE)]})#重叠结构
        自身._重叠=类重叠()#重叠 I/O
        自身._事件=内核.CreateEventW(None,True,False,None)#手动复位事件
        if not 自身._事件:#建事件失败
            内核.CloseHandle(句柄)#收句柄
            raise OSError(ctypes.get_last_error(),'CreateEventW failed')#上抛
        自身._重叠.hEvent=自身._事件#挂到重叠
        自身._掩码=0x00000001|0x00000002|0x00000004|0x00000008|0x00000010|0x00000040#名/目录/属性/大小/写入/创建
        自身._已关=False#拆除旗
    def 等待(自身,超时秒):#等到事件或超时
        """有变化返回 True，超时返回 False；拆除中返回 False。"""
        if 自身._已关:#已关
            return False#结束
        ctypes=自身._ctypes#ctypes
        内核=自身._内核#API
        字节数=ctypes.c_ulong(0)#写出长度
        内核.ResetEvent(自身._事件)#清事件
        成功=内核.ReadDirectoryChangesW(自身._句柄,自身._缓冲,len(自身._缓冲),True,自身._掩码,ctypes.byref(字节数),ctypes.byref(自身._重叠),None)#异步读
        if not 成功:#启动失败
            错=ctypes.get_last_error()#错误码
            if 错==997:#ERROR_IO_PENDING 正常
                pass#等事件
            else:#真失败
                raise OSError(错,'ReadDirectoryChangesW failed')#上抛
        等待毫秒=max(int(超时秒*1000),1)#至少 1ms
        结果=内核.WaitForSingleObject(自身._事件,等待毫秒)#等通知或超时
        if 结果==0:#WAIT_OBJECT_0
            内核.GetOverlappedResult(自身._句柄,ctypes.byref(自身._重叠),ctypes.byref(字节数),False)#收完成
            return True#有事件
        if 结果==0x00000102:#WAIT_TIMEOUT
            内核.CancelIoEx(自身._句柄,ctypes.byref(自身._重叠))#取消挂起读
            return False#超时
        return False#其它等待结果当无事件
    def 关闭(自身):#关掉句柄
        """取消挂起 I/O 并关闭句柄。"""
        if 自身._已关:#已关
            return#幂等
        自身._已关=True#标记
        内核=自身._内核#API
        try:#取消可能已无挂起
            内核.CancelIoEx(自身._句柄,None)#取消
        except Exception:#忽略
            pass#拆卸收容
        内核.CloseHandle(自身._句柄)#关目录
        内核.CloseHandle(自身._事件)#关事件

class _Linux目录等待:#inotify 根+一层子目录
    """Linux inotify：监视根与直接子目录，覆盖 depth 1 的 SKILL.md。"""
    def __init__(自身,路径):#初始化 inotify
        """打开 inotify 并监视根与现有子目录。"""
        import ctypes,select#libc 与 select
        自身._ctypes=ctypes#保留
        自身._select=select#保留
        自身._路径=路径#根路径
        try:#优先 libc.so.6
            libc=ctypes.CDLL('libc.so.6',use_errno=True)#glibc
        except OSError:#其它 libc 名
            libc=ctypes.CDLL(None,use_errno=True)#进程默认
        自身._libc=libc#API
        IN_CLOEXEC=0x80000#close-on-exec
        IN_NONBLOCK=0x800#非阻塞
        自身._掩码=0x00000100|0x00000200|0x00000002|0x00000040|0x00000080|0x00000004|0x00000400|0x00000800#CREATE/DELETE/MODIFY/MOVED_FROM/MOVED_TO/ATTRIB/DELETE_SELF/MOVE_SELF
        自身._fd=libc.inotify_init1(IN_CLOEXEC|IN_NONBLOCK)#实例
        if 自身._fd<0:#失败
            raise OSError(ctypes.get_errno(),'inotify_init1 failed')#上抛
        自身._表={}#wd→路径
        自身._已关=False#拆除旗
        自身._加监视(路径)#根
        自身._刷新子目录()#一层子目录
    def _加监视(自身,目标):#inotify_add_watch
        """为路径加监视；已存在则刷新掩码。"""
        if 自身._已关:#已关
            return#忽略
        wd=自身._libc.inotify_add_watch(自身._fd,os.fsencode(目标),自身._掩码)#加监视
        if wd<0:#失败则跳过该路径
            return#子项可能竞态消失
        自身._表[wd]=目标#记下
    def _刷新子目录(自身):#对齐 depth 1 子目录监视
        """根下现有子目录都挂上 inotify。"""
        try:#根可能消失
            for 名 in os.listdir(自身._路径):#直接子项
                子=os.path.join(自身._路径,名)#子路径
                try:#只监视目录
                    if os.path.isdir(子):#目录包
                        自身._加监视(子)#挂上
                except OSError:#竞态
                    continue#跳过
        except OSError:#根没了
            return#等下次
    def 等待(自身,超时秒):#select 等到事件或超时
        """有变化返回 True，超时返回 False。"""
        if 自身._已关:#已关
            return False#结束
        可读,_,_=自身._select.select([自身._fd],[],[],max(超时秒,0.001))#等可读
        if not 可读:#超时
            return False#无事件
        try:#排空事件队列
            while True:#非阻塞读光
                块=os.read(自身._fd,4096)#读一批
                if not 块:#无更多
                    break#离开
        except BlockingIOError:#已空
            pass#正常
        except OSError:#fd 已关
            return False#当无事件
        自身._刷新子目录()#新建子目录补监视
        return True#有事件
    def 关闭(自身):#关 inotify
        """关闭 inotify fd。"""
        if 自身._已关:#已关
            return#幂等
        自身._已关=True#标记
        try:#关 fd
            os.close(自身._fd)#关闭
        except OSError:#已关
            pass#收容

class 根目录监视器:#已存在根的目录监视（原生或轮询）
    """对齐 chokidar：忽略初扫、写入稳定窗口、depth 1；usePolling 切换原生事件与轮询。"""
    def __init__(自身,路径,稳定毫秒,轮询毫秒,跟随符号链接,用轮询=False):#记下窗口与后端
        """记下监视路径、落定期窗口与是否强制轮询。"""
        自身.路径=路径#监视锚点
        自身.稳定毫秒=稳定毫秒#落定期
        自身.轮询毫秒=轮询毫秒#轮询/稳定探测间隔
        自身.跟随符号链接=跟随符号链接#是否跟随符号链接
        自身.用轮询=用轮询#True→轮询；False→原生（不可用则等待时退回间隔）
        自身.options={'usePolling':用轮询,'interval':轮询毫秒,'awaitWriteFinish':{'stabilityThreshold':稳定毫秒,'pollInterval':轮询毫秒},'followSymlinks':跟随符号链接,'depth':1,'ignoreInitial':True}#对齐 chokidar.watch 选项，供检视
        自身.监听={'ready':[],'error':[],'add':[],'addDir':[],'change':[],'unlink':[],'unlinkDir':[]}#事件表
        自身.停止=threading.Event()#拆除旗标
        自身.线程=None#工作线程
        自身._原生=None#原生等待句柄
    def on(自身,事件,回调):#登记回调
        """登记一个监视事件回调。"""
        自身.监听[事件].append(回调)#挂上
        return 自身#链式
    def 启动(自身):#启动线程
        """启动监视线程。"""
        if not 自身.用轮询:#请求原生后端
            try:#打开失败则循环内用间隔等待
                自身._原生=建原生目录等待(自身.路径)#原生等待
            except Exception:#打开原生失败
                自身._原生=None#退回间隔等待，但仍记录 usePolling=False
        自身.线程=threading.Thread(target=自身.循环)#工作线程
        自身.线程.daemon=True#不挡住退出
        自身.线程.start()#启动
    def 关闭(自身):#停止监视
        """停止监视并等待线程退出。"""
        自身.停止.set()#拒绝新等待
        原生=自身._原生#原生句柄
        自身._原生=None#先摘
        if 原生 is not None:#有原生
            try:#关闭可能抛
                原生.关闭()#取消挂起等待
            except Exception:#收容
                pass#拆卸
        if 自身.线程 is not None and 自身.线程.is_alive() and threading.current_thread() is not 自身.线程:#不能 join 自己
            自身.线程.join()#排空线程
    def 发出(自身,事件,*位置参数):#扇出回调
        """同步调用该事件的全部回调。"""
        for 回调 in list(自身.监听.get(事件,[])):#快照回调
            回调(*位置参数)#逐个调用
    def _等下一拍(自身):#原生事件或轮询间隔
        """usePolling 时睡间隔；否则等原生目录事件（不可用则退回间隔）。"""
        间隔秒=max(自身.轮询毫秒,1)/1000.0#稳定/轮询节拍
        if 自身.用轮询 or 自身._原生 is None:#轮询后端或无原生
            自身.停止.wait(间隔秒)#按间隔等待
            return#结束
        try:#原生等待可被关闭打断
            自身._原生.等待(间隔秒)#有事件或超时都回到快照路径
        except Exception as 错误:#原生运行时失败
            自身.发出('error',错误)#监视错误
            自身.停止.wait(间隔秒)#避免紧自旋
    def 拍快照(自身):#depth 1 目录快照
        """根与直接子项以及子目录内文件的存在性签名；根缺失则为 None。"""
        锚点=自身.路径#监视锚点
        跟随=自身.跟随符号链接#是否跟随
        try:#根可能缺失
            根信息=os.stat(锚点) if 跟随 else os.lstat(锚点)#根状态
        except OSError as 错误:#stat 失败
            if 是否缺失路径错误(错误):#根不存在
                return None#缺失
            raise 错误#其它错误上抛
        if not stat.S_ISDIR(根信息.st_mode):#不是目录
            return None#当缺失
        结果={os.path.abspath(锚点):('directory',根信息.st_mtime_ns,根信息.st_size)}#根签名
        try:#列直接子项
            扫描=os.scandir(锚点)#带类型读取
        except OSError as 错误:#列目录失败
            if 是否缺失路径错误(错误):#根消失
                return None#缺失
            raise 错误#其它错误上抛
        for 条目 in 扫描:#逐条
            子路径=os.path.join(锚点,条目.name)#绝对路径
            绝对=os.path.abspath(子路径)#规范化
            try:#子项可能在扫描中消失
                信息=os.stat(子路径) if 跟随 else os.lstat(子路径)#子项状态
            except OSError as 错误:#stat 失败
                if 是否缺失路径错误(错误):#扫描竞态
                    continue#跳过
                raise 错误#其它错误上抛
            if stat.S_ISDIR(信息.st_mode):#目录包
                结果[绝对]=('directory',信息.st_mtime_ns,信息.st_size)#目录签名
                try:#depth 1 再看包内文件
                    内扫描=os.scandir(子路径)#列包内
                except OSError as 错误:#列失败
                    if 是否缺失路径错误(错误):#包消失
                        continue#跳过
                    raise 错误#其它错误上抛
                for 内条目 in 内扫描:#包内条目
                    内路径=os.path.join(子路径,内条目.name)#包内路径
                    内绝对=os.path.abspath(内路径)#规范化
                    try:#内项可能消失
                        内信息=os.stat(内路径) if 跟随 else os.lstat(内路径)#内项状态
                    except OSError as 错误:#stat 失败
                        if 是否缺失路径错误(错误):#扫描竞态
                            continue#跳过
                        raise 错误#其它错误上抛
                    if stat.S_ISDIR(内信息.st_mode):#不再往下走
                        continue#depth 止于包内文件
                    结果[内绝对]=('file',内信息.st_mtime_ns,内信息.st_size)#文件签名
            elif stat.S_ISREG(信息.st_mode):#扁平文件
                结果[绝对]=('file',信息.st_mtime_ns,信息.st_size)#文件签名
        return 结果#快照
    def 发出差异(自身,旧,新):#把两次快照收成 chokidar 事件
        """把两次快照收成 add/addDir/change/unlink/unlinkDir。"""
        if 旧 is None and 新 is None:#仍缺失
            return#无事件
        if 新 is None:#根没了
            自身.发出('unlinkDir',自身.路径)#根目录本身被删
            if 旧 is None:#没有旧子项
                return#结束
            根绝对=os.path.abspath(自身.路径)#根键
            for 路径 in 旧:#旧子项
                if 路径==根绝对:#根已发
                    continue#跳过
                if 旧[路径][0]=='directory':#目录
                    自身.发出('unlinkDir',路径)#目录删除
                else:#文件
                    自身.发出('unlink',路径)#文件删除
            return#结束
        if 旧 is None:#根刚出现
            旧={}#从空比
        旧键=set(旧.keys())#旧路径
        新键=set(新.keys())#新路径
        for 路径 in 旧键-新键:#删除
            if 旧[路径][0]=='directory':#目录
                自身.发出('unlinkDir',路径)#目录删除
            else:#文件
                自身.发出('unlink',路径)#文件删除
        for 路径 in 新键-旧键:#新增
            if 新[路径][0]=='directory':#目录
                自身.发出('addDir',路径)#目录新增
            else:#文件
                自身.发出('add',路径)#文件新增
        for 路径 in 旧键&新键:#仍在
            if 旧[路径]!=新[路径]:#签名变了
                自身.发出('change',路径)#变更
    def 循环(自身):#监视主循环
        """忽略初始签名，就绪后把落定的外部改动发成类型化事件。"""
        try:#整段循环
            已发布=自身.拍快照()#初始签名不发事件
            观察中=已发布#当前观察
            待定时刻=0#落定计时
            有待定=False#是否等待落定
            自身.发出('ready')#监视就绪
            while not 自身.停止.is_set():#直到拆除
                自身._等下一拍()#原生或轮询
                if 自身.停止.is_set():#已拆除
                    return#已拆除
                try:#再读快照
                    现在=自身.拍快照()#再读快照
                except Exception as 错误:#读失败
                    自身.发出('error',错误)#监视错误
                    continue#保持活着
                此刻=time.time()*1000.0#毫秒
                if 现在!=观察中:#有改动
                    观察中=现在#新观察
                    待定时刻=此刻#重置落定
                    有待定=True#等待落定
                if 有待定 and 现在==观察中 and (此刻-待定时刻)>=自身.稳定毫秒:#已落定
                    有待定=False#已落定
                    if 现在!=已发布:#尚未发出
                        旧=已发布#上一份
                        已发布=现在#记下已发
                        自身.发出差异(旧,现在)#类型化事件
        except Exception as 错误:#循环失败
            自身.发出('error',错误)#循环失败

class 技能监视管理器:#技能根监视管理器
    """拥有有界宿主监视器，发现与读取仍走文件系统服务。"""
    def __init__(自身,上下文,失效,配置):#注入失效回调与已解析配置
        """注入失效回调与已解析配置。"""
        自身.ctx=上下文#记监视失败
        自身.invalidate=失效#通知注册表
        自身.config=配置#监视配置
        自身.根={}#路径→状态
        自身.项目={}#项目根→其技能路径
        自身.生命周期=中止控制器()#管理器生命周期
        自身.closing=False#拆除中
        自身.invalidationQueued=False#微任务失效是否已排队
        自身.锁=threading.Lock()#状态锁
    def 观察根(自身,根们):#按当前发现根保留监视
        """按当前发现根保留监视。"""
        任务=操作任务()#本次观察
        def 跑():#工作线程
            """分类共享根与项目根并保留/释放。"""
            try:#观察失败上抛
                自身._观察根体(根们)#体
                任务.兑现()#成功
            except BaseException as 错误:#失败
                任务.拒绝(错误)#拒绝
        工作=threading.Thread(target=跑)#工作线程
        工作.daemon=True#不挡住退出
        工作.start()#启动
        return 任务#承诺
    def _观察根体(自身,根们):#观察体
        """分类共享根与项目根并保留/释放。"""
        if 自身.closing:#拆除中不再打开
            return#结束
        项目根表={}#按项目根分组
        待定=[]#保留/释放承诺
        for 根 in 根们:#分类共享根与项目根
            if 试取(根,'projectRoot') is None:#非项目根
                待定.append(自身.保留根(根,'shared:'+根['path']))#共享所有权
                continue#下一根
            分组=项目根表.get(根['projectRoot'])#该项目已有组
            if 分组 is None:#首次
                分组=[]#空组
                项目根表[根['projectRoot']]=分组#写入
            分组.append(根)#收入
        for 项目根 in 项目根表:#每个项目一组
            分组=项目根表[项目根]#该组
            所有者='project:'+项目根#项目所有者键
            with 自身.锁:#先摘再插以刷新插入序
                if 项目根 in 自身.项目:#已有
                    del 自身.项目[项目根]#先摘
                自身.项目[项目根]=set(根['path'] for 根 in 分组)#记为最新
            for 根 in 分组:#保留各根
                待定.append(自身.保留根(根,所有者))#保留
        逐出项目=False#是否因上限逐出项目
        while True:#超出项目上限
            with 自身.锁:#读项目表
                超了=len(自身.项目)>自身.config['maxProjects']#是否超上限
                if not 超了:#未超
                    break#离开
                try:#插入序最旧
                    最旧=next(iter(自身.项目.items()))#最旧项目
                except StopIteration:#无条目
                    break#防御：无条目
                项目根,路径们=最旧#最旧项目
                del 自身.项目[项目根]#从表移除
            所有者='project:'+项目根#对应所有者
            for 路径 in 路径们:#释放其根
                待定.append(自身.释放根(路径,所有者))#释放
            逐出项目=True#需要失效，因监视覆盖已变
        等待全部(待定)#等保留/释放完成
        if 逐出项目:#逐出后通知目录可能过期
            自身.invalidate()#通知注册表
    def 观察宿主变更(自身,路径):#第一方写/编辑路径
        """第一方写/编辑路径。"""
        if 自身.closing:#拆除中忽略
            return#忽略
        规范化=os.path.abspath(路径)#绝对化
        with 自身.锁:#读根表
            状态们=list(自身.根.values())#快照状态
        for 状态 in 状态们:#任一技能根下
            if 是否潜在技能路径(状态['root'],规范化):#可能是技能
                自身.invalidate()#同步失效
                return#结束
    def 拆除(自身):#关闭全部监视
        """关闭每一个宿主监视器并收容迟到的文件系统回调。"""
        任务=操作任务()#拆除任务
        def 跑():#工作线程
            """关闭全部监视。"""
            try:#拆除失败上抛
                自身._拆除体()#体
                任务.兑现()#成功
            except BaseException as 错误:#失败
                任务.拒绝(错误)#拒绝
        工作=threading.Thread(target=跑)#工作线程
        工作.daemon=True#不挡住退出
        工作.start()#启动
        return 任务#共享承诺由提供方记忆化
    def _拆除体(自身):#拆除体
        """关闭全部监视。"""
        自身.closing=True#拒绝新打开
        自身.生命周期.中止(Exception('skill-filesystem watcher disposed'))#中止打开中的 ready
        with 自身.锁:#快照状态
            状态们=list(自身.根.values())#快照状态
            自身.根.clear()#先清空表
            自身.项目.clear()#清项目表
        关闭们=[]#关闭承诺
        for 状态 in 状态们:#逐个关闭
            等待监视器打开(状态.get('opening'))#等打开结束
            监视器=状态.get('watcher')#当前句柄
            状态['watcher']=None#摘掉
            if 监视器 is not None:#有句柄
                关闭们.append(自身.关闭监视器(监视器))#关闭
        等待全部(关闭们)#等全部关闭
    def 保留根(自身,根,所有者):#增加一个所有者
        """增加一个所有者。"""
        任务=操作任务()#本次保留
        def 跑():#工作线程
            """增加所有者并确保句柄。"""
            try:#保留失败上抛
                with 自身.锁:#取或建状态
                    状态=自身.根.get(根['path'])#已有状态
                    if 状态 is None:#首次见到此根
                        状态={'root':根,'owners':set(),'watcher':None,'opening':None,'unhealthy':True}#新建不健康，待打开
                        自身.根[根['path']]=状态#放入表
                    状态['owners'].add(所有者)#记下所有者
                if 自身.config['enabled']:#配置开监视则确保句柄
                    解开(自身.确保监视器(状态))#确保
                任务.兑现()#成功
            except BaseException as 错误:#失败
                任务.拒绝(错误)#拒绝
        工作=threading.Thread(target=跑)#工作线程
        工作.daemon=True#不挡住退出
        工作.start()#启动
        return 任务#承诺
    def 释放根(自身,路径,所有者):#去掉一个所有者
        """去掉一个所有者。"""
        任务=操作任务()#本次释放
        def 跑():#工作线程
            """去掉所有者，无人则关闭。"""
            try:#释放失败上抛
                with 自身.锁:#取状态
                    状态=自身.根.get(路径)#当前状态
                    if 状态 is None:#已不在表中
                        任务.兑现()#并发 cwd 观察可能在本次释放结算前逐出同一共享根
                        return#结束
                    状态['owners'].discard(所有者)#去掉此所有者
                    仍有=len(状态['owners'])>0#还有其他所有者
                    if not 仍有:#无人拥有则移除
                        自身.根.pop(路径,None)#移除
                if 状态 is not None and len(状态['owners'])==0:#无人拥有
                    等待监视器打开(状态.get('opening'))#等打开结束
                    监视器=状态.get('watcher')#当前句柄
                    状态['watcher']=None#摘掉
                    if 监视器 is not None:#有句柄
                        解开(自身.关闭监视器(监视器))#关闭
                任务.兑现()#成功
            except BaseException as 错误:#失败
                任务.拒绝(错误)#拒绝
        工作=threading.Thread(target=跑)#工作线程
        工作.daemon=True#不挡住退出
        工作.start()#启动
        return 任务#承诺
    def 确保监视器(自身,状态):#确保有健康监视
        """确保有健康监视。"""
        if 自身.closing or (not 自身.config['enabled']):#拆除或关闭监视
            return 已兑现()#立刻
        已有=状态.get('opening')#已有进行中的打开
        if 已有 is not None:#已有进行中的打开
            return 已有#交给调用方
        打开=操作任务()#启动打开
        状态['opening']=打开#记下进行中
        def 跑():#无论成败都清 opening
            """核对现有句柄或替换。"""
            try:#打开失败上抛
                自身.确保当前监视器(状态)#核对或替换
                打开.兑现()#成功
            except BaseException as 错误:#失败
                打开.拒绝(错误)#失败
            状态['opening']=None#清进行中
        工作=threading.Thread(target=跑)#工作线程
        工作.daemon=True#不挡住退出
        工作.start()#启动
        return 打开#交给调用方
    def 确保当前监视器(自身,状态):#核对现有句柄或替换
        """核对现有句柄或替换。"""
        监视器=状态.get('watcher')#当前句柄
        if 监视器 is not None and (not 状态.get('unhealthy')):#有健康句柄
            当前=解析根监视模式(状态['root']['path'],自身.config['followSymlinks'])#现探模式
            if (not 状态.get('unhealthy')) and 同一监视模式(监视器['mode'],当前):#模式未变则保留
                return#保留
        自身.替换监视器(状态)#关闭旧的并打开新的
    def 替换监视器(自身,状态):#替换监视句柄
        """替换监视句柄。"""
        旧句柄=状态.get('watcher')#旧句柄
        状态['watcher']=None#先摘掉
        if 旧句柄 is not None:#有旧的
            解开(自身.关闭监视器(旧句柄))#关闭旧的
        if 自身.closing or len(状态.get('owners') or [])==0:#拆除或已无所有者
            return#不打开
        try:#打开失败则标不健康
            监视器=自身.打开稳定监视器(状态)#打开与现模式一致的句柄
            if 监视器 is None:#拆除赢了
                return#不安装
            if 自身.closing or len(状态.get('owners') or [])==0:#打开后已被拆除
                解开(自身.关闭监视器(监视器))#关掉刚打开的
                return#不安装
            状态['watcher']=监视器#安装新句柄
            状态['unhealthy']=False#标健康
        except BaseException as 错误:#打开失败
            if not 自身.closing:#非拆除失败才记日志
                状态['unhealthy']=True#标不健康
                自身.ctx.logger.warn('skill-filesystem: failed to watch '+状态['root']['path']+': '+错误消息(错误))#记失败
            raise 错误#上抛给发现标不完整
    def 打开稳定监视器(自身,状态):#打开与现模式一致的句柄
        """打开与现模式一致的句柄。"""
        while (not 自身.closing) and len(状态.get('owners') or [])>0:#直到模式在两次探测间稳定
            模式=解析根监视模式(状态['root']['path'],自身.config['followSymlinks'])#第一次探测
            if 模式['kind']=='ancestor':#缺失根走祖先轮询
                监视器=自身.打开祖先监视器(状态,模式)#watchFile 下一路径
            else:#根已存在
                监视器=自身.打开根监视器(状态,模式)#目录监视根
            当前=解析根监视模式(状态['root']['path'],自身.config['followSymlinks'])#第二次探测
            if 同一监视模式(模式,当前):#模式稳定则交句柄
                return 监视器#交句柄
            解开(自身.关闭监视器(监视器))#模式变了，关掉重来
        return None#拆除赢了
    def 打开祖先监视器(自身,状态,模式):#监视缺失根的下一路径
        """监视缺失根的下一路径。"""
        def 监听():#stat 变化
            """祖先路径变化。"""
            自身.处理祖先监视事件(状态,模式)#异步处理
        监视器=祖先路径监视器(模式['nextPath'],自身.config['pollIntervalMs'],监听)#轮询下一路径出现
        def 关闭():#摘掉该监听
            """摘掉该监听。"""
            监视器.close()#只摘本 listener
        return {'mode':模式,'close':关闭}#句柄
    def 处理祖先监视事件(自身,状态,模式):#祖先路径变化
        """祖先路径变化。"""
        def 跑():#不阻塞 fs 回调
            """再探模式并按需重监视。"""
            try:#stat 失败可能是权限/IO
                当前=解析根监视模式(状态['root']['path'],自身.config['followSymlinks'])#再探
            except BaseException as 错误:#非缺失类失败
                if (not 自身.closing) and len(状态.get('owners') or [])>0:#仍有主
                    自身.处理监视错误(状态,错误)#记错误并重监视
                return#本次事件结束
            if 自身.closing or len(状态.get('owners') or [])==0 or 同一监视模式(模式,当前):#拆除、无主或模式未变
                return#结束
            自身.排队失效()#模式变了，目录可能变
            状态['unhealthy']=True#需要换句柄
            自身.调度重监视(状态)#调度重监视
        工作=threading.Thread(target=跑)#后台处理
        工作.daemon=True#不挡住退出
        工作.start()#启动
    def 打开根监视器(自身,状态,模式):#目录监视已存在的根
        """目录监视已存在的根；watchUsePolling 传入根监视器以切换原生/轮询后端。"""
        监视器=根目录监视器(模式['anchor'],自身.config['stabilityThresholdMs'],自身.config['pollIntervalMs'],自身.config['followSymlinks'],自身.config['usePolling'])#打开根监视；usePolling 对齐 chokidar
        def 关闭():#关掉目录监视
            """关掉目录监视。"""
            监视器.close()#关掉
        句柄={'mode':模式,'close':关闭,'options':监视器.options,'watcher':监视器}#包装 close，并暴露 chokidar 对齐选项
        已就绪=False#ready 之前的 error 拒绝 readiness
        就绪=操作任务()#等待 ready
        信号=自身.生命周期.signal#管理器生命周期
        if 已中止(信号):#已拆除
            解开(自身.关闭监视器(句柄))#关掉刚打开的
            抛若中止(信号)#抛拆除原因
        def 收到中止(*位置参数):#拆除则拒绝 ready
            """拆除则拒绝 ready。"""
            原因=中止原因(信号)#拆除原因
            就绪.拒绝(原因 if isinstance(原因,BaseException) else Exception(str(原因)))#拒绝
        听中止(信号,收到中止)#只听一次
        def 收到错误(错误):#监视 error
            """监视 error。"""
            if not 已就绪:#尚未 ready
                就绪.拒绝(错误)#打开失败
                return#不走运行时错误路径
            自身.处理监视错误(状态,错误)#运行时错误：记日志并重监视
        def 收到就绪(*位置参数):#首次就绪
            """首次就绪。"""
            nonlocal 已就绪#改外层
            已就绪=True#之后 error 走运行时路径
            就绪.兑现()#打开完成
        监视器.on('error',收到错误)#挂错误
        监视器.on('ready',收到就绪)#首次就绪
        for 事件 in ('add','addDir','change','unlink','unlinkDir'):#关心的事件
            def 绑定(事件名):#闭包钉住事件名
                """过滤后失效。"""
                def 收到(路径):#事件路径
                    """过滤后失效。"""
                    自身.处理监视事件(状态,模式,事件名,路径)#过滤后失效
                return 收到#该事件回调
            监视器.on(事件,绑定(事件))#挂事件
        监视器.启动()#开始监视（原生或轮询由 usePolling 决定）
        try:#等待 ready 或失败
            就绪.等待()#打开完成
        except BaseException as 错误:#ready 前失败
            解开(自身.关闭监视器(句柄))#关掉
            raise 错误#上抛
        finally:#无论成败
            摘中止(信号,收到中止)#摘拆除监听
        return 句柄#健康句柄
    def 处理监视事件(自身,状态,模式,事件,路径):#根监视事件
        """根监视事件。"""
        目标=os.path.abspath(路径)#绝对化
        过滤根=dict(状态['root'])#拷贝根
        过滤根['path']=模式['anchor']#path 可能是监视锚点
        if 自身.closing or (not 是否相关监视事件(过滤根,事件,目标)):#拆除或与技能无关
            return#忽略
        自身.排队失效()#相关则排队失效
        if 目标==os.path.abspath(模式['anchor']) and 事件=='unlinkDir':#根目录本身被删
            状态['unhealthy']=True#需要改祖先模式
            自身.调度重监视(状态)#调度重监视
    def 处理监视错误(自身,状态,错误):#运行时监视错误
        """运行时监视错误。"""
        if 自身.closing:#拆除中忽略
            return#忽略
        自身.ctx.logger.warn('skill-filesystem: watcher for '+状态['root']['path']+' failed: '+错误消息(错误))#记失败
        状态['unhealthy']=True#需要重开
        自身.排队失效()#目录可能已过期
        自身.调度重监视(状态)#调度重监视
    def 调度重监视(自身,状态):#等当前打开结束后再确保句柄
        """等当前打开结束后再确保句柄。"""
        当前打开=状态.get('opening')#当前打开
        if 当前打开 is None:#没有进行中
            当前打开=已兑现()#立刻
        def 跑():#不阻塞事件回调
            """收容打开失败后再确保。"""
            等待监视器打开(当前打开)#收容打开失败
            try:#重开失败已有日志
                解开(自身.确保监视器(状态))#再确保
            except BaseException:#打开失败
                return#监视启动已记下这次重试失败；下一次不完整发现会再试
            自身.排队失效()#重开成功，目录可能已变
        工作=threading.Thread(target=跑)#后台重开
        工作.daemon=True#不挡住退出
        工作.start()#立即启动
    def 排队失效(自身):#合并到下一微任务
        """合并到下一微任务。"""
        if 自身.closing or 自身.invalidationQueued:#拆除中或已排队
            return#忽略
        自身.invalidationQueued=True#占位
        def 微任务():#同一轮事件合并
            """同一轮事件合并。"""
            自身.invalidationQueued=False#允许再排
            if 自身.closing:#拆除赢了
                return#忽略
            自身.invalidate()#通知注册表
        工作=threading.Thread(target=微任务)#微任务线程
        工作.daemon=True#不挡住退出
        工作.start()#启动
    def 关闭监视器(自身,监视器):#关闭句柄并收容错误
        """关闭句柄并收容错误。"""
        任务=操作任务()#关闭承诺
        def 跑():#关闭可能抛
            """关掉目录监视或 unwatchFile。"""
            try:#close 可能抛
                解开(监视器['close']())#关掉
                任务.兑现()#成功
            except BaseException as 错误:#关闭失败
                自身.ctx.logger.warn('skill-filesystem: failed to close watcher: '+错误消息(错误))#记失败
                任务.兑现()#收容后仍兑现
        工作=threading.Thread(target=跑)#关闭线程
        工作.daemon=True#不挡住退出
        工作.start()#启动
        return 任务#承诺

class 文件系统技能提供方:#本地文件系统提供方
    """把本地项目/用户技能根映射进 ctx.skills 的提供方。"""
    def __init__(自身,上下文,控制,配置=None):#解析配置并挂生命周期
        """解析配置并挂生命周期。"""
        if 配置 is None:#省略配置
            配置={}#空配置
        提供方名=试取(配置,'providerName')#提供方名
        if 提供方名 is None:#省略
            提供方名='filesystem'#默认 filesystem
        自身.name=提供方名#提供方名
        自身.名称=提供方名#中文别名
        包含默认根=试取(配置,'includeDefaultRoots')#是否扫默认根
        if 包含默认根 is None:#省略
            包含默认根=True#默认包含默认根
        自身.包含默认根=包含默认根#是否扫默认根
        自身.dsh家=解析dsh家目录(试取(配置,'dshHome'))#解析 dsh 家目录
        已配置agents=试取(配置,'agentsHome')#显式 agents 家目录
        if 已配置agents is not None:#显式配置优先
            自身.agents家=os.path.abspath(已配置agents)#绝对化
        elif 'DSH_AGENTS_HOME' in os.environ:#环境变量存在（空串也算）
            自身.agents家=os.path.abspath(os.environ.get('DSH_AGENTS_HOME'))#解析 agents 家目录
        else:#都没有
            自身.agents家=os.path.abspath(os.path.join(os.path.expanduser('~'),'.agents'))#默认 ~/.agents
        自定义=试取(配置,'customSkillDirs')#自定义根
        if 自定义 is None:#省略
            自定义=[]#空
        自身.自定义技能目录=[os.path.abspath(根) for 根 in 自定义]#自定义根绝对化
        自身.ctx=上下文#Cordis 上下文
        自身.监视管理器=技能监视管理器(上下文,取字段(控制,'invalidate'),解析监视配置(配置))#监视管理器
        def 收到拆除(*位置参数):#注册拆除时关闭监视
            """注册拆除时关闭监视。"""
            自身.拆除()#不阻塞 abort 回调
        听中止(取字段(控制,'signal'),收到拆除)#注册拆除时关闭监视
        捆绑=试取(配置,'bundledSkillDir')#显式捆绑根优先
        if 捆绑 is None:#未显式给出
            if 包含默认根:#仅默认根模式才读环境
                捆绑=os.environ.get('DSH_BUNDLED_SKILL_DIR')#环境捆绑根
            else:#隔离提供方必须只看见自己显式给出的根
                捆绑=None#不挂载
        if 捆绑 is None:#省略
            自身.捆绑技能目录=None#不挂载
        else:#有捆绑根
            自身.捆绑技能目录=os.path.abspath(捆绑)#绝对化
        自身.拆除承诺=None#共享拆除承诺
    def 列出(自身,选项):#列本地候选
        """为对 cwd 敏感的工作区发现本地技能摘要。监视器启动失败则把可读候选作为不完整观察返回。"""
        根们=自身.根列表(试取(选项,'cwd'))#解析本 cwd 的扫描根
        完整=True#监视失败则标不完整
        try:#监视启动失败不丢已发现候选
            解开(自身.监视管理器.观察根(根们))#按根保留监视
        except BaseException as 错误:#监视启动失败
            if 自身.拆除承诺 is not None:#拆除中则上抛
                raise 错误#上抛
            完整=False#否则标不完整，仍返回候选
        候选们=[]#发现结果
        for 根 in 根们:#逐根扫描
            for 技能 in 发现根(根,自身.ctx,自身.name):#根下技能
                候选们.append(技能)#收入候选
        if 完整:#完整则数组简写
            return 已兑现(候选们)#数组
        return 已兑现({'candidates':候选们,'complete':完整})#不完整观察
    def 获取(自身,候选,选项):#加载正文
        """从候选的文件定位器加载完整本地技能正文；文件已消失则 None。"""
        定位器=取字段(候选,'locator')#本提供方定位器
        解析结果=解析技能文件(取字段(定位器,'path'),自身.ctx,试取(选项,'signal'),取字段(候选,'source')=='bundled')#捆绑根走宿主直读
        if 解析结果 is None:#文件消失或非法
            return 已兑现(None)#没有
        定义={'name':解析结果['name'],'description':解析结果['description'],'invocation':解析结果['invocation'],'source':取字段(候选,'source'),'provider':自身.name,'resourceBase':{'kind':'directory','path':取字段(定位器,'directory')},'path':取字段(定位器,'path'),'content':解析结果['content']}#组装完整定义
        if 'whenToUse' in 解析结果:#可选何时使用
            定义['whenToUse']=解析结果['whenToUse']#何时使用
        if 'metadata' in 解析结果:#可选元数据
            定义['metadata']=解析结果['metadata']#元数据
        return 已兑现(定义)#完整定义
    def 观察宿主变更(自身,路径):#宿主变更失效
        """第一方文件系统变更后同步使本提供方失效。"""
        自身.监视管理器.观察宿主变更(路径)#交给监视管理器
    def 拆除(自身):#拆除监视
        """关闭每一个宿主监视器并收容迟到的文件系统回调。"""
        if 自身.拆除承诺 is None:#只启动一次拆除
            自身.拆除承诺=自身.监视管理器.拆除()#共享承诺
        return 自身.拆除承诺#共享承诺
    def 根列表(自身,工作目录):#解析本查找的扫描根
        """解析本查找的扫描根。"""
        根们=[]#按优先级排列
        if 自身.包含默认根 and 工作目录 is not None:#有 cwd 才扫项目根
            项目根=查找项目根(os.path.abspath(工作目录),可选文件系统(自身.ctx))#向上找 .git
            根们.append({'path':os.path.join(项目根,'.dsh','skills'),'source':'project-dsh','rank':项目dsh排名,'projectRoot':项目根})#项目 dsh
            根们.append({'path':os.path.join(项目根,'.agents','skills'),'source':'project-agents','rank':项目agents排名,'projectRoot':项目根})#项目 agents
        for 路径 in 自身.自定义技能目录:#自定义根
            根们.append({'path':路径,'source':'custom','rank':自定义排名})#自定义根
        if 自身.包含默认根:#用户两根
            根们.append({'path':os.path.join(自身.dsh家,'skills'),'source':'user-dsh','rank':用户dsh排名,'skipSystem':True})#用户 dsh，跳过 .system
            根们.append({'path':os.path.join(自身.agents家,'skills'),'source':'user-agents','rank':用户agents排名})#用户 agents
        if 自身.捆绑技能目录 is not None:#有捆绑根则追加
            根们.append({'path':自身.捆绑技能目录,'source':'bundled','rank':捆绑技能排名,'trustedHost':True})#捆绑根信任宿主
        return 根们#扫描根列表

def 应用(上下文,配置=None):#安装提供方与监视拆除
    """在 ctx.skills 上注册本地文件系统技能提供方。"""
    if 配置 is None:#省略配置
        配置={}#空配置
    提供方盒=[None]#effect 拆除时需要同一实例
    def 构造(控制):#同步工厂
        """构造提供方并交给注册表。"""
        提供方盒[0]=文件系统技能提供方(上下文,控制,配置)#构造提供方
        return 提供方盒[0]#交给注册表
    上下文.skills.登记提供方(构造)#挂到技能注册表
    def 监视副作用():#把监视器拆除接到光纤
        """把监视器拆除接到光纤。"""
        def 拆除监视():#异步关闭全部监视器
            """异步关闭全部监视器。"""
            return 提供方盒[0].拆除()#共享拆除
        return 拆除监视#释放器
    上下文.effect(监视副作用,'skill-filesystem watcher')#effect 标签
    def 收到观察(目标,_观察=None,行动者=None,*剩余):#第一方写/编辑后同步失效
        """只认 edit/write。"""
        if 变更工具名(行动者) is None:#只认 edit/write
            return#忽略
        提供方盒[0].观察宿主变更(取字段(目标,'displayPath'))#按展示路径失效
    上下文.on('fs/observed',收到观察)#结束 fs/observed

apply=应用#Cordis插件入口
default=应用#默认导出
默认=应用#中文默认导出
