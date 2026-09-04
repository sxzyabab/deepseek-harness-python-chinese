"""Worker 拥有的合成 Client 上下文与源代数之间的路由。"""
#对齐上游 worker/bridge/runtime-rpc.ts 段1

import uuid,threading#请求id与超时
from .....内核.智能体循环.辅助 import 操作任务#单次结果
from .会话 import 发送Client会话关闭#会话关闭
from .枢纽 import 检查器协议版本#协议版本

__all__=['Client运行时远程错误','Client运行时路由']#仅中文公开名

class Client运行时远程错误(Exception):#Client Runtime远程错误
    """Client Runtime 执行器有意返回的错误。"""
    def __init__(自身,码,信息):#构造
        """保存错误码。"""
        super().__init__(信息)#基类
        自身.code=码#错误码

class Client运行时路由:#Client Runtime路由
    """Runtime 上下文注册表与关联的 Worker→Client 请求所有者。"""
    def __init__(自身,源们,超时毫秒):#构造
        """订阅源事件。"""
        自身.源们=源们#源注册表
        自身._超时毫秒=超时毫秒#超时
        自身._按源目标={}#按源目标
        自身._待决={}#待决
        自身._控制台订阅=set()#Console订阅
        自身._监听=set()#生命周期监听
        自身._下一上下文id=-1#下一上下文id
        自身._已关闭=False#是否已关闭
        自身._取消订阅=源们.订阅事件(自身._接收源事件)#订阅

    def 目标们(自身):#列出目标
        """快照全部活动 Client 执行上下文。"""
        return list(自身._按源目标.values())#拷贝

    def 按源(自身,源):#按源查找
        """解析一个活动源代数的 Client 目标。"""
        目标=自身._按源目标.get(源['sourceId'])#取目标
        if 目标 is None:#无
            return None#无
        return 目标 if 目标['source']['generation']==源['generation'] else None#代数匹配

    def 订阅(自身,监听):#订阅
        """订阅合成执行上下文生命周期。"""
        自身._监听.add(监听)#加入
        return lambda:自身._监听.discard(监听)#释放

    def 订阅控制台(自身,目标,会话id,监听):#订阅Console
        """为一个 Client realm 与 DevTools 会话启用 Console 事件。"""
        if not 自身.源们.发送(目标['source'],{#发送启用
            'v':检查器协议版本,'t':'client-console/enable',#类型
            'sourceId':目标['source']['sourceId'],'generation':目标['source']['generation'],#代数
            'sessionId':会话id,#会话
        }):#send结束
            raise RuntimeError('Client Console source disconnected before enable')#未发送
        订阅={'target':目标,'sessionId':会话id,'listener':监听}#订阅项
        自身._控制台订阅.add(id(订阅))#登记键
        自身._控制台订阅对象=getattr(自身,'_控制台订阅对象',{})#对象表
        自身._控制台订阅对象[id(订阅)]=订阅#保存
        def 释放():#释放
            """禁用 Console。"""
            表=getattr(自身,'_控制台订阅对象',{})#表
            if id(订阅) not in 表:#已无
                return#返回
            del 表[id(订阅)]#移除
            自身._控制台订阅.discard(id(订阅))#键
            try:#发送禁用
                自身.源们.发送(目标['source'],{#禁用帧
                    'v':检查器协议版本,'t':'client-console/disable',#类型
                    'sourceId':目标['source']['sourceId'],'generation':目标['source']['generation'],#代数
                    'sessionId':会话id,#会话
                })#send结束
            except Exception:#源已失效
                pass#源移除也会在 Client 侧禁用 Console 观察
        return 释放#释放器

    def 请求(自身,目标,会话id,命令):#发起请求
        """在其当前活动源代数中执行一次类型化命令。"""
        if 自身._已关闭 or 自身._按源目标.get(目标['source']['sourceId']) is not 目标:#不可用
            任务=操作任务()#失败任务
            任务.拒绝(RuntimeError('Client execution context is no longer available'))#拒绝
            return 任务#返回
        请求id=str(uuid.uuid4())#请求id
        任务=操作任务()#待决任务
        def 超时():#超时
            """超时取消并拒绝。"""
            if 请求id not in 自身._待决:#已结算
                return#返回
            自身._取消Client响应(目标['source'],会话id,请求id)#取消Client侧
            自身._拒绝待决(请求id,TimeoutError(f"Client Runtime {命令['op']} timed out after {自身._超时毫秒}ms"))#拒绝
        定时=threading.Timer(自身._超时毫秒/1000,超时)#超时
        定时.daemon=True#守护
        定时.start()#启动
        自身._待决[请求id]={'target':目标,'sessionId':会话id,'op':命令['op'],'future':任务,'timer':定时}#登记
        try:#投递
            已发=自身.源们.发送(目标['source'],{#请求帧
                'v':检查器协议版本,'t':'client-runtime/request',#类型
                'sourceId':目标['source']['sourceId'],'generation':目标['source']['generation'],#代数
                'sessionId':会话id,'requestId':请求id,'command':命令,#命令
            })#send结束
            if not 已发:#未发
                自身._拒绝待决(请求id,RuntimeError('Client execution context disconnected before dispatch'))#拒绝
        except Exception as 错误:#投递失败
            自身._拒绝待决(请求id,错误 if isinstance(错误,Exception) else RuntimeError(str(错误)))#拒绝
        return 任务#结果

    def 关闭目标会话(自身,目标,会话id):#关闭目标会话
        """关闭一个 realm 本地 Runtime 会话，不通知兄弟 Client realm。"""
        for 请求id,待决 in list(自身._待决.items()):#扫待决
            if 待决['target'] is not 目标 or 待决['sessionId']!=会话id:#不匹配
                continue#跳过
            自身._拒绝待决(请求id,RuntimeError('DevTools Runtime session closed'))#拒绝
        表=getattr(自身,'_控制台订阅对象',{})#Console表
        for 键 in list(表.keys()):#扫Console
            订阅=表[键]#取
            if 订阅['target'] is 目标 and 订阅['sessionId']==会话id:#匹配
                del 表[键]#移除
                自身._控制台订阅.discard(键)#键
        发送Client会话关闭(自身.源们,目标['source'],{#通知关闭
            'v':检查器协议版本,'t':'client-runtime/session-closed',#类型
            'sourceId':目标['source']['sourceId'],'generation':目标['source']['generation'],#代数
            'sessionId':会话id,#会话
        })#通知结束

    def 关闭(自身):#关闭
        """停止路由并拒绝每一笔未完成操作。"""
        if 自身._已关闭:#幂等
            return#返回
        自身._已关闭=True#置位
        自身._取消订阅()#取消订阅
        for 请求id in list(自身._待决.keys()):#拒绝全部
            自身._拒绝待决(请求id,RuntimeError('Client Runtime router closed'))#拒绝
        自身._按源目标.clear()#清目标
        getattr(自身,'_控制台订阅对象',{}).clear()#清Console
        自身._控制台订阅.clear()#清键
        自身._监听.clear()#清监听

    def _接收源事件(自身,事件):#处理源事件
        """按类型分发。"""
        类型=事件['type']#类型
        if 类型=='opened':#打开
            自身._打开(事件['source'])#打开目标
        elif 类型=='closed':#关闭
            自身._移除(事件['source'],事件['reason'])#移除
        elif 类型=='client-runtime-response':#Runtime响应
            自身._结算(事件['source'],事件['frame'])#结算
        elif 类型=='client-console-event':#Console事件
            自身._控制台事件(事件['source'],事件['frame'])#分发

    def _打开(自身,源):#打开目标
        """登记 Client Runtime 能力目标。"""
        能力=None#能力
        for 候 in 源['capabilities']:#找能力
            if 候['type']=='client-runtime':#命中
                能力=候#保存
                break#停止
        if 能力 is None:#无Runtime能力
            return#返回
        目标={#目标
            'contextId':自身._下一上下文id,#递减id
            'uniqueContextId':f"dsh-client:{源['sourceId']}:{源['generation']}",#唯一id
            'source':源,'capability':能力,#能力
        }#target结束
        自身._下一上下文id-=1#递减
        自身._按源目标[源['sourceId']]=目标#登记
        自身._发出({'type':'opened','target':目标})#发出

    def _移除(自身,源,原因):#移除目标
        """拒绝待决并发出关闭。"""
        目标=自身._按源目标.get(源['sourceId'])#取目标
        if 目标 is None or 目标['source']['generation']!=源['generation']:#代数不符
            return#返回
        del 自身._按源目标[源['sourceId']]#删除
        for 请求id,待决 in list(自身._待决.items()):#扫待决
            if 待决['target'] is not 目标:#非本目标
                continue#跳过
            自身._拒绝待决(请求id,RuntimeError(f'Client execution context closed: {原因}'))#拒绝
        表=getattr(自身,'_控制台订阅对象',{})#Console
        for 键 in list(表.keys()):#扫
            if 表[键]['target'] is 目标:#匹配
                del 表[键]#移除
                自身._控制台订阅.discard(键)#键
        自身._发出({'type':'closed','target':目标})#发出

    def _控制台事件(自身,源,帧):#Console事件
        """分发到匹配订阅。"""
        目标=自身._按源目标.get(源['sourceId'])#取目标
        if 目标 is None or 目标['source']['generation']!=源['generation']:#不符
            return#返回
        表=getattr(自身,'_控制台订阅对象',{})#表
        for 订阅 in list(表.values()):#扫订阅
            if 订阅['target'] is not 目标 or 订阅['sessionId']!=帧['sessionId']:#不匹配
                continue#跳过
            try:#隔离回调
                订阅['listener'](帧['event'])#通知
            except Exception:#会话故障
                pass#一个 DevTools Console 会话不能扰乱兄弟会话

    def _结算(自身,源,帧):#结算响应
        """确认并兑现或拒绝。"""
        待决=自身._待决.get(帧['requestId'])#取待决
        if 待决 is None:#无待决
            自身._取消Client响应(源,帧['sessionId'],帧['requestId'])#取消残余
            return#返回
        if 待决['target']['source']['sourceId']!=源['sourceId'] or 待决['target']['source']['generation']!=源['generation'] or 待决['sessionId']!=帧['sessionId']:#关联失败
            自身._取消Client响应(源,帧['sessionId'],帧['requestId'])#取消帧侧
            自身._取消Client响应(待决['target']['source'],待决['sessionId'],帧['requestId'])#取消待决侧
            自身._拒绝待决(帧['requestId'],RuntimeError('Client Runtime response correlation mismatch'))#关联失败
            return#返回
        结果=帧['outcome']#结果
        if not 结果.get('ok'):#失败结果
            自身._确认Client响应(源,帧['sessionId'],帧['requestId'])#确认
            错=结果['error']#错误
            自身._拒绝待决(帧['requestId'],Client运行时远程错误(错['code'],错['message']))#拒绝
            return#返回
        if 结果['result']['op']!=待决['op']:#操作不符
            自身._取消Client响应(源,帧['sessionId'],帧['requestId'])#取消
            自身._拒绝待决(帧['requestId'],RuntimeError(f"Client Runtime response op {结果['result']['op']} does not match {待决['op']}"))#拒绝
            return#返回
        if not 自身._确认Client响应(源,帧['sessionId'],帧['requestId']):#确认失败
            自身._拒绝待决(帧['requestId'],RuntimeError('Client execution context disconnected before acknowledgement'))#拒绝
            return#返回
        待决['timer'].cancel()#清超时
        del 自身._待决[帧['requestId']]#移除
        待决['future'].兑现(结果['result'])#成功

    def _确认Client响应(自身,源,会话id,请求id):#确认Client响应
        """发送确认帧。"""
        try:#发送确认
            return 自身.源们.发送(源,{#确认帧
                'v':检查器协议版本,'t':'client-runtime/response-acknowledged',#类型
                'sourceId':源['sourceId'],'generation':源['generation'],#代数
                'sessionId':会话id,'requestId':请求id,#请求
            })#send结束
        except Exception:#发送失败
            return False#失败

    def _取消Client响应(自身,源,会话id,请求id):#取消Client响应
        """发送取消帧。"""
        try:#发送取消
            自身.源们.发送(源,{#取消帧
                'v':检查器协议版本,'t':'client-runtime/cancel',#类型
                'sourceId':源['sourceId'],'generation':源['generation'],#代数
                'sessionId':会话id,'requestId':请求id,#请求
            })#send结束
        except Exception:#投递失败
            pass#取消结算不依赖对可能正在关闭的源的投递

    def _拒绝待决(自身,请求id,错误):#拒绝待决
        """清理并拒绝。"""
        待决=自身._待决.pop(请求id,None)#取待决
        if 待决 is None:#无
            return#返回
        待决['timer'].cancel()#清超时
        if not 待决['future']._future.done():#未结算
            待决['future'].拒绝(错误)#拒绝

    def _发出(自身,事件):#发出事件
        """隔离投递生命周期。"""
        for 监听 in list(自身._监听):#扫监听
            try:#隔离
                监听(事件)#回调
            except Exception:#故障
                pass#一个 CDP 会话不能扰乱对另一会话的上下文投递
