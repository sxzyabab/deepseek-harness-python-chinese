"""配置档装载操作共用的可本地化拒绝。"""
from .类型 import 装载错误码#错误码联合

__all__=['装载失败']#仅中文公开名

class 装载失败(Exception):
    """预期的装载拒绝；呈现交给调用方词典。"""
    def __init__(自身,码):
        """记下可本地化拒绝码；消息原样为码字符串。"""
        super().__init__(码)#英文消息即码
        自身.code=码#ManagementError.code
