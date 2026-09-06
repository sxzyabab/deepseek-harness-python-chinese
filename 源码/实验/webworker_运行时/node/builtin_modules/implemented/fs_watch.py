"""跨活动内存 VFS 的 Node 文件系统监视。

对齐上游 `webworker-runtime/src/node/builtin_modules/implemented/fs-watch.ts`。
文件名下划线：Python 无法 import 连字符模块名。
公开面中文名；Node 面经别名暴露英文名。
"""
import threading#中止等待
from .buffer import Buffer#本包Buffer
from .events import 事件发出器#导入事件发出器
from .async_hooks import 捕获异步上下文,在异步上下文运行#导入异步上下文
from .path import 基名,相对,解析,分隔符#导入路径工具
from ....storage.活动 import 要求活动vfs#导入活动VFS
from ...未实现失败 import 运行时错误#VFS 错误
from .abort_error import 中止错误,已中止,若已中止则抛出#导入中止原语

__all__=['文件系统监视器','统计监视器','监视','监视文件','取消监视文件','异步监视']#仅中文公开名；Node 面挂名不入表

def 归一路径(路径):#归一为绝对路径字符串
    """路径参数转绝对路径。"""
    if isinstance(路径,str): return 解析(路径)#字符串直接解析
    if type(路径).__name__=='URL' or hasattr(路径,'pathname'):#URL
        from urllib.parse import unquote#解码
        return 解析(unquote(路径.pathname))#URL取路径
    return 解析(bytes(路径).decode('utf-8') if isinstance(路径,(bytes,bytearray)) else str(路径))#字节解码

def _恒假():#Stats恒假谓词
    """缺失路径占位 Stats 上恒假的类型谓词。"""
    return False#否

def 缺失统计(bigint):#缺失路径的占位stats
    """缺失路径的占位 stats。"""
    零=0#大小零
    基={#公共字段
        'size':零,'ino':零,'mtimeMs':零,'ctimeMs':零,'atimeMs':零,'birthtimeMs':零,#数值
        'mtime':0,'mode':零,#时间与模式
        'isFile':_恒假,'isDirectory':_恒假,'isSymbolicLink':_恒假,#类型
        'isFIFO':_恒假,'isSocket':_恒假,'isBlockDevice':_恒假,#续
        'isCharacterDevice':_恒假,#字符设备
    }#基结束
    if bigint:#BigInt附加
        基.update({'dev':0,'nlink':0,'mtimeNs':0,'ctimeNs':0,'atimeNs':0,'birthtimeNs':0,'ctime':0,'atime':0,'birthtime':0})#附加
    return 基#交回

def 统计或缺失(路径,bigint):#stat或占位
    """stat 或 ENOENT 时占位。"""
    try:#尝试真实stat
        return 要求活动vfs().统计同步(路径,{'bigint':bigint})#同步stat
    except 运行时错误 as 错误:#捕获 VFS 错误
        if getattr(错误,'code',None)=='ENOENT': return 缺失统计(bigint)#缺失则占位
        raise#其它错误抛出

def 统计已变(左,右):#比较stats是否变化
    """比较 stats 是否变化。"""
    return (左['size']!=右['size'] or 左['mtimeMs']!=右['mtimeMs']#大小时间
        or 左['mode']!=右['mode'] or 左['ino']!=右['ino']#模式inode
        or 左['isFile']()!=右['isFile']() or 左['isDirectory']()!=右['isDirectory']())#类型

def 包含(父,子):#父路径是否包含子路径
    """父路径是否包含子路径。"""
    return 父=='/' or 子==父 or 子.startswith(f'{父}{分隔符}')#根或相等或前缀

def 重叠(左,右):#两路径是否重叠
    """两路径是否重叠。"""
    return 包含(左,右) or 包含(右,左)#双向

class 文件系统监视器(事件发出器):#文件系统监视器
    """跨 VFS 变更的 `fs.FSWatcher`。"""

    def __init__(自身,目标,目录,选项,监听器=None):#构造监视器
        """订阅 VFS 变更并可选注册监听器。"""
        super().__init__()#初始化事件发出器
        自身._目标=目标#监视目标路径
        自身._是目录=目录#目标是否目录
        自身._选项={} if 选项 is None else 选项#??空表，空字典合法
        自身._已关闭=False#是否已关闭
        自身._引用=自身._选项.get('persistent',True)#默认保持活性
        自身._上下文=捕获异步上下文()#捕获异步上下文
        if 监听器 is not None: 自身.监听('change',监听器)#注册监听器

        def 收变更(变更):#订阅VFS变更
            """匹配则微任务发射 change。"""
            if not 自身._匹配(变更): return#不匹配则忽略
            种类=变更['kind']#种类
            条目变=变更['entryChanged'] if 'entryChanged' in 变更 else None#条目变
            事件类型='change' if (种类=='write' and not 条目变) or 种类=='chmod' else 'rename'#判定事件类型
            路径=变更['path']#路径
            文件名=自身._文件名(路径)#派生文件名
            微任务=globals().get('queueMicrotask')#微任务
            def 发出变更():#微任务体
                """在上下文中发出。"""
                if 自身._已关闭:#已关闭
                    return#跳过
                def 发变更():#发出体
                    """发出 change。"""
                    自身.发出('change',事件类型,文件名)#发出
                在异步上下文运行(自身._上下文,发变更)#发出
            if callable(微任务):#有微任务
                微任务(发出变更)#排队
            else:#无
                发出变更()#同步

        自身._取消订阅=要求活动vfs().subscribe(收变更)#订阅VFS变更
        自身._信号=自身._选项['signal'] if 'signal' in 自身._选项 else None#保存信号
        if 已中止(自身._信号):#已中止
            自身.关闭()#立即关闭
            return#提前返回
        if 自身._信号 is not None:#有中止事件
            def 等待中止置位():#等到置位后关闭
                """阻塞到信号置位后关闭监视器。"""
                自身._信号.wait()#等中止
                if not 自身._已关闭:#仍开
                    自身.关闭()#关闭
            threading.Thread(target=等待中止置位,daemon=True).start()#盯梢

    def _匹配(自身,变更):#变更是否命中本监视器
        """变更是否命中本监视器。"""
        路径=变更['path']#路径
        种类=变更['kind']#种类
        if 路径==自身._目标: return True#路径完全匹配
        if 种类=='remove' and 包含(路径,自身._目标): return True#祖先被删
        if not 自身._是目录 or not 包含(自身._目标,路径): return False#非目录或不在树下
        if 自身._选项.get('recursive') is True: return True#递归则全树命中
        子=相对(自身._目标,路径)#相对路径
        return 子!='' and not 子.startswith('..') and 分隔符 not in 子#仅直接子项

    def _文件名(自身,路径):#从变更路径派生文件名
        """从变更路径派生文件名。"""
        相对路径=相对(自身._目标,路径)#相对目标的路径
        if 自身._是目录 and 包含(自身._目标,路径):#目录且在树内
            值=相对路径 if 自身._选项.get('recursive') is True else (相对路径.split(分隔符)[0] if 相对路径 else '')#递归用相对
        else: 值=基名(自身._目标)#文件监视用基名
        return Buffer.from(值) if 自身._选项.get('encoding')=='buffer' else 值#按编码返回

    def 关闭(自身):#关闭监视器
        """停止观察并发布一次 `close`。"""
        if 自身._已关闭: return#已关闭则跳过
        自身._已关闭=True#标记关闭
        自身._取消订阅()#取消订阅
        微任务=globals().get('queueMicrotask')#微任务
        def 发关闭():#发射 close
            """发射 close。"""
            自身.发出('close')#发射
        if callable(微任务):#有微任务
            微任务(发关闭)#排队
        else:#无
            自身.发出('close')#同步

    def 引用(自身):#标记保持活性
        """将本监视器标为承载进程活性。"""
        自身._引用=True#设为引用
        return 自身#链式返回

    def 取消引用(自身):#清除活性标志
        """清除进程活性标志。"""
        自身._引用=False#取消引用
        return 自身#链式返回

    def 有引用(自身):#读取活性标志
        """读取保留的进程活性标志。"""
        return 自身._引用#返回引用状态

    close=关闭#Node面
    ref=引用#Node面
    unref=取消引用#Node面
    hasRef=有引用#Node面

FSWatcher=文件系统监视器#Node面别名

def 监视(路径,选项或监听器=None,或许监听器=None):#导出watch
    """经活动 VFS 监视一条路径。"""
    if isinstance(选项或监听器,dict): 选项=选项或监听器#对象即选项
    elif isinstance(选项或监听器,str): 选项={'encoding':选项或监听器}#字符串为编码
    else: 选项={}#空
    监听器=选项或监听器 if callable(选项或监听器) else 或许监听器#解析监听器
    目标=归一路径(路径)#归一路径
    统计=要求活动vfs().统计同步(目标)#取目标stats
    是目录=统计['isDirectory']()#是否目录
    return 文件系统监视器(目标,是目录,选项,监听器)#构造并返回

def 定时器引用(定时器):#调用定时器ref
    """浏览器定时器为数值；Node 定时器暴露可选活性方法。"""
    ref=getattr(定时器,'ref',None) if not isinstance(定时器,(int,float)) else None#ref面
    if callable(ref): ref()#可选调用ref

def 定时器取消引用(定时器):#调用定时器unref
    """浏览器定时器为数值；Node 定时器暴露可选活性方法。"""
    unref=getattr(定时器,'unref',None) if not isinstance(定时器,(int,float)) else None#unref面
    if callable(unref): unref()#可选调用unref

_统计监视表={}#路径到共享stat监视器

class 统计监视器(事件发出器):#stat轮询监视器
    """`watchFile` 返回的 `fs.StatWatcher`。"""

    def __init__(自身,路径,选项):#构造stat监视器
        """订阅变更并可选立即调度。"""
        super().__init__()#初始化事件发出器
        自身.path=路径#路径
        表={} if 选项 is None else 选项#??空表，空字典合法
        自身._引用=True if 表.get('persistent') is None else 表['persistent']#??True，False 合法
        自身._间隔=5007 if 表.get('interval') is None else 表['interval']#??5007，interval=0 合法
        自身._bigint=False if 表.get('bigint') is None else 表['bigint']#??False
        自身._上次=统计或缺失(路径,自身._bigint)#初始stats
        自身._上下文=捕获异步上下文()#捕获上下文
        自身._定时器=None#轮询定时器
        自身._已停=False#是否已停止

        def 收变更(变更):#订阅变更
            """重叠则调度。"""
            路径值=变更['path'] if 'path' in 变更 else None#路径
            if 重叠(路径,路径值): 自身._调度()#重叠则调度

        自身._取消订阅=要求活动vfs().subscribe(收变更)#订阅结束
        if not 自身._上次['isFile']() and not 自身._上次['isDirectory'](): 自身._调度(True)#初始缺失

    def _调度(自身,初缺=False):#调度一次轮询
        """调度一次轮询。"""
        if 自身._已停 or 自身._定时器 is not None: return#已停或已有定时器
        全局=globals()#宿主

        def 到期():#超时体
            """比较并可能发出 change。"""
            自身._定时器=None#清除句柄
            if 自身._已停: return#已停则跳过
            当前=统计或缺失(自身.path,自身._bigint)#当前stats
            上次=自身._上次#上次快照
            自身._上次=当前#更新快照
            if 初缺 or 统计已变(当前,上次):#初缺或有变化
            def 发变更():#发出 change
                """在捕获上下文中发出。"""
                自身.发出('change',当前,上次)#发出
            在异步上下文运行(自身._上下文,发变更)#发出变更

        自身._定时器=全局['setTimeout'](到期,自身._间隔)#设置超时
        if not 自身._引用: 定时器取消引用(自身._定时器)#非引用则unref

    def 停止(自身):#停止监视
        """停止轮询并释放 VFS 订阅。"""
        if 自身._已停: return#已停则跳过
        自身._已停=True#标记停止
        自身._取消订阅()#取消订阅
        if 自身._定时器 is not None: globals()['clearTimeout'](自身._定时器)#清除定时器
        自身._定时器=None#清空句柄
        自身.发出('stop')#发出stop

    def 关闭(自身):#关闭别名
        """将监视器当作可关闭句柄的调用方所用的别名。"""
        自身.停止()#委托停止

    def 引用(自身):#标记保持活性
        """将本监视器标为承载进程活性。"""
        自身._引用=True#设为引用
        if 自身._定时器 is not None: 定时器引用(自身._定时器)#定时器ref
        return 自身#链式返回

    def 取消引用(自身):#清除活性标志
        """将本监视器标为不保持其所有者存活。"""
        自身._引用=False#取消引用
        if 自身._定时器 is not None: 定时器取消引用(自身._定时器)#定时器unref
        return 自身#链式返回

    def 有引用(自身):#读取活性标志
        """读取保留的进程活性标志。"""
        return 自身._引用#返回引用状态

    stop=停止#Node面
    close=关闭#Node面
    ref=引用#Node面
    unref=取消引用#Node面
    hasRef=有引用#Node面

StatWatcher=统计监视器#Node面别名

def 监视文件(路径,选项或监听器,或许监听器=None):#导出watchFile
    """为一条路径注册 stat 轮询监视器。"""
    选项={} if callable(选项或监听器) else 选项或监听器#解析选项
    监听器=选项或监听器 if callable(选项或监听器) else 或许监听器#解析监听器
    if 监听器 is None: raise TypeError('The "listener" argument must be of type function')#必须有监听器
    目标=归一路径(路径)#归一路径
    监视器=_统计监视表.get(目标)#查共享监视器
    if 监视器 is None:#尚无共享实例
        监视器=统计监视器(目标,选项)#新建
        _统计监视表[目标]=监视器#登记
        def 摘掉():#停止时移除共享表
            """从共享表删除本路径。"""
            _统计监视表.pop(目标,None)#移除
        监视器.一次('stop',摘掉)#停止时移除
    监视器.监听('change',监听器)#挂接监听器
    return 监视器#返回共享监视器

def 取消监视文件(路径,监听器=None):#取消文件监视
    """移除一条路径的一个或全部监听器。"""
    目标=归一路径(路径)#归一路径
    监视器=_统计监视表.get(目标)#取监视器
    if 监视器 is None: return#无则返回
    if 监听器 is None: 监视器.移除全部监听器('change')#移除全部
    else: 监视器.移除监听器('change',监听器)#移除指定
    if 监视器.监听器数量('change')==0: 监视器.停止()#无监听则停止

def 异步监视(路径,选项=None):#导出异步监视
    """同步生成器：产出 {eventType, filename}。"""
    if 选项 is None:#缺省
        选项={}#空选项
    信号=None if 'signal' not in 选项 else 选项['signal']#中止事件
    若已中止则抛出(信号)#入口已中止
    队列=[]#待取事件
    门=threading.Event()#有事件或终态
    失败=[None]#挂起失败
    关闭=[False]#是否已关闭
    def 收事件(事件类型,文件名):#回调监视
        """入队并放行等待者。"""
        if 关闭[0]:#已关
            return#忽略
        队列.append({'eventType':事件类型,'filename':文件名})#入队
        门.set()#放行
    监视器=监视(路径,选项,收事件)#创建回调监视
    def 等待中止置位():#等到置位
        """中止后失败结算。"""
        if 信号 is None:#无信号
            return#不盯
        信号.wait()#等中止
        失败[0]=中止错误()#记下
        关闭[0]=True#终态
        门.set()#放行
    if 信号 is not None:#有中止
        threading.Thread(target=等待中止置位,daemon=True).start()#盯梢
    try:#产出事件
        while True:#直到关闭或失败
            if 失败[0] is not None:#失败
                raise 失败[0]#抛出
            if 已中止(信号):#中止
                raise 中止错误()#抛出
            if len(队列)>0:#有事件
                yield 队列.pop(0)#产出
                continue#再取
            门.clear()#准备等
            门.wait()#阻塞
    finally:#关闭底层
        关闭[0]=True#标记
        监视器.关闭()#停监视

watch=监视#Node面
watchFile=监视文件#Node面
unwatchFile=取消监视文件#Node面
watchAsync=异步监视#Node面
