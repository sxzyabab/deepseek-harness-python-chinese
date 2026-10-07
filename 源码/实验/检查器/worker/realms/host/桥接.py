import threading#串行投递
from ......基础设施.js特性 import PromiseEX as 期约扩展#请求结果期约与投递链
from ....异常 import 检查器错误#包内错误

__all__=['Host检查器会话','Host通知通道']#仅中文公开名

class Host检查器会话:#Host inspector会话
    'Host V8 inspector 请求与通知的连接本地载体'
    def __init__(自身,上下文名):#构造
        '创建会话并监听通知'
        自身.上下文名=上下文名#上下文名
        自身._监听=set()#监听
        自身._已连接=False#是否已连接
        自身._失败=None#连接失败信息
        自身._会话=None#原生会话占位（Python 侧由宿主写入）

    def 订阅(自身,监听):#订阅
        '订阅原生 inspector 通知'
        自身._监听.add(监听)#加入
        def 拆除():#取消订阅
            '从监听集摘掉'
            自身._监听.discard(监听)#拆除
        return 拆除#拆除器

    def 请求(自身,方法,参数):#请求
        '为 Worker 拥有的复合 Runtime 操作执行一次 Host V8 请求，返回期约，兑现值是原生结果'
        结果期约=期约扩展()#本次请求的期约
        失败=自身._连接()#确保连接
        if 失败 is not None:#连接失败
            结果期约.拒绝(检查器错误(失败))#连接失败
            return 结果期约#返回已拒绝的期约
        if 自身._会话 is None:#无会话实现
            结果期约.拒绝(检查器错误('Host V8 inspector session is not bound'))#未绑定
            return 结果期约#返回已拒绝的期约
        try:#投递
            结果期约.解决(自身._会话.post(方法,参数))#原生会话同步返回结果
        except Exception as 错误:#post 可能抛连接/协议错误，契约未定所以收不窄
            结果期约.拒绝(检查器错误(str(错误)))#以渲染后的消息拒绝
        return 结果期约#返回期约

    def 关闭(自身):#关闭
        '断开此 DevTools 客户端的 V8 会话'
        自身._监听.clear()#清监听
        if not 自身._已连接 or 自身._失败 is not None:#未连或已失败
            return#返回
        自身._已连接=False#置未连
        try:#断开
            if 自身._会话 is not None:#有会话
                自身._会话.disconnect()#断开
        except Exception:#会话.disconnect 底层已断时可能抛 OSError/RuntimeError，契约未定所以收不窄
            pass#底层 inspector 会话已断开

    def _连接(自身):#连接
        '连接主线程 inspector'
        if 自身._已连接:#已连
            return 自身._失败#返回失败或None
        自身._已连接=True#置位
        try:#连主线程
            if 自身._会话 is not None:#有会话
                自身._会话.connectToMainThread()#连接
        except Exception as 错误:#connectToMainThread 可能抛连接/协议错误，契约未定所以收不窄
            自身._失败=f'Host V8 inspector is unavailable: {错误}'#记录
        return 自身._失败#返回失败或None

    def _改写上下文名(自身,消息):#改写上下文名
        '默认上下文改名'
        if 消息.get('method')!='Runtime.executionContextCreated':#非创建
            return 消息#原样
        参数=消息['params'] if 'params' in 消息 else None#参数
        if not isinstance(参数,dict):#无效
            return 消息#原样
        上下文=参数['context'] if 'context' in 参数 else None#上下文
        if not isinstance(上下文,dict):#无效
            return 消息#原样
        辅助=上下文['auxData'] if 'auxData' in 上下文 else None#辅助数据
        if not isinstance(辅助,dict) or 辅助.get('isDefault') is not True:#非默认
            return 消息#原样
        return {'method':消息['method'],'params':{**参数,'context':{**上下文,'name':自身.上下文名}}}#改写

    def _投递通知(自身,消息):#投递通知
        '改写后隔离投递'
        改写=自身._改写上下文名(消息)#改写上下文名
        for 监听 in list(自身._监听):#扫监听
            try:#隔离
                监听(改写)#回调
            except Exception:#桥接观察者回调什么都可能抛，收不窄
                pass#一个域订阅者不能饿死兄弟域的通知

class Host通知通道:#Host通知通道
    '串行化已接受的原生通知并隔离兄弟消费者'
    def __init__(自身,目标,接受,投影):#构造
        '订阅并串行投递'
        自身._接受=接受#是否接受
        自身._投影=投影#投影
        自身._监听=set()#监听
        自身._取消订阅=目标.订阅(自身._接收)#订阅
        自身._投递锁=threading.Lock()#保护投递链的衔接
        自身._投递链=期约扩展()#按接收顺序串行投递的期约链
        自身._投递链.解决()#链头已解决，第一条通知可立即投递

    def 订阅(自身,监听):#订阅
        '订阅投影后的原生通知'
        自身._监听.add(监听)#加入
        def 拆除():#取消订阅
            '从监听集摘掉'
            自身._监听.discard(监听)#拆除
        return 拆除#拆除器

    def 关闭(自身):#关闭
        '拆除原生通知订阅与全部消费者'
        自身._取消订阅()#取消
        自身._监听.clear()#清空

    def _接收(自身,消息):#接收
        '把本条通知接到投递链末尾，按接收顺序串行投影投递'
        if not 自身._接受(消息):#不接受
            return#返回
        def 投影并投递(上一条结果):#上一条通知投递完后执行
            '投影本条通知，投影完成后逐个通知消费者'
            def 投递(事件):#投影完成后调用
                '事件非空则逐个通知消费者'
                if 事件 is None:#无事件
                    return#返回
                for 监听 in list(自身._监听):#扫监听
                    try:#隔离
                        监听(事件)#回调
                    except Exception:#桥接观察者回调什么都可能抛，收不窄
                        pass#一个通知消费者不能阻止对其兄弟的投递
            return 自身._投影(消息).然后(投递)#投影期约兑现后再投递
        def 忽略畸形通知(错误):#投影或投递失败后调用
            '畸形的可选原生通知不中断后续通知的投递'
            return None#返回后投递链恢复为已解决
        with 自身._投递锁:#多个原生通知线程衔接链尾时互斥
            自身._投递链=自身._投递链.然后(投影并投递).捕获(忽略畸形通知)#接到链尾
