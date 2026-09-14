from ..约定.类型 import 停靠错误,窗格宿主停靠,窗格宿主浮动,节点种分割#约定
from .树 import (#树读写
    断言穷尽,
    条目对,
    找父分割,
    查找标签窗格,
    首停靠窗格标识,
    浮动序号,
    浮动矩形,
    取窗格,
    取分割,
    取标签,
    插入于,
    键列表,
    邻标签标识,
    归一尺寸,
    唯一标签标识,
    窗格换标签条,
    移除于,
    父槽替换,
    换节点,
    换标签,
)#树结束

__all__=['施加操作','回放']#仅中文公开名


def _焦点快照(状态,窗格标识表):
    """捕获所列窗格活动标签与全局焦点，作为 restoreFocus 操作。"""
    窗格活动={}#窗格→活动标签
    for 标识 in 窗格标识表:#逐个
        窗格活动[标识]=取窗格(状态,标识)['activeTabId']#记下
    return {#恢复焦点操作
        'type':'restoreFocus',
        'activePaneId':状态['activePaneId'],
        'floats':list(状态['floats']),
        'paneActiveTabs':窗格活动,
    }#操作结束


def _抬升(浮动表,窗格标识):
    """把窗格标识移到浮动 z 序顶。"""
    return [项 for 项 in 浮动表 if 项!=窗格标识]+[窗格标识]#去重后置顶


def _重安置焦点(状态,已移除窗格标识):
    """焦点窗格已删时落到首停靠窗格。"""
    if 状态['activePaneId']!=已移除窗格标识:#仍活
        return 状态#不变
    下一=dict(状态)#浅拷
    下一['activePaneId']=首停靠窗格标识(状态)#回落
    return 下一#状态


def _空停靠窗格(标识):
    """新建空停靠窗格节点。"""
    return {#空窗格
        'kind':'pane',
        'id':标识,
        'host':窗格宿主停靠,
        'tabs':[],
        'activeTabId':None,
        'rect':None,
    }#节点结束


def _断言节点空闲(状态,标识):
    """创建类操作要求标识尚未占用。"""
    if 标识 in 状态['nodes']:#已有
        raise 停靠错误('layout: node '+str(标识)+' already exists')#拒绝


def _断言标签空闲(状态,标识):
    """打开类操作要求标签标识尚未占用。"""
    if 标识 in 状态['tabs']:#已有
        raise 停靠错误('layout: tab '+str(标识)+' already exists')#拒绝


def _应用分割(状态,操作):
    """沿轴给窗格一个空兄弟。"""
    窗格=取窗格(状态,操作['paneId'])#参考
    if 窗格['host']!=窗格宿主停靠:#须停靠
        raise 停靠错误('layout: split requires a docked pane')#拒绝
    _断言节点空闲(状态,操作['newPaneId'])#新窗格空闲
    新窗格=_空停靠窗格(操作['newPaneId'])#空
    父=找父分割(状态,操作['paneId'])#父

    if 父 is not None and 父['axis']==操作['axis']:#同轴并入
        下标=父['children'].index(操作['paneId'])#参考位
        处=下标+1 if 操作['direction']=='after' else 下标#插入位
        子表=插入于(父['children'],处,操作['newPaneId'])#子
        尺寸=[]#新份额
        for 甲,份额 in enumerate(父['sizes']):#对半
            if 甲==下标:#参考份额对半
                尺寸.extend([份额/2,份额/2])#两半
            else:#其余
                尺寸.append(份额)#原样
        新父=dict(父)#浅拷
        新父['children']=子表#子
        新父['sizes']=尺寸#份额
        return {#结果
            'state':换节点(状态,{操作['newPaneId']:新窗格,父['id']:新父}),
            'inverse':[
                {'type':'merge','paneId':操作['newPaneId']},
                {'type':'resize','splitId':父['id'],'sizes':list(父['sizes'])},
            ],
        }#结果结束

    _断言节点空闲(状态,操作['newSplitId'])#新分割空闲
    迁根=父槽替换(状态,操作['paneId'],操作['newSplitId'])#先换槽
    if 操作['direction']=='after':#后
        子表=[操作['paneId'],操作['newPaneId']]#序
    else:#前
        子表=[操作['newPaneId'],操作['paneId']]#序
    新分割={#分割节点
        'kind':节点种分割,
        'id':操作['newSplitId'],
        'axis':操作['axis'],
        'children':子表,
        'sizes':[0.5,0.5],
    }#节点结束
    return {#结果
        'state':换节点(迁根,{操作['newPaneId']:新窗格,操作['newSplitId']:新分割}),
        'inverse':[{'type':'merge','paneId':操作['newPaneId']}],
    }#结果结束


def _应用合并(状态,操作):
    """丢掉空窗格；两子分割塌成幸存子。"""
    窗格=取窗格(状态,操作['paneId'])#目标
    if len(窗格['tabs'])>0:#非空
        raise 停靠错误('layout: merge requires an empty pane')#拒绝
    焦点=_焦点快照(状态,[])#全局焦点

    if 窗格['host']==窗格宿主浮动:#浮动空窗格
        序号=浮动序号(状态,操作['paneId'])#z
        浮动=移除于(状态['floats'],序号)#去
        中=dict(状态)#浅拷
        中['floats']=浮动#写
        丢掉=换节点(中,{操作['paneId']:None})#删节点
        return {#结果
            'state':_重安置焦点(丢掉,操作['paneId']),
            'inverse':[
                {'type':'insertPane','pane':窗格,'tabs':[],'attach':{'mode':'float','index':序号}},
                焦点,
            ],
        }#结果结束

    父=找父分割(状态,操作['paneId'])#父
    if 父 is None:#根不可并
        raise 停靠错误('layout: the docked root pane cannot be merged')#拒绝
    下标=父['children'].index(操作['paneId'])#位

    if len(父['children'])>2:#多子只摘一
        子表=移除于(父['children'],下标)#子
        尺寸=归一尺寸(移除于(父['sizes'],下标))#份额
        新父=dict(父)#浅拷
        新父['children']=子表#子
        新父['sizes']=尺寸#份额
        丢掉=换节点(状态,{操作['paneId']:None,父['id']:新父})#写
        return {#结果
            'state':_重安置焦点(丢掉,操作['paneId']),
            'inverse':[
                {
                    'type':'insertPane',
                    'pane':窗格,
                    'tabs':[],
                    'attach':{
                        'mode':'child',
                        'parentId':父['id'],
                        'index':下标,
                        'sizes':list(父['sizes']),
                    },
                },
                焦点,
            ],
        }#结果结束

    兄标识=父['children'][1-下标]#幸存
    塌=换节点(父槽替换(状态,父['id'],兄标识),{操作['paneId']:None,父['id']:None})#塌分割
    return {#结果
        'state':_重安置焦点(塌,操作['paneId']),
        'inverse':[
            {'type':'insertPane','pane':窗格,'tabs':[],'attach':{'mode':'wrap','targetId':兄标识,'split':父}},
            焦点,
        ],
    }#结果结束


def _应用打开标签(状态,操作):
    """向停靠窗格加标签并聚焦。"""
    窗格=取窗格(状态,操作['paneId'])#目标
    if 窗格['host']!=窗格宿主停靠:#须停靠
        raise 停靠错误('layout: openTab requires a docked pane')#拒绝
    _断言标签空闲(状态,操作['tab']['id'])#空闲
    焦点=_焦点快照(状态,[窗格['id']])#快照
    就座=换节点(
        换标签(状态,{操作['tab']['id']:操作['tab']}),
        {窗格['id']:窗格换标签条(窗格,插入于(窗格['tabs'],操作['index'],操作['tab']['id']),操作['tab']['id'])},
    )#就座
    下一=dict(就座)#浅拷
    下一['activePaneId']=窗格['id']#焦点窗格
    return {'state':下一,'inverse':[{'type':'closeTab','tabId':操作['tab']['id']},焦点]}#结果


def _应用插入标签(状态,操作):
    """把标签记录放回，不抢焦点。"""
    窗格=取窗格(状态,操作['paneId'])#目标
    if 窗格['host']!=窗格宿主停靠:#须停靠
        raise 停靠错误('layout: insertTab requires a docked pane')#拒绝
    _断言标签空闲(状态,操作['tab']['id'])#空闲
    焦点=_焦点快照(状态,[窗格['id']])#快照
    标签条=插入于(窗格['tabs'],操作['index'],操作['tab']['id'])#条
    活动=窗格['activeTabId'] if 窗格['activeTabId'] is not None else 操作['tab']['id']#活动
    return {#结果
        'state':换节点(
            换标签(状态,{操作['tab']['id']:操作['tab']}),
            {窗格['id']:窗格换标签条(窗格,标签条,活动)},
        ),
        'inverse':[{'type':'closeTab','tabId':操作['tab']['id']},焦点],
    }#结果结束


def _应用关闭标签(状态,操作):
    """销毁标签；浮动宿主随唯一标签而去。"""
    标签=取标签(状态,操作['tabId'])#记录
    窗格=查找标签窗格(状态,操作['tabId'])#宿主
    下标=窗格['tabs'].index(操作['tabId'])#位
    焦点=_焦点快照(状态,[窗格['id']])#快照

    if 窗格['host']==窗格宿主浮动:#浮动整面板
        序号=浮动序号(状态,窗格['id'])#z
        浮动=移除于(状态['floats'],序号)#去
        中=dict(状态)#浅拷
        中['floats']=浮动#写
        丢掉=换标签(换节点(中,{窗格['id']:None}),{操作['tabId']:None})#删
        return {#结果
            'state':_重安置焦点(丢掉,窗格['id']),
            'inverse':[
                {'type':'insertPane','pane':窗格,'tabs':[标签],'attach':{'mode':'float','index':序号}},
                焦点,
            ],
        }#结果结束

    if 窗格['activeTabId']==操作['tabId']:#关的是活动
        活动=邻标签标识(窗格['tabs'],下标)#邻
    else:#否
        活动=窗格['activeTabId']#保留
    return {#结果
        'state':换标签(
            换节点(状态,{窗格['id']:窗格换标签条(窗格,移除于(窗格['tabs'],下标),活动)}),
            {操作['tabId']:None},
        ),
        'inverse':[{'type':'insertTab','paneId':窗格['id'],'tab':标签,'index':下标},焦点],
    }#结果结束


def _应用插入窗格(状态,操作):
    """把窗格连同其标签记录放回。"""
    _断言节点空闲(状态,操作['pane']['id'])#空闲
    if len(操作['pane']['tabs'])!=len(操作['tabs']):#不匹配
        raise 停靠错误('layout: insertPane tab records do not match the pane')#拒绝
    if 操作['pane']['host']==窗格宿主停靠 and len(操作['tabs'])>0:#停靠须空回
        raise 停靠错误('layout: insertPane returns a docked pane empty')#拒绝
    标签更新={}#记录
    for 标签 in 操作['tabs']:#逐条
        _断言标签空闲(状态,标签['id'])#空闲
        标签更新[标签['id']]=标签#记
    if len(操作['tabs'])==0:#空回
        逆表=[{'type':'merge','paneId':操作['pane']['id']}]#并回
    else:#带标签
        逆表=[
            {'type':'closeTab','tabId':操作['tabs'][0]['id']},
            _焦点快照(状态,[]),
        ]#关回

    附着=操作['attach']#附着
    模式=附着['mode']#模式
    if 模式=='child':#子槽
        父=取分割(状态,附着['parentId'])#父
        子表=插入于(父['children'],附着['index'],操作['pane']['id'])#子
        if len(附着['sizes'])!=len(子表):#份额数
            raise 停靠错误('layout: insertPane sizes do not match the split')#拒绝
        逆表.append({'type':'resize','splitId':父['id'],'sizes':list(父['sizes'])})#份额逆
        新父=dict(父)#浅拷
        新父['children']=子表#子
        新父['sizes']=list(附着['sizes'])#份额
        return {#结果
            'state':换节点(换标签(状态,标签更新),{操作['pane']['id']:操作['pane'],父['id']:新父}),
            'inverse':逆表,
        }#结果结束
    if 模式=='wrap':#再包分割
        if 操作['pane']['id'] not in 附着['split']['children']:#须列本窗格
            raise 停靠错误('layout: insertPane wrap split does not list the pane')#拒绝
        迁根=父槽替换(状态,附着['targetId'],附着['split']['id'])#换槽
        return {#结果
            'state':换节点(
                换标签(迁根,标签更新),
                {操作['pane']['id']:操作['pane'],附着['split']['id']:附着['split']},
            ),
            'inverse':逆表,
        }#结果结束
    if 模式=='float':#浮动附着
        if 操作['pane']['host']!=窗格宿主浮动:#须浮动
            raise 停靠错误('layout: float attachment requires a floating pane')#拒绝
        浮动=插入于(状态['floats'],附着['index'],操作['pane']['id'])#z
        中=dict(状态)#浅拷
        中['floats']=浮动#写
        return {#结果
            'state':换节点(换标签(中,标签更新),{操作['pane']['id']:操作['pane']}),
            'inverse':逆表,
        }#结果结束
    return 断言穷尽(附着,'layout: insertPane attachment')#穷尽


def _应用移动标签(状态,操作):
    """跨停靠窗格移动并聚焦目标。"""
    源=查找标签窗格(状态,操作['tabId'])#源
    if 源['host']!=窗格宿主停靠:#须停靠
        raise 停靠错误('layout: moveTab source must be docked; use unfloat')#拒绝
    目标=取窗格(状态,操作['toPaneId'])#目标
    if 目标['host']!=窗格宿主停靠:#须停靠
        raise 停靠错误('layout: moveTab target must be docked')#拒绝
    if 目标['id']==源['id']:#同窗格
        raise 停靠错误('layout: moveTab across one pane; use reorderTab')#拒绝
    下标=源['tabs'].index(操作['tabId'])#源位
    焦点=_焦点快照(状态,[源['id'],目标['id']])#快照
    if 源['activeTabId']==操作['tabId']:#带走活动
        源活动=邻标签标识(源['tabs'],下标)#邻
    else:#否
        源活动=源['activeTabId']#保留
    已迁=换节点(状态,{
        源['id']:窗格换标签条(源,移除于(源['tabs'],下标),源活动),
        目标['id']:窗格换标签条(目标,插入于(目标['tabs'],操作['index'],操作['tabId']),操作['tabId']),
    })#迁
    下一=dict(已迁)#浅拷
    下一['activePaneId']=目标['id']#焦点
    return {#结果
        'state':下一,
        'inverse':[{'type':'moveTab','tabId':操作['tabId'],'toPaneId':源['id'],'index':下标},焦点],
    }#结果结束


def _应用重排标签(状态,操作):
    """同窗格内重排。"""
    窗格=查找标签窗格(状态,操作['tabId'])#宿主
    自=窗格['tabs'].index(操作['tabId'])#原位
    标签条=插入于(移除于(窗格['tabs'],自),操作['index'],操作['tabId'])#新序
    下一窗格=dict(窗格)#浅拷
    下一窗格['tabs']=标签条#条
    return {#结果
        'state':换节点(状态,{窗格['id']:下一窗格}),
        'inverse':[{'type':'reorderTab','tabId':操作['tabId'],'index':自}],
    }#结果结束


def _应用聚焦标签(状态,操作):
    """聚焦标签及其窗格，浮动则抬升。"""
    窗格=查找标签窗格(状态,操作['tabId'])#宿主
    焦点=_焦点快照(状态,[窗格['id']])#快照
    下一窗格=dict(窗格)#浅拷
    下一窗格['activeTabId']=操作['tabId']#活动
    已焦=换节点(状态,{窗格['id']:下一窗格})#写回
    浮动=_抬升(已焦['floats'],窗格['id']) if 窗格['host']==窗格宿主浮动 else 已焦['floats']#z
    下一=dict(已焦)#浅拷
    下一['activePaneId']=窗格['id']#焦点窗格
    下一['floats']=浮动#z
    return {'state':下一,'inverse':[焦点]}#结果


def _应用聚焦窗格(状态,操作):
    """聚焦窗格，浮动则抬升。"""
    窗格=取窗格(状态,操作['paneId'])#目标
    焦点=_焦点快照(状态,[])#快照
    浮动=_抬升(状态['floats'],窗格['id']) if 窗格['host']==窗格宿主浮动 else 状态['floats']#z
    下一=dict(状态)#浅拷
    下一['activePaneId']=窗格['id']#焦点
    下一['floats']=浮动#z
    return {'state':下一,'inverse':[焦点]}#结果


def _应用缩放(状态,操作):
    """记录分隔条拖动净结果。"""
    分割=取分割(状态,操作['splitId'])#目标
    if len(操作['sizes'])!=len(分割['children']):#份额数
        raise 停靠错误('layout: resize sizes do not match the split')#拒绝
    for 份额 in 操作['sizes']:#须正
        if not (份额>0):#非正
            raise 停靠错误('layout: resize sizes must all be above zero')#拒绝
    新分割=dict(分割)#浅拷
    新分割['sizes']=归一尺寸(操作['sizes'])#归一
    return {#结果
        'state':换节点(状态,{分割['id']:新分割}),
        'inverse':[{'type':'resize','splitId':分割['id'],'sizes':list(分割['sizes'])}],
    }#结果结束


def _应用浮动(状态,操作):
    """把停靠标签取出为新浮动窗格并置顶。"""
    取标签(状态,操作['tabId'])#须在
    源=查找标签窗格(状态,操作['tabId'])#源
    if 源['host']!=窗格宿主停靠:#须停靠
        raise 停靠错误('layout: float requires a docked tab')#拒绝
    _断言节点空闲(状态,操作['newPaneId'])#新窗格空闲
    下标=源['tabs'].index(操作['tabId'])#位
    焦点=_焦点快照(状态,[源['id']])#快照
    if 源['activeTabId']==操作['tabId']:#带走活动
        源活动=邻标签标识(源['tabs'],下标)#邻
    else:#否
        源活动=源['activeTabId']#保留
    浮窗={#浮动窗格
        'kind':'pane',
        'id':操作['newPaneId'],
        'host':窗格宿主浮动,
        'tabs':[操作['tabId']],
        'activeTabId':操作['tabId'],
        'rect':操作['rect'],
    }#节点结束
    已浮=换节点(状态,{
        源['id']:窗格换标签条(源,移除于(源['tabs'],下标),源活动),
        操作['newPaneId']:浮窗,
    })#写
    下一=dict(已浮)#浅拷
    下一['floats']=list(已浮['floats'])+[操作['newPaneId']]#置顶
    下一['activePaneId']=操作['newPaneId']#焦点
    return {#结果
        'state':下一,
        'inverse':[{'type':'unfloat','paneId':操作['newPaneId'],'toPaneId':源['id'],'index':下标},焦点],
    }#结果结束


def _应用收回(状态,操作):
    """把浮动窗格唯一标签收回停靠窗格并销毁浮窗。"""
    窗格=取窗格(状态,操作['paneId'])#浮窗
    矩形=浮动矩形(窗格)#旧矩形
    标签标识=唯一标签标识(窗格)#唯一签
    目标=取窗格(状态,操作['toPaneId'])#目标
    if 目标['host']!=窗格宿主停靠:#须停靠
        raise 停靠错误('layout: unfloat target must be docked')#拒绝
    焦点=_焦点快照(状态,[目标['id']])#快照
    中=dict(状态)#浅拷
    中['floats']=移除于(状态['floats'],浮动序号(状态,操作['paneId']))#去 z
    已收=换节点(中,{
        操作['paneId']:None,
        目标['id']:窗格换标签条(目标,插入于(目标['tabs'],操作['index'],标签标识),标签标识),
    })#写
    下一=dict(已收)#浅拷
    下一['activePaneId']=目标['id']#焦点
    return {#结果
        'state':下一,
        'inverse':[{'type':'float','tabId':标签标识,'newPaneId':操作['paneId'],'rect':矩形},焦点],
    }#结果结束


def _重塑浮动(状态,窗格,矩形):
    """改浮动矩形并聚焦抬升：拖移与缩放共用。"""
    下一窗格=dict(窗格)#浅拷
    下一窗格['rect']=矩形#矩形
    已塑=换节点(状态,{窗格['id']:下一窗格})#写
    下一=dict(已塑)#浅拷
    下一['activePaneId']=窗格['id']#焦点
    下一['floats']=_抬升(已塑['floats'],窗格['id'])#抬升
    return 下一#状态


def _应用移浮(状态,操作):
    """记录浮动拖动净位置，并聚焦抬升。"""
    窗格=取窗格(状态,操作['paneId'])#目标
    矩形=浮动矩形(窗格)#旧
    新矩=dict(矩形)#浅拷
    新矩['x']=操作['x']#x
    新矩['y']=操作['y']#y
    return {#结果
        'state':_重塑浮动(状态,窗格,新矩),
        'inverse':[{'type':'moveFloat','paneId':操作['paneId'],'x':矩形['x'],'y':矩形['y']},_焦点快照(状态,[])],
    }#结果结束


def _应用缩浮(状态,操作):
    """记录浮动缩放净矩形，并聚焦抬升。"""
    窗格=取窗格(状态,操作['paneId'])#目标
    矩形=浮动矩形(窗格)#旧
    新矩=操作['rect']#新
    if not (新矩['width']>0) or not (新矩['height']>0):#须正
        raise 停靠错误('layout: float size must be above zero')#拒绝
    return {#结果
        'state':_重塑浮动(状态,窗格,新矩),
        'inverse':[{'type':'resizeFloat','paneId':操作['paneId'],'rect':矩形},_焦点快照(状态,[])],
    }#结果结束


def _应用恢复焦点(状态,操作):
    """恢复先前操作挪动的焦点事实。"""
    逆=_焦点快照(状态,键列表(操作['paneActiveTabs']))#当前焦点作逆
    for 窗格标识 in 操作['floats']:#校验浮列
        窗格=取窗格(状态,窗格标识)#须在
        if 窗格['host']!=窗格宿主浮动:#须浮动
            raise 停靠错误('layout: restoreFocus lists docked pane '+str(窗格标识)+' as floating')#拒绝
    下一=状态#游标
    for 窗格标识,活动标签标识 in 条目对(操作['paneActiveTabs']):#写活动
        窗格=取窗格(下一,窗格标识)#窗格
        下一窗格=dict(窗格)#浅拷
        下一窗格['activeTabId']=活动标签标识#活动
        下一=换节点(下一,{窗格标识:下一窗格})#写
    取窗格(下一,操作['activePaneId'])#须在
    结果=dict(下一)#浅拷
    结果['activePaneId']=操作['activePaneId']#焦点窗格
    结果['floats']=list(操作['floats'])#z
    return {'state':结果,'inverse':[逆]}#结果


def 施加操作(状态,操作):
    """施加一操作，返回次态与逆操作序列（dict：state/inverse）。"""
    种=操作['type']#种类
    if 种=='split':#分窗
        return _应用分割(状态,操作)#分
    if 种=='merge':#合并
        return _应用合并(状态,操作)#并
    if 种=='openTab':#开签
        return _应用打开标签(状态,操作)#开
    if 种=='insertTab':#插签
        return _应用插入标签(状态,操作)#插
    if 种=='closeTab':#关签
        return _应用关闭标签(状态,操作)#关
    if 种=='insertPane':#插窗
        return _应用插入窗格(状态,操作)#插窗
    if 种=='moveTab':#移签
        return _应用移动标签(状态,操作)#移
    if 种=='reorderTab':#重排
        return _应用重排标签(状态,操作)#排
    if 种=='focusTab':#焦签
        return _应用聚焦标签(状态,操作)#焦
    if 种=='focusPane':#焦窗
        return _应用聚焦窗格(状态,操作)#焦
    if 种=='resize':#调分割
        return _应用缩放(状态,操作)#调
    if 种=='float':#浮出
        return _应用浮动(状态,操作)#浮
    if 种=='unfloat':#收回
        return _应用收回(状态,操作)#收
    if 种=='moveFloat':#移浮
        return _应用移浮(状态,操作)#移
    if 种=='resizeFloat':#缩浮
        return _应用缩浮(状态,操作)#缩
    if 种=='setExpanded':#展开
        下一=dict(状态)#浅拷
        下一['expanded']=操作['expanded']#写
        return {'state':下一,'inverse':[{'type':'setExpanded','expanded':状态['expanded']}]}#结果
    if 种=='setMode':#模式
        下一=dict(状态)#浅拷
        下一['mode']=操作['mode']#写
        return {'state':下一,'inverse':[{'type':'setMode','mode':状态['mode']}]}#结果
    if 种=='restoreFocus':#复焦
        return _应用恢复焦点(状态,操作)#复
    return 断言穷尽(操作,'layout: operation')#穷尽


def 回放(状态,操作表):
    """正向折叠操作，丢弃逆。"""
    当前=状态#游标
    for 操作 in 操作表:#逐项
        当前=施加操作(当前,操作)['state']#进
    return 当前#终态
