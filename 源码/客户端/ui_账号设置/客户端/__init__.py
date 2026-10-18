'账号设置登记，以及可重连的账号状态订阅'
from ...模块.客户端.通告 import 取握手窗口
import os
from urllib.parse import parse_qsl,urlencode,urlsplit,urlunsplit
from ....基础设施.通用工具 import 获取内部数据,启动守护线程
from ..联系配置 import 联系配置全局键,联系字段
from ..上手引导设置 import 桌面引导命名空间
from . import (
    上手引导余额,
    上手引导凭据,
    上手引导插图,
    上手引导欢迎步,
    上手引导状态,
    上手引导确认,
    上手引导表面,
    上手引导目的步,
    上手引导过程步,
    上手引导额度步,
    授权网址,
    平台页,
    平台覆盖层,
    格式化余额,
    文案,
    桌面上手引导,
    桌面上手引导入口,
    浏览器登录,
    登出图标,
    登出对话框,
    登录对话框,
    覆盖层惰性,
    账号分区,
    账号头像,
    账号头像装载,
    账号平台宿主,
    账号引导,
    账号须知,
    账号菜单,
    账号配额须知,
    赠金须知,
    区域设置列表,
)
from .文案 import 中文,英文,命名空间
from .授权网址 import 授权网址带主题
from .平台页 import 创建平台页
from .浏览器登录 import 浏览器登录
from .账号头像装载 import 账号头像装载
from .赠金须知 import 创建赠金须知控制器
from .上手引导状态 import 桌面上手引导控制器
from .上手引导凭据 import 读上手引导密钥
from .账号引导 import 账号引导
from .账号菜单 import 账号菜单
from .账号分区 import 账号分区
from .账号配额须知 import 账号配额须知
from .账号平台宿主 import 账号平台宿主
from .桌面上手引导入口 import 桌面上手引导入口

__all__=[
    '上手引导余额','上手引导凭据','上手引导插图','上手引导欢迎步','上手引导状态',
    '上手引导确认','上手引导表面','上手引导目的步','上手引导过程步','上手引导额度步',
    '授权网址','平台页','平台覆盖层','格式化余额','文案','桌面上手引导','桌面上手引导入口',
    '浏览器登录','登出图标','登出对话框','登录对话框','覆盖层惰性','账号分区','账号头像',
    '账号头像装载','账号平台宿主','账号引导','账号须知','账号菜单','账号配额须知','赠金须知',
    '区域设置列表','命名空间','依赖','应用',
]

依赖=['slots','locale','remote','remote.account','remote.session','theme','configForms']

def 应用(上下文,配置=None):
    '在桌面和普通网页里登记账号界面，并跟上账号状态流'
    窗口=取握手窗口()
    桌面=getattr(窗口,'dshDesktop',None) is not None
    def 登记词典():
        '登记本页中英文案表。页面显示不走英文表'
        return 上下文.locale.register(命名空间,{'zh':中文,'en':英文})
    上下文.副作用(登记词典,'account: dictionaries')
    if 联系配置全局键 in 窗口:
        载荷=窗口[联系配置全局键]
    else:
        载荷={}
    配置=联系字段({} if 载荷 is None else 载荷)
    快照盒={'值':{
        'view':None,
        'details':None,
        'avatar':None,
        'failed':False,
        'loginVisible':False,
        'desktopOnboardingVisible':桌面,
    }}
    监听者=set()
    def 发布(值):
        '替换快照并通知'
        快照盒['值']=值
        for 监听 in list(监听者):
            监听()
    def 目的地(网址):
        '授权页带上当前色板'
        return 授权网址带主题(网址,上下文.theme.取主题()['active']['colorScheme'])
    浏览器=浏览器登录(目的地)
    def 拆浏览器():
        '关掉还开着的授权标签'
        def 拆():
            '释放标签'
            浏览器.拆除()
        return 拆
    上下文.副作用(拆浏览器,'account: pending browser window')
    def 发布头像(值):
        '把头像状态写进账号快照'
        发布({**快照盒['值'],'avatar':值})
    头像=账号头像装载(发布头像)
    def 拆头像():
        '卸下头像加载'
        def 拆():
            '不再加载'
            头像.拆除()
        return 拆
    上下文.副作用(拆头像,'account: profile picture lifetime')
    def 客户():
        '一次账号调用的身份。调用时再读语言和时区'
        版本=os.environ.get('DSH_CLIENT_VERSION')
        if 版本 is None or 版本=='':
            raise RuntimeError('account: this client build carries no DSH_CLIENT_VERSION')
        时刻=窗口.Date()
        return {
            'version':版本,
            'locale':上下文.locale.getSnapshot()['active'],
            'timezoneOffsetSeconds':-时刻.getTimezoneOffset()*60,
        }
    def 发布须知(通知):
        '没有通知时去掉字段。有通知时挂上'
        其余=dict(快照盒['值'])
        其余.pop('notice',None)
        if 通知 is None:
            发布(其余)
        else:
            其余['notice']=通知
            发布(其余)
    def 读赠金():
        '读未通知的赠金。业务失败就抛'
        结果=上下文.remote.account.getUnnotifiedBonuses(客户())
        if 结果['ok'] is not True:
            raise RuntimeError('account bonus read failed')
        return 结果['value']
    def 确认赠金(账号标识,订单标识):
        '把一笔订单标成已通知'
        结果=上下文.remote.account.ackBonusNotified(账号标识,订单标识,客户())
        if 结果['ok'] is not True:
            raise RuntimeError('account bonus acknowledgement failed')
        return 结果['value']
    须知=创建赠金须知控制器({
        'ackRetryDelayMs':配置['bonusAckRetryDelayMs'],
        'ackRetryMaxDelayMs':配置['bonusAckRetryMaxDelayMs'],
        'read':读赠金,
        'acknowledge':确认赠金,
        'publish':发布须知,
    })
    def 拆须知():
        '结束赠金生命周期'
        def 拆():
            '丢掉卡片和确认'
            须知['end']()
        return 拆
    上下文.副作用(拆须知,'account: bonus notice lifetime')
    修订盒={'值':0}
    刷新中盒={'值':None}
    def 刷新():
        '已登录时读资料和余额。进行中的刷新不重复发'
        视图=快照盒['值'].get('view')
        if not isinstance(视图,dict) or 视图.get('status')!='credential-stored':
            return
        if 刷新中盒['值'] is not None:
            return
        代=修订盒['值']
        刷新中盒['值']=True
        def 写入(字段,值):
            '这一代还有效才写进 details'
            if 值 is None or 代!=修订盒['值']:
                return
            if isinstance(值,dict) and 值.get('status')=='failed':
                窗口.console.error('[deepseek-account] account read failed',{'field':字段})
            细节=dict(快照盒['值'].get('details') or {})
            细节[字段]=值
            发布({**快照盒['值'],'details':细节})
        def 读栏(字段,查询):
            '查询失败记成 failed'
            try:
                值=查询()
            except Exception:
                值={'status':'failed'}
            写入(字段,值)
        def 读资料():
            '资料成功且仍是这一代时开始加载头像'
            结果=上下文.remote.account.getProfile(客户())
            if 结果['ok'] is not True:
                raise RuntimeError('account profile failed')
            if 代==修订盒['值'] and isinstance(结果['value'],dict) and 结果['value'].get('status')=='ready':
                人=结果['value'].get('value') if isinstance(结果['value'].get('value'),dict) else {}
                头像.设地址(人.get('avatarUrl'))
            return 结果['value']
        def 读余额():
            '读充值余额和赠金'
            结果=上下文.remote.account.getBalance(客户())
            if 结果['ok'] is not True:
                raise RuntimeError('account balance failed')
            return 结果['value']
        读栏('profile',读资料)
        读栏('balance',读余额)
        if 刷新中盒['值'] is True:
            刷新中盒['值']=None
    def 拆修订():
        '卸下时作废在途的资料请求'
        def 拆():
            '抬高代际'
            修订盒['值']+=1
        return 拆
    上下文.副作用(拆修订,'account: details request lifetime')
    def 开账号流(信号):
        '打开账号状态流'
        return 上下文.remote.account.watch(信号)
    def 账号流结束(_已接受=None):
        '流结束'
        return RuntimeError('account stream ended')
    流=获取内部数据(上下文.remote,'stream')({
        'name':'account',
        'open':开账号流,
        'ended':账号流结束,
    })
    已拆除={'值':False}
    def 拆流():
        '拆除状态流'
        def 拆():
            '标记并 dispose'
            已拆除['值']=True
            return 流.dispose()
        return 拆
    上下文.副作用(拆流,'account: state stream')
    def 消费流():
        '把每一帧写进快照'
        try:
            for 帧 in 流:
                修订盒['值']+=1
                刷新中盒['值']=None
                头像.重置()
                视图=帧.value
                先前=快照盒['值']
                要初始化=isinstance(视图,dict) and 视图.get('status')=='credential-stored' and isinstance(视图.get('attempt'),dict) and 视图['attempt'].get('phase')=='succeeded' and not (isinstance(先前.get('view'),dict) and isinstance(先前['view'].get('attempt'),dict) and 先前['view']['attempt'].get('phase')=='succeeded')
                下一=dict(先前)
                旧须知=下一.pop('notice',None)
                下一['view']=视图
                下一['details']=None
                下一['avatar']=None
                下一['failed']=False
                if isinstance(视图,dict) and 视图.get('status')=='credential-stored' and 旧须知 is not None:
                    下一['notice']=旧须知
                发布(下一)
                浏览器.更新(视图)
                帧.accept()
                if isinstance(视图,dict) and 视图.get('status')=='credential-stored':
                    须知['begin']()
                else:
                    须知['end']()
                if 要初始化:
                    try:
                        已初始化=上下文.remote.session.initializeDefaultModel()
                        if 已初始化['ok'] is not True:
                            窗口.console.error('[deepseek-account] default model initialization failed',{'reason':'refused'})
                    except Exception:
                        窗口.console.error('[deepseek-account] default model initialization failed',{'reason':'disconnected'})
                刷新()
        except Exception:
            if 已拆除['值'] is not True:
                发布({**快照盒['值'],'failed':True})
    启动守护线程(消费流)
    原生平台=getattr(窗口,'dshPlatform',None)
    平台页通道=创建平台页()
    def 拆平台页():
        '卸下平台页请求'
        def 拆():
            '丢掉请求，不通知业主'
            平台页通道['dispose']()
        return 拆
    上下文.副作用(拆平台页,'account: platform page request')
    def 刷新账号():
        '重试头像，并重读余额和未通知赠金'
        头像.重试()
        刷新()
        须知['refresh']()
    def 打开平台页(再读):
        '从充值页返回才重读。被换掉的页不读'
        def 打开(页,关闭时):
            '打开一页，返回时按原因决定要不要重读'
            def 结束(原因):
                '先交给这一面，再按返回重读'
                关闭时(原因)
                if 原因=='returned' and 页=='top-up':
                    再读()
            return 平台页通道['open'](页,结束)
        return 打开
    def 头像失败(值):
        '渲染出来的图片失败'
        头像.失败(值)
    def 订过期(监听):
        '登录失效'
        return getattr(上下文.remote,'$on')('deepseek-account/session-expired',监听)
    def 订要登录(监听):
        '模型要求登录'
        return getattr(上下文.remote,'$on')('deepseek-account/model-sign-in-required',监听)
    def 意见反馈():
        '用这一次点击时的账号、版本和屏幕打开问卷'
        资料=None
        细节=快照盒['值'].get('details')
        if isinstance(细节,dict):
            资料=细节.get('profile')
        标识=None
        if isinstance(资料,dict) and 资料.get('status')=='ready' and isinstance(资料.get('value'),dict):
            标识=资料['value'].get('id')
        现场={
            'uid':标识,
            'version':os.environ.get('DSH_CLIENT_VERSION'),
            'width':窗口.screen.width,
            'height':窗口.screen.height,
            'pixelRatio':窗口.devicePixelRatio,
        }
        def 打开问卷(设备信息):
            '拼问卷地址并打开'
            地址=urlsplit(配置['contactFormUrl'])
            比例=现场['pixelRatio']
            try:
                比例数=float(比例)
            except (TypeError,ValueError):
                比例数=1
            if 比例数!=比例数:
                比例数=1
            宽=round(现场['width']*比例数)
            高=round(现场['height']*比例数)
            设备=[设备信息]
            if 宽>0 and 高>0:
                设备.append('screen_resolution='+str(宽)+'x'+str(高))
            字段={
                'uid':现场['uid'],
                'source':配置['contactSource'],
                'harness_version':现场['version'],
                'device_info':'; '.join([项 for 项 in 设备 if 项]),
            }
            查询=parse_qsl(地址.query,keep_blank_values=True)
            表={}
            for 键,值 in 查询:
                表[键]=值
            for 名,值 in 字段.items():
                表['hide_'+名]='1'
                表.pop('prefill_'+名,None)
                if 值:
                    表['prefill_'+名]=值
            for 名 in ('os_version','device_brand','app_locale','screen_resolution','app_version','device_model'):
                表.pop('prefill_'+名,None)
                表.pop('hide_'+名,None)
            网址=urlunsplit((地址.scheme,地址.netloc,地址.path,urlencode(list(表.items())),地址.fragment))
            窗口.open(网址,'_blank','noopener,noreferrer')
        桌面桥=getattr(窗口,'dshDesktop',None)
        读设备=getattr(桌面桥,'deviceInfo',None) if 桌面桥 is not None else None
        if 读设备 is None:
            打开问卷(窗口.navigator.userAgent)
            return
        def 已读(设备信息):
            '带上原生设备信息'
            打开问卷(设备信息 if isinstance(设备信息,str) else '')
        def 读失败(_错误=None):
            '原生信息可选，没有也打开问卷'
            打开问卷('')
        try:
            结果=读设备()
        except Exception as 错误:
            读失败(错误)
            return
        if hasattr(结果,'然后'):
            结果.然后(已读,读失败)
        elif hasattr(结果,'then'):
            结果.then(已读,读失败)
        else:
            已读(结果)
    def 显示登录(可见):
        '打开或关掉登录框'
        发布({**快照盒['值'],'loginVisible':可见})
    def 设引导(进行中):
        '引导占有登录框时推迟赠金卡片'
        发布({**快照盒['值'],'onboarding':进行中})
    def 赠金已展示(订单标识):
        '卡片画出一帧'
        须知['shown'](订单标识)
    def 赠金已关(订单标识):
        '用户关掉卡片'
        须知['dismiss'](订单标识)
    def 取账号():
        '当前账号快照'
        return 快照盒['值']
    def 订账号(监听):
        '订阅账号快照'
        监听者.add(监听)
        def 退():
            '卸下这个监听'
            监听者.discard(监听)
        return 退
    def 取主题快照():
        '当前主题'
        return 上下文.theme.取主题()
    def 订主题(监听):
        '主题变化'
        return 上下文.监听('theme/change',监听)
    def 开始():
        '打开发起登录。失败写进快照再抛出'
        发布({**快照盒['值'],'loginVisible':True,'loginFailed':False})
        传输=getattr(窗口,'__DSH_TRANSPORT__',None)
        源=窗口.location.origin
        if 桌面 and isinstance(传输,dict) and 传输.get('streamBaseUrl') is not None:
            源=窗口.URL(传输['streamBaseUrl']).origin
        def 请求():
            '向宿主发起登录'
            结果=上下文.remote.account.startSignIn(客户(),源,'desktop' if 桌面 else 'web')
            if 结果['ok'] is not True:
                raise RuntimeError('account start failed')
            return 结果['value']
        def 最新():
            '发起返回前已经到达的视图'
            return 快照盒['值'].get('view')
        try:
            if 桌面:
                请求()
            else:
                浏览器.开始(请求,最新)
        except Exception as 错误:
            发布({**快照盒['值'],'loginFailed':True})
            raise 错误
    def 取消(标识):
        '取消这次尝试'
        结果=上下文.remote.account.cancelSignIn(标识)
        if 结果['ok'] is not True:
            raise RuntimeError('account cancel failed')
    def 有运行任务():
        '有没有还在用这个账号的任务'
        结果=上下文.remote.account.hasRunningAccountTasks()
        if 结果['ok'] is not True:
            raise RuntimeError('account task query failed')
        return 结果['value']
    def 退出():
        '去掉本地账号凭证'
        结果=上下文.remote.account.signOut(客户())
        if 结果['ok'] is True:
            return
        raise 结果['error']
    操作={
        'avatarFailed':头像失败,
        'subscribeSessionExpired':订过期,
        'subscribeModelSignInRequired':订要登录,
        'refreshAccount':刷新账号,
        'contactUs':意见反馈,
        'showLogin':显示登录,
        'setOnboarding':设引导,
        'bonusNoticeShown':赠金已展示,
        'bonusNoticeDismissed':赠金已关,
        'hooks':{
            'account':{'getSnapshot':取账号,'subscribe':订账号},
            'theme':{'getSnapshot':取主题快照,'subscribe':订主题},
        },
        'start':开始,
        'cancel':取消,
        'hasRunningAccountTasks':有运行任务,
        'signOut':退出,
    }
    if 原生平台 is not None:
        操作['openPlatformPage']=打开平台页(刷新账号)
    def 注入操作():
        '槽位登记用的账号动作'
        return 操作
    if 桌面:
        控制器=桌面上手引导控制器(
            上下文.configForms.get(桌面引导命名空间),
            上下文.configForms.get('ui-chat'),
            上下文.configForms.developerTools.setEnabled,
            操作['hooks']['account'],
            读上手引导密钥,
            上下文.configForms.describe(),
        )
        def 拆引导():
            '卸下引导控制器'
            def 拆():
                '不再写进度'
                控制器.拆除()
            return 拆
        上下文.副作用(拆引导,'account: desktop onboarding lifetime')
        def 挂凭据():
            '凭据或适配器变化时重查密钥'
            def 刷新凭据(_事件=None):
                '忽略事件参数'
                控制器.作废凭据()
            远程开=getattr(上下文.remote,'$on')
            拆除器=[
                远程开('credentials/reference-updated',刷新凭据),
                远程开('llm/adapters-updated',刷新凭据),
                上下文.configForms.describe().subscribe(刷新凭据),
            ]
            def 拆():
                '卸下这三路'
                for 退 in 拆除器:
                    退()
            return 拆
        上下文.副作用(挂凭据,'account: desktop credential readiness')
        def 登记桌面引导():
            '登记壳层覆盖'
            def 注入引导():
                '引导的钩子和动作'
                注入={'hooks':{
                    'account':操作['hooks']['account'],
                    'onboarding':控制器.状态,
                }}
                def 设可见(可见):
                    '覆盖层是否还盖着工作区'
                    if 快照盒['值'].get('desktopOnboardingVisible') is not 可见:
                        发布({**快照盒['值'],'desktopOnboardingVisible':可见})
                注入['setVisible']=设可见
                if 原生平台 is not None:
                    注入['openPlatformPage']=打开平台页(刷新)
                注入['update']=控制器.更新
                注入['complete']=控制器.完成
                注入['retry']=控制器.重试
                def 跟踪(名,属性=None):
                    '有产品埋点才记'
                    埋点=上下文.get('productAnalytics')
                    if 埋点 is None:
                        return
                    埋点.track(名,属性)
                注入['track']=跟踪
                return 注入
            return 上下文.slots.register({
                'name':'shell.overlay',
                'id':'desktop-onboarding',
                'locale':命名空间,
                'inject':注入引导,
            },桌面上手引导入口)
        上下文.slots.inject('shell.overlay',登记桌面引导)
    def 登记引导():
        '模型设置里的账号登录'
        return 上下文.slots.register({
            'name':'settings.models.sign-in',
            'locale':命名空间,
            'inject':注入操作,
        },账号引导)
    上下文.slots.inject('settings.models.sign-in',登记引导)
    def 选额度(业主):
        '只接账号额度这一种通知'
        if isinstance(业主,dict) and 业主.get('code')=='ACCOUNT_QUOTA':
            return 业主
        return None
    def 登记额度():
        '全帧额度通知'
        def 注入额度():
            '账号和平台页'
            注入={'hooks':{
                'account':操作['hooks']['account'],
                'platformPage':平台页通道,
            }}
            if 原生平台 is not None:
                注入['openPlatformPage']=打开平台页(刷新账号)
            return 注入
        return 上下文.slots.register({
            'name':'shell.quota-notice',
            'locale':命名空间,
            'select':选额度,
            'inject':注入额度,
        },账号配额须知)
    上下文.slots.inject('shell.quota-notice',登记额度)
    if 原生平台 is not None:
        def 登记平台宿主():
            '共享的原生平台页'
            def 注入宿主():
                '原生桥和当前请求'
                return {
                    'platform':原生平台,
                    'hooks':{'page':平台页通道},
                    'closePage':平台页通道['close'],
                }
            return 上下文.slots.register({
                'name':'shell.overlay',
                'id':'account.platform-page',
                'locale':命名空间,
                'inject':注入宿主,
            },账号平台宿主)
        上下文.slots.inject('shell.overlay',登记平台宿主)
    def 登记菜单():
        '侧栏账号入口'
        return 上下文.slots.register({
            'name':'settings.launcher',
            'locale':命名空间,
            'inject':注入操作,
        },账号菜单)
    上下文.slots.inject('settings.launcher',登记菜单)
    def 注入分区():
        '已登录才登记账号分区'
        退登={'值':None}
        def 更新():
            '登录状态变化时挂上或拆掉'
            视图=快照盒['值'].get('view')
            if isinstance(视图,dict) and 视图.get('status')=='credential-stored':
                if 退登['值'] is None:
                    def 标签():
                        '分区名。用中文表原文，是账号与余额'
                        return 中文['nav']
                    退登['值']=上下文.slots.register({
                        'name':'settings.section',
                        'id':'account',
                        'order':-10,
                        'label':标签,
                        'locale':命名空间,
                        'inject':注入操作,
                    },账号分区)
            else:
                if 退登['值'] is not None:
                    退登['值']()
                    退登['值']=None
        监听者.add(更新)
        更新()
        def 拆():
            '卸下监听和分区'
            监听者.discard(更新)
            if 退登['值'] is not None:
                退登['值']()
        return 拆
    上下文.slots.inject('settings.section',注入分区)

inject=依赖
apply=应用
