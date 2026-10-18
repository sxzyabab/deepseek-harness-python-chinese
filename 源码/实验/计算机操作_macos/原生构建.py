'源码检出时准备原生可执行文件，已安装包则直接使用现成文件'
import hashlib,json,os,threading
from ...基础设施.js特性 import PromiseEX as 期约
from ...工具.原子写入 import 带文件锁
from ...内核.智能体循环.中止与并发 import 中止控制器,合成信号
from ..计算机操作.原生客户端 import 若已中止则抛出

__all__=['原生架构','本机原生架构','原生可执行路径','是否源码包','构建原生可执行文件','准备原生可执行文件']

原生架构=str#arm64 或 x64

def 等到(任务):
    '阻塞到期约结算'
    完成=threading.Event()#结算
    盒子={}#结果
    def 成功(值=None):
        '兑现'
        盒子['值']=值#值
        完成.set()#唤醒
    def 失败(错误=None):
        '拒绝'
        盒子['错误']=错误#错误
        完成.set()#唤醒
    任务.然后(成功,失败)#接上
    完成.wait()#阻塞
    if '错误' in 盒子 and 盒子['错误'] is not None:#失败
        错误=盒子['错误']#错误
        if isinstance(错误,BaseException):#异常
            raise 错误#抛出
        raise RuntimeError(str(错误))#包成异常
    return 盒子.get('值')#成功值

def 在线程里(函数):
    '在后台线程跑同步工作，返回期约'
    任务=期约()#结果
    def 工作():
        '跑函数并结算期约'
        try:#成功
            任务.解决(函数())#兑现
        except Exception as 错误:#失败
            任务.拒绝(错误)#拒绝
    threading.Thread(target=工作,daemon=True).start()#不挡住进程退出
    return 任务#期约

def 本机原生架构(平台,架构):
    '只接受 darwin 上的 arm64 与 x64'
    if 平台!='darwin' or (架构!='arm64' and 架构!='x64'):#没有对应的原生实现
        raise Exception('Computer Use currently requires macOS on Apple silicon or Intel. Windows support is in development')#拒绝
    return 架构#原样返回

def 原生可执行路径(包根,架构):
    '这个包拥有的平台可执行文件'
    return os.path.join(包根,'native','bin','darwin-'+架构,'dsh-cua-native')#包内路径

def 判断源码包(包根):
    '仓库根的包名必须是 @deepseek-ai/dsh-root，且包路径落在 experimental/cua-macos'
    绝对=os.path.abspath(包根)#规范路径
    根=os.path.abspath(os.path.join(绝对,'..','..','..'))#仓库根
    if os.path.join(根,'packages','experimental','cua-macos')!=绝对:#不是源码树里的这个包
        return False#已安装包
    try:#读仓库清单
        文件=open(os.path.join(根,'package.json'),encoding='utf-8')#清单
        try:#读完即关
            清单=json.loads(文件.read())#解析
        finally:#关闭
            文件.close()#关闭
    except FileNotFoundError:#没有清单
        return False#不是源码包
    return isinstance(清单,dict) and 清单.get('name')=='@deepseek-ai/dsh-root'#根包名

def 是否源码包(包根):
    '源码包才构建，已安装包直接使用现成文件'
    def 工作():
        '判断这个包根是不是源码检出'
        return 判断源码包(包根)#布尔
    return 在线程里(工作)#期约

def 原子写字节(文件名,内容,权限):
    '用独占临时文件替换目标。内容是字节'
    父目录=os.path.dirname(文件名) or '.'#父目录
    os.makedirs(父目录,exist_ok=True)#父目录
    临时=文件名+'.'+os.urandom(6).hex()+'.tmp'#同目录临时文件
    已建=False#是否需要删
    try:#写入再替换
        标志=os.O_CREAT|os.O_EXCL|os.O_WRONLY#独占创建
        if os.name=='nt':#Windows 二进制
            标志|=os.O_BINARY#二进制
        描述符=os.open(临时,标志,权限)#权限打在新文件上
        已建=True#建成了
        try:#写完
            视图=内容#剩余
            while len(视图)>0:#还有
                写出=os.write(描述符,视图)#写
                视图=视图[写出:]#前进
        finally:#关闭描述符
            os.close(描述符)#关闭
        os.replace(临时,文件名)#同目录替换
        已建=False#已经搬走
    finally:#失败时删临时文件
        if 已建:#还在
            try:#删除
                os.unlink(临时)#删
            except OSError:#可能已经没了
                pass#忽略删除失败

def 读已有(路径):
    '没有文件时返回空。其他错误原样抛出'
    try:#读取
        文件=open(路径,'rb')#二进制
        try:#读完即关
            return 文件.read()#字节
        finally:#关闭
            文件.close()#关闭
    except FileNotFoundError:#还没有
        return None#空

def 可执行(路径):
    '文件必须存在并且可执行'
    描述符=os.open(路径,os.O_RDONLY)#不存在会抛
    os.close(描述符)#只检查存在
    if not os.access(路径,os.X_OK):#不可执行
        raise PermissionError('Computer Use native executable is not executable')#不把路径写进说明
    return 路径#可用

def 编译原生(规格,信号,可执行):
    '调用 swift build，并把产物按内容摘要留一份不可变副本'
    原生根=os.path.join(规格['packageRoot'],'native')#Swift 包
    暂存=os.path.join(原生根,'.build','runtime-'+规格['architecture'])#这次构建目录
    架构='x86_64' if 规格['architecture']=='x64' else 'arm64'#swift 的架构名
    句柄=规格['subprocess'].启动({#受管进程
        'argv':['/usr/bin/xcrun','swift','build','--package-path',原生根,'--scratch-path',暂存,'--configuration','release','--product','dsh-cua-native','--arch',架构],#构建
        'cwd':规格['packageRoot'],#包根
        'signal':信号,#取消
        'graceMs':规格['graceMs'],#宽限
        'stdio':{'stdin':'ignore','stdout':{'maxBytes':65536},'stderr':{'maxBytes':65536}},#有界输出
    })#启动
    try:#等退出事实
        结局=等到(句柄.done)#退出事实
    finally:#无论成败都收进程
        try:#先发终止
            句柄.终止()#终止
        finally:#再等整棵树
            等到(句柄.等待退出())#树退出
    若已中止则抛出(信号)#取消优先
    if 结局['exitCode']!=0 or 结局['signal'] is not None:#构建失败
        诊断=''#编译器输出
        收集=句柄.collected if isinstance(句柄.collected,dict) else {}#收集
        for 路 in ('stdout','stderr'):#两路
            读取器=收集.get(路)#这一路
            if 读取器 is not None:#有
                诊断+=读取器.自偏移读取(0).get('text') or ''#文本
        raise Exception('Computer Use native preparation failed ('+str(结局['exitCode'])+', '+str(结局['signal'])+'): '+诊断)#带上诊断
    建成=读已有(os.path.join(暂存,'release','dsh-cua-native'))#产物
    if 建成 is None:#没有产物
        raise Exception('Computer Use native preparation failed (None, None): ')#没有可执行文件
    先前=读已有(可执行)#已发布的副本
    若已中止则抛出(信号)#写之前取消
    if 先前!=建成:#内容变了才替换
        原子写字节(可执行,建成,0o755)#可执行位
    摘要=hashlib.sha256(建成).hexdigest()#内容地址
    运行时=os.path.join(原生根,'.build','prepared',规格['architecture'],摘要,'dsh-cua-native')#按摘要留存
    os.makedirs(os.path.dirname(运行时),exist_ok=True)#父目录
    留存=读已有(运行时)#已留存的副本
    if 留存 is not None and 留存!=建成:#摘要对不上内容
        raise Exception('Computer Use retained executable does not match its content digest')#拒绝
    若已中止则抛出(信号)#再写之前取消
    if 留存 is None:#还没留存
        原子写字节(运行时,建成,0o755)#写入
    return 可执行检查(运行时)#确认可执行

def 可执行检查(路径):
    '确认留存文件可执行后返回它'
    return 可执行(路径)#可执行

def 同步构建(规格):
    '在文件锁里编译。取消和构建超时时限共用'
    若已中止则抛出(规格['signal'])#开始前取消
    可执行=原生可执行路径(规格['packageRoot'],规格['architecture'])#发布路径
    os.makedirs(os.path.dirname(可执行),exist_ok=True)#父目录
    超时=中止控制器()#构建超时
    定时=threading.Timer(规格['timeoutMs']/1000.0,超时.中止,args=(TimeoutError('The operation was aborted due to timeout'),))#定时
    定时.daemon=True#不挡住退出
    定时.start()#开始
    try:#合并调用方取消和超时
        信号=合成信号(规格['signal'],超时.信号)#先到的胜出
        def 锁内():
            '持锁编译'
            return 编译原生(规格,信号,可执行)#编译
        return 带文件锁(可执行,锁内,{'waitMs':规格['timeoutMs']})#跨进程锁
    finally:#停掉定时器
        定时.cancel()#停

def 构建原生可执行文件(规格):
    '编译并留下按内容寻址的运行副本'
    def 工作():
        '在线程里构建'
        return 同步构建(规格)#路径
    return 在线程里(工作)#期约

def 同步准备(规格):
    '源码包才构建'
    if 判断源码包(规格['packageRoot']):#源码检出
        return 同步构建(规格)#构建
    可执行=原生可执行路径(规格['packageRoot'],规格['architecture'])#现成文件
    可执行检查(可执行)#必须已经可执行
    若已中止则抛出(规格['signal'])#检查之后取消
    return 可执行#路径

def 准备原生可执行文件(规格):
    '源码包才构建，已安装包直接使用现成文件'
    def 工作():
        '在线程里准备'
        return 同步准备(规格)#路径
    return 在线程里(工作)#期约
