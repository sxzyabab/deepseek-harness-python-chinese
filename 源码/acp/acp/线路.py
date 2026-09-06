"""本包内嵌的 ACP 智能体侧 NDJSON JSON-RPC 最小线路。

对齐上游对 `@agentclientprotocol/sdk` 的消费面（AgentSideConnection / ndJsonStream / RequestError / PROTOCOL_VERSION）。
公开面仅中文名。方法名与错误码字面量保持 ACP 线约定。
"""
import json,threading#JSON 与读写线程
from concurrent.futures import Future as 原生结果#单次操作结果

__all__=[#仅中文公开名
    '协议版本','ACP线路错误','请求错误','NDJSON流','智能体侧连接','操作任务','创建NDJSON流',
]#公开面结束

协议版本=1#ACP 协议版本常量（与 SDK PROTOCOL_VERSION 对齐的本桥接钉值）

class ACP线路错误(Exception):
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
                自身._未来.set_exception(ACP线路错误(str(错误)))#包装拒绝

    def 等待(自身,超时=None):
        """阻塞等到结算。"""
        return 自身._未来.result(timeout=超时)#取结果或抛错

class 请求错误(ACP线路错误):
    """ACP 线路错误，保留 code 与可选 data。"""
    def __init__(自身,码,消息,数据=None):
        """记下错误码、消息与可选载荷。"""
        super().__init__(消息)#消息
        自身.code=码#错误码
        自身.message=消息#消息
        自身.data=数据#可选 data
        自身.name='RequestError'#固定名

    @staticmethod
    def 非法参数(数据,细节):
        """把非法参数细节保留在线路错误消息里。"""
        return 请求错误(-32602,细节,数据)#invalid params

    @staticmethod
    def 内部错误(数据,细节):
        """把失败细节保留为内部错误。"""
        return 请求错误(-32603,细节,数据)#internal error

class NDJSON流:
    """可读/可写字节或文本流对，供智能体侧连接使用。"""
    def __init__(自身,写出流,读入流):
        """记下写出与读入。"""
        自身.写出=写出流#出站
        自身.读入=读入流#入站

def 创建NDJSON流(写出流,读入流):
    """测试覆盖或 stdio NDJSON。"""
    return NDJSON流(写出流,读入流)#包装

class 智能体侧连接:
    """打开智能体侧连接：入站方法派发到 makeAgent 返回的处理器，出站 sessionUpdate / requestPermission。"""
    def __init__(自身,铸造智能体,流):
        """铸造处理器并开始读帧。"""
        自身.流=流#传输流
        自身.写锁=threading.Lock()#写出互斥
        自身.未决={}#出站请求 id → 任务
        自身.下一标识=1#下一个出站 id
        自身.已关闭=操作任务()#连接关闭任务
        自身._关闭落定=False#是否已兑现关闭
        自身.智能体=铸造智能体(自身)#记下连接后铸造 ACP Agent
        自身._读线程=threading.Thread(target=自身._读循环,daemon=True)#后台读
        自身._读线程.start()#启动

    @property
    def 已关闭承诺(自身):
        """对齐上游 conn.closed。返回关闭任务。"""
        return 自身.已关闭#任务

    def 会话更新(自身,通知):
        """发送协议更新通知。同步返回。"""
        自身._通知('session/update',通知)#出站通知

    def 请求许可(自身,参数):
        """session/request_permission。同步返回结果。"""
        return 自身._请求('session/request_permission',参数)#出站请求

    def _通知(自身,方法,参数):
        """省略响应。"""
        自身._写出({'jsonrpc':'2.0','method':方法,'params':参数})#通知帧

    def _请求(自身,方法,参数):
        """等待响应。同步返回结果。"""
        等待=操作任务()#结果
        with 自身.写锁:#互斥取 id
            标识=自身.下一标识#分配
            自身.下一标识+=1#递增
            自身.未决[标识]=等待#登记
        try:
            自身._写出({'jsonrpc':'2.0','id':标识,'method':方法,'params':参数})#请求帧
        except BaseException as 错误:
            自身.未决.pop(标识,None)#清 pending
            if isinstance(错误,BaseException):#已是异常
                等待.拒绝(错误)#拒绝
            else:#非异常
                等待.拒绝(ACP线路错误(str(错误)))#包装
        return 等待.等待()#同步交出

    def _写出(自身,消息):
        """序列化后加换行。"""
        行=json.dumps(消息,ensure_ascii=False,separators=(',',':'),allow_nan=False)+'\n'#紧凑行
        with 自身.写锁:#写出互斥
            写出=自身.流.写出#出站流
            编码=getattr(写出,'encoding',None)#文本流编码
            if 编码 is not None:#文本
                写出.write(行)#写文本
            else:#二进制
                写出.write(行.encode('utf-8'))#写字节
            if hasattr(写出,'flush'):#可刷新
                写出.flush()#刷新

    def _读循环(自身):
        """派发请求/响应/通知。"""
        缓冲=''#行缓冲
        读入=自身.流.读入#入站
        try:
            while True:#直到 EOF
                if hasattr(读入,'readline'):#按行
                    行=读入.readline()#读一行
                    if 行=='' or 行 is None:#EOF
                        break#结束
                    if isinstance(行,bytes):#字节
                        行=行.decode('utf-8')#解码
                    自身._处理行(行.strip())#处理
                    continue#下一行
                块=读入.read(65536)#一块
                if not 块:#EOF
                    break#结束
                if isinstance(块,bytes):#字节
                    块=块.decode('utf-8')#解码
                缓冲+=块#拼
                while True:#切行
                    换行=缓冲.find('\n')#找换行
                    if 换行<0:#没有
                        break#停
                    行=缓冲[:换行].strip()#取出
                    缓冲=缓冲[换行+1:]#剩余
                    if 行!='':#非空
                        自身._处理行(行)#处理
        except BaseException as 错误:
            if isinstance(错误,BaseException):#已是异常
                自身._关闭(错误)#带错关闭
            else:#非异常
                自身._关闭(ACP线路错误(str(错误)))#包装关闭
            return#结束
        自身._关闭(None)#正常关闭

    def _处理行(自身,行):
        """畸形 JSON 忽略。"""
        try:
            消息=json.loads(行)#JSON
        except json.JSONDecodeError:
            return#忽略
        if not isinstance(消息,dict):#非对象
            return#忽略
        标识=消息['id'] if 'id' in 消息 else None#可能的 id
        方法=消息['method'] if 'method' in 消息 else None#可能的方法
        if 'id' in 消息 and 方法 is None:#入站响应
            等待=自身.未决.pop(标识,None)#认领
            if 等待 is None:#未知
                return#忽略
            if 'error' in 消息 and isinstance(消息['error'],dict):#错误响应
                错=消息['error']#错误体
                码=错['code'] if 'code' in 错 else None#错误码
                原始消息=错['message'] if 'message' in 错 else None#消息
                文案=原始消息 if isinstance(原始消息,str) and 原始消息!='' else 'ACP error'#默认消息
                数据=错['data'] if 'data' in 错 else None#可选 data
                等待.拒绝(请求错误(码,文案,数据))#拒绝
            else:#成功
                等待.兑现(消息['result'] if 'result' in 消息 else None)#兑现
            return#完
        if isinstance(方法,str):#入站请求或通知
            原始参数=消息['params'] if 'params' in 消息 else None#params
            参数=原始参数 if isinstance(原始参数,dict) else {}#非对象则空对象
            threading.Thread(target=自身._派发入站,args=(标识,方法,参数),daemon=True).start()#异步派发

    def _派发入站(自身,标识,方法,参数):
        """有 id 则回写响应。控制流错误按 name 字段识别。"""
        处理映射={#ACP 方法到智能体处理器
            'initialize':'initialize',#握手
            'authenticate':'authenticate',#认证
            'session/new':'newSession',#新建会话
            'session/prompt':'prompt',#提示
            'session/cancel':'cancel',#取消
        }#映射结束
        名=处理映射[方法] if 方法 in 处理映射 else None#处理器名
        try:
            if 名 is None:#未知方法
                raise 请求错误(-32601,'method not found: '+方法)#方法未找到
            处理=getattr(自身.智能体,名,None)#取出
            if 处理 is None:#无处理器
                raise 请求错误(-32601,'method not found: '+方法)#方法未找到
            结果=处理(参数)#同步调用
            if 标识 is not None:#有 id：响应
                自身._写出({'jsonrpc':'2.0','id':标识,'result':结果 if 结果 is not None else {}})#成功响应
        except BaseException as 错误:
            错误名=getattr(错误,'name',None)#结构名
            错误码=getattr(错误,'code',None)#结构码
            if 错误名=='RequestError':#线路错误
                if 标识 is not None:#有 id
                    消息=getattr(错误,'message',str(错误))#消息
                    自身._写出({'jsonrpc':'2.0','id':标识,'error':{'code':错误码,'message':消息}})#错误响应
                return#已写出
            if 标识 is not None:#其它错误
                自身._写出({'jsonrpc':'2.0','id':标识,'error':{'code':-32603,'message':str(错误)}})#内部错误

    def _关闭(自身,错误):
        """只落定一次。"""
        if 自身._关闭落定:#已关闭
            return#忽略
        自身._关闭落定=True#标记
        关闭错=错误 if 错误 is not None else ACP线路错误('ACP connection closed')#默认关闭
        for 等待 in list(自身.未决.values()):#拒绝未决
            等待.拒绝(关闭错)#拒绝
        自身.未决.clear()#清空
        if 错误 is not None:#带错关闭
            自身.已关闭.拒绝(错误)#拒绝关闭承诺
        else:#正常
            自身.已关闭.兑现(None)#兑现关闭
