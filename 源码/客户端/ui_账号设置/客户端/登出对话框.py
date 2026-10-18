'退出登录前按当前任务影响确认'
from ...模块.客户端.通告 import 取握手窗口
import os
from ...ui_对话.异常 import 注入模块样式文件,挂上,清空子
from ...ui_基础界面组件 import 按钮,模态
from ...ui_基础界面组件.icons import 图标关闭描边常规
from .文案 import 中文

__all__=['登出对话框']

样式模块='登录对话框'

def 建(文档,标签,类名=None):
    '确认框沿用登录对话框的样式'
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

class 登出对话框:
    '按查不到、正在跑或空闲显示不同说明'
    def __init__(自身,属性):
        '记下任务影响和退出动作'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.根=None
        自身.模态=None
        自身.忙=False
        自身.失败了=False
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
        '确认后才真正退出'
        属性=自身.属性
        窗口=属性['window'] if 'window' in 属性 else 取握手窗口()
        文档=窗口.document
        if 自身.根 is None:
            自身.根=文档.createElement('div')
            自身.根.style.display='contents'
        else:
            清空子(自身.根)
        影响=属性.get('running')
        if 影响=='unknown':
            说明文=中文['signOutUnknownDescription']
        elif 影响:
            说明文=中文['signOutRunningDescription']
        else:
            说明文=中文['signOutDescription']
        def 关闭():
            '忙的时候不能关'
            if 自身.忙:
                return
            属性['close']()
        内容=建(文档,'div','content')
        头=建(文档,'div','header')
        题=建(文档,'h2','title')
        题.textContent=中文['signOut']
        头.appendChild(题)
        关钮=建(文档,'button','close')
        关钮.type='button'
        关钮.setAttribute('aria-label',中文['close'])
        关钮.disabled=自身.忙
        关钮.appendChild(图标关闭描边常规({'window':窗口,'size':14}))
        def 点关(_事件=None):
            '点关闭'
            关闭()
        关钮.addEventListener('click',点关)
        头.appendChild(关钮)
        内容.appendChild(头)
        说明=建(文档,'p','description')
        说明.textContent=说明文
        内容.appendChild(说明)
        if 自身.失败了:
            警=建(文档,'p','description')
            警.setAttribute('role','alert')
            警.textContent=中文['failed']
            内容.appendChild(警)
        动作=建(文档,'div','actions')
        取消=按钮({
            'window':窗口,
            'variant':'outline',
            'className':'secondaryButton',
            'disabled':自身.忙,
            'onClick':关闭,
            'children':中文['cancel'],
        })
        取消根=取消.渲染()
        取消根.setAttribute('data-dsh-css',样式模块)
        动作.appendChild(取消根)
        def 确认():
            '退出成功后关闭。失败留在框里'
            自身.忙=True
            自身.失败了=False
            自身.渲染()
            try:
                属性['signOut']()
                属性['close']()
            except Exception:
                自身.失败了=True
            finally:
                自身.忙=False
                自身.渲染()
        退出=按钮({
            'window':窗口,
            'variant':'primary',
            'className':'primaryButton',
            'disabled':自身.忙,
            'onClick':确认,
            'children':中文['signOut'],
        })
        退出根=退出.渲染()
        退出根.setAttribute('data-dsh-css',样式模块)
        动作.appendChild(退出根)
        模态属性={
            'window':窗口,
            'open':True,
            'headless':True,
            'title':中文['signOut'],
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
