'按调用方拥有的对象保留进程的 Node PTC 内存执行'
import codecs,math,os,sys,threading,weakref#输出解码、有限数、路径、冻结探测、线程与所有者
from ...基础设施.js特性 import PromiseEX as 期约#期约
from ...工具.超时 import 夹取超时#数值截止
from ...工具.值 import 快照json值,断言永不#绑定值与封闭联合
from ...沙盒.沙盒 import 沙箱不可用错误,分类运行器失败,是否运行器派生失败#沙箱失败
from .异常 import 节点ptc错误#本包异常
from .绑定 import 校验绑定#绑定名
from .通道 import json通道#控制通道
from .环境 import 启动环境名#启动环境
from .json线 import 编码ptcJson线,解码ptcJson线#线格式
from .输出json import 计量json字符串字节上限,截断json字符串字节#超限诊断
from .输出账本 import 输出账本#外层账本
from .输出流 import 排空输出#排空

__all__=['内存执行']#仅中文公开名

执行说明文案=('The program contains TypeScript REPL statements; only erasable syntax is accepted, with no enum or namespaces. '
    +'Type annotations are advisory. Top-level declarations and await are supported; top-level return is not supported. '
    +'Emit output with console.log(...) or a final lossless JSON expression. Only printed values and that final expression become program output. '
    +'Variables, functions, and imported modules remain in memory for this Agent across calls. Use await import(...) for modules. '
    +"Direct filesystem access follows this execution's sandbox policy; process.env starts empty. "
    +'Changing the session sandbox mode clears retained variables. An approved sandbox escalation runs in a separate temporary environment: '
    +'it cannot access retained variables, and its declarations are discarded afterward. Restart, Agent disposal, cancellation, timeout, output overflow, '
    +'or process failure clears the environment. If a variable is undefined, recreate it and reacquire its resources. State is not restored from the conversation, '
    +'and failed evaluations can leave earlier mutations in memory. Redeclaring an existing let, const, or class name fails; assign to a mutable binding or use a new name. '
    +'Await all tool calls; background callbacks cannot call tools after their evaluation ends. Await child-process completion before ending an evaluation; '
    +'raw subprocess output belongs to whichever evaluation is active when it arrives.')#面向模型的保留变量说明

保留变量已清除后缀='; retained variables were cleared'#失败文案后缀

class 中止信号:#本内核的取消
    '触发一次；原因留在 _异常'
    def __init__(自身):#未中止
        '创建一条取消通道'
        自身._事件=threading.Event()#旗标
        自身._异常=None#原因

    def 触发(自身,原因=None):#中止
        '只生效一次'
        if 自身._事件.is_set():#已经中止
            return#忽略
        if isinstance(原因,BaseException):#异常原因
            自身._异常=原因#记下
        自身._事件.set()#置位

def 已中止(信号):#读中止旗标
    '无信号视为未中止'
    if 信号 is None or not hasattr(信号,'_事件'):#没有旗标
        return False#未中止
    return 信号._事件.is_set()#已置位

def 取出消息(错误):#错误英文消息
    '异常取消息，其它强制转字符串'
    if isinstance(错误,BaseException) and len(错误.args)>0:#有消息
        return str(错误.args[0]) if type(错误.args[0]) is str else str(错误)#消息
    return str(错误)#强制转

def 是否记录(值):#非数组对象
    '是否为 dict'
    return type(值) is dict#只要 dict

def 延后(函数):#setImmediate
    '让已经排队的输出回调先走'
    threading.Thread(target=函数,daemon=True).start()#延后一拍

def 映到进程世界(文件系统,路径):#宿主路径到子进程世界
    '映射失败时不把路径写进消息'
    结果=文件系统.宿主路径转进程路径(路径)#后端映射
    if 结果 is None:#执行世界读不到
        raise 节点ptc错误('PTC runtime bootstrap is unavailable in the subprocess execution world')#不可用
    return 结果#进程路径

def 选出持久引导参数(文件系统,启动配置,最大消息字节):#持久 REPL 的引导参数
    'embedded 不能做持久执行；预装路径原样放进参数，不写进错误'
    种类=启动配置['kind']#启动种类
    if 种类=='embedded':#打包工人没有持久引导
        raise 节点ptc错误('Persistent PTC requires a node-script launch')#拒绝
    if 种类!='node-script':#封闭联合
        return 断言永不(启动配置)#不可达
    if 'bootstrapPath' in 启动配置 and 启动配置['bootstrapPath'] is not None:#显式预装
        return [启动配置['bootstrapPath'],str(最大消息字节)]#预装路径加上限
    if hasattr(sys,'frozen'):#打包可执行
        return [str(最大消息字节)]#只传上限
    入口=os.path.join(os.path.dirname(os.path.abspath(__file__)),'持久进程入口.py')#本包持久入口
    return [映到进程世界(文件系统,入口),str(最大消息字节)]#映射后的入口加上限

def 读取输出(流,接纳,失败):#一路 UTF-8 管道
    '阻塞读到结束；传输失败交给失败'
    解码器=codecs.getincrementaldecoder('utf-8')()#增量 UTF-8
    try:#读
        while True:#直到 EOF
            块=流.read(65536)#一块
            if not 块:#结束
                break#停
            文本=解码器.decode(块)#增量
            if len(文本)>0:#有文本
                接纳(文本)#接纳
        文本=解码器.decode(b'',True)#收尾
        if len(文本)>0:#有文本
            接纳(文本)#接纳
    except (OSError,ValueError,UnicodeDecodeError) as 错误:#传输
        失败(错误)#失败

def 关掉流(流):#关掉一路管道
    '已关闭再关不算失败'
    if 流 is None:#无
        return#无流
    try:#关
        流.close()#关
    except (OSError,ValueError) as 关闭错误:#已关
        _=关闭错误#不能替代清理结果

def 终止进程(句柄,宽限毫秒):#终止并排空
    '返回期约，解决值是两路输出是否都干净结束'
    回执=期约()#调用方
    def 工作():#后台终止
        '终止、等退出、排空，最后关掉管道'
        try:#终止
            句柄.终止()#升级终止
            def 忽略(错误):#孩子结局拒绝不挡清理
                '吞掉结局拒绝'
                return None#当成功
            def 已退出(忽略值=None):#进程已退出
                '排空后解决'
                try:#排空
                    出干净=排空输出(句柄.stdout,宽限毫秒)#stdout
                    错干净=排空输出(句柄.stderr,宽限毫秒)#stderr
                    关掉流(句柄.stdout)#关
                    关掉流(句柄.stderr)#关
                    回执.解决(bool(出干净 and 错干净))#是否干净
                except BaseException as 错误:#排空失败
                    关掉流(句柄.stdout)#仍关
                    关掉流(句柄.stderr)#仍关
                    回执.拒绝(错误)#拒绝
            def 退出失败(错误):#等退出失败
                '关掉后拒绝'
                关掉流(句柄.stdout)#关
                关掉流(句柄.stderr)#关
                回执.拒绝(错误)#拒绝
            期约.全部([句柄.done.捕获(忽略),句柄.等待退出()]).然后(已退出,退出失败)#结局与整树
        except BaseException as 错误:#终止本身失败
            关掉流(句柄.stdout)#仍关
            关掉流(句柄.stderr)#仍关
            回执.拒绝(错误)#拒绝
    threading.Thread(target=工作,daemon=True).start()#不阻塞调用方
    return 回执#清理期约

def 回复绑定(标识,函数,参数):#一次宿主绑定
    '不可用或有损时回 ok 为假的回复，不把异常抛出通道'
    回执=期约()#回复帧
    def 成功回复(值):#绑定结果
        '无损 JSON 才 ok'
        try:#快照
            if 值 is None:#JSON null
                快照=None#null
            else:#其它值
                快照=快照json值(值)#分离
                if 快照 is None:#有损
                    raise 节点ptc错误('binding resolution must be lossless JSON')#拒绝
            回执.解决({'type':'reply','id':标识,'ok':True,'value':编码ptcJson线(快照)})#成功帧
        except BaseException as 错误:#快照或编码失败
            回执.解决({'type':'reply','id':标识,'ok':False,'message':取出消息(错误)})#失败帧
    def 失败回复(错误):#绑定拒绝
        '失败也是一条回复'
        回执.解决({'type':'reply','id':标识,'ok':False,'message':取出消息(错误)})#失败帧
    try:#调用
        if not callable(函数):#这次求值没有这个绑定
            raise 节点ptc错误('binding is unavailable in this evaluation; reacquire the current tool')#拒绝
        结果=函数(参数)#执行
    except BaseException as 错误:#同步失败
        失败回复(错误)#回复
        return 回执#失败帧
    if hasattr(结果,'然后'):#异步绑定
        结果.然后(成功回复,失败回复)#等它
    else:#同步结果
        成功回复(结果)#立刻回复
    return 回执#回复帧

class 持久输出账本(输出账本):#保留变量被清掉时的超限文案
    '超限诊断改成保留变量已被清空'
    def __init__(自身,最大字节,溢出消息):#记下硬顶与文案
        '文案必须是 ASCII，字节按字符数加引号计'
        super().__init__(最大字节)#父账本
        自身._溢出消息=溢出消息#固定诊断

    def 构造超限失败(自身,日志):#显式输出上限失败
        '保留能放下的日志前缀'
        全文=自身._溢出消息#固定诊断
        消息字节=len(全文)+2#ASCII 加引号
        保留=[]#能放下的前缀
        保留字节=2#[]
        日志预算=自身._最大字节-消息字节#留给日志
        for 文本 in 日志:#逐条
            分隔=1 if len(保留)>0 else 0#逗号
            可用=日志预算-保留字节-分隔#本条可用
            串字节=计量json字符串字节上限(文本,可用)#整条
            if 串字节 is not None:#整条放下
                保留.append(文本)#收下
                保留字节+=串字节+分隔#入账
                continue#下一条
            前缀=截断json字符串字节(文本,可用)#截前缀
            if len(前缀)>0:#有前缀
                前缀字节=计量json字符串字节上限(前缀,可用)#前缀字节
                if 前缀字节 is None:#截断保证可放入
                    raise 节点ptc错误('output ledger produced an oversized log prefix')#账本自相矛盾
                保留.append(前缀)#收下前缀
                保留字节+=前缀字节+分隔#入账
            break#截断后停止
        可用消息=自身._最大字节-保留字节#留给消息
        消息=截断json字符串字节(全文,可用消息)#必要时截消息
        return {'logs':保留,'error':{'kind':'output-limit','message':消息}}#超限结果

def 持久输出(最大字节):#这次求值的账本
    '超限文案说明保留变量已被清空'
    return 持久输出账本(最大字节,'retained variables were cleared; outer output exceeded '+str(最大字节)+' bytes')#账本

class 内核:#一个受管进程
    '可变的程序状态只属于这个进程'
    def __init__(自身,上下文,配置,政策,进程表):#记下并登记失效
        '登记的释放回调就是本内核的释放'
        自身.上下文=上下文#宿主
        自身.配置=配置#已校验界限
        自身.政策=dict(政策)#这份文件政策的拷贝
        自身.注销=进程表.登记(政策,自身.释放)#政策变更时释放
        自身.已隔离=None#沙箱包装
        自身.句柄=None#子进程
        自身.通道=None#控制通道
        自身.活动=None#当前求值
        自身.运行中=False#已接纳、清理尚未计入结果
        自身.清理未完=False#停止尚未完成
        自身.就绪=False#已经收到 ready
        自身.序号=0#求值 id
        自身.下一调用=1#绑定调用 id
        自身.标准错误=''#尾部 stderr
        自身.已停=None#停止期约
        自身.启动中=None#启动期约
        自身.退出事实=None#进程已退出
        自身.已关=False#不再接纳
        自身.控制器=中止信号()#解析可执行文件与隔离用
        自身.锁=threading.Lock()#活动与停止只结算一次

    def 断言空闲(自身):#同一所有者不能并发
        '清理未完成时必须先释放所有者'
        if 自身.运行中:#已经有一次在跑
            raise 节点ptc错误('persistent PTC does not accept concurrent runs for one state owner')#拒绝
        if 自身.清理未完:#上次清理还没完
            raise 节点ptc错误('persistent PTC environment cleanup is incomplete; release the owner before running another program')#拒绝

    def 运行(自身,规格,绑定,代码):#一次求值
        '返回期约，解决为带沙箱事实的运行结果'
        自身.运行中=True#占住
        沙箱={'mode':自身.政策['mode'],'denied':False}#沙箱事实
        回执=期约()#调用方
        def 交还(结果=None,错误=None):#无论成败都放开占位
            '成功时写上沙箱事实'
            try:#写事实
                if 错误 is not None:#求值期约被拒绝
                    回执.拒绝(错误)#原错误
                    return#已拒绝
                if 自身.已隔离 is not None:#有强制包装
                    沙箱['enforcement']=自身.已隔离['enforcement']#记下
                    结果错误=结果['error'] if 'error' in 结果 else None#运行错误
                    拒绝=False#默认没被文件政策拒绝
                    if 结果错误 is None or 结果错误.get('kind')!='sandbox-unavailable':#沙箱不可用本身不是文件拒绝
                        消息=结果错误['message'].lower() if 结果错误 is not None and 'message' in 结果错误 else ''#小写
                        for 签名 in 自身.已隔离['denialSignatures']:#逐条
                            if 签名.lower() in 消息:#命中
                                拒绝=True#拒绝
                                break#停
                    沙箱['denied']=拒绝#文件拒绝
                带沙箱=dict(结果)#拷贝
                带沙箱['sandbox']=沙箱#沙箱事实
                回执.解决(带沙箱)#解决
            finally:#放开
                自身.运行中=False#允许下一次
        def 成功(结果):#求值解决
            '写上沙箱事实'
            交还(结果,None)#成功
        def 失败(错误):#求值拒绝
            '原样拒绝'
            交还(None,错误)#失败
        try:#求值
            自身.求值(规格,绑定,代码).然后(成功,失败)#等清理后的结果
        except BaseException as 错误:#求值同步抛出
            交还(None,错误)#拒绝
        return 回执#结果

    def 求值(自身,规格,绑定,代码):#一次求值的结果期约
        '进程已经退出时先停掉再返回失败，不再复用残留状态'
        回执=期约()#结果
        if 自身.退出事实 is not None:#进程已经死了
            输出=持久输出(自身.配置['maxOutputBytes'])#账本
            if 已中止(规格['signal'] if 'signal' in 规格 else None):#调用方取消
                失败={'kind':'abort','message':'execution canceled'+保留变量已清除后缀}#取消
            else:#进程退出
                失败={'kind':'worker-exit','message':自身.退出消息(自身.退出事实)+保留变量已清除后缀}#退出
            def 已停(忽略=None):#停止完成
                '清理成功仍返回原来的失败'
                回执.解决(输出.结算失败([],失败))#失败结果
            def 停失败(错误):#停止失败
                '改报清理失败'
                回执.解决(输出.结算失败([],{'kind':'worker-exit','message':'managed process cleanup failed: '+取出消息(错误)}))#清理失败
            自身.停止().然后(已停,停失败)#先停
            return 回执#结果
        自身.标准错误=''#这次重新积累
        输出=持久输出(自身.配置['maxOutputBytes'])#账本
        日志=[]#已接纳日志
        自身.序号+=1#新 id
        求值标识=自身.序号#这次
        空间列表=[]#boot 命名空间
        for 项 in 绑定.values():#按插入序
            一条={'global':项['global'],'names':list(项['functions'].keys())}#全局与名
            if 'errorClass' in 项 and 项['errorClass'] is not None:#有错误类
                一条['errorClass']=项['errorClass']#带上
            空间列表.append(一条)#收下
        数据={'code':代码,'maxOutputBytes':自身.配置['maxOutputBytes'],'namespaces':空间列表}#boot
        停=threading.Event()#停掉截止监视
        定时器盒=[None]#墙钟
        求值={'id':求值标识,'数据':数据,'规格':规格,'绑定':绑定,'未决数':0,'未决字节':0,'日志':日志,'输出':输出}#这次求值
        def 结束(错误=None,值=None,丢弃=False):#结算这次求值
            '输出上限、丢弃或没有所有者时停掉进程'
            with 自身.锁:#只结算一次
                if 自身.活动 is not 求值:#不是当前
                    return#忽略
                自身.活动=None#摘掉
            停.set()#停监视
            if 定时器盒[0] is not None:#有墙钟
                定时器盒[0].cancel()#取消
            if 错误 is not None and 错误.get('kind')=='output-limit':#触顶走超限结果
                结局=输出.构造超限失败(日志)#超限
            elif 错误 is not None:#失败
                结局=输出.结算失败(日志,错误)#失败
            else:#成功
                结局=输出.结算成功(日志,值)#成功
            无所有者='stateOwner' not in 规格 or 规格['stateOwner'] is None#临时进程
            结果错误=结局['error'] if 'error' in 结局 else None#结算后的错误
            要停=丢弃 or 无所有者 or (结果错误 is not None and 结果错误.get('kind')=='output-limit')#这些都清掉保留状态
            if 要停:#停进程
                清理=自身.停止()#停止期约
            else:#留下进程
                清理=期约()#当作已经排空
                清理.解决(True)#干净
            def 已清理(排空了):#清理结束
                '没排干净则改报 worker-exit'
                if 排空了:#干净
                    回执.解决(结局)#原结局
                else:#输出没关干净
                    回执.解决(输出.结算失败(日志,{'kind':'worker-exit','message':'managed process exited but its output did not drain cleanly'}))#改报
            def 清理失败(失败值):#清理抛错
                '改报清理失败'
                回执.解决(输出.结算失败(日志,{'kind':'worker-exit','message':'managed process cleanup failed: '+取出消息(失败值)}))#清理失败
            清理.然后(已清理,清理失败)#结果在清理之后
        求值['结束']=结束#给定时器与帧
        def 接纳(文本):#一条外层文本
            '账本拒绝时把这条放进日志再结束'
            if not 输出.接纳日志(文本,日志):#越顶
                日志.append(文本)#超限结果要看到这条
                结束({'kind':'output-limit','message':'output limit exceeded'},None,True)#丢弃
        求值['接纳']=接纳#输出接纳
        自身.活动=求值#当前
        if 规格['timeoutMs'] is not None:#有墙钟
            def 到期():#到点
                '超时并清掉保留变量'
                结束({'kind':'timeout','message':'execution deadline reached ('+str(规格['timeoutMs'])+'ms)'+保留变量已清除后缀},None,True)#丢弃
            定时器=threading.Timer(规格['timeoutMs']/1000.0,到期)#定时器
            定时器.daemon=True#守护
            定时器盒[0]=定时器#供结束取消
            定时器.start()#武装
        信号=规格['signal'] if 'signal' in 规格 else None#调用方取消
        if 信号 is not None:#要监视
            def 监视中止():#等到中止
                '中止则清掉保留变量'
                while not 停.is_set():#求值还没结束
                    if 已中止(信号):#取消
                        结束({'kind':'abort','message':'execution canceled'+保留变量已清除后缀},None,True)#丢弃
                        return#结束
                    停.wait(0.05)#短等
            threading.Thread(target=监视中止,daemon=True).start()#监视
        if 信号 is not None and 已中止(信号):#开始前已经取消
            结束({'kind':'abort','message':'execution canceled'+保留变量已清除后缀},None,True)#丢弃
        elif 自身.就绪:#进程已在
            自身.派发(求值)#直接跑
        else:#还要启动
            自身.启动中=自身.开始(规格['cwd'])#启动期约
            def 启动失败(错误):#启动失败
                '沙箱或运行器派生失败单独分类'
                种类='worker-exit'#默认
                if isinstance(错误,沙箱不可用错误):#沙箱
                    种类='sandbox-unavailable'#沙箱
                elif 自身.已隔离 is not None and 是否运行器派生失败(错误,自身.已隔离['argv'][0],规格['cwd']):#运行器
                    种类='sandbox-unavailable'#沙箱
                自身.失败(种类,取出消息(错误))#清掉保留变量
            自身.启动中.捕获(启动失败)#不让启动失败变成未处理拒绝
        return 回执#清理完成后解决

    def 释放(自身):#丢掉保留状态
        '中止当前求值并等待进程停下'
        if 自身.活动 is not None:#还有求值
            自身.活动['结束']({'kind':'abort','message':'PTC environment disposed'+保留变量已清除后缀},None,True)#丢弃
        return 自身.停止()#等待

    def 停止(自身):#关掉进程
        '失败时清掉停止槽，调用方可以再停一次'
        with 自身.锁:#只创建一次
            if 自身.已停 is not None:#已经在停
                return 自身.已停#同一条
            自身.已关=True#不再接纳
            自身.清理未完=True#清理中
            回执=期约()#调用方
            自身.已停=回执#占槽
        自身.控制器.触发(节点ptc错误('The operation was aborted'))#取消启动
        if 自身.通道 is not None:#有通道
            自身.通道.关闭()#关
        启动期约=自身.启动中#可能还在启动
        if 启动期约 is None:#没有启动
            启动期约=期约()#当作已结束
            启动期约.解决()#成功
        def 吞启动(错误):#启动失败不挡停止
            '吞掉'
            return None#当成功
        def 接到终止(忽略=None):#启动已结束
            '没有进程则视为已排空'
            if 自身.句柄 is None:#没启动出来
                已排空(True)#干净
                return None#不再链式
            终止进程(自身.句柄,自身.配置['graceMs']).然后(已排空,停止失败)#终止
            return None#回执由已排空解决
        def 已排空(排空了):#终止完成
            '注销跟踪；没排干净只记日志'
            if 自身.注销 is not None:#有摘除
                自身.注销()#摘掉
            自身.清理未完=False#清理完成
            if not 排空了:#输出没关干净
                自身.上下文.日志.警告('persistent Node process exited but its output did not drain cleanly')#日志
            回执.解决(bool(排空了))#结果
        def 停止失败(错误):#终止失败
            '清掉停止槽再拒绝'
            with 自身.锁:#允许再停
                自身.已停=None#可再试
            回执.拒绝(错误)#拒绝
        启动期约.捕获(吞启动).然后(接到终止,停止失败)#等启动再终止
        return 回执#停止期约

    def 失败(自身,种类,消息):#协议、退出或启动失败
        '有求值就结束它并清掉保留变量；否则停进程'
        if 自身.活动 is not None:#有求值
            自身.活动['结束']({'kind':种类,'message':消息+保留变量已清除后缀},None,True)#丢弃
            return#求值会停进程
        if not 自身.已关:#还没人停
            自身.上下文.日志.警告(消息)#没有求值可归
        def 停止失败(错误):#停的时候又失败
            '再记一条'
            自身.上下文.日志.警告(取出消息(错误))#日志
        自身.停止().捕获(停止失败)#尽量停

    def 派发(自身,求值):#把程序交给已就绪的进程
        '发送失败按协议失败处理'
        if 自身.通道 is None:#没有通道
            return#无法派发
        def 发送失败(错误):#run 帧失败
            '协议失败'
            自身.失败('protocol',取出消息(错误))#清掉
        try:#编码并发送
            自身.通道.发送帧({'type':'run','id':求值['id'],'cwd':求值['规格']['cwd'],'data':求值['数据']}).捕获(发送失败)#run
        except (节点ptc错误,OSError,ValueError,TypeError) as 错误:#编码失败
            自身.失败('protocol',取出消息(错误))#清掉

    def 退出消息(自身,结局):#进程退出文案
        '带退出码、信号，以及还留着的标准错误尾'
        尾=''#无尾
        if 自身.标准错误:#有尾
            尾=': '+自身.标准错误#附上
        return 'Node process exited ('+str(结局['exitCode'])+', signal '+str(结局['signal'])+')'+尾#文案

    def 开始(自身,目录):#拉起持久进程
        '返回期约，进程与通道装好后解决；中途已关则直接解决'
        回执=期约()#启动回执
        try:#解析、隔离、启动
            可执行=自身.上下文.subprocess.解析可执行文件(自身.配置['launch']['executable'],None,自身.控制器)#解析
            if 自身.已关:#停止赢了
                回执.解决()#不再启动
                return 回执#结束
            堆标志='--max-old-space-size='+str(自身.配置['maxOldGenerationSizeMb'])#堆上限
            参数表=[可执行,堆标志]#argv0 与堆
            参数表.extend(选出持久引导参数(自身.上下文.fs,自身.配置['launch'],自身.配置['maxMessageBytes']))#持久引导
            政策=自身.政策#这份政策
            if 政策['mode']=='danger-full-access':#不隔离
                自身.已隔离=None#无包装
            else:#隔离
                自身.已隔离=自身.上下文.sandbox.隔离(参数表,dict(政策),自身.控制器)#包装 argv
            if 自身.已关:#隔离期间被关掉
                回执.解决()#不再启动
                return 回执#结束
            环境={}#墓碑表
            for 键 in os.environ.keys():#父环境
                if 键.upper() not in 启动环境名 and 键.upper()!='ELECTRON_RUN_AS_NODE':#非启动名且非 Electron 选择器
                    环境[键]=None#删除墓碑
            启动参数表=自身.已隔离['argv'] if 自身.已隔离 is not None else 参数表#最终 argv
            句柄=自身.上下文.subprocess.启动({'argv':启动参数表,'cwd':目录,'env':环境,'stdio':{'stdin':'ignore','stdout':'pipe','stderr':'pipe','control':'pipe'},'graceMs':自身.配置['graceMs']})#启动
            自身.句柄=句柄#记下
            if 句柄.control is None or 句柄.stdout is None or 句柄.stderr is None:#缺管
                raise 节点ptc错误('subprocess provider did not supply persistent PTC pipes')#拒绝
            def 管道失败(错误):#stdout/stderr
                '传输失败'
                自身.失败('worker-exit',取出消息(错误))#清掉
            def 接纳标准输出(文本):#stdout
                '归到当前求值'
                if 自身.活动 is not None:#有求值
                    自身.活动['接纳'](文本)#接纳
            def 接纳标准错误(文本):#stderr 另留尾
                '保留尾部再接纳'
                自身.标准错误=(自身.标准错误+文本)[-自身.配置['maxOutputBytes']:]#尾部
                if 自身.活动 is not None:#有求值
                    自身.活动['接纳'](文本)#接纳
            threading.Thread(target=读取输出,args=(句柄.stdout,接纳标准输出,管道失败),daemon=True).start()#stdout
            threading.Thread(target=读取输出,args=(句柄.stderr,接纳标准错误,管道失败),daemon=True).start()#stderr
            def 通道失败(错误,种类):#通道失败
                '协议失败立刻结束；传输失败则在还没看到退出时终止进程'
                if 种类=='protocol':#协议
                    自身.失败('protocol',取出消息(错误))#协议
                    return#完
                def 稍后终止():#让退出回调先走
                    '还活着才终止'
                    if not 自身.已关 and 自身.退出事实 is None:#还没退出
                        try:#终止
                            句柄.终止()#终止
                        except (节点ptc错误,OSError,ValueError) as 终止错误:#终止失败
                            自身.失败('worker-exit',取出消息(终止错误))#清掉
                延后(稍后终止)#延后
            自身.通道=json通道(句柄.control,自身.配置['maxMessageBytes'],自身.接收,通道失败)#分帧
            def 进程已退出(结局):#孩子退出
                '先排空，再分类'
                自身.退出事实=结局#记下
                排空输出(句柄.stdout,自身.配置['graceMs'])#stdout
                排空输出(句柄.stderr,自身.配置['graceMs'])#stderr
                def 稍后分类():#终态帧可能已经排在退出前面
                    '未关闭才分类'
                    if 自身.已关:#已经在停
                        return#忽略
                    种类='worker-exit'#默认
                    if 自身.已隔离 is not None and 分类运行器失败(结局['exitCode'],自身.标准错误,自身.已隔离['runnerFailureRules']) is not None:#运行器
                        种类='sandbox-unavailable'#沙箱
                    自身.失败(种类,自身.退出消息(结局))#清掉
                延后(稍后分类)#延后
            def 进程等待失败(错误):#spawn 或等待失败
                '按 worker-exit'
                自身.失败('worker-exit',取出消息(错误))#清掉
            句柄.done.然后(进程已退出,进程等待失败)#监视退出
            回执.解决()#通道已装上
        except BaseException as 错误:#启动失败
            回执.拒绝(错误)#拒绝
        return 回执#启动期约

    def 接收(自身,原始,字节):#控制帧
        '分派 ready、日志、终态与绑定调用'
        if not 是否记录(原始):#非对象
            自身.失败('protocol','invalid persistent PTC frame')#协议
            return#完
        求值=自身.活动#当前
        if 求值 is None:#没有求值
            自身.失败('protocol','frame arrived without an active PTC evaluation')#协议
            return#完
        if not 自身.就绪:#等 ready
            if 原始.get('type')!='ready':#不是
                自身.失败('protocol','expected persistent PTC readiness')#协议
                return#完
            自身.就绪=True#就绪
            自身.派发(求值)#现在才能跑
            return#完
        if 原始.get('id')!=求值['id'] or not 是否记录(原始.get('payload')):#不是这次求值
            自身.失败('protocol','frame does not belong to the active PTC evaluation')#协议
            return#完
        载荷=原始['payload']#程序帧
        种类=载荷.get('type')#帧类
        if 种类=='log':#日志
            if type(载荷.get('text')) is str:#必须字符串
                求值['接纳'](载荷['text'])#接纳
            else:#畸形
                自身.失败('protocol','invalid persistent PTC log')#协议
            return#完
        if 种类=='output-limit':#程序侧触顶
            def 稍后触顶():#让旁边的标准输出先入账
                '触顶并丢弃'
                求值['结束']({'kind':'output-limit','message':'output limit exceeded'},None,True)#丢弃
            延后(稍后触顶)#延后
            return#完
        if 种类=='done':#终态
            if 'error' in 载荷 and 载荷['error'] is not None:#失败
                错=载荷['error']#错误
                if not 是否记录(错) or type(错.get('message')) is not str or 错.get('kind') not in ('exception','invalid-output','output-limit'):#畸形
                    自身.失败('protocol','invalid persistent PTC failure')#协议
                    return#完
                失败={'kind':错['kind'],'message':错['message']}#失败
                def 稍后失败():#让旁边的标准输出先入账
                    '输出上限才丢弃保留状态'
                    求值['结束'](失败,None,失败['kind']=='output-limit')#终态
                延后(稍后失败)#延后
                return#完
            if 'value' not in 载荷:#缺席完成
                值=None#无完成值
                失败=None#成功
            else:#有完成值
                值=解码ptcJson线(载荷['value'])#重建
                if 值 is None:#有损，含根上的 JSON null 与畸形线
                    失败={'kind':'invalid-output','message':'program completion must be lossless JSON'}#有损
                    值=None#无值
                else:#无损
                    失败=None#成功
            def 稍后完成():#让旁边的标准输出先入账
                '成功或有损完成'
                求值['结束'](失败,值)#不因有损而丢弃，除非结算变成输出上限
            延后(稍后完成)#延后
            return#完
        if 种类=='call':#绑定调用
            if 载荷.get('id')!=自身.下一调用 or type(载荷.get('global')) is not str or type(载荷.get('name')) is not str:#身份
                自身.失败('protocol','invalid persistent PTC binding identity')#协议
                return#完
            自身.下一调用+=1#推进
            参数=解码ptcJson线(载荷.get('args'))#参数
            if 参数 is None:#有损
                自身.失败('protocol','binding arguments must be lossless JSON')#协议
                return#完
            求值['未决数']+=1#先加次数
            if 求值['未决数']>自身.配置['maxPendingCalls']:#次数超限；字节不加
                自身.失败('protocol','pending binding calls exceed configured limits')#协议
                return#完
            求值['未决字节']+=字节#再加字节
            if 求值['未决字节']>自身.配置['maxMessageBytes']:#字节超限
                自身.失败('protocol','pending binding calls exceed configured limits')#协议
                return#完
            函数表=None#该全局的函数
            if 载荷['global'] in 求值['绑定']:#声明过
                函数表=求值['绑定'][载荷['global']]['functions']#函数表
            函数=None#未声明
            if 函数表 is not None and 载荷['name'] in 函数表:#自有名
                函数=函数表[载荷['name']]#取出
            调用标识=载荷['id']#回复 id
            帧字节=字节#这条帧的字节
            def 已回复(回复):#绑定已回复
                '先还名额，当前求值还在才把回复写回'
                求值['未决数']-=1#减一
                求值['未决字节']-=帧字节#减字节
                if 自身.活动 is 求值 and 自身.通道 is not None:#还是这次
                    def 回复失败(错误):#回复帧失败
                        '协议失败'
                        自身.失败('protocol',取出消息(错误))#清掉
                    自身.通道.发送帧(回复).捕获(回复失败)#回复
            def 回复抛错(错误):#回复过程失败
                '还名额并按协议失败'
                求值['未决数']-=1#减一
                求值['未决字节']-=帧字节#减字节
                自身.失败('protocol',取出消息(错误))#清掉
            回复绑定(调用标识,函数,参数).然后(已回复,回复抛错)#异步回复
            return#完
        自身.失败('protocol','unknown persistent PTC message')#未知

class 内存执行:#沙箱里尽力保留的状态
    '重启、释放和被打断的执行都会清掉它'
    def 执行说明(自身):#保留变量的用法
        '附加到 run_code 模式的用法说明'
        return 执行说明文案#固定英文

    def __init__(自身,上下文,配置,进程表):#挂上拆除
        'embedded 启动不能做持久执行'
        if 配置['launch']['kind']=='embedded':#没有 node 脚本引导
            raise 节点ptc错误('Persistent PTC requires a node-script launch')#拒绝
        自身.上下文=上下文#宿主
        自身.配置=配置#已校验界限
        自身.进程表=进程表#政策失效
        自身.所有者表=weakref.WeakKeyDictionary()#所有者到内核
        自身.内核集合=set()#全部内核
        自身.已释放=False#拆除后拒绝
        def 登记清理():#纤程拆除
            '丢掉全部保留环境'
            def 拆除():#拆除器
                '返回全部内核释放后的期约'
                自身.已释放=True#标记
                内核列表=list(自身.内核集合)#快照
                回执=期约()#拆除回执
                if len(内核列表)==0:#没有
                    自身.内核集合.clear()#清空
                    回执.解决()#完成
                    return 回执#已完成
                结果=[None]*len(内核列表)#按快照顺序
                剩余=[len(内核列表)]#还没结算
                def 记下(下标,状态,值):#一条
                    '有拒绝则抛第一个'
                    结果[下标]=(状态,值)#记下
                    剩余[0]-=1#减一
                    if 剩余[0]!=0:#未齐
                        return#等
                    自身.内核集合.clear()#清空
                    for 状态项,值项 in 结果:#输入顺序
                        if 状态项=='rejected':#第一个失败
                            回执.拒绝(值项)#拒绝
                            return#结束
                    回执.解决()#都成功
                下标=0#顺序
                for 内核 in 内核列表:#逐个
                    def 成功(值=None,序号=下标):#释放成功
                        '记成功'
                        记下(序号,'fulfilled',值)#成功
                    def 失败(错误,序号=下标):#释放失败
                        '记失败'
                        记下(序号,'rejected',错误)#失败
                    内核.释放().然后(成功,失败)#等它
                    下标+=1#下一个
                return 回执#拆除期约
            return 拆除#拆除器
        上下文.副作用(登记清理,'Persistent PTC environments')#登记

    def 解析(自身,请求):#保留 REPL 的政策、目录与截止
        """补全文件政策、目录和截止。
        请求含程序、绑定、所有者、目录与经过时间预算。
        返回带上所选文件政策的输入
        """
        if 自身.已释放:#已拆
            raise 节点ptc错误('persistent PTC: resolve after disposal')#拒绝
        if 'sandboxPolicy' in 请求 and 请求['sandboxPolicy'] is not None:#请求自带
            政策=请求['sandboxPolicy']#用请求
        else:#部署解析
            政策=自身.上下文.sandboxPolicy.解析()#默认政策
        if 'cwd' in 请求 and 请求['cwd'] is not None:#请求目录
            目录=请求['cwd']#用请求
        else:#政策根
            目录=政策['workspaceRoot']#工作区根
        if not os.path.isabs(目录):#必须绝对
            raise 节点ptc错误('persistent PTC: cwd must be absolute')#拒绝
        规格=dict(请求)#拷贝
        规格['sandboxPolicy']=政策#已解析政策
        规格['cwd']=目录#绝对目录
        if 'timeoutMs' in 请求 and 请求['timeoutMs'] is None:#显式不设截止
            规格['timeoutMs']=None#空截止
        else:#数值截止
            请求截止=请求['timeoutMs'] if 'timeoutMs' in 请求 else None#缺席用默认
            规格['timeoutMs']=夹取超时(请求截止,自身.配置['timeoutMs'],自身.配置['maxTimeoutMs'],'persistent PTC timeoutMs')#钳
        return 规格#已解析

    def 运行(自身,规格):#用所有者的进程，或没有所有者时用临时进程
        """求值语句。同一所有者的并发调用会被拒绝。
        规格是已解析请求。
        返回期约，解决为日志、最终 JSON 表达式或结构化失败
        """
        if 自身.已释放:#已拆
            raise 节点ptc错误('persistent PTC: run after disposal')#拒绝
        if 'timeoutMs' not in 规格:#缺截止
            截止非法=True#必须已解析
        else:#有截止
            截止=规格['timeoutMs']#数值或空
            截止非法=截止 is not None and (type(截止) is bool or not isinstance(截止,(int,float)) or not math.isfinite(截止) or 截止<=0 or 截止>自身.配置['maxTimeoutMs'])#非正、非有限或超上限
        if 'sandboxPolicy' not in 规格 or 规格['sandboxPolicy'] is None or not os.path.isabs(规格['cwd']) or 截止非法:#缺已解析输入
            raise 节点ptc错误('persistent PTC: run requires resolved inputs with a sandbox policy')#拒绝
        绑定=校验绑定(规格)#绑定表
        内核=None#已有内核
        if 'stateOwner' in 规格 and 规格['stateOwner'] is not None:#有所有者
            内核=自身.所有者表.get(规格['stateOwner'])#按身份
        if 内核 is not None:#已有
            内核.断言空闲()#不能并发，清理未完也不行
        if 内核 is not None and not 内核.已关:#还活着
            政策=规格['sandboxPolicy']#这次的政策
            if 内核.政策.get('mode')!=政策.get('mode') or 内核.政策.get('workspaceRoot')!=政策.get('workspaceRoot') or 内核.政策.get('sessionId')!=政策.get('sessionId'):#政策变了
                raise 节点ptc错误('persistent PTC: release the retained environment before changing its sandbox policy')#拒绝
        代码=规格['program']#Python 宿主不擦 TypeScript 类型
        if 内核 is None or 内核.已关:#需要新进程
            if 内核 is not None:#旧的已关
                自身.内核集合.discard(内核)#不再拆除它
            内核=内核类(自身.上下文,自身.配置,dict(规格['sandboxPolicy']),自身.进程表)#新内核
            自身.内核集合.add(内核)#拆除时等它
            if 'stateOwner' in 规格 and 规格['stateOwner'] is not None:#有所有者
                自身.所有者表[规格['stateOwner']]=内核#按身份记住
        无所有者='stateOwner' not in 规格 or 规格['stateOwner'] is None#临时进程
        def 跑完(结果):#成功
            '临时进程结束后不再跟踪'
            if 无所有者:#没有所有者
                自身.内核集合.discard(内核)#求值自己会停进程
            return 结果#原结果
        def 跑失败(错误):#失败
            '临时进程结束后再拒绝'
            if 无所有者:#没有所有者
                自身.内核集合.discard(内核)#不再跟踪
            失败=期约()#拒绝回执
            失败.拒绝(错误)#原错误
            return 失败#继续拒绝
        return 内核.运行(规格,绑定,代码).然后(跑完,跑失败)#结果

    def 释放(自身,所有者):#释放保留状态
        """释放保留状态并等待进程清理。
        所有者必须是交给运行的同一个对象。
        返回期约，进程与输出流停下后解决
        """
        回执=期约()#调用方
        内核=自身.所有者表.get(所有者)#按身份
        if 内核 is None:#没有
            回执.解决()#无事
            return 回执#已完成
        def 成功(忽略=None):#内核已停
            '仍是这个所有者的内核才摘掉'
            if 自身.所有者表.get(所有者) is 内核:#没被换掉
                自身.所有者表.pop(所有者,None)#摘掉
            自身.内核集合.discard(内核)#不再跟踪
            回执.解决()#完成
        def 失败(错误):#清理失败
            '原样拒绝'
            回执.拒绝(错误)#拒绝
        内核.释放().然后(成功,失败)#等待
        return 回执#清理期约

内核类=内核#运行方法里的局部名占用了类名
