"""按认证 URL 键控的宿主记录一次性读取缓存。"""
import threading#寿命与代际中止
from concurrent.futures import Future as _原生Future,wait as _等待全部#在飞
from ...客户端.存储 import 创建快照存储#快照

__all__=['宿主读存储']#仅中文公开名

class 宿主读存储:#一种记录的读取
    """连接替换时清空；拆除时取消在飞。"""
    def __init__(自身,策略,拉取=None):
        """策略含 loading/failed/retryable/decode；可选注入拉取。"""
        自身._策略=策略#策略
        自身.状态=创建快照存储({})#url→态
        自身._寿命=threading.Event()#寿命中止
        自身._代际=threading.Event()#代际中止
        自身._在飞=set()#在飞 Future
        自身._拉取=拉取#可选拉取

    def 加载网址(自身,网址):#读一 URL
        """已有不可重试态则保持。"""
        快照=自身.状态.getSnapshot()#当前
        当前=快照[网址] if 网址 in 快照 else None#态
        if 自身._寿命.is_set():#已拆除
            return#空
        if 当前 is not None and not 自身._策略['retryable'](当前):#保持
            return#空
        def 写加载(态):#进入加载
            """loading。"""
            态[网址]=自身._策略['loading']#加载
        自身.状态.update(写加载)#发布
        未来=_原生Future()#在飞
        自身._在飞.add(未来)#记下
        try:#读
            自身._读(网址)#同步
            未来.set_result(None)#成功
        except BaseException as 错误:#失败
            未来.set_exception(错误)#拒绝
            raise#上抛
        finally:#结算
            自身._在飞.discard(未来)#移出

    def 重置(自身):#连接替换
        """作废全部态与在飞。"""
        自身._代际.set()#中止旧代
        自身._代际=threading.Event()#新代
        自身.状态.set({})#清空

    def 拆除(自身):#拆除
        """取消未完并等结算。"""
        自身._寿命.set()#中止
        if len(自身._在飞)>0:#有在飞
            _等待全部(list(自身._在飞))#等

    def _读(自身,网址):#一次拉取
        """解码应答或失败态。"""
        if 自身._寿命.is_set() or 自身._代际.is_set():#已中止
            return#空
        try:#拉取
            if 自身._拉取 is not None:#注入
                应答=自身._拉取(网址,{'method':'GET'})#GET
                if 应答 is None:#无应答
                    下一=自身._策略['failed']#失败
                else:#有应答
                    下一=自身._策略['decode'](应答)#解码
            else:#无拉取
                下一=自身._策略['failed']#失败
        except Exception:#传输失败
            下一=自身._策略['failed']#失败
        if not 自身._寿命.is_set() and not 自身._代际.is_set():#未中止
            def 写下一(态):#发布
                """下一态。"""
                态[网址]=下一#写
            自身.状态.update(写下一)#发布
