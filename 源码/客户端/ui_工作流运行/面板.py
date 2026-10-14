'持久工作流运行节点：运行和阶段按状态展开或收起'
import json
import importlib.resources as 包资源
from nicegui import ui as 界面
from ..存储 import 浅相等#会话选择的比较
from ..ui_基础界面组件.状态点 import 状态点#运行和成员状态点

__all__=['工作流运行面板']#仅中文公开名

槽位键=('node','sessionId','useSessions','useSessionStatus','openSession','t')

def 读样式():
    '读同目录样式并给类名加前缀。失败时异常文案只有样式读不到，不含路径'
    try:
        原文=包资源.files(__package__).joinpath('面板.module.css').read_text(encoding='utf-8')
    except OSError:
        raise OSError('样式读不到') from None
    类名=(
        'memberLabelWrap','memberButton','memberStatus','memberLabel','memberRow',
        'phaseLeading','phaseHeader','phaseStatus','phaseCount','phaseTitle','phaseList',
        'runLeading','runSummary','runHeader','runTitle','statusTail','separator',
        'dotSlot','members','empty','phase','root',
    )
    for 名 in 类名:
        原文=原文.replace('.'+名,'.wf-'+名)
    return 原文

界面.add_css(读样式(),shared=True)

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
    成员表=阶段['members'] if isinstance(阶段,dict) and isinstance(阶段.get('members'),list) else []
    if any(是异常(成员['status']) for 成员 in 成员表 if isinstance(成员,dict) and 'status' in 成员):
        模式='abnormal'#异常
    elif any(成员['status']=='running' for 成员 in 成员表 if isinstance(成员,dict) and 'status' in 成员):
        模式='running'#运行
    else:#都结束了
        模式='clean'#干净
    return {'mode':模式,'activityCount':len(成员表)}#事实

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
        if not isinstance(成员,dict) or 'status' not in 成员:
            continue
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

def 可导航成员(会话,阶段表,父标识,状态表):
    '仍在跑、父会话对得上、并且子会话投影里有 subagent 身份的成员'
    结果={}
    按标识=取字段(会话,'byId')
    投影表=取字段(会话,'projectionsBySession')
    for 阶段 in 阶段表:
        成员表=阶段['members'] if isinstance(阶段,dict) and 'members' in 阶段 else []
        for 成员 in 成员表:
            if not isinstance(成员,dict) or 成员.get('status')!='running':
                continue
            子标识=成员.get('childId')
            子=取字段(按标识,子标识)
            if 子 is None or 取字段(子,'parentId')!=父标识:
                continue
            身份=取字段(取字段(取字段(投影表,子标识),'values'),'subagent')
            模式=取字段(身份,'mode')
            if 模式 is None:
                continue
            子会话标识=取字段(子,'id')
            if hasattr(状态表,'get'):
                快照=状态表.get(子会话标识)
            else:
                快照=取字段(状态表,子会话标识)
            在跑=取字段(快照,'running')
            if 在跑 is None:
                在跑=取字段(子,'running')
            if 在跑 is True:
                结果[子标识]=模式
    return 结果

class 工作流运行面板:#一个持久工作流运行
    '披露状态留在实例上，渲染时按最新事实推进'
    def __init__(自身,属性=None):#构造
        '记下 props'
        自身.属性=属性 if 属性 is not None else {}#props
        自身.披露=None#第一次渲染时建立
        自身.焦点={}#run 或阶段键是否含焦点
        if isinstance(自身.属性,dict) and all(键 in 自身.属性 for 键 in 槽位键):
            自身.渲染()

    def 更新(自身,属性):#props 变了
        '换上最新 props'
        自身.属性=属性 if 属性 is not None else {}#最新

    def 设焦点(自身,键,在内):#宿主报告焦点
        '键是 run 或阶段 key'
        自身.焦点[键]=在内

    def 切换运行(自身):#手点运行头
        '取消推迟收起'
        if 自身.披露 is None:#还没渲染
            return#无
        运行=dict(自身.披露['run'])#拷贝
        运行['open']=not 运行['open']#翻转
        运行['pendingCleanCollapse']=False#取消推迟
        自身.披露={'run':运行,'phases':自身.披露['phases']}#写回
        自身.请求重画()

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
        自身.请求重画()

    def 运行失焦(自身):#运行内容失焦
        '完成推迟的收起'
        if 自身.披露 is None:#无
            return#无
        运行=收起待定(自身.披露['run'])#可能收起
        if 运行 is not 自身.披露['run']:#变了
            自身.披露={'run':运行,'phases':自身.披露['phases']}#写回
            自身.请求重画()

    def 阶段失焦(自身,键):#阶段内容失焦
        '完成这一阶段推迟的收起'
        if 自身.披露 is None or 键 not in 自身.披露['phases']:#无
            return#无
        阶段=收起待定(自身.披露['phases'][键])#可能收起
        if 阶段 is 自身.披露['phases'][键]:#没变
            return
        阶段表=dict(自身.披露['phases'])#拷贝
        阶段表[键]=阶段#换上
        自身.披露={'run':自身.披露['run'],'phases':阶段表}#写回
        自身.请求重画()

    def 请求重画(自身):
        '交互之后按当前披露再画'
        if getattr(自身,'_壳',None) is not None:
            自身.渲染()

    def _推进(自身,阶段事实表,运行事实值):#按当前焦点推进披露
        '新阶段用初始状态；已有阶段用推进'
        if 自身.披露 is None:#第一次
            自身.披露={#建立
                'run':初始披露(运行事实值),#运行
                'phases':{键:初始披露(事实) for 键,事实 in 阶段事实表},#阶段
            }#结束
            return
        阶段表={}#新表
        阶段变了=len(自身.披露['phases'])!=len(阶段事实表)#数量变了
        阶段开了新一轮=False#有阶段离开干净
        for 键,事实 in 阶段事实表:#逐阶段
            先前=自身.披露['phases'].get(键)#旧
            下一=初始披露(事实) if 先前 is None else 推进披露(先前,事实,自身.焦点.get(键,False))#下一
            阶段表[键]=下一
            if 下一 is not 先前:#变了
                阶段变了=True#标记
            if 先前 is not None and 先前['mode']=='clean' and (事实['mode']!='clean' or 事实['activityCount']!=先前['activityCount']):#离开干净
                阶段开了新一轮=True#标记
        推进运行=推进披露(自身.披露['run'],运行事实值,自身.焦点.get('run',False))#运行
        if 阶段开了新一轮 and 运行事实值['mode']!='clean' and not 推进运行['open']:#子阶段重新忙而运行头是关的
            运行={'mode':推进运行['mode'],'activityCount':推进运行['activityCount'],'open':True,'pendingCleanCollapse':False}#撑开
        else:#用推进结果
            运行=推进运行#原样
        if 运行 is not 自身.披露['run'] or 阶段变了:
            自身.披露={'run':运行,'phases':阶段表}#写回

    def 键齐(自身,属性):
        '槽位要的键都在，并且钩子可以调用'
        if not isinstance(属性,dict):
            return False
        if not all(键 in 属性 for 键 in 槽位键):
            return False
        if not callable(属性['t']):
            return False
        if not callable(属性['useSessions']):
            return False
        if not callable(属性['useSessionStatus']):
            return False
        if not callable(属性['openSession']):
            return False
        return True

    def 画状态(自身,状态,翻译,类名):
        '状态点旁边是词表里的状态句'
        with 界面.row().classes(类名):
            状态点({'state':点状态(状态)}).渲染()
            if 状态 in 状态键:
                界面.label(翻译(状态键[状态]))

    def 画成员(自身,成员,翻译,可导航,打开会话,父标识):
        '能打开时用子会话投影里的 mode，不写死 one-shot'
        if not isinstance(成员,dict):
            return
        名=可读成员(成员.get('label') if isinstance(成员.get('label'),str) else '',翻译)
        状态=成员.get('status')
        模式=可导航.get(成员.get('childId')) if isinstance(可导航,dict) else None
        能开=模式 is not None
        行类='wf-memberButton' if 能开 else 'wf-memberRow'
        行=界面.row().classes(行类)
        if 能开:
            def 打开(子标识=成员.get('childId'),打开模式=模式):
                '打开该成员的子会话'
                打开会话({
                    'parentSessionId':父标识,
                    'childSessionId':子标识,
                    'mode':打开模式,
                })
            行.on('click',lambda _事件=None:打开())
            行.props('aria-label='+json.dumps(翻译('member.open',{'name':名}),ensure_ascii=False))
        with 行:
            with 界面.element('span').classes('wf-dotSlot'):
                状态点({'state':点状态(状态)}).渲染()
            with 界面.element('span').classes('wf-memberLabelWrap'):
                界面.label(名).classes('wf-memberLabel')
            if 状态 in 状态键:
                界面.label(翻译(状态键[状态])).classes('wf-memberStatus')

    def 渲染(自身):
        '只画 workflow-run；别的种类留给聊天节点自己的回退'
        属性=自身.属性
        if not 自身.键齐(属性):
            if getattr(自身,'_壳',None) is not None:
                自身._壳.clear()
            return
        def 清掉():
            '不是本节点时不留上一帧'
            if getattr(自身,'_壳',None) is not None:
                自身._壳.clear()
        节点=属性['node']
        if not isinstance(节点,dict):
            清掉()
            return
        种类=节点.get('kind')
        if 种类 is not None and 种类!='workflow-run':
            清掉()
            return
        数据=节点.get('data')
        if not isinstance(数据,dict) or not isinstance(数据.get('phases'),list):
            清掉()
            return
        if 'name' not in 数据 or 'status' not in 数据:
            清掉()
            return
        翻译=属性['t']
        阶段事实表=[]
        for 阶段 in 数据['phases']:
            if isinstance(阶段,dict) and 'key' in 阶段:
                阶段事实表.append((阶段['key'],阶段事实(阶段)))
        运行事实值=运行事实(数据['status'],阶段事实表)
        自身._推进(阶段事实表,运行事实值)
        def 原样(值):
            '原样返回状态'
            return 值
        状态表=属性['useSessionStatus'](原样)
        def 选择(会话):
            '按当前阶段与状态表挑可打开的成员'
            return 可导航成员(会话,数据['phases'],属性['sessionId'],状态表)
        可导航=属性['useSessions'](选择,浅相等)
        if not isinstance(可导航,dict):
            可导航={}
        打开会话=属性['openSession']
        运行披露=自身.披露['run']
        if getattr(自身,'_壳',None) is None:
            自身._壳=界面.column().classes('wf-root')
        自身._壳.clear()
        自身._壳.props('data-workflow-run data-run-status='+str(数据['status']))
        def 进入运行(_事件=None):
            '运行内容获得焦点'
            自身.设焦点('run',True)
        def 离开运行(_事件=None):
            '运行内容失焦后完成推迟的收起'
            自身.设焦点('run',False)
            自身.运行失焦()
        with 自身._壳:
            头=界面.row().classes('wf-runHeader')
            头.on('click',lambda _事件=None:自身.切换运行())
            with 头:
                箭头='▾' if 运行披露['open'] else '▸'
                界面.label(箭头).classes('wf-runLeading')
                界面.label(翻译('run.title',{'name':数据['name']})).classes('wf-runTitle')
                界面.element('span').classes('wf-separator')
                界面.label(成员数量(运行事实值['activityCount'],翻译)).classes('wf-runSummary')
                自身.画状态(数据['status'],翻译,'wf-statusTail')
            if 运行披露['open']:
                阶段列=界面.column().classes('wf-phaseList')
                阶段列.on('focus',进入运行)
                阶段列.on('blur',离开运行)
                with 阶段列:
                    if len(数据['phases'])==0:
                        界面.label(翻译('run.empty')).classes('wf-empty')
                    for 阶段 in 数据['phases']:
                        if not isinstance(阶段,dict) or 'key' not in 阶段:
                            continue
                        披露=自身.披露['phases'].get(阶段['key'],初始披露(阶段事实(阶段)))
                        def 切换阶段(_事件=None,键=阶段['key']):
                            '展开或收起阶段'
                            自身.切换阶段(键)
                        with 界面.column().classes('wf-phase'):
                            阶段头=界面.row().classes('wf-phaseHeader')
                            阶段头.on('click',切换阶段)
                            with 阶段头:
                                阶段箭头='▾' if 披露['open'] else '▸'
                                界面.label(阶段箭头).classes('wf-phaseLeading')
                                界面.label(可读阶段(阶段.get('phase'),翻译)).classes('wf-phaseTitle')
                                界面.element('span').classes('wf-separator')
                                成员表=阶段['members'] if isinstance(阶段.get('members'),list) else []
                                界面.label(成员数量(len(成员表),翻译)).classes('wf-phaseCount')
                                界面.label(阶段状态摘要(成员表,翻译)).classes('wf-phaseStatus')
                            if 披露['open']:
                                def 进入阶段(_事件=None,键=阶段['key']):
                                    '阶段内容获得焦点'
                                    自身.设焦点(键,True)
                                def 离开阶段(_事件=None,键=阶段['key']):
                                    '阶段内容失焦后完成推迟的收起'
                                    自身.设焦点(键,False)
                                    自身.阶段失焦(键)
                                成员列=界面.column().classes('wf-members')
                                成员列.on('focus',进入阶段)
                                成员列.on('blur',离开阶段)
                                with 成员列:
                                    for 成员 in 成员表:
                                        自身.画成员(成员,翻译,可导航,打开会话,属性['sessionId'])

    def __call__(自身,属性=None,**关键字参数):#对齐其它界面组件
        '有新 props 就先更新再渲染'
        if 属性 is not None or len(关键字参数)>0:
            合并=dict(属性 if 属性 is not None else {})#基
            合并.update(关键字参数)#覆盖
            自身.更新(合并)#刷
        return 自身.渲染()#视图
