"""跨 worker 自有内存 VFS 的 `node:fs` 桥。`MemoryVfs` 拥有路径、字节、目录树与
Node 错误码；本模块只添加 Node-API 形态而非 VFS 业务的部分：Buffer 结果、
`Dirent` 对象、文件描述符、`mkdtemp`、访问检查、监视器、流与 promise 表面。

对齐上游 `webworker-runtime/src/node/builtin_modules/implemented/fs.ts`。
公开面中文名；Node 面经别名与 default 暴露英文名。
"""
from .buffer import Buffer#本包Buffer
from ....storage.活动 import 要求活动vfs#导入活动VFS
from .stream import Readable,Writable#导入流基类
from .path import dirname#导入目录名
from .abort_error import 中止错误,已中止#导入中止错误|中止谓词
from ...未实现失败 import 运行时错误#本包错误
from .fs_watch import FSWatcher,StatWatcher,unwatchFile,watch,watchAsync,watchFile#监视导出

__all__=[#中文公开名与Node英文挂名
    '目录条目','常量','读流','写流','承诺面',
    '读取文件同步','写入文件同步','追加文件同步','存在同步','统计同步','统计',
    '改权限同步','链接统计同步','链接统计','真实路径同步','读目录同步','建目录同步','建临时目录同步',
    '移除同步','取消链接同步','重命名同步','访问同步','打开同步','读取同步','写入同步',
    '关闭同步','硬链接同步','打开句柄同步','创建读流','创建写流','打开目录同步',
    'Dirent','constants','FSWatcher','StatWatcher','unwatchFile','watch','watchFile',
    'readFileSync','writeFileSync','appendFileSync','existsSync','statSync','stat',
    'chmodSync','lstatSync','lstat','realpathSync','readdirSync','mkdirSync','mkdtempSync',
    'rmSync','unlinkSync','renameSync','accessSync','openSync','readSync','writeSync',
    'closeSync','linkSync','openHandleSync','ReadStream','WriteStream',
    'createReadStream','createWriteStream','opendirSync','promises','__esModule','default',
]#公开结束

def vfs():#取当前活动VFS
    """取当前活动 VFS。"""
    return 要求活动vfs()#取当前活动VFS

def 归一路径(路径):#归一为路径字符串
    """路径参数转字符串。"""
    if isinstance(路径,str): return 路径#字符串原样
    if type(路径).__name__=='URL' or hasattr(路径,'pathname'):#URL
        from urllib.parse import unquote#解码
        return unquote(路径.pathname)#URL取路径
    return bytes(路径).decode('utf-8') if isinstance(路径,(bytes,bytearray)) else str(路径)#字节解码

def 取编码(选项):#提取编码
    """从编码选项提取编码。"""
    if 选项 is None: return None#空则无编码
    if isinstance(选项,str): return 选项#字符串即编码
    if isinstance(选项,dict): return 选项.get('encoding')#对象取encoding
    return getattr(选项,'encoding',None)#属性

def 读字节(路径):#同步读字节
    """同步读文件字节。"""
    return vfs().读取文件同步(路径)#委托VFS

def 作缓冲(字节):#视图包为Buffer
    """共享 VFS 字节而非复制。"""
    return Buffer.from(字节)#包装

class 目录条目:#目录条目
    """`readdirSync(dir, { withFileTypes: true })` 返回的 Node `Dirent` 子集。"""

    def __init__(自身,名称,父路径,文件):#构造目录条目
        """构建一个目录条目。"""
        自身.name=名称#保存名
        自身.parentPath=父路径#保存父路径
        自身._文件=文件#保存文件标志

    def 是文件(自身):#是否文件
        """条目是否为普通文件。"""
        return 自身._文件#返回标志

    def 是目录(自身):#是否目录
        """条目是否为目录。"""
        return not 自身._文件#非文件即目录

    def 是符号链接(自身):#是否符号链接
        """镜像物化时无符号链接。"""
        return False#镜像无符号链接

    isFile=是文件#Node面
    isDirectory=是目录#Node面
    isSymbolicLink=是符号链接#Node面

Dirent=目录条目#Node面别名

常量={#fs常量
    'F_OK':0,'R_OK':4,'W_OK':2,'X_OK':1,'COPYFILE_EXCL':1,#访问与复制
    'O_RDONLY':0,'O_WRONLY':1,'O_RDWR':2,'O_CREAT':64,'O_TRUNC':512,'O_APPEND':1024,#打开标志
}#常量结束
constants=常量#Node面别名

def 读取文件同步(路径,选项=None):#同步读文件
    """读取文件。"""
    编码=取编码(选项)#解析编码
    字节=读字节(归一路径(路径))#读字节
    if 编码 is None: return 作缓冲(字节)#Buffer
    if 编码 in ('utf8','utf-8'): return bytes(字节).decode('utf-8')#utf8文本
    return 作缓冲(字节).toString(编码)#其它编码

def 写入文件同步(路径,数据,选项=None):#同步写文件
    """写入文件。"""
    vfs().写入文件同步(归一路径(路径),数据,选项)#委托VFS

def 追加文件同步(路径,数据):#同步追加
    """追加到文件，不存在时创建。"""
    vfs().追加文件同步(归一路径(路径),数据)#委托VFS

def 存在同步(路径):#同步存在性
    """路径是否存在。"""
    return vfs().存在同步(归一路径(路径))#委托VFS

def 统计同步(路径,选项=None):#同步stat
    """对路径做 stat。"""
    return vfs().统计同步(归一路径(路径),选项)#委托VFS

def 统计(路径,选项或回调=None,或许回调=None):#异步回调stat
    """经 Node 回调形式读取 stats。"""
    选项=None if callable(选项或回调) else 选项或回调#解析选项
    回调=选项或回调 if callable(选项或回调) else 或许回调#解析回调
    if 回调 is None: raise TypeError('The "callback" argument must be of type function')#必须有回调
    微任务=globals().get('queueMicrotask')#微任务
    def 执行():#微任务体
        """同步stat后回调。"""
        try: 结果=统计同步(路径,选项)#同步stat
        except 运行时错误 as 错误:#VFS 失败
            回调(错误)#回调错误
            return#结束
        回调(None,结果)#成功回调
    if callable(微任务): 微任务(执行)#排队
    else: 执行()#同步兜底仅当无微任务API

def 改权限同步(路径,模式):#同步chmod
    """更改条目权限位；stat 精确读回所设。"""
    位=int(str(模式),8) if isinstance(模式,str) else 模式#解析八进制或数值
    vfs().改权限同步(归一路径(路径),位)#委托

def 链接统计同步(路径,选项=None):#同步lstat
    """对路径做 stat 且不跟随符号链接（镜像无符号链接）。"""
    return 统计同步(路径,选项)#无符号链接委托stat

def 链接统计(路径,选项或回调=None,或许回调=None):#异步回调lstat
    """经 Node 回调形式读取链接 stats；此无符号链接 VFS 委托给 stat。"""
    统计(路径,选项或回调,或许回调)#委托stat

def 真实路径同步(路径):#同步realpath
    """规范路径（仅规范化：镜像无符号链接）。"""
    return vfs().真实路径同步(归一路径(路径))#委托VFS

def 读目录同步(路径,选项=None):#同步列目录
    """列出目录。"""
    目标=归一路径(路径)#归一路径
    名称列表=vfs().读目录同步(目标)#列名
    if not isinstance(选项,dict) or 选项.get('withFileTypes') is not True: return 名称列表#仅名称
    结果=[]#Dirent列表
    for 名 in 名称列表:#逐名
        统计值=vfs().统计同步(f'{目标}/{名}')#stat
        是文件=统计值.isFile() if hasattr(统计值,'isFile') else 统计值['isFile']()#是否文件
        结果.append(目录条目(名,目标,是文件))#映射Dirent
    return 结果#返回

def 建目录同步(路径,选项=None):#同步mkdir
    """创建目录。"""
    return vfs().建目录同步(归一路径(路径),选项)#委托VFS

def 建临时目录同步(前缀):#同步mkdtemp
    """创建唯一命名目录。"""
    #不用 crypto.randomUUID：浏览器仅在安全上下文暴露它。
    字节=bytearray(3)#3字节
    globals()['crypto'].getRandomValues(字节)#填充随机
    后缀=''.join(f'{b:02x}' for b in 字节)#六十六进制字符
    目标=f'{前缀}{后缀}'#拼目标路径
    vfs().建目录同步(目标,{'recursive':True})#创建目录
    return 目标#返回路径

def 移除同步(路径,选项=None):#同步rm
    """移除文件或目录。"""
    vfs().移除同步(归一路径(路径),选项)#委托VFS

def 取消链接同步(路径):#同步unlink
    """移除文件。"""
    vfs().移除同步(归一路径(路径))#委托rm

def 重命名同步(源路径,目标路径):#同步rename
    """重命名路径。"""
    vfs().重命名同步(归一路径(源路径),归一路径(目标路径))#委托VFS

def 访问同步(路径):#同步access
    """访问检查：仅存在性。"""
    vfs().真实路径同步(归一路径(路径))#存在性检查

_打开文件表={}#fd到打开文件
_下一fd=3#下一描述符从3起

def 打开同步(路径,标志='r',模式=None):#同步open
    """打开文件描述符。"""
    global _下一fd#_下一fd
    目标=归一路径(路径)#归一路径
    文件=vfs().打开文件同步(目标,标志,模式)#打开文件
    fd=_下一fd#分配fd
    _下一fd+=1#递增
    _打开文件表[fd]={'file':文件,'position':0}#登记
    return fd#返回描述符

def 坏描述符(系统调用):#抛出EBADF
    """抛出 EBADF。"""
    错误=Exception(f'EBADF: bad file descriptor, {系统调用}')#构造错误
    错误.code='EBADF'#错误码
    错误.syscall=系统调用#系统调用名
    raise 错误#抛出

def 取打开文件(fd,系统调用):#按fd取打开文件
    """按 fd 取打开文件。"""
    文件=_打开文件表.get(fd)#查找
    if 文件 is None: return 坏描述符(系统调用)#无效则抛
    return 文件#返回

def 读取同步(fd,缓冲,偏移=0,长度=None,位置=None):#同步read
    """从描述符读取。"""
    if 长度 is None:#默认长度
        长度=缓冲.byteLength if hasattr(缓冲,'byteLength') else len(缓冲)#读取长度
    打开=取打开文件(fd,'read')#取打开文件
    起点=打开['position'] if 位置 is None else 位置#起始位置
    切片=打开['file'].read(起点,长度)#读切片
    长=切片.byteLength if hasattr(切片,'byteLength') else len(切片)#切片长
    if hasattr(缓冲,'set'): 缓冲.set(切片,偏移)#类型化数组
    else: 缓冲[偏移:偏移+长]=切片#字节赋值
    if 位置 is None: 打开['position']=起点+长#推进游标
    return 长#返回长度

def 写入同步(fd,数据):#同步write
    """经描述符写入。"""
    打开=取打开文件(fd,'write')#取打开文件
    if isinstance(数据,str):#文本
        编码器=globals().get('TextEncoder')#TextEncoder
        字节=编码器().encode(数据) if 编码器 is not None else 数据.encode('utf-8')#归一字节
    else: 字节=数据#已是字节
    统计值=打开['file'].stat()#文件stat
    追加=打开['file']['append'] if 'append' in 打开['file'] else False#追加否
    大小=统计值['size']#大小
    位置=大小 if 追加 else 打开['position']#追加或游标
    已写=打开['file'].write(位置,字节)#写入
    打开['position']=位置+已写#更新游标
    return 已写#返回写入数

def 关闭同步(fd):#同步close
    """关闭描述符。"""
    if not _打开文件表.pop(fd,None): 取打开文件(fd,'close')#删除失败则抛EBADF

def 硬链接同步(源路径,目标路径):#同步硬链
    """为同一文件身份创建第二个名称。"""
    vfs().硬链接同步(归一路径(源路径),归一路径(目标路径))#委托VFS

def _兑现(值):#同步交回
    """翻译后无 Promise 包装，原样交回同步值。"""
    return 值#同步值

def 打开句柄同步(路径,标志='r',模式=None):#同步打开句柄
    """打开文件句柄（`fs.FileHandle` 子集）：存储后端使用的原子写与持久化对。"""
    目标=归一路径(路径)#归一路径
    存在=vfs().存在同步(目标)#存在
    统计值=vfs().统计同步(目标) if 存在 else None#stat
    if 统计值 is None:#不存在
        目录=False#非目录
    else:#有 stats
        目录=统计值['isDirectory']()#对象面
    fd=-1 if 目录 else 打开同步(目标,标志,模式)#目录无fd
    已关闭=[False]#关闭标志

    def 描述符(系统调用):#按调用取打开文件
        """按调用取打开文件。"""
        return 取打开文件(fd,系统调用)#取

    def 读整文件(选项=None):#读整文件
        """读整文件。"""
        if 目录: return _兑现(读取文件同步(目标,选项))#目录路径读文件
        打开=描述符('read')#取打开状态
        文统=打开['file'].stat()#stat
        大小=文统['size']#大小
        字节=打开['file'].read(打开['position'],max(0,大小-打开['position']))#从游标读完
        打开['position']+=字节.byteLength if hasattr(字节,'byteLength') else len(字节)#推进游标
        编码=取编码(选项)#解析编码
        if 编码 is None: return _兑现(作缓冲(字节))#Buffer
        if 编码 in ('utf8','utf-8'): return _兑现(bytes(字节).decode('utf-8'))#文本
        return _兑现(作缓冲(字节).toString(编码))#其它编码

    def 写整文件(数据,编码=None):#写整文件
        """写整文件。"""
        if 目录: 写入文件同步(目标,数据)#目录路径写文件
        else: 写入同步(fd,数据)#经fd写
        return _兑现(None)#兑现

    def 写一段(数据):#写一段
        """写一段。"""
        return _兑现({'bytesWritten':写入同步(fd,数据)})#写一段

    def 读一段(缓冲,偏移=0,长度=None,位置=None):#读一段
        """读一段。"""
        return _兑现({'bytesRead':读取同步(fd,缓冲,偏移,长度,位置),'buffer':缓冲})#同步读

    def 取统计():#取stats
        """取 stats。"""
        return _兑现(统计同步(目标) if 目录 else 描述符('fstat')['file'].stat())#取stats

    def 截断(长度=0):#截断
        """截断。"""
        if 目录: 写入文件同步(目标,bytearray(长度))#目录路径写空字节
        else: 描述符('ftruncate')['file'].truncate(长度)#经句柄截断
        return _兑现(None)#兑现

    def 刷盘():#刷盘
        """刷盘。"""
        return vfs().flush()#刷盘

    def 数据刷盘():#数据刷盘
        """数据刷盘。"""
        return vfs().flush()#数据刷盘

    def 关闭句柄():#关闭句柄
        """关闭句柄。"""
        if 已关闭[0]: return _兑现(None)#已关则跳过
        已关闭[0]=True#标记关闭
        if fd!=-1: 关闭同步(fd)#有fd则关闭
        return _兑现(None)#兑现

    return {'fd':fd,'readFile':读整文件,'writeFile':写整文件,'write':写一段,'read':读一段,#句柄
        'stat':取统计,'truncate':截断,'sync':刷盘,'datasync':数据刷盘,'close':关闭句柄}#其余

def 流自动销毁(自动关闭):#默认自动销毁
    """Node 通过流的 `autoDestroy` 状态实现文件流 `autoClose`。"""
    return True if 自动关闭 is None else 自动关闭#默认自动销毁

def 销毁文件流(流,信号,中止回调,错误,回调):#销毁文件流
    """释放两个文件流方向共享的描述符。"""
    if 流.fd is not None:#有描述符
        关闭同步(流.fd)#关闭fd
    流.fd=None#清空fd
    流.pending=False#不再待打开
    回调(错误)#回调

def 关闭文件流(流,回调=None):#关闭文件流
    """注册可选完成回调并显式销毁文件流。"""
    if 回调 is not None:#有完成回调
        def 关闭后():#close 后回调
            """以无错误回调。"""
            回调(None)#完成
        流.once('close',关闭后)#close后回调
    流.destroy()#销毁

class 读流(Readable):#可读文件流
    """跨一个 VFS 文件的读流。"""

    def __init__(自身,路径,选项=None):#构造读流
        """打开路径上的读流。"""
        if 选项 is None: 选项={}#缺省
        super().__init__({#初始化可读基类
            'autoDestroy':流自动销毁(选项.get('autoClose')),#自动销毁
            'emitClose':True if 选项.get('emitClose') is None else 选项.get('emitClose'),#默认发射close
            'highWaterMark':64*1024 if 选项.get('highWaterMark') is None else 选项.get('highWaterMark'),#默认高水位
        })#超类参数结束
        自身.path=归一路径(路径)#保存路径
        自身.fd=None#描述符
        自身.pending=True#待打开
        自身.bytesRead=0#已读字节
        自身._start=0 if 选项.get('start') is None else 选项.get('start')#起始
        自身._end=float('inf') if 选项.get('end') is None else 选项.get('end')#结束
        自身._flags='r' if 选项.get('flags') is None else 选项['flags']#??r，空串合法
        自身._position=自身._start#游标从起始
        自身._信号=选项['signal'] if 'signal' in 选项 else None#信号
        自身._中止回调=None#不再挂监听
        if 'encoding' in 选项 and 选项['encoding'] is not None:#有编码
            自身.setEncoding(选项['encoding'])#设编码

    def _construct(自身,callback):#打开构造
        """打开描述符。"""
        if 自身._start<0 or 自身._end<自身._start:#范围非法
            callback(RangeError('The value of "start" is out of range'))#回调范围错
            return#返回
        if 已中止(自身._信号):#已中止
            callback(中止错误())#回调中止错
            return#返回
        try: fd=打开同步(自身.path,自身._flags)#同步打开
        except 运行时错误 as 错误:#VFS 打开失败
            callback(错误)#回调错误
            return#返回
        自身.fd=fd#保存fd
        自身.pending=False#已打开
        callback()#成功回调
        自身.emit('open',fd)#发射open
        自身.emit('ready')#发射ready

    def _read(自身,size):#拉取数据
        """拉取数据。"""
        if 自身.fd is None: return#尚无fd
        剩余=size if 自身._end==float('inf') else min(size,自身._end-自身._position+1)#剩余可读
        if 剩余<=0:#无剩余
            自身.push(None)#结束
            return#返回
        缓冲=Buffer.allocUnsafe(剩余)#分配缓冲
        try: 计数=读取同步(自身.fd,缓冲,0,剩余,自身._position)#同步读
        except 运行时错误 as 错误:#VFS 读失败
            自身.destroy(错误)#销毁
            return#返回
        if 计数==0:#EOF
            自身.push(None)#结束
            return#返回
        自身._position+=计数#推进位置
        自身.bytesRead+=计数#累计
        自身.push(缓冲.subarray(0,计数) if hasattr(缓冲,'subarray') else 缓冲[0:计数])#推送切片

    def _destroy(自身,error,callback):#销毁钩子
        """销毁钩子。"""
        销毁文件流(自身,自身._信号,自身._中止回调,error,callback)#共享销毁

    def 关闭(自身,回调=None):#关闭读流
        """关闭流并释放其描述符。"""
        关闭文件流(自身,回调)#共享关闭

    close=关闭#Node面

ReadStream=读流#Node面别名

class 写流(Writable):#可写文件流
    """经 VFS 文件描述符表面提交块的可写流。"""

    def __init__(自身,路径,选项=None):#构造写流
        """打开路径上的写流。"""
        if 选项 is None: 选项={}#缺省
        super().__init__({#初始化可写基类
            'autoDestroy':流自动销毁(选项.get('autoClose')),#自动销毁
            'decodeStrings':True,#解码字符串
            'defaultEncoding':'utf8' if 选项.get('encoding') is None else 选项['encoding'],#??utf8，空串合法
            'emitClose':True if 选项.get('emitClose') is None else 选项.get('emitClose'),#默认发射close
            'highWaterMark':64*1024 if 选项.get('highWaterMark') is None else 选项.get('highWaterMark'),#默认高水位
        })#超类参数结束
        自身.path=归一路径(路径)#保存路径
        自身.fd=None#描述符
        自身.pending=True#待打开
        自身.bytesWritten=0#已写字节
        自身._flags='w' if 选项.get('flags') is None else 选项['flags']#??w，空串合法
        自身._mode=选项.get('mode')#模式
        自身._start=选项.get('start')#起始
        自身._信号=选项['signal'] if 'signal' in 选项 else None#信号
        自身._中止回调=None#不再挂监听

    def _construct(自身,callback):#打开构造
        """打开描述符。"""
        if 自身._start is not None and 自身._start<0:#起始非法
            callback(RangeError('The value of "start" is out of range'))#回调范围错
            return#返回
        if 已中止(自身._信号):#已中止
            callback(中止错误())#回调中止错
            return#返回
        try: fd=打开同步(自身.path,自身._flags,自身._mode)#同步打开
        except 运行时错误 as 错误:#VFS 打开失败
            callback(错误)#回调错误
            return#返回
        自身.fd=fd#保存fd
        if 自身._start is not None: 取打开文件(fd,'write')['position']=自身._start#设置起始游标
        自身.pending=False#已打开
        callback()#成功回调
        自身.emit('open',fd)#发射open
        自身.emit('ready')#发射ready

    def _write(自身,chunk,encoding,callback):#写入钩子
        """写入钩子。"""
        try:#尝试写
            if 自身.fd is None: return 坏描述符('write')#无fd则抛
            数据=Buffer.from(chunk,encoding) if isinstance(chunk,str) else chunk#归一字节
            自身.bytesWritten+=写入同步(自身.fd,数据)#同步写并累计
            callback()#成功回调
        except 运行时错误 as 错误:#VFS 写失败
            callback(错误)#回调错误

    def _destroy(自身,error,callback):#销毁钩子
        """销毁钩子。"""
        销毁文件流(自身,自身._信号,自身._中止回调,error,callback)#共享销毁

    def 关闭(自身,回调=None):#关闭写流
        """关闭流并释放其描述符。"""
        关闭文件流(自身,回调)#共享关闭

    close=关闭#Node面

WriteStream=写流#Node面别名

def 创建读流(路径,选项=None):#创建读流
    """跨 VFS 创建 Node 兼容的可读文件流。"""
    return 读流(路径,{'encoding':选项} if isinstance(选项,str) else 选项)#构造

def 创建写流(路径,选项=None):#创建写流
    """跨 VFS 创建 Node 兼容的可写文件流。"""
    return 写流(路径,{'encoding':选项} if isinstance(选项,str) else 选项)#构造

def 打开目录同步(路径):#同步打开目录
    """打开目录句柄。列表取一次，因为 VFS 无外部写者可竞态。"""
    目标=归一路径(路径)#归一路径
    条目列表=读目录同步(目标,{'withFileTypes':True})#一次列出
    下标=[0]#游标

    def 下一条():#取下一条
        """取下一条。"""
        if 下标[0]>=len(条目列表): return None#耗尽
        条目=条目列表[下标[0]]#取
        下标[0]+=1#推进
        return 条目#交回

    def 读():#异步读
        """异步读下一条。"""
        return _兑现(下一条())#兑现

    def 关():#异步关闭
        """异步关闭耗尽。"""
        下标[0]=len(条目列表)#耗尽
        return _兑现(None)#兑现

    def 同步关():#同步关闭耗尽
        """同步关闭耗尽。"""
        下标[0]=len(条目列表)#耗尽

    return {'path':目标,'read':读,'close':关,'closeSync':同步关}#返回句柄

def _异步写文件(路径,数据,选项=None):#写文件
    """写文件，含排他与追加。"""
    flag=None if 选项 is None or 'flag' not in 选项 else 选项['flag']#取flag
    mode=None if 选项 is None or 'mode' not in 选项 else 选项['mode']#取mode
    if flag is not None and 'x' in flag and 存在同步(路径):#排他且已存在
        错误=运行时错误(f"EEXIST: file already exists, open '{归一路径(路径)}'")#构造错误
        错误.code='EEXIST'#错误码
        raise 错误#抛出
    if flag is not None and flag.startswith('a'):#追加
        追加文件同步(路径,数据)#追加
        return None#完成
    写选项={}#写选项
    if flag is not None:#有flag
        写选项['flag']=flag#flag
    if mode is not None:#有mode
        写选项['mode']=mode#mode
    写入文件同步(路径,数据,None if len(写选项)==0 else 写选项)#写
    return None#完成

def _异步复制(源路径,目标路径):#复制
    """递归复制文件或目录。"""
    源=归一路径(源路径)#源路径
    目标=归一路径(目标路径)#目标路径
    统计值=统计同步(源)#stats
    if 统计值.isDirectory():#目录递归
        建目录同步(目标,{'recursive':True})#建目标目录
        for 名 in vfs().读目录同步(源):#逐项
            _异步复制(f'{源}/{名}',f'{目标}/{名}')#递归复制
        return None#完成
    建目录同步(dirname(目标),{'recursive':True})#确保父目录
    写入文件同步(目标,读字节(源))#写文件内容
    return None#完成

def 承诺读文件(路径,选项=None):#fs.promises.readFile
    """读文件。"""
    return 读取文件同步(路径,选项)#同步读

def 承诺追加文件(路径,数据):#fs.promises.appendFile
    """追加文件。"""
    追加文件同步(路径,数据)#同步追加
    return None#完成

def 承诺建目录(路径,选项=None):#fs.promises.mkdir
    """建目录。"""
    return 建目录同步(路径,选项)#同步

def 承诺建临时目录(前缀):#fs.promises.mkdtemp
    """建临时目录。"""
    return 建临时目录同步(前缀)#同步

def 承诺读目录(路径,选项=None):#fs.promises.readdir
    """列目录。"""
    return 读目录同步(路径,选项)#同步

def 承诺统计(路径,选项=None):#fs.promises.stat
    """stat。"""
    return 统计同步(路径,选项)#同步

def 承诺链接统计(路径,选项=None):#fs.promises.lstat
    """lstat。"""
    return 链接统计同步(路径,选项)#同步

def 承诺真实路径(路径):#fs.promises.realpath
    """realpath。"""
    return 真实路径同步(路径)#同步

def 承诺移除(路径,选项=None):#fs.promises.rm
    """rm。"""
    移除同步(路径,选项)#同步
    return None#完成

def 承诺取消链接(路径):#fs.promises.unlink
    """unlink。"""
    取消链接同步(路径)#同步
    return None#完成

def 承诺重命名(源路径,目标):#fs.promises.rename
    """rename。"""
    重命名同步(源路径,目标)#同步
    return None#完成

def 承诺访问(路径):#fs.promises.access
    """access。"""
    访问同步(路径)#同步
    return None#完成

def 承诺改权限(路径,模式):#fs.promises.chmod
    """chmod。"""
    改权限同步(路径,模式)#同步
    return None#完成

def 承诺硬链接(源路径,目标):#fs.promises.link
    """硬链。"""
    硬链接同步(源路径,目标)#同步
    return None#完成

def 承诺打开(路径,标志=None,模式=None):#fs.promises.open
    """打开句柄。"""
    return 打开句柄同步(路径,'r' if 标志 is None else 标志,模式)#同步

def 承诺打开目录(路径):#fs.promises.opendir
    """打开目录。"""
    return 打开目录同步(路径)#同步

def 承诺截断(路径,长度=0):#fs.promises.truncate
    """截断。"""
    vfs().截断同步(归一路径(路径),长度)#同步
    return None#完成

承诺面={#promises 表面（同步实现）
    'readFile':承诺读文件,#读文件
    'writeFile':_异步写文件,#写文件
    'appendFile':承诺追加文件,#追加
    'mkdir':承诺建目录,#mkdir
    'mkdtemp':承诺建临时目录,#mkdtemp
    'readdir':承诺读目录,#列目录
    'stat':承诺统计,#stat
    'lstat':承诺链接统计,#lstat
    'realpath':承诺真实路径,#realpath
    'rm':承诺移除,#rm
    'unlink':承诺取消链接,#unlink
    'rename':承诺重命名,#rename
    'access':承诺访问,#access
    'chmod':承诺改权限,#chmod
    'cp':_异步复制,#复制
    'link':承诺硬链接,#硬链
    'open':承诺打开,#打开句柄
    'opendir':承诺打开目录,#打开目录
    'truncate':承诺截断,#截断
    'watch':watchAsync,#监视
    'constants':常量,#常量
}#承诺面结束
promises=承诺面#Node面别名

#Node面英文别名
readFileSync=读取文件同步#同步读
writeFileSync=写入文件同步#同步写
appendFileSync=追加文件同步#同步追加
existsSync=存在同步#存在
statSync=统计同步#stat
stat=统计#异步stat
chmodSync=改权限同步#chmod
lstatSync=链接统计同步#lstat
lstat=链接统计#异步lstat
realpathSync=真实路径同步#realpath
readdirSync=读目录同步#列目录
mkdirSync=建目录同步#mkdir
mkdtempSync=建临时目录同步#mkdtemp
rmSync=移除同步#rm
unlinkSync=取消链接同步#unlink
renameSync=重命名同步#rename
accessSync=访问同步#access
openSync=打开同步#open
readSync=读取同步#read
writeSync=写入同步#write
closeSync=关闭同步#close
linkSync=硬链接同步#link
openHandleSync=打开句柄同步#句柄
createReadStream=创建读流#读流工厂
createWriteStream=创建写流#写流工厂
opendirSync=打开目录同步#opendir

__esModule=True#ES模块标记
default={#默认导出
    'constants':常量,'promises':承诺面,'Dirent':目录条目,#类型与常量
    'FSWatcher':FSWatcher,'StatWatcher':StatWatcher,'ReadStream':读流,'WriteStream':写流,#类
    'readFileSync':读取文件同步,'writeFileSync':写入文件同步,'appendFileSync':追加文件同步,#读写
    'existsSync':存在同步,'statSync':统计同步,'stat':统计,'lstatSync':链接统计同步,'lstat':链接统计,#stat
    'realpathSync':真实路径同步,'chmodSync':改权限同步,#路径
    'readdirSync':读目录同步,'mkdirSync':建目录同步,'mkdtempSync':建临时目录同步,#目录
    'rmSync':移除同步,'unlinkSync':取消链接同步,'renameSync':重命名同步,'accessSync':访问同步,#路径操作
    'opendirSync':打开目录同步,'openHandleSync':打开句柄同步,'linkSync':硬链接同步,#句柄与硬链
    'openSync':打开同步,'readSync':读取同步,'writeSync':写入同步,'closeSync':关闭同步,#fd
    'watch':watch,'watchFile':watchFile,'unwatchFile':unwatchFile,#监视
    'createReadStream':创建读流,'createWriteStream':创建写流,#流工厂
}#默认导出结束
