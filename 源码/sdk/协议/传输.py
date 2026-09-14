import json,threading,uuid#JSON、互斥与请求 id
from concurrent.futures import Future as 原生结果#单次操作结果

__all__=['JSONRPC响应错误','JSONRPC传输对等端','换行JSONRPC传输','操作任务','已中止','中止信号','中止控制器']#仅中文公开名

class JSONRPC传输错误(Exception):
    """本包异常基类。"""

class 操作任务:
    """单次操作的 Future 包装，只留 等待。"""
    def __init__(自身):
        """构造未决任务。"""
        自身._未来=原生结果()#底层 Future

    def 兑现(自身,值=None):
        """成功结算。"""
        if not 自身._未来.done():#尚未结算
            自身._未来.set_result(值)#写入结果
        return 值#返回兑现值

    def 拒绝(自身,错误):
        """失败结算。"""
        if not 自身._未来.done():#尚未结算
            if isinstance(错误,BaseException):#已是异常
                自身._未来.set_exception(错误)#原样拒绝
            else:#非异常
                包装=JSONRPC传输错误('任务被拒绝')#包装拒绝
                包装.原因=错误#附加属性
                自身._未来.set_exception(包装)#包装拒绝

    def 等待(自身,超时=None):
        """阻塞等到结算。"""
        return 自身._未来.result(timeout=超时)#取结果或抛错

class 中止信号:
    """threading.Event 取消通道。"""
    def __init__(自身,已中止标志=False):
        """创建一条取消通道。"""
        自身._事件=threading.Event()#中止标志
        自身._异常=None#中止时抛出的异常
        if 已中止标志:#创建时已中止
            自身._事件.set()#置位
            自身._异常=JSONRPC传输错误('JSON-RPC 请求已中止')#默认

    def 触发(自身,原因=None):
        """标记中止。"""
        if 自身._事件.is_set():#只触发一次
            return#已触发
        if isinstance(原因,BaseException):#已是异常
            自身._异常=原因#承载
        elif 原因 is not None:#非异常
            错=JSONRPC传输错误('JSON-RPC 请求已中止：'+str(原因))#包装
            自身._异常=错#记下
        else:#无原因
            自身._异常=JSONRPC传输错误('JSON-RPC 请求已中止')#默认
        自身._事件.set()#置位

class 中止控制器:
    """发出中止的控制器。"""
    def __init__(自身):
        """创建配套信号。"""
        自身.信号=中止信号()#本控制器的信号

    def 中止(自身,原因=None):
        """中止配套信号。"""
        自身.信号.触发(原因)#触发一次

def 已中止(信号):
    """信号是否已中止。无信号视为未中止。"""
    if 信号 is None:#无信号
        return False#未中止
    return 信号._事件.is_set()#Event 置位

def 对象参数(参数):
    """把 JSON-RPC params 归一成普通对象。空 dict 在 JS 为真，这里只认 dict。"""
    if isinstance(参数,dict):#普通对象
        return 参数#原样
    return {}#非普通对象则空对象

def 中止错误(原因):
    """把中止原因归一成拒绝用的异常。"""
    if isinstance(原因,BaseException):#已是异常
        return 原因#原样
    return JSONRPC传输错误('JSON-RPC 请求已中止：'+str(原因))#包一层消息

def 错误消息(错误):
    """取出错误消息。"""
    return str(错误)#字符串化

class JSONRPC响应错误(JSONRPC传输错误):
    """JSON-RPC 错误响应，保留线上 code 与可选 data。"""
    def __init__(自身,码,消息,数据=None):
        """记下线上错误码、消息与可选载荷。"""
        super().__init__(消息)#用线上消息构造
        自身.code=码#线上错误码；对端未给时为 None
        自身.message=消息#线上错误消息
        自身.data=数据#可选结构化错误载荷
        自身.name='JsonRpcResponseError'#固定错误名

class JSONRPC传输对等端:
    """运行时服务端与 SDK 客户端共用的出站请求与通知面。"""
    def 请求(自身,方法,参数):
        """发送请求并等待响应。"""
        raise NotImplementedError#子类实现

    def 通知(自身,方法,参数=None):
        """发送通知；省略 params 则不写 params 成员。"""
        raise NotImplementedError#子类实现

class 换行JSONRPC传输(JSONRPC传输对等端):
    """基于调用方拥有的流的按行端点。启动挂上监听；关闭卸掉监听并拒绝未完成请求，不销毁流。"""
    def __init__(自身,输入流,输出流):
        """记下入站与出站流。"""
        自身.输入=输入流#入站字节/文本流
        自身.输出=输出流#出站字节/文本流
        自身.缓冲=''#尚未凑成完整行的文本缓冲
        自身.已启动=False#是否已挂上输入监听
        自身.请求处理=None#当前入站请求处理函数
        自身.通知处理=None#当前入站通知处理函数
        自身.未决={}#按 id 登记的未完成请求
        自身.锁=threading.Lock()#未决与缓冲互斥
        自身._读线程=None#后台读线程
        自身._写锁=threading.Lock()#写出互斥

    def 启动(自身):
        """幂等。"""
        if 自身.已启动:#已启动
            return#不再挂监听
        自身.已启动=True#标记已启动
        def 读循环():
            """读到 EOF 或出错为止。"""
            try:
                while True:#直到 EOF
                    if hasattr(自身.输入,'readline'):#按行可读
                        行=自身.输入.readline()#读一行
                        if 行=='' or 行 is None:#EOF
                            break#结束
                        if isinstance(行,bytes):#字节行
                            行=行.decode('utf-8')#解码
                        自身._处理数据(行)#喂入
                        continue#下一行
                    块=自身.输入.read(65536)#一块
                    if not 块:#EOF
                        break#结束
                    if isinstance(块,bytes):#字节块
                        块=块.decode('utf-8')#解码
                    自身._处理数据(块)#喂入
            except BaseException as 错误:
                包装=错误 if isinstance(错误,BaseException) else JSONRPC传输错误(str(错误))#归一
                自身._失败未决(包装)#拒绝未决
                return#结束读线程
            自身._失败未决(JSONRPC传输错误('JSON-RPC 输入已关闭'))#输入关闭
        自身._读线程=threading.Thread(target=读循环,daemon=True)#后台线程
        自身._读线程.start()#启动

    def 关闭(自身):
        """在启动之前调用也安全。不销毁流。"""
        自身._失败未决(JSONRPC传输错误('JSON-RPC 传输已关闭'))#拒绝所有未完成请求

    def 当请求(自身,处理函数):
        """安装请求处理函数，替换先前的处理函数。"""
        自身.请求处理=处理函数#替换

    def 当通知(自身,处理函数):
        """安装通知处理函数，替换先前的处理函数。"""
        自身.通知处理=处理函数#替换

    def 请求(自身,方法,参数,信号=None):
        """发送请求并等待响应；可选中止信号。同步返回结果。"""
        标识='req_'+uuid.uuid4().hex#无连字符请求 id
        消息={'jsonrpc':'2.0','id':标识,'method':方法,'params':参数}#组装请求帧
        等待=操作任务()#为本 id 挂起
        if 已中止(信号):#已经中止
            等待.拒绝(中止错误(信号._异常 if 信号 is not None else None))#立刻拒绝
            return 等待.等待()#抛出
        def 监视中止():
            """中止时清 pending 并拒绝。"""
            if 信号 is None:#无信号
                return#无需
            信号._事件.wait()#等到中止
            with 自身.锁:#互斥
                自身.未决.pop(标识,None)#丢掉该 id
            等待.拒绝(中止错误(信号._异常))#拒绝
        if 信号 is not None:#调用方给了放弃信号
            监视线程=threading.Thread(target=监视中止,daemon=True)#监视中止
            监视线程.start()#启动
        def 兑现(值):
            """成功回调。"""
            等待.兑现(值)#把结果交给调用方
        def 拒绝(错误):
            """失败回调。"""
            等待.拒绝(错误)#把错误交给调用方
        with 自身.锁:#互斥
            自身.未决[标识]={'兑现':兑现,'拒绝':拒绝}#登记未完成请求
        try:
            自身._写出(消息)#写到输出流
        except BaseException as 错误:
            with 自身.锁:#互斥
                自身.未决.pop(标识,None)#清掉 pending
            等待.拒绝(错误 if isinstance(错误,BaseException) else JSONRPC传输错误(str(错误)))#拒绝
        return 等待.等待()#同步交出结果

    def 通知(自身,方法,参数=None):
        """省略 params 则不写该成员。"""
        if 参数 is None:#无 params
            自身._写出({'jsonrpc':'2.0','method':方法})#省略 params
        else:#有 params
            自身._写出({'jsonrpc':'2.0','method':方法,'params':参数})#带 params

    def 刷出(自身):
        """等待此前帧写出落定。空屏障不发出字节。同步返回。"""
        if hasattr(自身.输出,'flush'):#可刷新
            自身.输出.flush()#刷新

    def _处理数据(自身,块):
        """拼缓冲并切行。"""
        自身.缓冲+=块#拼进缓冲
        自身._切行()#尽量切出完整行

    def _切行(自身):
        """直到没有完整换行。"""
        while True:#切行循环
            换行=自身.缓冲.find('\n')#找下一个换行
            if 换行<0:#没有完整行
                break#停
            行=自身.缓冲[:换行].strip()#取出并去掉首尾空白
            自身.缓冲=自身.缓冲[换行+1:]#剩下未处理缓冲
            if 行=='':#空行
                continue#跳过
            threading.Thread(target=自身._处理行,args=(行,),daemon=True).start()#异步处理该行

    def _处理行(自身,行):
        """畸形 JSON 忽略。"""
        try:
            消息=json.loads(行)#解析帧
        except json.JSONDecodeError:
            return#忽略本行
        if not isinstance(消息,dict):#非对象帧
            return#忽略
        标识=消息['id'] if 'id' in 消息 else None#可能的请求/响应 id
        方法=消息['method'] if 'method' in 消息 else None#可能的方法名
        有标识=isinstance(标识,str) or (isinstance(标识,(int,float)) and not isinstance(标识,bool))#合法 id
        if 有标识 and isinstance(方法,str):#入站请求
            参数=消息['params'] if 'params' in 消息 else None#params
            自身._处理入站请求(标识,方法,对象参数(参数))#派发请求
            return#本行处理完
        if 有标识:#只有 id：入站响应
            自身._处理入站响应(标识,消息)#交给 pending 认领
            return#本行处理完
        if isinstance(方法,str):#只有 method：入站通知
            处理=自身.通知处理#有处理函数才调用
            if 处理 is not None:#有处理函数
                参数=消息['params'] if 'params' in 消息 else None#params
                处理(方法,对象参数(参数))#调用

    def _处理入站请求(自身,标识,方法,参数):
        """未安装处理函数返回 -32601；处理失败返回 -32603。"""
        处理=自身.请求处理#当前请求处理函数
        if 处理 is None:#未安装处理函数
            自身._写出错误(标识,-32601,'找不到方法：'+str(方法))#方法未找到
            return#不再往下
        try:
            结果=处理(方法,参数)#同步业务结果
            自身._写出({'jsonrpc':'2.0','id':标识,'result':结果})#写出成功响应
        except BaseException as 错误:
            自身._写出错误(标识,-32603,错误消息(错误))#内部错误

    def _处理入站响应(自身,标识,帧):
        """未知 id 忽略。帧为 dict。"""
        with 自身.锁:#互斥
            未决=自身.未决.pop(标识,None)#按 id 查找并认领
        if 未决 is None:#未知 id
            return#忽略
        if 'error' in 帧 and isinstance(帧['error'],dict):#对端给了 error 对象
            错误体=帧['error']#error
            原始码=错误体['code'] if 'code' in 错误体 else None#可能的错误码
            码=原始码 if isinstance(原始码,(int,float)) and not isinstance(原始码,bool) else None#非数字视为未给
            原始消息=错误体['message'] if 'message' in 错误体 else None#可能的消息
            消息=原始消息 if isinstance(原始消息,str) else 'JSON-RPC 错误'#默认消息
            数据=错误体['data'] if 'data' in 错误体 else None#可选 data
            未决['拒绝'](JSONRPC响应错误(码,消息,数据))#拒绝为 JSONRPC响应错误
            return#错误响应处理完
        结果=帧['result'] if 'result' in 帧 else None#成功 result
        未决['兑现'](结果)#成功则兑现 result

    def _写出错误(自身,标识,码,消息):
        """标准 JSON-RPC 错误对象。"""
        自身._写出({'jsonrpc':'2.0','id':标识,'error':{'code':码,'message':消息}})#写出

    def _写出(自身,消息):
        """序列化后加换行写出。"""
        行=json.dumps(消息,ensure_ascii=False,separators=(',',':'),allow_nan=False)+'\n'#紧凑 JSON 行
        with 自身._写锁:#写出互斥
            编码=getattr(自身.输出,'encoding',None)#文本流编码
            if 编码 is not None:#文本模式
                自身.输出.write(行)#写文本
            else:#二进制
                自身.输出.write(行.encode('utf-8'))#写字节
            if hasattr(自身.输出,'flush'):#可刷新
                自身.输出.flush()#刷新

    def _失败未决(自身,错误):
        """快照后清空，避免重复拒绝。"""
        with 自身.锁:#互斥
            等待者=list(自身.未决.values())#先快照
            自身.未决.clear()#立刻清空
        for 一项 in 等待者:#逐个拒绝
            一项['拒绝'](错误)#拒绝
