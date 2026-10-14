from .调用模型 import 派生工具行
from .网页卡模型 import 网页卡模型
from .工具行 import 工具行
from .文案 import 会话命名空间

__all__=['网页行','网页工具视图','网页标题表']

网页标题表={'web_search':'Search','web_fetch':'Fetch'}

class 网页行:
    '按工具名选图标与标题。槽位只调用构造，键齐了就画'
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
        网页=网页卡模型(块)
        标题=网页标题表[工具名] if 工具名 in 网页标题表 else None
        if 标题 is None:
            标题=模型['title'] if 'title' in 模型 else None
        图标='browse' if 工具名=='web_fetch' else 'globe'
        载荷={
            't':属性['t'] if 't' in 属性 else None,
            'variant':模型['variant'] if 'variant' in 模型 else None,
            'toolName':工具名,
            'icon':图标,
            'title':标题,
            'summary':模型['summary'] if 'summary' in 模型 else None,
            'body':None,
            'output':模型['output'] if 'output' in 模型 else None,
            'errorSummary':模型['errorSummary'] if 'errorSummary' in 模型 else None,
            'web':网页,
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

网页工具视图={
    'name':'web-toolview',
    'inject':['slots'],
    'keys':('web_search','web_fetch'),
    'locale':会话命名空间,
    'component':网页行,
}
