'账号余额用尽时接管全帧额度通知'
from ...模块.客户端.通告 import 取握手窗口
from ...ui_对话.异常 import 挂上
from ...ui_基础界面组件 import 按钮,模态,吐司
from ...ui_基础界面组件.icons import 图标警告16
from .文案 import 中文

__all__=['账号配额须知']

def 读选择(钩,选择):
    '用钩子选出一截'
    if 钩 is None:
        return None
    return 钩(选择)

class 账号配额须知:
    '已登录且有原生页时出充值对话框。否则用原来的提示'
    def __init__(自身,属性):
        '记下通知和平台页通道'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.根=None
        自身.已打开=False
        自身.先前已登录=None
        自身.放开占住=None
        自身.放开页面=None
        自身.已订=False
        自身.退订=[]
        自身.绘制中=False
        自身.待重画=False
        自身.渲染()

    def 更新(自身,属性):
        '换成新的 props'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 渲染(自身):
        '绘制中再来一次只记一笔'
        if 自身.绘制中:
            自身.待重画=True
            return 自身.根
        自身.绘制中=True
        try:
            自身.画出()
        finally:
            自身.绘制中=False
        if 自身.待重画:
            自身.待重画=False
            return 自身.渲染()
        return 自身.根

    def 放开(自身):
        '同时放下页面请求和通知占住'
        if 自身.放开页面 is not None:
            自身.放开页面()
            自身.放开页面=None
        if 自身.放开占住 is not None:
            自身.放开占住()
            自身.放开占住=None

    def 画出(自身):
        '等第一份账号状态。退出登录就关掉'
        属性=自身.属性
        窗口=属性['window'] if 'window' in 属性 else 取握手窗口()
        文档=窗口.document
        if 自身.根 is None:
            自身.根=文档.createElement('div')
            自身.根.style.display='contents'
        while 自身.根.firstElementChild is not None:
            自身.根.firstElementChild.remove()
        匹配=属性.get('matched') if isinstance(属性.get('matched'),dict) else {}
        def 取状态(快照):
            '登录状态'
            视图=快照.get('view') if isinstance(快照,dict) else None
            if isinstance(视图,dict):
                return 视图.get('status')
            return None
        def 取失败(快照):
            '状态流是否失败'
            return 快照.get('failed') is True if isinstance(快照,dict) else False
        def 取页(快照):
            '当前平台页'
            return 快照
        状态=读选择(属性.get('useAccount'),取状态)
        失败=读选择(属性.get('useAccount'),取失败)
        已登录=状态=='credential-stored'
        页=读选择(属性.get('usePlatformPage'),取页)
        if 自身.先前已登录 and 已登录 is not True:
            自身.放开()
            关=匹配.get('dismiss')
            if 关 is not None:
                关()
        自身.先前已登录=已登录
        打开页=属性.get('openPlatformPage')
        if 状态 is None and 失败 is not True and 打开页 is not None:
            自身.订上()
            return
        if 已登录 is not True or 打开页 is None:
            图标=图标警告16({'window':窗口,'size':18})
            挂上(自身.根,吐司({
                'window':窗口,
                'text':匹配.get('message') or '',
                'icon':图标,
                'onDone':匹配.get('dismiss'),
            }))
            自身.订上()
            return
        if 自身.已打开 or 页 is not None:
            自身.订上()
            return
        def 去充值():
            '先占住通知，再打开充值页。返回后关闭通知'
            占住=匹配.get('keepOpen')
            if 占住 is not None:
                自身.放开占住=占住()
            def 返回(_原因=None):
                '充值页结束'
                自身.放开页面=None
                关=匹配.get('dismiss')
                if 关 is not None:
                    关()
            自身.放开页面=打开页('top-up',返回)
            自身.已打开=True
            自身.渲染()
        取消=按钮({
            'window':窗口,
            'variant':'outline',
            'onClick':匹配.get('dismiss'),
            'children':中文['cancel'],
        })
        充值=按钮({
            'window':窗口,
            'variant':'primary',
            'onClick':去充值,
            'children':中文['quotaTopUp'],
        })
        框=模态({
            'window':窗口,
            'open':True,
            'title':中文['quotaTitle'],
            'closeLabel':中文['close'],
            'description':中文['quotaDescription'],
            'onClose':匹配.get('dismiss'),
            'footer':[取消,充值],
        })
        挂上(自身.根,框)
        自身.订上()

    def 订上(自身):
        '账号和平台页变化时重画'
        if 自身.已订:
            return
        def 变更():
            '绘制中只记一笔'
            if 自身.绘制中:
                自身.待重画=True
                return
            自身.渲染()
        for 名 in ('useAccount','usePlatformPage'):
            钩=自身.属性.get(名)
            订=getattr(钩,'_subscribe',None) if 钩 is not None else None
            if callable(订):
                自身.退订.append(订(变更))
        自身.已订=True

    def 拆除(自身):
        '卸下时不能留下占住或原生页'
        自身.放开()
        for 退 in 自身.退订:
            退()
        自身.退订=[]
        自身.已订=False
