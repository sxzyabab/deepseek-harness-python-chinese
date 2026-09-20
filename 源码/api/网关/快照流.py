"""叠在可重连 Remote 流上的基线加增量协议。"""
import threading#消费线程
from .网关 import 已中止#中止查询

__all__=['远程快照流']#仅中文公开名


def _协议违规(消息):
    """Host 侧流协议违规。"""
    错误=RuntimeError(消息)#错误
    错误.name='RemoteError'#名
    错误.code='gateway/internal'#码
    return 错误


class 远程快照流:
    """消费每代恰好一个开口快照再跟增量的代际。"""

    def __init__(自身,流,选项):
        """选项：name / isSnapshot / replace / update / failed。流为远程流。"""
        自身._流=流#底层
        自身._选项=选项#选项
        自身._已启动=False
        自身._已拆除=False#拆除
        自身._完成=threading.Event()#消费完成

    def start(自身):
        """启动单消费者；重复调用无效果。"""
        if 自身._已启动:#已启
            return#空
        自身._已启动=True#标记
        线=threading.Thread(target=自身._消费,daemon=True,name='dsh-remote-snapshot')#泵
        线.start()

    def restart(自身):
        """替换活动物理代际。"""
        自身._流.restart()

    def dispose(自身):
        """永久停止并等待消费者静默。"""
        自身._已拆除=True#标记
        自身._流.dispose()#拆底层
        自身._完成.wait(timeout=30)

    def _消费(自身):
        """消费循环。"""
        代际=0#当前
        已见快照=False#本代
        try:
            for 项 in 自身._流:#逐项
                if 项.generation!=代际:#换代
                    代际=项.generation#更新
                    已见快照=False#重置
                if 自身._选项['isSnapshot'](项.value):#快照
                    if 已见快照:#重复
                        raise _协议违规(自身._选项['name']+' emitted more than one opening snapshot')#违规
                    自身._选项['replace'](项.value)#替换
                    已见快照=True#记下
                    项.accept()#接受开口
                    continue#下一项
                if not 已见快照:#增量早到
                    raise _协议违规(自身._选项['name']+' emitted an update before its opening snapshot')#违规
                自身._选项['update'](项.value)#增量
        except BaseException as 错误:
            if not 自身._已拆除:#未拆
                自身._选项['failed'](错误)
        finally:
            自身._完成.set()#结算
