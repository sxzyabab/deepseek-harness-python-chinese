"""一个已连接 Client realm 的 Worker 侧桥依赖。"""
#对齐上游 worker/realms/client/bridge.ts

__all__=['创建Client_realm桥']#仅中文公开名

def 创建Client_realm桥(目标,运行时,源):#创建Client realm桥
    """将一个 Client 源代数绑定到可寻址它的 Worker 桥服务。"""
    return {'target':目标,'runtime':运行时,'sources':源}#组装
