from ..未实现失败 import 不可用错误#不可用错误

__all__=['创建转换器']#仅中文公开名

def 创建转换器():#拒绝创建转换器
    """以 kit 的 unavailable 错误码拒绝创建转换器。"""
    错误=不可用错误('@deepseek-ai/libreoffice-kit','createConverter')#不可用诊断
    错误.code='unavailable'#线协议错误码
    raise 错误#抛出
