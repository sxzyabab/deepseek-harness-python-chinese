from ....模块.客户端.通告 import 取握手窗口
from .浏览器呈现形式 import 确保浏览器样式,标浏览器

__all__=['网页沙箱令牌','内嵌帧呈现形式']

网页沙箱令牌='allow-scripts allow-forms allow-same-origin allow-popups allow-popups-to-escape-sandbox'


class 内嵌帧呈现形式:
    '持有内嵌帧元素。导航和历史留在内嵌帧实现里'

    def __init__(自身,事件):
        '记下加载和重新挂载回调'
        自身.事件=事件
        自身.宿主=None
        自身.元素=None
        自身.文档=None
        自身.已绘=False

    def 挂载(自身,视口标识):
        '把帧放进已提交的视口。返回的函数只摘掉这一次附着'
        文档=取握手窗口().document
        确保浏览器样式(文档)
        宿主=文档.getElementById(视口标识)
        if 宿主 is None:
            raise RuntimeError('iframe presentation: viewport is not mounted')
        if 自身.元素 is not None:
            自身.元素.remove()
        自身.元素=None
        自身.宿主=宿主
        if 自身.已绘:
            自身.事件['remounted']()
        else:
            自身.绘制()

        def 摘掉(这次=宿主):
            '只摘掉还挂在这次容器上的帧'
            if 自身.宿主 is not 这次:
                return
            if 自身.元素 is not None:
                自身.元素.remove()
            自身.元素=None
            自身.宿主=None

        return 摘掉

    def 展示(自身,值):
        '记下准备好的文档，容器在的时候就画出来'
        自身.文档=值
        自身.绘制()

    def 拆除(自身):
        '去掉元素和留下的呈现数据'
        if 自身.元素 is not None:
            自身.元素.remove()
        自身.元素=None
        自身.宿主=None
        自身.文档=None

    def 绘制(自身):
        '文档和容器都在时重建内嵌帧'
        当前=自身.文档
        宿主=自身.宿主
        if 当前 is None or 宿主 is None:
            return
        if 自身.元素 is not None:
            自身.元素.remove()
        文档=取握手窗口().document
        元素=文档.createElement('iframe')
        标浏览器(元素,'frame')
        元素.src=当前['target']['url']
        元素.title=当前['target']['title']
        元素.referrerPolicy='no-referrer'
        元素.setAttribute('data-sidebar-browser-frame','iframe')
        if 当前['sandboxed']:
            元素.setAttribute('sandbox',网页沙箱令牌)
        修订=当前['revision']

        def 加载完(事件,帧=元素,代=修订):
            '只认还挂着的这一代'
            if 自身.元素 is 帧:
                自身.事件['loaded'](代)

        def 加载失败(事件,帧=元素,代=修订):
            '只认还挂着的这一代'
            if 自身.元素 is 帧:
                自身.事件['failed'](代)

        元素.addEventListener('load',加载完)
        元素.addEventListener('error',加载失败)
        自身.元素=元素
        自身.已绘=True
        宿主.append(元素)
