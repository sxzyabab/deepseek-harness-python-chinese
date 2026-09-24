__all__=['预设注册表错误','远程错误']

class 预设注册表错误(Exception):
    """本包异常基类。"""

class 远程错误(预设注册表错误):
    """带码与详情的远程失败。"""
    def __init__(自身,码,消息,详情=None):
        """记下码、消息与详情。"""
        super().__init__(消息)
        自身.code=码
        自身.message=消息
        自身.details={} if 详情 is None else 详情
