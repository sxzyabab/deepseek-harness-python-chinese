"""工作线程代码运行时：每次用全新工作线程跑一份程序，并经消息端口桥接绑定。这是隔离，不是安全边界：尽管有堆/忙时/墙钟预算以及终止，模型代码仍有与 bash 相当的信任。"""
import queue,re,threading,time#队列、标识符、线程与墙钟
from ...依赖.schemastery import 数字字段#配置字段
from ...工具.超时 import 定时器延迟上限毫秒,已中止,若已中止则抛出,等待中止#定时器上限与中止
from ..代码运行时 import (#运行时基类与保留名
    代码运行时,#基类
    保留绑定全局,#后端自有槽
    可移植保留字,#跨语言保留字
    保留错误成员,#保留错误成员
    双下划线成员,#dunder成员
)#来自code_runtime
from ...内核.会话 import 快照json值#会话侧无损JSON快照
from .输出json import (#JSON字节账本
    json字符串字节上限,#字符串计量
    json值字节上限,#值计量
    截断json字符串字节,#截断
)#来自输出json
from .工作线程json import (#扁平线路编解码
    编码工作线程json,#编码
    解码工作线程json,#解码
)#来自工作线程json
from .工作线程入口 import 工作线程入口#工作线程入口

标识符=re.compile(r'^[A-Za-z_][A-Za-z0-9_]*$')#可移植标识符
事件循环采样间隔毫秒=25#ELU采样间隔毫秒（内部节拍，不是配置）
最小输出字节=4#能表示已计数载荷的最小上限：空日志数组加空JSON失败消息

配置模式={#schemastery配置模式
    'computeMs':数字字段(默认值=60000),#默认忙时60s
    'maxWallMs':数字字段(默认值=600000),#默认墙钟600s
    'maxOutputBytes':数字字段(默认值=67108864),#默认64MiB外层输出
    'maxOldGenerationSizeMb':数字字段(默认值=512),#默认512MiB老生代（Python侧作信息上限）
}#结束配置模式

__all__=[#仅中文公开名；Cordis 槽英文别名不入表
    '标识符','事件循环采样间隔毫秒','最小输出字节','配置模式',
    '消息于','解析工作线程消息','输出账本','队列端口','工作线程代码运行时','默认',
]#公开面结束

def 消息于(错误):#抛出值转说明
    """把未知抛出值渲成消息。"""
    if 错误 is None:#无抛出值
        return ''#空串
    return str(错误)#强制转字符串

def 解析工作线程消息(原始):#校验并重建入站消息
    """入站端口流量的运行时形态门；垃圾返回None并丢弃。原始是 dict。"""
    if not isinstance(原始,dict):#必须是对象
        return None#丢弃
    if 'type' not in 原始:#无标签
        return None#丢弃
    类型=原始['type']#标签
    if 类型=='call':#绑定调用
        if 'id' not in 原始 or 'global' not in 原始 or 'name' not in 原始:#缺必填键
            return None#丢弃
        编号=原始['id']#调用编号
        if isinstance(编号,bool) or not isinstance(编号,(int,float)):#编号须是数字且排除布尔
            return None#丢弃
        if not isinstance(原始['global'],str) or not isinstance(原始['name'],str):#名须字符串
            return None#丢弃
        重建={'type':'call','id':编号,'global':原始['global'],'name':原始['name']}#必填字段
        if 'args' in 原始:#可选实参
            重建['args']=原始['args']#带上
        return 重建#重建
    if 类型=='log':#日志
        if 'text' not in 原始 or not isinstance(原始['text'],str):#text必须是字符串
            return None#丢弃
        return {'type':'log','text':原始['text']}#重建
    if 类型=='output-limit':#触顶
        return {'type':'output-limit'}#重建
    if 类型=='done':#完成
        if 'error' not in 原始 or 原始['error'] is None:#无error或null则成功路径
            结果={'type':'done'}#基
            if 'value' in 原始:#可选完成值
                结果['value']=原始['value']#带上
            return 结果#重建
        错误=原始['error']#失败字段
        if not isinstance(错误,dict):#必须是对象
            return None#丢弃
        if 'kind' not in 错误 or 'message' not in 错误:#缺失败字段
            return None#丢弃
        种类=错误['kind']#类别
        消息=错误['message']#说明
        if 种类 not in ('exception','invalid-output','output-limit') or not isinstance(消息,str):#合法kind与字符串
            return None#丢弃
        return {'type':'done','error':{'kind':种类,'message':消息}}#重建
    return None#未知标签

class 输出账本:#宿主侧外层输出账本
    """一次运行的外层输出合账；绑定值从不进入。"""
    def __init__(自身,最大字节):#记下硬上限
        """记下硬上限。"""
        自身.最大字节=最大字节#上限
        自身.已用字节=2#空日志数组[]占2字节
        自身.条数=0#已准入条数

    def 准入(自身,文本,收集器):#尝试收一条日志
        """准入一条精确日志，或报告已越过硬上限。"""
        分隔=1 if 自身.条数>0 else 0#非首条逗号
        串字节=json字符串字节上限(文本,自身.最大字节-自身.已用字节-分隔)#剩余预算内计量
        if 串字节 is None:#装不下
            return False#拒绝
        自身.已用字节+=串字节+分隔#计入
        自身.条数+=1#条数加一
        收集器.append(文本)#写入收集器
        return True#已准入

    def 成功(自身,日志列表,值=None,有完成值=False):#成功结果
        """对照合上限敲定一次成功。有完成值则带 value；无完成值则省略该键。"""
        if 有完成值 and json值字节上限(值,自身.最大字节-自身.已用字节) is None:#完成值越界
            return 自身.超限(日志列表)#改报超限
        结果={'logs':日志列表}#基
        if 有完成值:#有完成值
            结果['value']=值#带上
        return 结果#成功

    def 失败(自身,日志列表,错误):#失败结果
        """敲定失败诊断；合字节越上限时output-limit优先。错误是 dict。"""
        if json字符串字节上限(错误['message'],自身.最大字节-自身.已用字节) is None:#说明越界
            return 自身.超限(日志列表)#改报超限
        return {'logs':日志列表,'error':错误}#原样携带失败

    def 超限(自身,日志列表):#超限结果
        """构造显式output-limit失败，同时保留最后一条日志中装得下的前缀。"""
        全文='outer output exceeded '+str(自身.最大字节)+' bytes'#固定诊断全文
        消息字节=len(全文)+2#诊断本身占用（ASCII）
        保留=[]#装得下的日志前缀
        保留字节=2#空数组[]
        日志预算=自身.最大字节-消息字节#留给日志的预算
        for 文本 in 日志列表:#按原序尽量保留
            分隔=1 if len(保留)>0 else 0#非首条逗号
            可用=日志预算-保留字节-分隔#本条可用
            串字节=json字符串字节上限(文本,可用)#全文能否装下
            if 串字节 is not None:#能装下
                保留.append(文本)#整条保留
                保留字节+=串字节+分隔#计入
                continue#下一条
            前缀=截断json字符串字节(文本,可用)#截断本条
            if len(前缀)>0:#前缀非空；判 length
                前缀字节=json字符串字节上限(前缀,可用)#再计量
                if 前缀字节 is None:#前缀越界是内部错误
                    raise RuntimeError('output ledger produced an oversized log prefix')#内部错误
                保留.append(前缀)#保留前缀
                保留字节+=前缀字节+分隔#计入
            break#一旦截断就停
        可用消息=自身.最大字节-保留字节#诊断还剩多少
        消息=截断json字符串字节(全文,可用消息)#必要时截断诊断
        return {'logs':保留,'error':{'kind':'output-limit','message':消息}}#超限失败

class 队列端口:#同进程队列消息端口
    """把双向队列收成工作线程端口形态，供工作线程与宿主共用。"""
    def __init__(自身,入队,出队,关闭标志):#绑定队列
        """绑定入队/出队与关闭标志。"""
        自身.入队=入队#收到的消息
        自身.出队=出队#发出的消息
        自身.关闭标志=关闭标志#关闭标志
        自身.处理=None#message回调
        自身.泵线程=None#泵线程

    def 投递(自身,消息):#投递一条消息
        """投递一条消息。"""
        if 自身.关闭标志.is_set():#已关闭
            return#无处可投
        自身.出队.put(消息)#入出队

    def 监听(自身,事件,回调):#登记事件回调
        """登记message回调并启动泵。"""
        if 事件!='message':#只支持message
            return#忽略
        自身.处理=回调#记住回调
        def 泵():#后台读入队
            """从入队取消息并分发。"""
            while not 自身.关闭标志.is_set():#未关闭
                try:#带超时取消息
                    消息=自身.入队.get(timeout=0.05)#取一条
                except queue.Empty:#暂时没有
                    continue#再试
                if 消息 is None:#毒丸
                    break#结束
                if 自身.处理 is not None:#有回调
                    try:#分发
                        自身.处理(消息)#调用
                    except Exception:#回调可抛任意类型，泵必须活着
                        pass#收容
        自身.泵线程=threading.Thread(target=泵,daemon=True)#泵线程
        自身.泵线程.start()#启动

    def 关闭(自身):#关闭端口
        """关闭并投毒丸。"""
        自身.关闭标志.set()#置位
        try:#投毒丸
            自身.入队.put(None)#唤醒泵
        except Exception:#队列已死，关闭路径必须完备
            pass#忽略

class 工作线程代码运行时(代码运行时):#worker-thread后端
    """已交付的CodeRuntime后端（ctx.codeRuntime）。注册为codeRuntime服务；每一项上限都来自已校验配置。配置是 dict。"""
    Config=配置模式#静态配置模式
    def __init__(自身,上下文对象,配置):#注册服务并校验配置
        """挂到codeRuntime并校验正数与墙钟上限。配置是 dict。"""
        super().__init__(上下文对象)#挂服务
        自身.配置={#已填默认的配置
            'computeMs':配置['computeMs'],#忙时
            'maxWallMs':配置['maxWallMs'],#墙钟
            'maxOutputBytes':配置['maxOutputBytes'],#外层输出
            'maxOldGenerationSizeMb':配置['maxOldGenerationSizeMb'],#堆信息
        }#结束配置
        for 键,值 in 自身.配置.items():#逐项检查
            if isinstance(值,bool) or not isinstance(值,(int,float)) or not (值>0) or 值!=值:#必须是正有限数，排除布尔
                raise RuntimeError('dsh-code-runtime-worker-thread: config.'+键+' must be a positive number, got '+str(值))#加载失败
        if isinstance(自身.配置['maxOutputBytes'],bool) or not isinstance(自身.配置['maxOutputBytes'],int) or 自身.配置['maxOutputBytes']<最小输出字节:#输出上限
            raise RuntimeError('dsh-code-runtime-worker-thread: config.maxOutputBytes must be a safe integer of at least '+str(最小输出字节)+', got '+str(自身.配置['maxOutputBytes']))#过小
        if 自身.配置['maxWallMs']>定时器延迟上限毫秒:#墙钟不得超过定时器上限
            raise RuntimeError('dsh-code-runtime-worker-thread: config.maxWallMs must be at most '+str(定时器延迟上限毫秒)+' (Node clamps a longer setTimeout delay to 1ms), got '+str(自身.配置['maxWallMs']))#过长
        自身.飞行表={}#飞行中运行：身份→句柄
        自身.已拆除=False#是否已拆除
        自身.锁=threading.Lock()#飞行集合锁
        def 拆除服务():#fiber拆除回调
            """fiber拆除时静止。"""
            自身.拆除()#拆除
        上下文对象.副作用(拆除服务,'worker code-runtime teardown')#纤程拆除时静止

    @property#只读
    def 语言(自身):#源语言
        """run期望program所用的源语言。"""
        return 'python'#本中文实现执行Python程序体

    @property#只读
    def 隔离(自身):#隔离基底
        """执行基底标识。"""
        return 'worker-thread'#对齐上游隔离标签

    def 拆除(自身):#fiber拆除
        """拆除到静止：标记不可用，把每条飞行中运行以中止失败，并等待每个工作线程退出。"""
        自身.已拆除=True#拒绝后续run
        with 自身.锁:#快照飞行中运行
            运行列表=list(自身.飞行表.values())#拷贝句柄
        for 运行 in 运行列表:#全部以拆除中止
            运行['settle']({'kind':'abort','message':'runtime disposed'})#强制失败
        for 运行 in 运行列表:#等到每个工作线程退出
            运行['finished'].wait()#等待

    def 运行(自身,请求):#执行一次程序
        """在全新工作线程里执行一份程序。程序结局以result.error决议；只有约定误用才拒绝。请求是 dict。"""
        if 自身.已拆除:#拆除后拒绝
            raise RuntimeError('dsh-code-runtime-worker-thread: run() after disposal')#拒绝
        绑定索引=自身.校验绑定(请求)#校验并索引绑定
        信号=请求['signal'] if 'signal' in 请求 else None#可选中止信号
        if 信号 is not None and 已中止(信号):#请求时已中止
            消息=自身.中止消息(信号)#原因异常的字符串
            return 自身.工作线程前失败({'kind':'abort','message':消息})#无工作线程的abort
        代码=请求['program']#程序体
        if not isinstance(代码,str):#必须是字符串
            return 自身.工作线程前失败({'kind':'exception','message':'program must be a string'})#程序失败
        try:#编译可能因语法失败
            compile(代码,'<code-runtime>','exec')#只解析——不拉起工作线程前的语法门
        except SyntaxError as 错误:#语法失败
            return 自身.工作线程前失败({'kind':'exception','message':消息于(错误)})#无工作线程的exception
        return 自身.执行(请求,代码,绑定索引)#拉起工作线程跑

    def 中止消息(自身,信号):#把中止原因收成字符串
        """已中止信号上的原因异常转成消息。"""
        try:#抛出原因异常
            若已中止则抛出(信号)#抛原因
        except BaseException as 错误:#原因异常
            return str(错误)#英文消息
        return ''#未抛则空串

    def 工作线程前失败(自身,错误):#无工作线程失败
        """把外层输出账本套到工作线程拥有账本之前发生的失败上。错误是 dict。"""
        return 输出账本(自身.配置['maxOutputBytes']).失败([],错误)#空日志上敲定失败

    def 校验绑定(自身,请求):#校验绑定
        """把畸形绑定全局或带类型错误声明当作约定误用拒绝。请求是 dict。"""
        绑定列表=请求['bindings']#命名空间列表
        索引={}#全局名→命名空间
        for 命名空间 in 绑定列表:#逐个
            全局=命名空间['global']#全局名
            if not isinstance(全局,str) or 标识符.match(全局) is None or 全局 in 可移植保留字:#标识符或保留字
                raise RuntimeError('dsh-code-runtime-worker-thread: binding global '+repr(全局)+' is not a usable identifier')#不可用
            if 全局 in 保留绑定全局:#后端自有槽
                raise RuntimeError('dsh-code-runtime-worker-thread: reserved binding global '+repr(全局))#保留
            if 全局 in 索引:#重复
                raise RuntimeError('dsh-code-runtime-worker-thread: duplicate binding global '+repr(全局))#重复
            索引[全局]=命名空间#收入
        错误类名集合=set()#已注入的错误类名
        for 命名空间 in 绑定列表:#再扫一遍错误类
            if 'errorClass' not in 命名空间:#无则跳过
                continue#下一项
            描述=命名空间['errorClass']#可选
            名=描述['name']#类名
            if not isinstance(名,str) or 标识符.match(名) is None or 名 in 可移植保留字:#类名必须可移植
                raise RuntimeError('dsh-code-runtime-worker-thread: binding error class '+repr(名)+' is not a usable identifier')#不可用
            if 名 in 保留绑定全局:#不能占用后端自有槽
                raise RuntimeError('dsh-code-runtime-worker-thread: reserved binding global '+repr(名))#保留
            if 名 in 索引 or 名 in 错误类名集合:#撞名
                raise RuntimeError('dsh-code-runtime-worker-thread: duplicate injected global '+repr(名))#重复
            成员=描述['memberNameProperty']#成员名属性
            if not isinstance(成员,str) or len(成员)==0 or 成员 in 保留错误成员 or 双下划线成员.match(成员) is not None:#不可用；判 length
                raise RuntimeError('dsh-code-runtime-worker-thread: binding error member property '+repr(成员)+' is not usable')#拒绝
            错误类名集合.add(名)#记下
        return 索引#返回索引

    def 执行(自身,请求,代码,绑定索引):#拉起并驱动一次运行
        """为一次已校验的运行拉起工作线程并驱动到结算。请求是 dict。"""
        命名空间声明=[]#声明列表
        for 全局,命名空间 in 绑定索引.items():#逐个
            函数表=命名空间['functions']#函数表
            项={'global':全局,'names':list(函数表.keys()) if isinstance(函数表,dict) else []}#基
            if 'errorClass' in 命名空间:#有错误类
                描述=命名空间['errorClass']#错误类描述
                项['errorClass']={'name':描述['name'],'memberNameProperty':描述['memberNameProperty']}#带上
            命名空间声明.append(项)#收入
        启动={'code':代码,'namespaces':命名空间声明,'maxOutputBytes':自身.配置['maxOutputBytes']}#经workerData交给工作线程
        宿主到工作线程=queue.Queue()#宿主→工作线程
        工作线程到宿主=queue.Queue()#工作线程→宿主
        关闭标志=threading.Event()#关闭标志
        工作线程端口=队列端口(宿主到工作线程,工作线程到宿主,关闭标志)#工作线程侧端口（入=宿主出）
        宿主端口=队列端口(工作线程到宿主,宿主到工作线程,关闭标志)#宿主侧端口（入=工作线程出）
        结算事件=threading.Event()#拆除完成
        结果盒={'value':None,'settled':False,'terminal':None}#结算盒
        已应答=set()#已应答的call id
        日志列表=[]#端口日志
        账本=输出账本(自身.配置['maxOutputBytes'])#外层合账
        忙时起=time.monotonic()#忙时起点（Python侧用墙钟忙时近似；对齐computeMs语义的尽力实现）
        锁=threading.Lock()#结算锁
        def 完成(物化):#选定结局
            """恰好一个结局获胜；物化在锁内取当前日志。"""
            with 锁:#恰好一个结局获胜
                if 结果盒['settled']:#已结算
                    return#忽略
                结果盒['settled']=True#锁死
                if 结果盒['terminal'] is not None:#管道/日志抢先
                    结果盒['value']=结果盒['terminal']#优先
                else:#当场物化
                    结果盒['value']=物化()#调用
            关闭标志.set()#关闭端口
            try:#毒丸
                宿主到工作线程.put(None)#唤醒
                工作线程到宿主.put(None)#唤醒
            except Exception:#队列可能已关，关闭路径必须完备
                pass#收容
            结算事件.set()#通知拆除完成
        def 结算失败(失败):#外部强制失败
            """合账后敲定失败。失败是 dict。"""
            def 物化失败():#锁内物化
                """按当前日志敲定失败。"""
                return 账本.失败(list(日志列表),失败)#合账后敲定
            完成(物化失败)#选定失败
        飞行={'settle':结算失败,'finished':结算事件}#登记飞行中运行
        飞行身份=id(飞行)#句柄身份
        with 自身.锁:#加入飞行集合
            自身.飞行表[飞行身份]=飞行#记下
        def 工作线程主():#工作线程
            """跑工作线程入口；崩溃则报基底死亡。"""
            try:#跑主逻辑
                工作线程入口(工作线程端口,启动)#入口
            except Exception as 错误:#工作线程崩溃；入口可抛任意类型
                def 物化崩溃():#锁内物化
                    """按当前日志敲定工作线程退出。"""
                    return 账本.失败(list(日志列表),{'kind':'worker-exit','message':'worker error: '+消息于(错误)})#基底死亡
                完成(物化崩溃)#结算
        工作线程=threading.Thread(target=工作线程主,daemon=True)#全新工作线程
        def 处理宿主消息(原始):#入站端口流量
            """分发工作线程→宿主消息。"""
            if 结果盒['settled']:#已结算
                return#忽略
            消息=解析工作线程消息(原始)#校验并重建
            if 消息 is None:#垃圾丢弃
                return#忽略
            if 消息['type']=='log':#日志
                if not 账本.准入(消息['text'],日志列表):#装不进合账
                    受限=账本.超限(日志列表+[消息['text']])#含本条的超限结果
                    结果盒['terminal']=受限#抢先
                    def 物化超限日志():#锁内物化
                        """返回已抢先的超限结果。"""
                        return 受限#超限
                    完成(物化超限日志)#立刻结算
                return#不再分发
            if 消息['type']=='output-limit':#工作线程侧触顶
                受限=账本.超限(list(日志列表))#按已捕获日志超限
                结果盒['terminal']=受限#抢先
                def 物化工作线程触顶():#锁内物化
                    """返回已抢先的超限结果。"""
                    return 受限#超限
                完成(物化工作线程触顶)#立刻结算
                return#不再分发
            if 消息['type']=='call':#绑定调用
                if 消息['id'] in 已应答:#重复id丢弃
                    return#忽略
                已应答.add(消息['id'])#记下已应答
                def 应答(载荷):#向工作线程应答
                    """向工作线程投递应答。载荷是 dict。"""
                    if 结果盒['settled']:#已结算则不再投递
                        return#忽略
                    宿主端口.投递(载荷)#发出应答
                if 消息['global'] not in 绑定索引:#未知全局
                    应答({'type':'reply','id':消息['id'],'ok':False,'message':'unknown binding '+repr(消息['global']+'.'+消息['name'])})#失败应答
                    return#结束
                记录=绑定索引[消息['global']]#目标命名空间
                函数表=记录['functions']#函数表
                if 消息['name'] not in 函数表:#未知成员
                    应答({'type':'reply','id':消息['id'],'ok':False,'message':'unknown binding '+repr(消息['global']+'.'+消息['name'])})#失败应答
                    return#结束
                函数=函数表[消息['name']]#自有成员
                if not callable(函数):#不是可调用
                    应答({'type':'reply','id':消息['id'],'ok':False,'message':'unknown binding '+repr(消息['global']+'.'+消息['name'])})#失败应答
                    return#结束
                实参=解码工作线程json(消息['args'] if 'args' in 消息 else None)#解码实参
                if 实参 is None:#有损实参
                    应答({'type':'reply','id':消息['id'],'ok':False,'message':'binding arguments must be lossless JSON'})#失败应答
                    return#结束
                def 执行绑定():#异步执行绑定，不阻塞消息循环
                    """调用宿主绑定并把决议编回工作线程。"""
                    try:#绑定可能抛
                        决议=函数(实参)#调用宿主函数；绑定按同步 JSON 定死
                        try:#快照可能抛
                            值=快照json值(决议)#脱离为无损JSON
                        except Exception:#快照对任意值没有收窄契约
                            值=None#视为无效决议
                        if 值 is None:#不是无损JSON
                            应答({'type':'reply','id':消息['id'],'ok':False,'message':'binding resolution must be lossless JSON'})#失败
                        else:#无损
                            应答({'type':'reply','id':消息['id'],'ok':True,'value':编码工作线程json(值)})#成功
                    except Exception as 错误:#绑定抛；宿主函数可抛任意类型
                        应答({'type':'reply','id':消息['id'],'ok':False,'message':消息于(错误)})#失败说明
                threading.Thread(target=执行绑定,daemon=True).start()#立即启动
                return#结束call
            if 消息['type']=='done':#完成
                if 'error' in 消息:#程序/输出失败
                    错误=消息['error']#失败字段
                    def 物化完成失败():#锁内物化
                        """按当前日志敲定失败。"""
                        return 账本.失败(list(日志列表),错误)#合账后敲定失败
                    完成(物化完成失败)#结算
                    return#结束
                if 'value' not in 消息:#无完成值
                    def 物化无值成功():#锁内物化
                        """成功且省略 value。"""
                        return 账本.成功(list(日志列表))#成功且无value
                    完成(物化无值成功)#结算
                    return#结束
                值=解码工作线程json(消息['value'])#解码完成值
                if 值 is None:#有损JSON
                    def 物化无效完成():#锁内物化
                        """报无效完成。"""
                        return 账本.失败(list(日志列表),{'kind':'invalid-output','message':'program completion must be lossless JSON'})#报无效完成
                    完成(物化无效完成)#结算
                else:#无损
                    def 物化有值成功():#锁内物化
                        """成功带 value。"""
                        return 账本.成功(list(日志列表),值,True)#成功带value
                    完成(物化有值成功)#结算
        宿主端口.监听('message',处理宿主消息)#监听工作线程→宿主
        工作线程.start()#拉起工作线程
        def 墙钟到期():#墙钟超时
            """墙钟预算耗尽。"""
            def 物化墙钟():#锁内物化
                """敲定墙钟超时。"""
                return 账本.失败(list(日志列表),{'kind':'timeout','message':'wall-clock ceiling reached ('+str(自身.配置['maxWallMs'])+'ms)'})#墙钟超时
            完成(物化墙钟)#结算
        墙钟秒=自身.配置['maxWallMs']/1000.0#转秒
        墙钟定时=threading.Timer(墙钟秒,墙钟到期)#墙钟定时器
        墙钟定时.daemon=True#守护
        墙钟定时.start()#启动
        def 忙时采样():#按节拍采样
            """热循环耗尽忙时预算。"""
            while not 结果盒['settled'] and not 关闭标志.is_set():#未结算
                已忙=(time.monotonic()-忙时起)*1000.0#毫秒
                if 已忙>自身.配置['computeMs']:#忙时超预算
                    def 物化忙时():#锁内物化
                        """敲定忙时超时。"""
                        return 账本.失败(list(日志列表),{'kind':'timeout','message':'compute budget exhausted ('+str(自身.配置['computeMs'])+'ms busy)'})#超时
                    完成(物化忙时)#结算
                    return#结束
                time.sleep(事件循环采样间隔毫秒/1000.0)#采样间隔
        threading.Thread(target=忙时采样,daemon=True).start()#启动采样
        信号=请求['signal'] if 'signal' in 请求 else None#中止信号
        if 信号 is not None:#有信号
            def 等待中止结算():#请求中止
                """阻塞到中止再结算 abort。"""
                等待中止(信号)#阻塞到中止
                消息=自身.中止消息(信号)#原因消息
                def 物化中止():#锁内物化
                    """敲定中止失败。"""
                    return 账本.失败(list(日志列表),{'kind':'abort','message':消息})#中止失败
                完成(物化中止)#结算
            threading.Thread(target=等待中止结算,daemon=True).start()#等待中止结算
        结算事件.wait()#等到结算
        墙钟定时.cancel()#停墙钟
        with 自身.锁:#移出飞行集合
            自身.飞行表.pop(飞行身份,None)#摘掉
        工作线程端口.关闭()#关闭
        宿主端口.关闭()#关闭
        return 结果盒['value']#决议本次运行

默认=工作线程代码运行时#默认导出
Config=配置模式#Cordis配置槽
default=工作线程代码运行时#Cordis默认导出槽
