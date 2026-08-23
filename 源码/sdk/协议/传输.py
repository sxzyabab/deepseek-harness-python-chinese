"""基于字节流的换行分隔 JSON-RPC 2.0。

对齐上游 `sdk/protocol/src/transport.ts`。公开面仅中文名。带 id 与 method 的帧是请求，只有 id 的是响应，只有 method 的是通知。畸形行忽略；处理失败变成错误帧。
"""
import json,threading,uuid#JSON、互斥与请求 id
from ...依赖 import cordis#外部依赖胶水
承诺=cordis.工具.承诺#承诺
是否thenable=cordis.工具.是否thenable#可等待判定

__all__=['JSONRPC响应错误','JSONRPC传输对等端','换行JSONRPC传输']#仅中文公开名

def 解开(值):#承诺则等待否则原样
    """承诺则等待，否则原样返回。"""
    if 是否thenable(值):#可等待
        return 值.等待()#等待承诺
    return 值#同步值

def 对象参数(参数):#把 JSON-RPC params 归一成普通对象
    """数组与标量塌成空对象。"""
    if 参数 and isinstance(参数,dict):#普通对象
        return 参数#原样
    return {}#非普通对象则空对象

def 中止错误(原因):#把中止原因归一成拒绝用的 Error
    """非 Exception 原因会字符串化。"""
    if isinstance(原因,BaseException):#已是异常
        return 原因#原样
    return Exception('JSON-RPC request aborted: '+str(原因))#包一层消息

def 错误消息(错误):#取出错误消息
    """传输只抛 Exception；其余用 str 兜底。"""
    if isinstance(错误,BaseException):#异常
        return str(错误)#字符串化
    return str(错误)#兜底

class JSONRPC响应错误(Exception):#对端错误响应转成的 Error
    """JSON-RPC 错误响应，保留线上 code 与可选 data。"""
    def __init__(自身,码,消息,数据=None):#记下 code/message/data
        """记下线上错误码、消息与可选载荷。"""
        super().__init__(消息)#用线上消息构造
        自身.code=码#线上错误码；对端未给时为 None
        自身.message=消息#线上错误消息
        自身.data=数据#可选结构化错误载荷
        自身.name='JsonRpcResponseError'#固定错误名

class JSONRPC传输对等端:#传输对等端出站面（协议约定，非强制基类）
    """运行时服务端与 SDK 客户端共用的出站请求与通知面。"""
    def 请求(自身,方法,参数):#发送请求并等待响应
        """发送请求并等待响应。"""
        raise NotImplementedError#子类实现
    def 通知(自身,方法,参数=None):#发送通知
        """发送通知；省略 params 则不写 params 成员。"""
        raise NotImplementedError#子类实现

class 换行JSONRPC传输(JSONRPC传输对等端):#换行分隔 JSON-RPC 传输
    """基于调用方拥有的流的按行端点。启动挂上监听；关闭卸掉监听并拒绝未完成请求，不销毁流。"""
    def __init__(自身,输入流,输出流):#保存调用方拥有的输入输出流
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

    def 启动(自身):#挂上输入监听并开始读帧
        """幂等。"""
        if 自身.已启动:#已启动
            return#不再挂监听
        自身.已启动=True#标记已启动
        def 读循环():#后台读入站
            """读到 EOF 或出错为止。"""
            try:#读流
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
            except BaseException as 错误:#输入出错
                自身._失败未决(错误 if isinstance(错误,Exception) else Exception(str(错误)))#拒绝未决
                return#结束读线程
            自身._失败未决(Exception('JSON-RPC input closed'))#输入关闭
        自身._读线程=threading.Thread(target=读循环,daemon=True)#后台线程
        自身._读线程.start()#启动

    def 关闭(自身):#卸掉监听并拒绝未完成请求
        """在启动之前调用也安全。不销毁流。"""
        自身._失败未决(Exception('JSON-RPC transport closed'))#拒绝所有未完成请求

    def 当请求(自身,处理函数):#登记入站请求处理函数
        """安装请求处理函数，替换先前的处理函数。"""
        自身.请求处理=处理函数#替换

    def 当通知(自身,处理函数):#登记入站通知处理函数
        """安装通知处理函数，替换先前的处理函数。"""
        自身.通知处理=处理函数#替换

    def 请求(自身,方法,参数,信号=None):#发送出站请求
        """发送请求并等待响应；可选中止信号。返回承诺。"""
        标识='req_'+uuid.uuid4().hex#无连字符请求 id
        消息={'jsonrpc':'2.0','id':标识,'method':方法,'params':参数}#组装请求帧
        等待=承诺()#为本 id 挂起
        卸中止=lambda:None#默认无 AbortSignal 可卸
        if 信号 is not None:#调用方给了放弃信号
            if getattr(信号,'aborted',False) or getattr(信号,'已中止',False):#已经中止
                等待.拒绝(中止错误(getattr(信号,'reason',None) or getattr(信号,'原因',None)))#立刻拒绝
                return 等待#不再登记
            def 当中止(*_剩余):#中止时清 pending 并拒绝
                """按信号原因拒绝。"""
                with 自身.锁:#互斥
                    自身.未决.pop(标识,None)#丢掉该 id
                等待.拒绝(中止错误(getattr(信号,'reason',None) or getattr(信号,'原因',None)))#拒绝
            加监听=getattr(信号,'addEventListener',None)#英文
            if 加监听 is None:#试中文
                加监听=getattr(信号,'添加监听',None)#中文
            if 加监听 is not None:#有监听 API
                try:#英文 once
                    加监听('abort',当中止,{'once':True})#听 abort
                except TypeError:#中文或无 once
                    加监听('abort',当中止)#听 abort
                def 卸中止():#响应到来时卸掉
                    """卸 abort 监听。"""
                    卸监听=getattr(信号,'removeEventListener',None)#英文
                    if 卸监听 is None:#试中文
                        卸监听=getattr(信号,'移除监听',None)#中文
                    if 卸监听 is not None:#有卸函数
                        卸监听('abort',当中止)#卸掉
        def 兑现(值):#成功时先卸 abort 再兑现
            """成功回调。"""
            卸中止()#卸 abort 监听
            等待.兑现(值)#把结果交给调用方
        def 拒绝(错误):#失败时先卸 abort 再拒绝
            """失败回调。"""
            卸中止()#卸 abort 监听
            等待.拒绝(错误)#把错误交给调用方
        with 自身.锁:#互斥
            自身.未决[标识]={'兑现':兑现,'拒绝':拒绝}#登记未完成请求
        try:#尝试写出请求帧
            自身._写出(消息)#写到输出流
        except BaseException as 错误:#写出失败则不再等待响应
            with 自身.锁:#互斥
                自身.未决.pop(标识,None)#清掉 pending
            卸中止()#卸 abort 监听
            等待.拒绝(错误 if isinstance(错误,Exception) else Exception(str(错误)))#拒绝
        return 等待#交给调用方等待

    def 通知(自身,方法,参数=None):#发送出站通知
        """省略 params 则不写该成员。"""
        if 参数 is None:#无 params
            自身._写出({'jsonrpc':'2.0','method':方法})#省略 params
        else:#有 params
            自身._写出({'jsonrpc':'2.0','method':方法,'params':参数})#带 params

    def 刷出(自身):#排空已排队写出
        """等待此前帧写出落定。空屏障不发出字节。返回承诺。"""
        等待=承诺()#屏障承诺
        try:#写空或 flush
            if hasattr(自身.输出,'flush'):#可刷新
                自身.输出.flush()#刷新
            等待.兑现(None)#成功
        except BaseException as 错误:#写出出错
            等待.拒绝(错误 if isinstance(错误,Exception) else Exception(str(错误)))#拒绝
        return 等待#交给调用方

    def _处理数据(自身,块):#处理输入数据块
        """拼缓冲并切行。"""
        自身.缓冲+=块#拼进缓冲
        自身._切行()#尽量切出完整行

    def _切行(自身):#从缓冲切出行并处理
        """直到没有完整换行。"""
        while True:#切行循环
            换行=自身.缓冲.find('\n')#找下一个换行
            if 换行<0:#没有完整行
                break#停
            行=自身.缓冲[:换行].strip()#取出并去掉首尾空白
            自身.缓冲=自身.缓冲[换行+1:]#剩下未处理缓冲
            if not 行:#空行
                continue#跳过
            threading.Thread(target=自身._处理行,args=(行,),daemon=True).start()#异步处理该行

    def _处理行(自身,行):#解析并派发一行
        """畸形 JSON 忽略。"""
        try:#尝试把该行当 JSON
            消息=json.loads(行)#解析帧
        except Exception:#JSON 语法错误
            return#忽略本行
        if not 消息 or not isinstance(消息,dict):#非对象帧
            return#忽略
        标识=消息.get('id')#可能的请求/响应 id
        方法=消息.get('method')#可能的方法名
        有标识=isinstance(标识,str) or (isinstance(标识,(int,float)) and not isinstance(标识,bool))#合法 id
        if 有标识 and isinstance(方法,str):#入站请求
            自身._处理入站请求(标识,方法,对象参数(消息.get('params')))#派发请求
            return#本行处理完
        if 有标识:#只有 id：入站响应
            自身._处理入站响应(标识,消息)#交给 pending 认领
            return#本行处理完
        if isinstance(方法,str):#只有 method：入站通知
            处理=自身.通知处理#有处理函数才调用
            if 处理 is not None:#有处理函数
                处理(方法,对象参数(消息.get('params')))#调用

    def _处理入站请求(自身,标识,方法,参数):#处理入站请求
        """未安装处理函数返回 -32601；处理失败返回 -32603。"""
        处理=自身.请求处理#当前请求处理函数
        if 处理 is None:#未安装处理函数
            自身._写出错误(标识,-32601,'method not found: '+str(方法))#方法未找到
            return#不再往下
        try:#调用处理函数
            结果=解开(处理(方法,参数))#等待业务结果
            自身._写出({'jsonrpc':'2.0','id':标识,'result':结果})#写出成功响应
        except BaseException as 错误:#处理函数抛错或拒绝
            自身._写出错误(标识,-32603,错误消息(错误))#内部错误

    def _处理入站响应(自身,标识,帧):#把响应交给 pending
        """未知 id 忽略。"""
        with 自身.锁:#互斥
            未决=自身.未决.pop(标识,None)#按 id 查找并认领
        if 未决 is None:#未知 id
            return#忽略
        错误体=帧.get('error')#对端 error
        if 错误体 and isinstance(错误体,dict):#对端给了 error 对象
            原始码=错误体.get('code')#可能的错误码
            码=原始码 if isinstance(原始码,(int,float)) and not isinstance(原始码,bool) else None#非数字视为未给
            原始消息=错误体.get('message')#可能的消息
            消息=原始消息 if isinstance(原始消息,str) else 'JSON-RPC error'#默认消息
            未决['拒绝'](JSONRPC响应错误(码,消息,错误体.get('data')))#拒绝为 JSONRPC响应错误
            return#错误响应处理完
        未决['兑现'](帧.get('result'))#成功则兑现 result

    def _写出错误(自身,标识,码,消息):#写出错误响应帧
        """标准 JSON-RPC 错误对象。"""
        自身._写出({'jsonrpc':'2.0','id':标识,'error':{'code':码,'message':消息}})#写出

    def _写出(自身,消息):#把对象写成一行 JSON
        """序列化后加换行写出。"""
        行=json.dumps(消息,ensure_ascii=False,separators=(',',':'))+'\n'#紧凑 JSON 行
        with 自身._写锁:#写出互斥
            编码=getattr(自身.输出,'encoding',None)#文本流编码
            if 编码:#文本模式
                自身.输出.write(行)#写文本
            else:#二进制
                自身.输出.write(行.encode('utf-8'))#写字节
            if hasattr(自身.输出,'flush'):#可刷新
                自身.输出.flush()#刷新

    def _失败未决(自身,错误):#拒绝并清空所有未完成请求
        """快照后清空，避免重复拒绝。"""
        with 自身.锁:#互斥
            等待者=list(自身.未决.values())#先快照
            自身.未决.clear()#立刻清空
        for 一项 in 等待者:#逐个拒绝
            一项['拒绝'](错误)#拒绝
