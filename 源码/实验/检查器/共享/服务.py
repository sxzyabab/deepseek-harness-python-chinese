"""Host 与 Client 插件面共用的 Cordis 服务 API。

对齐上游 `shared/service.ts`。公开面仅中文名。
"""
from .桥接.查询读取器 import 创建查询cordis运行时树读取器#查询读取器

__all__=['检查器服务','创建检查器服务']#仅中文公开名

class 检查器服务:#检查器服务门面
    """覆盖界域源发布器的共享 Host/Client 服务门面。"""
    def __init__(自身,发布,cordis):#构造
        """保存发布与 Cordis 只读面。"""
        自身._发布=发布#发布回调
        自身.cordis=cordis#Cordis只读面

    def 发布(自身,topic,payload,monotonicMs=None):#发布观测
        """发布一条 JSON 观测，不等待 Worker 投递。"""
        自身._发布(topic,payload,monotonicMs)#转发发布

def 创建检查器服务(连接):#创建服务门面
    """创建共享服务门面，不暴露载体实现。"""
    return 检查器服务(#门面对象
        lambda topic,payload,monotonicMs=None:连接.发布(topic,payload,monotonicMs),#转发发布
        创建查询cordis运行时树读取器(连接),#查询只读Cordis
    )#返回结束
