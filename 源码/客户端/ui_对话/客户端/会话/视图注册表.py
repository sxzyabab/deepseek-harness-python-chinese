'每个目标一份快照构建器'
from .定义注册表 import 会话定义注册表

__all__=['会话视图注册表']

class 会话视图注册表(会话定义注册表):
    '已登记的视图构建器工厂'
    def register(自身,定义):
        '同一个目标只能登记一次'
        return 自身.登记定义(
            定义['target'],
            定义,
            'conversation view target "'+定义['target']+'" is already registered',
            'uiConversation.views.register('+repr(定义['target'])+')',
        )
