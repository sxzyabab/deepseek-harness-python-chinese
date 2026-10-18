'选择要看到多少工作过程。方向键在三个选项间移动'
from ...模块.客户端.通告 import 取握手窗口
import os
from ...ui_对话.异常 import 注入模块样式文件
from ...ui_基础界面组件 import 按钮
from .文案 import 中文
from .上手引导插图 import 图地址

__all__=['上手引导过程步','过程选项']

样式模块='桌面上手引导'
过程选项=(
    {'value':'compact','titleKey':'onboardingCompact','descriptionKey':'onboardingCompactDescription','icon':'onboarding-compact.svg','size':40},
    {'value':'standard','titleKey':'onboardingStandard','descriptionKey':'onboardingStandardDescription','icon':'onboarding-standard.svg','size':36},
    {'value':'detailed','titleKey':'onboardingDetailed','descriptionKey':'onboardingDetailedDescription','icon':'onboarding-detailed.svg','size':36},
)

class 上手引导过程步:
    '三个单选。选了才能进入应用'
    def __init__(自身,属性):
        '记下当前过程'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.根=None
        自身.渲染()

    def 更新(自身,属性):
        '换成新的 props'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 渲染(自身):
        '方向键切换并聚焦下一张'
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
        根.className='content process'
        根.setAttribute('data-dsh-css',样式模块)
        文=文档.createElement('div')
        文.className='copy'
        文.setAttribute('data-dsh-css',样式模块)
        题=文档.createElement('h1')
        题.id='desktop-onboarding-title'
        题.tabIndex=-1
        题.textContent=中文['onboardingProcess']
        述=文档.createElement('p')
        述.className='subtitle'
        述.setAttribute('data-dsh-css',样式模块)
        述.textContent=中文['onboardingProcessDescription']
        文.appendChild(题)
        文.appendChild(述)
        根.appendChild(文)
        组=文档.createElement('div')
        组.className='processCards'
        组.setAttribute('role','radiogroup')
        组.setAttribute('aria-labelledby','desktop-onboarding-title')
        组.setAttribute('data-dsh-css',样式模块)
        当前=属性.get('process')
        忙=属性.get('busy') is True
        for 下标,选项 in enumerate(过程选项):
            钮=文档.createElement('button')
            钮.type='button'
            钮.setAttribute('role','radio')
            钮.setAttribute('data-process',选项['value'])
            钮.setAttribute('data-dsh-css',样式模块)
            选中=当前==选项['value']
            钮.setAttribute('aria-checked','true' if 选中 else 'false')
            if 选中 or (当前 is None and 选项['value']=='compact'):
                钮.tabIndex=0
            else:
                钮.tabIndex=-1
            类名='card'
            if 选中:
                类名=类名+' selected'
            钮.className=类名
            if 忙:
                钮.setAttribute('aria-disabled','true')
            def 点(_事件=None,值=选项['value']):
                '不忙才选中'
                if 忙:
                    return
                回调=属性.get('onSelect')
                if 回调 is not None:
                    回调(值)
            def 按键(事件,值=选项['value'],钮=钮):
                '左右或上下移到相邻选项'
                if 忙:
                    return
                if 事件.key in ('ArrowRight','ArrowDown'):
                    方向=1
                elif 事件.key in ('ArrowLeft','ArrowUp'):
                    方向=-1
                else:
                    return
                事件.preventDefault()
                现下标=0
                for 序,项 in enumerate(过程选项):
                    if 项['value']==值:
                        现下标=序
                        break
                下一=过程选项[(现下标+方向+len(过程选项))%len(过程选项)]
                回调=属性.get('onSelect')
                if 回调 is not None:
                    回调(下一['value'])
                父=钮.parentElement
                if 父 is not None:
                    目标=父.querySelector('[data-process="'+下一['value']+'"]')
                    if 目标 is not None:
                        目标.focus()
            钮.addEventListener('click',点)
            钮.addEventListener('keydown',按键)
            图标盒=文档.createElement('span')
            图标盒.className='processIcon'
            图标盒.setAttribute('data-dsh-css',样式模块)
            图=文档.createElement('img')
            图.src=图地址(选项['icon'])
            图.width=选项['size']
            图.height=选项['size']
            图.alt=''
            图标盒.appendChild(图)
            题字=文档.createElement('span')
            题字.className='cardTitle'
            题字.setAttribute('data-dsh-css',样式模块)
            题字.textContent=中文[选项['titleKey']]
            述字=文档.createElement('span')
            述字.className='cardDescription'
            述字.setAttribute('data-dsh-css',样式模块)
            述字.textContent=中文[选项['descriptionKey']]
            钮.appendChild(图标盒)
            钮.appendChild(题字)
            钮.appendChild(述字)
            组.appendChild(钮)
        根.appendChild(组)
        主动=文档.createElement('div')
        主动.className='primaryAction'
        主动.setAttribute('data-dsh-css',样式模块)
        if 当前 is not None:
            def 进入():
                '不忙才进入应用'
                if 忙:
                    return
                回调=属性.get('onComplete')
                if 回调 is not None:
                    回调()
            进=按钮({
                'window':窗口,
                'variant':'primary',
                'className':'action',
                'onClick':进入,
                'children':中文['onboardingEnter'],
            })
            进根=进.渲染()
            进根.setAttribute('data-dsh-css',样式模块)
            if 忙:
                进根.setAttribute('aria-disabled','true')
            主动.appendChild(进根)
        根.appendChild(主动)
        标题盒=属性.get('heading')
        if isinstance(标题盒,dict):
            标题盒['当前']=题
        自身.根=根
        return 自身.根
