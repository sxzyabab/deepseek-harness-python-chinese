"""跨活动内存 VFS 的 Node 文件系统监视。

对齐上游 `webworker-runtime/src/node/builtin_modules/implemented/fs-watch.ts`。
文件名下划线：Python 无法 import 连字符模块名。
公开面中文名；Node 面经别名暴露英文名。
"""
from .buffer import Buffer#本包Buffer
from .events import 事件发射器#导入事件发射器
from .async_hooks import 捕获异步上下文,在异步上下文运行#导入异步上下文
from .path import 基名,相对,解析,分隔符#导入路径工具
from ....storage.活动 import 要求活动vfs#导入活动VFS
from .abort_error import 中止错误#导入中止错误

__all__=[#中文与Node面
    '文件系统监视器','统计监视器','监视','监视文件','取消监视文件','异步监视',
    'FSWatcher','StatWatcher','watch','watchFile','unwatchFile','watchAsync',
]#公开结束

def 归一路径(路径):#归一为绝对路径字符串
    """路径参数转绝对路径。"""
    if isinstance(路径,str): return 解析(路径)#字符串直接解析
    if type(路径).__name__=='URL' or hasattr(路径,'pathname'):#URL
        from urllib.parse import unquote#解码
        return 解析(unquote(路径.pathname))#URL取路径
    return 解析(bytes(路径).decode('utf-8') if isinstance(路径,(bytes,bytearray)) else str(路径))#字节解码

def 缺失统计(bigint):#缺失路径的占位stats
    """缺失路径的占位 stats。"""
    零=0 if not bigint else 0#大小零
    基={#公共字段
        'size':零,'ino':零,'mtimeMs':零,'ctimeMs':零,'atimeMs':零,'birthtimeMs':零,#数值
        'mtime':0,'mode':零,#时间与模式
        'isFile':(lambda:False),'isDirectory':(lambda:False),'isSymbolicLink':(lambda:False),#类型
        'isFIFO':(lambda:False),'isSocket':(lambda:False),'isBlockDevice':(lambda:False),#续
        'isCharacterDevice':(lambda:False),#字符设备
    }#基结束
    if bigint:#BigInt附加
        基.update({'dev':0,'nlink':0,'mtimeNs':0,'ctimeNs':0,'atimeNs':0,'birthtimeNs':0,'ctime':0,'atime':0,'birthtime':0})#附加
    return 基#交回

def 统计或缺失(路径,bigint):#stat或占位
    """stat 或 ENOENT 时占位。"""
    try:#尝试真实stat
        return 要求活动vfs().statSync(路径,{'bigint':bigint})#同步stat
    except Exception as 错误:#捕获错误
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

class 文件系统监视器(事件发射器):#文件系统监视器
    """跨 VFS 变更的 `fs.FSWatcher`。"""

    def __init__(自身,目标,目录,选项,监听器=None):#构造监视器
        """订阅 VFS 变更并可选注册监听器。"""
        super().__init__()#初始化事件发射器
        自身._目标=目标#监视目标路径
        自身._是目录=目录#目标是否目录
        自身._选项=选项 or {}#监视选项
        自身._已关闭=False#是否已关闭
        自身._引用=自身._选项.get('persistent',True)#默认保持活性
        自身._上下文=捕获异步上下文()#捕获异步上下文
        if 监听器 is not None: 自身.监听('change',监听器)#注册监听器

        def 收变更(变更):#订阅VFS变更
            """匹配则微任务发射 change。"""
            if not 自身._匹配(变更): return#不匹配则忽略
            种类=变更.get('kind') if isinstance(变更,dict) else getattr(变更,'kind',None)#种类
            条目变=变更.get('entryChanged') if isinstance(变更,dict) else getattr(变更,'entryChanged',None)#条目变
            事件类型='change' if (种类=='write' and not 条目变) or 种类=='chmod' else 'rename'#判定事件类型
            路径=变更.get('path') if isinstance(变更,dict) else getattr(变更,'path',None)#路径
            文件名=自身._文件名(路径)#派生文件名
            微任务=globals().get('queueMicrotask')#微任务
            def 发射():#微任务体
                """在上下文中发射。"""
                if 自身._已关闭: return#已关闭则跳过
                在异步上下文运行(自身._上下文,lambda:自身.发射('change',事件类型,文件名))#发射
            if callable(微任务): 微任务(发射)#排队
            else: 发射()#同步

        自身._取消订阅=要求活动vfs().subscribe(收变更)#订阅VFS变更
        自身._信号=自身._选项.get('signal')#保存信号
        自身._中止回调=None if 自身._信号 is None else (lambda *a:自身.关闭())#信号中止时关闭
        if 自身._信号 is not None and getattr(自身._信号,'aborted',False):#已中止
            自身.关闭()#立即关闭
            return#提前返回
        if 自身._信号 is not None and hasattr(自身._信号,'addEventListener'):#可监听
            自身._信号.addEventListener('abort',自身._中止回调,{'once':True})#注册一次性中止

    def _匹配(自身,变更):#变更是否命中本监视器
        """变更是否命中本监视器。"""
        路径=变更.get('path') if isinstance(变更,dict) else getattr(变更,'path',None)#路径
        种类=变更.get('kind') if isinstance(变更,dict) else getattr(变更,'kind',None)#种类
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
        if 自身._中止回调 is not None and 自身._信号 is not None:#有中止监听
            if hasattr(自身._信号,'removeEventListener'): 自身._信号.removeEventListener('abort',自身._中止回调)#移除
        微任务=globals().get('queueMicrotask')#微任务
        if callable(微任务): 微任务(lambda:自身.发射('close'))#异步发射close
        else: 自身.发射('close')#同步

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
    统计=要求活动vfs().statSync(目标)#取目标stats
    是目录=统计['isDirectory']() if isinstance(统计,dict) else 统计.isDirectory()#是否目录
    return 文件系统监视器(目标,是目录,选项,监听器)#构造并返回

def 定时器引用(定时器):#调用定时器ref
    """浏览器定时器为数值；Node 定时器暴露可选活性方法。"""
    ref=getattr(定时器,'ref',None) if not isinstance(定时器,(int,float)) else None#ref面
    if callable(ref): ref()#可选调用ref

def 定时器取消引用(定时器):#调用定时器unref
    """浏览器定时器为数值；Node 定时器暴露可选活性方法。"""
    unref=getattr(定时器,'unref',None) if not isinstance(定时器,(int,float)) else None#unref面
    if callable(unref): unref()#可选调用unref

_统计监视们={}#路径到共享stat监视器

class 统计监视器(事件发射器):#stat轮询监视器
    """`watchFile` 返回的 `fs.StatWatcher`。"""

    def __init__(自身,路径,选项):#构造stat监视器
        """订阅变更并可选立即调度。"""
        super().__init__()#初始化事件发射器
        自身.path=路径#路径
        自身._引用=(选项 or {}).get('persistent',True)#默认保持活性
        自身._间隔=(选项 or {}).get('interval',5007)#默认间隔
        自身._bigint=(选项 or {}).get('bigint',False)#默认非BigInt
        自身._上次=统计或缺失(路径,自身._bigint)#初始stats
        自身._上下文=捕获异步上下文()#捕获上下文
        自身._定时器=None#轮询定时器
        自身._已停=False#是否已停止

        def 收变更(变更):#订阅变更
            """重叠则调度。"""
            路径值=变更.get('path') if isinstance(变更,dict) else getattr(变更,'path',None)#路径
            if 重叠(路径,路径值): 自身._调度()#重叠则调度

        自身._取消订阅=要求活动vfs().subscribe(收变更)#订阅结束
        if not 自身._上次['isFile']() and not 自身._上次['isDirectory'](): 自身._调度(True)#初始缺失

    def _调度(自身,初缺=False):#调度一次轮询
        """调度一次轮询。"""
        if 自身._已停 or 自身._定时器 is not None: return#已停或已有定时器
        全局=globals()#宿主

        def 到期():#超时体
            """比较并可能发射 change。"""
            自身._定时器=None#清除句柄
            if 自身._已停: return#已停则跳过
            当前=统计或缺失(自身.path,自身._bigint)#当前stats
            上次=自身._上次#上次快照
            自身._上次=当前#更新快照
            if 初缺 or 统计已变(当前,上次):#初缺或有变化
                在异步上下文运行(自身._上下文,lambda:自身.发射('change',当前,上次))#发射变更

        自身._定时器=全局['setTimeout'](到期,自身._间隔)#设置超时
        if not 自身._引用: 定时器取消引用(自身._定时器)#非引用则unref

    def 停止(自身):#停止监视
        """停止轮询并释放 VFS 订阅。"""
        if 自身._已停: return#已停则跳过
        自身._已停=True#标记停止
        自身._取消订阅()#取消订阅
        if 自身._定时器 is not None: globals()['clearTimeout'](自身._定时器)#清除定时器
        自身._定时器=None#清空句柄
        自身.发射('stop')#发射stop

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
    监视器=_统计监视们.get(目标)#查共享监视器
    if 监视器 is None:#尚无共享实例
        监视器=统计监视器(目标,选项)#新建
        _统计监视们[目标]=监视器#登记
        监视器.一次('stop',lambda: _统计监视们.pop(目标,None))#停止时移除
    监视器.监听('change',监听器)#挂接监听器
    return 监视器#返回共享监视器

def 取消监视文件(路径,监听器=None):#取消文件监视
    """移除一条路径的一个或全部监听器。"""
    目标=归一路径(路径)#归一路径
    监视器=_统计监视们.get(目标)#取监视器
    if 监视器 is None: return#无则返回
    if 监听器 is None: 监视器.移除全部监听器('change')#移除全部
    else: 监视器.移除监听器('change',监听器)#移除指定
    if 监视器.监听器数量('change')==0: 监视器.停止()#无监听则停止

def 异步监视(路径,选项=None):#导出异步监视
    """在回调监视器上创建基于 promise 的监视迭代器。"""
    if 选项 is None: 选项={}#选项默认空
    队列=[]#待取事件队列
    等待们=[]#等待中的Promise
    监视器盒=[None]#底层监视器
    失败盒=[None]#挂起失败
    关闭盒=[False]#是否已关闭
    承诺类=globals().get('Promise')#Promise

    def 停监视():#停止底层监视
        """移除中止监听并关闭监视器。"""
        信号=选项.get('signal')#信号
        if 信号 is not None and hasattr(信号,'removeEventListener'): 信号.removeEventListener('abort',中止时)#移除
        if 监视器盒[0] is not None: 监视器盒[0].关闭()#关闭监视器

    def 结算失败(原因):#以失败结算
        """以失败结算迭代器。"""
        if 关闭盒[0]: return#已关闭则跳过
        错误=原因 if isinstance(原因,Exception) else Exception(str(原因))#归一错误
        关闭盒[0]=True#标记关闭
        队列.clear()#清空队列
        停监视()#停监视
        if 等待们:#有等待者
            失败者=等待们.pop(0)#取一个等待者
            失败者['reject'](错误)#立即拒绝
            for 挂起 in list(等待们): 挂起['resolve']({'done':True,'value':None})#其余完成
            等待们.clear()#清空
        else: 失败盒[0]=错误#无人等待则挂起失败

    def 中止时(*位置参数):#中止时失败结算
        """中止时失败结算。"""
        信号=选项.get('signal')#信号
        结算失败(中止错误(getattr(信号,'reason',None) if 信号 is not None else None))#结算

    def 启动():#惰性启动监视
        """惰性启动监视。"""
        if 监视器盒[0] is not None or 关闭盒[0] or 失败盒[0] is not None: return#已启或已终
        信号=选项.get('signal')#信号
        if 信号 is not None and getattr(信号,'aborted',False):#信号已中止
            结算失败(中止错误(getattr(信号,'reason',None)))#立即失败
            return#返回
        try:#尝试启动
            def 收事件(事件类型,文件名):#创建回调监视
                """交付事件给等待者或入队。"""
                事件={'eventType':事件类型,'filename':文件名}#组装事件
                if 等待们: 等待们.pop(0)['resolve']({'done':False,'value':事件})#交付
                else: 队列.append(事件)#无人则入队
            监视器盒[0]=监视(路径,选项,收事件)#创建回调监视
            监视器盒[0].监听('error',结算失败)#错误转失败
            if 信号 is not None and hasattr(信号,'addEventListener'): 信号.addEventListener('abort',中止时,{'once':True})#注册中止
        except Exception as 错误:#启动失败
            结算失败(错误)#结算失败

    def 关闭():#关闭迭代器
        """关闭迭代器。"""
        已关=关闭盒[0]#记录原状态
        关闭盒[0]=True#标记关闭
        队列.clear()#清空队列
        失败盒[0]=None#清除失败
        if not 已关: 停监视()#首次关闭才停监视
        for 挂起 in list(等待们): 挂起['resolve']({'done':True,'value':None})#唤醒等待者
        等待们.clear()#清空

    def 下一():#取下一事件
        """取下一事件。"""
        启动()#确保已启动
        if 失败盒[0] is not None:#有挂起失败
            原因=失败盒[0]#取出原因
            失败盒[0]=None#清除
            return 承诺类.reject(原因)#拒绝
        if 队列: return 承诺类.resolve({'done':False,'value':队列.pop(0)})#交付
        if 关闭盒[0]: return 承诺类.resolve({'done':True,'value':None})#结束
        return 承诺类(lambda resolve,reject:等待们.append({'resolve':resolve,'reject':reject}))#挂起等待

    def 返回():#迭代器return
        """关闭并结束。"""
        关闭()#关闭
        return 承诺类.resolve({'done':True,'value':None})#结束

    def 抛出(原因=None):#迭代器throw
        """关闭并原样拒绝。"""
        关闭()#关闭
        return 承诺类.reject(原因)#原样拒绝

    return {'next':下一,'return':返回,'throw':抛出}#迭代器对象结束

watch=监视#Node面
watchFile=监视文件#Node面
unwatchFile=取消监视文件#Node面
watchAsync=异步监视#Node面
