'投递和变更文件走所属会话的授权地址，再接到共用打开按钮。'
from .文件应用 import 接上文件应用
from .打开目标按钮 import 打开目标按钮

__all__=['查询路由','文件路由动作']


def 查询路由(网址,信号):
    '这个网页引擎不再通过浏览器请求宿主。没有应用，回落到显示位置'
    return None


class 文件路由动作:
    '不绕开所属会话的授权地址。没有桌面时不画'
    def __init__(自身,属性=None):
        '记下 props。有窗口就画'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.按钮=None
        自身.根=None
        自身.绘制中=False
        自身.待重画=False
        自身.联想键=None
        自身.状态仓=None
        自身.刷新函数=None
        自身.退订联想=None
        if 'window' in 自身.属性:
            自身.渲染()

    def 更新(自身,属性):
        '换上新的 props'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 重画(自身):
        '文件关联变了'
        if 自身.绘制中:
            自身.待重画=True
            return
        自身.渲染()

    def 卸根(自身):
        '没有桌面时拆掉旧按钮'
        if 自身.根 is not None:
            自身.根.remove()
        自身.根=None
        自身.按钮=None

    def 渲染(自身):
        '桌面可用才画紧凑的文件按钮'
        if 自身.绘制中:
            自身.待重画=True
            return 自身.根
        自身.绘制中=True
        try:
            属性=自身.属性
            网址=属性.get('actionUrl')
            启用=bool(属性.get('available'))
            if 启用 is not True:
                接上文件应用(自身,网址,查询路由,False,自身.重画)
                自身.卸根()
            else:
                联想=接上文件应用(自身,网址,查询路由,True,自身.重画)
                应用=联想['apps']
                默认=None
                for 项 in 应用:
                    if 项.get('default') is True:
                        默认=项['id']
                        break

                def 执行(操作,属性=属性):
                    '打开或显示位置交给所属会话'
                    if 操作['kind']=='reveal':
                        动作='reveal'
                    else:
                        动作='open'
                    应用标识=操作['id'] if 操作['kind']=='application' else None
                    return 属性['onAction'](动作,应用标识)

                面={
                    'window':属性['window'],
                    'kind':'file',
                    'applications':应用,
                    'defaultId':默认,
                    'failed':联想['failed'],
                    'loading':联想['loading'],
                    'busy':属性.get('pending') is True,
                    'refresh':联想['refresh'],
                    'execute':执行,
                    'absolutePath':网址,
                }
                if 'parent' in 属性:
                    面['parent']=属性['parent']
                if 自身.按钮 is None:
                    自身.按钮=打开目标按钮(面)
                else:
                    自身.按钮.更新(面)
                    自身.按钮.渲染()
                自身.根=自身.按钮.根
        finally:
            自身.绘制中=False
        if 自身.待重画:
            自身.待重画=False
            return 自身.渲染()
        return 自身.根

    def __call__(自身,属性=None):
        '再次交给槽位时刷新'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()
