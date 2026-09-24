from .登录对话框 import 登录对话框

__all__=['账号引导']

def 读账号(属性):
    """注入面 hooks.account 快照。"""
    钩=属性.get('hooks') or {}
    存储=钩.get('account')
    if 存储 is not None:
        return 存储.getSnapshot()
    取=属性.get('useAccount')
    if 取 is not None:
        def 全量(快照):
            """整份账号快照。"""
            return 快照
        return 取(全量)
    return {'view':None,'details':None,'failed':False}

def 读主题(属性):
    """注入面 hooks.theme 快照。"""
    钩=属性.get('hooks') or {}
    存储=钩.get('theme')
    if 存储 is not None:
        return 存储.getSnapshot()
    取=属性.get('useTheme')
    if 取 is not None:
        def 全量(快照):
            """整份主题快照。"""
            return 快照
        return 取(全量)
    return {'active':{'colorScheme':'light'}}

class 账号引导:
    """模型设置登录引导：未登录时独占弹窗。"""
    def __init__(自身,属性):
        """占有弹窗。"""
        自身.属性=属性
        自身.对话框=None
        设=属性.get('setOnboarding')
        if 设 is not None:
            设(True)

    def 更新(自身,属性):
        """刷新。"""
        自身.属性=属性

    def 拆除(自身):
        """交还弹窗所有权。"""
        设=自身.属性.get('setOnboarding')
        if 设 is not None:
            设(False)

    def 渲染(自身):
        """已登录则 complete；未登录渲染弹窗。"""
        翻译=自身.属性['t']
        账号=读账号(自身.属性)
        主题=读主题(自身.属性)
        配色=主题.get('active',{}).get('colorScheme','light')
        视图=账号.get('view')
        if 视图 is not None and 视图.get('status')=='credential-stored':
            自身.属性['complete']()
            return None
        if 视图 is None:
            return None
        def 关():
            """关掉登录并结束本步。"""
            自身.属性['showLogin'](False)
            自身.属性['complete']()
        def 改走密钥():
            """关掉登录并走 API Key。"""
            自身.属性['showLogin'](False)
            自身.属性['useApiKey']()
        面={
            'account':账号,
            'colorScheme':配色,
            'start':自身.属性['start'],
            'cancel':自身.属性['cancel'],
            'close':关,
            'useApiKey':改走密钥,
            't':翻译,
        }
        if 自身.对话框 is None:
            自身.对话框=登录对话框(面)
        return 自身.对话框(面)

    def __call__(自身,属性=None):
        """对齐 React 调用。"""
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()
