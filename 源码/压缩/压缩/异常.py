class 压缩错误(Exception):
    '压缩包的异常基类'

class 手动压缩错误(压缩错误):
    """适合直接作为人类命令结果的预期手动压缩失败。
    共享耐久锁入口断言也可能从自动压缩路径抛出 busy 子类"""
    def __init__(自身,码,消息,选项=None):
        """创建一次已分类的压缩失败。
        code 为稳定失败类别；busy 可来自任一压缩入口路径。
        message 为后端诊断。
        选项可带 cause"""
        super().__init__(消息)#交给 Exception
        自身.code=码#失败类别
        自身.message=消息#诊断消息
        自身.name='ManualCompactionError'#错误名
        if isinstance(选项,dict) and 'cause' in 选项 and 选项['cause'] is not None:#可选原始失败
            自身.cause=选项['cause']#保留原始失败供诊断
            自身.__cause__=选项['cause']#Python 异常链

class 工具配对错误(Exception):
    '压缩工具配对包的异常基类'
