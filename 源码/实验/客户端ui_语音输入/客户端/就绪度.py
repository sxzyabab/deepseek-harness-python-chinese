import threading
from ....api.网关.流载体 import 远程流载体错误
from ....客户端.存储 import 创建快照存储

__all__=['观察就绪度']

def 观察就绪度(上下文):
    """每个 Client 插件订阅一次，与页面和 Session 无关。"""
    状态=创建快照存储({'catalog':None,'connected':False,'error':None})
    已拆除=False
    def 失败(错误):
        """只写传输失败，不改写 Host 就绪字段。"""
        当前=状态.getSnapshot()
        状态.set({**当前,'connected':False,'error':str(错误)})
    def 开流(信号):
        """打开就绪流。"""
        return 上下文.remote.speech.follow(信号)
    def 流结束():
        """流意外结束。"""
        return 远程流载体错误('Speech readiness stream ended')
    流=上下文.remote.$stream({
        'name':'Speech readiness',
        'open':开流,
        'ended':流结束,
        'carrierFailed':失败,
    })
    观察完成=threading.Event()
    def 消费():
        """把目录帧写入共享快照。"""
        try:
            for 帧 in 流:
                状态.set({'catalog':帧.value,'connected':True,'error':None})
                帧.accept()
        except Exception as 错误:
            if not 已拆除:
                失败(错误)
        finally:
            观察完成.set()
    threading.Thread(target=消费,daemon=True).start()
    def 拆除():
        """停流并等消费结束。"""
        nonlocal 已拆除
        已拆除=True
        流.dispose()
        观察完成.wait()
    return {'state':状态,'dispose':拆除}
