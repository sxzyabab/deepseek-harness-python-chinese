from decimal import Decimal
from nicegui import ui as 界面
from .格式化余额 import 格式化余额
from .授权网址 import 带主题的授权网址
from .账号头像 import 账号头像
from .平台覆盖层 import 平台覆盖层

__all__=['账号分区','样式表']

样式表='''
.账号区{display:flex;flex-direction:column;gap:16px;width:100%;padding:8px 0;font-size:13px;line-height:22px;color:var(--dsw-alias-label-primary)}
.账号卡,.账号余额卡{padding:12px 16px;border:0.5px solid var(--dsw-alias-settings-card-stroke);border-radius:var(--dsw-radius-xl);background:var(--dsw-alias-settings-card-fill)}
.账号卡{display:flex;align-items:center;justify-content:space-between;gap:16px;width:100%;flex-wrap:nowrap}
.账号身份{display:flex;align-items:center;gap:10px;min-height:44px;min-width:0}
.账号头像{flex:none;display:flex;align-items:center;justify-content:center;width:32px;height:32px;border-radius:50%;color:var(--dsw-alias-label-tertiary);background:var(--dsw-alias-bg-skeleton);object-fit:cover}
.账号文{display:flex;flex-direction:column;min-width:0}
.账号名{font-size:14px;font-weight:500;line-height:22px}
.账号态{color:var(--dsw-alias-label-tertiary);font-size:13px;line-height:22px}
.账号余额卡{display:flex;flex-direction:column;gap:8px;width:100%}
.账号行{display:flex;align-items:center;justify-content:space-between;gap:16px;width:100%;min-height:40px;padding:6px 0;box-sizing:border-box;flex-wrap:nowrap}
.账号行+.账号行{border-top:0.5px solid var(--dsw-alias-border-l2)}
.账号金额{font-size:18px;line-height:28px;font-weight:510}
.账号链{color:var(--dsw-alias-label-primary);font-size:13px;line-height:22px;text-decoration:none}
.账号动作{display:flex;justify-content:flex-end;align-items:center;gap:10px;flex-wrap:wrap}
button.q-btn.账号钮{height:36px;min-height:36px;min-width:58px;padding:0 14px;border:0.5px solid var(--dsw-alias-border-l3) !important;border-radius:var(--dsw-radius-md);background:transparent !important;color:var(--dsw-alias-label-primary) !important;box-shadow:none !important;font-size:14px;line-height:22px}
button.q-btn.账号钮:hover{background:var(--dsw-alias-interactive-bg-hover) !important}
button.q-btn.账号主钮{min-width:72px;font-weight:500;color:var(--dsw-alias-label-primary-foreground) !important;background:var(--dsw-alias-button-primary-fill) !important;border-color:transparent !important}
button.q-btn.账号主钮:hover{background:var(--dsw-alias-button-primary-hover) !important}
.账号未登录{display:flex;flex-direction:column;align-items:center;justify-content:center;width:100%;min-height:calc(100% + 16px);margin-bottom:-16px;padding-bottom:8px;box-sizing:border-box;color:var(--dsw-alias-label-primary)}
.账号未登录内容{display:flex;flex-direction:column;align-items:center;justify-content:center;width:100%;min-height:60px;padding:12px 0;gap:20px}
.账号未登录文{display:flex;flex-direction:column;gap:4px;width:100%;align-items:center}
.账号未登录题{font-size:14px;line-height:22px;text-align:center}
.账号未登录述{color:var(--dsw-alias-label-tertiary);font-size:12px;line-height:18px;text-align:center}
'''
界面.add_css(样式表,shared=True)

活动阶段=('initializing','waiting-browser','exchanging','committing')

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

class 账号分区:
    '设置里的账号与余额分区'
    def __init__(自身,属性):
        '记下 props 并拉一次资料'
        自身.属性=属性
        自身.平台页=None
        自身.覆盖层=None
        自身.头像=账号头像()
        自身.失败=False
        自身.忙碌=False
        刷新=属性.get('refresh')
        if 刷新 is not None:
            刷新()
        if isinstance(属性,dict) and 't' in 属性:
            自身.渲染()#槽位只调用构造，键齐了就画

    def 更新(自身,属性):
        '刷新'
        自身.属性=属性

    def 执行(自身,动作):
        '串行跑一项'
        自身.忙碌=True
        自身.失败=False
        try:
            动作()
        except Exception:
            自身.失败=True
            界面.label(自身.属性['t']('failed'))
        自身.忙碌=False

    def 关平台(自身):
        '拆原生视口；关闭失败时在页面上留下失败'
        if 自身.覆盖层 is not None:
            try:
                自身.覆盖层.拆除()
            except Exception:
                自身.失败=True
                if 't' in 自身.属性:
                    界面.label(自身.属性['t']('failed'))
            自身.覆盖层=None
        自身.平台页=None

    def 开平台(自身,页):
        'Desktop 才改走原生页'
        自身.平台页=页

    def 渲染(自身):
        '未登录居中提示，已登录展示资料与余额'
        翻译=自身.属性['t']
        账号=读账号(自身.属性)
        主题=读主题(自身.属性)
        配色=主题.get('active',{}).get('colorScheme','light')
        视图=账号.get('view')
        细节=账号.get('details')
        流失败=bool(账号.get('failed'))
        资料=None
        钱包=None
        赠金钱包=[]
        if 细节 is not None:
            资料项=细节.get('profile')
            if 资料项 is not None and 资料项.get('status')=='ready':
                资料=资料项.get('value')
            余额项=细节.get('balance')
            if 余额项 is not None and 余额项.get('status')=='ready':
                钱包=余额项.get('value')
                for 项 in 余额项.get('bonusWallets') or []:
                    if Decimal(项['balance'])>0:
                        赠金钱包.append(项)
        尝试=None if 视图 is None else 视图.get('attempt')
        活动=尝试 is not None and 尝试.get('phase') in 活动阶段
        已登录=视图 is not None and 视图.get('status')=='credential-stored'
        if not 已登录:
            自身.关平台()
        if 自身.失败 or 流失败 or (尝试 is not None and 尝试.get('phase')=='failed'):
            状态文=翻译('failed')
        elif 尝试 is not None and 尝试.get('phase')=='expired':
            状态文=翻译('expired')
        elif 活动:
            阶段=尝试['phase']
            if 阶段=='initializing':
                状态文=翻译('initializing')
            elif 阶段=='waiting-browser':
                状态文=翻译('waiting')
            else:
                状态文=翻译('completing')
        elif 已登录:
            if 资料 is not None and 资料.get('contact'):
                状态文=资料['contact']
            elif 细节 is None or 细节.get('profile') is None:
                状态文=翻译('loading')
            else:
                状态文=翻译('profileUnavailable')
        else:
            状态文=翻译('signInDescription')
        if not 已登录 and not 活动:
            def 点登录():
                '发起登录'
                自身.执行(自身.属性['start'])
            with 界面.column().classes('账号未登录'):
                with 界面.column().classes('账号未登录内容'):
                    with 界面.column().classes('账号未登录文'):
                        界面.label(翻译('settingsSignedOutTitle')).classes('账号未登录题')
                        界面.label(翻译('failed') if 自身.失败 or 流失败 else 翻译('settingsSignedOutDescription')).classes('账号未登录述')
                    钮=界面.button(翻译('signIn'), on_click=点登录).props('flat no-caps').classes('账号钮 账号主钮')
                    if 自身.忙碌 or 视图 is None:
                        钮.disable()
            return
        平台=自身.属性.get('platform')
        面=None
        if 自身.平台页 is not None and 平台 is not None and 已登录:
            面={
                'bridge':平台,
                'page':自身.平台页,
                'backLabel':翻译('backToHarness'),
                'loadingLabel':翻译('loading'),
                'failureLabel':翻译('platformFailed'),
                'retryLabel':翻译('platformRetry'),
                'onClose':自身.关平台,
            }
            if 自身.覆盖层 is None:
                自身.覆盖层=平台覆盖层(面)
        头像网址=None if not 已登录 or 资料 is None else 资料.get('avatarUrl')
        名称=翻译('signedOut')
        if 已登录:
            名称=翻译('signedIn') if 资料 is None or 资料.get('name') is None else 资料['name']
        金额=[]
        if 已登录 and 钱包 is not None and len(钱包)>0:
            for 项 in 钱包:
                符号='¥' if 项.get('currency')=='CNY' else '$'
                金额.append(格式化余额(项['balance'],符号))
        if 已登录 and 钱包 is None:
            if 细节 is None or 细节.get('balance') is None:
                余额文=翻译('loading')
            else:
                余额文=翻译('balanceUnavailable')
        elif not 已登录:
            余额文=翻译('balanceSignedOut')
        else:
            余额文=None
        赠金=[]
        for 项 in 赠金钱包:
            符号='¥' if 项.get('currency')=='CNY' else '$'
            赠金.append(格式化余额(项['balance'],符号))
        授权=None if 尝试 is None else 尝试.get('authorizeUrl')
        def 点用量():
            'Desktop 走原生用量页'
            if 平台 is not None and 已登录:
                自身.开平台('usage')
        def 点充值():
            'Desktop 走原生充值页'
            if 平台 is not None and 已登录:
                自身.开平台('top-up')
        def 点取消():
            '取消进行中的登录'
            def 取消():
                '交给注入面'
                自身.属性['cancel'](尝试['id'])
            自身.执行(取消)
        if 自身.覆盖层 is not None and 面 is not None:
            自身.覆盖层.更新(面)
            自身.覆盖层.渲染()
        with 界面.column().classes('账号区'):
            with 界面.row().classes('账号卡'):
                with 界面.row().classes('账号身份'):
                    自身.头像.更新({'url':头像网址})
                    自身.头像.渲染()
                    with 界面.column().classes('账号文'):
                        界面.label(名称).classes('账号名')
                        界面.label(状态文).classes('账号态')
                if 已登录:
                    界面.link(翻译('accountInfo'), 'https://platform.deepseek.com', new_tab=True).classes('账号链')
            if 活动:
                授权址=None if 授权 is None else 带主题的授权网址(授权,配色)
                with 界面.row().classes('账号动作'):
                    if isinstance(授权址,str) and 授权址!='':
                        界面.link(翻译('open'), 授权址, new_tab=True).classes('账号链')
                    取消钮=界面.button(翻译('cancel'), on_click=点取消).props('flat no-caps').classes('账号钮')
                    if 自身.忙碌 or (尝试 is not None and 尝试.get('phase')=='committing'):
                        取消钮.disable()
            with 界面.column().classes('账号余额卡'):
                with 界面.row().classes('账号行'):
                    界面.label(翻译('balance')).classes('账号态')
                    if 余额文 is not None:
                        界面.label(余额文).classes('账号态')
                    elif len(金额)>0:
                        界面.label(' + '.join(金额)).classes('账号金额')
                if len(赠金)>0:
                    with 界面.row().classes('账号行'):
                        界面.label(翻译('bonusBalance')).classes('账号态')
                        界面.label(' + '.join(赠金)).classes('账号金额')
                with 界面.row().classes('账号动作'):
                    界面.button(翻译('usage'), on_click=点用量).props('flat no-caps').classes('账号钮')
                    界面.button(翻译('topUp'), on_click=点充值).props('flat no-caps').classes('账号钮 账号主钮')

    def __call__(自身,属性=None):
        '对齐 React 调用'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()
