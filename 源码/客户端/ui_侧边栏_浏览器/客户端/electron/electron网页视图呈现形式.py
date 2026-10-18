from ....模块.客户端.通告 import 取握手窗口
from ..视图.浏览器呈现形式 import 确保浏览器样式,标浏览器

__all__=['electron网页视图呈现形式']


class electron网页视图呈现形式:
    '在侧栏内容容器里创建和附着 webview，不跟着别的元素量位置'

    def __init__(自身,事件):
        '记下附着和脱离回调'
        自身.事件=事件
        自身.元素=None
        自身.宿主=None

    def 挂载(自身,视口标识):
        '附着到已提交的内容容器。返回的函数结束附着并放开宾客'
        文档=取握手窗口().document
        确保浏览器样式(文档)
        宿主=文档.getElementById(视口标识)
        if 宿主 is None:
            raise RuntimeError('Electron presentation: content container is not mounted')
        if 自身.宿主 is not None:
            自身.事件['unmounted']()
        自身.宿主=宿主
        自身.事件['mounted']()

        def 摘掉(这次=宿主):
            '只结束还挂在这次容器上的附着'
            if 自身.宿主 is not 这次:
                return
            自身.事件['unmounted']()
            自身.宿主=None

        return 摘掉

    def 造元素(自身,预约):
        '按已批准的宾客预约配置一个尚未附着的 webview'
        文档=取握手窗口().document
        确保浏览器样式(文档)
        元素=文档.createElement('webview')
        标浏览器(元素,'webview')
        元素.setAttribute('data-sidebar-browser-frame','webview')
        元素.setAttribute('name',预约['lease'])
        元素.setAttribute('partition',预约['partition'])
        元素.setAttribute('allowpopups','')
        元素.setAttribute('src','about:blank#'+str(预约['lease']))
        return 元素

    def 呈现(自身,元素):
        '把准备好的宾客放进容器，并去掉上一个宾客'
        if 自身.宿主 is None:
            raise RuntimeError('Electron presentation: cannot attach without a content container')
        自身.清空()
        自身.元素=元素
        自身.宿主.append(元素)

    def 展示(自身,标题):
        '把观察到的文档标题写成无障碍名称'
        if 自身.元素 is not None:
            自身.元素.setAttribute('aria-label',标题)

    def 清空(自身):
        '只拆掉宾客节点，容器可以继续留给下一个'
        if 自身.元素 is not None:
            自身.元素.remove()
        自身.元素=None

    def 拆除(自身):
        '拆掉宾客节点并放开内容容器'
        自身.清空()
        自身.宿主=None
