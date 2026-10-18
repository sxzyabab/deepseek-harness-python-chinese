from ...存储 import 创建快照存储

__all__=['桌面更新源']

忙阶段=('checking','downloading','verifying','installing')

class 桌面更新源:
    '两侧栏共用一份桌面预加载订阅'
    def __init__(自身,桥):
        '桥缺席就是普通浏览器。status 按同步结果收下'
        自身.桥=桥
        自身.存储=创建快照存储({'failed':False,'opening':False})
        自身.活=True
        自身.已收=False
        自身.退订=None
        if 桥 is None:
            return
        def 收到(呈现):
            '推送盖过还没回来的首次 status，并清掉失败'
            if 自身.活 is False:
                return
            自身.已收=True
            当前=自身.存储.getSnapshot()
            自身.存储.set({**当前,'presentation':呈现,'failed':False})
        自身.退订=桥.subscribe(收到)
        try:
            呈现=桥.status()
        except Exception:
            if 自身.活 and 自身.已收 is False:
                当前=自身.存储.getSnapshot()
                自身.存储.set({**当前,'failed':True})
        else:
            if 自身.活 and 自身.已收 is False:
                当前=自身.存储.getSnapshot()
                自身.存储.set({**当前,'presentation':呈现})

    def 打开(自身):
        '点一次。正在检查、下载、校验、安装或已经在打开时，后来的点击并进去'
        if 自身.活 is False or 自身.桥 is None:
            return
        状态=自身.存储.getSnapshot()
        呈现=状态.get('presentation')
        if 状态['opening'] or (呈现 is not None and 呈现.get('phase') in 忙阶段):
            return
        自身.存储.set({**状态,'opening':True})
        try:
            自身.桥.open()
        except Exception:
            if 自身.活:
                当前=自身.存储.getSnapshot()
                自身.存储.set({**当前,'failed':True})
        finally:
            if 自身.活:
                当前=自身.存储.getSnapshot()
                自身.存储.set({**当前,'opening':False})

    def 拆除(自身):
        '拆掉订阅。之后到达的状态和动作结果都忽略'
        自身.活=False
        if 自身.退订 is not None:
            自身.退订()
            自身.退订=None
