from ...工具.超时 import 若已中止则抛出
from .唤醒 import 输出等待者,休眠

__all__=['流出作业表行']

def 流出作业表行(注册表,请求,选项,信号):
    """按会话可见集合整表替换：开口一帧，生命周期提交后再一帧。"""
    若已中止则抛出(信号)
    等待者=输出等待者()
    def 监听(事件):
        """输出追加不刷新名册。"""
        if 事件['type']=='output':
            return
        拥有者=事件['job']['owner'] if 'owner' in 事件['job'] else None
        if 拥有者 is None or 拥有者==请求['sessionId']:
            等待者.唤醒()
    退订=注册表.events.subscribe({'owners':'all'},监听)
    try:
        yield {'type':'rows','jobs':注册表.list(请求['sessionId'])}
        while True:
            等待者.等待(信号)
            休眠(选项['flushMs'],信号)
            if 信号 is not None and 信号.is_set():
                return
            yield {'type':'rows','jobs':注册表.list(请求['sessionId'])}
    finally:
        退订()
