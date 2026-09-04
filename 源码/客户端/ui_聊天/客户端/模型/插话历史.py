"""从事件溯源的 agent 收件箱重建持久转向身份。

对齐上游 `ui-chat/src/client/model/steering-history.ts`。公开面仅中文名。
"""

__all__=['插话历史']#仅中文公开名

def 取字段(对象,键,缺省=None):#读字段
    """映射或属性。"""
    if 对象 is None:#空
        return 缺省#缺
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

class 插话历史:#转向历史
    """增量识别从 next-step 收件箱认领的 user/message。"""

    def __init__(自身):#构造
        """空队列与认领集。"""
        自身.收件箱={'next-turn':[],'next-step':[]}#各目标
        自身.已认领下一步=set()#认领集

    def reset(自身):#重置
        """重建历史窗口前清空。"""
        自身.收件箱['next-turn']=[]#清
        自身.收件箱['next-step']=[]#清
        自身.已认领下一步.clear()#清

    def apply(自身,事件):#应用事件
        """仅当用户来源消息先前从 next-step 认领时为 True。"""
        种=取字段(事件,'type')#种
        if 种=='agent/inbox/spliced':#拼接
            自身._应用拼接(取字段(事件,'data') or {})#叠
            return False#拼接非转向
        if 种!='user/message':#非用户
            return False#否
        标识=取字段(取字段(事件,'data'),'id')#消息 id
        if 标识 not in 自身.已认领下一步:#未认领
            return False#否
        自身.已认领下一步.discard(标识)#消耗
        return 取字段(取字段(取字段(事件,'data'),'source'),'kind')=='user'#须用户来源

    def _应用拼接(自身,拼接):#应用拼接
        """重放主机校验过的收件箱拼接。"""
        目标=取字段(拼接,'target')#目标
        起=取字段(拼接,'start',0)#起
        删=取字段(拼接,'removedCount',0) or 0#删
        插入=list(取字段(拼接,'inserted') or [])#插
        队=自身.收件箱.get(目标)#队列
        if 队 is None:#未知
            return#停
        被删=队[起:起+删]#被删
        队[起:起+删]=插入#splice
        for 身份 in 插入:#插入不再认领
            自身.已认领下一步.discard(取字段(身份,'id'))#删
        if 目标!='next-step' or 取字段(拼接,'outcome')=='canceled':#非下一步或取消
            return#停
        for 身份 in 被删:#移除项认领
            自身.已认领下一步.add(取字段(身份,'id'))#加
