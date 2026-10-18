'额度页。第一次进入时决定按钮顺序，之后保持'
from ...模块.客户端.通告 import 取握手窗口
import os
from ...ui_对话.异常 import 注入模块样式文件,挂上
from ...ui_基础界面组件 import 按钮
from .文案 import 中文
from .上手引导插图 import 上手引导插图,图地址

__all__=['上手引导额度步']

样式模块='桌面上手引导'

class 上手引导额度步:
    '已有额度时继续在前。没有额度时充值在前'
    def __init__(自身,属性):
        '记下额度和充值动作'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.根=None
        自身.渲染()

    def 更新(自身,属性):
        '换成新的 props'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 渲染(自身):
        '按已有额度切换主按钮'
        属性=自身.属性
        窗口=属性['window'] if 'window' in 属性 else 取握手窗口()
        文档=窗口.document
        注入模块样式文件(
            文档,
            '桌面上手引导样式',
            os.path.join(os.path.dirname(__file__),'桌面上手引导.module.css'),
            样式模块,
        )
        if 自身.根 is not None:
            自身.根.remove()
        根=文档.createElement('div')
        根.className='content credit'
        根.setAttribute('data-dsh-css',样式模块)
        中文图=属性.get('locale')=='zh'
        if 中文图:
            浅='onboarding-recharge-zh.webp'
            深='onboarding-recharge-zh-dark.webp'
        else:
            浅='onboarding-recharge.webp'
            深='onboarding-recharge-dark.webp'
        图=上手引导插图({
            'window':窗口,
            'className':'creditIllustration',
            'src':图地址(浅),
            'darkSrc':图地址(深),
        })
        挂上(根,图)
        文=文档.createElement('div')
        文.className='copy'
        文.setAttribute('data-dsh-css',样式模块)
        题=文档.createElement('h1')
        题.id='desktop-onboarding-title'
        题.tabIndex=-1
        题.textContent=中文['onboardingCredit']
        述=文档.createElement('p')
        述.className='heroDescription'
        述.setAttribute('data-dsh-css',样式模块)
        述.textContent=中文['onboardingCreditDescription']
        文.appendChild(题)
        文.appendChild(述)
        已有=属性.get('funded') is True
        能充=属性.get('canRecharge') is True
        忙=属性.get('busy') is True
        动作=文档.createElement('div')
        动作.className='creditActions'
        动作.setAttribute('data-dsh-css',样式模块)
        主=按钮({
            'window':窗口,
            'variant':'primary',
            'className':'action',
            'disabled':忙 or (已有 is not True and 能充 is not True),
            'onClick':属性.get('onContinue') if 已有 else 属性.get('onRecharge'),
            'children':中文['onboardingContinue'] if 已有 else 中文['onboardingTopUp'],
        })
        主根=主.渲染()
        主根.setAttribute('data-dsh-css',样式模块)
        次=按钮({
            'window':窗口,
            'variant':'outline',
            'className':'action laterAction',
            'disabled':忙 or (已有 and 能充 is not True),
            'onClick':属性.get('onRecharge') if 已有 else 属性.get('onLater'),
            'children':中文['onboardingFundedTopUp'] if 已有 else 中文['onboardingLater'],
        })
        次根=次.渲染()
        次根.setAttribute('data-dsh-css',样式模块)
        动作.appendChild(主根)
        动作.appendChild(次根)
        文.appendChild(动作)
        根.appendChild(文)
        标题盒=属性.get('heading')
        if isinstance(标题盒,dict):
            标题盒['当前']=题
        自身.根=根
        return 自身.根
