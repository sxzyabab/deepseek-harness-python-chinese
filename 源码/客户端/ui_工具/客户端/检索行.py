from .调用模型 import 派生工具行
from .检索卡模型 import 检索卡模型
from .工具行 import 工具行
from .文案 import 会话命名空间

__all__=['检索行','检索工具视图','检索标题表']

检索标题表={'grep':'Grep','glob':'Glob'}

class 检索行:
    '共享工具行，卡片材料在 search。槽位只调用构造，键齐了就画'
    def __init__(自身,属性=None):
        '记下 props，并挂上空的工具行。工具行由渲染画出'
        自身.属性=属性 if 属性 is not None else {}
        自身.行=工具行()
        if isinstance(自身.属性,dict) and ('block' in 自身.属性 or 'phase' in 自身.属性):
            自身.渲染()

    def 更新(自身,属性):
        '刷新 props'
        自身.属性=属性 if 属性 is not None else {}

    def 渲染(自身):
        '派生后交给工具行'
        属性=自身.属性
        工具名=属性['toolName'] if 'toolName' in 属性 else None
        块=属性['block'] if 'block' in 属性 else None
        模型=派生工具行(工具名,块)
        检索=检索卡模型(块)
        标题=检索标题表[工具名] if 工具名 in 检索标题表 else None
        if 标题 is None:
            标题=模型['title'] if 'title' in 模型 else None
        摘要=None
        if 检索 is not None:
            摘要=检索['title'] if 'title' in 检索 else None
        if 摘要 is None:
            摘要=模型['summary'] if 'summary' in 模型 else None
        载荷={
            't':属性['t'] if 't' in 属性 else None,
            'variant':模型['variant'] if 'variant' in 模型 else None,
            'toolName':工具名,
            'icon':'search',
            'title':标题,
            'summary':摘要,
            'body':None,
            'output':模型['output'] if 'output' in 模型 else None,
            'errorSummary':模型['errorSummary'] if 'errorSummary' in 模型 else None,
            'search':检索,
            'state':模型['state'] if 'state' in 模型 else None,
            'inspect':属性['inspect'] if 'inspect' in 属性 else None,
        }
        自身.行.更新(载荷)
        return 自身.行.渲染()

    def __call__(自身,属性=None):
        '有新属性则刷新后渲染'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()

检索工具视图={
    'name':'search-toolview',
    'inject':['slots'],
    'keys':('grep','glob'),
    'locale':会话命名空间,
    'component':检索行,
}
