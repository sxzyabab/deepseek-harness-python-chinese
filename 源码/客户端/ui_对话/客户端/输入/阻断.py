'别的插件让某个会话的输入停下来的唯一入口'
from ....存储 import 创建快照存储

__all__=['撰写器阻断登记表']

class 撰写器阻断登记表:
    '每个插件纤程一份。按会话存阻断原因'
    def __init__(自身):
        '空表'
        自身.存储表={}

    def set(自身,会话标识,阻断):
        '原因没变就不发布'
        仓=自身.storeFor(会话标识)
        当前=仓.getSnapshot()
        当前原因=None if 当前 is None else 当前.get('reason')
        下一原因=None if 阻断 is None else 阻断.get('reason')
        if 当前原因==下一原因:
            return
        仓.set(阻断)

    def storeFor(自身,会话标识):
        '没有就建一份快照'
        已有=自身.存储表.get(会话标识)
        if 已有 is not None:
            return 已有
        建=创建快照存储(None)
        自身.存储表[会话标识]=建
        return 建

    def forget(自身,会话标识):
        '会话走了就忘掉这份阻断'
        if 会话标识 in 自身.存储表:
            del 自身.存储表[会话标识]
