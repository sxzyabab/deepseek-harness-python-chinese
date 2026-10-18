'侧栏账号入口，以及本地决定的退出登录'
from ...模块.客户端.通告 import 取握手窗口
import os
from ...ui_对话.异常 import 注入模块样式文件,挂上,清空子
from ...ui_基础界面组件 import 菜单,吐司
from ...ui_基础界面组件.icons import 图标省略16,图标发送16,图标设置16,图标用户16
from .文案 import 中文
from .登出图标 import 登出图标
from .账号头像 import 账号头像
from .账号须知 import 账号须知卡片
from .登录对话框 import 登录对话框
from .登出对话框 import 登出对话框

__all__=['账号菜单']

样式模块='账号菜单'

def 建(文档,标签,类名=None):
    '带账号菜单类名的节点'
    注入模块样式文件(
        文档,
        '账号菜单样式',
        os.path.join(os.path.dirname(__file__),'账号菜单.module.css'),
        样式模块,
    )
    节点=文档.createElement(标签)
    if isinstance(类名,str) and 类名!='':
        节点.className=类名
    节点.setAttribute('data-dsh-css',样式模块)
    return 节点

def 读全量(钩):
    '钩子选出整份快照'
    if 钩 is None:
        return None
    def 全量(快照):
        '原样返回'
        return 快照
    return 钩(全量)

class 账号菜单:
    '侧栏上的账号按钮。设置打开的上升沿刷新一次账号'
    def __init__(自身,属性):
        '记下渲染器交来的 props'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.根=None
        自身.菜单=None
        自身.登录框=None
        自身.退出框=None
        自身.须知=None
        自身.打开=False
        自身.忙=False
        自身.退出影响=None
        自身.登录通知=0
        自身.过期通知=False
        自身.设置曾开=False
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

    def 画出(自身):
        '已登录显示头像和名字。未登录显示更多'
        属性=自身.属性
        窗口=属性['window'] if 'window' in 属性 else 取握手窗口()
        文档=窗口.document
        if 自身.根 is None:
            自身.根=建(文档,'div','root')
            父=属性.get('parent')
            if 父 is not None:
                父.appendChild(自身.根)
        else:
            清空子(自身.根)
        开着=属性.get('settingsOpen') is True
        if 开着 and 自身.设置曾开 is not True:
            刷新=属性.get('refreshAccount')
            if 刷新 is not None:
                刷新()
        自身.设置曾开=开着
        账号=读全量(属性.get('useAccount'))
        if isinstance(账号,dict) is False:
            账号={}
        def 取色(快照):
            '当前色板'
            活动=快照.get('active') if isinstance(快照,dict) else None
            if isinstance(活动,dict):
                return 活动.get('colorScheme')
            return None
        色板钩=属性.get('useTheme')
        色板='light'
        if 色板钩 is not None:
            取到=色板钩(取色)
            if 取到 in ('light','dark'):
                色板=取到
        视图=账号.get('view') if isinstance(账号.get('view'),dict) else None
        已登录=isinstance(视图,dict) and 视图.get('status')=='credential-stored'
        资料=账号.get('details')
        资料=资料.get('profile') if isinstance(资料,dict) else None
        if 资料 is None:
            标签=None
        elif 资料.get('status')=='ready':
            人=资料.get('value') if isinstance(资料.get('value'),dict) else {}
            标签=人.get('name') or 人.get('contact') or 中文['signedIn']
        else:
            标签=中文['signedIn']
        宽=属性.get('wide') is True
        if 自身.登录通知>0:
            def 登录完():
                '这条提示结束'
                自身.登录通知=0
                自身.渲染()
            挂上(自身.根,吐司({
                'window':窗口,
                'text':中文['modelSignInRequired'],
                'onDone':登录完,
            }))
        if 自身.过期通知:
            def 过期完():
                '这条提示结束'
                自身.过期通知=False
                自身.渲染()
            挂上(自身.根,吐司({
                'window':窗口,
                'text':中文['sessionExpired'],
                'onDone':过期完,
            }))
        须知=账号.get('notice')
        if 已登录 and 账号.get('desktopOnboardingVisible') is not True and 账号.get('onboarding') is not True and isinstance(须知,dict):
            if 自身.须知 is None or 自身.须知.订单!=须知.get('orderId'):
                自身.须知=账号须知卡片({
                    'window':窗口,
                    'notice':须知,
                    'anchor':自身.根,
                    'onShown':属性.get('bonusNoticeShown'),
                    'onDismiss':属性.get('bonusNoticeDismissed'),
                })
            else:
                自身.须知.更新({
                    'window':窗口,
                    'notice':须知,
                    'anchor':自身.根,
                    'onShown':属性.get('bonusNoticeShown'),
                    'onDismiss':属性.get('bonusNoticeDismissed'),
                })
                自身.须知.渲染()
            挂上(自身.根,自身.须知)
        触发=建(文档,'button','trigger')
        触发.type='button'
        触发.setAttribute('data-collapsed','true' if 宽 is not True else 'false')
        触发.setAttribute('data-signed-out','true' if 已登录 is not True else 'false')
        触发.setAttribute('aria-label',中文['menu'])
        触发.setAttribute('aria-haspopup','menu')
        触发.setAttribute('aria-expanded','true' if 自身.打开 else 'false')
        def 切换(_事件=None):
            '打开或关上菜单'
            自身.打开=自身.打开 is not True
            自身.渲染()
        触发.addEventListener('click',切换)
        if 已登录:
            头像盒=建(文档,'span','avatar')
            if isinstance(账号.get('avatar'),dict):
                头像盒.setAttribute('data-avatar-status',账号['avatar'].get('status') or '')
            头像=账号头像({
                'window':窗口,
                'avatar':账号.get('avatar'),
                'avatarFailed':属性.get('avatarFailed'),
            })
            挂上(头像盒,头像)
            触发.appendChild(头像盒)
        else:
            触发.appendChild(图标省略16({'window':窗口,'size':14}))
        if 宽:
            名=建(文档,'span','label')
            名.textContent=标签 if 已登录 else 中文['more']
            触发.appendChild(名)
        条目=[
            {'id':'settings','label':中文['settings'],'icon':图标设置16({'window':窗口,'size':16})},
            {'id':'contact','label':中文['contactUs'],'icon':图标发送16({'window':窗口,'size':16})},
        ]
        快捷=属性.get('settingsShortcut')
        if 快捷 is not None:
            条目[0]['shortcut']=快捷
        if 已登录:
            退图=登出图标({'window':窗口})
            条目.append({'id':'signout','label':中文['signOut'],'icon':退图.渲染(),'disabled':自身.忙})
        else:
            条目.append({'id':'signin','label':中文['signIn'],'icon':图标用户16({'window':窗口,'size':16})})
        def 选中(标识):
            '设置、反馈、登录或退出'
            if 标识=='settings':
                自身.打开=False
                触发.focus()
                属性['openSettings']()
                自身.渲染()
            elif 标识=='contact':
                自身.打开=False
                属性['contactUs']()
                自身.渲染()
            elif 标识=='signin':
                自身.打开=False
                def 吞(_错误=None):
                    '发起失败已经写进快照'
                    return None
                try:
                    属性['start']()
                except Exception as 错误:
                    吞(错误)
                自身.渲染()
            else:
                自身.请求退出()
        def 关上():
            '菜单自己关上时同步状态'
            if 自身.打开:
                自身.打开=False
                自身.渲染()
        菜单属性={
            'window':窗口,
            'open':自身.打开,
            'side':'top',
            'portal':True,
            'className':'anchor',
            'anchor':触发,
            'items':条目,
            'onClose':关上,
            'onSelect':选中,
        }
        if 自身.菜单 is None:
            自身.菜单=菜单(菜单属性)
        else:
            自身.菜单.更新(菜单属性)
        自身.菜单.渲染()
        挂上(自身.根,自身.菜单)
        if 账号.get('loginVisible') is True and 账号.get('onboarding') is not True:
            登录属性={
                'window':窗口,
                'account':账号,
                'colorScheme':色板,
                'start':属性.get('start'),
                'cancel':属性.get('cancel'),
                'close':自身.关登录,
                'useApiKey':自身.改用密钥,
            }
            if 自身.登录框 is None:
                自身.登录框=登录对话框(登录属性)
            else:
                自身.登录框.更新(登录属性)
                自身.登录框.渲染()
            挂上(自身.根,自身.登录框)
        if 已登录 and 自身.退出影响 is not None:
            退出属性={
                'window':窗口,
                'running':自身.退出影响,
                'signOut':属性.get('signOut'),
                'close':自身.关退出,
            }
            if 自身.退出框 is None:
                自身.退出框=登出对话框(退出属性)
            else:
                自身.退出框.更新(退出属性)
                自身.退出框.渲染()
            挂上(自身.根,自身.退出框)
        自身.订上()

    def 关登录(自身):
        '关掉登录框'
        属性=自身.属性
        显示=属性.get('showLogin')
        if 显示 is not None:
            显示(False)

    def 改用密钥(自身):
        '关掉登录框并打开官方密钥引导'
        自身.关登录()
        打开=自身.属性.get('openOnboarding')
        if 打开 is not None:
            打开('deepseek-official')

    def 关退出(自身):
        '关掉退出确认'
        自身.退出影响=None
        自身.渲染()

    def 请求退出(自身):
        '先问有没有正在用这个账号的任务'
        自身.忙=True
        自身.渲染()
        try:
            自身.退出影响=自身.属性['hasRunningAccountTasks']()
            自身.打开=False
        except Exception:
            自身.退出影响='unknown'
            自身.打开=False
        finally:
            自身.忙=False
            自身.渲染()

    def 订上(自身):
        '账号、主题和两条登录事件变化时重画'
        if 自身.已订:
            return
        def 变更():
            '绘制中只记一笔。节点不在页面上就退订'
            if 自身.绘制中:
                自身.待重画=True
                return
            if 自身.根 is None or 自身.根.parentNode is None:
                自身.拆除()
                return
            自身.渲染()
        属性=自身.属性
        for 名 in ('useAccount','useTheme'):
            钩=属性.get(名)
            订=getattr(钩,'_subscribe',None) if 钩 is not None else None
            if callable(订):
                自身.退订.append(订(变更))
        会话=属性.get('subscribeSessionExpired')
        if callable(会话):
            def 过期():
                '登录失效提示'
                自身.过期通知=True
                变更()
            自身.退订.append(会话(过期))
        模型=属性.get('subscribeModelSignInRequired')
        if callable(模型):
            def 要登录():
                '模型要求登录时再提示一条'
                自身.登录通知+=1
                变更()
            自身.退订.append(模型(要登录))
        自身.已订=True

    def 拆除(自身):
        '卸下订阅'
        for 退 in 自身.退订:
            退()
        自身.退订=[]
        自身.已订=False
        if 自身.登录框 is not None:
            自身.登录框.拆除()
