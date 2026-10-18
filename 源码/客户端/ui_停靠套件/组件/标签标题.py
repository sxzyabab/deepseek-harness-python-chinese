'芯片标题：一行，在芯片内边被裁切，不用省略号。裁切标记直接写在节点上'
import pywebbridge
from .渲染 import 清空,挂上

__all__=['标签标题']

class 标签标题:
    '条带芯片或浮动页眉上的标题'
    def __init__(自身,属性):
        '记下子节点并画出标题'
        自身.属性=属性
        自身.根=None
        自身.观察=None
        自身.渲染()

    def 标裁切(自身):
        '按现在的宽，决定要不要挂上 data-dockkit-tab-clipped。超过一整像素才算裁切'
        元素=自身.根
        if 元素 is None:
            return
        if 元素.scrollWidth>元素.clientWidth+1:
            元素.setAttribute('data-dockkit-tab-clipped','')
        else:
            元素.removeAttribute('data-dockkit-tab-clipped')

    def 渲染(自身):
        '画出或换上标题内容，并重新量裁切'
        窗口=自身.属性['window']
        文档=窗口.document
        if 自身.根 is None:
            自身.根=文档.createElement('span')
            自身.根.className='tabTitle'
            自身.根.setAttribute('data-dockkit-tab-title','')
        else:
            清空(自身.根)
        if 'children' in 自身.属性:
            挂上(自身.根,自身.属性['children'])
        自身.标裁切()
        if 自身.观察 is None and hasattr(窗口,'ResizeObserver'):
            def 变了():
                '盒子变了就重标裁切'
                自身.标裁切()
            自身.观察=窗口.ResizeObserver(变了)
            自身.观察.observe(自身.根)
        return 自身.根

    def 更新(自身,属性):
        '换内容后再画'
        自身.属性=属性
        return 自身.渲染()

    def 拆除(自身):
        '卸掉尺寸观察'
        if 自身.观察 is not None:
            自身.观察.disconnect()
            自身.观察=None
