"""意图规划：自当前状态到操作表的纯函数。

对齐上游 `ui-dockkit/src/engine/planner.ts`。公开面仅中文名。
规划铸造其操作创建的标识并强制交互限额，但不持状态、不施加。
返回空操作表表示意图对此状态无改动。铸造为可调用：铸造(前缀)->str。
"""
from .约束 import 可分割,钳制尺寸,浮动默认尺寸,区位分割#约束
from .操作 import 施加操作#操作
from .树 import 停靠窗格标识列表,查找标签窗格,首停靠窗格标识,取节点,取窗格,取标签#树

__all__=[#仅中文公开名
    '查找窗格内容标签',
    '查找内容标签',
    '活动停靠窗格标识',
    '规划设展开',
    '规划设模式',
    '规划分窗格',
    '规划加标签',
    '规划打开内容',
    '规划复制标签',
    '规划安置标签',
    '规划投放标签',
    '规划浮出标签',
    '规划收回浮窗',
    '规划调整分割',
    '规划落定',
]#公开面结束

_浮窗级联步=24#新浮窗相对上块的级联位移
_浮窗原点左=160#首块原点
_浮窗原点上=120#首块原点


def 查找窗格内容标签(状态,窗格标识,内容标识,种类=None):
    """窗内条带序首个同 contentId（可选限制 kind）；无则 None。"""
    for 标签标识 in 取窗格(状态,窗格标识)['tabs']:#条带
        if 标签标识 not in 状态['tabs']:#缺席
            continue#跳
        标签=状态['tabs'][标签标识]#记录
        if 标签['contentId']==内容标识 and (种类 is None or 标签['kind']==种类):#命中
            return 标签标识#签
    return None#无


def 查找内容标签(状态,内容标识,种类=None):
    """全表面首个同内容：停靠窗视觉序优先，再浮动。"""
    for 窗格标识 in list(停靠窗格标识列表(状态))+list(状态['floats']):#停靠先
        找到=查找窗格内容标签(状态,窗格标识,内容标识,种类)#找
        if 找到 is not None:#命中
            return 找到#签
    return None#无


def 活动停靠窗格标识(状态):
    """新标签落点：活动窗若停靠则用之，否则首停靠窗。"""
    活动=取窗格(状态,状态['activePaneId'])#活动
    if 活动['host']=='dock':#停靠
        return 活动['id']#本窗
    return 首停靠窗格标识(状态)#回退


def _签入窗(源窗,标签标识,到窗标识,下标):
    """按源宿主选 moveTab / unfloat。"""
    if 源窗['host']=='float':#浮
        return {'type':'unfloat','paneId':源窗['id'],'toPaneId':到窗标识,'index':下标}#收
    return {'type':'moveTab','tabId':标签标识,'toPaneId':到窗标识,'index':下标}#移


def 规划设展开(状态,展开):
    """设停靠区展开；已同则空。"""
    if 状态['expanded']==展开:#未变
        return []#空
    return [{'type':'setExpanded','expanded':展开}]#操作


def 规划设模式(状态,模式):
    """设呈现模式；已同则空。"""
    if 状态['mode']==模式:#未变
        return []#空
    return [{'type':'setMode','mode':模式}]#操作


def 规划分窗格(状态,铸造,窗格标识=None,造窗签=None):
    """向右分一窗并可选播种；预算满或非停靠则空。"""
    if not 可分割(状态):#满
        return []#空
    目标=活动停靠窗格标识(状态) if 窗格标识 is None else 窗格标识#目标
    if 取窗格(状态,目标)['host']!='dock':#非停靠
        return []#空
    新窗=铸造('pane')#新窗
    操作=[{#分
        'type':'split',
        'paneId':目标,
        'axis':'row',
        'direction':'after',
        'newPaneId':新窗,
        'newSplitId':铸造('split'),
    }]#操作
    if 造窗签 is not None:#播种
        种子=造窗签(铸造('tab'))#签
        if 种子 is not None:#有
            操作.append({'type':'openTab','paneId':新窗,'tab':种子,'index':0})#开签
    return 操作#列表


def 规划加标签(状态,铸造,窗格标识,造签=None):
    """在停靠窗条带末加播种签；无工厂或非停靠则空。"""
    if 造签 is None:#无种
        return []#空
    窗格=取窗格(状态,窗格标识)#窗
    if 窗格['host']!='dock':#须停靠
        return []#空
    return [{'type':'openTab','paneId':窗格标识,'tab':造签(铸造('tab')),'index':len(窗格['tabs'])}]#开


def 规划打开内容(状态,铸造,入):
    """打开内容或聚焦已有；返回 {ops, tabId}。入为 dict。"""
    if ('revealIfOpened' in 入) and 入['revealIfOpened'] is False:#强制新开
        已有=None#无
    else:#可揭示
        已有=查找内容标签(状态,入['contentId'],入['kind'])#已有
    if 已有 is not None:#揭示
        return {'ops':[{'type':'focusTab','tabId':已有}],'tabId':已有}#焦
    if ('paneId' in 入) and 入['paneId'] is not None:#显式窗
        窗=入['paneId']#落点
    else:#默认
        窗=活动停靠窗格标识(状态)#活动停靠
    签={'id':铸造('tab'),'kind':入['kind'],'contentId':入['contentId'],'title':入['title']}#新签
    if ('index' in 入) and 入['index'] is not None:#显式槽
        下标=入['index']#槽
    else:#末
        下标=len(取窗格(状态,窗)['tabs'])#末
    return {'ops':[{'type':'openTab','paneId':窗,'tab':签,'index':下标}],'tabId':签['id']}#开


def 规划复制标签(状态,铸造,标签标识):
    """旁开同内容独立签；返回 {ops, tabId}。"""
    源=取标签(状态,标签标识)#源
    窗=查找标签窗格(状态,标签标识)#窗
    if 窗['host']=='dock':#停靠
        宿主=窗['id']#宿主
        下标=窗['tabs'].index(标签标识)+1#旁
    else:#浮
        宿主=活动停靠窗格标识(状态)#回停靠
        下标=len(取窗格(状态,宿主)['tabs'])#末
    签={#副本
        'id':铸造('tab'),
        'kind':源['kind'],
        'contentId':源['contentId'],
        'title':源['title'],
    }#签
    return {'ops':[{'type':'openTab','paneId':宿主,'tab':签,'index':下标}],'tabId':签['id']}#结果


def 规划安置标签(状态,标签标识,到窗标识,下标):
    """放到明确条带槽：同窗重排，否则移入或收回。"""
    源=查找标签窗格(状态,标签标识)#源
    if 取窗格(状态,到窗标识)['host']!='dock':#须停靠
        return []#空
    if 源['id']==到窗标识:#同窗重排
        自=源['tabs'].index(标签标识)#原
        到=下标-1 if 下标>自 else 下标#去自身占位
        if 到==自:#未变
            return []#空
        return [{'type':'reorderTab','tabId':标签标识,'index':到}]#重排
    return [_签入窗(源,标签标识,到窗标识,下标)]#移


def 规划投放标签(状态,铸造,标签标识,目标窗标识,区,造签=None):
    """投放：中心移入，边沿分裂就座；唯一签离本窗边沿时需造签回填，否则空。"""
    源=查找标签窗格(状态,标签标识)#源
    目=取窗格(状态,目标窗标识)#目
    if 目['host']!='dock':#须停靠
        return []#空
    分=区位分割(区)#分裂
    if 分 is None:#中心
        if 源['id']==目标窗标识:#同窗
            return []#空
        return [_签入窗(源,标签标识,目标窗标识,len(目['tabs']))]#移末
    腾空=源['id']==目标窗标识 and len(源['tabs'])==1#唯一签离本窗
    if 腾空 and 造签 is None:#需回填却无工厂
        return []#空
    if not 可分割(状态):#满
        return []#空
    新窗=铸造('pane')#新
    操作=[{#分裂
        'type':'split',
        'paneId':目标窗标识,
        'axis':分['axis'],
        'direction':分['direction'],
        'newPaneId':新窗,
        'newSplitId':铸造('split'),
    }]#操作
    if 腾空 and 造签 is not None:#回填原窗
        操作.append({'type':'openTab','paneId':目标窗标识,'tab':造签(铸造('tab')),'index':len(源['tabs'])})#回填
    操作.append(_签入窗(源,标签标识,新窗,0))#移入新格
    return 操作#操作


def 规划浮出标签(状态,铸造,标签标识,矩形=None):
    """签出浮窗；返回 {ops, paneId}。"""
    步=len(状态['floats'])*_浮窗级联步#级联
    新窗=铸造('float')#浮 id
    if 矩形 is None:#默认级联
        矩形={#矩形
            'x':_浮窗原点左+步,
            'y':_浮窗原点上+步,
            'width':浮动默认尺寸['width'],
            'height':浮动默认尺寸['height'],
        }#矩
    return {'ops':[{'type':'float','tabId':标签标识,'newPaneId':新窗,'rect':矩形}],'paneId':新窗}#结果


def 规划收回浮窗(状态,窗格标识,到窗标识=None):
    """浮签回停靠；默认落到活动停靠窗末。"""
    目=活动停靠窗格标识(状态) if 到窗标识 is None else 到窗标识#目
    return [{'type':'unfloat','paneId':窗格标识,'toPaneId':目,'index':len(取窗格(状态,目)['tabs'])}]#操作


def 规划调整分割(分割标识,尺寸表,下限=None):
    """记分隔拖动净份额（已夹紧）。"""
    if 下限 is None:#缺省
        份额=钳制尺寸(尺寸表)#默认下限
    else:#显式
        份额=钳制尺寸(尺寸表,下限)#夹
    return [{'type':'resize','splitId':分割标识,'sizes':份额}]#操作


def 规划落定(状态,铸造,造签=None):
    """意图后落定：并掉空停靠非根窗；根空则重播种子。"""
    操作=[]#列表
    当=状态#游标
    while True:#并空非根
        空=None#候选
        for 标识 in 停靠窗格标识列表(当):#逐窗
            if 标识!=当['rootId'] and len(取窗格(当,标识)['tabs'])==0:#空非根
                空=标识#记下
                break#一格
        if 空 is None:#无空
            break#止
        并={'type':'merge','paneId':空}#并
        操作.append(并)#记
        当=施加操作(当,并)['state']#进
    根=取节点(当,当['rootId'])#根
    if 根['kind']=='pane' and len(根['tabs'])==0 and 造签 is not None:#根空重播
        操作.append({'type':'openTab','paneId':根['id'],'tab':造签(铸造('tab')),'index':0})#播
    return 操作#列表
