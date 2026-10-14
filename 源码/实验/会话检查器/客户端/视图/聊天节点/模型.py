'表格顺序跟随根引用和分组成员，与行数据无关'

import math
from ......基础设施.js特性 import PromiseEX as 期约#分组成员变化排到当前调用之后
from ......客户端.存储 import 创建快照存储
from ..表格模型 import 检查器记录源
from ..格式 import 检查器预览
from .对象 import 聊天对象索引,取
from .选取匹配 import 匹配聊天节点行

__all__=['聊天节点模型']

空行=()
列字段=('key','kind')

def 节点记录(节点):
    '一行节点的类型、身份、位置和横向摘要'
    位置=取(节点,'location') or {}
    种类=取(位置,'kind')
    if 种类=='step':
        坐标=f"{取(取(位置,'turn'),'turn')}/{取(取(位置,'step'),'step')}"
    elif 种类=='turn':
        坐标=str(取(取(位置,'turn'),'turn'))
    else:
        坐标=种类 if 种类 is not None else ''
    return {'type':取(节点,'kind'),'identity':取(节点,'key'),'location':坐标,'value':节点,'summary':检查器预览(节点,列字段)}

class 聊天节点模型:
    '观察 Chat 结构变化；可见行再观察自己的 Node 或 Group'
    def __init__(自身,绑定):
        '绑定是被检查会话上、与目标无关的 Conversation 绑定'
        自身._绑定=绑定
        自身._行=创建行存储()
        自身._来源={}
        自身._组={}
        自身._条目=None
        自身._序=None
        自身._键=None
        自身._锚=None
        自身._节点存储=None
        自身._已分组=None
        自身._订阅数=0
        自身._断开=None
        自身._已排队=False
        自身._目标={}
        自身._对象索引=聊天对象索引(绑定)
        自身._刷新()

    def 对象(自身,会话标识):
        '把对象引用和发布更新绑到被检查的会话'
        def 引用(值):
            '索引里的具名引用，能对上表格行时带上 rowKey'
            找到=自身._对象索引.引用(值)
            if 找到 is None:
                return None
            行=None
            for 键,目标 in 自身._目标.items():
                if 找到['target'].get('nodeKey') is not None:
                    if 目标.get('nodeKey')==找到['target']['nodeKey'] and (找到['target'].get('groupPart') is None or 目标.get('groupPart')==找到['target']['groupPart']):
                        行=(键,目标)
                        break
                elif 找到['target'].get('groupKey') is not None and 目标.get('groupKey')==找到['target']['groupKey']:
                    行=(键,目标)
                    break
            结果=dict(找到)
            if 行 is not None:
                结果['rowKey']=行[0]
            return 结果
        def 行(键):
            '表格行自己的引用，目标改成这一行的坐标'
            来源=自身.行(键)
            值=None if 来源 is None else (来源.getSnapshot() or {}).get('value')
            if 值 is None or isinstance(值,(str,int,float,bool)):
                return None
            找到=引用(值)
            目标=自身._目标.get(键)
            if 找到 is None or 目标 is None:
                return None
            return {**找到,'rowKey':键,'target':目标}
        return {'sessionId':会话标识,'updates':自身._绑定.snapshot,'reference':引用,'row':行}

    def getSnapshot(自身):
        '稳定的、展平后的 group/node 顺序'
        return 自身._行.getSnapshot()

    def 选取(自身,目标):
        '用当前表格匹配选中的 Chat 对象，包括折叠的子行'
        自身._刷新(True)
        return 匹配聊天节点行(目标,自身._目标)

    def subscribe(自身,监听):
        '结构失效回调，返回退订函数'
        停止=自身._行.subscribe(监听)
        if 自身._订阅数==0:
            自身._断开=自身._绑定.snapshot.subscribe(lambda:自身._刷新())
            自身._绑定.activate('chat')
            自身._刷新(True)
        自身._订阅数+=1
        def 退订():
            '最后一个订阅者离开时断开分组订阅'
            停止()
            自身._订阅数-=1
            if 自身._订阅数==0:
                if 自身._断开 is not None:
                    自身._断开()
                    自身._断开=None
                for 停 in 自身._组.values():
                    停()
                自身._组.clear()
        return 退订

    def 行(自身,键):
        '已加载行的元数据来源；不增加订阅'
        return 自身._来源.get(键)

    def _刷新(自身,强制=False):
        '结构或锚点变了才重建行；分组切换时清掉来源'
        快照=自身._绑定.snapshot.getSnapshot()
        视图=取(快照,'views')
        聊天=None if 视图 is None else 视图.get('chat')
        分组=None if 视图 is None else 视图.grouped('chat')
        节点存储=取(聊天,'nodes')
        节点=None if 节点存储 is None else 节点存储.values()
        if 节点 is None:
            相同键=自身._键 is None
        else:
            键表=自身._键
            锚表=自身._锚
            相同键=(键表 is not None and 锚表 is not None and len(节点)==len(键表)
                and all(取(节点[下标],'key')==键表[下标] and 取(节点[下标],'anchorSeq')==锚表[下标] for 下标 in range(len(节点))))
        序=取(聊天,'order')
        条目身份=取(分组,'entries')
        if (not 强制 and 序 is 自身._序 and 节点存储 is 自身._节点存储 and 相同键 and 分组 is 自身._已分组 and 条目身份 is 自身._条目):
            return
        自身._序=序
        自身._条目=条目身份
        自身._键=None if 节点 is None else [取(项,'key') for 项 in 节点]
        自身._锚=None if 节点 is None else [取(项,'anchorSeq') for 项 in 节点]
        if 分组 is not 自身._已分组:
            for 停 in 自身._组.values():
                停()
            自身._组.clear()
            自身._来源.clear()
        自身._已分组=分组
        if 节点存储 is not 自身._节点存储:
            自身._来源.clear()
        自身._节点存储=节点存储
        活动组=set()
        自身._目标.clear()
        行表=[]
        def 加节点(条目,父=None):
            '放入一个节点行，并在需要时挂上记录源'
            组分=取(条目,'groupPart')
            键=f"node:{取(条目,'key')}:{组分 or ''}"
            位置=None
            if 聊天 is not None and 节点存储 is not None:
                位置=取(节点存储.get(取(条目,'key')),'location')
            位置种类=取(位置,'kind')
            回合=取(取(位置,'turn'),'turn') if 位置种类 in ('turn','step') else None
            步=取(取(位置,'step'),'step') if 位置种类=='step' else None
            目标={'nodeKey':取(条目,'key')}
            if 组分 is not None:
                目标['groupPart']=组分
            if 回合 is not None:
                目标['turn']=回合
            if 步 is not None:
                目标['step']=步
            自身._目标[键]=目标
            行={'key':键,'depth':0 if 父 is None else 1}
            if 父 is not None:
                行['parent']=父
            行表.append(行)
            if 键 not in 自身._来源 and 聊天 is not None:
                节点键=取(条目,'key')
                def 投影(节点,组分=组分):
                    '分组部位写进身份'
                    记录=节点记录(节点)
                    if 组分 is None:
                        return 记录
                    return {**记录,'identity':f"{取(节点,'key')}#{组分}"}
                自身._来源[键]=检查器记录源(节点存储.source(节点键),投影)
        if 条目身份 is not None:
            条目表=条目身份
        elif 序 is not None:
            条目表=[{'kind':'node','key':键} for 键 in 序]
        else:
            条目表=[]
        已含=set()
        条目锚=[]
        for 条目 in 条目表:
            if 取(条目,'kind')=='node':
                成员=[条目]
            else:
                成员=取(分组.groupSource(取(条目,'key')).getSnapshot(),'members') or []
            锚=None
            for 成员项 in 成员:
                已含.add(取(成员项,'key'))
                序号=None
                if 节点存储 is not None:
                    序号=取(节点存储.get(取(成员项,'key')),'anchorSeq')
                if 序号 is not None:
                    锚=序号 if 锚 is None else min(锚,序号)
            条目锚.append(锚)
        未列出=sorted([项 for 项 in (节点 or []) if 取(项,'key') not in 已含],key=lambda 项:(取(项,'anchorSeq'),取(项,'key') or ''))
        未列出下标={'值':0}
        def 在锚前加未列出(锚):
            '把锚点不晚于该根的未列出节点插进来'
            while 未列出下标['值']<len(未列出) and 取(未列出[未列出下标['值']],'anchorSeq')<=锚:
                加节点({'key':取(未列出[未列出下标['值']],'key')})
                未列出下标['值']+=1
        for 下标,条目 in enumerate(条目表):
            锚=条目锚[下标]
            if 锚 is not None:
                在锚前加未列出(锚)
            if 取(条目,'kind')=='node':
                加节点(条目)
                continue
            活动组.add(取(条目,'key'))
            键=f"group:{取(条目,'key')}"
            自身._目标[键]={'groupKey':取(条目,'key')}
            源=分组.groupSource(取(条目,'key'))
            组=源.getSnapshot()
            行表.append({'key':键,'depth':0})
            if 键 not in 自身._来源:
                def 投影组(值):
                    '分组行的摘要'
                    return {'type':'group','identity':取(值,'key'),'location':'','value':值,'summary':检查器预览(值,列字段)}
                自身._来源[键]=检查器记录源(源,投影组)
            for 成员项 in 取(组,'members') or []:
                加节点(成员项,键)
            if 自身._订阅数>0 and 取(条目,'key') not in 自身._组:
                成员持有={'值':取(组,'members')}
                组键=取(条目,'key')
                def 接到(成员持有=成员持有,源=源):
                    '成员身份变了才排程重建'
                    下一=取(源.getSnapshot(),'members')
                    if 下一 is 成员持有['值']:
                        return
                    成员持有['值']=下一
                    自身._排程()
                自身._组[组键]=源.subscribe(接到)
        在锚前加未列出(math.inf)
        for 键,停 in list(自身._组.items()):
            if 键 not in 活动组:
                停()
                del 自身._组[键]
        行键={行['key'] for 行 in 行表}
        for 键 in list(自身._来源.keys()):
            if 键 not in 行键:
                del 自身._来源[键]
        自身._行.set(行表)

    def _排程(自身):
        '把同一次发布里的成员变化合并到当前调用之后'
        if 自身._已排队:
            return
        自身._已排队=True
        def 跑(结果=None):
            '订阅还在才强制刷新'
            自身._已排队=False
            if 自身._订阅数>0:
                自身._刷新(True)
        起点=期约()
        起点.然后(跑)
        起点.解决(None)

def 创建行存储():
    '空顺序使用稳定常量'
    return 创建快照存储(空行)
