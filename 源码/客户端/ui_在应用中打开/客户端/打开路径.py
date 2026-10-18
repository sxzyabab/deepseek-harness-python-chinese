'主机能不能把路径交给桌面，以及打开、显示位置、查询文件关联。'
from ...存储 import 创建快照存储

__all__=['在应用中打开路径控制器']


class 在应用中打开路径控制器:
    '整页一份桌面可用性，以及各处路径按钮共用的打开和揭示'
    def __init__(自身,远程):
        '记下会话远程'
        自身.远程=远程
        自身.桌面=创建快照存储(None)
        自身.加载中=None

    def 加载(自身):
        '每个控制器只问一次桌面。失败发布不可用'
        if 自身.加载中 is not None:
            return
        自身.加载中=True
        自身.跑()

    def 打开路径(自身,路径,动作,应用=None):
        '打开或显示位置。返回要宣告的失败种类，主机确认则是 None'
        if 动作=='reveal':
            请求={'path':路径,'action':动作}
        elif 应用 is None:
            请求={'path':路径}
        else:
            请求={'path':路径,'application':应用}
        成功=False
        try:
            成功=自身.远程.session.openWorkspacePath(请求)['ok'] is True
        except Exception:
            成功=False
        if 成功:
            return None
        if 动作=='open':
            return 'openError'
        return 'revealError'

    def 查询应用(自身,路径,信号):
        '刷新这个文件的系统关联。查询失败是 None，和空列表分开'
        try:
            结果=自身.远程.session.workspacePathApplications({'path':路径},信号)
        except Exception:
            return None
        if 结果['ok'] is True:
            return 结果['value']
        return None

    def 跑(自身):
        '问主机能否把路径交给桌面。到不了就当成不能'
        可用=False
        try:
            结果=自身.远程.session.canOpenWorkspacePath()
            可用=bool(结果['ok'] and 结果['value'])
        except Exception:
            可用=False
        自身.桌面.set(可用)
