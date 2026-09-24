from decimal import Decimal
from .格式化余额 import 格式化余额
from .授权网址 import 带主题的授权网址
from .账号头像 import 账号头像
from .平台覆盖层 import 平台覆盖层

__all__=['账号分区']

活动阶段=('initializing','waiting-browser','exchanging','committing')

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

class 账号分区:
    """设置里的账号与余额分区。"""
    def __init__(自身,属性):
        """记下 props 并拉一次资料。"""
        自身.属性=属性
        自身.平台页=None
        自身.覆盖层=None
        自身.头像=账号头像()
        自身.失败=False
        自身.忙碌=False
        刷新=属性.get('refresh')
        if 刷新 is not None:
            刷新()

    def 更新(自身,属性):
        """刷新。"""
        自身.属性=属性

    def 执行(自身,动作):
        """串行跑一项。"""
        自身.忙碌=True
        自身.失败=False
        try:
            动作()
        except Exception:
            自身.失败=True
        自身.忙碌=False

    def 关平台(自身):
        """拆原生视口。"""
        if 自身.覆盖层 is not None:
            自身.覆盖层.拆除()
            自身.覆盖层=None
        自身.平台页=None

    def 开平台(自身,页):
        """Desktop 才改走原生页。"""
        自身.平台页=页

    def 渲染(自身):
        """未登录居中提示，已登录展示资料与余额。"""
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
                """发起登录。"""
                自身.执行(自身.属性['start'])
            return {
                'type':'account-section',
                'mode':'signed-out',
                'cssModule':'账号分区.module.css',
                'nav':翻译('nav'),
                'title':翻译('settingsSignedOutTitle'),
                'description':翻译('failed') if 自身.失败 or 流失败 else 翻译('settingsSignedOutDescription'),
                'signInLabel':翻译('signIn'),
                'disabled':自身.忙碌 or 视图 is None,
                'onSignIn':点登录,
            }
        平台=自身.属性.get('platform')
        覆盖=None
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
            覆盖=自身.覆盖层(面)
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
            """Desktop 走原生用量页。"""
            if 平台 is not None and 已登录:
                自身.开平台('usage')
        def 点充值():
            """Desktop 走原生充值页。"""
            if 平台 is not None and 已登录:
                自身.开平台('top-up')
        def 点取消():
            """取消进行中的登录。"""
            def 取消():
                """交给注入面。"""
                自身.属性['cancel'](尝试['id'])
            自身.执行(取消)
        return {
            'type':'account-section',
            'mode':'signed-in',
            'cssModule':'账号分区.module.css',
            'nav':翻译('nav'),
            'overlay':覆盖,
            'avatar':自身.头像({'url':头像网址}),
            'name':名称,
            'status':状态文,
            'accountInfo':翻译('accountInfo') if 已登录 else None,
            'accountInfoUrl':'https://platform.deepseek.com',
            'active':活动,
            'openLabel':翻译('open'),
            'authorizeUrl':None if 授权 is None else 带主题的授权网址(授权,配色),
            'cancelLabel':翻译('cancel'),
            'cancelDisabled':自身.忙碌 or (尝试 is not None and 尝试.get('phase')=='committing'),
            'onCancel':点取消 if 活动 else None,
            'balanceLabel':翻译('balance'),
            'amounts':金额,
            'balanceUnavailable':余额文,
            'bonusLabel':翻译('bonusBalance') if len(赠金)>0 else None,
            'bonusAmounts':赠金,
            'moreLabel':翻译('more'),
            'usageLabel':翻译('usage'),
            'topUpLabel':翻译('topUp'),
            'usageUrl':None if 视图 is None else 视图.get('links',{}).get('usageUrl'),
            'topUpUrl':None if 视图 is None else 视图.get('links',{}).get('topUpUrl'),
            'onUsage':点用量,
            'onTopUp':点充值,
        }

    def __call__(自身,属性=None):
        """对齐 React 调用。"""
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()
