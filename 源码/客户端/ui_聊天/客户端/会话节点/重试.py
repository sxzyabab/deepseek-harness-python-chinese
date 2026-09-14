from .节点工厂 import 聊天错误,聊天节点,上下文位置#公共

__all__=['重试定义','登记重试会话节点']#仅中文公开名

def 调度节点(匹配项):#从 llm/retry 造 scheduled 节点
    """非调度事件则 None。"""
    事件=匹配项['event']#事件
    if 事件['type']!='llm/retry':#非
        return None#无
    数据=事件['data'] if 'data' in 事件 else {}#载荷
    节点={'kind':'model-retry','seq':事件['seq'],'time':事件['time'] if 'time' in 事件 else None,'retryState':'scheduled'}#底座
    if isinstance(数据,dict):#展开字段
        节点.update(数据)#展开
    return 节点#scheduled

def 已关闭(位置):#所属步骤或回合是否已关闭
    """任一边关闭即 true。"""
    种=位置['kind'] if 'kind' in 位置 else None#种
    if 种=='step':#步骤
        步位=位置['step'] if 'step' in 位置 else None#步
        if 步位 is not None and 'status' in 步位 and 步位['status']=='closed':#步骤关
            return True#关
    if 种 in ('step','turn'):#回合
        回合位=位置['turn'] if 'turn' in 位置 else None#回合
        if 回合位 is not None and 'status' in 回合位 and 回合位['status']=='closed':#回合关
            return True#关
    return False#开放

def 重试匹配(事件):#判定事件是否属于本节点
    """llm/retry 与 llm/retry-started。"""
    种=事件['type']#种
    数据=事件['data'] if 'data' in 事件 else {}#载荷
    if 种=='llm/retry':#调度
        重试标识=数据['retryId'] if 'retryId' in 数据 else None#id
        if not isinstance(重试标识,str) or 重试标识=='':#非法
            return None#忽略
        次=数据['retry'] if 'retry' in 数据 else None#次数
        return {'id':重试标识,'role':'start' if 次==1 else 'update'}#首次开
    if 种=='llm/retry-started':#已开始
        重试标识=数据['retryId'] if 'retryId' in 数据 else None#id
        if isinstance(重试标识,str) and 重试标识!='':#合法
            return {'id':重试标识,'role':'update'}#更新
        return None#忽略
    return None#其余

def 重试开始(_上下文,匹配项):#用首条 llm/retry 开节点
    """记下回合、步骤与首次尝试。"""
    节点=调度节点(匹配项)#造
    if 节点 is None:#非
        raise 聊天错误('model-retry start requires a valid llm/retry event')#硬失败
    return {'turn':节点['turn'] if 'turn' in 节点 else None,'step':节点['step'] if 'step' in 节点 else None,'attempts':[节点]}#初态

def 重试更新(上下文,匹配项):#把后续重试事件折进状态
    """追加 scheduled 或标 started。"""
    事件=匹配项['event']#事件
    态=上下文['state']#态
    种=事件['type']#种
    if 种=='llm/retry':#又一次调度
        节点=调度节点(匹配项)#造
        if 节点 is None:#无
            return 态#不改
        尝试=list(态['attempts'] if 'attempts' in 态 else [])#拷
        尝试.append(节点)#追加
        return {**态,'attempts':尝试}#追加
    if 种!='llm/retry-started':#其它
        return 态#不改
    数据=事件['data'] if 'data' in 事件 else {}#载荷
    序号=数据['retry'] if 'retry' in 数据 else None#尝试序号
    尝试列表=[]#新表
    for 候 in (态['attempts'] if 'attempts' in 态 else []):#扫
        if ('retry' in 候) and 候['retry']==序号:#命中
            尝试列表.append({**候,'retryState':'started'})#标 started
        else:#原样
            尝试列表.append(候)#收
    return {**态,'attempts':尝试列表}#写回

def 重试建视图(上下文):#组装可见 Chat 节点
    """末次 scheduled 且边界已关 → cancelled。"""
    态=上下文['state'] if 'state' in 上下文 else None#态
    if 态 is None or 'attempts' not in 态 or len(态['attempts'])==0:#无
        return None#不渲染
    位置=上下文位置(上下文)#位置
    原尝试=list(态['attempts'])#折叠尝试
    尝试列表=[]#投影
    for 甲,候 in enumerate(原尝试):#逐条
        态名=候['retryState'] if 'retryState' in 候 else None#态
        if 甲==len(原尝试)-1 and 态名=='scheduled' and 已关闭(位置):#末次且关
            尝试列表.append({**候,'retryState':'cancelled'})#cancelled
        else:#原样
            尝试列表.append(候)#收下
    当前=尝试列表[-1] if len(尝试列表)>0 else None#当前
    if 当前 is None:#空
        return None#不渲染
    数据={'attempts':尝试列表,'current':当前}#载荷
    锚=尝试列表[0]['seq'] if len(尝试列表)>0 else 当前['seq']#锚
    return 聊天节点(上下文,'model-retry',锚,数据)#节点

重试定义={#模型重试会话节点定义
    'kind':'model-retry','target':'chat',#kind/目标
    'match':重试匹配,'start':重试开始,'update':重试更新,'buildViewNode':重试建视图,#生命周期
}#结束

def 登记重试会话节点(上下文):#注册模型重试业务贡献
    """挂到 uiConversation.events。"""
    上下文.uiConversation.events.register(重试定义)#登记
