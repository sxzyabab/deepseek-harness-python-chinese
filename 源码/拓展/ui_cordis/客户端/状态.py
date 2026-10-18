'从宿主清单和本页已加载集合推导看得见的三种状态'

__all__=['取包','可见状态']

def 取包(行,包标识):
    '在插件行里找出这个不可变包。没有则是 None'
    for 包 in 行['packages']:#逐个包
        if 包['packageId']==包标识:#同一包
            return 包#命中
    return None#没有

def 可见状态(行,包标识,已加载):
    'idle、client-pending 或 running。已加载是本页现场行'
    运行=行.get('activeRun')#当前激活
    if 运行 is None or 运行.get('packageId')!=包标识:#不是这个包在跑
        return 'idle'#待激活
    包=取包(行,包标识)#包元数据
    if 包 is None or 包.get('hasClientHalf') is not True:#没有客户端半
        return 'running'#宿主半即算在跑
    运行号=运行.get('pluginRunId')#这次激活
    for 现场 in 已加载:#本页已加载
        if 现场.get('pluginId')==行['pluginId'] and 现场.get('packageId')==包标识 and 现场.get('pluginRunId')==运行号:#同一激活
            return 'running'#两端都在
    return 'client-pending'#宿主已起，客户端还没接上
