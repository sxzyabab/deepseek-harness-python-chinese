'欢迎页。必须明确点开始'
from ...模块.客户端.通告 import 取握手窗口
import os
from ...ui_对话.异常 import 注入模块样式文件,挂上
from ...ui_基础界面组件 import 按钮
from .文案 import 中文
from .上手引导插图 import 上手引导插图,图地址

__all__=['上手引导欢迎步']

样式模块='桌面上手引导'

class 上手引导欢迎步:
    '欢迎文案和开始设置'
    def __init__(自身,属性):
        '记下标题节点和开始动作'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.根=None
        自身.渲染()

    def 更新(自身,属性):
        '换成新的 props'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 渲染(自身):
        '中文和英文用不同的欢迎图'
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
        根.className='content welcome'
        根.setAttribute('data-dsh-css',样式模块)
        文=文档.createElement('div')
        文.className='copy'
        文.setAttribute('data-dsh-css',样式模块)
        题=文档.createElement('h1')
        题.id='desktop-onboarding-title'
        题.tabIndex=-1
        题.appendChild(文档.createTextNode(中文['onboardingWelcome']+' '))
        牌=文档.createElement('em')
        牌.className='brand'
        牌.setAttribute('data-dsh-css',样式模块)
        牌.textContent=中文['onboardingBrand']
        题.appendChild(牌)
        述=文档.createElement('p')
        述.className='heroDescription'
        述.setAttribute('data-dsh-css',样式模块)
        述.textContent=中文['onboardingIntroduction']
        文.appendChild(题)
        文.appendChild(述)
        钮=按钮({
            'window':窗口,
            'variant':'primary',
            'className':'action start',
            'disabled':属性.get('busy') is True,
            'onClick':属性.get('onStart'),
            'children':中文['onboardingStart'],
        })
        钮根=钮.渲染()
        钮根.setAttribute('data-dsh-css',样式模块)
        文.appendChild(钮根)
        根.appendChild(文)
        图盒=文档.createElement('div')
        图盒.className='welcomeIllustration'
        图盒.setAttribute('aria-hidden','true')
        图盒.setAttribute('data-dsh-css',样式模块)
        中文图=属性.get('locale')=='zh'
        if 中文图:
            浅='onboarding-welcome-zh.webp'
            深='onboarding-welcome-zh-dark.webp'
        else:
            浅='onboarding-welcome.webp'
            深='onboarding-welcome-dark.webp'
        图=上手引导插图({
            'window':窗口,
            'className':'welcomeArtwork',
            'src':图地址(浅),
            'darkSrc':图地址(深),
        })
        挂上(图盒,图)
        根.appendChild(图盒)
        标题盒=属性.get('heading')
        if isinstance(标题盒,dict):
            标题盒['当前']=题
        自身.根=根
        return 自身.根
