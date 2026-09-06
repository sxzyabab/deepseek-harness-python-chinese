"""webhook 不透明身份。对齐上游 `webhook/src/brand.ts`。"""
from ...工具.标识构造 import 标识构造#标识构造原语

def Webhook规则标识(值):#构造规则id标识
    """为 webhook 规则 id 做标识构造。"""
    return 标识构造(值)#原样标识构造

def Webhook来源标识(值):#构造来源id标识
    """为 webhook 适配器实例 id 做标识构造。"""
    return 标识构造(值)#原样标识构造

def Webhook投递标识(值):#构造投递id标识
    """为 provider delivery id 做标识构造。"""
    return 标识构造(值)#原样标识构造

__all__=['Webhook规则标识','Webhook来源标识','Webhook投递标识']#公开面
