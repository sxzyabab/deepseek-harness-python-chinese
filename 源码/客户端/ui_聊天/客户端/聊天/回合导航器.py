from ....ui_对话.异常 import 标样式模块
from .用披露 import 注入聊天样式,真属性

__all__=['回合导航器']

样式模块='turn-navigator'
间距=10
内边=6
淡出=24


class 回合导航器:
    '转录右侧的回合刻度。点一下跳到那一回合'
    def __init__(自身,属性=None):
        '记下轨条目'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.根=None
        自身.悬停=None
        if 'window' in 自身.属性:
            自身.渲染()

    def 更新(自身,属性):
        '刷新属性'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 渲染(自身):
        '刻度按固定间距排。窄容器由样式藏起'
        if 自身.根 is not None:
            自身.根.remove()
        属性=自身.属性
        窗口=属性['window']
        文档=窗口.document
        注入聊天样式(文档,样式模块,'回合导航器.module.css')
        翻译=属性.get('t')
        if not callable(翻译):
            def 翻译(键,参数=None):
                '没有文案表时返回键'
                return 键
        项表=属性.get('items') or []
        槽=文档.createElement('div')
        槽.className='slot'
        标样式模块(槽,样式模块)
        框=文档.createElement('div')
        框.className='frame'
        标样式模块(框,样式模块)
        滚=文档.createElement('div')
        滚.className='scroller'
        标样式模块(滚,样式模块)
        刻=文档.createElement('div')
        刻.className='marks'
        标样式模块(刻,样式模块)
        刻.style.height=str(max(0,len(项表)*间距))+'px'
        下标=0
        for 项 in 项表:
            if not isinstance(项,dict):
                下标+=1
                continue
            钮=文档.createElement('button')
            钮.type='button'
            钮.className='mark'
            标样式模块(钮,样式模块)
            钮.style.top=str(下标*间距)+'px'
            锚=项.get('anchor') if isinstance(项.get('anchor'),dict) else {}
            if 锚.get('kind')!='loaded':
                钮.classList.add('markUnloaded')
            if 项.get('turn')==属性.get('activeTurn'):
                钮.classList.add('markActive')
            if 项.get('turn')==属性.get('busyTurn'):
                钮.classList.add('markBusy')
            钮.setAttribute('aria-label',str(项.get('turn')))

            def 跳(事件=None,钉项=项):
                '跳到这一回合'
                去=属性.get('onNavigate')
                if callable(去):
                    去(钉项)

            def 进入(事件=None,钉项=项,钉钮=钮):
                '悬停时给出预览'
                自身.悬停=钉项
                钉钮.classList.add('markPreview')
                自身.画预览(文档,框,钉项,翻译)

            def 离开(事件=None,钉钮=钮):
                '离开刻度就收起预览'
                钉钮.classList.remove('markPreview')
                自身.收预览()

            钮.addEventListener('click',跳)
            钮.addEventListener('mouseenter',进入)
            钮.addEventListener('mouseleave',离开)
            刻.appendChild(钮)
            下标+=1
        滚.appendChild(刻)
        框.appendChild(滚)
        槽.appendChild(框)
        自身.根=槽
        自身.框=框
        if 属性.get('parent') is not None:
            属性['parent'].appendChild(槽)
        return 槽

    def 画预览(自身,文档,框,项,翻译):
        '预览里是提示和回复的前几行'
        自身.收预览()
        预=文档.createElement('div')
        预.className='preview'
        标样式模块(预,样式模块)
        提示=文档.createElement('div')
        提示.className='previewPrompt'
        标样式模块(提示,样式模块)
        提示.textContent=项.get('prompt') or ''
        回复=文档.createElement('div')
        回复.className='previewResponse'
        标样式模块(回复,样式模块)
        回复.textContent=项.get('response') or ''
        预.appendChild(提示)
        预.appendChild(回复)
        框.appendChild(预)
        自身.预览=预

    def 收预览(自身):
        '去掉预览'
        预=getattr(自身,'预览',None)
        if 预 is not None and 预.parentNode is not None:
            预.remove()
        自身.预览=None
