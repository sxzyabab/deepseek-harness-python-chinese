'分叉菜单项。当前会话不允许 session/fork 时不画'
from ....模块.客户端.通告 import 取握手窗口
from .派生 import 菜单项按钮,画图标,换上
from ..文案 import 中文

__all__=['分叉会话菜单项','分叉会话菜单项组件']

class 分叉会话菜单项:
    '在最后一轮已完成处分叉。子会话由宿主列表送回来'
    def __init__(自身,属性):
        '记下属性'
        自身.属性=属性#宿主属性
        自身.根=None#节点

    def 渲染(自身):
        '没有分叉权限就不画'
        属性=自身.属性#属性
        窗口=属性['window'] if 'window' in 属性 else 取握手窗口()#窗口
        会话号=属性['sessionId']#会话
        允许=属性['useSessionAccess'](会话号,'session/fork')#权限
        if not 允许:#不允许
            return 换上(自身,None)#不画
        def 找分叉(行列):
            '分叉命令的快捷键'
            for 行 in 行列:#目录
                if 行.get('id')=='session.fork':#分叉
                    return 行#这条
            return None#没有
        快捷=属性['useShortcuts'](找分叉)#分叉快捷键
        打开对=属性['useMenuOpenState']()#菜单
        def 点下():
            '关掉菜单再分叉'
            打开对[1](False)#关掉
            属性['forkSession'](会话号)#分叉
        根=菜单项按钮(窗口,中文['menu.fork'],点下,画图标(窗口,'branch-16'),快捷)#菜单项
        return 换上(自身,根)#节点

def 分叉会话菜单项组件(属性):
    '渲染器按函数调用'
    return 分叉会话菜单项(属性).渲染()#节点
