'检查器自己的 DOM 定位和原生滚动，没有 Conversation 请求通道'

from .文档对象 import 已显示,查找聊天目标,矩形字典
from .高亮 import 放置聊天高亮,可见聊天矩形

__all__=['检查器聊天定位器']

滚动安静毫秒=150
滚动键={'ArrowUp','ArrowDown','PageUp','PageDown','Home','End',' ','Escape'}

def 有渲染盒(元素):
    '已显示且宽高都大于 0'
    if not 已显示(元素):
        return False
    盒=矩形字典(元素.getBoundingClientRect())
    return 盒['width']>0 and 盒['height']>0

class 检查器聊天定位器:
    '拥有一次延后定位和 body 层闪烁，不修改 Chat 内容节点'
    def __init__(自身,取根):
        '取根返回当前会话已显示的主 Chat，没有时为 None'
        自身._取根=取根
        自身._帧=None
        自身._覆盖=None
        自身._动画=None
        自身._取消滚动=None

    def 定位(自身,目标表):
        '定位第一个可用出现，否则退到已显示的 Chat 列'
        自身.拆除()
        def 帧():
            '下一帧里查找并滚动或闪烁'
            自身._帧=None
            根=自身._取根()
            if 根 is None:
                return
            for 初始 in 查找聊天目标(根,目标表):
                if not 根.contains(初始):
                    continue
                隐藏=[]
                元素=初始
                while 元素 is not None and 元素 is not 根:
                    if 元素.getAttribute('hidden')=='until-found':
                        隐藏.append(元素)
                    元素=元素.parentElement
                if len(隐藏)>0 or 可见聊天矩形(初始) is None:
                    滚动口=根.closest('[data-conversation-scroll]')
                    if 滚动口 is not None:
                        滚动口.dispatchEvent(Event('beforematch'))
                for 元素 in reversed(隐藏):
                    元素.dispatchEvent(Event('beforematch'))
                if 自身._取根() is not 根:
                    return
                if 根.contains(初始):
                    行=初始
                else:
                    行=None
                    for 候选 in 查找聊天目标(根,目标表):
                        if 有渲染盒(候选):
                            行=候选
                            break
                if 行 is None or not 有渲染盒(行):
                    continue
                if 可见聊天矩形(行) is None:
                    if not window.matchMedia('(prefers-reduced-motion: reduce)').matches:
                        自身._平滑滚动(行,根,目标表)
                        return
                    行.scrollIntoView({'behavior':'instant','block':'center','inline':'nearest'})
                自身._排队闪烁(行,根,目标表)
                return
            if 已显示(根) and 可见聊天矩形(根) is not None:
                自身._排队闪烁(根,根,目标表)
        自身._帧=requestAnimationFrame(帧)

    def 拆除(自身):
        '取消未完成的原生滚动，并去掉检查器自己的覆盖层'
        if 自身._帧 is not None:
            cancelAnimationFrame(自身._帧)
        自身._帧=None
        if 自身._取消滚动 is not None:
            自身._取消滚动()
        if 自身._动画 is not None:
            自身._动画.onfinish=None
            自身._动画.cancel()
        自身._动画=None
        if 自身._覆盖 is not None:
            自身._覆盖.remove()
        自身._覆盖=None

    def _排队闪烁(自身,行,根,目标表):
        '滚动安定后再闪；失败则试下一个候选'
        def 帧():
            '下一帧闪烁，根已换则拆除'
            自身._帧=None
            if 自身._取根() is not 根:
                自身.拆除()
                return
            if 自身._闪烁(行):
                return
            for 候选 in 查找聊天目标(根,目标表):
                if 候选 is not 行 and 自身._闪烁(候选):
                    return
            if 行 is not 根 and 自身._闪烁(根):
                return
            自身.拆除()
        自身._帧=requestAnimationFrame(帧)

    def _平滑滚动(自身,行,根,目标表):
        '平滑滚到行中部；滚动停下或被打断后结束观察'
        父级=set()
        元素=行.parentElement
        while 元素 is not None:
            父级.add(元素)
            元素=元素.parentElement
        移动=set()
        状态={'pending':True,'quiet':None,'settledFrame':None}
        def 事件目标(事件):
            '只认这条行的滚动祖先'
            目标=document.scrollingElement if 事件.target is document else 事件.target
            if isinstance(目标,Element) and 目标 in 父级:
                return 目标
            return None
        def 清理():
            '卸下滚动观察'
            状态['pending']=False
            window.clearTimeout(状态['quiet'])
            if 状态['settledFrame'] is not None:
                cancelAnimationFrame(状态['settledFrame'])
            window.removeEventListener('scroll',当滚动,True)
            window.removeEventListener('scrollend',当结束,True)
            for 种类 in ('wheel','touchstart','pointerdown','keydown'):
                window.removeEventListener(种类,打断,True)
            自身._取消滚动=None
        def 完成():
            '观察结束后排队闪烁'
            if not 状态['pending']:
                return
            清理()
            自身._排队闪烁(行,根,目标表)
        def 等安静():
            '没有 scrollend 时也在安静后放开'
            window.clearTimeout(状态['quiet'])
            状态['quiet']=window.setTimeout(完成,滚动安静毫秒)
        def 当滚动(事件):
            '祖先在滚动则重新计时'
            目标=事件目标(事件)
            if 目标 is None:
                return
            移动.add(目标)
            等安静()
        def 当结束(事件):
            '全部滚动祖先都结束后再闪'
            目标=事件目标(事件)
            if 目标 is None or 目标 not in 移动 or 状态['settledFrame'] is not None:
                return
            移动.discard(目标)
            if len(移动)>0:
                return
            def 安定帧():
                '再等一帧确认没有新的滚动'
                状态['settledFrame']=None
                if len(移动)==0:
                    完成()
            状态['settledFrame']=requestAnimationFrame(安定帧)
        def 取消():
            '停在当前位置'
            if not 状态['pending']:
                return
            清理()
            for 元素 in 父级:
                if 元素.isConnected and (元素.scrollHeight>元素.clientHeight or 元素.scrollWidth>元素.clientWidth):
                    元素.scrollTo({'top':元素.scrollTop,'left':元素.scrollLeft,'behavior':'instant'})
        def 打断(事件):
            '滚轮、触摸、指针或滚动键取消定位'
            if isinstance(事件,KeyboardEvent) and 事件.key not in 滚动键:
                return
            取消()
            自身.拆除()
        自身._取消滚动=取消
        window.addEventListener('scroll',当滚动,{'capture':True,'passive':True})
        window.addEventListener('scrollend',当结束,{'capture':True,'passive':True})
        for 种类 in ('wheel','touchstart','pointerdown','keydown'):
            window.addEventListener(种类,打断,{'capture':True,'passive':True})
        等安静()
        行.scrollIntoView({'behavior':'smooth','block':'center','inline':'nearest'})

    def _闪烁(自身,行):
        '减少动画时直接结束；否则在 body 上闪一下'
        if window.matchMedia('(prefers-reduced-motion: reduce)').matches:
            自身.拆除()
            return True
        if not 已显示(行):
            return False
        覆盖=document.createElement('div')
        if not 放置聊天高亮(覆盖,行):
            return False
        覆盖.className='chatReveal'
        覆盖.dataset.sessionInspectorHighlight='reveal'
        覆盖.setAttribute('aria-hidden','true')
        document.body.append(覆盖)
        自身._覆盖=覆盖
        动画=覆盖.animate([{'opacity':0.65},{'opacity':0.1},{'opacity':0.5},{'opacity':0}],{'duration':700})
        自身._动画=动画
        def 结束(事件=None):
            '这次动画结束才拆除'
            if 自身._动画 is 动画:
                自身.拆除()
        动画.onfinish=结束
        return True
