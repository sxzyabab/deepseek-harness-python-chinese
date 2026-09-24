__all__=['内嵌帧呈现形式']

class 内嵌帧呈现形式:
    """持有准备文档；挂载时把修订交给载体回调。"""
    def __init__(自身,事件):
        自身.事件=事件
        自身.视口标识=None
        自身.文档=None
        自身.已绘=False

    def 挂载(自身,视口标识):
        旧=自身.视口标识
        自身.视口标识=视口标识
        if 自身.已绘:
            自身.事件['remounted']()
        else:
            自身.绘制()
        def 卸():
            if 自身.视口标识!=视口标识:
                return
            自身.视口标识=None
        return 卸

    def 展示(自身,值):
        自身.文档=值
        自身.绘制()

    def 拆除(自身):
        自身.视口标识=None
        自身.文档=None

    def 绘制(自身):
        当前=自身.文档
        if 当前 is None or 自身.视口标识 is None:
            return
        自身.已绘=True
        自身.事件['loaded'](当前['revision'])
