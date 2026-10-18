import importlib.resources as 包资源
import pywebbridge
from ...ui_基础界面组件.icons import 描边图标#常规描边搜索，基础界面没有这枚

样式文本=包资源.files(__package__).joinpath('轨迹工具栏.module.css').read_text(encoding='utf-8')

class 轨迹工具栏:
    '时长开关、折叠轮次和调用、搜索'
    def __init__(自身,属性):
        '记下属性并画出工具栏'
        自身.属性=属性#宿主属性
        自身.根=None#尚未画出
        自身.渲染()#构造时画出

    def __call__(自身,属性=None):
        '属性变了就重画'
        if 属性 is not None:
            自身.属性=属性
        return 自身.渲染()

    def 渲染(自身):
        '画出工具栏。看得见的字用中文原文'
        属性=自身.属性
        窗口=属性['window']
        文档=窗口.document
        if 文档.getElementById('轨迹工具栏样式') is None:
            样式=文档.createElement('style')
            样式.id='轨迹工具栏样式'
            样式.textContent=样式文本
            文档.head.appendChild(样式)
        实测=属性.get('actualDuration') is True
        实际时间=属性.get('actualTime') is True
        轮次收起=属性.get('allTurnsCollapsed') is True
        调用收起=属性.get('allAssistantsCollapsed') is True
        查询=属性.get('searchQuery') or ''
        旧=自身.根
        父=None if 旧 is None else 旧.parentNode
        if 旧 is not None:
            旧.remove()
        根=文档.createElement('div')
        根.className='root'
        根.setAttribute('role','toolbar')
        根.setAttribute('aria-label','轨迹工具栏')
        内=文档.createElement('div')
        内.className='inner'
        动作=文档.createElement('div')
        动作.className='actions'
        时长钮=文档.createElement('button')
        时长钮.setAttribute('type','button')
        时长钮.className='toggle'
        时长钮.setAttribute('aria-label','使用实际时长')
        时长钮.setAttribute('aria-pressed','true' if 实测 else 'false')
        时长钮.setAttribute('title','使用等宽操作' if 实测 else '使用实际时长')
        钟=文档.createElementNS('http://www.w3.org/2000/svg','svg')
        钟.setAttribute('class','toggleIcon')
        钟.setAttribute('viewBox','0 0 16 16')
        钟.setAttribute('fill','none')
        钟.setAttribute('aria-hidden','true')
        圆=文档.createElementNS('http://www.w3.org/2000/svg','circle')
        圆.setAttribute('cx','8')
        圆.setAttribute('cy','8')
        圆.setAttribute('r','5.25')
        针=文档.createElementNS('http://www.w3.org/2000/svg','path')
        针.setAttribute('d','M8 4.75V8l2.25 1.5')
        钟.appendChild(圆)
        钟.appendChild(针)
        时长钮.appendChild(钟)
        时长钮.appendChild(文档.createTextNode('时长'))
        def 切换时长(_事件):
            '在实测时长和等宽之间切换'
            回调=属性.get('onActualDurationChange')
            if callable(回调):
                回调(not 实测)
        时长钮.addEventListener('click',切换时长)
        时间钮=文档.createElement('button')
        时间钮.setAttribute('type','button')
        时间钮.className='control'
        时间钮.setAttribute('role','switch')
        时间钮.setAttribute('aria-checked','true' if 实际时间 else 'false')
        时间钮.hidden=True
        时间字=文档.createElement('span')
        时间字.textContent='实际时间'
        轨=文档.createElement('span')
        轨.className='controlTrack'
        if 实际时间:
            轨.setAttribute('data-on','true')
        轨.setAttribute('aria-hidden','true')
        拇指=文档.createElement('span')
        拇指.className='controlThumb'
        轨.appendChild(拇指)
        时间钮.appendChild(时间字)
        时间钮.appendChild(轨)
        def 切换时间(_事件):
            '在完整墙钟和压缩空闲之间切换'
            回调=属性.get('onActualTimeChange')
            if callable(回调):
                回调(not 实际时间)
        时间钮.addEventListener('click',切换时间)
        轮次钮=文档.createElement('button')
        轮次钮.setAttribute('type','button')
        轮次钮.className='action'
        轮次文案='展开所有轮次' if 轮次收起 else '收起所有轮次'
        轮次钮.setAttribute('aria-label',轮次文案)
        轮次钮.setAttribute('aria-pressed','true' if 轮次收起 else 'false')
        轮次钮.setAttribute('title',轮次文案)
        轮次标=文档.createElement('span')
        轮次标.className='actionIcon'
        轮次标.setAttribute('aria-hidden','true')
        轮次标.textContent='⊞' if 轮次收起 else '⊟'
        轮次钮.appendChild(轮次标)
        轮次钮.appendChild(文档.createTextNode('轮次'))
        def 切换轮次(_事件):
            '展开或收起全部可折叠轮次'
            回调=属性.get('onToggleAllTurns')
            if callable(回调):
                回调()
        轮次钮.addEventListener('click',切换轮次)
        调用钮=文档.createElement('button')
        调用钮.setAttribute('type','button')
        调用钮.className='action'
        调用文案='展开所有调用' if 调用收起 else '收起所有调用'
        调用钮.setAttribute('aria-label',调用文案)
        调用钮.setAttribute('aria-pressed','true' if 调用收起 else 'false')
        调用钮.setAttribute('title',调用文案)
        调用标=文档.createElement('span')
        调用标.className='actionIcon'
        调用标.setAttribute('aria-hidden','true')
        调用标.textContent='⊞' if 调用收起 else '⊟'
        调用钮.appendChild(调用标)
        调用钮.appendChild(文档.createTextNode('调用'))
        def 切换调用(_事件):
            '展开或收起全部助手下的工具调用'
            回调=属性.get('onToggleAllAssistants')
            if callable(回调):
                回调()
        调用钮.addEventListener('click',切换调用)
        动作.appendChild(时长钮)
        动作.appendChild(时间钮)
        动作.appendChild(轮次钮)
        动作.appendChild(调用钮)
        搜索=文档.createElement('div')
        搜索.className='search'
        图=描边图标({
            'window':窗口,
            'size':11,
            'className':'searchIcon',
        },'0 0 16 16',[
            'M6.58727 11.8586C9.55061 11.8586 11.9529 9.45637 11.9529 6.49304C11.9529 3.5297 9.55061 1.12744 6.58727 1.12744C3.62394 1.12744 1.22168 3.5297 1.22168 6.49304C1.22168 9.45637 3.62394 11.8586 6.58727 11.8586Z',
            'M10.2991 10.3933L14.7783 14.8725',
        ],16,1)
        搜索.appendChild(图)
        框=文档.createElement('input')
        框.setAttribute('type','search')
        框.className='searchInput'
        框.setAttribute('aria-label','搜索轨迹')
        框.setAttribute('placeholder','搜索')
        框.value=查询
        def 改查询(事件):
            '把输入交给宿主'
            回调=属性.get('onSearchQueryChange')
            if callable(回调):
                回调(事件.currentTarget.value)
        框.addEventListener('input',改查询)
        搜索.appendChild(框)
        内.appendChild(动作)
        内.appendChild(搜索)
        根.appendChild(内)
        自身.根=根
        if 父 is None and 属性.get('parent') is not None:
            父=属性['parent']
        if 父 is not None and 根.parentNode is not 父:
            父.appendChild(根)
        return 根
