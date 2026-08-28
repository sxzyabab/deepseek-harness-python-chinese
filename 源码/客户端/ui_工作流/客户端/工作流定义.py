"""工作流一次运行的 ConversationNode Definition：把 tool-workflow 事件折成一条带键的 Chat 节点。

对齐上游 `ui-workflow-run/src/client/workflow-definition.ts`。公开面仅中文名。
"""

__all__=[#仅中文公开名
    '工作流阶段键',
    '工作流运行定义',
    '取字段',
]#公开面结束

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段，缺席为缺省。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺席)#对象属性

def 工作流阶段键(阶段):#精确阶段身份 → 稳定键
    """为精确阶段身份生成无碰撞键，保留缺席与空字符串的区别。"""
    if 阶段 is None:#字段缺席
        return 'missing'#缺席记 missing
    return f'value:{len(阶段)}:{阶段}'#带长度前缀防碰撞

def 停止原因状态(停止原因):#停止原因 → 运行展示状态
    """把整次运行停止原因映射为展示状态。"""
    if 停止原因=='completed':#正常完成
        return 'completed'#已完成
    if 停止原因=='cancelled':#已取消
        return 'cancelled'#已取消
    if 停止原因=='error':#出错
        return 'failed'#失败
    return 停止原因#其它原样

def 结局状态(结局):#成员结局 → 成员展示状态
    """把成员结局映射为展示状态。"""
    if 结局=='completed':#成员完成
        return 'completed'#已完成
    if 结局=='cancelled':#成员取消
        return 'cancelled'#已取消
    if 结局=='failed':#成员失败
        return 'failed'#失败
    return 结局#其它原样

def 位置已闭合(位置):#会话位置上的步或回合是否已闭合
    """步或所属回合任一闭合，或回合位置已闭合则为真。"""
    种类=取字段(位置,'kind')#位置种类
    if 种类=='step':#挂在步上
        步=取字段(位置,'step')#步
        回合=取字段(位置,'turn')#所属回合
        return 取字段(步,'status')=='closed' or 取字段(回合,'status')=='closed'#任一闭合
    return 种类=='turn' and 取字段(取字段(位置,'turn'),'status')=='closed'#回合已闭合

def 投影工作流(上下文,位置):#累积状态 → 最终 Chat 载荷
    """按阶段身份分组已启动成员，并投影最终渲染数据。"""
    状态=取字段(上下文,'state')#本节点状态
    中断=取字段(状态,'stopReason') is None and 位置已闭合(位置)#尚未 run-end 且位置已闭合
    阶段表={}#阶段键 → 阶段名与成员列表（保插入序）
    for 成员 in 取字段(状态,'members') or []:#逐成员归入阶段
        原始阶段=取字段(成员,'phase')#阶段字段
        阶段=None if 原始阶段 is None and 'phase' not in (成员 if isinstance(成员,dict) else {}) else 原始阶段#缺席归一
        if not isinstance(成员,dict):#对象形态
            阶段=None if not hasattr(成员,'phase') else 取字段(成员,'phase')#按属性判缺席
        键=工作流阶段键(阶段)#无碰撞阶段键
        if 键 not in 阶段表:#首次见到该阶段身份
            阶段表[键]={'phase':阶段,'members':[]}#新建空成员列表
        结局=取字段(成员,'outcome')#成员结局
        if 结局 is None:#尚未结束
            成员状态='interrupted' if 中断 else 'running'#位置已闭合则中断，否则仍运行中
        else:#已结束
            成员状态=结局状态(结局)#按结局映射
        阶段表[键]['members'].append({#追加成员渲染数据
            'seq':取字段(成员,'seq'),#成员序号
            'label':取字段(成员,'label'),#成员展示名
            'childId':取字段(成员,'childId'),#子会话 id
            'status':成员状态,#展示状态
        })#成员结束
    投影阶段=[]#按插入序的阶段数组
    for 键,组 in 阶段表.items():#Map 转数组
        投影阶段.append({'key':键,'phase':组['phase'],'members':组['members']})#阶段段
    停止=取字段(状态,'stopReason')#整次停止原因
    if 停止 is None:#尚未 run-end
        整状='interrupted' if 中断 else 'running'#中断或运行中
    else:#已停止
        整状=停止原因状态(停止)#按原因映射
    return {'name':取字段(状态,'name'),'status':整状,'phases':投影阶段}#最终 Chat 载荷

def 更新成员开始(状态,数据):#把一名成员的开始并入状态
    """从 agent-start 载荷抽出本成员并追加。"""
    成员={'seq':取字段(数据,'seq'),'label':取字段(数据,'label'),'childId':取字段(数据,'childId')}#基本字段
    if 取字段(数据,'phase') is not None or (isinstance(数据,dict) and 'phase' in 数据):#有阶段字段
        if isinstance(数据,dict) and 'phase' in 数据:#映射带键
            成员['phase']=数据['phase']#可为空串
        elif hasattr(数据,'phase'):#对象有属性
            成员['phase']=取字段(数据,'phase')#写入
    成员们=list(取字段(状态,'members') or [])#拷贝列表
    成员们.append(成员)#追加
    return {**状态,'members':成员们} if isinstance(状态,dict) else {'name':取字段(状态,'name'),'stopReason':取字段(状态,'stopReason'),'members':成员们}#新状态

def 更新成员结束(状态,数据):#把一名成员的结局写回对应序号
    """按序号定位成员并写入 outcome。"""
    序号=取字段(数据,'seq')#目标序号
    结局=取字段(数据,'outcome')#结局
    成员们=[]#新列表
    for 成员 in 取字段(状态,'members') or []:#逐成员
        if 取字段(成员,'seq')==序号:#命中
            if isinstance(成员,dict):#映射
                成员们.append({**成员,'outcome':结局})#写入结局
            else:#对象转映射
                成员们.append({'seq':取字段(成员,'seq'),'label':取字段(成员,'label'),'childId':取字段(成员,'childId'),'phase':取字段(成员,'phase'),'outcome':结局})#拷贝+结局
        else:#其余原样
            成员们.append(成员)#原样
    if isinstance(状态,dict):#映射状态
        return {**状态,'members':成员们}#新状态
    return {'name':取字段(状态,'name'),'stopReason':取字段(状态,'stopReason'),'members':成员们}#对象态组装

def 匹配事件(事件):#按事件类型归入本 runId
    """返回 {id, role} 或 None。"""
    种类=取字段(事件,'type')#事件类型
    数据=取字段(事件,'data')#载荷
    if 种类=='tool-workflow/run-start':#运行开始
        return {'id':str(取字段(数据,'runId')),'role':'start'}#作本节点 start
    if 种类 in ('tool-workflow/agent-start','tool-workflow/agent-end','tool-workflow/run-end'):#成员或运行结束
        return {'id':str(取字段(数据,'runId')),'role':'update'}#挂到同一 runId
    return None#无关事件

def 开始(_上下文,匹配):#从 run-start 播种状态
    """记下名称，尚无成员。"""
    事件=取字段(匹配,'event')#匹配事件
    if 取字段(事件,'type')!='tool-workflow/run-start':#类型守卫
        raise Exception('workflow-run start requires tool-workflow/run-start')#收窄失败
    return {'name':取字段(取字段(事件,'data'),'name'),'members':[]}#初始状态

def 更新(上下文,匹配):#按后续事件推进状态
    """agent-start / agent-end / run-end 折叠。"""
    事件=取字段(匹配,'event')#事件
    种类=取字段(事件,'type')#类型
    状态=取字段(上下文,'state')#当前状态
    数据=取字段(事件,'data')#载荷
    if 种类=='tool-workflow/agent-start':#成员开始
        return 更新成员开始(状态,数据)#追加成员
    if 种类=='tool-workflow/agent-end':#成员结束
        return 更新成员结束(状态,数据)#写入结局
    if 种类=='tool-workflow/run-end':#整次运行结束
        if isinstance(状态,dict):#映射
            return {**状态,'stopReason':取字段(数据,'stopReason')}#记下停止原因
        return {'name':取字段(状态,'name'),'members':取字段(状态,'members'),'stopReason':取字段(数据,'stopReason')}#对象态
    return 状态#其余不改

def 构建视图节点(上下文):#累积状态 → Chat 视图节点
    """尚未 start 则不产出。"""
    if 取字段(上下文,'start') is None:#尚未 start
        return None#不产出
    起点=取字段(上下文,'start')#start 匹配
    数据=投影工作流(上下文,取字段(起点,'location'))#按阶段投影
    return {#组装 Chat 视图节点
        'key':取字段(上下文,'key'),#节点键
        'kind':'workflow-run',#节点种类
        'id':取字段(上下文,'id'),#节点 id（runId）
        'target':'chat',#投递到 Chat 槽
        'anchorSeq':取字段(取字段(起点,'event'),'seq'),#用 start 事件序号排序
        'location':取字段(起点,'location'),#起点位置
        'visibility':'visible',#始终可见
        'data':数据,#最终渲染载荷
    }#视图节点结束

工作流运行定义={#工作流运行 Definition
    'kind':'workflow-run',#节点种类
    'target':'chat',#投递到 Chat 槽
    'match':匹配事件,#按事件归入
    'start':开始,#播种
    'update':更新,#推进
    'buildViewNode':构建视图节点,#投影视图
}#定义结束
