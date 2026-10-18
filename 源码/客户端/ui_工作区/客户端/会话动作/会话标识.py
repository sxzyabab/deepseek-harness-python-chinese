'复制这一行的 Session ID，不打开历史'
from ....模块.客户端.通告 import 取握手窗口
from .派生 import 菜单项按钮,画图标,换上
from ..文案 import 中文

__all__=['会话标识菜单项','会话标识菜单项组件']

class 会话标识菜单项:
    '菜单最后一项：复制完整会话号'
    def __init__(自身,属性):
        '记下属性'
        自身.属性=属性#宿主属性
        自身.根=None#节点

    def 渲染(自身):
        '关掉菜单后复制'
        属性=自身.属性#属性
        窗口=属性['window'] if 'window' in 属性 else 取握手窗口()#窗口
        会话号=属性['sessionId']#会话
        打开对=属性['useMenuOpenState']()#菜单
        def 点下():
            '关掉再复制'
            打开对[1](False)#关掉
            属性['copySessionId'](会话号)#复制
        根=菜单项按钮(窗口,中文['menu.sessionId'],点下,画图标(窗口,'copy-16'))#菜单项
        return 换上(自身,根)#节点

def 会话标识菜单项组件(属性):
    '渲染器按函数调用'
    return 会话标识菜单项(属性).渲染()#节点
