__all__=['取包','可见状态']#仅中文公开名

def 取包(行,包标识):
    '在插件行里定位不可变包。行与包均为 dict'
    if 行 is None or 'packages' not in 行 or 行['packages'] is None:
        return None
    for 包 in 行['packages']:
        if 'packageId' in 包 and 包['packageId']==包标识:
            return 包
    return None

def 可见状态(行,包标识,已加载):
    'idle / client-pending / running。行、当前运行、包、活均为 dict'
    当前运行=行['activeRun'] if 行 is not None and 'activeRun' in 行 else None
    if 当前运行 is None or 'packageId' not in 当前运行 or 当前运行['packageId']!=包标识:
        return 'idle'
    包=取包(行,包标识)
    if 包 is None or 'hasClientHalf' not in 包 or 包['hasClientHalf'] is not True:
        return 'running'#宿主跑即在跑
    行插件=行['pluginId'] if 'pluginId' in 行 else None
    运行标识=当前运行['pluginRunId'] if 'pluginRunId' in 当前运行 else None#运行 id
    if 已加载 is None:#本页没有已加载表
        return 'client-pending'
    for 活 in 已加载:
        活插件=活['pluginId'] if 'pluginId' in 活 else None
        活包=活['packageId'] if 'packageId' in 活 else None
        活运行=活['pluginRunId'] if 'pluginRunId' in 活 else None
        if 活插件==行插件 and 活包==包标识 and 活运行==运行标识:
            return 'running'
    return 'client-pending'
