"""每个 DevTools 连接通向 Host 主线程真实 V8 inspector 目标的桥。"""
#对齐上游 worker/realms/host/bridge.ts

import threading#串行投递
from ......内核.智能体循环.辅助 import 解开#可等待则等待

__all__=['Host检查器会话','Host通知通道']#仅中文公开名

def _渲染错误(错误):#渲染错误
    """错误信息。"""
    return str(错误)#信息

class Host检查器会话:#Host inspector会话
    """Host V8 inspector 请求与通知的连接本地载体。"""
    def __init__(自身,上下文名):#构造
        """创建会话并监听通知。"""
        自身.上下文名=上下文名#上下文名
        自身._监听=set()#监听
        自身._已连接=False#是否已连接
        自身._失败=None#连接失败信息
        自身._会话=None#原生会话占位（Python 侧由宿主注入）

    def 订阅(自身,监听):#订阅
        """订阅原生 inspector 通知。"""
        自身._监听.add(监听)#加入
        return lambda:自身._监听.discard(监听)#释放

    def 请求(自身,方法,参数):#请求
        """为 Worker 拥有的复合 Runtime 操作执行一次 Host V8 请求。"""
        失败=自身._连接()#确保连接
        if 失败 is not None:#连接失败
            raise RuntimeError(失败)#拒绝
        if 自身._会话 is None:#无会话实现
            raise RuntimeError('Host V8 inspector session is not bound')#未绑定
        return 解开(自身._会话.post(方法,参数))#投递

    def 关闭(自身):#关闭
        """断开此 DevTools 客户端的 V8 会话。"""
        自身._监听.clear()#清监听
        if not 自身._已连接 or 自身._失败 is not None:#未连或已失败
            return#返回
        自身._已连接=False#置未连
        try:#断开
            if 自身._会话 is not None:#有会话
                自身._会话.disconnect()#断开
        except Exception:#已断
            pass#底层 inspector 会话已断开

    def _连接(自身):#连接
        """连接主线程 inspector。"""
        if 自身._已连接:#已连
            return 自身._失败#返回失败或None
        自身._已连接=True#置位
        try:#连主线程
            if 自身._会话 is not None:#有会话
                自身._会话.connectToMainThread()#连接
        except Exception as 错误:#失败
            自身._失败=f'Host V8 inspector is unavailable: {_渲染错误(错误)}'#记录
        return 自身._失败#返回失败或None

    def _改写上下文名(自身,消息):#改写上下文名
        """默认上下文改名。"""
        if 消息.get('method')!='Runtime.executionContextCreated':#非创建
            return 消息#原样
        参数=消息.get('params') or {}#参数
        上下文=参数.get('context')#上下文
        if not isinstance(上下文,dict):#无效
            return 消息#原样
        辅助=上下文.get('auxData')#辅助数据
        if not isinstance(辅助,dict) or 辅助.get('isDefault') is not True:#非默认
            return 消息#原样
        return {'method':消息['method'],'params':{**参数,'context':{**上下文,'name':自身.上下文名}}}#改写

    def _投递通知(自身,消息):#投递通知
        """改写后隔离投递。"""
        改写=自身._改写上下文名(消息)#改写上下文名
        for 监听 in list(自身._监听):#扫监听
            try:#隔离
                监听(改写)#回调
            except Exception:#故障
                pass#一个域订阅者不能饿死兄弟域的通知

class Host通知通道:#Host通知通道
    """串行化已接受的原生通知并隔离兄弟消费者。"""
    def __init__(自身,目标,接受,投影):#构造
        """订阅并串行投递。"""
        自身._接受=接受#是否接受
        自身._投影=投影#投影
        自身._监听=set()#监听
        自身._取消订阅=目标.订阅(自身._接收)#订阅
        自身._投递锁=threading.Lock()#串行锁

    def 订阅(自身,监听):#订阅
        """订阅投影后的原生通知。"""
        自身._监听.add(监听)#加入
        return lambda:自身._监听.discard(监听)#释放

    def 关闭(自身):#关闭
        """释放原生通知订阅与全部消费者。"""
        自身._取消订阅()#取消
        自身._监听.clear()#清空

    def _接收(自身,消息):#接收
        """串行投影投递。"""
        if not 自身._接受(消息):#不接受
            return#返回
        with 自身._投递锁:#串行
            try:#投影
                事件=解开(自身._投影(消息))#投影
                if 事件 is None:#无事件
                    return#返回
                for 监听 in list(自身._监听):#扫监听
                    try:#隔离
                        监听(事件)#回调
                    except Exception:#故障
                        pass#一个通知消费者不能阻止对其兄弟的投递
            except Exception:#投影失败
                pass#畸形的可选原生通知不中断请求处理
