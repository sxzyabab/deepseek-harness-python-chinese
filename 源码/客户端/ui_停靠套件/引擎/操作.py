'一次操作得到下一状态和把它撤回去的操作。标识都写在操作里，回放不会再铸造'
from ..异常 import 停靠错误,要求节点空闲,要求标签空闲,未处理
from .树 import (
    盖上,
    取窗格,
    取分割,
    取标签,
    找父分割,
    查找标签窗格,
    首停靠窗格标识,
    浮动矩形,
    浮动序号,
    唯一标签标识,
    归一份额,
    换节点,
    换标签,
    插入于,
    移除于,
    邻标签标识,
    窗格换标签,
    父中替换,
    条目表,
)

__all__=['施加操作','回放']

def 焦点快照(状态,窗格标识表):
    '记下这些窗格的活动标签，以及全局焦点和浮动叠放'
    窗格活动={}
    for 标识 in 窗格标识表:
        窗格活动[标识]=取窗格(状态,标识)['activeTabId']
    return {
        'type':'restoreFocus',
        'activePaneId':状态['activePaneId'],
        'floats':状态['floats'],
        'paneActiveTabs':窗格活动,
    }

def 抬到顶(浮层,窗格标识):
    '把这块窗格挪到浮动叠放的最上面'
    留下=[]
    for 标识 in 浮层:
        if 标识!=窗格标识:
            留下.append(标识)
    留下.append(窗格标识)
    return 留下

def 重坐焦点(状态,去掉的窗格):
    '焦点所在的窗格没了，就落到第一块停靠窗格'
    if 状态['activePaneId']!=去掉的窗格:
        return 状态
    return 盖上(状态,{'activePaneId':首停靠窗格标识(状态)})

def 改形浮动(状态,窗格,矩形):
    '改浮动矩形，同时聚焦并抬到顶'
    改后=换节点(状态,{窗格['id']:盖上(窗格,{'rect':矩形})})
    return 盖上(改后,{
        'activePaneId':窗格['id'],
        'floats':抬到顶(改后['floats'],窗格['id']),
    })

def 施加操作(状态,操作):
    '施加一条操作。状态本身不改。返回下一状态，以及按顺序撤回去的操作'
    种类=操作['type']
    if 种类=='split':
        窗格=取窗格(状态,操作['paneId'])
        if 窗格['host']!='dock':
            raise 停靠错误('layout: split requires a docked pane')
        要求节点空闲(状态,操作['newPaneId'])
        新窗格={'kind':'pane','id':操作['newPaneId'],'host':'dock','tabs':[],'activeTabId':None,'rect':None}
        父=找父分割(状态,操作['paneId'])
        if 父 is not None and 父['axis']==操作['axis']:
            序号=父['children'].index(操作['paneId'])
            if 操作['direction']=='after':
                插入点=序号+1
            else:
                插入点=序号
            子序=插入于(父['children'],插入点,操作['newPaneId'])
            份额=[]
            for 序,大小 in enumerate(父['sizes']):
                if 序==序号:
                    份额.append(大小/2)
                    份额.append(大小/2)
                else:
                    份额.append(大小)
            return {
                'state':换节点(状态,{
                    操作['newPaneId']:新窗格,
                    父['id']:盖上(父,{'children':子序,'sizes':份额}),
                }),
                'inverse':[
                    {'type':'merge','paneId':操作['newPaneId']},
                    {'type':'resize','splitId':父['id'],'sizes':父['sizes']},
                ],
            }
        要求节点空闲(状态,操作['newSplitId'])
        搬好=父中替换(状态,操作['paneId'],操作['newSplitId'])
        if 操作['direction']=='after':
            子序=[操作['paneId'],操作['newPaneId']]
        else:
            子序=[操作['newPaneId'],操作['paneId']]
        return {
            'state':换节点(搬好,{
                操作['newPaneId']:新窗格,
                操作['newSplitId']:{
                    'kind':'split',
                    'id':操作['newSplitId'],
                    'axis':操作['axis'],
                    'children':子序,
                    'sizes':[0.5,0.5],
                },
            }),
            'inverse':[{'type':'merge','paneId':操作['newPaneId']}],
        }
    if 种类=='merge':
        窗格=取窗格(状态,操作['paneId'])
        if len(窗格['tabs'])>0:
            raise 停靠错误('layout: merge requires an empty pane')
        焦点=焦点快照(状态,[])
        if 窗格['host']=='float':
            浮序=浮动序号(状态,操作['paneId'])
            去掉=换节点(盖上(状态,{'floats':移除于(状态['floats'],浮序)}),{操作['paneId']:None})
            return {
                'state':重坐焦点(去掉,操作['paneId']),
                'inverse':[
                    {'type':'insertPane','pane':窗格,'tabs':[],'attach':{'mode':'float','index':浮序}},
                    焦点,
                ],
            }
        父=找父分割(状态,操作['paneId'])
        if 父 is None:
            raise 停靠错误('layout: the docked root pane cannot be merged')
        序号=父['children'].index(操作['paneId'])
        if len(父['children'])>2:
            子序=移除于(父['children'],序号)
            份额=归一份额(移除于(父['sizes'],序号))
            去掉=换节点(状态,{
                操作['paneId']:None,
                父['id']:盖上(父,{'children':子序,'sizes':份额}),
            })
            return {
                'state':重坐焦点(去掉,操作['paneId']),
                'inverse':[
                    {
                        'type':'insertPane',
                        'pane':窗格,
                        'tabs':[],
                        'attach':{'mode':'child','parentId':父['id'],'index':序号,'sizes':父['sizes']},
                    },
                    焦点,
                ],
            }
        兄弟标识=父['children'][1-序号]
        if 兄弟标识 is None:
            raise 停靠错误('layout: merge found a split without a sibling')
        塌掉=换节点(父中替换(状态,父['id'],兄弟标识),{
            操作['paneId']:None,
            父['id']:None,
        })
        return {
            'state':重坐焦点(塌掉,操作['paneId']),
            'inverse':[
                {'type':'insertPane','pane':窗格,'tabs':[],'attach':{'mode':'wrap','targetId':兄弟标识,'split':父}},
                焦点,
            ],
        }
    if 种类=='openTab':
        窗格=取窗格(状态,操作['paneId'])
        if 窗格['host']!='dock':
            raise 停靠错误('layout: openTab requires a docked pane')
        要求标签空闲(状态,操作['tab']['id'])
        焦点=焦点快照(状态,[窗格['id']])
        坐下=换节点(换标签(状态,{操作['tab']['id']:操作['tab']}),{
            窗格['id']:窗格换标签(窗格,插入于(窗格['tabs'],操作['index'],操作['tab']['id']),操作['tab']['id']),
        })
        return {
            'state':盖上(坐下,{'activePaneId':窗格['id']}),
            'inverse':[{'type':'closeTab','tabId':操作['tab']['id']},焦点],
        }
    if 种类=='insertTab':
        窗格=取窗格(状态,操作['paneId'])
        if 窗格['host']!='dock':
            raise 停靠错误('layout: insertTab requires a docked pane')
        要求标签空闲(状态,操作['tab']['id'])
        焦点=焦点快照(状态,[窗格['id']])
        标签序=插入于(窗格['tabs'],操作['index'],操作['tab']['id'])
        if 窗格['activeTabId'] is None:
            活动=操作['tab']['id']
        else:
            活动=窗格['activeTabId']
        return {
            'state':换节点(换标签(状态,{操作['tab']['id']:操作['tab']}),{
                窗格['id']:窗格换标签(窗格,标签序,活动),
            }),
            'inverse':[{'type':'closeTab','tabId':操作['tab']['id']},焦点],
        }
    if 种类=='closeTab':
        标签=取标签(状态,操作['tabId'])
        窗格=查找标签窗格(状态,操作['tabId'])
        序号=窗格['tabs'].index(操作['tabId'])
        焦点=焦点快照(状态,[窗格['id']])
        if 窗格['host']=='float':
            浮序=浮动序号(状态,窗格['id'])
            去掉=换标签(
                换节点(盖上(状态,{'floats':移除于(状态['floats'],浮序)}),{窗格['id']:None}),
                {操作['tabId']:None},
            )
            return {
                'state':重坐焦点(去掉,窗格['id']),
                'inverse':[
                    {'type':'insertPane','pane':窗格,'tabs':[标签],'attach':{'mode':'float','index':浮序}},
                    焦点,
                ],
            }
        if 窗格['activeTabId']==操作['tabId']:
            活动=邻标签标识(窗格['tabs'],序号)
        else:
            活动=窗格['activeTabId']
        return {
            'state':换标签(
                换节点(状态,{窗格['id']:窗格换标签(窗格,移除于(窗格['tabs'],序号),活动)}),
                {操作['tabId']:None},
            ),
            'inverse':[{'type':'insertTab','paneId':窗格['id'],'tab':标签,'index':序号},焦点],
        }
    if 种类=='insertPane':
        要求节点空闲(状态,操作['pane']['id'])
        if len(操作['pane']['tabs'])!=len(操作['tabs']):
            raise 停靠错误('layout: insertPane tab records do not match the pane')
        if 操作['pane']['host']=='dock' and len(操作['tabs'])>0:
            raise 停靠错误('layout: insertPane returns a docked pane empty')
        标签更新={}
        for 标签 in 操作['tabs']:
            要求标签空闲(状态,标签['id'])
            标签更新[标签['id']]=标签
        if len(操作['tabs'])==0:
            逆序=[{'type':'merge','paneId':操作['pane']['id']}]
        else:
            逆序=[{'type':'closeTab','tabId':操作['tabs'][0]['id']},焦点快照(状态,[])]
        附着=操作['attach']
        if 附着['mode']=='child':
            父=取分割(状态,附着['parentId'])
            子序=插入于(父['children'],附着['index'],操作['pane']['id'])
            if len(附着['sizes'])!=len(子序):
                raise 停靠错误('layout: insertPane sizes do not match the split')
            逆序.append({'type':'resize','splitId':父['id'],'sizes':父['sizes']})
            return {
                'state':换节点(换标签(状态,标签更新),{
                    操作['pane']['id']:操作['pane'],
                    父['id']:盖上(父,{'children':子序,'sizes':附着['sizes']}),
                }),
                'inverse':逆序,
            }
        if 附着['mode']=='wrap':
            if 操作['pane']['id'] not in 附着['split']['children']:
                raise 停靠错误('layout: insertPane wrap split does not list the pane')
            搬好=父中替换(状态,附着['targetId'],附着['split']['id'])
            return {
                'state':换节点(换标签(搬好,标签更新),{
                    操作['pane']['id']:操作['pane'],
                    附着['split']['id']:附着['split'],
                }),
                'inverse':逆序,
            }
        if 附着['mode']=='float':
            if 操作['pane']['host']!='float':
                raise 停靠错误('layout: float attachment requires a floating pane')
            浮层=插入于(状态['floats'],附着['index'],操作['pane']['id'])
            return {
                'state':换节点(换标签(盖上(状态,{'floats':浮层}),标签更新),{操作['pane']['id']:操作['pane']}),
                'inverse':逆序,
            }
        未处理(附着,'layout: insertPane attachment')
    if 种类=='moveTab':
        来源=查找标签窗格(状态,操作['tabId'])
        if 来源['host']!='dock':
            raise 停靠错误('layout: moveTab source must be docked; use unfloat')
        去处=取窗格(状态,操作['toPaneId'])
        if 去处['host']!='dock':
            raise 停靠错误('layout: moveTab target must be docked')
        if 去处['id']==来源['id']:
            raise 停靠错误('layout: moveTab across one pane; use reorderTab')
        序号=来源['tabs'].index(操作['tabId'])
        焦点=焦点快照(状态,[来源['id'],去处['id']])
        if 来源['activeTabId']==操作['tabId']:
            活动=邻标签标识(来源['tabs'],序号)
        else:
            活动=来源['activeTabId']
        搬走=换节点(状态,{
            来源['id']:窗格换标签(来源,移除于(来源['tabs'],序号),活动),
            去处['id']:窗格换标签(去处,插入于(去处['tabs'],操作['index'],操作['tabId']),操作['tabId']),
        })
        return {
            'state':盖上(搬走,{'activePaneId':去处['id']}),
            'inverse':[{'type':'moveTab','tabId':操作['tabId'],'toPaneId':来源['id'],'index':序号},焦点],
        }
    if 种类=='reorderTab':
        窗格=查找标签窗格(状态,操作['tabId'])
        从哪=窗格['tabs'].index(操作['tabId'])
        标签序=插入于(移除于(窗格['tabs'],从哪),操作['index'],操作['tabId'])
        return {
            'state':换节点(状态,{窗格['id']:盖上(窗格,{'tabs':标签序})}),
            'inverse':[{'type':'reorderTab','tabId':操作['tabId'],'index':从哪}],
        }
    if 种类=='focusTab':
        窗格=查找标签窗格(状态,操作['tabId'])
        焦点=焦点快照(状态,[窗格['id']])
        聚焦=换节点(状态,{窗格['id']:盖上(窗格,{'activeTabId':操作['tabId']})})
        if 窗格['host']=='float':
            浮层=抬到顶(聚焦['floats'],窗格['id'])
        else:
            浮层=聚焦['floats']
        return {
            'state':盖上(聚焦,{'activePaneId':窗格['id'],'floats':浮层}),
            'inverse':[焦点],
        }
    if 种类=='focusPane':
        窗格=取窗格(状态,操作['paneId'])
        焦点=焦点快照(状态,[])
        if 窗格['host']=='float':
            浮层=抬到顶(状态['floats'],窗格['id'])
        else:
            浮层=状态['floats']
        return {
            'state':盖上(状态,{'activePaneId':窗格['id'],'floats':浮层}),
            'inverse':[焦点],
        }
    if 种类=='resize':
        分割=取分割(状态,操作['splitId'])
        if len(操作['sizes'])!=len(分割['children']):
            raise 停靠错误('layout: resize sizes do not match the split')
        for 大小 in 操作['sizes']:
            if not (大小>0):
                raise 停靠错误('layout: resize sizes must all be above zero')
        return {
            'state':换节点(状态,{分割['id']:盖上(分割,{'sizes':归一份额(操作['sizes'])})}),
            'inverse':[{'type':'resize','splitId':分割['id'],'sizes':分割['sizes']}],
        }
    if 种类=='float':
        取标签(状态,操作['tabId'])
        来源=查找标签窗格(状态,操作['tabId'])
        if 来源['host']!='dock':
            raise 停靠错误('layout: float requires a docked tab')
        要求节点空闲(状态,操作['newPaneId'])
        序号=来源['tabs'].index(操作['tabId'])
        焦点=焦点快照(状态,[来源['id']])
        if 来源['activeTabId']==操作['tabId']:
            活动=邻标签标识(来源['tabs'],序号)
        else:
            活动=来源['activeTabId']
        浮出=换节点(状态,{
            来源['id']:窗格换标签(来源,移除于(来源['tabs'],序号),活动),
            操作['newPaneId']:{
                'kind':'pane',
                'id':操作['newPaneId'],
                'host':'float',
                'tabs':[操作['tabId']],
                'activeTabId':操作['tabId'],
                'rect':操作['rect'],
            },
        })
        return {
            'state':盖上(浮出,{
                'floats':[*浮出['floats'],操作['newPaneId']],
                'activePaneId':操作['newPaneId'],
            }),
            'inverse':[{'type':'unfloat','paneId':操作['newPaneId'],'toPaneId':来源['id'],'index':序号},焦点],
        }
    if 种类=='unfloat':
        窗格=取窗格(状态,操作['paneId'])
        矩形=浮动矩形(窗格)
        标签标识=唯一标签标识(窗格)
        去处=取窗格(状态,操作['toPaneId'])
        if 去处['host']!='dock':
            raise 停靠错误('layout: unfloat target must be docked')
        焦点=焦点快照(状态,[去处['id']])
        收回=换节点(盖上(状态,{'floats':移除于(状态['floats'],浮动序号(状态,操作['paneId']))}),{
            操作['paneId']:None,
            去处['id']:窗格换标签(去处,插入于(去处['tabs'],操作['index'],标签标识),标签标识),
        })
        return {
            'state':盖上(收回,{'activePaneId':去处['id']}),
            'inverse':[{'type':'float','tabId':标签标识,'newPaneId':操作['paneId'],'rect':矩形},焦点],
        }
    if 种类=='moveFloat':
        窗格=取窗格(状态,操作['paneId'])
        矩形=浮动矩形(窗格)
        下一=dict(矩形)
        下一['x']=操作['x']
        下一['y']=操作['y']
        return {
            'state':改形浮动(状态,窗格,下一),
            'inverse':[
                {'type':'moveFloat','paneId':操作['paneId'],'x':矩形['x'],'y':矩形['y']},
                焦点快照(状态,[]),
            ],
        }
    if 种类=='resizeFloat':
        窗格=取窗格(状态,操作['paneId'])
        矩形=浮动矩形(窗格)
        if not (操作['rect']['width']>0) or not (操作['rect']['height']>0):
            raise 停靠错误('layout: float size must be above zero')
        return {
            'state':改形浮动(状态,窗格,操作['rect']),
            'inverse':[
                {'type':'resizeFloat','paneId':操作['paneId'],'rect':矩形},
                焦点快照(状态,[]),
            ],
        }
    if 种类=='setExpanded':
        return {
            'state':盖上(状态,{'expanded':操作['expanded']}),
            'inverse':[{'type':'setExpanded','expanded':状态['expanded']}],
        }
    if 种类=='setMode':
        return {
            'state':盖上(状态,{'mode':操作['mode']}),
            'inverse':[{'type':'setMode','mode':状态['mode']}],
        }
    if 种类=='restoreFocus':
        逆=焦点快照(状态,[标识 for 标识,活动 in 条目表(操作['paneActiveTabs'])])
        for 窗格标识 in 操作['floats']:
            窗格=取窗格(状态,窗格标识)
            if 窗格['host']!='float':
                raise 停靠错误(f'layout: restoreFocus lists docked pane {窗格标识} as floating')
        下一=状态
        for 窗格标识,活动标签 in 条目表(操作['paneActiveTabs']):
            窗格=取窗格(下一,窗格标识)
            下一=换节点(下一,{窗格标识:盖上(窗格,{'activeTabId':活动标签})})
        取窗格(下一,操作['activePaneId'])
        return {
            'state':盖上(下一,{
                'activePaneId':操作['activePaneId'],
                'floats':操作['floats'],
            }),
            'inverse':[逆],
        }
    return 未处理(操作,'layout: operation')

def 回放(状态,操作表):
    '按记录顺序往前叠操作，丢掉逆操作'
    当前=状态
    for 操作 in 操作表:
        当前=施加操作(当前,操作)['state']
    return 当前
