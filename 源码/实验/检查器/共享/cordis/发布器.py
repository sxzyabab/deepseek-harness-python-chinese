"""Host/Client 共用的浏览器安全 Cordis 快照发布。

对齐上游 `shared/cordis/publisher.ts`。公开面仅中文名。
"""
from ..桥接.消息.cordis import cordis树主题#主题
from .观察者 import 观察cordis树#观察

__all__=['发布cordis树']#仅中文公开名

def 发布cordis树(上下文,发布器,上限):#发布Cordis树
    """观察一个 Cordis 运行时并保留其最新源快照。"""
    def 写入(快照):#观察并写状态
        """写入主题状态。"""
        发布器.设置状态(cordis树主题,快照)#写入主题状态
    return 观察cordis树(上下文,写入,上限)#带上限
