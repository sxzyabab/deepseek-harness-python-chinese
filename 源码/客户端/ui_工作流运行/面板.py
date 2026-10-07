'持久工作流运行节点：运行和阶段按状态展开或收起'
from ..ui_基础界面组件.披露行 import 披露行#披露行
from ..ui_基础界面组件.状态点 import 状态点#状态点
from ..ui_基础界面组件.icons import 图标右chevron14#右箭头
from ..存储 import 浅相等#会话选择的比较

__all__=['工作流运行面板']#仅中文公开名

状态键={#展示状态到文案键
    'running':'status.running',#运行中
    'completed':'status.completed',#已完成
    'failed':'status.failed',#失败
    'cancelled':'status.cancelled',#已取消
    'interrupted':'status.interrupted',#已中断
}#结束

def 点状态(状态):#展示状态到状态点
    '取消和中断都是警告'
    if 状态=='running':#运行
        return 'ongoing'#进行
    if 状态=='completed':#完成
        return 'done'#完成
    if 状态=='failed':#失败
        return 'error'#错误
    return 'warning'#警告

def 是异常(状态):#失败、取消、中断
    '这三种要撑开披露'
    return 状态=='failed' or 状态=='cancelled' or 状态=='interrupted'#异常

def 可读阶段(阶段,翻译):#阶段标题
    '缺席和空字符串各有文案'
    if 阶段 is None:#没有阶段
        return 翻译('phase.unassigned')#未分阶段
    return 翻译('phase.empty') if 阶段=='' else 阶段#空名或原文

def 可读成员(标签,翻译):#成员名
    '空标签有文案'
    return 翻译('member.empty') if 标签=='' else 标签#名

def 状态计数(状态,数量,翻译):#「运行中 2」
    '带数量的状态短语'
    return 翻译('statusCount.'+状态,{'count':数量})#短语

def 成员数量(数量,翻译):#成员数
    '一条和多条用不同键'
    键='run.members.one' if 数量==1 else 'run.members.other'#键
    return 翻译(键,{'count':数量})#短语

def 阶段事实(阶段):#这一阶段的披露事实
    '有异常优先，其次仍在跑，否则干净'
    if any(是异常(成员['status']) for 成员 in 阶段['members']):#有异常
        模式='abnormal'#异常
    elif any(成员['status']=='running' for 成员 in 阶段['members']):#有人在跑
        模式='running'#运行
    else:#都结束了
        模式='clean'#干净
    return {'mode':模式,'activityCount':len(阶段['members'])}#事实

def 运行事实(状态,阶段事实表):#整次运行的披露事实
    '活动数是各阶段成员数之和'
    if 是异常(状态) or any(事实['mode']=='abnormal' for _键,事实 in 阶段事实表):#异常
        模式='abnormal'#异常
    elif 状态=='running' or any(事实['mode']=='running' for _键,事实 in 阶段事实表):#仍在跑
        模式='running'#运行
    else:#干净
        模式='clean'#干净
    活动=0#成员总数
    for _键,事实 in 阶段事实表:#逐阶段
        活动+=事实['activityCount']#累加
    return {'mode':模式,'activityCount':活动}#事实

def 初始披露(事实):#第一次见到这组事实
    '干净默认收起，其余默认展开'
    return {'mode':事实['mode'],'activityCount':事实['activityCount'],'open':事实['mode']!='clean','pendingCleanCollapse':False}#状态

def 推进披露(当前,事实,焦点在内):#事实变化后的下一状态
    '干净且焦点还在内容里时，收起推迟到失焦'
    同样=当前['mode']==事实['mode'] and 当前['activityCount']==事实['activityCount']#事实没变
    if 同样:#没变
        if (not 当前['pendingCleanCollapse']) or 焦点在内:#保持
            return 当前#原样
        return {'mode':当前['mode'],'activityCount':当前['activityCount'],'open':False,'pendingCleanCollapse':False}#收起
    if 事实['mode']=='clean':#变成干净
        推迟=当前['open'] and 焦点在内#焦点还在
        return {'mode':事实['mode'],'activityCount':事实['activityCount'],'open':推迟,'pendingCleanCollapse':推迟}#可能推迟
    if 当前['mode']=='clean' or (事实['mode']=='abnormal' and 当前['mode']!='abnormal'):#从干净进入，或新出现异常
        return {'mode':事实['mode'],'activityCount':事实['activityCount'],'open':True,'pendingCleanCollapse':False}#展开
    return {'mode':事实['mode'],'activityCount':事实['activityCount'],'open':当前['open'],'pendingCleanCollapse':False}#保持开合

def 收起待定(状态):#失焦时完成推迟的收起
    '没有待定就原样返回'
    if not 状态['pendingCleanCollapse']:#没有
        return 状态#原样
    return {'mode':状态['mode'],'activityCount':状态['activityCount'],'open':False,'pendingCleanCollapse':False}#收起

def 阶段状态摘要(成员表,翻译):#折叠时右侧的状态短语
    '没有进行中的异常时只显示已完成数量'
    计数={}#状态到数量
    for 成员 in 成员表:#逐个
        计数[成员['status']]=计数.get(成员['status'],0)+1#加一
    活跃=[状态 for 状态 in ('running','failed','cancelled','interrupted') if 计数.get(状态,0)>0]#还需要露出的状态
    if len(活跃)==0:#全都完成
        return 状态计数('completed',计数.get('completed',0),翻译)#已完成
    可见=['completed']+活跃 if 'interrupted' in 活跃 and 计数.get('completed',0)>0 else 活跃#中断时带上已完成
    return ' · '.join(状态计数(状态,计数.get(状态,0),翻译) for 状态 in 可见)#拼起来

def 取字段(对象,键):#dict 或对象
    '没有这个字段则 None'
    if 对象 is None:#空
        return None#无
    if isinstance(对象,dict):#字典
        return 对象[键] if 键 in 对象 else None#键
    return getattr(对象,键,None)#属性

def 可导航成员(会话,阶段表,父标识,状态表):#仍在跑且目录里也在跑的子会话
    '点了能打开的子会话 id'
    目录=取字段(取字段(会话,'projectionsBySession'),父标识)#该父会话的投影
    册=取字段(取字段(目录,'values'),'subagentCatalog')#子会话目录
    结果=[]#可打开
    for 阶段 in 阶段表:#逐阶段
        for 成员 in 阶段['members']:#逐成员
            子=None#目录项
            if isinstance(册,list):#有目录
                for 项 in 册:#找
                    if 取字段(项,'id')==成员['childId']:#命中
                        子=项#记下
                        break#停
            if 成员['status']!='running' or 子 is None:#不是正在跑
                continue#跳过
            子标识=取字段(子,'id')#id
            快照=状态表.get(子标识) if hasattr(状态表,'get') else 取字段(状态表,子标识)#状态快照
            在跑=取字段(快照,'running')#快照里的运行位
            if 在跑 is None:#快照没有
                按标识=取字段(会话,'byId')#列表
                在跑=取字段(取字段(按标识,子标识),'running')#列表里的运行位
            if 在跑 is True:#确实在跑
                结果.append(成员['childId'])#可打开
    return 结果#列表

class 工作流运行面板:#一个持久工作流运行
    '披露状态留在实例上，渲染时按最新事实推进'
    def __init__(自身,属性=None):#构造
        '记下 props'
        自身.属性=属性 if 属性 is not None else {}#props
        自身.披露=None#第一次渲染时建立
        自身.焦点={}#run 或阶段键是否含焦点

    def 更新(自身,属性):#props 变了
        '换上最新 props'
        自身.属性=属性 if 属性 is not None else {}#最新

    def 设焦点(自身,键,在内):#宿主报告焦点
        '键是 run 或阶段 key'
        自身.焦点[键]=在内#记下

    def 切换运行(自身):#手点运行头
        '取消推迟收起'
        if 自身.披露 is None:#还没渲染
            return#无
        运行=dict(自身.披露['run'])#拷贝
        运行['open']=not 运行['open']#翻转
        运行['pendingCleanCollapse']=False#取消推迟
        自身.披露={'run':运行,'phases':自身.披露['phases']}#写回

    def 切换阶段(自身,键):#手点阶段头
        '没有这份状态则忽略'
        if 自身.披露 is None or 键 not in 自身.披露['phases']:#无
            return#无
        阶段=dict(自身.披露['phases'][键])#拷贝
        阶段['open']=not 阶段['open']#翻转
        阶段['pendingCleanCollapse']=False#取消推迟
        阶段表=dict(自身.披露['phases'])#拷贝表
        阶段表[键]=阶段#换上
        自身.披露={'run':自身.披露['run'],'phases':阶段表}#写回

    def 运行失焦(自身):#运行内容失焦
        '完成推迟的收起'
        if 自身.披露 is None:#无
            return#无
        运行=收起待定(自身.披露['run'])#可能收起
        if 运行 is not 自身.披露['run']:#变了
            自身.披露={'run':运行,'phases':自身.披露['phases']}#写回

    def 阶段失焦(自身,键):#阶段内容失焦
        '完成这一阶段推迟的收起'
        if 自身.披露 is None or 键 not in 自身.披露['phases']:#无
            return#无
        阶段=收起待定(自身.披露['phases'][键])#可能收起
        if 阶段 is 自身.披露['phases'][键]:#没变
            return#停
        阶段表=dict(自身.披露['phases'])#拷贝
        阶段表[键]=阶段#换上
        自身.披露={'run':自身.披露['run'],'phases':阶段表}#写回

    def _推进(自身,阶段事实表,运行事实值):#按当前焦点推进披露
        '新阶段用初始状态；已有阶段用推进'
        if 自身.披露 is None:#第一次
            自身.披露={#建立
                'run':初始披露(运行事实值),#运行
                'phases':{键:初始披露(事实) for 键,事实 in 阶段事实表},#阶段
            }#结束
            return#停
        阶段表={}#新表
        阶段变了=len(自身.披露['phases'])!=len(阶段事实表)#数量变了
        阶段开了新一轮=False#有阶段离开干净
        for 键,事实 in 阶段事实表:#逐阶段
            先前=自身.披露['phases'].get(键)#旧
            下一=初始披露(事实) if 先前 is None else 推进披露(先前,事实,自身.焦点.get(键,False))#下一
            阶段表[键]=下一#记下
            if 下一 is not 先前:#变了
                阶段变了=True#标记
            if 先前 is not None and 先前['mode']=='clean' and (事实['mode']!='clean' or 事实['activityCount']!=先前['activityCount']):#离开干净
                阶段开了新一轮=True#标记
        推进运行=推进披露(自身.披露['run'],运行事实值,自身.焦点.get('run',False))#运行
        if 阶段开了新一轮 and 运行事实值['mode']!='clean' and not 推进运行['open']:#子阶段重新忙而运行头是关的
            运行={'mode':推进运行['mode'],'activityCount':推进运行['activityCount'],'open':True,'pendingCleanCollapse':False}#撑开
        else:#用推进结果
            运行=推进运行#原样
        if 运行 is not 自身.披露['run'] or 阶段变了:#有变化
            自身.披露={'run':运行,'phases':阶段表}#写回

    def 渲染(自身):#视图
        '运行头套阶段列表，阶段头套成员行'
        属性=自身.属性#props
        节点=属性['node']#聊天节点
        翻译=属性['t']#文案
        数据=节点['data']#载荷
        阶段事实表=[(阶段['key'],阶段事实(阶段)) for 阶段 in 数据['phases']]#阶段事实
        运行事实值=运行事实(数据['status'],阶段事实表)#运行事实
        自身._推进(阶段事实表,运行事实值)#推进披露
        状态表=属性['useSessionStatus'](lambda 值:值) if 'useSessionStatus' in 属性 and callable(属性['useSessionStatus']) else {}#状态
        def 选择(会话):#挑可导航成员
            '按当前阶段与状态表'
            return 可导航成员(会话,数据['phases'],属性['sessionId'],状态表)#列表
        可导航=属性['useSessions'](选择,浅相等) if 'useSessions' in 属性 and callable(属性['useSessions']) else []#可打开
        打开会话=属性['openSession']#打开子会话
        阶段视图=[]#阶段
        for 阶段 in 数据['phases']:#逐阶段
            披露=自身.披露['phases'].get(阶段['key'],初始披露(阶段事实(阶段)))#披露
            成员视图=[]#成员
            for 成员 in 阶段['members']:#逐成员
                名=可读成员(成员['label'],翻译)#名
                能开=成员['childId'] in 可导航#可点
                成员视图.append({#一行
                    'type':'workflow-member','seq':成员['seq'],'status':成员['status'],'name':名,#身份
                    'navigable':能开,#可点
                    'label':翻译('member.open',{'name':名}) if 能开 else 名,#无障碍名
                    'dot':状态点({'state':点状态(成员['status'])})(),#点
                    'statusText':翻译(状态键[成员['status']]),#状态文案
                    'onClick':(lambda 子标识=成员['childId']:打开会话({'parentSessionId':属性['sessionId'],'childSessionId':子标识,'mode':'one-shot'})) if 能开 else None,#打开
                })#结束
            阶段视图.append({#一阶段
                'type':'workflow-phase','key':阶段['key'],#身份
                'pendingCleanCollapse':披露['pendingCleanCollapse'],#推迟收起
                'onBlur':lambda 键=阶段['key']:自身.阶段失焦(键),#失焦
                'header':披露行({#头
                    'icon':图标右chevron14(),'title':可读阶段(阶段['phase'],翻译),#标题
                    'open':披露['open'],'onToggle':lambda 键=阶段['key']:自身.切换阶段(键),#开合
                    'expandable':True,'expandOnRowClick':True,'previewChevron':False,'keepContentWhenOpen':True,#行为
                    'rowClassName':'phaseHeader','leadingClassName':'phaseLeading','titleClassName':'phaseTitle',#类
                    'collapsedContent':[{'type':'separator'},{'type':'phase-count','text':成员数量(len(阶段['members']),翻译)},{'type':'phase-status','text':阶段状态摘要(阶段['members'],翻译)}],#折叠侧
                    'children':{'type':'members','className':'members','rows':成员视图},#成员
                })(),#渲染
            })#结束
        运行披露=自身.披露['run']#运行披露
        return {#整面板
            'type':'workflow-run','cssModule':'面板.module.css','status':数据['status'],#根
            'pendingCleanCollapse':运行披露['pendingCleanCollapse'],#推迟收起
            'onBlur':自身.运行失焦,#失焦
            'header':披露行({#运行头
                'icon':图标右chevron14(),'title':翻译('run.title',{'name':数据['name']}),#标题
                'open':运行披露['open'],'onToggle':自身.切换运行,#开合
                'expandable':True,'expandOnRowClick':True,'previewChevron':False,'keepContentWhenOpen':True,#行为
                'rowClassName':'runHeader','leadingClassName':'runLeading','titleClassName':'runTitle',#类
                'collapsedContent':[#折叠侧
                    {'type':'separator'},#点
                    {'type':'run-summary','text':成员数量(运行事实值['activityCount'],翻译)},#成员数
                    {'type':'status-tail','status':数据['status'],'dot':状态点({'state':点状态(数据['status'])})(),'text':翻译(状态键[数据['status']])},#状态
                ],#结束
                'children':{'type':'phase-list','className':'phaseList','empty':翻译('run.empty') if len(阶段视图)==0 else None,'phases':阶段视图},#阶段
            })(),#渲染
        }#结束

    def __call__(自身,属性=None,**关键字参数):#对齐其它界面组件
        '有新 props 就先更新再渲染'
        if 属性 is not None or len(关键字参数)>0:#有
            合并=dict(属性 if 属性 is not None else {})#基
            合并.update(关键字参数)#覆盖
            自身.更新(合并)#刷
        return 自身.渲染()#视图
