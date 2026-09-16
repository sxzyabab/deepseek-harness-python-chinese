from threading import Timer as 定时器#超时定时器
from .标识 import 检查器id#标识构造
from ..json import 操作任务,json字节长度,检查器错误#单次结果|帧字节|本包错误
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
            raise 检查器错误('inspector query connection is closed')#英文诊断
        自身.断开('Inspector source generation replaced')#断开旧世代
        自身._活动={'sourceId':sourceId,'generation':generation,'sender':sender}#安装新世代

    def 请求(自身,查询):#执行查询
        """对当前已接受的源世代执行一次查询。"""
        活动=自身._活动#当前世代
        if 自身._已关闭 or 活动 is None:#未连接
            失败=操作任务()#失败任务
            失败.拒绝(Exception('Inspector query transport is not connected'))#拒绝
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
            失败=操作任务()#失败任务
            失败.拒绝(Exception(f'Inspector query request exceeds {自身.选项.maxFrameBytes} bytes'))#拒绝
            return 失败#返回
        任务=操作任务()#待决任务
        def 超时():#超时
            """超时拒绝。"""
            if 自身._待决.pop(请求id,None) is not None:#仍待决
                任务.拒绝(Exception(f'Inspector query {查询["op"]} timed out after {自身.选项.timeoutMs}ms'))#超时拒绝
        计时=定时器(自身.选项.timeoutMs/1000,超时)#定时器
        计时.daemon=True#守护
        自身._待决[请求id]={'op':查询['op'],'任务':任务,'timer':计时}#登记待决
        计时.start()#启动定时器
        try:#发送
            活动['sender'].发送(帧) if hasattr(活动['sender'],'发送') else 活动['sender'].send(帧)#写载体
        except Exception as 错误:#rpc 发送可能抛 OSError/连接断开，契约未定所以收不窄
            自身._拒绝待决(请求id,渲染错误(错误))#拒绝待决
        return 任务#返回任务

    def 接收(自身,值):#消费响应
        """当解码后的载体值是查询响应时加以消费。"""
        if not 是否检查器查询响应信封(值):#非查询响应
            return False#未消费
        try:#解码
            帧=解析检查器查询响应帧(值)#解析帧
            if json字节长度(帧)>自身.选项.maxFrameBytes:#超帧
                raise 检查器错误(f'inspector protocol: query response exceeds {自身.选项.maxFrameBytes} bytes')#英文诊断
        except Exception as 错误:#解析检查器查询响应帧可能抛检查器错误/TypeError，契约未定所以收不窄
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
        待决['任务'].兑现(结果封装['result'])#兑现结果
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
        待决['任务'].拒绝(error)#拒绝

def 渲染错误(错误):#规范化错误
    """包装为 Exception。"""
    return 错误 if isinstance(错误,Exception) else Exception(str(错误))#包装为Error
