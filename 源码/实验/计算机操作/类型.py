'与求值器所有权和持久化无关的原生应用程序对象'
__all__=['应用程序句柄','快照标识','观察汇聚端','观察选项','辅助功能选项']

应用程序句柄=str#辅助进程发出的应用程序选择
快照标识=str#辅助进程发出的辅助功能观察身份

class 观察汇聚端:
    '调用方拥有的可选输出。持久化与图像准入在外部'

    def __init__(自身,text,image):
        '记下文本和图像两个发出函数'
        自身._text=text#文本发出
        自身._image=image#图像发出

    def text(自身,值):
        '发出观察到的应用程序状态文本'
        return 自身._text(值)

    def image(自身,截图):
        '发出已校验的编码图像'
        return 自身._image(截图)

class 观察选项:
    '观察默认发出。返回值不受此选项影响'

    def __init__(自身,emit=True):
        '缺省发出'
        自身.emit=emit#为假则只返回、不发给汇聚端

class 辅助功能选项(观察选项):
    '完整观察请求的内容。每次读取替换该表面的索引'

    def __init__(自身,emit=True,disableDiffing=None,includeMenus=None,details=None):
        '菜单默认折叠，细节默认省略'
        super().__init__(emit)#发出开关
        自身.disableDiffing=disableDiffing#保留的兼容选项，观察从不是差分
        自身.includeMenus=includeMenus#展开菜单内容
        自身.details=details#标识、全局点边界和完整动作名
