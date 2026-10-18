'把 tool-workflow 事件折成一个持久的 workflow-run 聊天节点'

__all__=['工作流运行定义']

def 匹配(事件):
    'run-start 开节点，同一 runId 的后续事件更新'
    类型=事件['type']#事件类型
    if 类型=='tool-workflow/run-start':#开节点
        return {'id':str(事件['data']['runId']),'role':'start'}
    if 类型=='tool-workflow/agent-start' or 类型=='tool-workflow/agent-end' or 类型=='tool-workflow/run-end':#同一轮更新
        return {'id':str(事件['data']['runId']),'role':'update'}
    return None#其它事件不认

def 起始(上下文,匹配结果,读取=None):
    '开节点必须是 tool-workflow/run-start'
    事件=匹配结果['event']#起始事件
    if 事件['type']!='tool-workflow/run-start':#类型不对
        raise Exception('workflow-run start requires tool-workflow/run-start')
    return {'name':事件['data']['name'],'members':[]}#只有名字，还没有成员

def 更新(上下文,匹配结果):
    '未知类型保持原状态'
    事件=匹配结果['event']#这一条
    状态=上下文['state']#折到目前的状态
    类型=事件['type']#类型
    if 类型=='tool-workflow/agent-start':#追加一个已启动的成员
        数据=事件['data']#成员数据
        成员={'seq':数据['seq'],'label':数据['label'],'childId':数据['childId']}#不写 runId
        if 'phase' in 数据:#缺席的阶段字段不写进去
            成员['phase']=数据['phase']
        新状态=dict(状态)#保留其余字段
        成员表=list(状态['members'])#拷贝后再追加
        成员表.append(成员)
        新状态['members']=成员表
        return 新状态
    if 类型=='tool-workflow/agent-end':#给对应序号写结局
        数据=事件['data']#结局数据
        成员表=[]#新表
        for 成员 in 状态['members']:#其它成员不动
            if 成员['seq']==数据['seq']:#命中
                副本=dict(成员)#拷贝
                副本['outcome']=数据['outcome']#结局
                成员表.append(副本)
            else:#未命中
                成员表.append(成员)
        新状态=dict(状态)#保留其余字段
        新状态['members']=成员表
        return 新状态
    if 类型=='tool-workflow/run-end':#整次运行结束
        新状态=dict(状态)#保留成员
        新状态['stopReason']=事件['data']['stopReason']#停止原因
        return 新状态
    return 状态#原对象

def 建视图节点(上下文):
    '还没有起始就不发表。阶段按第一次出现的顺序分组'
    if 'start' not in 上下文 or 上下文['start'] is None:#还没有 run-start
        return None
    起始项=上下文['start']#起始匹配
    位置=起始项['location']#起始所在位置
    状态=上下文['state']#折叠状态
    种类=位置['kind']#位置种类
    if 种类!='step' and 种类!='turn':#普通关闭不能说明工作流已停
        放弃=False
    else:#步或回合
        回合=位置['turn']#所属回合
        结束=回合['end'] if 'end' in 回合 else None#可能还没关
        if 结束 is None:#没关
            放弃=False
        else:#已关
            原因种类=结束['data']['reason']['kind']#关闭原因
            放弃=原因种类=='interrupted' or 原因种类=='forked'#中断或分叉才算放弃
    中断=('stopReason' not in 状态) and 放弃#没有 run-end，且回合已被放弃
    阶段表={}#键到阶段，插入顺序就是首次出现顺序
    for 成员 in 状态['members']:#逐个已启动成员
        if 'phase' not in 成员:#缺席和空字符串是两种身份
            阶段=None
        else:#字段在
            阶段=成员['phase']
        if 阶段 is None:#缺席
            键='missing'
        else:#带长度，空字符串也留得住
            键=f'value:{len(阶段)}:{阶段}'
        if 键 not in 阶段表:#这一身份第一次出现
            阶段表[键]={'phase':阶段,'members':[]}
        if 'outcome' not in 成员:#还没有结局
            if 中断:#回合已放弃
                展示='interrupted'
            else:#仍在跑
                展示='running'
        else:#已有结局
            结局=成员['outcome']#成员结局
            if 结局=='completed':#完成
                展示='completed'
            elif 结局=='cancelled':#取消
                展示='cancelled'
            elif 结局=='failed':#失败
                展示='failed'
            else:#闭合集合之外原样留下
                展示=结局
        阶段表[键]['members'].append({
            'seq':成员['seq'],#序号
            'label':成员['label'],#名称
            'childId':成员['childId'],#子会话
            'status':展示,#展示状态
        })
    阶段列表=[]#投影后的阶段
    for 键,组 in 阶段表.items():#按首次出现
        阶段列表.append({'key':键,'phase':组['phase'],'members':组['members']})
    if 'stopReason' not in 状态:#运行还没结束
        if 中断:#回合已放弃
            运行状态='interrupted'
        else:#仍在跑
            运行状态='running'
    else:#已有停止原因
        原因=状态['stopReason']#停止原因
        if 原因=='completed':#完成
            运行状态='completed'
        elif 原因=='cancelled':#取消
            运行状态='cancelled'
        elif 原因=='error':#错误显示为失败
            运行状态='failed'
        else:#闭合集合之外原样留下
            运行状态=原因
    数据={'name':状态['name'],'status':运行状态,'phases':阶段列表}#聊天载荷
    return {
        'key':上下文['key'],#节点键
        'kind':'workflow-run',#种类
        'id':上下文['id'],#标识
        'target':'chat',#聊天面
        'anchorSeq':起始项['event']['seq'],#锚在 run-start
        'location':位置,#起始位置
        'visibility':'visible',#可见
        'data':数据,#载荷
    }

工作流运行定义={
    'kind':'workflow-run',#种类
    'target':'chat',#聊天面
    'match':匹配,#认领
    'start':起始,#开状态
    'update':更新,#折叠
    'buildViewNode':建视图节点,#投影
}
