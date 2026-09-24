from .登录对话框 import 登录对话框
from .登出图标 import 登出图标
from .账号头像 import 账号头像

__all__=['账号菜单']

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

class 账号菜单:
    """侧栏账号入口与本机权威退出登录。"""
    def __init__(自身,属性):
        """记下 props。"""
        自身.属性=属性
        自身.已打开=False
        自身.忙碌=False
        自身.退出失败=False
        自身.头像=账号头像()
        自身.对话框=None

    def 更新(自身,属性):
        """刷新。"""
        自身.属性=属性

    def 关菜单(自身):
        """收起菜单。"""
        自身.已打开=False

    def 切菜单(自身):
        """开或关。"""
        自身.已打开=not 自身.已打开

    def 退出(自身):
        """退出已存凭证。"""
        自身.忙碌=True
        自身.退出失败=False
        try:
            自身.属性['signOut']()
            自身.已打开=False
        except Exception:
            自身.退出失败=True
        自身.忙碌=False

    def 开始登录(自身):
        """关菜单后发起；失败由弹窗呈现。"""
        自身.已打开=False
        try:
            自身.属性['start']()
        except Exception:
            return

    def 选中(自身,标识):
        """菜单项。"""
        if 标识=='settings':
            自身.已打开=False
            自身.属性['openSettings']()
        elif 标识=='contact':
            自身.已打开=False
            自身.属性['contactUs']()
        elif 标识=='signin':
            自身.开始登录()
        else:
            自身.退出()

    def 渲染(自身):
        """入口、菜单项与可选登录弹窗。"""
        翻译=自身.属性['t']
        账号=读账号(自身.属性)
        主题=读主题(自身.属性)
        配色=主题.get('active',{}).get('colorScheme','light')
        已登录=账号.get('view') is not None and 账号['view'].get('status')=='credential-stored'
        资料=None if 账号.get('details') is None else 账号['details'].get('profile')
        标签=None
        if 资料 is not None:
            if 资料.get('status')=='ready':
                值=资料.get('value') or {}
                标签=值.get('name') or 值.get('contact') or 翻译('signedIn')
            else:
                标签=翻译('signedIn')
        头像网址=None
        if 已登录 and 资料 is not None and 资料.get('status')=='ready':
            头像网址=(资料.get('value') or {}).get('avatarUrl')
        项=[
            {'id':'settings','label':翻译('settings'),'icon':'settings'},
            {'id':'contact','label':翻译('contactUs'),'icon':'contact'},
        ]
        if 已登录:
            项.append({'id':'signout','label':翻译('signOut'),'icon':登出图标(),'disabled':自身.忙碌})
        else:
            项.append({'id':'signin','label':翻译('signIn'),'icon':'user'})
        弹窗=None
        if 账号.get('loginVisible') and not 账号.get('onboarding'):
            def 关弹窗():
                """关掉登录。"""
                自身.属性['showLogin'](False)
            def 改走密钥():
                """关掉登录并打开官方引导。"""
                自身.属性['showLogin'](False)
                自身.属性['openOnboarding']('deepseek-official')
            面={
                'account':账号,
                'colorScheme':配色,
                'start':自身.属性['start'],
                'cancel':自身.属性['cancel'],
                'close':关弹窗,
                'useApiKey':改走密钥,
                't':翻译,
            }
            if 自身.对话框 is None:
                自身.对话框=登录对话框(面)
            弹窗=自身.对话框(面)
        宽=自身.属性.get('wide')
        return {
            'type':'account-menu',
            'cssModule':'账号菜单.module.css',
            'wide':宽,
            'open':自身.已打开,
            'menuLabel':翻译('menu'),
            'avatar':自身.头像({'url':头像网址}),
            'label':标签 if 已登录 else 翻译('signedOut'),
            'items':项,
            'onToggle':自身.切菜单,
            'onClose':自身.关菜单,
            'onSelect':自身.选中,
            'dialog':弹窗,
            'logoutFailed':翻译('failed') if 自身.退出失败 else None,
        }

    def __call__(自身,属性=None):
        """对齐 React 调用。"""
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()
