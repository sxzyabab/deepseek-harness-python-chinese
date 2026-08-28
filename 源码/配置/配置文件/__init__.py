"""文件后端的设置提供方。用户 harness 主目录下的一份 YAML 或 JSON 文档承载每个命名空间段落；外部编辑经 seam 热发布，每次写入都在跨进程写锁下重读文档，再以保留注释的叶级 diff 打补丁。"""
import os,json,errno,threading,time,io#路径、JSON、错误码、线程、时间与内存流
from ...依赖 import cordis,ruamel_yaml#外部依赖胶水
from ...依赖.schemastery import 路径上节点,字符串字段,布尔字段,数字字段#配置字段
承诺=cordis.工具.承诺#操作链承诺
是否thenable=cordis.工具.是否thenable#可等待判定
YAML=ruamel_yaml.YAML#保留注释的YAML
CommentedMap=ruamel_yaml.comments.CommentedMap#带注释映射
from ...工具.原子写入 import 带文件锁,原子写文件#跨进程写锁与原子替换
from ...工具.工作区路径 import 规范化监视路径,解析主目录#监视路径与harness主目录
from ..配置 import 设置提供方,json深度相等#设置服务基类与JSON深等

格式表={#扩展名到格式
    '.yaml':'yaml',#YAML
    '.yml':'yaml',#YAML别名
    '.json':'json',#JSON
}#扩展名到格式

配置模式=路径上节点({#插件配置字段
    'path':字符串字段(),#文档路径
    'dshHome':字符串字段(),#主目录
    'watch':布尔字段(默认值=True),#默认监视
    'debounceMs':数字字段(最小=0,默认值=100),#默认防抖
})#插件配置模式

def 解开(值):#承诺则等待
    """承诺则等待，否则原样返回。"""
    if 是否thenable(值):#像承诺
        return 值.等待()#等待承诺
    return 值#同步值

def 取配置项(配置,键):#读配置字段
    """读取插件配置字段，缺席为 None。"""
    if 配置 is None:#无配置
        return None#无配置
    if isinstance(配置,dict):#映射
        return 配置.get(键)#映射键
    return getattr(配置,键,None)#对象属性

def 是否映射(值):#用于diff的映射
    """解析后的值是否是用于 diff 的映射。"""
    return isinstance(值,dict) and not isinstance(值,list)#非列表对象

def 是否不存在(错误):#ENOENT
    """文件系统错误是否表示缺失；每个非 ENOENT 失败都必须浮出。"""
    if getattr(错误,'code',None)=='ENOENT':#带Node风格码
        return True#带Node风格码
    return isinstance(错误,OSError) and 错误.errno==errno.ENOENT#Python缺失

def 是否已存在(错误):#EEXIST
    """独占创建文件时是否发现已有文档。"""
    if getattr(错误,'code',None)=='EEXIST':#带Node风格码
        return True#带Node风格码
    return isinstance(错误,OSError) and 错误.errno==errno.EEXIST#Python已存在

def 建yaml解析器():#往返解析器
    """构造保留注释的 YAML 1.2 往返解析器。"""
    解析器=YAML(typ='rt')#往返模式
    解析器.version=(1,2)#YAML 1.2
    解析器.preserve_quotes=True#保留引号
    解析器.default_flow_style=False#块样式
    return 解析器#解析器

def 倾倒yaml(解析器,数据):#渲染YAML文本
    """把可改 YAML 树渲染成文本。"""
    流=io.StringIO()#内存流
    解析器.dump(数据,流)#写出
    return 流.getvalue()#文本

def 转普通(值):#收成普通数据
    """把 YAML 节点收成普通字典、列表和标量。"""
    if isinstance(值,dict):#映射
        结果={}#普通字典
        for 键 in 值:#自有键
            结果[键]=转普通(值[键])#递归值
        return 结果#普通字典
    if isinstance(值,list):#列表
        结果=[]#普通列表
        for 项 in 值:#各项
            结果.append(转普通(项))#递归项
        return 结果#普通列表
    return 值#标量

def 设路径(文档,路径,值):#写入路径
    """在保留注释的映射树上写入一条路径。"""
    当前=文档#从根走
    末段=路径[len(路径)-1]#最后一段
    下标=0#中间段下标
    while 下标<len(路径)-1:#走中间段
        段=路径[下标]#本段
        if (not isinstance(当前,dict)) or (段 not in 当前) or (not isinstance(当前[段],dict)):#缺中间映射
            当前[段]=CommentedMap()#造中间映射
        当前=当前[段]#下行
        下标+=1#下一段
    当前[末段]=值#写入叶

def 删路径(文档,路径):#删掉路径
    """在保留注释的映射树上删掉一条路径。"""
    当前=文档#从根走
    末段=路径[len(路径)-1]#最后一段
    下标=0#中间段下标
    while 下标<len(路径)-1:#走中间段
        段=路径[下标]#本段
        if (not isinstance(当前,dict)) or (段 not in 当前):#没有这条路径
            return#没有这条路径
        当前=当前[段]#下行
        下标+=1#下一段
    if isinstance(当前,dict) and 末段 in 当前:#叶存在
        del 当前[末段]#删叶

def 打补丁节点(文档,路径,当前,下一值):#叶级diff
    """把一个节点已存值与下一值的差应用成最小的设路径/删路径编辑，并在映射里递归，因此每个未碰节点以及每个改动对的键节点都保住注释、锚点和格式。非映射值（数组和标量）不相等时整块替换，里面的注释一并带走。"""
    if 是否映射(当前) and 是否映射(下一值):#两边都是映射
        for 键 in list(当前.keys()):#已存键
            if 键 not in 下一值:#下一值没有
                删路径(文档,list(路径)+[键])#下一值没有则删
        for 键 in 下一值:#下一值键
            打补丁节点(文档,list(路径)+[键],当前.get(键),下一值[键])#递归打补丁
        return#映射处理完
    if not json深度相等(当前,下一值):#不相等
        设路径(文档,list(路径),下一值)#不相等则整块替换

def 读文件文本(路径):#读UTF-8
    """按 UTF-8 读取整个文档。"""
    文件=open(路径,'r',encoding='utf-8')#打开文本
    try:#读全部
        return 文件.read()#读全部
    finally:#关掉
        文件.close()#关掉

def 独占创建空文件(路径):#wx创建
    """以 wx 独占创建仅所有者空文档。"""
    标志=os.O_CREAT|os.O_EXCL|os.O_WRONLY#独占创建
    if os.name=='nt':#Windows
        标志|=os.O_BINARY#Windows二进制
    描述符=os.open(路径,标志,0o600)#仅所有者
    os.close(描述符)#空内容

class 已解析规格:#运行时规格
    """完全解析的提供方参数；默认值在这里发生，从不内联。"""
    def __init__(自身,文件名,格式,监视,防抖毫秒):#保存规格
        """保存已解析的文件位置、格式与监视行为。"""
        自身.文件名=文件名#文档路径
        自身.格式=格式#yaml或json
        自身.监视=监视#是否监视
        自身.防抖毫秒=防抖毫秒#防抖毫秒

def 解析规格(配置):#配置收成规格
    """从插件配置解析运行时 spec：显式 path 优先，否则文档落在 harness 主目录下的 settings.yaml。"""
    路径=取配置项(配置,'path')#显式路径
    if 路径 is None:#省略path
        主目录=解开(解析主目录(取配置项(配置,'dshHome')))#解析harness主目录
        文件名=os.path.abspath(os.path.join(主目录,'settings.yaml'))#默认文档
    else:#显式path
        文件名=os.path.abspath(路径)#显式文档
    扩展=os.path.splitext(文件名)[1]#扩展名
    格式=格式表.get(扩展)#按扩展名取格式
    if 格式 is None:#不支持
        raise Exception('settings-file: extension "'+扩展+'" is not supported (use .yaml, .yml, or .json)')#拒绝
    监视=取配置项(配置,'watch')#是否监视
    if 监视 is None:#省略watch
        监视=True#默认监视
    防抖=取配置项(配置,'debounceMs')#防抖毫秒
    if 防抖 is None:#省略debounceMs
        防抖=100#默认防抖
    return 已解析规格(文件名,格式,监视,防抖)#已解析规格

class 文档监视器:#轮询监视
    """按写入落定期轮询文档，对齐 chokidar 的 ignoreInitial 与 awaitWriteFinish。"""
    def __init__(自身,路径,稳定毫秒,轮询毫秒):#记下窗口
        """记下监视路径与落定期窗口。"""
        自身.路径=路径#监视路径
        自身.稳定毫秒=稳定毫秒#落定期
        自身.轮询毫秒=轮询毫秒#轮询间隔
        自身.监听={'all':[],'ready':[],'error':[]}#事件表
        自身.停止=threading.Event()#拆除旗标
        自身.线程=None#工作线程

    def on(自身,事件,回调):#登记回调
        """登记一个监视事件回调。"""
        自身.监听[事件].append(回调)#挂上
        return 自身#链式

    def 启动(自身):#启动线程
        """启动轮询线程。"""
        自身.线程=threading.Thread(target=自身.循环)#工作线程
        自身.线程.daemon=True#不挡住退出
        自身.线程.start()#启动

    def 关闭(自身):#停止轮询
        """停止轮询并等待线程退出。"""
        自身.停止.set()#拒绝新轮询
        if 自身.线程 is not None:#已启动
            自身.线程.join()#排空线程

    def 签名(自身):#读文件签名
        """读取存在性、mtime 与大小；缺失则为 missing。"""
        try:#跟随链接
            信息=os.stat(自身.路径)#跟随链接
            return ('file',信息.st_mtime_ns,信息.st_size)#文件签名
        except OSError as 错误:#stat失败
            if 是否不存在(错误):#缺失
                return ('missing',None,None)#记下缺失
            raise 错误#其余失败抛出

    def 发出(自身,事件,*位置参数):#扇出回调
        """同步调用该事件的全部回调。"""
        for 回调 in list(自身.监听.get(事件,[])):#快照回调
            回调(*位置参数)#逐个调用

    def 循环(自身):#轮询主循环
        """忽略初始签名，就绪后把落定的外部改动发成 all。"""
        try:#整段循环
            已发布=自身.签名()#初始签名不发all
            观察中=已发布#当前观察
            待定时刻=0#落定计时
            有待定=False#是否等待落定
            自身.发出('ready')#监视就绪
            while not 自身.停止.is_set():#直到拆除
                自身.停止.wait(max(自身.轮询毫秒,1)/1000.0)#按间隔等待
                if 自身.停止.is_set():#已拆除
                    return#已拆除
                try:#再读签名
                    现在=自身.签名()#再读签名
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
                        已发布=现在#记下已发
                        自身.发出('all')#外部改动
        except Exception as 错误:#循环失败
            自身.发出('error',错误)#循环失败

class 文件设置提供方(设置提供方):#文件设置提供方
    """文件后端的设置提供方（settings.yaml/.json）。"""
    Config=配置模式#Cordis配置模式

    def __init__(自身,ctx,配置):#构造提供方
        """程序化构造可能绕过 Schemastery 规范化；无论哪种路径都在一个显式步骤里解析同一套默认值。"""
        super().__init__(ctx)#登记提供方
        自身.config=配置#原始配置
        自身.配置=配置#中文别名
        自身.规格=解析规格(配置)#解析规格
        #上次成功解析或持久化的文档原文；文件缺失时为None。内容等于本缓存的监视器事件是空操作，这也是自我写入抑制。
        自身.文本=None#文档缓存，缺失为None
        #单一独占操作链：监视器重载与文档写入按队列顺序一次一个（已结算尾），因此写入永远不能从并发重载正忙着替换的文本渲染，重载也永远不能读到半提交的写入。
        自身.操作链=承诺()#单一独占操作链
        自身.操作链.兑现()#已结算空链
        自身.链锁=threading.Lock()#改链互斥
        自身.已关闭=False#拆除门：拒绝新的监视器事件，让进行中的工作变成空操作

    @property#只读属性
    def 可写(自身):#是否可写
        """本地文档始终可通过 update 写入。"""
        return True#始终可写

    @property#只读属性
    def 文档路径(自身):#文档路径
        """暴露给本地配置面的已解析 YAML/JSON 文档路径。"""
        return 自身.规格.文件名#已解析路径

    def 是否已关闭(自身):#读关闭标志
        """关闭标志的不透明读取：控制流不能跨等待收窄它。"""
        return 自身.已关闭#返回标志

    def 入队(自身,操作):#入队操作
        """把一次独占文档操作排到此前每一次后面。"""
        任务=承诺()#本切片
        with 自身.链锁:#改链互斥
            前=自身.操作链#此前尾巴
            本=承诺()#新尾巴
            自身.操作链=本#钉成新尾巴
        def 跑():#接到链尾后执行本切片
            """接到链尾后执行本切片，链环吞拒绝。"""
            try:#等前任
                前.等待()#等前任兑现
            except BaseException:#前任已拒绝
                pass#链环已保证前任兑现，这里只防意外
            try:#跑本切片
                任务.兑现(操作())#把本切片交给调用方
            except BaseException as 错误:#本切片失败
                任务.拒绝(错误)#调用方看见拒绝
            本.兑现()#链环永不拒绝
        工作=threading.Thread(target=跑)#工作线程
        工作.daemon=True#不挡住退出
        工作.start()#启动
        return 任务#本切片

    def 排队刷新(自身):#排队重载
        """排队一次重载；只有逃出提交的不变量违反才能拒绝它。"""
        def 操作():#链上刷新
            """链上刷新。"""
            自身.刷新()#重读发布
        任务=自身.入队(操作)#上操作链
        def 收住():#观察拒绝面
            #只有逃出提交路径的不变量违反才能拒绝刷新；保持操作队列存活并作为错误浮出，这样一次中毒提交不能静默永远结束热重载。
            """保持操作队列存活并作为错误浮出。"""
            try:#等待刷新
                任务.等待()#等待刷新
            except BaseException as 错误:#逃出提交的失败
                自身.ctx.logger.error('settings-file: reload commit failed at %s',自身.规格.文件名)#记错误
                自身.ctx.logger.error(错误)#记原因
        观察=threading.Thread(target=收住)#后台观察
        观察.daemon=True#不挡住退出
        观察.start()#启动

    def 准备文档(自身):#物化缺失文档
        """物化一份缺失的仅所有者文档，再返回其已解析路径。"""
        def 操作():#上操作链
            """上操作链：仅所有者目录，跨进程锁下独占创建。"""
            os.makedirs(os.path.dirname(自身.规格.文件名),mode=0o700,exist_ok=True)#仅所有者目录
            def 持锁():#独占创建空文档
                """独占创建空文档；已有则跳过。"""
                try:#独占创建
                    独占创建空文件(自身.规格.文件名)#空文档
                except OSError as 错误:#创建失败
                    if 是否已存在(错误):#已有文档
                        return#已有则跳过
                    raise 错误#其余失败抛出
                自身.文本=''#记下空缓存
                if not 自身.是否已关闭():#尚未拆除
                    自身.发布({})#发布空文档
            解开(带文件锁(自身.规格.文件名,持锁))#跨进程锁
            return 自身.规格.文件名#返回路径
        return 自身.入队(操作).等待()#上操作链并等待

    def 加载(自身):#读当前文档
        """读取提供方当前的原始文档。"""
        try:#读文件
            文本=读文件文本(自身.规格.文件名)#读文本
        except OSError as 错误:#读失败
            if not 是否不存在(错误):#非缺失
                raise 错误#非缺失则抛
            自身.文本=None#记下缺失
            return {}#空段落
        文档=自身.解析(文本)#解析文档
        自身.文本=文本#记下缓存
        return 文档#返回段落

    def 持久化(自身,命名空间,段落):#串行写入
        #一份文档承载每个命名空间，因此来自不同命名空间队列的写入彼此以及与监视器重载在同一条操作链上串行：每次渲染必须看见上一次操作提交的文本，否则兄弟段落会从磁盘静默消失。
        """一份文档承载每个命名空间，因此来自不同命名空间队列的写入彼此以及与监视器重载在同一条操作链上串行：每次渲染必须看见上一次操作提交的文本，否则兄弟段落会从磁盘静默消失。"""
        def 操作():#持久化一个段落
            """持久化一个段落。"""
            自身.持久化段落(命名空间,段落)#写盘
        自身.入队(操作).等待()#上操作链并等待

    def 持久化段落(自身,命名空间,段落):#读改写一段
        #写锁的独占创建需要父目录在原子写自己有机会创建它之前就存在。
        #0700：harness 主目录持有用户私有文档。
        """写锁的独占创建需要父目录在原子写自己有机会创建它之前就存在。0700：harness 主目录持有用户私有文档。"""
        os.makedirs(os.path.dirname(自身.规格.文件名),mode=0o700,exist_ok=True)#仅所有者目录
        def 持锁():#对齐后渲染并原子写
            #读改写：折入本进程尚未观察到的磁盘状态——仍在监视器防抖窗口内的外部编辑、监视器漏掉的改动、或另一进程的写入——这样下面的渲染永远不能复活过时文档。不可解析的磁盘文档让写入大声失败，而不是静默覆盖用户的手工编辑。
            """与磁盘对齐后按格式渲染并原子写；读改写折入未观察磁盘，不可解析则大声失败。"""
            自身.从磁盘对齐()#与磁盘对齐
            if 自身.规格.格式=='yaml':#YAML
                输出=自身.渲染yaml(命名空间,段落)#YAML叶级diff
            else:#JSON
                输出=自身.渲染json(命名空间,段落)#JSON整键替换
            #0600：可能持有个人值的文档永远不要对世界可读。
            解开(原子写文件(自身.规格.文件名,输出,{'mode':0o600,'dirMode':0o700}))#原子写，0600勿对世界可读
            自身.文本=输出#记下缓存
        解开(带文件锁(自身.规格.文件名,持锁))#跨进程锁

    def _初始化(自身):#服务初始化
        #基类 init 加载并发布；那里的解析失败是启动失败：已有但无效的文档必须大声失败，绝不能被静默忽略或覆盖。
        """基类 init 加载并发布；那里的解析失败是启动失败：已有但无效的文档必须大声失败，绝不能被静默忽略或覆盖。然后按配置建立监视器。"""
        yield from super()._初始化()#基类加载
        监视器=None#未配置则为空
        if 自身.规格.监视:#已配置监视
            路径=解开(规范化监视路径(自身.规格.文件名))#规范化监视路径
            轮询=max(1,min(自身.规格.防抖毫秒,10))#轮询间隔
            监视器=文档监视器(路径,自身.规格.防抖毫秒,轮询)#监视文档
            def 任意事件(*位置参数):#任意监视事件
                """任意监视事件。"""
                if 自身.已关闭:#已关闭
                    return#已关闭则跳过
                自身.排队刷新()#排队重载
            def 监视就绪(*位置参数):#监视就绪
                #基类 init 的加载与监视器自己的建立竞态：那次读取与监视器激活之间写入的改动永远不会开火事件。就绪时对齐一次关掉缺口。
                """基类加载与监视器建立竞态：就绪时对齐一次关掉缺口。"""
                if 自身.已关闭:#已关闭
                    return#已关闭则跳过
                自身.排队刷新()#排队对齐
            def 监视错误(错误,*位置参数):#监视错误
                """监视错误只记警告。"""
                自身.ctx.logger.warn('settings-file: watcher error on %s',自身.规格.文件名)#记警告
                自身.ctx.logger.warn(错误)#记原因
            监视器.on('all',任意事件)#任意事件
            监视器.on('ready',监视就绪)#监视就绪
            监视器.on('error',监视错误)#监视错误
            监视器.启动()#开始轮询
        def 拆除():#静默操作链
            """即使没配置监视器也静默每条操作链。"""
            自身.已关闭=True#拒绝新事件
            if 监视器 is not None:#已配置监视
                监视器.关闭()#关监视器
            自身.操作链.等待()#排空操作链
        yield 拆除#拆除器

    def 解析(自身,文本):#解析文档
        """把一份文档文本解析成原始段落，非映射根则失败。"""
        if 自身.规格.格式=='yaml':#YAML
            解析器=建yaml解析器()#往返解析器
            try:#解析YAML
                #只取行列位置；从不使用 error.message，因为解析器会引用出错源行，而设置文档可以持有 secret 值。
                根=解析器.load(文本)#解析YAML
            except Exception as 错误:#有解析错误
                #勿用 error.message（可含 secret 源行）；只报错误名与行列。
                标记=getattr(错误,'problem_mark',None)#行列
                if 标记 is None:#无行列
                    片段=type(错误).__name__#只有错误名
                else:#有行列
                    片段=type(错误).__name__+' at line '+str(标记.line+1)+', column '+str(标记.column+1)#错误名加位置
                raise Exception('settings-file: invalid document at '+自身.规格.文件名+': '+片段)#拒绝
            if 根 is None:#空文档
                根={}#空则空对象
            else:#有根
                根=转普通(根)#收成普通映射
        else:#JSON
            if len(文本.strip())==0:#空文本
                根={}#空则空对象
            else:#有内容
                根=json.loads(文本)#解析JSON
        if (not isinstance(根,dict)) or isinstance(根,list):#非映射根
            raise TypeError('settings-file: '+自身.规格.文件名+' must be a map of namespace sections')#拒绝
        return 根#段落映射

    def 刷新(自身):#监视器后重读
        """监视器事件后重读文档。未变内容（包括本提供方自己的写入）是空操作；不可读或不可解析的文档保住上次好段落并警告——活的热重载永远不得把进程打掉。逃出提交的不变量违反不是重载失败，会传播到队列的错误面。"""
        if 自身.已关闭:#已关闭
            return#已关闭则跳过
        try:#对齐磁盘
            自身.从磁盘对齐()#重读发布
        except Exception as 错误:#对齐失败
            if getattr(错误,'code',None)=='INVARIANT':#不变量违反
                raise 错误#不变量违反上浮
            自身.ctx.logger.warn('settings-file: reload failed at %s; keeping the last good document',自身.规格.文件名)#记警告
            自身.ctx.logger.warn(错误)#记原因

    def 从磁盘对齐(自身):#与磁盘对齐
        """把磁盘文本与缓存比较，有差则发布进 seam。缺失发布空文档；不可读或不可解析的文件抛错，因此每个调用方自选策略——重载警告并保住上次好文档，写入大声失败。"""
        try:#读文件
            文本=读文件文本(自身.规格.文件名)#读文本
        except OSError as 错误:#读失败
            if not 是否不存在(错误):#非缺失
                raise 错误#非缺失则抛
            文本=None#记下缺失
        if 文本==自身.文本 or 自身.是否已关闭():#未变或已关闭（自写抑制）
            return#未变或已关闭
        if 文本 is None:#文件没了
            自身.文本=None#清缓存
            自身.发布({})#发布空文档
            return#结束
        文档=自身.解析(文本)#解析
        自身.文本=文本#记下缓存
        自身.发布(文档)#发布段落

    def 渲染yaml(自身,命名空间,段落):#渲染YAML
        """在保留注释的文档里给一个命名空间打补丁，渲染下一份 YAML 文本。下一段落作为对已存段落的叶级 diff 落地——只设改过的值，只删去掉的键——因此段落内的注释在改兄弟时仍活着，不只是段外注释。"""
        if 自身.文本 is None:#没有缓存
            return 倾倒yaml(建yaml解析器(),{命名空间:段落})#新建文档
        #自身.文本只缓存解析成功过的内容，因此这次再解析（为可变的保留注释树）不能失败，且解析()已经拒绝过任何非映射根。
        解析器=建yaml解析器()#再解析树
        try:#再解析（缓存应已解析成功）
            文档=解析器.load(自身.文本)#可变的保留注释树
        except Exception as 错误:#不应失败
            raise 错误#缓存应已解析成功
        if 文档 is None:#空根
            文档=CommentedMap()#空根改成映射
            行们=[]#文档头注释
            for 行 in 自身.文本.splitlines():#扫头注释
                剥=行.strip()#去空白
                if 剥.startswith('#'):#注释行
                    内容=剥[1:]#去掉井号
                    if 内容.startswith(' '):#惯例空格
                        内容=内容[1:]#去掉一个空格
                    行们.append(内容)#收下
                elif 剥=='':#空行
                    if len(行们)==0:#开头空行
                        continue#开头空行跳过
                    break#注释块结束
                else:#正文
                    break#遇到正文
            if len(行们)>0:#有头注释
                文档.yaml_set_start_comment('\n'.join(行们))#挂上头注释
        根=转普通(文档)#转JS根
        if 是否映射(根):#映射根
            当前段=根.get(命名空间)#已存段落
        else:#非映射根
            当前段=None#非映射根
        打补丁节点(文档,[命名空间],当前段,段落)#叶级diff保注释
        return 倾倒yaml(解析器,文档)#渲染文本

    def 渲染json(自身,命名空间,段落):#渲染JSON
        """通过替换一个命名空间键渲染下一份 JSON 文本。"""
        if 自身.文本 is None:#没有缓存
            根={}#没有缓存
        else:#有缓存
            根=自身.解析(自身.文本)#从缓存解析
        根[命名空间]=段落#替换段落
        return json.dumps(根,indent=2,ensure_ascii=False)+'\n'#带换行的JSON

Config=配置模式#Cordis配置模式
默认=文件设置提供方#中文默认导出
default=文件设置提供方#Cordis默认导出

__all__=['文件设置提供方','配置模式','Config','默认','default']#公开面
