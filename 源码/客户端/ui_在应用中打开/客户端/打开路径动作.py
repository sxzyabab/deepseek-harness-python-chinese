'文档预览里的文件关联，接到共用打开按钮。'
from .文件应用 import 接上文件应用
from .打开目标按钮 import 打开目标按钮

__all__=['文件打开目标','打开路径动作']


class 文件打开目标:
    '查出文件关联再画共用按钮。没有桌面时不画'
    def __init__(自身,属性=None):
        '记下 props。键齐了就画'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.按钮=None
        自身.根=None
        自身.已订=False
        自身.绘制中=False
        自身.待重画=False
        自身.联想键=None
        自身.状态仓=None
        自身.刷新函数=None
        自身.退订联想=None
        if 'window' in 自身.属性 and 'useOpenInAppDesktop' in 自身.属性:
            自身.渲染()

    def 更新(自身,属性):
        '换上新的 props'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 重画(自身):
        '桌面或文件关联变了'
        if 自身.绘制中:
            自身.待重画=True
            return
        自身.渲染()

    def 确保订阅(自身):
        '桌面可用性变了就重画'
        if 自身.已订:
            return
        自身.已订=True
        钩=自身.属性.get('useOpenInAppDesktop')
        订=getattr(钩,'_subscribe',None)
        if callable(订):
            订(自身.重画)

    def 卸根(自身):
        '没有桌面时拆掉旧按钮'
        if 自身.根 is not None:
            自身.根.remove()
        自身.根=None
        自身.按钮=None

    def 渲染(自身):
        '桌面可用才画文件按钮'
        if 自身.绘制中:
            自身.待重画=True
            return 自身.根
        自身.绘制中=True
        try:
            自身.确保订阅()
            属性=自身.属性

            def 原样(值):
                '整份桌面可用性'
                return 值

            桌面=属性['useOpenInAppDesktop'](原样)
            if 桌面 is None:
                属性['loadDesktop']()
                桌面=属性['useOpenInAppDesktop'](原样)
            路径=属性['absolutePath']
            查询=属性['applications']
            if 桌面 is not True:
                接上文件应用(自身,路径,查询,False,自身.重画)
                自身.卸根()
            else:
                联想=接上文件应用(自身,路径,查询,True,自身.重画)
                应用=联想['apps']
                默认=None
                for 项 in 应用:
                    if 项.get('default') is True:
                        默认=项['id']
                        break

                def 执行(操作,属性=属性,路径=路径):
                    '揭示，或用点名的应用打开'
                    if 操作['kind']=='reveal':
                        动作='reveal'
                    else:
                        动作='open'
                    应用标识=操作['id'] if 操作['kind']=='application' else None
                    return 属性['openPath'](路径,动作,应用标识)

                面={
                    'window':属性['window'],
                    'kind':'file',
                    'applications':应用,
                    'defaultId':默认,
                    'loading':联想['loading'],
                    'failed':联想['failed'],
                    'prominent':属性.get('empty') is True,
                    'refresh':联想['refresh'],
                    'execute':执行,
                    'absolutePath':路径,
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


class 打开路径动作:
    '文档头上的文件打开按钮'
    def __init__(自身,属性=None):
        '交给文件打开目标'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.目标=None
        自身.根=None
        if 'window' in 自身.属性:
            自身.渲染()

    def 更新(自身,属性):
        '换上新的 props'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 渲染(自身):
        '画出文件按钮'
        if 自身.目标 is None:
            自身.目标=文件打开目标(自身.属性)
        else:
            自身.目标.更新(自身.属性)
            自身.目标.渲染()
        自身.根=自身.目标.根
        return 自身.根

    def __call__(自身,属性=None):
        '再次交给槽位时刷新'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()
