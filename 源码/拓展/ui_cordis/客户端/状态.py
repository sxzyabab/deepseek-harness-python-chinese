"""宿主清单与本页客户端活动上的共享状态推导。

对齐上游 `ui-cordis/src/client/status.ts`。公开面仅中文名。
"""

__all__=['取包','可见状态']#仅中文公开名

def 取包(行,包标识):
    """在插件行里定位不可变包。行与包均为 dict。"""
    if 行 is None or 'packages' not in 行 or 行['packages'] is None:#没有包表
        return None#缺席
    for 包 in 行['packages']:#逐包
        if 'packageId' in 包 and 包['packageId']==包标识:#命中
            return 包#包
    return None#缺席

def 可见状态(行,包标识,已加载):
    """idle / client-pending / running。行、跑、包、活均为 dict。"""
    跑=行['activeRun'] if 行 is not None and 'activeRun' in 行 else None#当前激活
    if 跑 is None or 'packageId' not in 跑 or 跑['packageId']!=包标识:#没跑这个包
        return 'idle'#空闲
    包=取包(行,包标识)#包元
    if 包 is None or 'hasClientHalf' not in 包 or 包['hasClientHalf'] is not True:#无客户端半
        return 'running'#宿主跑即在跑
    行插件=行['pluginId'] if 'pluginId' in 行 else None#行上的插件 id
    跑标识=跑['pluginRunId'] if 'pluginRunId' in 跑 else None#运行 id
    if 已加载 is None:#本页没有已加载表
        return 'client-pending'#等客户端
    for 活 in 已加载:#本页已加载
        活插件=活['pluginId'] if 'pluginId' in 活 else None#活插件
        活包=活['packageId'] if 'packageId' in 活 else None#活包
        活运行=活['pluginRunId'] if 'pluginRunId' in 活 else None#活运行
        if 活插件==行插件 and 活包==包标识 and 活运行==跑标识:#同一激活
            return 'running'#已加载
    return 'client-pending'#等客户端
