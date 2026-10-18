'跳过充值或跳过设置前的确认'
from ...模块.客户端.通告 import 取握手窗口
import os
from ...ui_对话.异常 import 注入模块样式文件,挂上
from ...ui_基础界面组件 import 按钮,模态
from ...ui_基础界面组件.icons import 图标关闭描边常规
from .文案 import 中文

__all__=['上手引导确认']

样式模块='桌面上手引导'

class 上手引导确认:
    '额度确认和跳过设置确认'
    def __init__(自身,属性):
        '记下要确认的动作'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.根=None
        自身.模态=None
        自身.渲染()

    def 更新(自身,属性):
        '换成新的 props'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 渲染(自身):
        '画出无标题栏的确认框'
        属性=自身.属性
        窗口=属性['window'] if 'window' in 属性 else 取握手窗口()
        文档=窗口.document
        注入模块样式文件(
            文档,
            '桌面上手引导样式',
            os.path.join(os.path.dirname(__file__),'桌面上手引导.module.css'),
            样式模块,
        )
        if 自身.根 is None:
            自身.根=文档.createElement('div')
            自身.根.style.display='contents'
        else:
            while 自身.根.firstChild is not None:
                自身.根.firstChild.remove()
        种类=属性.get('kind')
        额度=种类!='skip'
        标题=中文['onboardingNoCreditTitle'] if 额度 else 中文['onboardingSkipTitle']
        盒=文档.createElement('div')
        盒.className='confirmation'
        盒.setAttribute('data-dsh-css',样式模块)
        头=文档.createElement('div')
        头.className='confirmationHeading'
        头.setAttribute('data-dsh-css',样式模块)
        题=文档.createElement('h2')
        题.textContent=标题
        关=文档.createElement('button')
        关.type='button'
        关.className='confirmationClose'
        关.setAttribute('data-dsh-css',样式模块)
        关.setAttribute('aria-label',中文['close'])
        关.appendChild(图标关闭描边常规({'window':窗口,'size':14}))
        def 点关(_事件=None):
            '关闭确认'
            回调=属性.get('onClose')
            if 回调 is not None:
                回调()
        关.addEventListener('click',点关)
        头.appendChild(题)
        头.appendChild(关)
        述=文档.createElement('p')
        述.textContent=中文['onboardingNoCreditDescription'] if 额度 else 中文['onboardingSkipDescription']
        盒.appendChild(头)
        盒.appendChild(述)
        动作=文档.createElement('div')
        动作.className='confirmationActions'
        动作.setAttribute('data-dsh-css',样式模块)
        忙=属性.get('busy') is True
        能充=属性.get('canRecharge') is True
        if 种类=='credit-skip':
            次动作=属性.get('onSkip')
            次文=中文['onboardingUnderstood']
        elif 种类=='credit':
            次动作=属性.get('onContinue')
            次文=中文['onboardingUnderstood']
        else:
            次动作=属性.get('onContinueSetup')
            次文=中文['onboardingKeepSetting']
        次=按钮({
            'window':窗口,
            'variant':'outline',
            'className':'dialogButton',
            'disabled':忙,
            'onClick':次动作,
            'children':次文,
        })
        次根=次.渲染()
        次根.setAttribute('data-dsh-css',样式模块)
        主=按钮({
            'window':窗口,
            'variant':'primary',
            'className':'dialogButton',
            'disabled':忙 or (额度 and 能充 is not True),
            'onClick':属性.get('onRecharge') if 额度 else 属性.get('onSkip'),
            'children':中文['onboardingGoTopUp'] if 额度 else 中文['onboardingEnter'],
        })
        主根=主.渲染()
        主根.setAttribute('data-dsh-css',样式模块)
        动作.appendChild(次根)
        动作.appendChild(主根)
        盒.appendChild(动作)
        模态属性={
            'window':窗口,
            'open':True,
            'headless':True,
            'title':标题,
            'onClose':属性.get('onClose'),
            'children':[盒],
        }
        if 自身.模态 is None:
            自身.模态=模态(模态属性)
        else:
            自身.模态.更新(模态属性)
        自身.模态.渲染()
        挂上(自身.根,自身.模态)
        return 自身.根
