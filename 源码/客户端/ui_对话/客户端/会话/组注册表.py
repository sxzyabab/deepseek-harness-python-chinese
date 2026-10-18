'已有目标上的分组规则'
from ...异常 import 对话错误
from .定义注册表 import 会话定义注册表

__all__=['会话组注册表']

class 会话组注册表(会话定义注册表):
    '一个目标一份分组定义。登记时不实例化构建器'
    def __init__(自身,上下文,视图):
        '记下视图注册表，用来确认目标已经存在'
        super().__init__(上下文)
        自身.视图=视图

    def register(自身,定义):
        '目标必须已经登记'
        已有=False
        for 视图 in 自身.视图.entries():
            if 视图['target']==定义['target']:
                已有=True
                break
        if not 已有:
            raise 对话错误('conversation group target "'+定义['target']+'" is not registered')
        return 自身.登记定义(
            定义['target'],
            定义,
            'conversation group target "'+定义['target']+'" is already registered',
            'uiConversation.groups.register('+repr(定义['target'])+')',
        )

    def forTarget(自身,目标):
        '这个目标的分组定义'
        return 自身.定义表.get(目标)
