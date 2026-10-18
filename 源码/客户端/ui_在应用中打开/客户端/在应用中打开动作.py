'把已安装的目录应用接到共用打开按钮。'
from .文案 import 中文
from .应用列表 import 应用标签键
from .打开目标按钮 import 打开目标按钮

__all__=['在应用中打开动作']


def 原样(值):
    '选择整份快照'
    return 值


class 在应用中打开动作:
    '目录分体按钮。没有能命名的应用时不画'
    def __init__(自身,属性=None):
        '记下 props。键齐了就画'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.按钮=None
        自身.根=None
        自身.已订=False
        自身.绘制中=False
        自身.待重画=False
        if 'window' in 自身.属性 and 'useOpenInAppApps' in 自身.属性:
            自身.渲染()

    def 更新(自身,属性):
        '换上新的 props'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 确保订阅(自身):
        '应用表、选择、启动和快捷键变了就重画'
        if 自身.已订:
            return
        自身.已订=True

        def 变更():
            '快照变了'
            if 自身.绘制中:
                自身.待重画=True
                return
            自身.渲染()

        for 名 in ('useOpenInAppApps','useOpenInAppChoice','useOpenInAppLaunch','useShortcuts'):
            钩=自身.属性.get(名)
            订=getattr(钩,'_subscribe',None)
            if callable(订):
                订(变更)

    def 卸根(自身):
        '没有按钮时拆掉旧节点'
        if 自身.根 is not None:
            自身.根.remove()
        自身.根=None
        自身.按钮=None

    def 渲染(自身):
        '有可命名应用才画出共用按钮'
        if 自身.绘制中:
            自身.待重画=True
            return 自身.根
        自身.绘制中=True
        try:
            自身.确保订阅()
            属性=自身.属性
            可用=属性['useOpenInAppApps'](原样)
            选择=属性['useOpenInAppChoice'](原样)
            操作=属性['useOpenInAppLaunch'](原样)

            def 找本地打开(行表):
                'workspace.openLocal'
                for 行 in 行表:
                    if 行['id']=='workspace.openLocal':
                        return 行
                return None

            快捷=属性['useShortcuts'](找本地打开)
            源=可用 if isinstance(可用,list) else []
            应用=[]
            for 标识 in 源:
                键=应用标签键.get(标识)
                if 键 is None:
                    continue
                应用.append({
                    'id':标识,
                    'name':中文[键],
                    'icon':属性['iconUrl'](标识),
                })
            偏好=None
            for 项 in 应用:
                if 项['id']==选择:
                    偏好=项
                    break
            if 偏好 is None and len(应用)>0:
                偏好=应用[0]
            if 偏好 is None:
                自身.卸根()
            else:
                def 执行(操作,偏好=偏好,属性=属性):
                    '默认用当前应用。点了菜单里的应用再记住'
                    if 操作['kind']=='application':
                        标识=操作['id']
                    else:
                        标识=偏好['id']
                    try:
                        属性['launch'](标识,属性['absolutePath'])
                    except Exception:
                        return 'openError'
                    if 操作['kind']=='application':
                        属性['choose'](标识)
                    return None

                面={
                    'window':属性['window'],
                    'kind':'directory',
                    'applications':应用,
                    'defaultId':偏好['id'],
                    'failed':False,
                    'busy':操作['phase']=='busy',
                    'shortcut':快捷,
                    'execute':执行,
                    'absolutePath':属性.get('absolutePath'),
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
