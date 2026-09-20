__all__=[
    '资源状态_无',
    '资源状态_加载中',
    '资源状态_存活',
    '资源状态_失败',
    '资源提供方字段',
    '资源提供方打开上下文字段',
    '资源提供方',
    '资源服务协议',
    '使用资源',
]

资源状态_无='none'#无提供方或非资源地址
资源状态_加载中='loading'#提供方已开流尚未产出
资源状态_存活='live'#最新 ok 帧的值
资源状态_失败='failed'#最新帧报告失败

资源提供方字段=('protocol','open')#必填键
资源提供方打开上下文字段=('signal',)#open 第二参 dict 键；signal 为 threading.Event

class 资源提供方:
    """经 resources.登记 注册的 dict 形态说明；本类不参与运行时。"""
    protocol=None#协议键，对应 URL host

    def open(自身,地址,上下文):
        """产出远程结果帧的同步可迭代；中止后必须停止。"""
        raise NotImplementedError('ResourceProvider.open')#协议形状说明，运行时走 dict.open

class 资源服务协议:
    """resources 服务约定：协议提供方、钉住与按地址活源。"""
    def 登记(自身,提供方):
        """登记一协议提供方，返回幂等拆除器。"""
        raise NotImplementedError('Resources.register')#由资源注册表实现

    def 钉住(自身,地址,信号):
        """信号中止前保持打开；已中止的信号钉不住。"""
        raise NotImplementedError('Resources.pin')#由资源注册表实现

    def 取源(自身,地址):
        """返回带 getSnapshot/subscribe 的可观察快照。"""
        raise NotImplementedError('Resources.source')#由资源注册表实现

def 使用资源(注册表,地址):
    """同步读取一地址当前快照；不持有资源。

    要钉住并接收更新，请对注册表.取源(地址) 调用 subscribe，
    或经槽位根 keyedHooks resource 由渲染器合成标准钩子。
    """
    return 注册表.取源(地址).getSnapshot()
