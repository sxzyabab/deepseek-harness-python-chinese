import threading
from ....基础设施.js特性 import PromiseEX as 期约#消费结束的异步结果
from ....基础设施.通用工具 import 获取内部数据
from ....api.网关.异常 import 远程流载体错误
from ....客户端.存储 import 创建快照存储

__all__=['观察就绪度']

def 观察就绪度(上下文):
    '每个 Client 插件订阅一次，与页面和 Session 无关'
    状态=创建快照存储({'catalog':None,'connected':False,'error':None})
    已拆除=False
    def 失败(错误):
        '只写传输失败，不改写 Host 就绪字段'
        当前=状态.getSnapshot()
        状态.set({**当前,'connected':False,'error':str(错误)})
    def 开流(信号):
        '打开就绪流'
        return 上下文.remote.speech.follow(信号)
    def 流结束():
        '流意外结束'
        return 远程流载体错误('Speech readiness stream ended')
    流=获取内部数据(上下文.remote,'stream')({
        'name':'Speech readiness',
        'open':开流,
        'ended':流结束,
        'carrierFailed':失败,
    })
    观察结果=期约()#消费线程结束后兑现
    def 消费():
        '把目录帧写入共享快照'
        try:
            for 帧 in 流:
                状态.set({'catalog':帧.value,'connected':True,'error':None})
                帧.accept()
        except Exception as 错误:
            if not 已拆除:
                失败(错误)
        finally:
            观察结果.解决(None)
    threading.Thread(target=消费,daemon=True).start()
    def 等观察结束(流已拆除值):
        '流拆除后等消费线程结束'
        return 观察结果
    def 拆除():
        '停流并等消费结束。返回期约'
        nonlocal 已拆除
        已拆除=True
        return 流.dispose().然后(等观察结束)
    return {'state':状态,'dispose':拆除}
