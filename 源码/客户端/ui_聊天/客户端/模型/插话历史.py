"""从事件溯源的 agent 收件箱重建持久转向身份。

对齐上游 `ui-chat/src/client/model/steering-history.ts`。公开面仅中文名。
事件为会话事件 dict。
"""

__all__=['插话历史']#仅中文公开名

class 插话历史:
    """增量识别从 next-step 收件箱认领的 user/message。"""
    def __init__(自身):
        """空队列与认领集。"""
        自身.收件箱={'next-turn':[],'next-step':[]}#各目标
        自身.已认领下一步=set()#认领集

    def 重置(自身):
        """重建历史窗口前清空。"""
        自身.收件箱['next-turn']=[]#清
        自身.收件箱['next-step']=[]#清
        自身.已认领下一步.clear()#清

    def 应用(自身,事件):
        """仅当用户来源消息先前从 next-step 认领时为 True。事件为 dict。"""
        种=事件['type'] if 'type' in 事件 else None#种
        if 种=='agent/inbox/spliced':#拼接
            数据=事件['data'] if 'data' in 事件 and 事件['data'] is not None else {}#载荷
            自身._应用拼接(数据)#叠
            return False#拼接非转向
        if 种!='user/message':#非用户
            return False#否
        数据=事件['data'] if 'data' in 事件 else None#载荷
        标识=数据['id'] if 数据 is not None and 'id' in 数据 else None#消息 id
        if 标识 not in 自身.已认领下一步:#未认领
            return False#否
        自身.已认领下一步.discard(标识)#消耗
        来源=数据['source'] if 数据 is not None and 'source' in 数据 else None#来源
        来种=来源['kind'] if 来源 is not None and 'kind' in 来源 else None#来种
        return 来种=='user'#须用户来源

    def _应用拼接(自身,拼接):
        """重放主机校验过的收件箱拼接。拼接为 dict。"""
        目标=拼接['target'] if 'target' in 拼接 else None#目标
        起=拼接['start'] if 'start' in 拼接 else 0#起
        删=拼接['removedCount'] if 'removedCount' in 拼接 and 拼接['removedCount'] is not None else 0#删
        插入=list(拼接['inserted']) if 'inserted' in 拼接 and 拼接['inserted'] is not None else []#插
        if 目标 not in 自身.收件箱:#未知
            return#停
        队=自身.收件箱[目标]#队列
        被删=队[起:起+删]#被删
        队[起:起+删]=插入#splice
        for 身份 in 插入:#插入不再认领
            号=身份['id'] if 'id' in 身份 else None#id
            自身.已认领下一步.discard(号)#删
        结局=拼接['outcome'] if 'outcome' in 拼接 else None#结局
        if 目标!='next-step' or 结局=='canceled':#非下一步或取消
            return#停
        for 身份 in 被删:#移除项认领
            号=身份['id'] if 'id' in 身份 else None#id
            自身.已认领下一步.add(号)#加
