"""持久化工作流运行面板：按状态驱动运行与阶段 disclosure。

对齐上游 `ui-workflow-run/src/client/WorkflowRunPanel.tsx`。公开面仅中文名。
"""
from .工作流定义 import 取字段#字段读取

__all__=['工作流运行面板','样式表','点状态','可读阶段','可读成员','可导航成员']#仅中文公开名

状态文案键={#展示状态 → 词典键
    'running':'status.running',#运行中
    'completed':'status.completed',#已完成
    'failed':'status.failed',#失败
    'cancelled':'status.cancelled',#已取消
    'interrupted':'status.interrupted',#已中断
}#状态键结束

样式表='''#对齐 WorkflowRunPanel.module.css
.root{width:100%;min-width:0}
.runHeader{box-sizing:border-box;display:flex;align-items:center;gap:6px;width:100%;min-width:0;height:32px;padding:0 8px;border-radius:8px;background:var(--dsw-alias-bg-module-platform)}
.runHeader:focus-visible{outline:2px solid var(--dsw-alias-state-business-primary);outline-offset:-2px}
.runLeading{display:inline-flex;flex:none;width:16px;height:16px;align-items:center;justify-content:center;margin-right:0;color:var(--dsw-alias-label-tertiary)}
.runTitle{overflow:hidden;flex:none;max-width:42%;color:var(--dsw-alias-label-secondary);font-size:14px;font-weight:510;line-height:24px;text-overflow:ellipsis;white-space:nowrap}
.runSummary{overflow:hidden;flex:1;min-width:0;color:var(--dsw-alias-label-tertiary);font-size:12px;line-height:18px;text-overflow:ellipsis;white-space:nowrap}
.statusTail{display:inline-flex;flex:none;height:20px;align-items:center;gap:4px;overflow:hidden;font-size:11px;font-weight:510;line-height:16px;color:var(--dsw-alias-label-secondary);white-space:nowrap}
.phaseHeader{box-sizing:border-box;display:flex;align-items:center;gap:6px;width:100%;min-width:0;height:32px}
.phaseHeader:focus-visible{outline:2px solid var(--dsw-alias-state-business-primary);outline-offset:-2px;border-radius:4px}
.phaseLeading{display:inline-flex;flex:none;width:16px;height:16px;align-items:center;justify-content:center;margin-right:0;color:var(--dsw-alias-label-tertiary)}
.phaseTitle{overflow:hidden;flex:0 1 auto;min-width:0;max-width:42%;color:var(--dsw-alias-label-secondary);font-size:14px;line-height:24px;text-overflow:ellipsis;white-space:nowrap}
.phaseCount{overflow:hidden;flex:1;min-width:0;color:var(--dsw-alias-label-tertiary);font-size:13px;line-height:20px;text-overflow:ellipsis;white-space:nowrap}
.phaseStatus{overflow:hidden;flex:none;width:132px;color:var(--dsw-alias-label-secondary);font-size:13px;line-height:20px;text-align:right;text-overflow:ellipsis;white-space:nowrap}
.separator{flex:none;width:2px;height:2px;border-radius:50%;background:var(--dsw-alias-label-tertiary)}
.phaseList{display:flex;flex-direction:column;gap:4px;min-width:0;padding:4px 0 0 16px}
.phase{min-width:0}
.members{display:flex;flex-direction:column;gap:2px;min-width:0;padding:0 0 0 16px}
.memberRow,.memberButton{display:flex;align-items:center;gap:12px;width:100%;min-width:0;min-height:24px;padding:0;border:0;border-radius:4px;background:transparent;color:var(--dsw-alias-label-secondary);font:inherit;text-align:left}
.memberButton{cursor:pointer}
.memberButton .memberLabel{color:var(--dsw-alias-state-business-primary);text-decoration:underline;text-underline-position:from-font}
.dotSlot{display:inline-flex;flex:none;width:16px;height:24px;align-items:center;justify-content:center;overflow:hidden}
.memberButton:focus-visible{outline:none}
.memberButton:focus-visible .memberLabelWrap{outline:2px solid var(--dsw-alias-state-business-primary);outline-offset:-1px}
.memberLabelWrap{display:flex;overflow:hidden;flex:1;min-width:0;height:24px;align-items:center;padding:0 2px;border-radius:4px}
.memberLabel{overflow:hidden;flex:1;min-width:0;color:var(--dsw-alias-label-secondary);font-size:14px;line-height:24px;text-overflow:ellipsis;white-space:nowrap}
.memberStatus{flex:none;overflow:hidden;width:64px;color:var(--dsw-alias-label-secondary);font-size:13px;line-height:20px;text-align:right;text-overflow:ellipsis;white-space:nowrap}
.empty{color:var(--dsw-alias-label-tertiary);font-size:13px;line-height:20px;padding:0}
@media (max-width:560px){.phaseList,.members{padding-left:12px}}
'''#样式表结束

def 点状态(状态):#展示状态 → 状态点
    """把运行/成员展示状态映射为 StateDot 状态。"""
    if 状态=='running':#运行中
        return 'ongoing'#进行中点
    if 状态=='completed':#已完成
        return 'done'#完成点
    if 状态=='failed':#失败
        return 'error'#错误点
    if 状态 in ('cancelled','interrupted'):#取消或中断
        return 'warning'#警告点
    return 状态#其余原样

def 可读阶段(阶段,翻译):#阶段展示名
    """缺席用未分阶段；空串用空阶段名占位。"""
    if 阶段 is None:#缺席
        return 翻译('phase.unassigned')#未分阶段
    if 阶段=='':#空串身份
        return 翻译('phase.empty')#空阶段名
    return 阶段#原样

def 可读成员(标签,翻译):#成员展示名
    """空标签用空成员名占位。"""
    if 标签=='':#空名
        return 翻译('member.empty')#占位
    return 标签#原样

def 状态计数文案(状态,数量,翻译):#状态计数
    """本地化状态计数片段。"""
    return 翻译('statusCount.'+状态,{'count':数量})#带 count

def 成员计数文案(数量,翻译):#成员计数
    """本地化成员总数。"""
    return 翻译('run.members.one' if 数量==1 else 'run.members.other',{'count':数量})#单复数

def 阶段需展开(阶段):#阶段是否强制展开
    """任一成员未完成则强制展开。"""
    for 成员 in 取字段(阶段,'members') or []:#逐成员
        if 取字段(成员,'status')!='completed':#未完成
            return True#需展开
    return False#可折叠

def 阶段状态摘要(成员们,翻译):#阶段尾部聚合状态
    """按活跃状态拼聚合文案；纯完成则报完成计数。"""
    计数={}#状态 → 数量
    for 成员 in 成员们:#逐成员
        状态=取字段(成员,'status')#展示状态
        计数[状态]=计数.get(状态,0)+1#累加
    def 取数(状态):#某状态数量
        """读计数表。"""
        return 计数.get(状态,0)#缺省 0
    活跃=[状态 for 状态 in ('running','failed','cancelled','interrupted') if 取数(状态)>0]#活跃状态
    if len(活跃)==0:#全完成
        return 状态计数文案('completed',取数('completed'),翻译)#完成计数
    if 'interrupted' in 活跃 and 取数('completed')>0:#中断且有完成
        可见=['completed']+活跃#完成排前
    else:#常规
        可见=活跃#仅活跃
    return ' · '.join(状态计数文案(状态,取数(状态),翻译) for 状态 in 可见)#拼摘要

def 可导航成员(会话列表,阶段们,父标识):#可打开的子会话
    """成员仍在运行、在普通列表、origin 为 subagent、parentId 匹配且仍标记运行。"""
    普通=set(取字段(会话列表,'ids') or [])#普通会话 id 集
    按标识=取字段(会话列表,'byId') or {}#摘要表
    结果=[]#可导航 id
    for 阶段 in 阶段们:#各阶段
        for 成员 in 取字段(阶段,'members') or []:#各成员
            子标识=取字段(成员,'childId')#子会话 id
            摘要=按标识.get(子标识) if isinstance(按标识,dict) else 取字段(按标识,子标识)#摘要
            if (取字段(成员,'status')=='running'#仍运行
                and 子标识 in 普通#在普通列表
                and 取字段(摘要,'origin')=='subagent'#子智能体起源
                and 取字段(摘要,'parentId')==父标识#父级匹配
                and 取字段(摘要,'running')):#列表仍标记运行
                结果.append(子标识)#可导航
    return 结果#可导航列表

class 状态展开行:#可手动折叠或强制展开的 disclosure
    """干净时允许本地折叠；需强制展开时 open 且不可点。"""
    def __init__(自身,需展开,干净周期键=None):#展开政策
        """记下是否强制展开与干净周期键。"""
        自身.需展开=需展开#强制展开
        自身.干净周期键=干净周期键#成员数变化 remount
        自身.打开=False#本地折叠态

    def 切换(自身):#手动切换
        """仅非强制展开时可切换。"""
        if 自身.需展开:#强制展开
            return#忽略
        自身.打开=not 自身.打开#翻转

    def 是否打开(自身):#当前打开态
        """强制展开则恒真，否则本地态。"""
        if 自身.需展开:#强制
            return True#打开
        return 自身.打开#本地

class 工作流运行面板:#按键 Chat 渲染器
    """渲染一次持久工作流运行及其阶段成员。"""
    def __init__(自身,属性):#节点、会话、钩子与注入
        """记下节点载荷、会话 id、翻译与打开会话回调。"""
        自身.节点=取字段(属性,'node')#视图节点
        自身.会话标识=取字段(属性,'sessionId')#当前会话
        自身.用会话=取字段(属性,'useSessions')#会话列表选择器钩
        自身.打开会话=取字段(属性,'openSession')#注入的打开回调
        自身.翻译=取字段(属性,'t')#locale 翻译
        自身.阶段展开={}#阶段键 → 状态展开行
        自身.运行展开=None#运行级展开行

    def 数据(自身):#节点渲染数据
        """取出 workflow-run 载荷。"""
        return 取字段(自身.节点,'data')#载荷

    def 渲染(自身):#结构树
        """返回运行 disclosure 与阶段列表结构树。"""
        数据=自身.数据()#载荷
        阶段们=取字段(数据,'phases') or []#阶段列表
        总成员=sum(len(取字段(阶段,'members') or []) for 阶段 in 阶段们)#成员总数
        需展开=取字段(数据,'status')!='completed' or any(阶段需展开(阶段) for 阶段 in 阶段们)#运行强制展开
        if 自身.运行展开 is None or 自身.运行展开.需展开!=需展开:#重建运行展开行
            自身.运行展开=状态展开行(需展开)#新行
        可导航=自身.用会话(lambda 列表:可导航成员(列表,阶段们,自身.会话标识)) if 自身.用会话 else []#可导航子会话
        阶段节点=[]#阶段结构
        if len(阶段们)==0:#无成员
            阶段节点=[{'type':'span','class':'empty','children':[自身.翻译('run.empty')]}]#空态
        else:#有阶段
            for 阶段 in 阶段们:#逐阶段
                键=取字段(阶段,'key')#阶段键
                成员们=取字段(阶段,'members') or []#成员
                阶需=阶段需展开(阶段)#阶段强制展开
                展开=自身.阶段展开.get(键)#已有展开行
                if 展开 is None or 展开.需展开!=阶需 or 展开.干净周期键!=len(成员们):#需重建
                    展开=状态展开行(阶需,len(成员们))#新行
                    自身.阶段展开[键]=展开#记下
                成员节点=[]#成员行
                for 成员 in 成员们:#逐成员
                    名=可读成员(取字段(成员,'label'),自身.翻译)#展示名
                    内容=[#行内容
                        {'type':'span','class':'dotSlot','children':[{'type':'StateDot','state':点状态(取字段(成员,'status'))}]},#状态点
                        {'type':'span','class':'memberLabelWrap','data-member-label-wrap':True,'children':[{'type':'span','class':'memberLabel','data-member-label':True,'children':[名]}]},#名称
                        {'type':'span','class':'memberStatus','data-member-status-text':True,'children':[自身.翻译(状态文案键[取字段(成员,'status')])]},#状态文
                    ]#内容结束
                    可开=取字段(成员,'childId') in 可导航#是否可导航
                    if 可开:#按钮行
                        成员节点.append({'type':'button','buttonType':'button','class':'memberButton','data-member-status':取字段(成员,'status'),'aria-label':自身.翻译('member.open',{'name':名}),'onClick':('open',取字段(成员,'childId')),'children':内容})#可点
                    else:#静态行
                        成员节点.append({'type':'div','class':'memberRow','data-member-status':取字段(成员,'status'),'children':内容})#静态
                阶段节点.append({#阶段 disclosure
                    'type':'StatusDisclosure','class':'phase','open':展开.是否打开(),'expandable':not 阶需,#展开态
                    'title':可读阶段(取字段(阶段,'phase'),自身.翻译),#标题
                    'rowClassName':'phaseHeader','leadingClassName':'phaseLeading','titleClassName':'phaseTitle',#行样式
                    'collapsedContent':[#折叠尾
                        {'type':'span','class':'separator','aria-hidden':True},#分隔点
                        {'type':'span','class':'phaseCount','data-phase-count':True,'children':[成员计数文案(len(成员们),自身.翻译)]},#成员数
                        {'type':'span','class':'phaseStatus','data-phase-status-text':True,'children':[阶段状态摘要(成员们,自身.翻译)]},#聚合状态
                    ],#折叠尾结束
                    'children':[{'type':'div','class':'members','children':成员节点}],#成员列表
                    'onToggle':('phase',键),#切换键
                })#阶段结束
        运行状态=取字段(数据,'status')#运行状态
        return {#根
            'type':'section','class':'root','data-workflow-run':True,'data-run-status':运行状态,#根
            'children':[{#运行头
                'type':'StatusDisclosure','open':自身.运行展开.是否打开(),'expandable':not 需展开,#展开态
                'title':自身.翻译('run.title',{'name':取字段(数据,'name')}),#标题
                'rowClassName':'runHeader','leadingClassName':'runLeading','titleClassName':'runTitle',#行样式
                'collapsedContent':[#折叠尾
                    {'type':'span','class':'separator','aria-hidden':True},#分隔点
                    {'type':'span','class':'runSummary','children':[成员计数文案(总成员,自身.翻译)]},#成员数
                    {'type':'span','class':'statusTail','data-status':运行状态,'children':[{'type':'StateDot','state':点状态(运行状态)},{'type':'span','children':[自身.翻译(状态文案键[运行状态])]}]},#状态尾
                ],#折叠尾结束
                'children':[{'type':'div','class':'phaseList','children':阶段节点}],#阶段列表
                'onToggle':'run',#运行切换
            }],#运行头结束
        }#根结束

    def 处理动作(自身,动作):#分发交互
        """打开子会话或切换 disclosure。"""
        if 动作=='run':#运行头切换
            自身.运行展开.切换()#翻转
            return#已处理
        if isinstance(动作,tuple) and 动作[0]=='phase':#阶段切换
            展开=自身.阶段展开.get(动作[1])#对应行
            if 展开 is not None:#有行
                展开.切换()#翻转
            return#已处理
        if isinstance(动作,tuple) and 动作[0]=='open':#打开子会话
            自身.打开会话(动作[1])#注入回调
