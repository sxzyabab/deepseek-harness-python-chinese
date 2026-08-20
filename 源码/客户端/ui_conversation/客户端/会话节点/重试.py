"""模型重试链会话节点。

对齐上游 `ui-conversation/src/client/conversation-nodes/retry.ts`。公开面仅中文名。
"""
from .公共 import 聊天节点,上下文位置#公共
from .面辅助 import 取字段#字段

__all__=['重试定义','登记重试会话节点']#仅中文公开名

def 调度节点(匹配项):#从 llm/retry 造 scheduled 节点
    """非调度事件则 None。"""
    事件=取字段(匹配项,'event')#事件
    if 取字段(事件,'type')!='llm/retry':#非
        return None#无
    数据=取字段(事件,'data') or {}#载荷
    节点={'kind':'model-retry','seq':取字段(事件,'seq'),'time':取字段(事件,'time'),'retryState':'scheduled'}#底座
    节点.update(数据 if isinstance(数据,dict) else {})#展开字段
    return 节点#scheduled

def 已关闭(位置):#所属步骤或回合是否已关闭
    """任一边关闭即 true。"""
    种=取字段(位置,'kind')#种
    if 种=='step' and 取字段(取字段(位置,'step'),'status')=='closed':#步骤关
        return True#关
    if 种 in ('step','turn') and 取字段(取字段(位置,'turn'),'status')=='closed':#回合关
        return True#关
    return False#开放

def 重试匹配(事件):#判定事件是否属于本节点
    """llm/retry 与 llm/retry-started。"""
    种=取字段(事件,'type')#种
    数据=取字段(事件,'data') or {}#载荷
    if 种=='llm/retry':#调度
        重试标识=取字段(数据,'retryId')#id
        if not isinstance(重试标识,str) or 重试标识=='':#非法
            return None#忽略
        return {'id':重试标识,'role':'start' if 取字段(数据,'retry')==1 else 'update'}#首次开
    if 种=='llm/retry-started':#已开始
        重试标识=取字段(数据,'retryId')#id
        if isinstance(重试标识,str) and 重试标识!='':#合法
            return {'id':重试标识,'role':'update'}#更新
        return None#忽略
    return None#其余

def 重试开始(_上下文,匹配项):#用首条 llm/retry 开节点
    """记下回合、步骤与首次尝试。"""
    节点=调度节点(匹配项)#造
    if 节点 is None:#非
        raise Exception('model-retry start requires a valid llm/retry event')#硬失败
    return {'turn':取字段(节点,'turn'),'step':取字段(节点,'step'),'attempts':[节点]}#初态

def 重试更新(上下文,匹配项):#把后续重试事件折进状态
    """追加 scheduled 或标 started。"""
    事件=取字段(匹配项,'event')#事件
    态=取字段(上下文,'state')#态
    种=取字段(事件,'type')#种
    if 种=='llm/retry':#又一次调度
        节点=调度节点(匹配项)#造
        return 态 if 节点 is None else {**态,'attempts':list(态.get('attempts') or [])+[节点]}#追加
    if 种!='llm/retry-started':#其它
        return 态#不改
    序号=取字段(取字段(事件,'data'),'retry')#尝试序号
    尝试们=[{**候,'retryState':'started'} if 取字段(候,'retry')==序号 else 候 for 候 in (态.get('attempts') or [])]#标 started
    return {**态,'attempts':尝试们}#写回

def 重试建视图(上下文):#组装可见 Chat 节点
    """末次 scheduled 且边界已关 → cancelled。"""
    态=取字段(上下文,'state')#态
    if 态 is None or not 态.get('attempts'):#无
        return None#不渲染
    位置=上下文位置(上下文)#位置
    原尝试=list(态['attempts'])#折叠尝试
    尝试们=[]#投影
    for 甲,候 in enumerate(原尝试):#逐条
        if 甲==len(原尝试)-1 and 取字段(候,'retryState')=='scheduled' and 已关闭(位置):#末次且关
            尝试们.append({**候,'retryState':'cancelled'})#cancelled
        else:#原样
            尝试们.append(候)#收下
    当前=尝试们[-1] if 尝试们 else None#当前
    if 当前 is None:#空
        return None#不渲染
    数据={'attempts':尝试们,'current':当前}#载荷
    锚=取字段(尝试们[0],'seq') if 尝试们 else 取字段(当前,'seq')#锚
    return 聊天节点(上下文,'model-retry',锚,数据)#节点

重试定义={#模型重试会话节点定义
    'kind':'model-retry','target':'chat',#kind/目标
    'match':重试匹配,'start':重试开始,'update':重试更新,'buildViewNode':重试建视图,#生命周期
}#结束

def 登记重试会话节点(上下文):#注册模型重试业务贡献
    """挂到 conversationEvents。"""
    上下文.conversationEvents.register(重试定义)#登记
