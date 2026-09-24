import os,threading
from urllib.parse import urlparse
from .文案 import 命名空间,中文,英文
from .联系网址 import 联系网址
from ..联系配置 import 解析联系配置,联系配置全局键
from .账号引导 import 账号引导
from .账号菜单 import 账号菜单
from .账号分区 import 账号分区

__all__=['依赖','应用','命名空间','中文','英文']

依赖=['slots','locale','remote','remote.account','theme']

def 应用(上下文):
    """仅在 Desktop 渲染器登记账号界面，并订阅可重连的账号状态流。"""
    if 'dshDesktop' not in globals():
        return
    def 登记词典():
        """登记账号词典。"""
        return 上下文.locale.register(命名空间,{'en':英文,'zh':中文})
    上下文.副作用(登记词典,'account: dictionaries')
    翻译=上下文.locale.bind(命名空间)
    页面=globals()
    配置=解析联系配置(页面[联系配置全局键] if 联系配置全局键 in 页面 else {})
    快照={'view':None,'details':None,'failed':False,'loginVisible':False}
    监听者=set()
    def 发布(值):
        """替换快照并通知。"""
        nonlocal 快照
        快照=值
        for 监听 in list(监听者):
            监听()
    修订=0
    刷新中=None
    def 刷新():
        """凭证已存时并行拉取资料与余额。"""
        nonlocal 刷新中
        视图=快照['view']
        if 视图 is None or 视图.get('status')!='credential-stored':
            return
        if 刷新中 is not None:
            return 刷新中
        代=修订
        def 读字段(字段名,查询):
            """写入 details 的一栏。"""
            try:
                值=查询()
            except Exception:
                值={'status':'failed'}
            if 值 is None:
                return
            if 代!=修订:
                return
            细节={} if 快照['details'] is None else dict(快照['details'])
            细节[字段名]=值
            发布({**快照,'details':细节})
        def 跑():
            """顺序拉取资料与余额。"""
            def 资料():
                """读 profile。"""
                结果=上下文.remote.account.getProfile().等待()
                if not 结果['ok']:
                    raise RuntimeError('account profile failed')
                return 结果['value']
            def 余额():
                """读 balance。"""
                结果=上下文.remote.account.getBalance().等待()
                if not 结果['ok']:
                    raise RuntimeError('account balance failed')
                return 结果['value']
            读字段('profile',资料)
            读字段('balance',余额)
        刷新中=跑
        try:
            跑()
        finally:
            if 刷新中 is 跑:
                刷新中=None
        return 刷新中
    def 拆修订():
        """卸载时作废在途 details。"""
        def 拆():
            """抬修订。"""
            nonlocal 修订
            修订+=1
        return 拆
    上下文.副作用(拆修订,'account: details request lifetime')
    def 开账号流(信号):
        """打开账号状态流。"""
        return 上下文.remote.account.watch(信号)
    def 账号流结束():
        """流意外结束。"""
        return RuntimeError('account stream ended')
    流=上下文.remote.$stream({
        'name':'account',
        'open':开账号流,
        'ended':账号流结束,
    })
    已拆除=False
    def 拆流():
        """拆除状态流。"""
        def 拆():
            """标记并 dispose。"""
            nonlocal 已拆除
            已拆除=True
            return 流.dispose()
        return 拆
    上下文.副作用(拆流,'account: state stream')
    def 消费流():
        """把流帧写进快照。"""
        try:
            for 帧 in 流:
                nonlocal 修订,刷新中
                修订+=1
                刷新中=None
                发布({**快照,'view':帧['value'] if isinstance(帧,dict) else 帧.value,'details':None,'failed':False})
                if isinstance(帧,dict):
                    帧['accept']()
                else:
                    帧.accept()
                刷新()
        except Exception:
            if not 已拆除:
                发布({**快照,'failed':True})
    threading.Thread(target=消费流,daemon=True).start()
    原生平台=globals().get('dshPlatform')
    def 意见反馈():
        """系统浏览器打开问卷。"""
        语言快照=上下文.locale.getSnapshot()
        语言='zh-CN' if 语言快照['active']=='zh' else 'en'
        窗口=globals()['window']
        网址=联系网址(配置,{
            'version':os.environ.get('DSH_CLIENT_VERSION'),
            'locale':语言,
            'width':窗口.screen.width,
            'height':窗口.screen.height,
            'pixelRatio':窗口.devicePixelRatio,
        })
        窗口.open(网址,'_blank','noopener,noreferrer')
    def 显示登录(可见):
        """切换登录弹窗。"""
        发布({**快照,'loginVisible':可见})
    def 设引导(进行中):
        """切换引导标记。"""
        发布({**快照,'onboarding':进行中})
    def 开始登录():
        """发起 Desktop 登录。"""
        发布({**快照,'loginVisible':True,'loginFailed':False})
        传输=globals().get('__DSH_TRANSPORT__')
        窗口=globals()['window']
        源=窗口.location.origin
        if isinstance(传输,dict) and 传输.get('streamBaseUrl') is not None:
            解析=urlparse(传输['streamBaseUrl'])
            源=解析.scheme+'://'+解析.netloc
        try:
            结果=上下文.remote.account.startSignIn(上下文.locale.getSnapshot()['active'],源,'desktop').等待()
            if not 结果['ok']:
                raise RuntimeError('account start failed')
        except Exception as 错误:
            发布({**快照,'loginFailed':True})
            raise 错误
    def 取消登录(标识):
        """取消进行中的登录。"""
        结果=上下文.remote.account.cancelSignIn(标识).等待()
        if not 结果['ok']:
            raise RuntimeError('account cancel failed')
    def 退出登录():
        """退出已存凭证。"""
        结果=上下文.remote.account.signOut().等待()
        if not 结果['ok']:
            raise RuntimeError('account sign-out failed')
    def 读账号快照():
        """当前账号快照。"""
        return 快照
    def 订账号(监听):
        """订阅账号快照。"""
        监听者.add(监听)
        def 退订():
            """取消订阅。"""
            监听者.discard(监听)
        return 退订
    def 订主题(监听):
        """订阅主题变化。"""
        return 上下文.监听('theme/change',监听)
    def 注入操作():
        """账号操作表。"""
        return 操作
    操作={
        'refresh':刷新,
        'contactUs':意见反馈,
        'showLogin':显示登录,
        'setOnboarding':设引导,
        'hooks':{
            'account':{
                'getSnapshot':读账号快照,
                'subscribe':订账号,
            },
            'theme':{
                'getSnapshot':上下文.theme.getTheme,
                'subscribe':订主题,
            },
        },
        'start':开始登录,
        'cancel':取消登录,
        'signOut':退出登录,
    }
    if 原生平台 is not None:
        操作['platform']=原生平台
    def 登记引导():
        """登记模型设置登录引导。"""
        return 上下文.slots.register({
            'name':'settings.models.sign-in',
            'locale':命名空间,
            'inject':注入操作,
        },账号引导)
    上下文.slots.inject('settings.models.sign-in',登记引导)
    def 登记菜单():
        """登记侧栏账号菜单。"""
        return 上下文.slots.register({
            'name':'settings.launcher',
            'locale':命名空间,
            'inject':注入操作,
        },账号菜单)
    上下文.slots.inject('settings.launcher',登记菜单)
    def 登记分区():
        """仅凭证已存时登记账号设置分区。"""
        注销=None
        def 更新():
            """按快照挂上或拆掉分区。"""
            nonlocal 注销
            视图=快照['view']
            if 视图 is not None and 视图.get('status')=='credential-stored':
                if 注销 is None:
                    def 导航标签():
                        """账号导航标签。"""
                        return 翻译('nav')
                    注销=上下文.slots.register({
                        'name':'settings.section',
                        'id':'account',
                        'order':-10,
                        'label':导航标签,
                        'locale':命名空间,
                        'inject':注入操作,
                    },账号分区)
            else:
                if 注销 is not None:
                    注销()
                    注销=None
        监听者.add(更新)
        更新()
        def 拆():
            """取消订阅并拆分区。"""
            监听者.discard(更新)
            if 注销 is not None:
                注销()
        return 拆
    上下文.slots.inject('settings.section',登记分区)

inject=依赖
apply=应用
