"""本包拥有的压缩日志流不变量。"""
import weakref#会话与事件弱表
from ...内核.会话 import 是否替换表面事件
from ...内核.会话.表面 import 表面视图
from .检查点 import 是否压缩检查点来源

包名='@deepseek-ai/dsh-compaction'
名称='compaction-invariant'
依赖=['invariants']
安全整数上限=9007199254740991#外来 JSON Number.MAX_SAFE_INTEGER

__all__=['包名','名称','依赖','安装','应用']

def 校验标识(值,标签,失败):
    """要求耐久不透明身份为非空字符串。"""
    if not isinstance(值,str) or len(值)==0:
        失败(标签+' must be a non-empty string')

def 校验序号(值,标签,失败):
    """在本包事件边界校验耐久事件序号身份。"""
    if isinstance(值,bool) or not isinstance(值,(int,float)):
        失败(标签+' must be a non-negative safe integer event seq')
        return 0#占位
    if isinstance(值,float):#外来 JSON 整值浮点
        if not 值.is_integer():
            失败(标签+' must be a non-negative safe integer event seq')
            return 0#占位
        值=int(值)
    if 值<0 or abs(值)>安全整数上限:
        失败(标签+' must be a non-negative safe integer event seq')
        return 0#占位
    return 值

def 校验遮蔽序号(跟踪,事件,失败):
    """校验一段被遮蔽表面跨度及其完整有序身份列表。"""
    事件类型=事件['type']
    数据=事件['data']
    区间=数据['shadowedRange'] if 'shadowedRange' in 数据 and 数据['shadowedRange'] is not None else {}
    起点=校验序号(区间['start'] if 'start' in 区间 else None,事件类型+' shadowedRange.start',失败)
    终点=校验序号(区间['end'] if 'end' in 区间 else None,事件类型+' shadowedRange.end',失败)
    原始列表=数据['shadowedSeqs'] if 'shadowedSeqs' in 数据 and 数据['shadowedSeqs'] is not None else []
    序号列表=[校验序号(序号,事件类型+' shadowedSeqs['+str(下标)+']',失败) for 下标,序号 in enumerate(原始列表)]
    if len(序号列表)==0:
        失败(事件类型+' shadowedSeqs must be non-empty')
    if len(序号列表)>0 and (序号列表[0]!=起点 or 序号列表[-1]!=终点):
        失败(事件类型+' shadowedRange must match the first and last shadowedSeqs')
    表面=跟踪['surface'].nodes
    try:
        起点下标=表面.index(起点)
    except ValueError:
        起点下标=-1
    try:
        终点下标=表面.index(终点)
    except ValueError:
        终点下标=-1
    if 起点下标<0 or 终点下标<起点下标:
        失败(事件类型+' shadowed seqs must name an earlier current surface span')
        return
    期望=表面[起点下标:终点下标+1]
    if len(期望)!=len(序号列表) or any(期望[下标]!=序号列表[下标] for 下标 in range(len(期望))):
        失败(事件类型+' shadowedSeqs must list every node in the current surface span')

def 校验来源命令标识(事件类型,值,期望,失败):
    """保持可选发起命令身份在同一事务内稳定。"""
    if 值 is not None:
        校验标识(值,事件类型+' sourceCommandId',失败)
    if 值!=期望:
        失败(事件类型+' sourceCommandId '+str(值)+' does not match compaction/start sourceCommandId '+str(期望))

def 校验检查点(跟踪,事件,失败):
    """相对未结束压缩事务校验一次替换检查点。"""
    出处=事件['data']['source']
    校验标识(出处['compactionId'],'compaction checkpoint compactionId',失败)
    检查点命令=出处['sourceCommandId'] if 'sourceCommandId' in 出处 else None
    if 检查点命令 is not None:
        校验标识(检查点命令,'compaction checkpoint sourceCommandId',失败)
    未结束=跟踪['compaction']
    if 未结束 is None:
        失败('compaction checkpoint has no matching compaction/start')
        return
    if 出处['compactionId']!=未结束['compactionId']:
        失败('compaction checkpoint id '+str(出处['compactionId'])+' does not match compaction/start id '+str(未结束['compactionId']))
    校验来源命令标识('compaction checkpoint',检查点命令,未结束['sourceCommandId'] if 'sourceCommandId' in 未结束 else None,失败)

def 继承孤儿开始序号列表(事件列表):
    """后续种子边界已使未配对压缩 start 过期。"""
    过期=set()
    未结束开始=None
    for 事件 in 事件列表:
        类型=事件['type']
        if 类型=='compaction/start':
            未结束开始=事件['seq']
        elif 类型=='compaction/end':
            未结束开始=None
        elif 类型=='session/end-seed':
            if 未结束开始 is not None:
                过期.add(未结束开始)
            未结束开始=None
    return 过期

def 校验回合边界(跟踪,事件,失败):
    """每个回合边界两侧不得跨过未结束的压缩括号。"""
    类型=事件['type']
    if (类型!='turn/start' and 类型!='turn/end') or 跟踪['compaction'] is None:
        return
    未结束=跟踪['compaction']
    所有者='standalone compaction' if 未结束['turn'] is None else 'compaction for turn '+str(未结束['turn'])
    失败(类型+' cannot cross an open '+所有者)

def 应用回合边界(跟踪,事件):
    """边界已被接受后推进已提交的回合光标。"""
    类型=事件['type']
    if 类型=='turn/start':
        跟踪['openTurn']=事件['data']['turn']
        return True
    if 类型=='turn/end':
        跟踪['openTurn']=None
        return True
    return False

def 校验所有者(所有者,未结束回合,事件类型,失败):
    """要求有编号括号落在其确切回合内，或独立括号落在回合之间。"""
    if 所有者 is None:
        if 未结束回合 is not None:
            失败(事件类型+' is standalone but turn '+str(未结束回合)+' is open')
        return
    if 未结束回合 is None:
        失败(事件类型+' for turn '+str(所有者)+' appended outside any open turn')
        return
    if 所有者!=未结束回合:
        失败(事件类型+' names turn '+str(所有者)+' but open turn is '+str(未结束回合))

def 校验压缩事件(跟踪,事件,失败):
    """校验一次压缩事件，不推进已提交跟踪状态。返回待提交迁移或 None。"""
    类型=事件['type']
    if 类型=='session/end-seed':
        return {'kind':'end-seed'}
    if 类型=='compaction/prune':
        校验遮蔽序号(跟踪,事件,失败)
        return None
    if 类型=='user/message' and 是否替换表面事件(事件) and 是否压缩检查点来源(事件['data']['source'] if 'source' in 事件['data'] else None):
        校验检查点(跟踪,事件,失败)
        return None
    if 类型!='compaction/start' and 类型!='compaction/summary' and 类型!='compaction/end':
        return None
    未结束=跟踪['compaction']
    数据=事件['data']
    if 类型=='compaction/start':
        校验标识(数据['compactionId'],'compaction/start compactionId',失败)
        if 'sourceCommandId' in 数据 and 数据['sourceCommandId'] is not None:
            校验标识(数据['sourceCommandId'],'compaction/start sourceCommandId',失败)
        if 未结束 is not None:
            所有者描述='standalone compaction' if 未结束['turn'] is None else 'turn '+str(未结束['turn'])
            失败('compaction/start while '+所有者描述+' is still compacting')
        校验所有者(数据['turn'] if 'turn' in 数据 else None,跟踪['openTurn'],类型,失败)
        return {
            'kind':'start',
            'compactionId':数据['compactionId'],
            'sourceCommandId':数据['sourceCommandId'] if 'sourceCommandId' in 数据 else None,
            'startSeq':事件['seq'],
            'turn':数据['turn'] if 'turn' in 数据 else None,
        }
    if 类型=='compaction/summary':
        校验标识(数据['compactionId'],'compaction/summary compactionId',失败)
        if 'sourceCommandId' in 数据 and 数据['sourceCommandId'] is not None:
            校验标识(数据['sourceCommandId'],'compaction/summary sourceCommandId',失败)
        if 未结束 is None:
            失败('compaction/summary has no matching compaction/start')
            return None
        if 数据['compactionId']!=未结束['compactionId']:
            失败('compaction/summary id '+str(数据['compactionId'])+' does not match compaction/start id '+str(未结束['compactionId']))
        校验来源命令标识('compaction/summary',数据['sourceCommandId'] if 'sourceCommandId' in 数据 else None,未结束['sourceCommandId'] if 'sourceCommandId' in 未结束 else None,失败)
        校验所有者(未结束['turn'],跟踪['openTurn'],类型,失败)
        if 未结束['summarized']:
            失败('compaction/summary repeated within one compaction')
        校验遮蔽序号(跟踪,事件,失败)
        代币=数据['shadowedTokenCount']
        代币是整数=(not isinstance(代币,bool)) and (isinstance(代币,int) or (isinstance(代币,float) and 代币.is_integer()))
        if (not 代币是整数) or 代币<0 or abs(代币)>安全整数上限:
            失败('compaction/summary shadowedTokenCount must be a non-negative safe integer')
        return {
            'kind':'summary',
            'compactionId':未结束['compactionId'],
            'sourceCommandId':未结束['sourceCommandId'] if 'sourceCommandId' in 未结束 else None,
            'startSeq':未结束['startSeq'],
            'turn':未结束['turn'],
        }
    校验标识(数据['compactionId'],'compaction/end compactionId',失败)
    if 'sourceCommandId' in 数据 and 数据['sourceCommandId'] is not None:
        校验标识(数据['sourceCommandId'],'compaction/end sourceCommandId',失败)
    if 未结束 is None:
        失败('compaction/end has no matching compaction/start')
        return None
    if 数据['compactionId']!=未结束['compactionId']:
        失败('compaction/end id '+str(数据['compactionId'])+' does not match compaction/start id '+str(未结束['compactionId']))
    校验来源命令标识('compaction/end',数据['sourceCommandId'] if 'sourceCommandId' in 数据 else None,未结束['sourceCommandId'] if 'sourceCommandId' in 未结束 else None,失败)
    if (数据['turn'] if 'turn' in 数据 else None)!=未结束['turn']:
        失败('compaction/end owner '+str(数据['turn'] if 'turn' in 数据 else None)+' does not match compaction/start owner '+str(未结束['turn']))
    校验所有者(未结束['turn'],跟踪['openTurn'],类型,失败)
    if ('error' not in 数据 or 数据['error'] is None) and (not 未结束['summarized']):
        失败('successful compaction/end requires one compaction/summary')
    return {'kind':'end'}

def 应用压缩迁移(迁移):
    """应用一次已提交的压缩迁移。返回新跟踪或 None（清掉括号）。"""
    种类=迁移['kind']
    if 种类=='start':
        return {
            'compactionId':迁移['compactionId'],
            'sourceCommandId':迁移['sourceCommandId'],
            'startSeq':迁移['startSeq'],
            'turn':迁移['turn'],
            'summarized':False,
        }
    if 种类=='summary':
        return {
            'compactionId':迁移['compactionId'],
            'sourceCommandId':迁移['sourceCommandId'],
            'startSeq':迁移['startSeq'],
            'turn':迁移['turn'],
            'summarized':True,
        }
    return None

def 安装(上下文,失败):
    """安装压缩 start/summary/end 检查。事件所有者把预提交暂存留在本地，避免词汇表进入中央辅助。"""
    跟踪表=weakref.WeakKeyDictionary()#会话 → 跟踪
    暂存={}#事件 id → 预提交暂存

    def 种子(会话):
        """回放该会话已有事件并记下已提交跟踪。"""
        表面事件=[]
        跟踪={
            'openTurn':None,
            'compaction':None,
            'surfaceEvents':表面事件,
            'surface':表面视图(表面事件,0,上下文.sessions.消息投影列表),
        }
        跟踪表[会话]=跟踪
        过期孤儿=继承孤儿开始序号列表(会话.events)
        for 事件 in 会话.events:
            未结束=跟踪['compaction']
            if 未结束 is None or 未结束['startSeq'] not in 过期孤儿:
                校验回合边界(跟踪,事件,失败)
            迁移=校验压缩事件(跟踪,事件,失败)
            if 迁移 is not None:
                跟踪['compaction']=应用压缩迁移(迁移)
            应用回合边界(跟踪,事件)
            表面事件.append(事件)
        return 跟踪

    def 取跟踪(会话):
        """已有则用，否则补种子。"""
        if 会话 in 跟踪表:
            return 跟踪表[会话]
        return 种子(会话)

    for 会话 in 上下文.sessions.列出():
        种子(会话)
    def 会话已创建(会话,*其余):
        """新会话创建时再种子。"""
        种子(会话)
    上下文.监听('session/created',会话已创建,{'全局':True})
    def 会话事件(会话,事件,*其余):
        """事件真正发布后再提交压缩迁移。"""
        跟踪=取跟踪(会话)
        校验回合边界(跟踪,事件,失败)
        改了回合=应用回合边界(跟踪,事件)
        类型=事件['type']
        if (not 改了回合) and 类型!='session/end-seed' and 类型!='compaction/start' and 类型!='compaction/summary' and 类型!='compaction/end':
            跟踪['surfaceEvents'].append(事件)
            return
        if not 改了回合:
            if id(事件) not in 暂存:
                失败('compaction event published without pre-commit validation')
                return
            候选=暂存[id(事件)]
            if 候选['session'] is not 会话:
                失败('compaction event published without pre-commit validation')
                return
            暂存.pop(id(事件),None)
            跟踪['compaction']=应用压缩迁移(候选['transition'])
        跟踪['surfaceEvents'].append(事件)
    上下文.监听('session/event',会话事件,{'全局':True})
    def 内部派发(_模式,事件名,参数,*其余):
        """提交前检查 session/event。"""
        if 事件名!='session/event':
            return
        会话=参数[0]
        事件=参数[1]
        跟踪=取跟踪(会话)
        校验回合边界(跟踪,事件,失败)
        迁移=校验压缩事件(跟踪,事件,失败)
        if 迁移 is not None:
            暂存[id(事件)]={'session':会话,'transition':迁移}

    上下文.监听('internal/dispatch',内部派发,{'全局':True})

安装.inject=['sessions']

def 应用(上下文):
    """向 invariants 登记本包，返回拆除器。"""
    return 上下文.invariants.register(包名,安装)

name=名称
inject=依赖
apply=应用
default=应用
