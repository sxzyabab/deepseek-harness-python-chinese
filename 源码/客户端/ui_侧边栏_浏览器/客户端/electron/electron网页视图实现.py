from ....模块.客户端.通告 import 取握手窗口
import threading
from ....存储 import 创建快照存储
from ....ui_侧边栏_右侧.客户端.标签域 import 中止信号
from ..浏览器.帧 import 空浏览器帧
from ..浏览器.浏览器持久化 import 当前浏览器目标
from ..浏览器.地址 import 解析浏览器地址

__all__=['electron网页视图实现']


def 等结果(产出):
    '调用已经给出值就直接用。给出期约就等到结算，拒绝则抛出'
    if 产出 is None or not hasattr(产出,'然后'):
        return 产出
    箱={'值':None,'错误':None}
    门=threading.Event()

    def 成功(值):
        '兑现后开门'
        箱['值']=值
        门.set()
        return 值

    def 失败(错误):
        '拒绝后开门'
        箱['错误']=错误
        门.set()

    产出.然后(成功,失败)
    门.wait()
    if 箱['错误'] is not None:
        错误=箱['错误']
        if isinstance(错误,BaseException):
            raise 错误
        raise RuntimeError(str(错误))
    return 箱['值']


def 合并中止(*信号表):
    '任一信号中止时，返回的信号也中止'
    合=中止信号()

    def 转发():
        '跟着中止'
        合.abort()

    for 信号 in 信号表:
        if 信号.aborted:
            合.abort()
            return 合
        信号.addEventListener('abort',转发,{'once':True})
    return 合


def 记录失败(说明,错误):
    '桌面浏览器操作失败写到控制台'
    取握手窗口().console.error(说明,错误)


class electron网页视图实现:
    '持有 Chromium 历史，并把 Electron 观察到的情况收成共同的帧状态'

    def __init__(自身,选项,桥,工作区,呈现):
        '记下检查点、桥和呈现，先发布空状态'
        自身.选项=选项
        自身.桥=桥
        自身.工作区=工作区
        自身.呈现=呈现
        自身.存储=创建快照存储(空浏览器帧())
        自身.寿命=中止信号()
        自身.宾客寿命=None
        自身.元素=None
        自身.租约=None
        自身.工作区键=None
        自身.正在初始化=False
        自身.就绪=False
        自身.待发=None
        自身.修订=0
        自身.首份文档=True
        自身.检查点=当前浏览器目标(选项.get('initial'))
        自身.已拆除=False
        自身.附着=None

    def getSnapshot(自身):
        '当前与载体无关的导航状态'
        return 自身.存储.getSnapshot()

    def subscribe(自身,监听):
        '状态变化时调用，返回退订'
        return 自身.存储.subscribe(监听)

    def 挂上(自身):
        '物理挂载可以重建丢失的宾客。普通隐藏不会走到这里'
        if 自身.寿命.aborted:
            return
        自身.附着=中止信号()
        if 自身.待发 is None:
            自身.待发=自身.存储.getSnapshot().get('target')
        if 自身.待发 is not None:
            当前=自身.存储.getSnapshot()
            自身.存储.set({
                **当前,
                'address':'requested',
                'loading':True,
                'canGoBack':False,
                'canGoForward':False,
                'error':None,
            })
            自身.初始化()

    def 脱离(自身):
        '容器被拿走之前先作废这次附着'
        if 自身.附着 is not None:
            自身.附着.abort()
        自身.附着=None
        自身.待发=自身.存储.getSnapshot().get('target')
        自身.丢宾客()

    def 加载地址(自身,目标):
        '加载校验过的地址，不换掉宾客。已观察到同一地址则刷新'
        if 自身.寿命.aborted:
            return
        当前=自身.存储.getSnapshot()
        if 自身.就绪 and 当前['address']=='observed' and 当前.get('target') is not None and 当前['target']['url']==目标['url']:
            自身.刷新()
            return
        自身.修订=自身.修订+1
        自身.待发=目标
        自身.存储.set({**当前,'target':目标,'address':'requested','loading':True,'error':None})
        自身.持久化(目标)
        if 自身.就绪:
            自身.装待发()
        else:
            自身.初始化()

    def 后退(自身):
        '沿 Chromium 历史后退'
        if 自身.存储.getSnapshot()['canGoBack']:
            自身.导航('goBack')

    def 前进(自身):
        '沿 Chromium 历史前进'
        if 自身.存储.getSnapshot()['canGoForward']:
            自身.导航('goForward')

    def 刷新(自身):
        '重载当前页。宾客还没建好或上次失败则重试创建'
        当前=自身.存储.getSnapshot()
        if 自身.寿命.aborted or 当前.get('target') is None:
            return
        if not 自身.就绪 or 当前.get('error') is not None:
            自身.修订=自身.修订+1
            自身.待发=当前['target']
            自身.存储.set({**当前,'loading':True,'error':None})
            if 自身.就绪:
                自身.装待发()
            else:
                自身.初始化()
            return
        自身.导航('reload')

    def 拆除(自身):
        '放开初始化中的宾客。再拆一次直接返回'
        if 自身.已拆除:
            return
        自身.已拆除=True
        自身.寿命.abort()
        自身.待发=None
        if not 自身.正在初始化:
            自身.丢宾客()
        自身.呈现.拆除()

    def 导航(自身,命令):
        '对已就绪的宾客执行后退、前进或刷新'
        if 自身.寿命.aborted or not 自身.就绪 or 自身.元素 is None:
            return
        自身.修订=自身.修订+1
        自身.待发=None
        当前=自身.存储.getSnapshot()
        自身.存储.set({**当前,'loading':True,'error':None})
        try:
            getattr(自身.元素,命令)()
        except Exception as 错误:
            自身.命令失败(错误)

    def 初始化(自身):
        '没有宾客时创建。创建结束后如果附着已经换过且还有待发，再来一次'
        附着=自身.附着
        if 附着 is None or 自身.正在初始化 or 自身.元素 is not None or 自身.寿命.aborted:
            return
        信号=合并中止(自身.寿命,附着)
        自身.正在初始化=True
        try:
            try:
                自身.创建宾客(信号)
            except Exception as 错误:
                自身.丢宾客()
                if not 信号.aborted:
                    自身.命令失败(错误)
        finally:
            自身.正在初始化=False
            if 自身.已拆除:
                自身.丢宾客()
            elif 自身.附着 is not 附着 and 自身.待发 is not None:
                自身.初始化()

    def 创建宾客(自身,附着信号):
        '向主进程要预约，装上导航监听，再把 webview 放进容器'
        if 自身.工作区键 is None:
            自身.工作区键=自身.工作区(附着信号)
        if 附着信号.aborted:
            return
        预约=等结果(自身.桥.acquire(自身.工作区键))
        if 附着信号.aborted:
            自身.释放(预约['lease'])
            return
        自身.租约=预约['lease']
        自身.宾客寿命=中止信号()
        信号=合并中止(附着信号,自身.宾客寿命)
        元素=自身.呈现.造元素(预约)
        自身.元素=元素

        def 请求打开(地址,帧=元素,寿命=信号):
            '还是这个宾客时才把打开请求交出去'
            自身.收到打开(帧,寿命,地址)

        退订打开=自身.桥.onOpenRequested(预约['lease'],请求打开)

        def 摘打开():
            '寿命结束就摘掉打开监听'
            退订打开()

        信号.addEventListener('abort',摘打开,{'once':True})

        def 文档就绪(事件):
            '宾客能导航之后装上待发地址'
            自身.就绪=True
            自身.观察(自身.存储.getSnapshot()['address']!='requested')
            自身.装待发()

        def 已导航(事件):
            '主框架导航提交后读地址'
            自身.观察(True)

        def 页内导航(事件):
            '主框架的页内跳转也读地址'
            if 自身.是主帧(事件):
                自身.观察(True)

        def 开始导航(事件):
            '主框架开始导航时标成加载中'
            if 自身.是主帧(事件):
                当前=自身.存储.getSnapshot()
                自身.存储.set({**当前,'loading':True,'error':None})

        def 开始加载(事件):
            '加载开始时刷新观察到的状态'
            自身.观察(False)

        def 停止加载(事件):
            '加载停止时刷新观察到的状态'
            自身.观察(False)

        def 标题更新(事件):
            '已经观察到地址时，标题更新也写回'
            自身.观察(自身.存储.getSnapshot()['address']=='observed')

        def 加载失败(事件):
            '主框架失败写上码和说明。取消加载的 -3 不算失败'
            if not 自身.是主帧(事件):
                return
            码=自身.取字段(事件,'errorCode')
            if 码==-3:
                return
            自身.失败({
                'code':码,
                'description':自身.取字段(事件,'errorDescription'),
            })

        def 宾客没了(事件):
            '渲染进程没了或元素被销毁'
            自身.丢宾客()
            自身.失败()

        自身.听到(元素,'dom-ready',文档就绪,信号)
        自身.听到(元素,'did-navigate',已导航,信号)
        自身.听到(元素,'did-navigate-in-page',页内导航,信号)
        自身.听到(元素,'did-start-navigation',开始导航,信号)
        自身.听到(元素,'did-start-loading',开始加载,信号)
        自身.听到(元素,'did-stop-loading',停止加载,信号)
        自身.听到(元素,'page-title-updated',标题更新,信号)
        自身.听到(元素,'did-fail-load',加载失败,信号)
        自身.听到(元素,'render-process-gone',宾客没了,信号)
        自身.听到(元素,'destroyed',宾客没了,信号)
        自身.呈现.呈现(元素)

    def 收到打开(自身,元素,信号,地址):
        '还是这个宾客、也没中止时，把打开请求交出去'
        if 自身.元素 is 元素 and not 信号.aborted:
            自身.选项['openRequested'](地址)

    def 听到(自身,元素,名称,回调,信号):
        '登记监听，信号中止时摘掉'
        元素.addEventListener(名称,回调)

        def 摘掉():
            '中止后不再收这个事件'
            元素.removeEventListener(名称,回调)

        信号.addEventListener('abort',摘掉,{'once':True})

    def 是主帧(自身,事件):
        '只处理主框架事件'
        return 自身.取字段(事件,'isMainFrame') is True

    def 取字段(自身,事件,名称):
        '事件可能是对象，也可能是字典'
        if isinstance(事件,dict):
            return 事件.get(名称)
        return getattr(事件,名称,None)

    def 装待发(自身):
        '宾客就绪后加载待发地址。被取消或换代的失败丢掉'
        目标=自身.待发
        元素=自身.元素
        if not 自身.就绪 or 目标 is None or 元素 is None:
            return
        修订=自身.修订
        自身.待发=None
        try:
            等结果(元素.loadURL(目标['url']))
        except Exception as 错误:
            if 自身.元素 is not 元素 or 自身.寿命.aborted or 自身.修订!=修订:
                return
            if 自身.取字段(错误,'code')=='ERR_ABORTED':
                return
            if 自身.存储.getSnapshot().get('error') is None:
                自身.命令失败(错误)

    def 观察(自身,已提交):
        '读宾客现在的地址、标题和历史按钮'
        if not 自身.就绪 or 自身.元素 is None or 自身.寿命.aborted:
            return
        try:
            自身.观察就绪(自身.元素,已提交)
        except Exception as 错误:
            自身.命令失败(错误)

    def 观察就绪(自身,元素,已提交):
        '把读到的地址收成已观察状态。引导文档清掉历史'
        当前=自身.存储.getSnapshot()
        解析=None
        if 已提交:
            解析=解析浏览器地址(元素.getURL())
        if 解析 is not None and 解析['ok'] and 自身.首份文档:
            元素.clearHistory()
            自身.首份文档=False
        目标=当前.get('target')
        地址=当前['address']
        if 解析 is not None and 解析['ok']:
            标题=元素.getTitle()
            if 标题 is None or 标题=='':
                标题=解析['target']['title']
            目标={**解析['target'],'title':标题}
            地址='observed'
            自身.呈现.展示(目标['title'])
        加载中=当前.get('error') is None and 元素.isLoading()
        能退=元素.canGoBack()
        能进=元素.canGoForward()
        旧目标=当前.get('target')
        旧址=None if 旧目标 is None else 旧目标.get('url')
        新址=None if 目标 is None else 目标.get('url')
        旧题=None if 旧目标 is None else 旧目标.get('title')
        新题=None if 目标 is None else 目标.get('title')
        if 新址!=旧址 or 新题!=旧题 or 地址!=当前['address'] or 加载中!=当前['loading'] or 能退!=当前['canGoBack'] or 能进!=当前['canGoForward']:
            自身.存储.set({
                **当前,
                'target':目标,
                'address':地址,
                'loading':加载中,
                'canGoBack':能退,
                'canGoForward':能进,
            })
        if 解析 is not None and 解析['ok'] and 目标 is not None:
            自身.持久化(目标)

    def 持久化(自身,目标):
        '地址和标题都没变就不写。只存这一条地址检查点'
        if 自身.检查点 is not None and 目标['url']==自身.检查点.get('url') and 目标['title']==自身.检查点.get('title'):
            return
        自身.检查点=目标
        自身.选项['persist']({
            'entries':[目标],
            'index':0,
            'request':{'target':目标,'revision':自身.修订},
            'navigation':{'status':'known','revision':自身.修订},
            'failure':None,
        })

    def 失败(自身,错误=None):
        '停下加载并留下失败。还能用的历史按钮保留'
        if 自身.寿命.aborted:
            return
        if 错误 is None:
            错误={'code':None,'description':None}
        当前=自身.存储.getSnapshot()
        自身.存储.set({
            **当前,
            'loading':False,
            'error':错误,
            'canGoBack':自身.就绪 and 当前['canGoBack'],
            'canGoForward':自身.就绪 and 当前['canGoForward'],
        })

    def 命令失败(自身,错误):
        '操作失败写日志，并发布不带诊断的加载失败'
        记录失败('Desktop browser operation failed',错误)
        自身.失败()

    def 丢宾客(自身):
        '拆掉宾客节点并释放租约'
        if 自身.宾客寿命 is not None:
            自身.宾客寿命.abort()
        自身.宾客寿命=None
        自身.呈现.清空()
        自身.元素=None
        自身.就绪=False
        自身.首份文档=True
        租约=自身.租约
        自身.租约=None
        if 租约 is not None:
            自身.释放(租约)

    def 释放(自身,租约):
        '释放失败只记日志'
        try:
            等结果(自身.桥.release(租约))
        except Exception as 错误:
            记录失败('Desktop browser guest release failed',错误)
