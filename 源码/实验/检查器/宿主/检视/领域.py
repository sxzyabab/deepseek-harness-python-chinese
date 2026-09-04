"""Host 观测源代数的稳定描述符。

对齐上游 `host/inspection/realm.ts`。公开面仅中文名。
"""
import time,uuid#时间与UUID
from ...共享.身份 import 检查器id#带品牌id工厂
from ..cdp import 桥能力#桥能力集

__all__=['创建宿主领域源']#仅中文公开名

def 创建宿主领域源(标签):#创建Host源描述
    """为一个 Host→Worker MessagePort 代数创建描述符。"""
    return {#描述符
        'sourceId':检查器id(f'host-{uuid.uuid4()}','sourceId'),#源id
        'generation':检查器id(str(uuid.uuid4()),'generation'),#代数
        'kind':'host',#种类
        'label':标签,#标签
        'timeOriginMs':time.time()*1000,#时间原点近似
        'capabilities':桥能力('',False),#能力集
    }#返回
