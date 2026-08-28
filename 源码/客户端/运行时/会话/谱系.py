"""摘要 → 带谱系缩进的扁平列表（纯函数）。

对齐上游 `runtime/src/client/sessions/lineage.ts`。公开面仅中文名。
输入顺序是权威的；谱系只让每个子项紧挨其父项。孤儿谱系降级为根；环软失败并当作根发出。
"""
import warnings#环软失败告警

__all__=['展平谱系']#仅中文公开名

def 取字段(对象,键,缺省=None):#读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

def 展平谱系(摘要们,挂起交互=None,已完成=None):#展平谱系
    """摘要 → 带谱系缩进的扁平列表。

    根与兄弟顺序跟随既定输入顺序；本投影从不按可变时间戳重排已水合列表。
    @param 摘要们 - 宿主 session.list 条目。
    @param 挂起交互 - 管理器拥有的当前交互状态，按会话键控（dict 或带 get 的映射）。
    @param 已完成 - 待展示完成提醒的会话集合。
    @returns 渲染顺序的展示行。
    """
    按标识={}#id → 摘要
    for 摘要 in 摘要们:#建索引
        按标识[取字段(摘要,'sessionId')]=摘要#记下
    子表={}#父 → 子列表
    根们=[]#根（含孤儿）
    for 摘要 in 摘要们:#按输入顺序分根与子
        父标识=取字段(摘要,'parentSessionId')#父会话
        if 父标识 is not None and 父标识 in 按标识:#父在本批摘要里
            列表=子表.get(父标识)#已有或空
            if 列表 is None:#第一次
                列表=[]#新建
                子表[父标识]=列表#写回
            列表.append(摘要)#接到父下
        else:#根，或父不在摘要里的孤儿
            根们.append(摘要)#当作根发出
    输出=[]#输出行
    已访=set()#已走访，用于破环

    def 行走(摘要,深度):#深度优先写出
        """写出一行并下钻子项。"""
        标识=取字段(摘要,'sessionId')#会话 id
        if 标识 in 已访:#成环
            warnings.warn('[web-runtime] lineage cycle at '+str(标识)+'; emitting as root')#环软失败当根
            return#不再下钻
        已访.add(标识)#记已走访
        行=dict(摘要) if isinstance(摘要,dict) else dict(摘要.__dict__)#摘要字段拷贝
        if 挂起交互 is not None:#有挂起表
            取=挂起交互.get if hasattr(挂起交互,'get') else None#get
            挂=取(标识) if 取 is not None else None#该会话待处理
            if 挂 is not None:#有则带上
                行['pendingInteraction']=挂#写入
        行['completed']=(标识 in 已完成) if 已完成 is not None else False#完成提醒
        行['depth']=深度#缩进深度
        输出.append(行)#写出一行
        孩子们=子表.get(标识)#子项
        if 孩子们 is None:#无子则停
            return#完
        for 孩子 in 孩子们:#子项深度 +1
            行走(孩子,深度+1)#下钻

    for 根 in 根们:#从根走
        行走(根,0)#深度 0
    for 摘要 in 摘要们:#环成员补漏
        if 取字段(摘要,'sessionId') not in 已访:#未走访则当根
            行走(摘要,0)#当根
    return 输出#渲染顺序
