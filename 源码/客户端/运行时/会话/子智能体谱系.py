"""对保留的会话列表镜像做纯子智能体谱系聚合。

对齐上游 `runtime/src/client/sessions/subagent-lineage.ts`。公开面仅中文名。
普通分叉会终止传播，因此每个可见会话只拥有其不间断的子智能体子树。
"""

__all__=['索引子智能体后代']#仅中文公开名

def 取字段(对象,键,缺省=None):#读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

def 索引子智能体后代(摘要表):#索引子智能体后代
    """在每个祖先下索引它经不间断子智能体来源链到达的每一个子智能体后代。

    环路软失败；孤儿拥有者在其摘要到达前作为无害映射键留下。
    @param 摘要表 - 按 id 键控的保留会话摘要。
    @returns 按可能的父 id 键控的后代总数与运行中总数。
    """
    已索引={}#可变聚合 parentId → {count,runningCount}
    for 后代 in 摘要表.values():#每个可能的后代
        if 取字段(后代,'origin')!='subagent':#只沿子智能体来源走
            continue#跳过
        已见=set()#防环
        当前=后代#沿父链上走
        while (当前 is not None#仍有节点
              and 取字段(当前,'origin')=='subagent'#仍是子智能体
              and 取字段(当前,'parentId') is not None#有父
              and 取字段(当前,'id') not in 已见):#且未见过
            已见.add(取字段(当前,'id'))#记下本节点
            父标识=取字段(当前,'parentId')#父 id
            聚合=已索引.get(父标识)#父上的聚合
            if 聚合 is None:#第一次见到该父
                已索引[父标识]={#新建计数
                    'count':1,#一个后代
                    'runningCount':1 if 取字段(后代,'running') else 0,#叶子在跑则计运行
                }#结束
            else:#已有聚合
                聚合['count']+=1#后代加一
                if 取字段(后代,'running'):#叶子在跑
                    聚合['runningCount']+=1#运行加一
            当前=摘要表.get(父标识)#走到父
    return 已索引#只读映射（调用方勿原地改语义上）
