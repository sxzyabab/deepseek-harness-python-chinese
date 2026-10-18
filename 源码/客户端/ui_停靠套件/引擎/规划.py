'把一次交互规划成操作。这里不施加，也不持有状态'
from .约束 import 可分割,钳制尺寸,浮动默认尺寸,区位分割
from .操作 import 施加操作
from .树 import 停靠窗格标识列表,查找标签窗格,首停靠窗格标识,取节点,取窗格,取标签

__all__=[
    '查找窗格内容标签','查找内容标签','活动停靠窗格标识',
    '规划设展开','规划设模式','规划分窗格','规划加标签','规划打开内容',
    '规划复制标签','规划安置标签','规划投放标签','规划浮出标签',
    '规划收回浮窗','规划调整分割','规划落定',
]

浮动级联步=24
浮动原点横=160
浮动原点纵=120
无操作=()

def 查找窗格内容标签(状态,窗格标识,内容标识,种类=None):
    '这一格里第一张带着该内容标识的标签。种类省略则不限种类'
    for 标签标识 in 取窗格(状态,窗格标识)['tabs']:
        if 标签标识 not in 状态['tabs']:
            continue
        标签=状态['tabs'][标签标识]
        if 标签['contentId']==内容标识 and (种类 is None or 标签['kind']==种类):
            return 标签标识
    return None

def 查找内容标签(状态,内容标识,种类=None):
    '先搜停靠窗格，再搜浮动窗格，找第一张带着该内容的标签'
    窗格序=[*停靠窗格标识列表(状态),*状态['floats']]
    for 窗格标识 in 窗格序:
        找到=查找窗格内容标签(状态,窗格标识,内容标识,种类)
        if 找到 is not None:
            return 找到
    return None

def 活动停靠窗格标识(状态):
    '新标签该进哪一格。活动格若在停靠里就用它，否则用第一块停靠窗格'
    活动=取窗格(状态,状态['activePaneId'])
    if 活动['host']=='dock':
        return 活动['id']
    return 首停靠窗格标识(状态)

def 标签进入(来源,标签标识,到窗格,下标):
    '按标签现在的宿主，选收回浮动或搬到别的停靠窗格'
    if 来源['host']=='float':
        return {'type':'unfloat','paneId':来源['id'],'toPaneId':到窗格,'index':下标}
    return {'type':'moveTab','tabId':标签标识,'toPaneId':到窗格,'index':下标}

def 规划设展开(状态,展开):
    '展开或折叠停靠区。已经是这个值就没有操作'
    if 状态['expanded']==展开:
        return 无操作
    return [{'type':'setExpanded','expanded':展开}]

def 规划设模式(状态,模式):
    '切换停靠区的呈现。已经是这个值就没有操作'
    if 状态['mode']==模式:
        return 无操作
    return [{'type':'setMode','mode':模式}]

def 规划分窗格(状态,铸造,窗格标识=None,造窗格标签=None):
    '在窗格右侧切开，并给新窗格种一张标签。窗格数到顶就没有操作'
    if not 可分割(状态):
        return 无操作
    if 窗格标识 is None:
        目标=活动停靠窗格标识(状态)
    else:
        目标=窗格标识
    if 取窗格(状态,目标)['host']!='dock':
        return 无操作
    新窗格=铸造('pane')
    操作表=[{
        'type':'split',
        'paneId':目标,
        'axis':'row',
        'direction':'after',
        'newPaneId':新窗格,
        'newSplitId':铸造('split'),
    }]
    if 造窗格标签 is not None:
        种子=造窗格标签(铸造('tab'))
        if 种子 is not None:
            操作表.append({'type':'openTab','paneId':新窗格,'tab':种子,'index':0})
    return 操作表

def 规划加标签(状态,铸造,窗格标识,造标签=None):
    '把嵌入方的种子标签加到停靠窗格条带末尾'
    if 造标签 is None:
        return 无操作
    窗格=取窗格(状态,窗格标识)
    if 窗格['host']!='dock':
        return 无操作
    return [{
        'type':'openTab',
        'paneId':窗格标识,
        'tab':造标签(铸造('tab')),
        'index':len(窗格['tabs']),
    }]

def 规划打开内容(状态,铸造,输入):
    '打开内容。已经有这张内容就改为聚焦。返回操作和落定的标签标识'
    if 'revealIfOpened' in 输入 and 输入['revealIfOpened'] is False:
        已有=None
    else:
        已有=查找内容标签(状态,输入['contentId'],输入['kind'])
    if 已有 is not None:
        return {'ops':[{'type':'focusTab','tabId':已有}],'tabId':已有}
    if 'paneId' in 输入 and 输入['paneId'] is not None:
        窗格标识=输入['paneId']
    else:
        窗格标识=活动停靠窗格标识(状态)
    标签={
        'id':铸造('tab'),
        'kind':输入['kind'],
        'contentId':输入['contentId'],
        'title':输入['title'],
    }
    if 'index' in 输入 and 输入['index'] is not None:
        下标=输入['index']
    else:
        下标=len(取窗格(状态,窗格标识)['tabs'])
    return {
        'ops':[{'type':'openTab','paneId':窗格标识,'tab':标签,'index':下标}],
        'tabId':标签['id'],
    }

def 规划复制标签(状态,铸造,标签标识):
    '在原标签旁边再开一张独立副本。浮动标签的副本进活动停靠窗格'
    来源=取标签(状态,标签标识)
    窗格=查找标签窗格(状态,标签标识)
    if 窗格['host']=='dock':
        宿主=窗格['id']
        下标=窗格['tabs'].index(标签标识)+1
    else:
        宿主=活动停靠窗格标识(状态)
        下标=len(取窗格(状态,宿主)['tabs'])
    标签=dict(来源)
    标签['id']=铸造('tab')
    return {'ops':[{'type':'openTab','paneId':宿主,'tab':标签,'index':下标}],'tabId':标签['id']}

def 规划安置标签(状态,标签标识,到窗格,下标):
    '把标签放到条带的明确槽位。同一格是重排，浮动则是收回'
    来源=查找标签窗格(状态,标签标识)
    if 取窗格(状态,到窗格)['host']!='dock':
        return 无操作
    if 来源['id']==到窗格:
        从哪=来源['tabs'].index(标签标识)
        if 下标>从哪:
            到哪=下标-1
        else:
            到哪=下标
        if 到哪==从哪:
            return 无操作
        return [{'type':'reorderTab','tabId':标签标识,'index':到哪}]
    return [标签进入(来源,标签标识,到窗格,下标)]

def 规划投放标签(状态,铸造,标签标识,目标窗格,区,造标签=None):
    '在窗格正文上松开。中心是移入，边缘是切开再放入'
    来源=查找标签窗格(状态,标签标识)
    目标=取窗格(状态,目标窗格)
    if 目标['host']!='dock':
        return 无操作
    切开=区位分割(区)
    if 切开 is None:
        if 来源['id']==目标窗格:
            return 无操作
        return [标签进入(来源,标签标识,目标窗格,len(目标['tabs']))]
    腾空=来源['id']==目标窗格 and len(来源['tabs'])==1
    if 腾空 and 造标签 is None:
        return 无操作
    if not 可分割(状态):
        return 无操作
    新窗格=铸造('pane')
    操作表=[{
        'type':'split',
        'paneId':目标窗格,
        'axis':切开['axis'],
        'direction':切开['direction'],
        'newPaneId':新窗格,
        'newSplitId':铸造('split'),
    }]
    if 腾空 and 造标签 is not None:
        操作表.append({
            'type':'openTab',
            'paneId':目标窗格,
            'tab':造标签(铸造('tab')),
            'index':len(来源['tabs']),
        })
    操作表.append(标签进入(来源,标签标识,新窗格,0))
    return 操作表

def 规划浮出标签(状态,铸造,标签标识,矩形=None):
    '把标签拿成浮动面板。没给矩形就相对上一块往右下错一档'
    步=len(状态['floats'])*浮动级联步
    新窗格=铸造('float')
    if 矩形 is None:
        矩形={
            'x':浮动原点横+步,
            'y':浮动原点纵+步,
            'width':浮动默认尺寸['width'],
            'height':浮动默认尺寸['height'],
        }
    return {
        'ops':[{'type':'float','tabId':标签标识,'newPaneId':新窗格,'rect':矩形}],
        'paneId':新窗格,
    }

def 规划收回浮窗(状态,窗格标识,到窗格=None):
    '把浮动面板里的标签送回停靠树'
    if 到窗格 is None:
        去处=活动停靠窗格标识(状态)
    else:
        去处=到窗格
    return [{
        'type':'unfloat',
        'paneId':窗格标识,
        'toPaneId':去处,
        'index':len(取窗格(状态,去处)['tabs']),
    }]

def 规划调整分割(分割标识,份额表,下限=None):
    '记下分割条拖完的份额，并钳到窗格下限'
    return [{'type':'resize','splitId':分割标识,'sizes':钳制尺寸(份额表,下限)}]

def 规划落定(状态,铸造,造标签=None):
    '意图之后清掉空的停靠窗格。根窗格空了就重新种一张，没有工厂就留空'
    操作表=[]
    当前=状态
    while True:
        清空=None
        for 标识 in 停靠窗格标识列表(当前):
            if 标识!=当前['rootId'] and len(取窗格(当前,标识)['tabs'])==0:
                清空=标识
                break
        if 清空 is None:
            break
        合并={'type':'merge','paneId':清空}
        操作表.append(合并)
        当前=施加操作(当前,合并)['state']
    根=取节点(当前,当前['rootId'])
    if 根['kind']=='pane' and len(根['tabs'])==0 and 造标签 is not None:
        操作表.append({
            'type':'openTab',
            'paneId':根['id'],
            'tab':造标签(铸造('tab')),
            'index':0,
        })
    return 操作表
