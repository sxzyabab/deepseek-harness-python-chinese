from ...依赖.工具 import 聚合错误#搭建与清理双失败的聚合基类

class 终端错误(Exception):#带稳定错误码的错误
    '携带稳定 TerminalErrorCode 的错误'
    def __init__(自身,消息,码=None):#记下消息与可选码
        '记下可读消息与稳定码'
        super().__init__(消息)#交给Exception
        自身.name='TerminalError'#固定类名
        if 码 is not None:#有稳定码
            自身.code=码#稳定失败码

class 终端后端清理错误(聚合错误):#后端搭建与清理双失败
    '未发布的搭建失败后，后端报告清理部分资源失败'
    def __init__(自身,搭建错误,清理错误):#同时携带搭建失败与清理失败
        '记下原始搭建失败与清理失败'
        super().__init__([搭建错误,清理错误],'PTY backend startup and cleanup both failed')#两条失败聚合成一条
        自身.搭建错误=搭建错误#原始搭建或取消失败
        自身.清理错误=清理错误#可能让后端拥有的资源仍活着的失败
        自身.name='TerminalBackendCleanupError'#固定类名
