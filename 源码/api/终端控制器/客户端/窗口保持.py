'一条可重连的窗口保持，由这个终端的全部出现共用'
from threading import Event as 事件#确认等待
from threading import current_thread as 当前线程#释放时不要等自己
from ....基础设施.通用工具 import 启动守护线程,获取内部数据#消费保持流
from ....类型化远程调用.协议 import 远程错误#保持结束
from ...网关.流协议 import 已中止,若中止则抛 as 若已中止则抛出#取消
from ....客户端.连接.rpc import 中止信号,中止控制器#取消

__all__=['终端窗口保持']#仅这一类


class 终端窗口保持:
    '流上的确认门控每个物理连接的输出附着'
    def __init__(自身,网关,远程,会话标识,标识):
        '打开保持流并开始消费'
        自身._等待者=set()#还在等确认的人
        自身._代际=None#当前已确认的物理流
        自身._失败=None#终端域失败
        自身._消费线程=None#消费线程

        def 打开(信号):
            '向宿主要这一条保持流'
            return 远程.retain(会话标识,标识,信号)#保留帧

        def 结束(已接受=None):
            '正常结束视为终端不可用'
            return 远程错误('terminal/unavailable','Terminal hold ended',{})#拒绝

        自身._流=获取内部数据(网关,'stream')({#可重连逻辑流
            'name':'Browser terminal window hold',#名字
            'open':打开,#打开一代
            'ended':结束,#结束原因
        })#流
        自身._消费线程=启动守护线程(自身._消费)#后台消费

    @property
    def 已失败(自身):
        '是否因为终端域失败结束，从而允许显式重试'
        return 自身._失败 is not None#有失败

    def 就绪(自身,信号):
        '在跟随屏幕之前，等待当前物理保持已被确认'
        若已中止则抛出(信号)#调用方已取消
        if 自身._失败 is not None:#已经失败
            raise 自身._失败#拒绝
        if 自身._代际 is not None and not 已中止(自身._代际):#当前代还活着
            return#已经确认过
        完成=事件()#这次等待
        完成.错误=None#拒绝时写下

        def 解决():
            '确认到达'
            完成.set()#放开

        def 拒绝(错误):
            '取消或失败'
            完成.错误=错误#记下
            完成.set()#放开

        一对=(解决,拒绝)#这一位等待者
        自身._等待者.add(一对)#登记
        停止=中止控制器()#等待结束时停掉监听
        融合=中止信号.任一([信号,停止.信号])#调用方取消或等待结束

        def 听取消():
            '调用方取消则拒绝这次等待'
            融合._事件.wait()#阻塞
            if 已中止(信号):#是调用方
                原因=signal._异常 if getattr(signal,'_异常',None) is not None else RuntimeError('Terminal window hold aborted')#原因
                拒绝(原因)#拒绝

        启动守护线程(听取消)#后台听
        try:#等到确认或拒绝
            完成.wait()#阻塞
            if 完成.错误 is not None:#被拒绝
                if isinstance(完成.错误,BaseException):#异常
                    raise 完成.错误#原样
                raise RuntimeError(str(完成.错误))#收成异常
        finally:#无论成败都摘掉
            自身._等待者.discard(一对)#摘掉
            停止.中止配套信号()#让监听退出

    def 释放(自身):
        '放开这个窗口的流和全部确认等待'
        自身._拒绝(RuntimeError('Terminal window hold released'))#拒绝等待者
        自身._流.dispose()#停流
        线程=自身._消费线程#消费
        if 线程 is not None and 线程 is not 当前线程():#不是自己
            线程.join()#等消费者退出

    def _消费(自身):
        '接受确认并放开等待者。流失败则全部拒绝'
        try:#读到流结束
            for 项 in 自身._流:#每一项
                项.accept()#这个开口已接受
                自身._代际=项.signal#当前物理代
                for 解决,拒绝 in list(自身._等待者):#全部放开
                    解决()#确认
                自身._等待者.clear()#清掉
        except BaseException as 错误:#流失败
            自身._拒绝(错误)#拒绝等待者

    def _拒绝(自身,错误):
        '记下失败并拒绝全部等待者'
        if isinstance(错误,Exception):#普通异常
            自身._失败=错误#原样
        else:#不是 Error
            自身._失败=RuntimeError('Terminal window hold failed')#固定说明
            if isinstance(错误,BaseException):#还有原因
                自身._失败.__cause__=错误#挂上
        自身._代际=None#不再算已确认
        for 解决,拒绝 in list(自身._等待者):#每一位
            拒绝(错误)#拒绝
        自身._等待者.clear()#清掉
