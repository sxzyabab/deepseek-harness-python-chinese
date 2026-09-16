import json,threading#帧编码与唤醒
from ...工具.双端队列 import 双端队列#有界排队
from .类型 import 远程错误#本包错误

__all__=['终端跟随']#仅中文公开名

class 终端跟随:#一路 Remote 流世代的有界输出队列
    """过慢的跟随者明确失败；稍后附着从屏幕恢复。"""
    def __init__(自身,最大字节):#记下上限
        """最大排队 UTF-8 字节。"""
        自身._队列=双端队列()#帧
        自身._字节=0#已排队
        自身._唤醒=None#等待读
        自身._已关=False#关闭
        自身._已结束=False#finish
        自身._失败=None#超限错误
        自身.最大字节=最大字节#上限
        自身._锁=threading.Lock()#互斥
        自身._有项=threading.Event()#有帧或结束

    def 推入(自身,帧):#排队或失败
        """超限则记下错误并关闭本跟随。"""
        if 自身._已关 or 自身._已结束:#停
            return#忽略
        体=json.dumps(帧,ensure_ascii=False,separators=(',',':'),allow_nan=False)#JSON
        字节=len(体.encode('utf-8'))#UTF-8
        if 自身._字节+字节>自身.最大字节:#超
            自身._失败=远程错误('terminal/view','Terminal output consumer exceeded its buffer; reconnect to recover the current screen',{'issue':'invalidOutput'})#超限
            自身.关闭()#关
            return#结束
        自身._队列.尾推({'frame':帧,'bytes':字节})#入队
        自身._字节+=字节#记账
        自身._有项.set()#唤醒

    def 结束(自身):#交完队列含最终退出
        """标记结束并唤醒读者。"""
        自身._已结束=True#结束
        自身._有项.set()#唤醒

    def 关闭(自身):#停本跟随，不停终端
        """清空队列。"""
        自身._已关=True#关
        自身._队列.清空()#清空
        自身._字节=0#清
        自身._有项.set()#唤醒

    def 读(自身,信号):#排空直到拆或失败
        """产出有序终端帧。"""
        def 中止时():#信号
            """关跟随。"""
            自身.关闭()#关
        if 信号 is not None:#有
            def 监视():#等
                """置位后关。"""
                信号.wait()#等
                中止时()#关
            threading.Thread(target=监视,daemon=True).start()#监视
            if 信号.is_set():#已中止
                中止时()#立刻
        try:#读
            while not 自身._已关:#未关
                下=自身._队列.头弹()#出队
                if 下 is not None:#有
                    自身._字节-=下['bytes']#还账
                    yield 下['frame']#帧
                else:#空
                    if 自身._已结束:#结束
                        break#停
                    自身._有项.clear()#等
                    自身._有项.wait()#等推入
            if 自身._失败 is not None:#超限
                raise 自身._失败#抛
        finally:#关
            自身.关闭()#关
