"""工人侧执行逻辑，写成对着注入端口的普通函数，以便单元套件能在进程内对着假端口跑每一行。"""
import traceback#异常堆栈渲染
from .输出json import json字符串字节上限,json值字节上限,截断json字符串字节#JSON字节账本
from .工人json import 快照代码json值,编码工人json,解码工人json#无损JSON编解码

捕获错误=Exception#钉死异常基类，避免模型改写
控制台级别=('log','info','warn','error','debug')#五种日志级别
检视选项={'depth':4,'maxArrayLength':100,'maxStringLength':10000}#有界inspect选项：深到有用，又封顶以免病态值撑爆渲染

class 引导端口:#bootstrap所需的端口API——由父端口与测试假端口满足
    """工人/测试共用端口面（约定：实现postMessage与on）。"""
    def postMessage(自身,消息):#向宿主发消息
        """向宿主发消息。"""
        raise NotImplementedError('BootstrapPort.postMessage')#子类或鸭子类型实现
    def on(自身,事件,监听器):#监听宿主应答
        """监听message事件上的宿主应答。"""
        raise NotImplementedError('BootstrapPort.on')#子类或鸭子类型实现

class 可补丁流:#可写流的write槽，即bootstrap所打补丁的形态
    """可打补丁的写出流（约定：实现write）。"""
    def write(自身,块,*其余):#写出一块数据
        """写出一块数据。"""
        raise NotImplementedError('PatchableStream.write')#子类或鸭子类型实现

class 日志缓冲:#日志字节账本
    """共享外层JSON字节预算下的有序文本捕获，每条落地即交给sink。一旦耗尽，发出装得下的前缀并报告一次上限。"""
    def __init__(自身,最大字节,交付槽,触顶回调=None):#构造账本
        """记下上限、交付槽与可选触顶回调。"""
        自身.maxBytes=最大字节#外层字节上限
        自身.最大字节=最大字节#中文别名
        自身.sink=交付槽#每条文本的交付槽
        自身.交付槽=交付槽#中文别名
        自身.onLimit=触顶回调 if 触顶回调 is not None else (lambda:None)#首次触顶回调
        自身.触顶回调=自身.onLimit#中文别名
        自身._字节=2#空日志数组[]占2字节
        自身._条数=0#已准入条数
        自身._已截断=False#是否已因上限截断
    def push(自身,文本):#准入一条日志
        """把文本发给sink，并从预算扣费（耗尽后丢弃并只标记一次）。"""
        if 自身._已截断:#已触顶则后续全丢
            return#忽略
        分隔=1 if 自身._条数>0 else 0#非首条要计入逗号
        可用=自身.maxBytes-自身._字节-分隔#剩余可用字节
        串字节=json字符串字节上限(文本,可用)#全文能否装下
        if 串字节 is None:#装不下则截断
            自身._已截断=True#标记已触顶
            前缀=截断json字符串字节(文本,可用)#取装得下的前缀
            if len(前缀)>0:#前缀非空才交付
                前缀字节=json字符串字节上限(前缀,可用)#再计量前缀
                if 前缀字节 is None:#前缀越界是账本内部错误
                    raise 捕获错误('worker output ledger produced an oversized log prefix')#内部错误
                自身._字节+=前缀字节+分隔#计入前缀与逗号
                自身._条数+=1#条数加一
                自身.sink(前缀)#交付截断前缀
            自身.onLimit()#报告触顶
            return#不再处理原文
        自身._字节+=串字节+分隔#计入全文与逗号
        自身._条数+=1#条数加一
        自身.sink(文本)#交付原文
    def remainingOutputBytes(自身):#剩余外层预算
        """完成值或失败消息还剩的精确JSON字节预算。"""
        return 自身.maxBytes-自身._字节#上限减去已用
    def 剩余输出字节(自身):#中文别名
        """中文别名。"""
        return 自身.remainingOutputBytes()#委托

def 制作控制台垫片(日志):#构造缩小版console
    """替换用的console：五个带级别的方法把实参渲染后再写入缓冲。"""
    def 渲染(参数们):#把实参渲成一行
        段们=[]#片段
        for 参数 in 参数们:#逐个
            if isinstance(参数,str):#字符串原样
                段们.append(参数)#原样
            else:#其余有界repr
                文本=repr(参数)#渲染
                上限=检视选项['maxStringLength']#字符串长度封顶
                if len(文本)>上限:#过长则截断
                    文本=文本[0:上限]+'...'#截断标记
                段们.append(文本)#收入
        return ' '.join(段们)#空格拼接
    垫片={}#空映射shim
    for 级别 in 控制台级别:#为每个级别挂方法
        def 方法(*参数们,_日志=日志,_渲染=渲染):#渲染后推入账本
            _日志.push(_渲染(参数们))#交付
        垫片[级别]=方法#挂方法
    return 垫片#返回五方法对象

def 劫持流写出(日志,流):#劫持流写出进日志缓冲
    """把流的write重定向进日志缓冲，使裸写出按发出顺序与console输出并列。返回还原函数。"""
    原写出=getattr(流,'write',None)#保存原write
    def 写出(块,*其余):#替换写出
        文本=块 if isinstance(块,str) else str(块)#字符串原样，其余转字符串
        日志.push(文本)#准入日志
        回调=None#可选回调槽
        for 候选 in 其余[0:2]:#在encoding/callback槽里找函数
            if callable(候选):#找到回调
                回调=候选#记下
                break#停找
        if 回调 is not None:#有回调则异步成功
            try:#回调本身可能抛
                回调(None)#声称已写出
            except Exception:#回调失败不得打崩工人
                pass#收容
        return True#对外声称已写出
    try:#挂上替换
        流.write=写出#替换写出
    except Exception:#流不可补丁则跳过
        return lambda:None#空还原
    def 还原():#还原原write
        try:#还原可能失败
            if 原写出 is not None:#有原方法
                流.write=原写出#还原
        except Exception:#忽略
            pass#收容
    return 还原#返回还原函数

def 输出超限(最大输出字节):#固定超限诊断
    """构造固定溢出片段，不携带被拒绝的可变字节。"""
    return {'error':{'kind':'output-limit','message':'outer output exceeded '+str(最大输出字节)+' bytes'}}#kind加配置上限

def 准备失败(种类,消息,剩余输出字节,最大输出字节):#准备失败片段
    """准入一条有界失败消息，或换成固定溢出诊断。"""
    if json字符串字节上限(消息,剩余输出字节) is None:#说明本身越界
        return 输出超限(最大输出字节)#改报超限
    return {'error':{'kind':种类,'message':消息}}#原样携带

def 准备完成(值,剩余输出字节,最大输出字节=None):#准备完成值片段
    """为done消息准备程序完成值。只有无损JSON能过线；装不进剩余预算则报output-limit。"""
    if 最大输出字节 is None:#缺省用剩余
        最大输出字节=剩余输出字节#诊断用的配置上限
    if 值 is 准备完成.缺席:#无完成值（对齐上游undefined缺席；None仍是合法JSON null）
        return {}#空片段
    try:#快照可能因有损值失败
        快照=快照代码json值(值)#尝试脱离为无损JSON
    except Exception:#有损或不可快照
        快照=None#视为无效完成
    if 快照 is None:#不是无损JSON
        return 准备失败('invalid-output','program completion must be lossless JSON',剩余输出字节,最大输出字节)#改报invalid-output
    if json值字节上限(快照,剩余输出字节) is None:#快照装不进剩余预算
        return 输出超限(最大输出字节)#改报output-limit
    return {'value':编码工人json(快照)}#编码后作为完成值

准备完成.缺席=object()#无完成值哨兵

def 准备异常(错误,剩余输出字节,最大输出字节=None):#准备异常片段
    """准备程序抛出的值，不把无界堆栈或字符串送过工人端口。"""
    if 最大输出字节 is None:#缺省
        最大输出字节=剩余输出字节#诊断上限
    try:#渲染本身也可能抛
        if isinstance(错误,BaseException):#异常
            详情=''.join(traceback.format_exception(type(错误),错误,错误.__traceback__))#堆栈优先
            if len(详情.strip())==0:#无堆栈
                详情=str(错误)#退回消息
        else:#非异常
            详情=str(错误)#强制转
        消息=详情 if isinstance(详情,str) else str(详情)#保证字符串
    except Exception:#不可渲染
        消息='program threw an unrenderable value'#固定兜底说明
    return 准备失败('exception',消息,剩余输出字节,最大输出字节)#按异常准入

def 定义绑定错误字段(错误,键,值):#给错误实例挂自有字段
    """定义一个公开的绑定错误字段。"""
    setattr(错误,键,值)#挂上

def 制作绑定错误类(描述符):#构造一个绑定错误类
    """物化某一命名空间声明的真实错误构造函数。"""
    类名=描述符['name']#类名
    成员属性=描述符['memberNameProperty']#成员名属性
    class 绑定调用错误(捕获错误):#继承钉死的异常
        def __init__(自身,成员名,消息):#(失败成员,说明)
            super().__init__(消息)#先设消息
            定义绑定错误字段(自身,'name',类名)#公开类名
            定义绑定错误字段(自身,成员属性,成员名)#公开失败成员名
    绑定调用错误.__name__=类名#对齐类名
    return 绑定调用错误#返回构造函数

def 绑定失败(错误类,成员名,消息):#构造绑定失败
    """为一次失败的绑定调用创建该命名空间专用的拒绝。"""
    return 错误类(成员名,消息) if 错误类 is not None else 捕获错误(消息)#有声明类则用它

def 制作绑定错误类表(数据):#为全部命名空间建错误类
    """每个已声明错误类只建一次，使调用与isinstance共享构造函数身份。"""
    类表={}#全局名→构造函数
    for 命名空间 in 数据.get('namespaces',[]):#逐个命名空间
        描述=命名空间.get('errorClass')#可选错误类
        if 描述 is not None:#有声明才建
            类表[命名空间['global']]=制作绑定错误类(描述)#建类
    return 类表#返回表

def 接线应答(端口,待决):#把应答接到pending
    """把宿主应答路由进pending-call表：每条应答至多结算一次对应调用；未知id忽略。"""
    def 处理(消息):#每条宿主应答
        条目=待决.get(消息.get('id'))#按id取句柄
        if 条目 is None:#未知或重复
            return#丢
        del 待决[消息['id']]#先摘掉，保证只结算一次
        if 消息.get('ok'):#成功分支
            值=解码工人json(消息.get('value'))#解码线路值
            if 值 is None:#有损则拒
                条目['reject'](捕获错误('binding resolution must be lossless JSON'))#拒绝
            else:#无损则决议
                条目['resolve'](值)#决议
        else:#失败分支
            条目['reject'](捕获错误(消息.get('message','binding failed')))#用宿主说明拒绝
    端口.on('message',处理)#登记监听

def 制作命名空间们(数据,端口,待决,下一编号,错误类表=None):#构造程序可见命名空间
    """构造程序看到的绑定命名空间对象：每个命名空间一个空映射，每个已声明名是可调用桥接。"""
    if 错误类表 is None:#缺省按声明建类
        错误类表=制作绑定错误类表(数据)#建表
    结果=[]#声明顺序的命名空间对象
    for 项 in 数据.get('namespaces',[]):#每个声明一项
        全局=项['global']#全局名
        名字们=项.get('names',[])#成员名
        错误类=错误类表.get(全局)#该命名空间的拒绝类
        命名空间={}#空映射对象
        for 名 in 名字们:#每个成员名
            def 桥接(参数,_名=名,_全局=全局,_错误类=错误类):#异步桥接函数
                try:#快照可能抛
                    脱离=快照代码json值(参数)#脱离为无损JSON
                except Exception:#有损
                    脱离=None#视为无效实参
                if 脱离 is None:#不是无损JSON
                    raise 绑定失败(_错误类,_名,'binding arguments must be lossless JSON')#posting前拒绝
                盒子={'value':None,'error':None,'done':False}#结算盒
                def 决议(值):#成功
                    盒子['value']=值#记下
                    盒子['done']=True#完成
                def 拒绝(错误):#失败
                    盒子['error']=错误#记下
                    盒子['done']=True#完成
                编号=下一编号['value']#签发相关id
                下一编号['value']=编号+1#递增
                待决[编号]={'resolve':决议,'reject':lambda 错误,_拒=拒绝,_错=_错误类,_n=_名: _拒(绑定失败(_错,_n,str(错误)))}#登记
                try:#post可能失败
                    端口.postMessage({'type':'call','id':编号,'global':_全局,'name':_名,'args':编码工人json(脱离)})#发出绑定调用
                except Exception as 错误:#克隆失败
                    del 待决[编号]#立刻摘掉
                    raise 绑定失败(_错误类,_名,'binding arguments must be structured-cloneable: '+str(错误))#拒绝
                while not 盒子['done']:#自旋等待应答（工人线程内；宿主泵并发投递）
                    pass#等
                if 盒子['error'] is not None:#失败
                    raise 盒子['error']#抛出
                return 盒子['value']#成功值
            命名空间[名]=桥接#挂成员
        结果.append(命名空间)#收入
    return 结果#返回列表

def 跑工人主逻辑(端口,数据,流们=None):#工人主执行
    """跑一份程序体，允许顶层逻辑，并恰好投递一条终态done消息；程序抛错成为其error字段。"""
    日志=日志缓冲(#外层日志账本
        数据['maxOutputBytes'],#配置上限
        lambda 文本:端口.postMessage({'type':'log','text':文本}),#急切把日志发给宿主
        lambda:端口.postMessage({'type':'output-limit'}),#触顶时通知宿主
    )#结束日志缓冲
    还原们=[]#流补丁还原函数列表
    if 流们 is not None:#有标准流则劫持写出
        标准出=流们.get('stdout') if isinstance(流们,dict) else getattr(流们,'stdout',None)#stdout
        标准错=流们.get('stderr') if isinstance(流们,dict) else getattr(流们,'stderr',None)#stderr
        if 标准出 is not None:#有stdout
            还原们.append(劫持流写出(日志,标准出))#劫持stdout
        if 标准错 is not None:#有stderr
            还原们.append(劫持流写出(日志,标准错))#劫持stderr
    待决={}#飞行中绑定调用
    接线应答(端口,待决)#把宿主应答接到pending
    下一编号={'value':1}#相关id从1起
    错误类表=制作绑定错误类表(数据)#按声明建错误类
    命名空间们=制作命名空间们(数据,端口,待决,下一编号,错误类表)#物化命名空间对象
    控制台=制作控制台垫片(日志)#缩小版console
    全局环境={'console':控制台,'__builtins__':{}}#程序可见全局（空builtins防逃逸；绑定另行注入）
    for 下标,项 in enumerate(数据.get('namespaces',[])):#按声明注入
        全局环境[项['global']]=命名空间们[下标]#命名空间全局
        描述=项.get('errorClass')#可选错误类
        if 描述 is not None:#有声明
            全局环境[描述['name']]=错误类表[项['global']]#注入错误类
    完成=None#终态消息槽
    try:#程序体可能抛
        代码=数据.get('code','')#程序体
        编译=compile(代码,'<code-runtime>','exec')#编译
        本地={}#局部
        exec(编译,全局环境,本地)#执行
        值=本地.get('__dsh_result__',准备完成.缺席)#约定完成值槽；缺席则无value
        if 'result' in 本地:#兼容result名
            值=本地['result']#覆盖
        片段=准备完成(值,日志.remainingOutputBytes(),数据['maxOutputBytes'])#完成值或失败片段
        完成={'type':'done',**片段}#成功完成
    except BaseException as 错误:#程序抛错
        片段=准备异常(错误,日志.remainingOutputBytes(),数据['maxOutputBytes'])#有界异常片段
        完成={'type':'done',**片段}#异常完成
    for 还原 in 还原们:#拆流补丁（进程内测试需要；真实工人通常不需要）
        try:#还原可能抛
            还原()#还原
        except Exception:#忽略
            pass#收容
    端口.postMessage(完成)#恰好投递一条终态
