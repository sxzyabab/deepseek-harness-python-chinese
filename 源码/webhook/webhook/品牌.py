"""webhook 不透明身份。对齐上游 `webhook/src/brand.ts`。"""
from ...工具.品牌 import 带品牌#品牌原语

def Webhook规则标识(值):#品牌化规则id
    """为 webhook 规则 id 打品牌。"""
    return 带品牌(值)#原样品牌

def Webhook来源标识(值):#品牌化来源id
    """为 webhook 适配器实例 id 打品牌。"""
    return 带品牌(值)#原样品牌

def Webhook投递标识(值):#品牌化投递id
    """为 provider delivery id 打品牌。"""
    return 带品牌(值)#原样品牌

__all__=['Webhook规则标识','Webhook来源标识','Webhook投递标识']#公开面
