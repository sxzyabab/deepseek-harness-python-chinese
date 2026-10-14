from .回退命令卡 import 回退命令卡#命令卡
from .消息项 import 打开列

__all__=['审批命令']#仅中文公开名

from nicegui import ui as 界面

from nicegui import ui as 界面

def 恒等翻译(键,参数=None):
    '无文案表时返回键本身'
    return 键#键即文案

class 审批命令:
    '复用回退命令卡展示关联命令'
    def __init__(自身,属性=None):
        '记下合成 props'
        自身.属性=属性 if 属性 is not None else {}#合成
        自身.卡=回退命令卡()#卡
        自身.根=None#列
        自身.渲染()#槽位只调用构造，这里就要画

    def 更新(自身,属性):
        '刷新 props'
        自身.属性=属性 if 属性 is not None else {}#新

    def 渲染(自身):
        '审批命令'
        属性=自身.属性#props
        if 'node' in 属性 and 属性['node'] is not None:#有节点
            节点=属性['node']#节点
        elif 'command' in 属性 and 属性['command'] is not None:#有命令
            节点=属性['command']#命令
        else:#缺
            节点={}#空
        翻译=属性['t'] if 't' in 属性 else 恒等翻译#文案
        with 打开列(自身,'审批命令'):
            界面.label(翻译('command.title')).classes('标题')
            自身.卡.更新({'node':节点,'t':翻译})
            自身.卡.渲染()

    def __call__(自身,属性=None):
        '对齐'
        if 属性 is not None:
            自身.更新(属性)#刷
        自身.渲染()#画
