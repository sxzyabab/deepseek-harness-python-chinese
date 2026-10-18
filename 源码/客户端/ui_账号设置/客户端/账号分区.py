'设置里的账号页。只显示宿主给出的安全状态'
from ...模块.客户端.通告 import 取握手窗口
import os
from decimal import Decimal
from ...ui_对话.异常 import 注入模块样式文件,挂上,清空子
from ...ui_基础界面组件 import 按钮
from ...ui_基础界面组件.icons import 图标右上16
from .文案 import 中文
from .账号头像 import 账号头像
from .授权网址 import 授权网址带主题
from .格式化余额 import 格式化余额

__all__=['账号分区']

样式模块='账号分区'
进行中阶段=('initializing','waiting-browser','exchanging','committing')

def 建(文档,标签,类名=None):
    '带账号分区类名的节点'
    注入模块样式文件(
        文档,
        '账号分区样式',
        os.path.join(os.path.dirname(__file__),'账号分区.module.css'),
        样式模块,
    )
    节点=文档.createElement(标签)
    if isinstance(类名,str) and 类名!='':
        节点.className=类名
    节点.setAttribute('data-dsh-css',样式模块)
    return 节点

class 账号分区:
    '资料、充值余额、赠金和平台链接'
    def __init__(自身,属性):
        '记下账号订阅和平台页通道'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.根=None
        自身.忙=False
        自身.失败了=False
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

    def 显示页(自身,打开,页):
        '只保留自己仍是最新业主的那次请求'
        if 自身.放开页面 is not None:
            自身.放开页面()
        def 结束(_原因=None):
            '这一次不再占有页面'
            自身.放开页面=None
        自身.放开页面=打开(页,结束)

    def 执行(自身,动作):
        '失败留在状态行上'
        自身.忙=True
        自身.失败了=False
        自身.渲染()
        try:
            动作()
        except Exception:
            自身.失败了=True
        finally:
            自身.忙=False
            自身.渲染()

    def 画出(自身):
        '未登录且没有进行中的尝试时显示登录入口'
        属性=自身.属性
        窗口=属性['window'] if 'window' in 属性 else 取握手窗口()
        文档=窗口.document
        if 自身.根 is None:
            自身.根=文档.createElement('div')
            自身.根.style.display='contents'
            父=属性.get('parent')
            if 父 is not None:
                父.appendChild(自身.根)
        else:
            清空子(自身.根)
        def 全量(快照):
            '整份账号'
            return 快照
        钩=属性.get('useAccount')
        账号=钩(全量) if 钩 is not None else {}
        if isinstance(账号,dict) is False:
            账号={}
        def 取色(快照):
            '当前色板'
            活动=快照.get('active') if isinstance(快照,dict) else None
            if isinstance(活动,dict):
                return 活动.get('colorScheme')
            return 'light'
        色板钩=属性.get('useTheme')
        色板=色板钩(取色) if 色板钩 is not None else 'light'
        if 色板 not in ('light','dark'):
            色板='light'
        视图=账号.get('view') if isinstance(账号.get('view'),dict) else None
        细节=账号.get('details') if isinstance(账号.get('details'),dict) else {}
        资料栏=细节.get('profile') if isinstance(细节.get('profile'),dict) else None
        资料=资料栏.get('value') if isinstance(资料栏,dict) and 资料栏.get('status')=='ready' and isinstance(资料栏.get('value'),dict) else None
        余额栏=细节.get('balance') if isinstance(细节.get('balance'),dict) else None
        钱包=余额栏.get('value') if isinstance(余额栏,dict) and 余额栏.get('status')=='ready' else None
        赠金钱包=[]
        if isinstance(余额栏,dict) and 余额栏.get('status')=='ready':
            for 项 in 余额栏.get('bonusWallets') or []:
                if Decimal(项['balance'])>0:
                    赠金钱包.append(项)
        显示赠金=not (isinstance(余额栏,dict) and 余额栏.get('status')=='ready') or len(赠金钱包)>0
        尝试=视图.get('attempt') if isinstance(视图,dict) else None
        活动=isinstance(尝试,dict) and 尝试.get('phase') in 进行中阶段
        已登录=isinstance(视图,dict) and 视图.get('status')=='credential-stored'
        if 已登录 is not True:
            if 自身.放开页面 is not None:
                自身.放开页面()
                自身.放开页面=None
        链接=视图.get('links') if isinstance(视图,dict) and isinstance(视图.get('links'),dict) else {}
        def 平台链接(文案,类名):
            '桌面打开内嵌页，浏览器开新标签'
            链=文档.createElement('a')
            if isinstance(类名,str) and 类名!='':
                链.className=类名
                链.setAttribute('data-dsh-css',样式模块)
            链.href=链接.get('usageUrl') or ''
            链.target='_blank'
            链.rel='noreferrer'
            if 视图 is None:
                链.setAttribute('aria-disabled','true')
            链.textContent=文案
            def 点用量(事件):
                '已登录的桌面改走内嵌用量页'
                打开=属性.get('openPlatformPage')
                if 打开 is not None and 已登录:
                    事件.preventDefault()
                    自身.显示页(打开,'usage')
            链.addEventListener('click',点用量)
            return 链
        if 自身.失败了 or 账号.get('failed') is True or (isinstance(尝试,dict) and 尝试.get('phase')=='failed'):
            状态文=中文['failed']
        elif isinstance(尝试,dict) and 尝试.get('phase')=='expired':
            状态文=中文['expired']
        elif 活动:
            阶段=尝试.get('phase')
            if 阶段=='initializing':
                状态文=中文['initializing']
            elif 阶段=='waiting-browser':
                状态文=中文['waiting']
            else:
                状态文=中文['completing']
        elif 已登录:
            if isinstance(资料,dict) and 资料.get('contact'):
                状态文=资料.get('contact')
            elif 资料栏 is None:
                状态文=中文['loading']
            else:
                状态文=中文['profileUnavailable']
        else:
            状态文=中文['signInDescription']
        if 已登录 is not True and 活动 is not True:
            区=建(文档,'section','signedOut')
            区.setAttribute('aria-label',中文['nav'])
            盒=建(文档,'div','signedOutContent')
            文=建(文档,'div','signedOutCopy')
            题=建(文档,'span','signedOutTitle')
            题.textContent=中文['settingsSignedOutTitle']
            述=建(文档,'span','signedOutDescription')
            述.setAttribute('role','status')
            if 自身.失败了 or 账号.get('failed') is True:
                述.textContent=中文['failed']
            else:
                述.textContent=中文['settingsSignedOutDescription']
            文.appendChild(题)
            文.appendChild(述)
            盒.appendChild(文)
            def 点登录():
                '发起登录'
                自身.执行(属性.get('start'))
            钮=按钮({
                'window':窗口,
                'variant':'primary',
                'className':'signInButton',
                'disabled':自身.忙 or 视图 is None,
                'onClick':点登录,
                'children':中文['signIn'],
            })
            钮根=钮.渲染()
            钮根.setAttribute('data-dsh-css',样式模块)
            盒.appendChild(钮根)
            区.appendChild(盒)
            自身.根.appendChild(区)
            自身.订上()
            return
        区=建(文档,'section','section')
        区.setAttribute('aria-label',中文['nav'])
        卡=建(文档,'div','card')
        身份=建(文档,'div','identity')
        头像盒=建(文档,'span','avatar')
        if 已登录 and isinstance(账号.get('avatar'),dict):
            头像盒.setAttribute('data-avatar-status',账号['avatar'].get('status') or '')
        头像=账号头像({
            'window':窗口,
            'avatar':账号.get('avatar') if 已登录 else None,
            'avatarFailed':属性.get('avatarFailed'),
        })
        挂上(头像盒,头像)
        身份.appendChild(头像盒)
        文案盒=建(文档,'div','identityCopy')
        名=建(文档,'span','name')
        if 已登录:
            名.textContent=(资料.get('name') if isinstance(资料,dict) else None) or 中文['signedIn']
        else:
            名.textContent=中文['signedOut']
        态=建(文档,'span','status')
        态.setAttribute('role','status')
        态.textContent=状态文
        文案盒.appendChild(名)
        文案盒.appendChild(态)
        身份.appendChild(文案盒)
        卡.appendChild(身份)
        if 已登录 and 链接.get('usageUrl'):
            更多=建(文档,'a','accountInfo')
            更多.href=窗口.URL('/',链接['usageUrl']).href
            更多.target='_blank'
            更多.rel='noopener noreferrer'
            更多.appendChild(文档.createTextNode(中文['accountInfo']))
            更多.appendChild(图标右上16({'window':窗口,'size':12}))
            卡.appendChild(更多)
        区.appendChild(卡)
        if 活动:
            动作=建(文档,'div','actions')
            授权=尝试.get('authorizeUrl')
            if 授权:
                开=建(文档,'a','linkButton')
                开.href=授权网址带主题(授权,色板)
                开.target='_blank'
                开.rel='noreferrer'
                开.textContent=中文['open']
                动作.appendChild(开)
            def 点取消():
                '取消这次尝试'
                def 取消():
                    '交给宿主'
                    属性['cancel'](尝试['id'])
                自身.执行(取消)
            取消钮=按钮({
                'window':窗口,
                'variant':'outline',
                'disabled':自身.忙 or 尝试.get('phase')=='committing',
                'onClick':点取消,
                'children':中文['cancel'],
            })
            挂上(动作,取消钮)
            区.appendChild(动作)
        余额卡=建(文档,'div','balanceCard')
        行=建(文档,'div','row')
        行标=文档.createElement('span')
        行标.textContent=中文['balance']
        行.appendChild(行标)
        if 已登录 and isinstance(钱包,list) and len(钱包)>0:
            额=建(文档,'span','amount')
            for 项 in 钱包:
                符号='¥' if 项.get('currency')=='CNY' else '$'
                片=文档.createElement('span')
                片.textContent=格式化余额(项['balance'],符号)
                额.appendChild(片)
            行.appendChild(额)
        elif 已登录 is not True or 余额栏 is None:
            缺=建(文档,'span','unavailable')
            缺.textContent=中文['balanceSignedOut'] if 已登录 is not True else 中文['loading']
            行.appendChild(缺)
        else:
            行.appendChild(平台链接(中文['balanceUnavailable'],'unavailableLink'))
        余额卡.appendChild(行)
        if 已登录 and 显示赠金:
            隔=建(文档,'div','divider')
            余额卡.appendChild(隔)
            赠行=建(文档,'div','row')
            赠标=文档.createElement('span')
            赠标.textContent=中文['bonusBalance']
            赠行.appendChild(赠标)
            赠值=建(文档,'span','bonusValue')
            if len(赠金钱包)>0:
                额=建(文档,'span','amount')
                for 项 in 赠金钱包:
                    符号='¥' if 项.get('currency')=='CNY' else '$'
                    片=文档.createElement('span')
                    片.textContent=格式化余额(项['balance'],符号)
                    额.appendChild(片)
                赠值.appendChild(额)
            elif 余额栏 is None:
                缺=建(文档,'span','unavailable')
                缺.textContent=中文['loading']
                赠值.appendChild(缺)
            else:
                赠值.appendChild(平台链接(中文['balanceUnavailable'],'unavailableLink'))
            赠行.appendChild(赠值)
            余额卡.appendChild(赠行)
        隔=建(文档,'div','divider')
        余额卡.appendChild(隔)
        更多行=建(文档,'div','row')
        次=建(文档,'span','secondary')
        次.textContent=中文['more']
        更多行.appendChild(次)
        链接行=建(文档,'div','links')
        链接行.appendChild(平台链接(中文['usage'],'linkButton'))
        充值=建(文档,'a','linkButton')
        充值.className='linkButton primary'
        充值.href=链接.get('topUpUrl') or ''
        充值.target='_blank'
        充值.rel='noreferrer'
        if 视图 is None:
            充值.setAttribute('aria-disabled','true')
        充值.textContent=中文['topUp']
        def 点充值(事件):
            '已登录的桌面改走内嵌充值页'
            打开=属性.get('openPlatformPage')
            if 打开 is not None and 已登录:
                事件.preventDefault()
                自身.显示页(打开,'top-up')
        充值.addEventListener('click',点充值)
        链接行.appendChild(充值)
        更多行.appendChild(链接行)
        余额卡.appendChild(更多行)
        区.appendChild(余额卡)
        自身.根.appendChild(区)
        自身.订上()

    def 订上(自身):
        '账号或主题变化时重画'
        if 自身.已订:
            return
        def 变更():
            '绘制中只记一笔'
            if 自身.绘制中:
                自身.待重画=True
                return
            自身.渲染()
        for 名 in ('useAccount','useTheme'):
            钩=自身.属性.get(名)
            订=getattr(钩,'_subscribe',None) if 钩 is not None else None
            if callable(订):
                自身.退订.append(订(变更))
        自身.已订=True

    def 拆除(自身):
        '卸下订阅和平台页请求'
        if 自身.放开页面 is not None:
            自身.放开页面()
            自身.放开页面=None
        for 退 in 自身.退订:
            退()
        自身.退订=[]
        自身.已订=False
