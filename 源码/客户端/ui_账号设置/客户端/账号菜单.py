from nicegui import ui as 界面
from ...ui_基础界面组件.icons import 图标设置16,图标用户16
from .登录对话框 import 登录对话框
from .登出图标 import 登出图标
from .账号头像 import 账号头像

__all__=['账号菜单']

菜单样式='''
.账号菜单{flex:1;min-width:0}
button.q-btn.账号触发{width:100%;height:44px;min-height:44px;gap:8px;padding:6px;border-radius:var(--dsw-radius-md);background:transparent !important;box-shadow:none !important;color:var(--dsw-alias-label-primary) !important;font-size:14px;justify-content:flex-start}
button.q-btn.账号触发:hover{background:var(--dsw-alias-interactive-bg-hover) !important}
.账号菜单列{min-width:124px;max-width:280px;padding:4px;background:var(--dsw-specific-menu);border-radius:var(--dsw-radius-lg);box-shadow:var(--dsw-elevation-prominent)}
button.q-btn.账号菜单项{min-height:40px;padding:8px 10px;border-radius:var(--dsw-radius-md);background:transparent !important;box-shadow:none !important;color:var(--dsw-alias-label-primary) !important;font-size:14px;line-height:22px;justify-content:flex-start}
button.q-btn.账号菜单项 .q-btn__content{gap:8px;flex-wrap:nowrap;justify-content:flex-start}
.账号菜单标{flex:none;width:16px;height:16px;color:var(--dsw-alias-menu-icon)}
'''
界面.add_css(菜单样式,shared=True)

def 读账号(属性):
    '注入面 hooks.account 快照'
    钩=属性.get('hooks') or {}
    存储=钩.get('account')
    if 存储 is not None:
        return 存储.getSnapshot()
    取=属性.get('useAccount')
    if 取 is not None:
        def 全量(快照):
            '整份账号快照'
            return 快照
        return 取(全量)
    return {'view':None,'details':None,'failed':False}

def 读主题(属性):
    '注入面 hooks.theme 快照'
    钩=属性.get('hooks') or {}
    存储=钩.get('theme')
    if 存储 is not None:
        return 存储.getSnapshot()
    取=属性.get('useTheme')
    if 取 is not None:
        def 全量(快照):
            '整份主题快照'
            return 快照
        return 取(全量)
    return {'active':{'colorScheme':'light'}}

def 画字形(视图):
    '把图标视图画成 16 像素 svg'
    段=[]
    for 项 in 视图['paths']:
        数据=项 if isinstance(项,str) else 项['d']
        段.append('<path d="'+数据+'" fill="currentColor"/>')
    界面.html(
        '<svg class="账号菜单标" width="16" height="16" viewBox="'+视图['viewBox']+'" fill-rule="evenodd" aria-hidden="true">'+''.join(段)+'</svg>',
        sanitize=False,
    )

def 画纸飞机():
    '意见反馈字形'
    界面.html(
        '<svg class="账号菜单标" width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true" stroke="currentColor" stroke-width="1.3">'
        '<path d="M4.74024 9.11029L1.82882 7.79865C1.75022 7.76323 1.75026 7.65161 1.82889 7.61626L12.9665 2.60943C13.0354 2.57846 13.1125 2.63213 13.1073 2.70749L12.3914 13.1388C12.3864 13.2117 12.3073 13.2548 12.2433 13.2194L6.12677 9.83657"/>'
        '<path d="M8.44336 11.0825L6.2832 13.2843C6.22048 13.3482 6.11182 13.3038 6.11182 13.2143V9.86772C6.11182 9.84165 6.122 9.8166 6.1402 9.79793L12.972 2.78748"/>'
        '</svg>',
        sanitize=False,
    )

class 账号菜单:
    '侧栏账号入口与本机权威退出登录'
    def __init__(自身,属性):
        '记下 props'
        自身.属性=属性
        自身.已打开=False
        自身.忙碌=False
        自身.退出失败=False
        自身.登录失败=False
        自身.头像=账号头像()
        自身.对话框=None
        if isinstance(属性,dict) and 't' in 属性:
            自身.渲染()#槽位只调用构造，键齐了就画

    def 更新(自身,属性):
        '刷新'
        自身.属性=属性

    def 关菜单(自身):
        '收起菜单'
        自身.已打开=False

    def 切菜单(自身):
        '开或关'
        自身.已打开=not 自身.已打开

    def 退出(自身):
        '退出已存凭证'
        自身.忙碌=True
        自身.退出失败=False
        try:
            自身.属性['signOut']()
            自身.已打开=False
        except Exception:
            自身.退出失败=True
            界面.label(自身.属性['t']('failed'))
        自身.忙碌=False

    def 开始登录(自身):
        '关菜单后发起；同步失败留在入口旁'
        自身.已打开=False
        自身.登录失败=False
        try:
            自身.属性['start']()
        except Exception:
            自身.登录失败=True
            界面.label(自身.属性['t']('failed'))

    def 选中(自身,标识):
        '菜单项'
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
        '入口、菜单项与可选登录弹窗'
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
            {'id':'settings','label':翻译('settings')},
            {'id':'contact','label':翻译('contactUs')},
        ]
        if 已登录:
            项.append({'id':'signout','label':翻译('signOut'),'disabled':自身.忙碌})
        else:
            项.append({'id':'signin','label':翻译('signIn')})
        if 账号.get('loginVisible') and not 账号.get('onboarding'):
            def 关弹窗():
                '关掉登录'
                自身.属性['showLogin'](False)
            def 改走密钥():
                '关掉登录并打开官方引导'
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
            自身.对话框.更新(面)
        入口文=标签 if 已登录 and 标签 is not None else 翻译('signedOut')
        with 界面.row().classes('账号菜单'):
            自身.头像.更新({'url':头像网址})
            自身.头像.渲染()
            界面.button(入口文, on_click=自身.切菜单).props('flat no-caps align=left').classes('账号触发')
            if 自身.已打开:
                with 界面.column().classes('账号菜单列'):
                    for 条 in 项:
                        def 点条(标识=条['id']):
                            '选中菜单项'
                            自身.选中(标识)
                        钮=界面.button(on_click=点条).props('flat no-caps align=left').classes('账号菜单项')
                        with 钮:
                            if 条['id']=='settings':
                                画字形(图标设置16())
                            elif 条['id']=='contact':
                                画纸飞机()
                            elif 条['id']=='signin':
                                画字形(图标用户16())
                            elif 条['id']=='signout':
                                登出图标()
                            界面.label(条['label'])
                        if 条.get('disabled'):
                            钮.disable()
                    界面.button(翻译('menu'), on_click=自身.关菜单).props('flat no-caps align=left').classes('账号菜单项')
            if 自身.退出失败 or 自身.登录失败:
                界面.label(翻译('failed'))
        if 自身.对话框 is not None and 账号.get('loginVisible') and not 账号.get('onboarding'):
            自身.对话框.渲染()

    def __call__(自身,属性=None):
        '对齐 React 调用'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()
