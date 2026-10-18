'叠在可重连 Remote 流上的基线加增量'
from ..异常 import 协议违规#开口违规

class 远程快照流:
    '消费每代恰好一个开口快照，后面才是增量'
    def __init__(自身,流,选项):
        '选项：name、isSnapshot、replace、update、failed'
        自身._流=流#可重连流
        自身._选项=选项#领域操作
        自身._已启动=False#只启动一次
        自身._已拆除=False#拆除后不再报失败
        自身._完成=None#消费线程

    def start(自身):
        '启动单消费者。重复调用无效果'
        if 自身._已启动:#已经
            return#停
        自身._已启动=True#占住
        import threading#后台消费
        完成=threading.Event()#结束
        def 跑():
            '消费直到流结束'
            try:#消费
                自身._消费()#循环
            finally:#放开 dispose
                完成.set()#结束
        threading.Thread(target=跑,daemon=True).start()#不堵启动
        自身._完成=完成#等

    def restart(自身):
        '替换活动物理代际，已发布的快照先留着'
        自身._流.restart()#换代

    def dispose(自身):
        '永久停止并等到消费者静默'
        自身._已拆除=True#不再把结束报成失败
        自身._流.dispose()#停流
        if 自身._完成 is not None:#启动过
            自身._完成.wait()#等

    def _消费(自身):
        '每代先快照再增量'
        代际=0#当前代际
        见过快照=False#这一代是否已有开口
        try:#失败交给领域
            for 项 in 自身._流:#逐项
                if 项.generation!=代际:#新的一代
                    代际=项.generation#换
                    见过快照=False#重新等开口
                if 自身._选项['isSnapshot'](项.value):#开口快照
                    if 见过快照:#第二张
                        raise 协议违规(自身._选项['name']+' emitted more than one opening snapshot')#违规
                    自身._选项['replace'](项.value)#替换
                    见过快照=True#见过
                    项.accept()#接受
                    continue#下一项
                if not 见过快照:#增量出现在开口之前
                    raise 协议违规(自身._选项['name']+' emitted an update before its opening snapshot')#违规
                自身._选项['update'](项.value)#增量
        except Exception as 错误:#终端失败
            if not 自身._已拆除:#不是拆除
                自身._选项['failed'](错误)#交给领域

__all__=['远程快照流']#公开名
