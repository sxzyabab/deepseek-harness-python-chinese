'会话定义注册表共用的生命周期和稳定条目'
from .....基础设施.通用工具 import 设置内部数据
from ...异常 import 对话错误

__all__=['会话定义注册表']

class 会话定义注册表:
    '按登记顺序给出稳定的定义列表'
    def __init__(自身,上下文):
        '定义挂在调用方上下文的 effect 上'
        自身.ctx=上下文
        自身.定义表={}
        自身.监听=set()
        自身.缓存=[]
        设置内部数据(自身,'追踪器',{'属性':'ctx'})

    def entries(自身):
        '当前定义，引用稳定到下一次刷新'
        return 自身.缓存

    def subscribe(自身,监听):
        '低频变更。返回退订'
        自身.监听.add(监听)
        def 退订():
            '拿掉这个监听'
            自身.监听.discard(监听)
        return 退订

    def 登记定义(自身,键,定义,重复消息,效果名):
        '同一个键不能登记两次。返回可重复调用的拆除'
        if 键 in 自身.定义表:
            raise 对话错误(重复消息)
        所有者=自身.ctx
        def 挂上():
            '放进表并在拆除时摘掉'
            自身.定义表[键]=定义
            自身.刷新()
            def 拆():
                '只有还是这一份才摘'
                if 自身.定义表.get(键) is not 定义:
                    return
                del 自身.定义表[键]
                自身.刷新()
            return 拆
        拆除=所有者.effect(挂上,效果名)
        def 再拆():
            '幂等拆除'
            if callable(拆除):
                拆除()
        return 再拆

    def 刷新(自身):
        '缓存当前值并同步通知'
        自身.缓存=list(自身.定义表.values())
        for 监听 in list(自身.监听):
            try:
                监听()
            except Exception as 错误:
                print('[ui-conversation] definition registry subscriber failed:',错误)
