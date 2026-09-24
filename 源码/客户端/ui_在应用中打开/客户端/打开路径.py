from ...存储 import 创建快照存储

__all__=['在应用中打开路径控制器']

class 在应用中打开路径控制器:
    """页面寿命内的桌面可用性与打开/揭示载体。"""
    def __init__(自身,远程):
        自身.远程=远程
        自身.桌面=创建快照存储(None)
        自身.加载中=None

    def 加载(自身):
        if 自身.加载中 is None:
            自身.跑()
            自身.加载中=True
        return

    def 打开路径(自身,路径,动作,应用=None):
        请求={'path':路径,'action':动作} if 动作=='reveal' else {'path':路径}
        if 动作!='reveal' and 应用 is not None:
            请求['application']=应用
        成功=False
        try:
            应答=自身.远程.session.openWorkspacePath(请求)
            if hasattr(应答,'等待'):
                应答=应答.等待()
            成功=isinstance(应答,dict) and 应答.get('ok') is True
        except Exception:
            成功=False
        if 成功:
            return None
        return 'openError' if 动作=='open' else 'revealError'

    def 应用列表(自身,路径,信号):
        try:
            应答=自身.远程.session.workspacePathApplications({'path':路径},信号)
            if hasattr(应答,'等待'):
                应答=应答.等待()
        except Exception:
            return None
        if isinstance(应答,dict) and 应答.get('ok') is True:
            return 应答.get('value')
        return None

    def 跑(自身):
        可用=False
        try:
            应答=自身.远程.session.canOpenWorkspacePath()
            if hasattr(应答,'等待'):
                应答=应答.等待()
            可用=isinstance(应答,dict) and 应答.get('ok') is True and 应答.get('value') is True
        except Exception:
            可用=False
        自身.桌面.set(可用)
