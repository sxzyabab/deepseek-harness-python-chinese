"""摘要 -> 带谱系缩进的扁平列表（纯函数）。

输入顺序是权威的；谱系只让每个子项紧邻其父。孤儿降级为根级；环软失败并作为根发出。
"""
__all__=['展平谱系']#仅中文公开名

def 展平谱系(摘要列表):
    """摘要 -> 带谱系缩进的扁平列表。

    摘要列表为带 sessionId／可选 parentSessionId 的 dict 序列。
    返回渲染顺序的展示行（含 depth）。
    """
    按标识={}#按 id 索引
    for 摘要 in 摘要列表:#填充
        按标识[摘要['sessionId']]=摘要#写入
    子表={}#父 → 子列表
    根列表=[]#根
    for 摘要 in 摘要列表:#建树
        父=摘要['parentSessionId'] if 'parentSessionId' in 摘要 else None#父
        if 父 is not None and 父 in 按标识:#父在列表中
            if 父 not in 子表:#首次
                子表[父]=[]#新表
            子表[父].append(摘要)#挂到父下
        else:#根或孤儿
            根列表.append(摘要)#作根
    输出=[]#输出行
    已访问=set()#已访问
    def 行走(摘要,深度):
        """深度优先。"""
        标识=摘要['sessionId']#id
        if 标识 in 已访问:#环
            print('[session-controller] lineage cycle at '+str(标识)+'; emitting as root')#告警
            return#停
        已访问.add(标识)#标记
        行=dict(摘要)#拷贝
        行['depth']=深度#缩进
        输出.append(行)#收下
        for 子 in (子表[标识] if 标识 in 子表 else []):#子项
            行走(子,深度+1)#递归
    for 根 in 根列表:#从根走
        行走(根,0)#深度 0
    for 摘要 in 摘要列表:#环成员作根发出
        if 摘要['sessionId'] not in 已访问:#未达
            行走(摘要,0)#作根
    return 输出#行
