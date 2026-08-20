"""宿主清单与本页客户端活动上的共享状态推导。

对齐上游 `ui-cordis/src/client/status.ts`。公开面仅中文名。
"""

__all__=['取包','可见状态']#仅中文公开名

def 取字段(对象,键,缺省=None):#读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

def 取包(行,包标识):#按包 id 查找
    """在插件行里定位不可变包。"""
    for 包 in 取字段(行,'packages') or []:#逐包
        if 取字段(包,'packageId')==包标识:#命中
            return 包#包
    return None#缺席

def 可见状态(行,包标识,已加载):#三种可见读数
    """idle / client-pending / running。"""
    跑=取字段(行,'activeRun')#当前激活
    if 跑 is None or 取字段(跑,'packageId')!=包标识:#没跑这个包
        return 'idle'#空闲
    包=取包(行,包标识)#包元
    if 取字段(包,'hasClientHalf') is not True:#无客户端半
        return 'running'#宿主跑即在跑
    for 活 in 已加载 or []:#本页已加载
        if (取字段(活,'pluginId')==取字段(行,'pluginId')
            and 取字段(活,'packageId')==包标识
            and 取字段(活,'pluginRunId')==取字段(跑,'pluginRunId')):#同一激活
            return 'running'#已加载
    return 'client-pending'#等客户端
