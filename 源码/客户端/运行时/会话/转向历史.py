"""从事件溯源的智能体收件箱重建持久化转向身份。

对齐上游 `runtime/src/client/sessions/steering-history.ts`。公开面仅中文名。
"""

__all__=['转向历史']#仅中文公开名

def 取字段(对象,键,缺省=None):#读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

class 转向历史:#转向历史
    """增量识别从下一步收件箱认领的 `user/message` 事件。"""

    def __init__(自身):#空镜像
        """两个收件箱镜像与已认领集。"""
        自身.收件箱={'next-turn':[],'next-step':[]}#下一回合与下一步
        自身.已认领下一步=set()#已从 next-step 摘走、等待对应 user/message 的 id

    def 重置(自身):#重置
        """重建历史窗口前清掉全部回放状态。"""
        自身.收件箱['next-turn']=[]#清空下一回合
        自身.收件箱['next-step']=[]#清空下一步
        自身.已认领下一步.clear()#清空已认领集

    def 应用(自身,事件):#应用一条事件
        """应用一条事件，并报告它是否是持久化的人类转向消息。

        @param 事件 - 按序的下一条原始会话事件。
        @returns 仅当这是先前从 `next-step` 认领的、来源为用户的消息时为 True。
        """
        类型=取字段(事件,'type')#事件类型
        if 类型=='agent/inbox/spliced':#收件箱拼接
            自身._应用拼接(取字段(事件,'data'))#更新镜像
            return False#拼接本身不是转向消息
        if 类型!='user/message':#其它事件不是
            return False#不是
        数据=取字段(事件,'data')#消息载荷
        标识=取字段(数据,'id')#消息 id
        if 标识 not in 自身.已认领下一步:#不是从 next-step 认领的
            return False#不是
        自身.已认领下一步.discard(标识)#摘掉认领
        来源=取字段(数据,'source')#来源
        return 取字段(来源,'kind')=='user'#必须是用户来源

    def _应用拼接(自身,拼接):#应用拼接
        """回放一次宿主已校验的收件箱拼接。"""
        目标=取字段(拼接,'target')#目标列表
        起始=取字段(拼接,'start')#起始下标
        删除数=取字段(拼接,'removedCount',0)#删除数量
        插入=取字段(拼接,'inserted') or []#插入的身份
        结果=取字段(拼接,'outcome')#可选取消结果
        列表=自身.收件箱[目标]#该目标镜像
        被删=列表[起始:起始+删除数]#被删项
        自身.收件箱[目标]=列表[:起始]+list(插入)+列表[起始+删除数:]#改镜像
        for 身份 in 插入:#新插入的不再算已认领
            自身.已认领下一步.discard(取字段(身份,'id'))#摘掉
        if 目标!='next-step' or 结果=='canceled':#只把 next-step 且非取消的删除项记为已认领
            return#完
        for 身份 in 被删:#等待对应 user/message
            自身.已认领下一步.add(取字段(身份,'id'))#记认领
