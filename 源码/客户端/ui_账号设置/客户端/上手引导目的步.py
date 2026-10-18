'选择工作用途。两张卡片可以同时选'
from ...模块.客户端.通告 import 取握手窗口
import os
from ...ui_对话.异常 import 注入模块样式文件,挂上
from ...ui_基础界面组件 import 按钮
from ...ui_基础界面组件.icons import 图标勾描边常规
from ...ui_基础界面组件.文件类型图标 import 文件类型图标
from .文案 import 中文
from .上手引导插图 import 图地址

__all__=['上手引导目的步','目的卡片']

样式模块='桌面上手引导'
办公种类=('word','ppt','excel','pdf','image')
开发种类=('typescript','javascript','sql','python','cpp')

class 目的卡片:
    '一张可勾选的用途卡。刚选中时图标入场'
    def __init__(自身,属性):
        '记下用途和是否选中'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.根=None
        自身.上次选中=False
        自身.入场=False
        自身.渲染()

    def 更新(自身,属性):
        '换成新的 props'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 渲染(自身):
        '选中后换成一排文件图标'
        属性=自身.属性
        窗口=属性['window'] if 'window' in 属性 else 取握手窗口()
        文档=窗口.document
        注入模块样式文件(
            文档,
            '桌面上手引导样式',
            os.path.join(os.path.dirname(__file__),'桌面上手引导.module.css'),
            样式模块,
        )
        选中=属性.get('checked') is True
        自身.入场=选中 and 自身.上次选中 is not True
        自身.上次选中=选中
        用途=属性.get('purpose')
        if 自身.根 is not None:
            自身.根.remove()
        卡=文档.createElement('div')
        类名='card'
        if 选中:
            类名=类名+' selected'
        if 用途=='office':
            类名=类名+' officeCard'
        卡.className=类名
        卡.setAttribute('data-dsh-css',样式模块)
        顶=文档.createElement('div')
        顶.className='cardTop'
        顶.setAttribute('data-dsh-css',样式模块)
        if 选中:
            图标行=文档.createElement('span')
            图标行.className='fileIcons'
            if 自身.入场:
                图标行.className=图标行.className+' iconsEntering'
            图标行.setAttribute('aria-hidden','true')
            图标行.setAttribute('data-dsh-css',样式模块)
            种类=办公种类 if 用途=='office' else 开发种类
            for 种 in 种类:
                图标=文件类型图标({'window':窗口,'kind':种,'size':28})
                挂上(图标行,图标)
            顶.appendChild(图标行)
        else:
            图=文档.createElement('img')
            图.src=图地址('onboarding-office.svg' if 用途=='office' else 'onboarding-code.svg')
            图.width=40
            图.height=40
            图.alt=''
            顶.appendChild(图)
        标=文档.createElement('label')
        标.className='cardCheckbox'
        标.setAttribute('data-dsh-css',样式模块)
        框=文档.createElement('input')
        框.type='checkbox'
        题键='onboardingOffice' if 用途=='office' else 'onboardingDevelopment'
        框.setAttribute('aria-label',中文[题键])
        框.checked=选中
        def 切换(_事件=None):
            '点卡片'
            回调=属性.get('onToggle')
            if 回调 is not None:
                回调()
        框.addEventListener('change',切换)
        指示=文档.createElement('span')
        指示.className='indicator'
        指示.setAttribute('aria-hidden','true')
        指示.setAttribute('data-dsh-css',样式模块)
        指示.appendChild(图标勾描边常规({'window':窗口}))
        标.appendChild(框)
        标.appendChild(指示)
        顶.appendChild(标)
        卡.appendChild(顶)
        题=文档.createElement('span')
        题.className='cardTitle'
        题.setAttribute('data-dsh-css',样式模块)
        题.textContent=中文[题键]
        述=文档.createElement('span')
        述.className='cardDescription'
        述.setAttribute('data-dsh-css',样式模块)
        述键='onboardingOfficeDescription' if 用途=='office' else 'onboardingDevelopmentDescription'
        述.textContent=中文[述键]
        卡.appendChild(题)
        卡.appendChild(述)
        自身.根=卡
        return 自身.根

class 上手引导目的步:
    '办公和开发可以同时选。选了才能继续'
    def __init__(自身,属性):
        '记下当前选择'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.根=None
        自身.办公卡=None
        自身.开发卡=None
        自身.渲染()

    def 更新(自身,属性):
        '换成新的 props'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 已选(自身,值):
        '单独选中或两个都选都算这张卡选中'
        目的=自身.属性.get('purpose')
        return 目的==值 or 目的=='both'

    def 切换(自身,值):
        '点一下翻转这一张，再合成 office、development、both 或空'
        if 自身.属性.get('busy') is True:
            return
        办公=自身.已选('office')
        开发=自身.已选('development')
        if 值=='office':
            办公=办公 is not True
        else:
            开发=开发 is not True
        if 办公 and 开发:
            结果='both'
        elif 办公:
            结果='office'
        elif 开发:
            结果='development'
        else:
            结果=None
        回调=自身.属性.get('onSelect')
        if 回调 is not None:
            回调(结果)

    def 渲染(自身):
        '两张卡和继续按钮'
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
        else:
            while 自身.根.firstChild is not None:
                自身.根.firstChild.remove()
        自身.根.className='content purpose'
        自身.根.setAttribute('data-dsh-css',样式模块)
        文=文档.createElement('div')
        文.className='copy'
        文.setAttribute('data-dsh-css',样式模块)
        题=文档.createElement('h1')
        题.id='desktop-onboarding-title'
        题.tabIndex=-1
        题.appendChild(文档.createTextNode(中文['onboardingPurposePrefix']+' '))
        牌=文档.createElement('em')
        牌.className='brand'
        牌.setAttribute('data-dsh-css',样式模块)
        牌.textContent=中文['onboardingBrand']
        题.appendChild(牌)
        题.appendChild(文档.createTextNode(' '+中文['onboardingPurposeSuffix']))
        述=文档.createElement('p')
        述.className='subtitle'
        述.setAttribute('data-dsh-css',样式模块)
        述.textContent=中文['onboardingPurposeDescription']
        文.appendChild(题)
        文.appendChild(述)
        自身.根.appendChild(文)
        卡片行=文档.createElement('div')
        卡片行.className='purposeCards'
        卡片行.setAttribute('data-dsh-css',样式模块)
        for 用途,持有 in (('office','办公卡'),('development','开发卡')):
            def 点(用途=用途):
                '翻转这一张'
                自身.切换(用途)
            卡属性={
                'window':窗口,
                'purpose':用途,
                'checked':自身.已选(用途),
                'onToggle':点,
            }
            卡=getattr(自身,持有)
            if 卡 is None:
                卡=目的卡片(卡属性)
                setattr(自身,持有,卡)
            else:
                卡.更新(卡属性)
                卡.渲染()
            挂上(卡片行,卡)
        自身.根.appendChild(卡片行)
        主动=文档.createElement('div')
        主动.className='primaryAction'
        主动.setAttribute('data-dsh-css',样式模块)
        if 属性.get('purpose') is not None:
            忙=属性.get('busy') is True
            def 继续():
                '不忙才继续'
                if 忙:
                    return
                回调=属性.get('onContinue')
                if 回调 is not None:
                    回调()
            钮=按钮({
                'window':窗口,
                'variant':'primary',
                'className':'action',
                'onClick':继续,
                'children':中文['onboardingContinue'],
            })
            钮根=钮.渲染()
            钮根.setAttribute('data-dsh-css',样式模块)
            if 忙:
                钮根.setAttribute('aria-disabled','true')
            主动.appendChild(钮根)
        自身.根.appendChild(主动)
        标题盒=属性.get('heading')
        if isinstance(标题盒,dict):
            标题盒['当前']=题
        return 自身.根
