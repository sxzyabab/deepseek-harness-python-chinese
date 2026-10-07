'本包内嵌的 ACP 智能体侧 NDJSON JSON-RPC 最小线路'
import json,threading#JSON 与读写线程
from ...基础设施.js特性 import PromiseEX as 期约#连接关闭期约
from ...基础设施.通用工具.帧协议 import 换行帧解码器,编码ndjson行#换行帧
from ...基础设施.通用工具.jsonrpc协议 import (#JSON-RPC 构造与未决表
    构造jsonrpc请求,构造jsonrpc通知,构造jsonrpc成功响应,构造jsonrpc错误响应,
    分类jsonrpc消息,未决请求表,
)#构造与分类
from ...基础设施.通用工具.线程工具 import 启动守护线程#守护线程
from .异常 import ACP线路错误,请求错误#线路失败与带码请求失败

__all__=[#仅中文公开名
    '协议版本','ACP线路错误','请求错误','NDJSON流','智能体侧连接','创建NDJSON流',
]#公开面结束

协议版本=1#ACP 协议版本常量（与 SDK PROTOCOL_VERSION 对齐的本桥接钉值）

class NDJSON流:
    '可读/可写字节或文本流对，供智能体侧连接使用'
    def __init__(自身,写出流,读入流):
        '记下写出与读入'
        自身.写出=写出流#出站
        自身.读入=读入流#入站

def 创建NDJSON流(写出流,读入流):
    '测试覆盖或 stdio NDJSON'
    return NDJSON流(写出流,读入流)#包装

class 智能体侧连接:
    '打开智能体侧连接：入站方法派发到 makeAgent 返回的处理器，出站 sessionUpdate / requestPermission'
    def __init__(自身,铸造智能体,流):
        '铸造处理器并开始读帧'
        自身.流=流#传输流
        自身.写锁=threading.Lock()#写出互斥
        自身.未决表=未决请求表()#整数 id 的未决请求
        自身._出站任务={}#id → 请求期约，响应仍按请求错误拒绝
        自身.已关闭=期约()#连接关闭期约，正常关闭解决，带错关闭拒绝
        自身._关闭落定=False#是否已结算关闭期约
        自身.智能体=铸造智能体(自身)#记下连接后铸造 ACP Agent
        自身._读线程=启动守护线程(自身._读循环)#后台读

    @property
    def 已关闭承诺(自身):
        '返回连接关闭期约'
        return 自身.已关闭#期约

    def 会话更新(自身,通知):
        """发送协议更新通知。
        同步返回
        """
        自身._通知('session/update',通知)#出站通知

    def 请求许可(自身,参数):
        """session/request_permission。
        返回期约，兑现对端的结果
        """
        return 自身._请求('session/request_permission',参数)#出站请求

    def _通知(自身,方法,参数):
        '省略响应'
        自身._写出(构造jsonrpc通知(方法,参数))#通知帧

    def _请求(自身,方法,参数):
        """发出请求，返回期约：成功响应解决为 result，错误响应拒绝为请求错误，写出失败或连接关闭也拒绝
        """
        标识,响应期约=自身.未决表.新建请求()#整数 id 与等响应的期约
        自身._出站任务[标识]=响应期约#留下期约引用，响应按请求错误拒绝
        try:
            自身._写出(构造jsonrpc请求(标识,方法,参数))#请求帧
        except BaseException as 错误:
            自身._出站任务.pop(标识,None)#清 pending
            自身.未决表.撤销(标识)#撤销登记
            响应期约.拒绝(错误)#写出失败，响应不会来
        return 响应期约#交给调用方链式

    def _写出(自身,消息):
        '序列化后加换行'
        行=编码ndjson行(消息)#紧凑行
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
        '派发请求/响应/通知'
        解码器=换行帧解码器()#换行切分
        读入=自身.流.读入#入站
        按行=hasattr(读入,'readline')#按行读时末行可以没有换行
        try:
            while True:#直到 EOF
                if 按行:#按行
                    行=读入.readline()#读一行
                    if 行=='' or 行 is None:#EOF
                        break
                    for 整行 in 解码器.推入(行):#完整行
                        自身._处理行(整行)#处理
                    continue#下一行
                块=读入.read(65536)#一块
                if not 块:#EOF
                    break
                for 整行 in 解码器.推入(块):#完整行
                    自身._处理行(整行)#处理
            if 按行:#readline 的最后一行可能没有换行
                for 整行 in 解码器.结束():#末行
                    自身._处理行(整行)#处理
        except BaseException as 错误:
            if isinstance(错误,BaseException):#已是异常
                自身._关闭(错误)#带错关闭
            else:#非异常
                自身._关闭(ACP线路错误(str(错误)))#包装关闭
            return
        自身._关闭(None)#正常关闭

    def _处理行(自身,行):
        '畸形 JSON 忽略'
        try:
            消息=json.loads(行)#JSON
        except json.JSONDecodeError:
            return#忽略
        if not isinstance(消息,dict):#非对象
            return#忽略
        种类=分类jsonrpc消息(消息)#请求、通知、响应或无效
        if 种类=='响应':#入站响应
            标识=消息['id']#响应 id
            响应期约=自身._出站任务.pop(标识,None)#认领
            自身.未决表.撤销(标识)#从表摘掉
            if 响应期约 is None:#未知
                return#忽略
            if 'error' in 消息 and isinstance(消息['error'],dict):#错误响应
                错=消息['error']#错误体
                码=错['code'] if 'code' in 错 else None#错误码
                原始消息=错['message'] if 'message' in 错 else None#消息
                文案=原始消息 if isinstance(原始消息,str) and 原始消息!='' else 'ACP error'#默认消息
                数据=错['data'] if 'data' in 错 else None#可选 data
                响应期约.拒绝(请求错误(码,文案,数据))#拒绝，仍用请求错误
            else:#成功
                响应期约.解决(消息['result'] if 'result' in 消息 else None)#以 result 解决
            return#完
        if 种类=='请求' or 种类=='通知':#入站请求或通知
            标识=消息['id'] if 种类=='请求' else None#通知不回写
            方法=消息['method']#方法
            原始参数=消息['params'] if 'params' in 消息 else None#params
            参数=原始参数 if isinstance(原始参数,dict) else {}#非对象则空对象
            启动守护线程(自身._派发入站,标识,方法,参数)#异步派发

    def _派发入站(自身,标识,方法,参数):
        """有 id 则回写响应。
        控制流错误按 name 字段识别
        """
        处理映射={#ACP 方法到智能体处理器
            'initialize':'initialize',#握手
            'authenticate':'authenticate',#认证
            'session/new':'newSession',#新建会话
            'session/prompt':'prompt',#提示
            'session/cancel':'cancel',#取消
        }#映射结束
        名=处理映射[方法] if 方法 in 处理映射 else None#处理器名
        def 回写成功(结果):
            '有 id 则回写成功响应'
            if 标识 is not None:#有 id：响应
                自身._写出(构造jsonrpc成功响应(标识,结果 if 结果 is not None else {}))#成功响应
        def 回写失败(错误):
            '有 id 则回写错误响应：线路错误带码，其它是内部错误'
            错误名=getattr(错误,'name',None)#结构名
            错误码=getattr(错误,'code',None)#结构码
            if 错误名=='RequestError':#线路错误
                if 标识 is not None:#有 id
                    消息=getattr(错误,'message',str(错误))#消息
                    自身._写出(构造jsonrpc错误响应(标识,错误码,消息))#错误响应
                return#已写出
            if 标识 is not None:#其它错误
                自身._写出(构造jsonrpc错误响应(标识,-32603,str(错误)))#内部错误
        try:
            if 名 is None:#未知方法
                raise 请求错误(-32601,'method not found: '+方法)#方法未找到
            处理=getattr(自身.智能体,名,None)#取出
            if 处理 is None:#无处理器
                raise 请求错误(-32601,'method not found: '+方法)#方法未找到
            结果=处理(参数)#调用处理器
            if 名=='prompt':#提示要等回合结束，处理器返回期约
                结果.然后(回写成功,回写失败)#落定后再回写
            else:#其余处理器同步返回结果
                回写成功(结果)#立刻回写
        except BaseException as 错误:
            回写失败(错误)#同步失败回写

    def _关闭(自身,错误):
        '只落定一次'
        if 自身._关闭落定:#已关闭
            return#忽略
        自身._关闭落定=True#标记
        关闭错=错误 if 错误 is not None else ACP线路错误('ACP connection closed')#默认关闭
        自身.未决表.全部拒绝(关闭错)#拒绝未决
        自身._出站任务.clear()#清空引用
        if 错误 is not None:#带错关闭
            自身.已关闭.拒绝(错误)#拒绝关闭承诺
        else:#正常
            自身.已关闭.解决(None)#解决关闭期约
