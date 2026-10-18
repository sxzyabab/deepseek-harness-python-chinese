'按认证地址缓存宿主记录。连接换了就清空，拆除时取消还在读的'
from ...模块.客户端.通告 import 取握手窗口
import threading
from ...存储 import 创建快照存储

__all__=['宿主读存储']


class 宿主读存储:
    '一种记录的读取。策略决定加载态、失败态、能否再读和解码'
    def __init__(自身,策略):
        '记下策略，并准备寿命和代际'
        窗口=取握手窗口()
        自身.策略=策略
        自身.状态=创建快照存储({})
        自身._寿命=窗口.AbortController()
        自身._代际=窗口.AbortController()
        自身._在飞=set()

    def 加载网址(自身,网址):
        '已有且策略不让重读就保持。否则发布加载态再读'
        当前=自身.状态.getSnapshot().get(网址)
        if 自身._寿命.signal.aborted:
            return
        if 当前 is not None and not 自身.策略['retryable'](当前):
            return

        def 写加载(状态):
            '进入加载'
            状态[网址]=自身.策略['loading']

        自身.状态.update(写加载)
        完成=threading.Event()
        自身._在飞.add(完成)
        try:
            窗口=取握手窗口()
            信号=窗口.AbortSignal.any([自身._寿命.signal,自身._代际.signal])
            自身._读(网址,信号)
        finally:
            完成.set()
            自身._在飞.discard(完成)

    def 重置(自身):
        '丢掉全部状态，并让还在飞的读取不能再发布'
        自身._代际.abort()
        自身._代际=取握手窗口().AbortController()
        自身.状态.set({})

    def 拆除(自身):
        '取消未完的读取，并等到它们不再发布'
        自身._寿命.abort()
        for 完成 in list(自身._在飞):
            完成.wait()

    def _读(自身,网址,信号):
        '这个网页引擎不再通过浏览器请求宿主'
        下一=自身.策略['failed']
        if 信号.aborted:
            return

        def 写下一(状态):
            '发布这一次的结果'
            状态[网址]=下一

        自身.状态.update(写下一)
