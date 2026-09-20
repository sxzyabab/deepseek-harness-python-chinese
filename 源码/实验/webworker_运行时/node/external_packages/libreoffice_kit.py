from ..未实现失败 import 不可用错误

__all__=['创建转换器']

def 创建转换器():
    """以 kit 的 unavailable 错误码拒绝创建转换器。"""
    错误=不可用错误('@deepseek-ai/libreoffice-kit','createConverter')
    错误.code='unavailable'
    raise 错误
