'账号授权对话框。失败后可以取消当前尝试再重试'
from ...模块.客户端.通告 import 取握手窗口
import os
from ...ui_对话.异常 import 注入模块样式文件,挂上,清空子
from ...ui_基础界面组件 import 按钮,模态,写剪贴板
from ...ui_基础界面组件.icons import 图标关闭描边常规,图标加载描边常规
from .文案 import 中文
from .授权网址 import 授权网址带主题

__all__=['登录对话框']

样式模块='登录对话框'
进行中阶段=('initializing','waiting-browser','exchanging','committing')

def 建(文档,标签,类名=None):
    '带登录对话框类名的节点'
    注入模块样式文件(
        文档,
        '登录对话框样式',
        os.path.join(os.path.dirname(__file__),'登录对话框.module.css'),
        样式模块,
    )
    节点=文档.createElement(标签)
    if isinstance(类名,str) and 类名!='':
        节点.className=类名
    节点.setAttribute('data-dsh-css',样式模块)
    return 节点

class 登录对话框:
    '等待浏览器、超时、失败和复制登录链接'
    def __init__(自身,属性):
        '记下账号状态和动作'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.根=None
        自身.模态=None
        自身.忙=False
        自身.失败了=False
        自身.复制结果=None
        自身.复制定时=None
        自身.上次尝试=None
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

    def 清复制(自身):
        '两秒后收起复制结果'
        if 自身.复制定时 is not None:
            取握手窗口().clearTimeout(自身.复制定时)
            自身.复制定时=None

    def 画出(自身):
        '按尝试阶段显示等待、超时或失败'
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
        账号=属性.get('account') if isinstance(属性.get('account'),dict) else {}
        视图=账号.get('view') if isinstance(账号.get('view'),dict) else None
        if isinstance(视图,dict) and 视图.get('status')=='credential-stored':
            关=属性.get('close')
            if 关 is not None:
                关()
            return
        尝试=视图.get('attempt') if isinstance(视图,dict) else None
        尝试键=None
        if isinstance(尝试,dict):
            尝试键=(尝试.get('id'),尝试.get('authorizeUrl'))
        if 尝试键!=自身.上次尝试:
            自身.上次尝试=尝试键
            自身.复制结果=None
            自身.清复制()
        阶段=尝试.get('phase') if isinstance(尝试,dict) else None
        活动=自身.忙 or 阶段 in 进行中阶段
        过期=阶段=='expired'
        本地失败=自身.失败了 or 账号.get('loginFailed') is True or 账号.get('failed') is True
        出错=本地失败 or 阶段=='failed'
        失败键='failed'
        if 本地失败 is not True and 阶段=='failed' and isinstance(尝试,dict) and 尝试.get('errorCode')=='no-response':
            失败键='noResponse'
        等待=活动 and 出错 is not True
        提交中=阶段=='committing'
        授权=尝试.get('authorizeUrl') if isinstance(尝试,dict) else None
        if 出错:
            标题=中文['failureTitle']
        elif 活动:
            标题=中文['browserTitle']
        elif 过期:
            标题=中文['timeoutTitle']
        else:
            标题=中文['loginTitle']
        内容=建(文档,'div','content')
        头=建(文档,'div','header')
        题=建(文档,'h2','title')
        题.textContent=标题
        头.appendChild(题)
        def 关闭():
            '提交中不能关。进行中先取消再关'
            if 提交中 or 自身.忙:
                return
            if 活动 and isinstance(尝试,dict):
                def 取消再关():
                    '取消这次尝试后关闭'
                    属性['cancel'](尝试['id'])
                    属性['close']()
                自身.执行(取消再关)
            else:
                属性['close']()
        关钮=建(文档,'button','close')
        关钮.type='button'
        关钮.setAttribute('aria-label',中文['close'])
        关钮.appendChild(图标关闭描边常规({'window':窗口,'size':14}))
        def 点关(_事件=None):
            '点关闭'
            关闭()
        关钮.addEventListener('click',点关)
        头.appendChild(关钮)
        内容.appendChild(头)
        说明=建(文档,'p','description')
        if 等待:
            说明.appendChild(文档.createTextNode(中文['browserPrompt']))
            链=建(文档,'button','link')
            链.type='button'
            链.disabled=not 授权
            复制文=中文['copyLink']
            if 自身.复制结果=='copiedLink':
                复制文=中文['copiedLink']
            elif 自身.复制结果=='copyFailed':
                复制文=中文['copyFailed']
            链.textContent=复制文
            def 点复制(_事件=None,授权=授权):
                '把带主题的授权链接放进剪贴板'
                if not 授权:
                    return
                色板=属性.get('colorScheme')
                网址=授权网址带主题(授权,色板)
                if 写剪贴板(网址):
                    自身.复制结果='copiedLink'
                else:
                    自身.复制结果='copyFailed'
                自身.清复制()
                def 收起():
                    '两秒后回到复制登录链接'
                    自身.复制结果=None
                    自身.复制定时=None
                    自身.渲染()
                自身.复制定时=窗口.setTimeout(收起,2000)
                自身.渲染()
            if 授权:
                链.addEventListener('click',点复制)
            说明.appendChild(链)
            说明.appendChild(文档.createTextNode(中文['browserDescription']))
        elif 出错:
            说明.textContent=中文[失败键]
        elif 过期:
            说明.textContent=中文['timeoutDescription']
        else:
            说明.textContent=中文['loginDescription']
        内容.appendChild(说明)
        动作=建(文档,'div','actions')
        def 次要():
            '进行中是取消，否则去添加密钥'
            if 活动:
                关闭()
            else:
                属性['useApiKey']()
        次钮=按钮({
            'window':窗口,
            'variant':'outline',
            'className':'secondaryButton',
            'disabled':提交中 or 自身.忙,
            'onClick':次要,
            'children':中文['cancel'] if 活动 else 中文['addApiKey'],
        })
        次根=次钮.渲染()
        次根.setAttribute('data-dsh-css',样式模块)
        动作.appendChild(次根)
        def 重试():
            '进行中先取消，再重新发起'
            if 活动 and isinstance(尝试,dict):
                属性['cancel'](尝试['id'])
            属性['start']()
        def 点主():
            '主按钮执行重试或发起'
            自身.执行(重试)
        if 等待:
            主子=图标加载描边常规({'window':窗口,'className':'spinner'})
            主子.setAttribute('data-dsh-css',样式模块)
        elif 过期 or 出错:
            主子=中文['retry']
        else:
            主子=中文['signIn']
        主钮=按钮({
            'window':窗口,
            'variant':'primary',
            'className':'primaryButton',
            'disabled':自身.忙 or 提交中 or 等待 or 视图 is None,
            'onClick':点主,
            'children':主子,
        })
        主根=主钮.渲染()
        主根.setAttribute('data-dsh-css',样式模块)
        if 等待:
            主根.setAttribute('aria-label',中文['waiting'])
        动作.appendChild(主根)
        模态属性={
            'window':窗口,
            'open':True,
            'headless':True,
            'title':标题,
            'onClose':关闭,
            'className':'dialog',
            'children':[内容,动作],
        }
        if 自身.模态 is None:
            自身.模态=模态(模态属性)
        else:
            自身.模态.更新(模态属性)
        自身.模态.渲染()
        罩=自身.模态.根
        if 罩 is not None:
            子=罩.firstElementChild
            while 子 is not None:
                类名=getattr(子,'className','')
                if isinstance(类名,str) and 'dialog' in 类名.split():
                    子.setAttribute('data-dsh-css',样式模块)
                子=子.nextElementSibling
        挂上(自身.根,自身.模态)

    def 执行(自身,动作):
        '动作失败时留在对话框里，允许再试'
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

    def 拆除(自身):
        '卸下复制结果的定时器'
        自身.清复制()
