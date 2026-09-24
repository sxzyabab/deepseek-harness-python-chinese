"""插件导出与惰性构建边界上的身份检查。"""

__all__=['是否原生配置数据架构']

def 是否原生配置数据架构(值):
    """识别原生 Schemastery 图协议，不调用校验器或序列化钩。"""
    if 值 is None:
        return False
    类型=getattr(值,'type',None)
    元=getattr(值,'meta',None)
    return isinstance(类型,str) and 元 is not None and isinstance(元,dict)
