from ..模块.客户端.通告 import 取握手窗口
import os
from ..ui_对话.异常 import 注入模块样式文件,标样式模块

__all__=['分段控制']

样式模块='segmented'

def 是行走键(键):
    '左右上下和 Home、End'
    return 键 in ('ArrowLeft','ArrowRight','ArrowUp','ArrowDown','Home','End')

def 走向(选项,起点,键):
    '走到下一个没禁用的段。Home、End 跳到两端'
    可用=[]
    for 项 in 选项:
        if 项.get('disabled') is not True:
            可用.append(项)
    if 键=='Home':
        if len(可用)>0:
            return 可用[0]
        return None
    if 键=='End':
        if len(可用)>0:
            return 可用[-1]
        return None
    步=1 if 键 in ('ArrowRight','ArrowDown') else -1
    总数=len(选项)
    偏移=1
    while 偏移<总数:
        下标=((起点+步*偏移)%总数+总数)%总数
        候选=选项[下标]
        if 候选.get('disabled') is not True:
            return 候选
        偏移=偏移+1
    return None

class 分段控制:
    '等宽分段。选中段下面有一块滑块'
    def __init__(自身,属性=None):
        '记下选项和当前值'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.根=None

    def 渲染(自身):
        '画出 tablist。方向键只改值，焦点跟随后一次选中'
        if 自身.根 is not None:
            自身.根.remove()
        属性=自身.属性
        窗口=属性['window'] if 'window' in 属性 else 取握手窗口()
        文档=窗口.document
        注入模块样式文件(文档,'分段控制样式',os.path.join(os.path.dirname(__file__),'分段控制.module.css'),样式模块)
        选项=属性['options'] if isinstance(属性.get('options'),(list,tuple)) else []
        值=属性.get('value')
        选中=0
        序=0
        for 项 in 选项:
            if 项.get('value')==值:
                选中=序
            序=序+1
        根=文档.createElement('div')
        根.className='control'
        附加=属性.get('className')
        if isinstance(附加,str) and 附加!='':
            根.className=根.className+' '+附加
        标样式模块(根,样式模块)
        根.setAttribute('role','tablist')
        根.setAttribute('aria-label','' if 属性.get('label') is None else str(属性['label']))
        根.style.setProperty('--dsh-segment-count',str(len(选项)))
        根.style.setProperty('--dsh-segment-index',str(选中))
        滑=文档.createElement('span')
        滑.setAttribute('aria-hidden','true')
        滑.className='indicator'
        标样式模块(滑,样式模块)
        根.appendChild(滑)
        全禁=属性.get('disabled') is True
        标识=属性.get('id')
        def 按键(事件):
            '走到下一段并交给 onChange'
            if not 是行走键(事件.key):
                return
            事件.preventDefault()
            目标=走向(选项,选中,事件.key)
            if 目标 is not None and 目标.get('value')!=值:
                改=属性.get('onChange')
                if 改 is not None:
                    改(目标['value'])
        for 项 in 选项:
            活=项.get('value')==值
            钮=文档.createElement('button')
            钮.type='button'
            钮.className='tab'
            标样式模块(钮,样式模块)
            钮.id=str(标识)+'-'+str(项.get('value'))
            钮.setAttribute('role','tab')
            钮.setAttribute('aria-selected','true' if 活 else 'false')
            钮.setAttribute('aria-controls',str(标识)+'-'+str(项.get('value'))+'-panel')
            钮.tabIndex=0 if 活 else -1
            钮.disabled=全禁 or 项.get('disabled') is True
            if 'title' in 项 and 项['title'] is not None:
                钮.title=str(项['title'])
            钮.textContent='' if 项.get('label') is None else str(项['label'])
            def 点下(事件,项=项,活=活):
                '没选中才换'
                if 活:
                    return
                改=属性.get('onChange')
                if 改 is not None:
                    改(项.get('value'))
            钮.addEventListener('click',点下)
            钮.addEventListener('keydown',按键)
            根.appendChild(钮)
        if 'parent' in 属性 and 属性['parent'] is not None:
            属性['parent'].appendChild(根)
        自身.根=根
        return 根
