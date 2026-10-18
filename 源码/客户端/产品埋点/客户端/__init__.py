'桌面渲染进程的埋点发送器。浏览器没有采集能力'
from ...模块.客户端.通告 import 取握手窗口
import pywebbridge#页面全局，对应 globalThis
from ....基础设施.通用工具 import 获取内部数据,启动守护线程#远程流入口与策略消费
from ....基础设施.通用工具.时间工具 import 当前毫秒#缺省发生时间
from ....依赖.cordis import 服务#服务基类
from ..事件 import 引导页,产品事件图,产品事件,跟踪产品事件#事件形状

__all__=['依赖','应用','引导页','产品事件图','产品事件','跟踪产品事件']#不把桌面埋点类再导出给包根转发

依赖=['remote','remote.productAnalytics']#认证远程与策略流

class 桌面埋点(服务):
    '同步宿主策略后发送。不留到重连或以后再启用'
    def __init__(自身,上下文):
        '没有桌面标记则不订阅策略'
        super().__init__(上下文,'productAnalytics')#服务名
        自身.采集中=False#默认不采
        def 提交(事件):
            '远程断开或同步失败不打断操作'
            try:#缺远程或调用失败都吞掉
                结果=上下文.remote.productAnalytics.report(事件)#交给宿主
                if hasattr(结果,'等待'):#期约
                    结果.等待()#等它落定
            except Exception as 错误:#不重试，也不向外抛
                return#交互继续。错误是远程断开或同步失败
        自身._提交=提交#调用时仍用构造时的上下文
        窗口=取握手窗口()#页面全局
        if 窗口['dshDesktop'] is pywebbridge.基础.undefined:#不是桌面渲染进程
            return#浏览器没有采集能力
        def 打开(信号):
            '打开策略流'
            return 上下文.remote.productAnalytics.watchPolicy(信号)#宿主策略
        def 流结束(已接受=None):
            '流结束。已接受与否都用同一句'
            return RuntimeError('product analytics policy stream ended')#固定错误
        def 载体失败(错误=None):
            '断线后停采。错误不向外抛'
            自身.采集中=False#失败即关
        流=获取内部数据(上下文.remote,'stream')({#网关把 $stream 放在内部数据 stream
            'name':'product analytics policy',#流名
            'open':打开,#打开
            'ended':流结束,#正常结束
            'carrierFailed':载体失败,#载体失败
        })#流结束
        def 拆除效果():
            '卸载时停采并拆流'
            def 清理():
                '停采'
                自身.采集中=False#不再发
                return 流.dispose()#拆流
            return 清理#拆除器
        上下文.副作用(拆除效果)#随纤程拆除
        def 消费():
            '把策略帧写成是否采集。流断了就停采'
            try:#消费失败即关
                for 帧 in 流:#逐帧
                    自身.采集中=帧.value#当前策略
                    帧.accept()#确认
            except Exception as 错误:#流中断，不向外抛
                自身.采集中=False#停采
        启动守护线程(消费)#构造函数不等待整条流

    @property
    def enabled(自身):
        '同步后的宿主配置是否允许采集'
        return 自身.采集中#当前策略

    def track(自身,名称,属性,时间戳=None):
        '发送一条事件。关闭或未连接时丢掉，不留待以后'
        if not 自身.enabled:#当前不采
            return#丢掉
        if 时间戳 is None:#没给发生时间
            时间戳=当前毫秒()#现在
        自身._提交({'eventName':名称,'attributes':属性,'timestamp':时间戳})#不保留

def 应用(上下文,配置=None):
    '浏览器应用上下文上挂桌面埋点'
    上下文.启动插件(桌面埋点)#类插件

inject=依赖#模块依赖
apply=应用#模块入口
