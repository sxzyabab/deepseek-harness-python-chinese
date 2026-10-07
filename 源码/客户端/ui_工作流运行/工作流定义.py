'把 tool-workflow 事件折成一个持久的 workflow-run 聊天节点'
__all__=['工作流运行定义','阶段键']#仅中文公开名

def 阶段键(阶段):#缺席和空字符串是两种身份
    'null 用 missing，其余带长度前缀'
    return 'missing' if 阶段 is None else 'value:'+str(len(阶段))+':'+阶段#键

def 停止状态(原因):#运行停止原因到展示状态
    'completed / cancelled / error'
    if 原因=='completed':#完成
        return 'completed'#完成
    if 原因=='cancelled':#取消
        return 'cancelled'#取消
    if 原因=='error':#错误
        return 'failed'#失败
    return 原因#其余原样

def 结局状态(结局):#成员结局到展示状态
    'completed / cancelled / failed'
    if 结局=='completed':#完成
        return 'completed'#完成
    if 结局=='cancelled':#取消
        return 'cancelled'#取消
    if 结局=='failed':#失败
        return 'failed'#失败
    return 结局#其余原样

def 位置已关(位置):#这一步或这一轮已经关上
    '关上且没有 stopReason 时成员显示已中断'
    if 位置['kind']=='step':#步
        return 位置['step']['status']=='closed' or 位置['turn']['status']=='closed'#步或轮已关
    return 位置['kind']=='turn' and 位置['turn']['status']=='closed'#轮已关

def 投影(上下文,位置):#折叠状态到聊天载荷
    '按阶段键分组，保持首次出现的顺序'
    状态=上下文['state']#折叠状态
    中断=('stopReason' not in 状态 or 状态['stopReason'] is None) and 位置已关(位置)#未结束但位置已关
    阶段表={}#键到组
    顺序=[]#首次出现顺序
    for 成员 in 状态['members']:#逐成员
        阶段=None if 'phase' not in 成员 else 成员['phase']#缺席是 None
        键=阶段键(阶段)#稳定键
        if 键 not in 阶段表:#新阶段
            阶段表[键]={'phase':阶段,'members':[]}#建组
            顺序.append(键)#记下顺序
        if 'outcome' not in 成员 or 成员['outcome'] is None:#还没结局
            展示='interrupted' if 中断 else 'running'#中断或仍在跑
        else:#有结局
            展示=结局状态(成员['outcome'])#映射
        阶段表[键]['members'].append({#一行
            'seq':成员['seq'],'label':成员['label'],'childId':成员['childId'],'status':展示,#成员
        })#结束
    阶段列表=[]#投影
    for 键 in 顺序:#按出现顺序
        组=阶段表[键]#组
        阶段列表.append({'key':键,'phase':组['phase'],'members':组['members']})#一行
    if 'stopReason' not in 状态 or 状态['stopReason'] is None:#运行还没停
        运行状态='interrupted' if 中断 else 'running'#中断或运行中
    else:#已停
        运行状态=停止状态(状态['stopReason'])#映射
    return {'name':状态['name'],'status':运行状态,'phases':阶段列表}#载荷

def 成员开始(状态,数据):#追加一个成员
    'phase 缺席就不写这个字段'
    成员={'seq':数据['seq'],'label':数据['label'],'childId':数据['childId']}#必填
    if 'phase' in 数据 and 数据['phase'] is not None:#有阶段
        成员['phase']=数据['phase']#阶段
    成员表=list(状态['members'])#拷贝
    成员表.append(成员)#追加
    return {'name':状态['name'],'members':成员表,'stopReason':状态['stopReason'] if 'stopReason' in 状态 else None}#新状态

def 成员结束(状态,数据):#给对应 seq 写结局
    '其它成员不动'
    成员表=[]#新表
    for 成员 in 状态['members']:#逐个
        if 成员['seq']==数据['seq']:#命中
            副本=dict(成员)#拷贝
            副本['outcome']=数据['outcome']#结局
            成员表.append(副本)#换上
        else:#其它
            成员表.append(成员)#原样
    return {'name':状态['name'],'members':成员表,'stopReason':状态['stopReason'] if 'stopReason' in 状态 else None}#新状态

def 匹配(事件):#认不认这四类工作流事件
    'run-start 开节点，其余更新同一 runId'
    类型=事件['type']#类型
    数据=事件['data'] if 'data' in 事件 and 事件['data'] is not None else {}#数据
    if 类型=='tool-workflow/run-start':#开始
        return {'id':str(数据['runId']),'role':'start'}#开
    if 类型=='tool-workflow/agent-start' or 类型=='tool-workflow/agent-end' or 类型=='tool-workflow/run-end':#更新
        return {'id':str(数据['runId']),'role':'update'}#更新
    return None#无关

def 起始(_上下文,匹配结果):#用 run-start 建状态
    '开节点必须是 run-start'
    事件=匹配结果['event']#事件
    if 事件['type']!='tool-workflow/run-start':#不是
        raise RuntimeError('workflow-run start requires tool-workflow/run-start')#拒绝
    return {'name':事件['data']['name'],'members':[]}#初始

def 更新(上下文,匹配结果):#折叠后续事件
    '未知类型保持原状态'
    事件=匹配结果['event']#事件
    状态=上下文['state']#当前
    if 事件['type']=='tool-workflow/agent-start':#成员开始
        return 成员开始(状态,事件['data'])#追加
    if 事件['type']=='tool-workflow/agent-end':#成员结束
        return 成员结束(状态,事件['data'])#写结局
    if 事件['type']=='tool-workflow/run-end':#运行结束
        return {'name':状态['name'],'members':状态['members'],'stopReason':事件['data']['stopReason']}#写原因
    return 状态#原样

def 建视图节点(上下文):#投影聊天节点
    '还没有起始就不发表'
    起始项=上下文['start'] if 'start' in 上下文 else None#起始
    if 起始项 is None:#无
        return None#不发表
    位置=起始项['location']#位置
    数据=投影(上下文,位置)#载荷
    return {#节点
        'key':上下文['key'],'kind':'workflow-run','id':上下文['id'],'target':'chat',#身份
        'anchorSeq':起始项['event']['seq'],'location':位置,'visibility':'visible','data':数据,#位置与载荷
    }#结束

工作流运行定义={#会话节点定义
    'kind':'workflow-run',#种类
    'target':'chat',#聊天面
    'match':匹配,#匹配
    'start':起始,#起始
    'update':更新,#更新
    'buildViewNode':建视图节点,#视图
}#结束
