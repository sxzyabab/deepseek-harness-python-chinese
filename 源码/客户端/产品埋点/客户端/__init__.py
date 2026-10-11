'桌面渲染进程的埋点发送器；浏览器没有采集能力'
from ....依赖.cordis import 服务
from ....基础设施.通用工具 import 获取内部数据,启动守护线程
from ....基础设施.通用工具.时间工具 import 当前毫秒
from ..事件 import 产品事件字段

__all__=['依赖','应用','桌面埋点']

依赖=['remote','remote.productAnalytics']

class 桌面埋点(服务):
    '同步宿主策略后发送，不因断线补发'
    def __init__(自身,上下文):
        '没有桌面标记则不订阅策略'
        super().__init__(上下文,'productAnalytics')
        自身.上下文=上下文
        自身.采集中=False

        def 提交(事件):
            '远程断开不打断操作'
            try:
                结果=上下文.remote.productAnalytics.report(事件)
                if hasattr(结果,'等待'):
                    结果.等待()
            except Exception:
                return
        自身._提交=提交
        if 'dshDesktop' not in globals():
            return
        def 打开(信号):
            '打开策略流'
            return 上下文.remote.productAnalytics.watchPolicy(信号)
        def 结束():
            '流结束'
            return RuntimeError('product analytics policy stream ended')
        def 载体失败():
            '断线后停采'
            自身.采集中=False
        流=获取内部数据(上下文.remote,'stream')({
            'name':'product analytics policy',
            'open':打开,
            'ended':结束,
            'carrierFailed':载体失败,
        })
        def 拆除效果():
            '卸载时停采并拆流'
            def 清理():
                '停采'
                自身.采集中=False
                return 流.dispose()
            return 清理
        上下文.副作用(拆除效果)
        def 消费():
            '把策略帧写成是否采集'
            try:
                for 帧 in 流:
                    自身.采集中=帧['value'] if isinstance(帧,dict) else 帧.value
                    if isinstance(帧,dict):
                        帧['accept']()
                    else:
                        帧.accept()
            except Exception:
                自身.采集中=False
        启动守护线程(消费)

    @property
    def enabled(自身):
        '同步后的宿主配置是否允许采集'
        return 自身.采集中

    def track(自身,名称,属性,时间戳=None):
        '发送一条事件；关闭或未连接时丢掉，不留待以后'
        if not 自身.enabled:
            return
        if 名称 not in 产品事件字段:
            return
        if 时间戳 is None:
            时间戳=当前毫秒()
        自身._提交({'eventName':名称,'attributes':属性,'timestamp':时间戳})

def 应用(上下文):
    '浏览器应用上下文上挂桌面埋点'
    上下文.插件(桌面埋点)

inject=依赖
apply=应用
