"""工人线程代码运行时：每次用全新工人线程跑一份程序，并经消息端口桥接绑定。这是隔离，不是安全边界：尽管有堆/忙时/墙钟预算以及终止，模型代码仍有与 bash 相当的信任。"""
import queue,re,threading,time#队列、标识符、线程与墙钟
from ...依赖.schemastery import 数字字段#配置字段
from ...工具.超时 import 定时器延迟上限毫秒#setTimeout最大延迟
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
from .工人json import (#扁平线路编解码
    快照代码json值,#无损快照
    编码工人json,#编码
    解码工人json,#解码
)#来自工人json
from .引导 import (#工人侧引导公开面
    跑工人主逻辑,#主逻辑
    日志缓冲,#日志账本
    制作控制台垫片,#缩小版console
    劫持流写出,#流写出劫持
    准备完成,#完成值片段
    准备异常,#异常片段
    制作绑定错误类,#单个错误类
    制作绑定错误类表,#错误类表
    接线应答,#应答接线
    制作命名空间们,#命名空间物化
)#来自引导
from .工人 import 工人入口#工人入口
from .协议 import (#线路协议字段与标签
    工人启动数据,#启动载荷字段类
    工人到宿主类型,#工人→宿主标签
    应答消息,#宿主应答字段类
)#来自协议
from .不变量 import (#本包不变量配套
    应用 as 应用不变量,#登记配套
    安装 as 安装不变量,#空安装器
    包名 as 不变量包名,#所有权名
)#来自不变量

标识符=re.compile(r'^[A-Za-z_][A-Za-z0-9_]*$')#可移植标识符
事件循环采样间隔毫秒=25#ELU采样间隔毫秒（内部节拍，不是配置）
最小输出字节=4#能表示已计数载荷的最小上限：空日志数组加空JSON失败消息

配置模式={#schemastery配置模式
    'computeMs':数字字段(默认值=60000),#默认忙时60s
    'maxWallMs':数字字段(默认值=600000),#默认墙钟600s
    'maxOutputBytes':数字字段(默认值=67108864),#默认64MiB外层输出
    'maxOldGenerationSizeMb':数字字段(默认值=512),#默认512MiB老生代（Python侧作信息上限）
}#结束配置模式
Config=配置模式#Cordis配置模式

__all__=[#仅中文公开名；Cordis 槽英文别名不入表
    '标识符','事件循环采样间隔毫秒','最小输出字节','配置模式',
    '消息于','取字段','解析工人消息','输出账本','队列端口','工人线程代码运行时','默认',
]#公开面结束

def 消息于(错误):#抛出值转说明
    """把未知抛出值渲成消息。"""
    return str(错误) if 错误 is not None else ''#强制转

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#自有键
    return getattr(对象,键,缺省)#属性

def 解析工人消息(原始):#校验并重建入站消息
    """入站端口流量的运行时形态门；垃圾返回None并丢弃。"""
    if not isinstance(原始,dict):#必须是对象
        return None#丢弃
    类型=原始.get('type')#标签
    if 类型=='call':#绑定调用
        if not isinstance(原始.get('id'),(int,float)) or not isinstance(原始.get('global'),str) or not isinstance(原始.get('name'),str):#必填类型
            return None#丢弃
        return {'type':'call','id':原始['id'],'global':原始['global'],'name':原始['name'],'args':原始.get('args')}#重建
    if 类型=='log':#日志
        if not isinstance(原始.get('text'),str):#text必须是字符串
            return None#丢弃
        return {'type':'log','text':原始['text']}#重建
    if 类型=='output-limit':#触顶
        return {'type':'output-limit'}#重建
    if 类型=='done':#完成
        if 'error' not in 原始 or 原始.get('error') is None:#无error
            结果={'type':'done'}#基
            if 'value' in 原始 and 原始.get('value') is not None:#可选value
                结果['value']=原始['value']#带上
            return 结果#重建
        错误=原始.get('error')#失败字段
        if not isinstance(错误,dict):#必须是对象
            return None#丢弃
        种类=错误.get('kind')#类别
        消息=错误.get('message')#说明
        if 种类 not in ('exception','invalid-output','output-limit') or not isinstance(消息,str):#合法kind与字符串
            return None#丢弃
        return {'type':'done','error':{'kind':种类,'message':消息}}#重建
    return None#未知标签

class 输出账本:#宿主侧外层输出账本
    """一次运行的外层输出合账；绑定值从不进入。"""
    def __init__(自身,最大字节):#记下硬上限
        """记下硬上限。"""
        自身.maxBytes=最大字节#上限
        自身.最大字节=最大字节#中文别名
        自身._字节=2#空日志数组[]占2字节
        自身._条数=0#已准入条数
    def admit(自身,文本,收集器):#尝试收一条日志
        """准入一条精确日志，或报告已越过硬上限。"""
        分隔=1 if 自身._条数>0 else 0#非首条逗号
        串字节=json字符串字节上限(文本,自身.maxBytes-自身._字节-分隔)#剩余预算内计量
        if 串字节 is None:#装不下
            return False#拒绝
        自身._字节+=串字节+分隔#计入
        自身._条数+=1#条数加一
        收集器.append(文本)#写入收集器
        return True#已准入
    def 准入(自身,文本,收集器):#中文别名
        """中文别名。"""
        return 自身.admit(文本,收集器)#委托
    def success(自身,日志们,值=None):#成功结果
        """对照合上限敲定一次成功的缺席或JSON完成。"""
        if 值 is not None and json值字节上限(值,自身.maxBytes-自身._字节) is None:#完成值越界
            return 自身.limit(日志们)#改报超限
        结果={'logs':日志们}#基
        if 值 is not None:#有完成值
            结果['value']=值#带上
        return 结果#成功
    def 成功(自身,日志们,值=None):#中文别名
        """中文别名。"""
        return 自身.success(日志们,值)#委托
    def failure(自身,日志们,错误):#失败结果
        """敲定失败诊断；合字节越上限时output-limit优先。"""
        if json字符串字节上限(错误['message'],自身.maxBytes-自身._字节) is None:#说明越界
            return 自身.limit(日志们)#改报超限
        return {'logs':日志们,'error':错误}#原样携带失败
    def 失败(自身,日志们,错误):#中文别名
        """中文别名。"""
        return 自身.failure(日志们,错误)#委托
    def limit(自身,日志们):#超限结果
        """构造显式output-limit失败，同时保留最后一条日志中装得下的前缀。"""
        全文='outer output exceeded '+str(自身.maxBytes)+' bytes'#固定诊断全文
        消息字节=len(全文)+2#诊断本身占用（ASCII）
        保留=[]#装得下的日志前缀
        保留字节=2#空数组[]
        日志预算=自身.maxBytes-消息字节#留给日志的预算
        for 文本 in 日志们:#按原序尽量保留
            分隔=1 if len(保留)>0 else 0#非首条逗号
            可用=日志预算-保留字节-分隔#本条可用
            串字节=json字符串字节上限(文本,可用)#全文能否装下
            if 串字节 is not None:#能装下
                保留.append(文本)#整条保留
                保留字节+=串字节+分隔#计入
                continue#下一条
            前缀=截断json字符串字节(文本,可用)#截断本条
            if len(前缀)>0:#前缀非空
                前缀字节=json字符串字节上限(前缀,可用)#再计量
                if 前缀字节 is None:#前缀越界是内部错误
                    raise RuntimeError('output ledger produced an oversized log prefix')#内部错误
                保留.append(前缀)#保留前缀
                保留字节+=前缀字节+分隔#计入
            break#一旦截断就停
        可用消息=自身.maxBytes-保留字节#诊断还剩多少
        消息=截断json字符串字节(全文,可用消息)#必要时截断诊断
        return {'logs':保留,'error':{'kind':'output-limit','message':消息}}#超限失败
    def 超限(自身,日志们):#中文别名
        """中文别名。"""
        return 自身.limit(日志们)#委托

class 队列端口:#同进程队列消息端口
    """把双向队列收成MessagePort形态，供工人与宿主共用。"""
    def __init__(自身,入队,出队,关闭旗):#绑定队列
        """绑定入队/出队与关闭旗。"""
        自身._入=入队#收到的消息
        自身._出=出队#发出的消息
        自身._关闭=关闭旗#关闭旗
        自身._处理=None#message回调
        自身._泵=None#泵线程
    def postMessage(自身,消息):#投递一条消息
        """投递一条消息。"""
        if 自身._关闭.is_set():#已关闭
            return#无处可投
        自身._出.put(消息)#入出队
    def on(自身,事件,回调):#登记事件回调
        """登记message回调并启动泵。"""
        if 事件!='message':#只支持message
            return#忽略
        自身._处理=回调#记住回调
        def 泵():#后台读入队
            while not 自身._关闭.is_set():#未关闭
                try:#带超时取消息
                    消息=自身._入.get(timeout=0.05)#取一条
                except queue.Empty:#暂时没有
                    continue#再试
                if 消息 is None:#毒丸
                    break#结束
                if 自身._处理 is not None:#有回调
                    try:#分发
                        自身._处理(消息)#调用
                    except Exception:#回调失败不得杀死泵
                        pass#收容
        自身._泵=threading.Thread(target=泵,daemon=True)#泵线程
        自身._泵.start()#启动
    def 关闭(自身):#关闭端口
        """关闭并投毒丸。"""
        自身._关闭.set()#置位
        try:#投毒丸
            自身._入.put(None)#唤醒泵
        except Exception:#队列已死
            pass#忽略

class 工人线程代码运行时(代码运行时):#worker-thread后端
    """已交付的CodeRuntime后端（ctx.codeRuntime）。注册为codeRuntime服务；每一项上限都来自已校验配置。"""
    Config=配置模式#静态配置模式
    def __init__(自身,上下文对象,配置):#注册服务并校验配置
        """挂到codeRuntime并校验正数与墙钟上限。"""
        super().__init__(上下文对象)#挂服务
        自身.config={#已填默认的配置
            'computeMs':取字段(配置,'computeMs',60000),#忙时
            'maxWallMs':取字段(配置,'maxWallMs',600000),#墙钟
            'maxOutputBytes':取字段(配置,'maxOutputBytes',67108864),#外层输出
            'maxOldGenerationSizeMb':取字段(配置,'maxOldGenerationSizeMb',512),#堆信息
        }#结束config
        自身.配置=自身.config#中文别名
        for 键,值 in 自身.config.items():#逐项检查
            if not isinstance(值,(int,float)) or isinstance(值,bool) or not (值>0) or 值!=值:#必须是正有限数
                raise RuntimeError('dsh-code-runtime-worker-thread: config.'+键+' must be a positive number, got '+str(值))#加载失败
        if not isinstance(自身.config['maxOutputBytes'],int) or 自身.config['maxOutputBytes']<最小输出字节:#输出上限
            raise RuntimeError('dsh-code-runtime-worker-thread: config.maxOutputBytes must be a safe integer of at least '+str(最小输出字节)+', got '+str(自身.config['maxOutputBytes']))#过小
        if 自身.config['maxWallMs']>定时器延迟上限毫秒:#墙钟不得超过定时器上限
            raise RuntimeError('dsh-code-runtime-worker-thread: config.maxWallMs must be at most '+str(定时器延迟上限毫秒)+' (Node clamps a longer setTimeout delay to 1ms), got '+str(自身.config['maxWallMs']))#过长
        自身._飞行={}#飞行中运行：身份→句柄
        自身._已拆除=False#是否已拆除
        自身._锁=threading.Lock()#飞行集合锁
        上下文对象.effect(lambda:自身._拆除,'worker code-runtime teardown')#fiber拆除时静止
    @property#只读
    def 语言(自身):#源语言
        """run期望program所用的源语言。"""
        return 'python'#本中文实现执行Python程序体
    @property#只读
    def 隔离(自身):#隔离基底
        """执行基底标识。"""
        return 'worker-thread'#对齐上游隔离标签
    def _拆除(自身):#fiber拆除
        """拆除到静止：标记不可用，把每条飞行中运行以中止失败，并等待每个工人退出。"""
        自身._已拆除=True#拒绝后续run
        with 自身._锁:#快照飞行中运行
            运行们=list(自身._飞行.values())#拷贝句柄
        for 运行 in 运行们:#全部以拆除中止
            运行['settle']({'kind':'abort','message':'runtime disposed'})#强制失败
        for 运行 in 运行们:#等到每个工人退出
            运行['finished'].wait()#等待
    def 运行(自身,请求):#执行一次程序
        """在全新工人里执行一份程序。程序结局以result.error决议；只有约定误用才拒绝。"""
        if 自身._已拆除:#拆除后拒绝
            raise RuntimeError('dsh-code-runtime-worker-thread: run() after disposal')#拒绝
        绑定索引=自身._校验绑定(请求)#校验并索引绑定
        信号=取字段(请求,'signal')#可选中止信号
        if 信号 is not None and (取字段(信号,'aborted') or 取字段(信号,'已中止')):#请求时已中止
            return 自身._工人前失败({'kind':'abort','message':str(取字段(信号,'reason') or 取字段(信号,'原因') or '')})#无工人的abort
        代码=取字段(请求,'program','')#程序体
        if not isinstance(代码,str):#必须是字符串
            return 自身._工人前失败({'kind':'exception','message':'program must be a string'})#程序失败
        try:#编译可能因语法失败
            compile(代码,'<code-runtime>','exec')#只解析——不拉起工人前的语法门
        except Exception as 错误:#语法失败
            return 自身._工人前失败({'kind':'exception','message':消息于(错误)})#无工人的exception
        return 自身._执行(请求,代码,绑定索引)#拉起工人跑
    def _工人前失败(自身,错误):#无工人失败
        """把外层输出账本套到工人拥有账本之前发生的失败上。"""
        return 输出账本(自身.config['maxOutputBytes']).failure([],错误)#空日志上敲定失败
    def _校验绑定(自身,请求):#校验绑定
        """把畸形绑定全局或带类型错误声明当作约定误用拒绝。"""
        绑定们=取字段(请求,'bindings') or []#命名空间列表
        索引={}#全局名→命名空间
        for 命名空间 in 绑定们:#逐个
            全局=取字段(命名空间,'global')#全局名
            if not isinstance(全局,str) or 标识符.match(全局) is None or 全局 in 可移植保留字:#标识符或保留字
                raise RuntimeError('dsh-code-runtime-worker-thread: binding global '+repr(全局)+' is not a usable identifier')#不可用
            if 全局 in 保留绑定全局:#后端自有槽
                raise RuntimeError('dsh-code-runtime-worker-thread: reserved binding global '+repr(全局))#保留
            if 全局 in 索引:#重复
                raise RuntimeError('dsh-code-runtime-worker-thread: duplicate binding global '+repr(全局))#重复
            索引[全局]=命名空间#收入
        错误类名们=set()#已注入的错误类名
        for 命名空间 in 绑定们:#再扫一遍错误类
            描述=取字段(命名空间,'errorClass')#可选
            if 描述 is None:#无则跳过
                continue#下一项
            名=取字段(描述,'name')#类名
            if not isinstance(名,str) or 标识符.match(名) is None or 名 in 可移植保留字:#类名必须可移植
                raise RuntimeError('dsh-code-runtime-worker-thread: binding error class '+repr(名)+' is not a usable identifier')#不可用
            if 名 in 保留绑定全局:#不能占用后端自有槽
                raise RuntimeError('dsh-code-runtime-worker-thread: reserved binding global '+repr(名))#保留
            if 名 in 索引 or 名 in 错误类名们:#撞名
                raise RuntimeError('dsh-code-runtime-worker-thread: duplicate injected global '+repr(名))#重复
            成员=取字段(描述,'memberNameProperty','')#成员名属性
            if not isinstance(成员,str) or len(成员)==0 or 成员 in 保留错误成员 or 双下划线成员.match(成员) is not None:#不可用
                raise RuntimeError('dsh-code-runtime-worker-thread: binding error member property '+repr(成员)+' is not usable')#拒绝
            错误类名们.add(名)#记下
        return 索引#返回索引
    def _执行(自身,请求,代码,绑定索引):#拉起并驱动一次运行
        """为一次已校验的运行拉起工人并驱动到结算。"""
        命名空间声明=[]#声明列表
        for 全局,命名空间 in 绑定索引.items():#逐个
            函数表=取字段(命名空间,'functions') or {}#函数表
            项={'global':全局,'names':list(函数表.keys()) if isinstance(函数表,dict) else []}#基
            描述=取字段(命名空间,'errorClass')#可选错误类
            if 描述 is not None:#有
                项['errorClass']={'name':取字段(描述,'name'),'memberNameProperty':取字段(描述,'memberNameProperty')}#带上
            命名空间声明.append(项)#收入
        启动={'code':代码,'namespaces':命名空间声明,'maxOutputBytes':自身.config['maxOutputBytes']}#经workerData交给工人
        宿主到工人=queue.Queue()#宿主→工人
        工人到宿主=queue.Queue()#工人→宿主
        关闭旗=threading.Event()#关闭旗
        工人端口=队列端口(宿主到工人,工人到宿主,关闭旗)#工人侧端口（入=宿主出）
        宿主端口=队列端口(工人到宿主,宿主到工人,关闭旗)#宿主侧端口（入=工人出）
        结算事件=threading.Event()#拆除完成
        结果盒={'value':None,'settled':False,'terminal':None}#结算盒
        已应答=set()#已应答的call id
        日志们=[]#端口日志
        账本=输出账本(自身.config['maxOutputBytes'])#外层合账
        忙时起=time.monotonic()#忙时起点（Python侧用墙钟忙时近似；对齐computeMs语义的尽力实现）
        锁=threading.Lock()#结算锁
        def 完成(终态):#选定结局
            with 锁:#恰好一个结局获胜
                if 结果盒['settled']:#已结算
                    return#忽略
                结果盒['settled']=True#锁死
                if 结果盒['terminal'] is not None:#管道/日志抢先
                    结果盒['value']=结果盒['terminal']#优先
                elif callable(终态):#延迟物化
                    结果盒['value']=终态()#调用
                else:#直接结果
                    结果盒['value']=终态#记下
            关闭旗.set()#关闭端口
            try:#毒丸
                宿主到工人.put(None)#唤醒
                工人到宿主.put(None)#唤醒
            except Exception:#忽略
                pass#收容
            结算事件.set()#通知拆除完成
        def 结算失败(失败):#外部强制失败
            完成(lambda:账本.failure(list(日志们),失败))#合账后敲定
        飞行={'settle':结算失败,'finished':结算事件}#登记飞行中运行
        飞行身份=id(飞行)#句柄身份
        with 自身._锁:#加入飞行集合
            自身._飞行[飞行身份]=飞行#记下
        def 工人线程主():#工人线程
            try:#跑主逻辑
                工人入口(工人端口,启动)#入口
            except Exception as 错误:#工人崩溃
                完成(lambda:账本.failure(list(日志们),{'kind':'worker-exit','message':'worker error: '+消息于(错误)}))#基底死亡
        工人线程=threading.Thread(target=工人线程主,daemon=True)#全新工人
        def 处理宿主消息(原始):#入站端口流量
            if 结果盒['settled']:#已结算
                return#忽略
            消息=解析工人消息(原始)#校验并重建
            if 消息 is None:#垃圾丢弃
                return#忽略
            if 消息['type']=='log':#日志
                if not 账本.admit(消息['text'],日志们):#装不进合账
                    受限=账本.limit(日志们+[消息['text']])#含本条的超限结果
                    结果盒['terminal']=受限#抢先
                    完成(受限)#立刻结算
                return#不再分发
            if 消息['type']=='output-limit':#工人侧触顶
                受限=账本.limit(list(日志们))#按已捕获日志超限
                结果盒['terminal']=受限#抢先
                完成(受限)#立刻结算
                return#不再分发
            if 消息['type']=='call':#绑定调用
                if 消息['id'] in 已应答:#重复id丢弃
                    return#忽略
                已应答.add(消息['id'])#记下已应答
                def 应答(载荷):#向工人应答
                    if 结果盒['settled']:#已结算则不再post
                        return#忽略
                    宿主端口.postMessage(载荷)#发出应答
                记录=绑定索引.get(消息['global'])#目标命名空间
                函数表=取字段(记录,'functions') if 记录 is not None else None#函数表
                函数=函数表.get(消息['name']) if isinstance(函数表,dict) and 消息['name'] in 函数表 else None#自有成员
                if not callable(函数):#未知绑定
                    应答({'type':'reply','id':消息['id'],'ok':False,'message':'unknown binding '+repr(消息['global']+'.'+消息['name'])})#失败应答
                    return#结束
                实参=解码工人json(消息.get('args'))#解码实参
                if 实参 is None:#有损实参
                    应答({'type':'reply','id':消息['id'],'ok':False,'message':'binding arguments must be lossless JSON'})#失败应答
                    return#结束
                def 跑绑定():#异步执行绑定，不阻塞消息循环
                    try:#绑定可能抛/拒
                        决议=函数(实参)#调用宿主函数
                        if hasattr(决议,'等待'):#承诺
                            决议=决议.等待()#等待
                        try:#快照可能抛
                            值=快照json值(决议)#脱离为无损JSON
                        except Exception:#有损
                            值=None#视为无效决议
                        if 值 is None:#不是无损JSON
                            应答({'type':'reply','id':消息['id'],'ok':False,'message':'binding resolution must be lossless JSON'})#失败
                        else:#无损
                            应答({'type':'reply','id':消息['id'],'ok':True,'value':编码工人json(值)})#成功
                    except Exception as 错误:#绑定抛/拒
                        应答({'type':'reply','id':消息['id'],'ok':False,'message':消息于(错误)})#失败说明
                threading.Thread(target=跑绑定,daemon=True).start()#立即启动
                return#结束call
            if 消息['type']=='done':#完成
                if 消息.get('error') is not None:#程序/输出失败
                    错误=消息['error']#失败字段
                    完成(lambda:账本.failure(list(日志们),错误))#合账后敲定失败
                    return#结束
                if 'value' not in 消息:#无完成值
                    完成(lambda:账本.success(list(日志们)))#成功且无value
                    return#结束
                值=解码工人json(消息.get('value'))#解码完成值
                if 值 is None:#有损JSON
                    完成(lambda:账本.failure(list(日志们),{'kind':'invalid-output','message':'program completion must be lossless JSON'}))#报无效完成
                else:#无损
                    完成(lambda:账本.success(list(日志们),值))#成功带value
        宿主端口.on('message',处理宿主消息)#监听工人→宿主
        工人线程.start()#拉起工人
        #墙钟兜底
        def 墙钟到期():#墙钟超时
            完成(lambda:账本.failure(list(日志们),{'kind':'timeout','message':'wall-clock ceiling reached ('+str(自身.config['maxWallMs'])+'ms)'}))#墙钟超时
        墙钟秒=自身.config['maxWallMs']/1000.0#转秒
        墙钟定时=threading.Timer(墙钟秒,墙钟到期)#墙钟定时器
        墙钟定时.daemon=True#守护
        墙钟定时.start()#启动
        #忙时预算：Python线程无ELU，用墙钟忙时采样近似；热循环会耗尽墙钟与本预算
        def 忙时采样():#按节拍采样
            while not 结果盒['settled'] and not 关闭旗.is_set():#未结算
                已忙=(time.monotonic()-忙时起)*1000.0#毫秒
                if 已忙>自身.config['computeMs']:#忙时超预算
                    完成(lambda:账本.failure(list(日志们),{'kind':'timeout','message':'compute budget exhausted ('+str(自身.config['computeMs'])+'ms busy)'}))#超时
                    return#结束
                time.sleep(事件循环采样间隔毫秒/1000.0)#采样间隔
        threading.Thread(target=忙时采样,daemon=True).start()#启动采样
        信号=取字段(请求,'signal')#中止信号
        if 信号 is not None:#有信号
            def 中止时():#请求中止
                完成(lambda:账本.failure(list(日志们),{'kind':'abort','message':str(取字段(信号,'reason') or 取字段(信号,'原因') or '')}))#中止失败
            if hasattr(信号,'addEventListener'):#DOM风格
                信号.addEventListener('abort',中止时,{'once':True})#只听一次
            elif 取字段(信号,'aborted') or 取字段(信号,'已中止'):#已中止
                中止时()#立刻
        结算事件.wait()#等到结算
        墙钟定时.cancel()#停墙钟
        with 自身._锁:#移出飞行集合
            自身._飞行.pop(飞行身份,None)#摘掉
        工人端口.关闭()#关闭
        宿主端口.关闭()#关闭
        return 结果盒['value']#决议本次运行

默认=工人线程代码运行时#默认导出
default=工人线程代码运行时#Cordis默认导出
