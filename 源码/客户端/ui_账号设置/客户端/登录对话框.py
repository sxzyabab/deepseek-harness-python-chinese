import threading
from .授权网址 import 带主题的授权网址

__all__=['登录对话框']

活动阶段=('initializing','waiting-browser','exchanging','committing')

class 登录对话框:
    """账号授权弹窗；出错后可取消进行中的尝试再重试。"""
    def __init__(自身,属性):
        """记下 props。"""
        自身.属性=属性
        自身.忙碌=False
        自身.失败=False
        自身.复制结果=None
        自身.复制计时=None
        自身.上次尝试=None

    def 更新(自身,属性):
        """刷新；授权链接变了则清复制结果。"""
        自身.属性=属性
        尝试=自身.取尝试()
        键=None if 尝试 is None else (尝试.get('id'),尝试.get('authorizeUrl'))
        if 键!=自身.上次尝试:
            自身.上次尝试=键
            自身.清复制结果()

    def 取尝试(自身):
        """当前登录尝试。"""
        视图=自身.属性['account'].get('view')
        if 视图 is None:
            return None
        return 视图.get('attempt')

    def 清复制结果(自身):
        """停计时并清文案。"""
        if 自身.复制计时 is not None:
            自身.复制计时.cancel()
            自身.复制计时=None
        自身.复制结果=None

    def 排复制恢复(自身):
        """两秒后恢复复制按钮原文。"""
        if 自身.复制计时 is not None:
            自身.复制计时.cancel()
        def 到期():
            """清结果。"""
            自身.复制结果=None
            自身.复制计时=None
        自身.复制计时=threading.Timer(2,到期)
        自身.复制计时.daemon=True
        自身.复制计时.start()

    def 执行(自身,动作):
        """串行跑一项并记下失败。"""
        自身.忙碌=True
        自身.失败=False
        try:
            动作()
        except Exception:
            自身.失败=True
        自身.忙碌=False

    def 关闭(自身):
        """提交中不可关；进行中则先取消。"""
        尝试=自身.取尝试()
        阶段=None if 尝试 is None else 尝试.get('phase')
        活动=自身.忙碌 or 阶段 in 活动阶段
        if 阶段=='committing' or 自身.忙碌:
            return
        if 活动 and 尝试 is not None:
            def 取消后关():
                """取消当前尝试再关。"""
                自身.属性['cancel'](尝试['id'])
                自身.属性['close']()
            自身.执行(取消后关)
        else:
            自身.属性['close']()

    def 重试(自身):
        """有活动尝试则先取消再发起。"""
        尝试=自身.取尝试()
        阶段=None if 尝试 is None else 尝试.get('phase')
        if 自身.忙碌 or 阶段 in 活动阶段:
            if 尝试 is not None:
                自身.属性['cancel'](尝试['id'])
        自身.属性['start']()

    def 复制链接(自身,授权网址):
        """把带主题的授权链接写入剪贴板。"""
        导航=globals().get('navigator')
        剪贴板=None if 导航 is None else getattr(导航,'clipboard',None)
        try:
            剪贴板.writeText(带主题的授权网址(授权网址,自身.属性['colorScheme']))
            自身.复制结果='copiedLink'
        except Exception:
            自身.复制结果='copyFailed'
        自身.排复制恢复()

    def 渲染(自身):
        """结构化弹窗。"""
        翻译=自身.属性['t']
        账号=自身.属性['account']
        视图=账号.get('view')
        if 视图 is not None and 视图.get('status')=='credential-stored':
            自身.属性['close']()
            return None
        尝试=自身.取尝试()
        阶段=None if 尝试 is None else 尝试.get('phase')
        授权网址=None if 尝试 is None else 尝试.get('authorizeUrl')
        活动=自身.忙碌 or 阶段 in 活动阶段
        过期=阶段=='expired'
        出错=自身.失败 or 账号.get('loginFailed') or 账号.get('failed') or 阶段=='failed'
        等待=活动 and not 出错
        提交中=阶段=='committing'
        if 出错:
            标题=翻译('failureTitle')
        elif 活动:
            标题=翻译('browserTitle')
        elif 过期:
            标题=翻译('timeoutTitle')
        else:
            标题=翻译('loginTitle')
        if 等待:
            说明键=None
            复制键='copyLink' if 自身.复制结果 is None else 自身.复制结果
        elif 出错:
            说明键='failed'
            复制键=None
        elif 过期:
            说明键='timeoutDescription'
            复制键=None
        else:
            说明键='loginDescription'
            复制键=None
        def 点复制():
            """复制授权链接。"""
            if 授权网址:
                自身.复制链接(授权网址)
        def 点主按钮():
            """重试或登录。"""
            自身.执行(自身.重试)
        主文案=翻译('waiting') if 等待 else 翻译('retry' if 过期 or 出错 else 'signIn')
        return {
            'type':'sign-in-dialog',
            'cssModule':'登录对话框.module.css',
            'title':标题,
            'waiting':等待,
            'error':出错,
            'expired':过期,
            'active':活动,
            'committing':提交中,
            'busy':自身.忙碌,
            'authorizeUrl':授权网址,
            'copyKey':复制键,
            'descriptionKey':说明键,
            'browserPrompt':翻译('browserPrompt') if 等待 else None,
            'browserDescription':翻译('browserDescription') if 等待 else None,
            'description':None if 等待 or 说明键 is None else 翻译(说明键),
            'closeLabel':翻译('close'),
            'secondaryLabel':翻译('cancel' if 活动 else 'addApiKey'),
            'primaryLabel':主文案,
            'viewReady':视图 is not None,
            'onClose':自身.关闭,
            'onCopy':点复制,
            'onSecondary':自身.关闭 if 活动 else 自身.属性['useApiKey'],
            'onPrimary':点主按钮,
            't':翻译,
        }

    def __call__(自身,属性=None):
        """对齐 React 调用。"""
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()
