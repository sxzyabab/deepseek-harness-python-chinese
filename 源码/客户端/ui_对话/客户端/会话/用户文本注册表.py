'效果拥有的用户文本规则和修订号'
from ...异常 import 对话错误
from .定义注册表 import 会话定义注册表
from .用户文本文档 import 用户文本文档

__all__=['用户文本注册表']

class 用户文本注册表(会话定义注册表):
    '规则按顺序和标识排序。文档缓存只属于求值器'
    def __init__(自身,上下文):
        '修订从 0 开始'
        super().__init__(上下文)
        自身.规则=[]
        自身.修订=0

    def register(自身,规则):
        '空标识、保留的 text、非有限顺序都在发布前失败'
        if len(规则['id'])==0:
            raise 对话错误('user-text rule ID must not be empty')
        if 规则['id']=='text':
            raise 对话错误('user-text rule "text" is reserved for original text')
        顺序=规则['order']
        if isinstance(顺序,bool) or not isinstance(顺序,(int,float)) or 顺序!=顺序 or 顺序==float('inf') or 顺序==float('-inf'):
            raise 对话错误('user-text rule "'+规则['id']+'" order must be finite')
        return 自身.登记定义(
            规则['id'],
            规则,
            'user-text rule "'+规则['id']+'" is already registered',
            'uiConversation.userText.register('+repr(规则['id'])+')',
        )

    def createEvaluator(自身):
        '每次调用读当前规则，不订阅'
        文档=用户文本文档()
        def 求值(输入):
            '用这份文档求值'
            return 文档.求值(输入,自身.规则)
        return 求值

    def getSnapshot(自身):
        '规则修订。登记或拆除成功才增加'
        return 自身.修订

    def 刷新(自身):
        '按顺序再按标识排序，并抬修订'
        自身.规则=sorted(自身.定义表.values(),key=lambda 规则:(规则['order'],规则['id']))
        自身.修订+=1
        super().刷新()
