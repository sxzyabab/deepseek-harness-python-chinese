"""共享的 Host/Client 相关非 CDP 查询请求所有者。

对齐上游 `shared/bridge/rpc.ts`。公开面仅中文名。
"""
import threading#超时定时器
from concurrent.futures import Future as 期约#待决结果
from .标识 import 检查器id#品牌化
from ..json import json字节长度#帧字节
from .版本 import 检查器协议版本#协议版本
from .消息.查询.编解码 import 是否检查器查询响应信封,解析检查器查询响应帧#响应编解码

__all__=[#仅中文公开名
    '检查器查询发送器','检查器查询连接选项','检查器查询远程错误','检查器查询连接',
]#公开面结束

class 检查器查询发送器:#查询发送器
    """共用查询所有者所使用的活动载体写入。"""
    def 发送(自身,帧):#发送请求帧
        """发送一帧已校验的查询请求。"""
        raise NotImplementedError#子类实现

class 检查器查询连接选项:#查询连接选项
    """一个 Host 或 Client 查询连接所应用的边界。"""
    def __init__(自身,timeoutMs,maxFrameBytes):#构造
        """保存超时与帧上限。"""
        自身.timeoutMs=timeoutMs#超时毫秒
        自身.maxFrameBytes=maxFrameBytes#最大帧字节

class 检查器查询远程错误(Exception):#远程查询错误
    """Worker 查询处理器故意返回的失败。"""
    def __init__(自身,code,message):#错误码与信息
        """保存错误码与信息。"""
        super().__init__(message)#设置消息
        自身.code=code#错误码

class 检查器查询连接:#查询连接
    """为一个可重连的 Host 或 Client 源关联请求。"""
    def __init__(自身,选项):#连接选项
        """初始化待决表与世代。"""
        自身.选项=选项#连接选项
        自身._待决={}#待决表
        自身._活动=None#当前世代
        自身._下一请求号=0#下一请求号
        自身._已关闭=False#是否已永久关闭

    def 连接(自身,sourceId,generation,sender):#连接世代
        """接纳 Worker 已确认的源世代。"""
        if 自身._已关闭:#已关闭
            raise Exception('inspector query connection is closed')#英文诊断
        自身.断开('Inspector source generation replaced')#断开旧世代
        自身._活动={'sourceId':sourceId,'generation':generation,'sender':sender}#安装新世代

    def 请求(自身,查询):#执行查询
        """对当前已接受的源世代执行一次查询。"""
        活动=自身._活动#当前世代
        if 自身._已关闭 or 活动 is None:#未连接
            失败=期约()#失败期约
            失败.set_exception(Exception('Inspector query transport is not connected'))#拒绝
            return 失败#返回
        自身._下一请求号+=1#分配请求号
        请求id=检查器id(f'query-{自身._下一请求号}','requestId')#分配请求id
        帧={#请求帧
            'v':检查器协议版本,#协议版本
            't':'query/request',#帧类型
            'sourceId':活动['sourceId'],#源标识
            'generation':活动['generation'],#世代
            'requestId':请求id,#请求标识
            'query':查询,#查询体
        }#帧结束
        if json字节长度(帧)>自身.选项.maxFrameBytes:#超帧
            失败=期约()#失败期约
            失败.set_exception(Exception(f'Inspector query request exceeds {自身.选项.maxFrameBytes} bytes'))#拒绝
            return 失败#返回
        结果=期约()#待决期约
        def 超时():#超时
            """超时拒绝。"""
            if 自身._待决.pop(请求id,None) is not None:#仍待决
                结果.set_exception(Exception(f'Inspector query {查询["op"]} timed out after {自身.选项.timeoutMs}ms'))#超时拒绝
        定时器=threading.Timer(自身.选项.timeoutMs/1000,超时)#定时器
        定时器.daemon=True#守护
        自身._待决[请求id]={'op':查询['op'],'resolve':结果,'timer':定时器}#登记待决
        定时器.start()#启动定时器
        try:#发送
            活动['sender'].发送(帧) if hasattr(活动['sender'],'发送') else 活动['sender'].send(帧)#写载体
        except Exception as 错误:#发送失败
            自身._拒绝待决(请求id,渲染错误(错误))#拒绝待决
        return 结果#返回期约

    def 接收(自身,值):#消费响应
        """当解码后的载体值是查询响应时加以消费。"""
        if not 是否检查器查询响应信封(值):#非查询响应
            return False#未消费
        try:#解码
            帧=解析检查器查询响应帧(值)#解析帧
            if json字节长度(帧)>自身.选项.maxFrameBytes:#超帧
                raise Exception(f'inspector protocol: query response exceeds {自身.选项.maxFrameBytes} bytes')#英文诊断
        except Exception as 错误:#解码失败
            自身.断开(f'Invalid Inspector query response: {渲染错误(错误)}')#断开
            raise#原样抛出
        待决=自身._待决.get(帧['requestId'])#查待决
        if 待决 is None:#无待决
            return True#吞掉
        活动=自身._活动#当前世代
        if 活动 is None or 帧['sourceId']!=活动['sourceId'] or 帧['generation']!=活动['generation']:#世代不匹配
            自身._拒绝待决(帧['requestId'],Exception('Inspector query response source generation does not match'))#拒绝
            return True#已消费
        结果封装=帧['outcome']#结果封装
        if not 结果封装['ok']:#失败结果
            错误=结果封装['error']#错误
            自身._拒绝待决(帧['requestId'],检查器查询远程错误(错误['code'],错误['message']))#远程错误
            return True#已消费
        if 结果封装['result']['op']!=待决['op']:#操作不匹配
            自身._拒绝待决(帧['requestId'],Exception(f'Inspector query response op {结果封装["result"]["op"]} does not match {待决["op"]}'))#拒绝
            return True#已消费
        待决['timer'].cancel()#清超时
        del 自身._待决[帧['requestId']]#移除待决
        待决['resolve'].set_result(结果封装['result'])#兑现结果
        return True#已消费

    def 断开(自身,reason):#断开世代
        """拒绝活动请求，同时允许稍后的源世代。"""
        自身._活动=None#清世代
        for 请求id in list(自身._待决.keys()):#拒绝全部
            自身._拒绝待决(请求id,Exception(reason))#拒绝

    def 关闭(自身,reason='Inspector query connection closed'):#永久关闭
        """永久拒绝请求并阻止稍后重连。"""
        if 自身._已关闭:#幂等
            return#返回
        自身._已关闭=True#标记关闭
        自身.断开(reason)#断开

    def _拒绝待决(自身,requestId,error):#拒绝待决
        """拒绝一条待决请求。"""
        待决=自身._待决.pop(requestId,None)#取待决
        if 待决 is None:#无则返回
            return#返回
        待决['timer'].cancel()#清定时器
        待决['resolve'].set_exception(error)#拒绝

def 渲染错误(错误):#规范化错误
    """包装为 Exception。"""
    return 错误 if isinstance(错误,Exception) else Exception(str(错误))#包装为Error
