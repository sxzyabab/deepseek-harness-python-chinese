"""观测源界域内所保留活对象的不透明引用。

对齐上游 `shared/cordis/object-reference.ts`。公开面仅中文名。
"""
from ..校验 import 精确对象,线上标识#校验

__all__=['检查器对象引用','解析检查器对象引用']#仅中文公开名

class 检查器对象引用:#对象引用
    """一个活对象的可过线身份；源世代提供界域身份。"""
    def __init__(自身,registryId,handle):#构造
        """保存对象引用字段。"""
        自身.registryId=registryId#注册表标识
        自身.handle=handle#对象句柄

def 解析检查器对象引用(值):#解析对象引用
    """解码一个源本地活对象引用。"""
    记录=精确对象(值,['registryId','handle'],'object reference')#精确对象
    return 检查器对象引用(#引用对象
        registryId=线上标识(记录['registryId'],'registryId'),#注册表标识
        handle=线上标识(记录['handle'],'handle'),#对象句柄
    )#返回结束
