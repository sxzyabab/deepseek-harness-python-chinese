from ...存储 import 创建快照存储
from .会话视图 import 侧栏会话视图

__all__=['侧栏会话视图集']

class 侧栏会话视图集:
    """选择并退役独立拥有的侧栏会话视图。"""
    def __init__(自身,会话面):
        自身.会话面=会话面
        自身.源=创建快照存储([])
        自身.视图={}
        自身.按引用={}
        自身.已选=None
        自身.已关=False

    def 选择(自身,会话标识):
        if 自身.已关 or 自身.已选==会话标识:
            return
        自身.已选=会话标识
        if 会话标识 is not None and 会话标识 not in 自身.视图:
            def 拆除时(已拆):
                键=id(已拆.引用)
                if 键 in 自身.按引用:
                    del 自身.按引用[键]
            视图=侧栏会话视图(会话标识,自身.会话面,拆除时,自身.修剪)
            自身.视图[会话标识]=视图
            自身.按引用[id(视图.引用)]=视图
        for 视图 in list(自身.视图.values()):
            自身.修剪(视图)
        自身.发布()

    def 挂载(自身,引用):
        视图=自身.按引用.get(id(引用))
        if 视图 is None:
            if 自身.已关:
                return lambda:None
            raise RuntimeError('Sidebar Session view reference is no longer owned')
        return 视图.挂载()

    def 拆除(自身):
        自身.已关=True
        自身.视图.clear()
        自身.源.set([])
        for 视图 in list(自身.按引用.values()):
            视图.拆除()

    def 修剪(自身,视图):
        if 视图.会话标识==自身.已选 or 视图.有保留标签() or 自身.视图.get(视图.会话标识) is not 视图:
            return
        if 视图.会话标识 in 自身.视图:
            del 自身.视图[视图.会话标识]
        自身.发布()
        视图.退役()

    def 发布(自身):
        表=sorted(自身.视图.values(),key=lambda 项:项.会话标识)
        自身.源.set([{
            'sessionId':项.会话标识,
            'reference':项.引用,
            'selected':项.会话标识==自身.已选,
            'retainTab':项.保留标签,
        } for 项 in 表])
