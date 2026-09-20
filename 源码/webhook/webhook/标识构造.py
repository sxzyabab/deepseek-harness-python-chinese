"""webhook 不透明身份的标识构造。"""
from ...工具.标识构造 import 标识构造

def Webhook规则标识(值):
    """为 webhook 规则 id 做标识构造。"""
    return 标识构造(值)

def Webhook来源标识(值):
    """为 webhook 适配器实例 id 做标识构造。"""
    return 标识构造(值)

def Webhook投递标识(值):
    """为提供方投递 id 做标识构造。"""
    return 标识构造(值)

__all__=['Webhook规则标识','Webhook来源标识','Webhook投递标识']
