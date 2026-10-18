'标签的上下文菜单。次键打开。没有条目时不画弹出层。按在外面或单独的 Escape 会关掉，并把焦点还给标签'
import pywebbridge
from ...ui_基础界面组件.焦点 import 无轮廓聚焦
from ...ui_基础界面组件.模态层 import 模态选择器
from ...ui_基础界面组件.键盘合成 import 观察合成
from .渲染 import 挂上,注入样式

__all__=['标签菜单']

class 标签菜单:
    '挂在打开它的控件下面。门户放到 document.body，避免被条带裁掉'
    def __init__(自身,属性):
        '记下锚点和关闭方式并画出'
        自身.属性=属性
        自身.根=None
        自身.合成=None
        自身.拆键=None
        自身.拆指针=None
        自身.渲染()

    def 有条目(自身):
        '关闭项或嵌入方附加项里，至少有一个真正的条目'
        if 自身.属性.get('onClose') is not None:
            return True
        附加=自身.属性.get('extras')
        if 附加 is None or 附加=='' or 附加 is False:
            return False
        if isinstance(附加,(list,tuple)):
            for 项 in 附加:
                if 项 is not None and 项!='' and 项 is not False:
                    return True
            return False
        return True

    def 摆放(自身):
        '先藏着量宽度，再放到控件下方。靠右会超出视口时改对齐控件右缘'
        锚盒=自身.属性['anchor'].getBoundingClientRect()
        宽=自身.根.offsetWidth
        间隙=4
        窗口=自身.属性['window']
        if 锚盒.left+宽+间隙>窗口.innerWidth:
            左=max(间隙,锚盒.right-宽)
        else:
            左=锚盒.left
        自身.根.style.top=f'{锚盒.bottom+间隙}px'
        自身.根.style.left=f'{左}px'
        自身.根.style.visibility='visible'

    def 卸听(自身):
        '卸掉键盘、指针和合成观察'
        if 自身.合成 is not None:
            自身.合成['dispose']()
            自身.合成=None
        if 自身.拆键 is not None:
            自身.拆键()
            自身.拆键=None
        if 自身.拆指针 is not None:
            自身.拆指针()
            自身.拆指针=None

    def 渲染(自身):
        '有条目才把门户挂到 body'
        窗口=自身.属性['window']
        文档=窗口.document
        注入样式(文档)
        if not 自身.有条目():
            自身.拆除()
            return None
        if 自身.根 is None:
            自身.根=文档.createElement('div')
            自身.根.className='menu'
            自身.根.setAttribute('role','menu')
            自身.根.setAttribute('data-dockkit-tab-menu','')
            自身.根.setAttribute('data-menu-material','translucent')
            自身.根.style.visibility='hidden'
            自身.根.style.top='0px'
            自身.根.style.left='0px'
            材料=文档.createElement('div')
            材料.setAttribute('aria-hidden','true')
            材料.style.position='absolute'
            材料.style.inset='0'
            材料.style.zIndex='-1'
            材料.style.borderRadius='inherit'
            材料.style.background='var(--dsw-menu-surface-fill)'
            材料.style.backdropFilter='var(--dsw-menu-backdrop-filter)'
            材料.style.pointerEvents='none'
            自身.根.appendChild(材料)
            文档.body.appendChild(自身.根)

            def 按下(事件):
                '菜单上的按下停在这里，避免变成标签拖拽'
                事件.stopPropagation()

            def 点击(事件):
                '菜单上的点击停在这里，避免再去聚焦标签'
                事件.stopPropagation()

            自身.根.addEventListener('pointerdown',按下)
            自身.根.addEventListener('click',点击)
        else:
            留=[]
            子=自身.根.firstChild
            while 子 is not None:
                下一=子.nextSibling
                if 子.getAttribute('aria-hidden')!='true':
                    留.append(子)
                子=下一
            for 节点 in 留:
                节点.remove()
        关闭=自身.属性.get('onClose')
        if 关闭 is not None:
            钮=文档.createElement('button')
            钮.setAttribute('type','button')
            钮.setAttribute('role','menuitem')
            钮.className='menuItem'
            钮.setAttribute('data-dockkit-menu-close','')
            钮.textContent=自身.属性['labels']['closeTab']

            def 点关闭(事件):
                '执行关闭'
                事件.stopPropagation()
                关闭()

            钮.addEventListener('click',点关闭)
            自身.根.appendChild(钮)
        if 'extras' in 自身.属性:
            挂上(自身.根,自身.属性['extras'])
        自身.摆放()
        自身.装听()
        return 自身.根

    def 装听(自身):
        'Escape 和无元素目标的按下都算在菜单外面'
        if 自身.拆键 is not None:
            return
        窗口=自身.属性['window']
        文档=自身.根.ownerDocument
        菜单=自身.根
        锚=自身.属性['anchor']
        解散=自身.属性['onDismiss']
        自身.合成=观察合成(文档)

        def 按键(事件):
            '没修饰的 Escape，且本菜单在最上面，才关'
            if 自身.合成['guards'](事件) or 事件.defaultPrevented or 事件.key!='Escape':
                return
            if 事件.ctrlKey or 事件.altKey or 事件.metaKey or 事件.shiftKey:
                return
            顶=文档.querySelectorAll(模态选择器)
            if len(顶)==0 or 顶[len(顶)-1] is not 菜单:
                return
            事件.preventDefault()
            if 事件.repeat:
                return
            活动=文档.activeElement
            要还=活动 is not None and 菜单.contains(活动)
            解散()
            if 要还:
                无轮廓聚焦(锚)

        def 外按(事件):
            '点在菜单里不算外面。没有元素目标也算外面'
            目标=事件.target
            if 目标 is not None and hasattr(目标,'nodeType') and 菜单.contains(目标):
                return
            解散()

        文档.addEventListener('keydown',按键,True)
        窗口.addEventListener('pointerdown',外按,True)

        def 拆键():
            '卸键盘'
            文档.removeEventListener('keydown',按键,True)

        def 拆指针():
            '卸按下'
            窗口.removeEventListener('pointerdown',外按,True)

        自身.拆键=拆键
        自身.拆指针=拆指针

    def 更新(自身,属性):
        '锚点或条目变了就重画'
        自身.卸听()
        自身.属性=属性
        return 自身.渲染()

    def 拆除(自身):
        '卸监听并把门户从 body 拿掉'
        自身.卸听()
        if 自身.根 is not None:
            自身.根.remove()
            自身.根=None
