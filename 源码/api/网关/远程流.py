"""单消费者 Remote 流的可重连生命周期。

对齐上游 `api/gateway/src/client/remote-stream.ts`。
用同步生成器对齐异步代际语义；连接代际源取
`connection.generation` 或 `connection.hostDescription`。公开面仅中文名。
"""
import threading#代际寿命与等待
from .流载体 import 远程流载体错误#载体错误
from .网关 import 已中止,中止控制器,中止信号#中止原语

__all__=[#仅中文公开名
    '远程流项','远程流','取连接代际源',
]#公开面结束


def 取连接代际源(连接):
    """返回带 getSnapshot/subscribe 的代际观察面。"""
    if 连接 is None:#无
        return None#空
    if hasattr(连接,'generation'):#上游命名
        return 连接.generation#代际
    if hasattr(连接,'hostDescription'):#本地连接句柄
        return 连接.hostDescription#宿主描述
    return None#无


class 远程流项:
    """带物理代际注解的一项。"""

    def __init__(自身,代际,值,信号,接受器):
        """记下代际、值、信号与接受回调。"""
        自身.generation=代际#代际号
        自身.value=值#条目
        自身.signal=信号#代际信号
        自身._接受器=接受器#接受

    def accept(自身):
        """将该代际开口标为已接受。"""
        自身._接受器()#回调

    def 接受(自身):
        """中文别名。"""
        自身.accept()#委托


class 远程流:
    """跨载体代际重开一条逻辑 Remote 流。"""

    def __init__(自身,连接,选项):
        """选项：name / open(signal)->iterable / ended(accepted)->Error / carrierFailed?。"""
        自身._连接=连接#连接
        自身._选项=选项#选项
        自身._寿命=中止控制器()#逻辑寿命
        自身._代际中止=None#当前代际
        自身._修订=0#重启修订
        自身._已取=False#单消费者
        自身._关闭中=False#拆除旗
        自身._锁=threading.Lock()#状态锁

    @property
    def signal(自身):
        """共享取消寿命。"""
        return 自身._寿命.信号#信号

    @property
    def 信号(自身):
        """中文别名。"""
        return 自身.signal#信号

    def restart(自身):
        """中断当前代际并请求替换。"""
        if 已中止(自身._寿命.信号):#已拆
            return#空
        with 自身._锁:#改修订
            自身._修订+=1#推进
            代=自身._代际中止#当前
        if 代 is not None:#有代
            代.中止(Exception(自身._选项['name']+' generation restarted'))#中止

    def 重启(自身):
        """中文别名。"""
        自身.restart()#委托

    def dispose(自身):
        """永久停止本流。"""
        if 自身._关闭中:#幂等
            return#已拆
        自身._关闭中=True#标记
        if not 已中止(自身._寿命.信号):#未中止
            原因=Exception(自身._选项['name']+' disposed')#原因
            自身._寿命.中止(原因)#中止寿命
            with 自身._锁:#取代
                代=自身._代际中止#当前
            if 代 is not None:#有
                代.中止(原因)#中止代

    def 拆除(自身):
        """中文别名。"""
        自身.dispose()#委托

    def __iter__(自身):
        """单消费者同步迭代。"""
        if 自身._已取:#重复
            raise RuntimeError(自身._选项['name']+' already has a consumer')#拒绝
        自身._已取=True#占用
        return 自身._读()#生成器

    def _读(自身):
        """代际读取循环。"""
        尝试盒=[0]#重试（可变）
        代际号=0#计数
        已观察修订=自身._修订#修订
        try:
            while not 已中止(自身._寿命.信号):#未拆除
                if 已观察修订!=自身._修订:#外部重启
                    已观察修订=自身._修订#同步
                    尝试盒[0]=0#清零
                修订=自身._修订#本代修订快照
                代际控=中止控制器()#本代中止
                with 自身._锁:#登记
                    自身._代际中止=代际控#记下
                信号=中止信号.任一([自身._寿命.信号,代际控.信号])#合成
                代际号+=1#新代
                本代=代际号#捕获
                已接受=[False]#开口是否接受
                try:
                    for 值 in 自身._选项['open'](信号):#开代
                        if 已中止(自身._寿命.信号):#寿命尽
                            return#停
                        if 修订!=自身._修订:#被重启
                            break#换代
                        yield 远程流项(
                            本代,值,信号,
                            lambda 控=代际控,订=修订:自身._标记接受(控,订,已接受,尝试盒),
                        )#投递
                    if 已中止(自身._寿命.信号):#寿命尽
                        return#停
                    if 修订!=自身._修订:#重启
                        continue#下一代
                    raise 自身._选项['ended'](已接受[0])#正常结束分类
                except BaseException as 错误:
                    if 已中止(自身._寿命.信号):#寿命尽
                        return#停
                    if 修订!=自身._修订:#重启
                        continue#下一代
                    if not isinstance(错误,远程流载体错误):#终端
                        raise _终端流失败(错误)#打标
                    回调=自身._选项.get('carrierFailed')#可选
                    if 回调 is not None:#有
                        回调(错误)#观察
                    if 修订!=自身._修订:#重启
                        continue#下一代
                    尝试盒[0]+=1#计数
                    try:
                        _等待远程流重试(自身._连接,错误,尝试盒[0],信号)#等重连
                    except BaseException as 重试错:
                        if 已中止(自身._寿命.信号):#寿命尽
                            return#停
                        if 修订!=自身._修订:#重启
                            continue#下一代
                        raise _终端流失败(重试错)#终端
                finally:
                    with 自身._锁:#清代
                        if 自身._代际中止 is 代际控:#仍是本代
                            自身._代际中止=None#清
                    if not 已中止(代际控.信号):#未中止
                        代际控.中止(Exception(自身._选项['name']+' generation ended'))#结束代
        finally:
            if not 已中止(自身._寿命.信号):#消费者关
                自身._寿命.中止(Exception(自身._选项['name']+' consumer closed'))#关
            with 自身._锁:#取代
                代=自身._代际中止#当前
            if 代 is not None:#有
                代.中止(Exception(自身._选项['name']+' disposed'))#跟寿命

    def _标记接受(自身,控,订,已接受,尝试盒):
        """开口接受：重置重试计数。"""
        with 自身._锁:#核对
            if 自身._代际中止 is not 控 or 订!=自身._修订:#过期
                return#忽略
        已接受[0]=True#接受
        尝试盒[0]=0#清零


def _终端流失败(错误):
    """穿越流边界前标记终端逃逸。"""
    消息=错误.args[0] if isinstance(错误,BaseException) and 错误.args else str(错误)#消息
    包装=RuntimeError(消息)#包装
    包装.name='RemoteError'#近似
    包装.code='gateway/internal'#码
    if isinstance(错误,BaseException):#因果
        包装.__cause__=错误#挂
    return 包装#终端


def _等待远程流重试(连接,错误,尝试,信号):
    """Connection 拥有物理重试时机。"""
    if 已中止(信号):#已取消
        raise Exception('Remote stream retry aborted')#中止
    代际=取连接代际源(连接)#代际源
    if 代际 is not None and 代际.getSnapshot() is not None:#已连接
        if 尝试==1:#首次丢包且宿主仍在
            return#立刻重开
        raise 错误#宿主在却再次失败：终端
    if 代际 is None:#无代际源
        if 尝试==1:#允一次
            return#重开
        raise 错误#再失败终端
    完成=threading.Event()#等待
    失败=[None]#失败槽

    def 检查():
        """快照出现则放行。"""
        if 代际.getSnapshot() is not None:#已连
            完成.set()#放行

    取消订=代际.subscribe(检查)#订阅

    def 中止监视():
        """信号中止则失败。"""
        while not 完成.wait(0.05):#短等
            if 已中止(信号):#取消
                失败[0]=Exception('Remote stream retry aborted')#失败
                完成.set()#放行
                return#停

    线=threading.Thread(target=中止监视,daemon=True)#监视
    线.start()#启
    检查()#即时
    完成.wait()#等
    try:
        取消订()#退订
    except BaseException:
        pass#忽略
    if 失败[0] is not None:#中止
        raise 失败[0]#抛
