"""工作线程侧执行逻辑，写成对着注入端口的普通函数，以便单元套件能在进程内对着假端口跑每一行。"""
import traceback#异常堆栈渲染
from .输出json import json字符串字节上限,json值字节上限,截断json字符串字节#JSON字节账本
from .工作线程json import 快照代码json值,编码工作线程json,解码工作线程json#无损JSON编解码

捕获错误=Exception#钉死异常基类，避免模型改写
控制台级别=('log','info','warn','error','debug')#五种日志级别
检视选项={'depth':4,'maxArrayLength':100,'maxStringLength':10000}#有界inspect选项：深到有用，又封顶以免病态值撑爆渲染

class 引导端口:#bootstrap所需的端口API——由父端口与测试假端口满足
    """工作线程/测试共用端口面（约定：实现投递与监听）。"""
    def 投递(自身,消息):#向宿主发消息
        """向宿主发消息。消息是 dict。"""
        raise NotImplementedError('引导端口.投递')#子类实现

    def 监听(自身,事件,监听器):#监听宿主应答
        """监听message事件上的宿主应答。"""
        raise NotImplementedError('引导端口.监听')#子类实现

class 可补丁流:#可写流的write槽，即bootstrap所打补丁的形态
    """可打补丁的写出流（约定：实现write，对齐 Python 流协议名）。"""
    def write(自身,块,*位置参数):#写出一块数据
        """写出一块数据。"""
        raise NotImplementedError('可补丁流.write')#子类实现

def 空触顶():#无触顶回调
    """缺省触顶：什么也不做。"""
    return None#无动作

class 日志缓冲:#日志字节账本
    """共享外层JSON字节预算下的有序文本捕获，每条落地即交给交付槽。一旦耗尽，发出装得下的前缀并报告一次上限。"""
    def __init__(自身,最大字节,交付槽,触顶回调=None):#构造账本
        """记下上限、交付槽与可选触顶回调。"""
        自身.最大字节=最大字节#外层字节上限
        自身.交付槽=交付槽#每条文本的交付槽
        自身.触顶回调=触顶回调 if 触顶回调 is not None else 空触顶#首次触顶回调
        自身.已用字节=2#空日志数组[]占2字节
        自身.条数=0#已准入条数
        自身.已截断=False#是否已因上限截断

    def 推入(自身,文本):#准入一条日志
        """把文本发给交付槽，并从预算扣费（耗尽后丢弃并只标记一次）。"""
        if 自身.已截断:#已触顶则后续全丢
            return#忽略
        分隔=1 if 自身.条数>0 else 0#非首条要计入逗号
        可用=自身.最大字节-自身.已用字节-分隔#剩余可用字节
        串字节=json字符串字节上限(文本,可用)#全文能否装下
        if 串字节 is None:#装不下则截断
            自身.已截断=True#标记已触顶
            前缀=截断json字符串字节(文本,可用)#取装得下的前缀
            if len(前缀)>0:#前缀非空才交付；判 length
                前缀字节=json字符串字节上限(前缀,可用)#再计量前缀
                if 前缀字节 is None:#前缀越界是账本内部错误
                    raise 捕获错误('worker output ledger produced an oversized log prefix')#内部错误
                自身.已用字节+=前缀字节+分隔#计入前缀与逗号
                自身.条数+=1#条数加一
                自身.交付槽(前缀)#交付截断前缀
            自身.触顶回调()#报告触顶
            return#不再处理原文
        自身.已用字节+=串字节+分隔#计入全文与逗号
        自身.条数+=1#条数加一
        自身.交付槽(文本)#交付原文

    def 剩余输出字节(自身):#剩余外层预算
        """完成值或失败消息还剩的精确JSON字节预算。"""
        return 自身.最大字节-自身.已用字节#上限减去已用

def 制作控制台垫片(日志):#构造缩小版console
    """替换用的console：五个带级别的方法把实参渲染后再写入缓冲。"""
    def 渲染(参数列表):#把实参渲成一行
        """把实参渲成一行文本。"""
        段列表=[]#片段
        for 参数 in 参数列表:#逐个
            if isinstance(参数,str):#字符串原样
                段列表.append(参数)#原样
            else:#其余有界repr
                文本=repr(参数)#渲染
                上限=检视选项['maxStringLength']#字符串长度封顶
                if len(文本)>上限:#过长则截断；判 length
                    文本=文本[0:上限]+'...'#截断标记
                段列表.append(文本)#收入
        return ' '.join(段列表)#空格拼接
    垫片={}#空映射shim
    for 级别 in 控制台级别:#为每个级别挂方法
        def 方法(*位置参数,账本=日志,渲染行=渲染):#渲染后推入账本
            """把实参渲成一行再推入账本。"""
            账本.推入(渲染行(位置参数))#交付
        垫片[级别]=方法#挂方法
    return 垫片#返回五方法对象

def 空还原():#流不可补丁时的还原
    """什么也不还原。"""
    return None#无动作

def 劫持流写出(日志,流):#劫持流写出进日志缓冲
    """把流的write重定向进日志缓冲，使裸写出按发出顺序与console输出并列。返回还原函数。"""
    原写出=流.write#保存原write
    def 写出(块,*位置参数):#替换写出
        """把写出块记入日志。"""
        文本=块 if isinstance(块,str) else str(块)#字符串原样，其余转字符串
        日志.推入(文本)#准入日志
        回调=None#可选回调槽
        for 候选 in 位置参数[0:2]:#在encoding/callback槽里找函数
            if callable(候选):#找到回调
                回调=候选#记下
                break#停找
        if 回调 is not None:#有回调则异步成功
            try:#回调本身可能抛
                回调(None)#声称已写出
            except Exception:#回调可抛任意类型，工作线程不得崩
                pass#收容
        return True#对外声称已写出
    try:#挂上替换
        流.write=写出#替换写出
    except Exception:#流不可补丁则跳过；write 槽可能只读
        return 空还原#空还原
    def 还原():#还原原write
        """还原原 write。"""
        try:#还原可能失败
            流.write=原写出#还原
        except Exception:#忽略只读槽
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

def 准备完成(值,剩余输出字节,最大输出字节):#准备完成值片段
    """为done消息准备程序完成值。只有无损JSON能过线；装不进剩余预算则报output-limit。None 是合法 JSON null。"""
    try:#快照可能因有损值失败
        快照=快照代码json值(值)#尝试脱离为无损JSON
    except Exception:#快照对任意值没有收窄契约
        快照=None#视为无效完成
    if 快照 is None:#不是无损JSON
        return 准备失败('invalid-output','program completion must be lossless JSON',剩余输出字节,最大输出字节)#改报invalid-output
    if json值字节上限(快照,剩余输出字节) is None:#快照装不进剩余预算
        return 输出超限(最大输出字节)#改报output-limit
    return {'value':编码工作线程json(快照)}#编码后作为完成值

def 准备异常(错误,剩余输出字节,最大输出字节):#准备异常片段
    """准备程序抛出的值，不把无界堆栈或字符串送过工作线程端口。"""
    try:#渲染本身也可能抛
        if isinstance(错误,BaseException):#异常
            详情=''.join(traceback.format_exception(type(错误),错误,错误.__traceback__))#堆栈优先
            if len(详情.strip())==0:#无堆栈；判 length
                详情=str(错误)#退回消息
        else:#非异常
            详情=str(错误)#强制转
        消息=详情 if isinstance(详情,str) else str(详情)#保证字符串
    except Exception:#str/traceback 对任意抛出值没有收窄契约
        消息='program threw an unrenderable value'#固定兜底说明
    return 准备失败('exception',消息,剩余输出字节,最大输出字节)#按异常准入

def 定义绑定错误字段(错误,键,值):#给错误实例挂自有字段
    """定义一个公开的绑定错误字段。"""
    setattr(错误,键,值)#挂上

def 制作绑定错误类(描述符):#构造一个绑定错误类
    """物化某一命名空间声明的真实错误构造函数。描述符是 dict。"""
    类名=描述符['name']#类名
    成员属性=描述符['memberNameProperty']#成员名属性
    class 绑定调用错误(捕获错误):#继承钉死的异常
        """命名空间专用拒绝。"""
        def __init__(自身,成员名,消息):#(失败成员,说明)
            """记下成员名与说明。"""
            super().__init__(消息)#先设消息
            定义绑定错误字段(自身,'name',类名)#公开类名
            定义绑定错误字段(自身,成员属性,成员名)#公开失败成员名
    绑定调用错误.__name__=类名#对齐类名
    return 绑定调用错误#返回构造函数

def 绑定失败(错误类,成员名,消息):#构造绑定失败
    """为一次失败的绑定调用创建该命名空间专用的拒绝。"""
    if 错误类 is not None:#有声明类
        return 错误类(成员名,消息)#用声明类
    return 捕获错误(消息)#普通异常

def 制作绑定错误类表(数据):#为全部命名空间建错误类
    """每个已声明错误类只建一次，使调用与isinstance共享构造函数身份。数据是 dict。"""
    类表={}#全局名→构造函数
    for 命名空间 in 数据['namespaces']:#逐个命名空间
        if 'errorClass' not in 命名空间:#无声明则跳过
            continue#下一项
        描述=命名空间['errorClass']#错误类
        类表[命名空间['global']]=制作绑定错误类(描述)#建类
    return 类表#返回表

def 接线应答(端口,待决):#把应答接到pending
    """把宿主应答路由进pending-call表：每条应答至多结算一次对应调用；未知id忽略。"""
    def 处理(消息):#每条宿主应答
        """按 id 结算一次对应调用。消息是 dict。"""
        if 'id' not in 消息:#无编号
            return#丢
        编号=消息['id']#调用编号
        if 编号 not in 待决:#未知或重复
            return#丢
        条目=待决[编号]#句柄
        del 待决[编号]#先摘掉，保证只结算一次
        if 'ok' in 消息 and 消息['ok'] is True:#成功分支
            值=解码工作线程json(消息['value'] if 'value' in 消息 else None)#解码线路值
            if 值 is None:#有损则拒
                条目['reject'](捕获错误('binding resolution must be lossless JSON'))#拒绝
            else:#无损则决议
                条目['resolve'](值)#决议
        else:#失败分支
            说明=消息['message'] if 'message' in 消息 else 'binding failed'#宿主说明
            条目['reject'](捕获错误(说明))#用宿主说明拒绝
    端口.监听('message',处理)#登记监听

def 制作命名空间列表(数据,端口,待决,下一编号,错误类表=None):#构造程序可见命名空间
    """构造程序看到的绑定命名空间对象：每个命名空间一个空映射，每个已声明名是可调用桥接。数据是 dict。"""
    if 错误类表 is None:#缺省按声明建类
        错误类表=制作绑定错误类表(数据)#建表
    结果=[]#声明顺序的命名空间对象
    for 项 in 数据['namespaces']:#每个声明一项
        全局=项['global']#全局名
        名字列表=项['names'] if 'names' in 项 else []#成员名
        错误类=错误类表[全局] if 全局 in 错误类表 else None#该命名空间的拒绝类
        命名空间={}#空映射对象
        for 名 in 名字列表:#每个成员名
            def 桥接(参数,成员名=名,全局名=全局,拒绝类=错误类):#同步桥接函数
                """把一次绑定调用发到宿主并自旋等到应答。"""
                try:#快照可能抛
                    脱离=快照代码json值(参数)#脱离为无损JSON
                except Exception:#快照对任意值没有收窄契约
                    脱离=None#视为无效实参
                if 脱离 is None:#不是无损JSON
                    raise 绑定失败(拒绝类,成员名,'binding arguments must be lossless JSON')#posting前拒绝
                盒子={'value':None,'error':None,'done':False}#结算盒
                def 决议(值):#成功
                    """记下成功值。"""
                    盒子['value']=值#记下
                    盒子['done']=True#完成
                def 拒绝(错误):#失败
                    """记下失败。"""
                    盒子['error']=错误#记下
                    盒子['done']=True#完成
                def 拒绝并包装(错误):#失败并包成绑定错误
                    """把宿主拒绝包成命名空间错误。"""
                    拒绝(绑定失败(拒绝类,成员名,str(错误)))#包装
                编号=下一编号['value']#签发相关id
                下一编号['value']=编号+1#递增
                待决[编号]={'resolve':决议,'reject':拒绝并包装}#登记
                try:#投递可能失败
                    端口.投递({'type':'call','id':编号,'global':全局名,'name':成员名,'args':编码工作线程json(脱离)})#发出绑定调用
                except Exception as 错误:#克隆失败
                    del 待决[编号]#立刻摘掉
                    raise 绑定失败(拒绝类,成员名,'binding arguments must be structured-cloneable: '+str(错误))#拒绝
                while not 盒子['done']:#自旋等待应答（工作线程线程内；宿主泵并发投递）
                    pass#等
                if 盒子['error'] is not None:#失败
                    raise 盒子['error']#抛出
                return 盒子['value']#成功值
            命名空间[名]=桥接#挂成员
        结果.append(命名空间)#收入
    return 结果#返回列表

def 执行工作线程主逻辑(端口,数据,流表=None):#工作线程主执行
    """跑一份程序体，允许顶层逻辑，并恰好投递一条终态done消息；程序抛错成为其error字段。数据是 dict；流表是 dict 或 None。"""
    def 交付日志(文本):#急切把日志发给宿主
        """把一条日志发给宿主。"""
        端口.投递({'type':'log','text':文本})#日志消息
    def 报告触顶():#触顶时通知宿主
        """通知宿主外层输出触顶。"""
        端口.投递({'type':'output-limit'})#触顶消息
    日志=日志缓冲(数据['maxOutputBytes'],交付日志,报告触顶)#外层日志账本
    还原列表=[]#流补丁还原函数列表
    if 流表 is not None:#有标准流则劫持写出
        if 'stdout' in 流表 and 流表['stdout'] is not None:#有stdout
            还原列表.append(劫持流写出(日志,流表['stdout']))#劫持stdout
        if 'stderr' in 流表 and 流表['stderr'] is not None:#有stderr
            还原列表.append(劫持流写出(日志,流表['stderr']))#劫持stderr
    待决={}#飞行中绑定调用
    接线应答(端口,待决)#把宿主应答接到pending
    下一编号={'value':1}#相关id从1起
    错误类表=制作绑定错误类表(数据)#按声明建错误类
    命名空间列表=制作命名空间列表(数据,端口,待决,下一编号,错误类表)#物化命名空间对象
    控制台=制作控制台垫片(日志)#缩小版console
    全局环境={'console':控制台,'__builtins__':{}}#程序可见全局（空builtins防逃逸；绑定另行注入）
    for 下标,项 in enumerate(数据['namespaces']):#按声明注入
        全局环境[项['global']]=命名空间列表[下标]#命名空间全局
        if 'errorClass' in 项:#有声明
            描述=项['errorClass']#错误类
            全局环境[描述['name']]=错误类表[项['global']]#注入错误类
    完成=None#终态消息槽
    try:#程序体可能抛
        代码=数据['code']#程序体
        编译=compile(代码,'<code-runtime>','exec')#编译
        本地={}#局部
        exec(编译,全局环境,本地)#执行
        if 'result' in 本地:#兼容result名
            片段=准备完成(本地['result'],日志.剩余输出字节(),数据['maxOutputBytes'])#有完成值
        elif '__dsh_result__' in 本地:#约定完成值槽
            片段=准备完成(本地['__dsh_result__'],日志.剩余输出字节(),数据['maxOutputBytes'])#有完成值
        else:#无完成值则省略 value 键
            片段={}#空片段
        完成={'type':'done',**片段}#成功完成
    except BaseException as 错误:#程序抛错
        片段=准备异常(错误,日志.剩余输出字节(),数据['maxOutputBytes'])#有界异常片段
        完成={'type':'done',**片段}#异常完成
    for 还原 in 还原列表:#拆流补丁（进程内测试需要；真实工作线程通常不需要）
        try:#还原可能抛
            还原()#还原
        except Exception:#还原对只读槽没有收窄契约
            pass#收容
    端口.投递(完成)#恰好投递一条终态
