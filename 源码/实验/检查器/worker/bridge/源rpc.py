"""Worker 拥有的 Client 只读源目录请求路由。"""
#对齐上游 worker/bridge/source-rpc.ts

import uuid,threading#请求id与超时
from .....内核.智能体循环.辅助 import 操作任务#单次结果
from .会话 import 发送Client会话关闭#会话关闭
from .枢纽 import 检查器协议版本#协议版本

__all__=['Client源远程错误','Client源路由']#仅中文公开名

class Client源远程错误(Exception):#Client源远程错误
    """Client 源目录有意返回的错误。"""
    def __init__(自身,码,信息):#构造
        """保存错误码。"""
        super().__init__(信息)#基类
        自身.code=码#错误码

class Client源路由:#Client源路由
    """将有界源请求与一个活动 Client 源代数关联。"""
    def __init__(自身,源们,超时毫秒,最大内容字节,最大帧字节):#构造
        """计算分块并订阅源事件。"""
        自身.源们=源们#源注册表
        自身._超时毫秒=超时毫秒#超时
        自身.最大内容字节=最大内容字节#内容字节上限
        自身.分块字节=max(1,int((最大帧字节-4096)*3/4))#分块大小
        自身._待决={}#待决表
        自身._已关闭=False#是否已关闭
        自身._取消订阅=源们.订阅事件(自身._接收源事件)#订阅源事件

    def 请求(自身,源,会话id,命令):#发起请求
        """对活动 Client 源代数执行一次操作。"""
        if 自身._已关闭:#已关闭
            任务=操作任务()#失败任务
            任务.拒绝(RuntimeError('Client source router is closed'))#拒绝
            return 任务#返回
        请求id=str(uuid.uuid4())#请求id
        任务=操作任务()#新建任务
        def 超时():#超时
            """超时拒绝。"""
            if 请求id in 自身._待决:#仍待决
                del 自身._待决[请求id]#移除
                任务.拒绝(TimeoutError(f"Client source {命令['op']} timed out after {自身._超时毫秒}ms"))#拒绝
        定时=threading.Timer(自身._超时毫秒/1000,超时)#超时
        定时.daemon=True#守护
        定时.start()#启动
        自身._待决[请求id]={'source':源,'sessionId':会话id,'command':命令,'future':任务,'timer':定时}#登记
        try:#投递
            已发=自身.源们.发送(源,{#发送请求帧
                'v':检查器协议版本,'t':'client-sources/request',#类型
                'sourceId':源['sourceId'],'generation':源['generation'],#代数
                'sessionId':会话id,'requestId':请求id,'command':命令,#命令
            })#send结束
            if not 已发:#未发送
                自身._拒绝待决(请求id,RuntimeError('Client source disconnected before dispatch'))#拒绝
        except Exception as 错误:#投递失败
            自身._拒绝待决(请求id,错误 if isinstance(错误,Exception) else RuntimeError(str(错误)))#拒绝
        return 任务#结果任务

    def 关闭会话(自身,源,会话id):#关闭会话
        """拒绝待决操作并通知一个 Client 源会话已关闭。"""
        for 请求id,待决 in list(自身._待决.items()):#扫待决
            if 待决['source']['sourceId']!=源['sourceId'] or 待决['source']['generation']!=源['generation'] or 待决['sessionId']!=会话id:#不符
                continue#跳过
            自身._拒绝待决(请求id,RuntimeError('DevTools source session closed'))#拒绝
        发送Client会话关闭(自身.源们,源,{#通知关闭
            'v':检查器协议版本,'t':'client-sources/session-closed',#类型
            'sourceId':源['sourceId'],'generation':源['generation'],'sessionId':会话id,#会话
        })#通知结束

    def 关闭(自身):#关闭路由
        """停止路由并拒绝每一笔未完成的源操作。"""
        if 自身._已关闭:#幂等
            return#返回
        自身._已关闭=True#置位
        自身._取消订阅()#取消订阅
        for 请求id in list(自身._待决.keys()):#拒绝全部
            自身._拒绝待决(请求id,RuntimeError('Client source router closed'))#拒绝

    def _接收源事件(自身,事件):#处理源事件
        """结算或拒绝。"""
        if 事件['type']=='closed':#源关闭
            for 请求id,待决 in list(自身._待决.items()):#扫待决
                if 待决['source']['sourceId']==事件['source']['sourceId'] and 待决['source']['generation']==事件['source']['generation']:#同代数
                    自身._拒绝待决(请求id,RuntimeError(f"Client source closed: {事件['reason']}"))#拒绝
            return#返回
        if 事件['type']=='client-source-response':#源响应
            自身._结算(事件['source'],事件['frame'])#结算

    def _结算(自身,源,帧):#结算响应
        """匹配命令并兑现 Future。"""
        待决=自身._待决.get(帧['requestId'])#取待决
        if 待决 is None:#无待决
            return#返回
        if 待决['source']['sourceId']!=源['sourceId'] or 待决['source']['generation']!=源['generation'] or 待决['sessionId']!=帧['sessionId']:#关联失败
            自身._拒绝待决(帧['requestId'],RuntimeError('Client source response correlation mismatch'))#拒绝
            return#返回
        结果=帧['outcome']#结果
        if not 结果.get('ok'):#失败结果
            错=结果['error']#错误
            自身._拒绝待决(帧['requestId'],Client源远程错误(错['code'],错['message']))#拒绝
            return#返回
        if not _匹配命令(待决['command'],结果['result']):#命令不匹配
            自身._拒绝待决(帧['requestId'],RuntimeError('Client source response does not match its request'))#拒绝
            return#返回
        待决['timer'].cancel()#清超时
        del 自身._待决[帧['requestId']]#移除
        待决['future'].兑现(结果['result'])#成功

    def _拒绝待决(自身,请求id,错误):#拒绝待决
        """清理并拒绝。"""
        待决=自身._待决.pop(请求id,None)#取待决
        if 待决 is None:#无
            return#返回
        待决['timer'].cancel()#清超时
        if not 待决['future']._future.done():#未结算
            待决['future'].拒绝(错误)#拒绝

def _匹配命令(命令,结果):#命令与结果匹配
    """校验响应与请求对应。"""
    if 命令['op']!=结果['op']:#操作不符
        return False#不符
    if 命令['op']=='list-scripts' or 结果['op']=='list-scripts':#列表即匹配
        return True#匹配
    return 结果.get('scriptKey')==命令.get('scriptKey') and 结果.get('content')==命令.get('content') and (not 结果.get('available') or 结果.get('offset')==命令.get('offset'))#脚本键
