__all__=['electron网页视图呈现形式']

class electron网页视图呈现形式:
    """宿主容器内的桌面网页视图标签。"""
    def __init__(自身,事件):
        自身.事件=事件
        自身.元素=None
        自身.宿主=None

    def 挂载(自身,视口标识):
        if 自身.宿主 is not None:
            自身.事件['unmounted']()
        自身.宿主=视口标识
        自身.事件['mounted']()
        def 卸():
            if 自身.宿主!=视口标识:
                return
            自身.事件['unmounted']()
            自身.宿主=None
        return 卸

    def 创建元素(自身,预约):
        return {
            'partition':预约['partition'],
            'lease':预约['lease'],
            'src':'about:blank#'+str(预约['lease']),
        }

    def 呈现(自身,元素):
        if 自身.宿主 is None:
            raise RuntimeError('Electron presentation: cannot attach without a content container')
        自身.清空()
        自身.元素=元素

    def 展示(自身,标题):
        if 自身.元素 is not None:
            自身.元素['aria-label']=标题

    def 清空(自身):
        自身.元素=None

    def 拆除(自身):
        自身.清空()
        自身.宿主=None

    mount=挂载
    createElement=创建元素
    present=呈现
    show=展示
    clear=清空
    dispose=拆除
