"""本包拥有的压缩日志流不变量。"""
import weakref#会话与事件弱表
from ...内核.会话 import 是否替换表面事件#替换表面事件判断
from .检查点 import 是否压缩检查点来源#压缩检查点来源判断

包名='@deepseek-ai/dsh-compaction'#本包的不变量所有权名
名称='compaction-invariant'#配套不变量插件名
注入=['invariants']#依赖invariants服务
安全整数上限=9007199254740991#外来 JSON Number.MAX_SAFE_INTEGER

__all__=['包名','名称','注入','安装','应用']#仅中文公开名

def 校验标识(值,标签,失败):
    """要求耐久不透明身份为非空字符串。"""
    if not isinstance(值,str) or len(值)==0:#空或非字符串
        失败(标签+' must be a non-empty string')#失败

def 校验来源命令标识(事件类型,值,期望,失败):
    """保持可选发起命令身份在同一事务内稳定。"""
    if 值 is not None:#有值则须非空字符串
        校验标识(值,事件类型+' sourceCommandId',失败)#校验形态
    if 值!=期望:#与 start 不一致
        失败(事件类型+' sourceCommandId '+str(值)+' does not match compaction/start sourceCommandId '+str(期望))#报告不匹配

def 校验检查点(跟踪,事件,失败):
    """相对未结束压缩事务校验一次替换检查点。"""
    出处=事件['data']['source']#消息出处
    校验标识(出处['compactionId'],'compaction checkpoint compactionId',失败)#检查点须带事务 id
    检查点命令=出处['sourceCommandId'] if 'sourceCommandId' in 出处 else None#可选来源命令
    if 检查点命令 is not None:#检查点带了来源命令
        校验标识(检查点命令,'compaction checkpoint sourceCommandId',失败)#须非空字符串
    未结束=跟踪['compaction']#当前未结束事务
    if 未结束 is None:#没有配对 start
        失败('compaction checkpoint has no matching compaction/start')#没有配对 start
        return#已失败
    if 出处['compactionId']!=未结束['compactionId']:#事务 id 不一致
        失败('compaction checkpoint id '+str(出处['compactionId'])+' does not match compaction/start id '+str(未结束['compactionId']))#报告 id 不匹配
    校验来源命令标识('compaction checkpoint',检查点命令,未结束['sourceCommandId'] if 'sourceCommandId' in 未结束 else None,失败)#来源命令须与 start 一致

def 继承孤儿开始序号列表(事件列表):
    """后续种子边界已使未配对压缩 start 过期。"""
    过期=set()#过期 seq
    未结束开始=None#当前未结束 start
    for 事件 in 事件列表:#顺序扫描
        类型=事件['type']#事件类型
        if 类型=='compaction/start':#新开压缩
            未结束开始=事件['seq']#记下 start 序号
        elif 类型=='compaction/end':#正常结束
            未结束开始=None#配对完成
        elif 类型=='session/end-seed':#种子边界
            if 未结束开始 is not None:#未配对 start 作废
                过期.add(未结束开始)#记入过期集合
            未结束开始=None#边界后不再持有
    return 过期#返回过期集合

def 校验回合边界(跟踪,事件,失败):
    """每个回合边界两侧不得跨过未结束的压缩括号。"""
    类型=事件['type']#事件类型
    if (类型!='turn/start' and 类型!='turn/end') or 跟踪['compaction'] is None:#非回合边界或没有未结束压缩
        return#无需检查
    未结束=跟踪['compaction']#未结束事务
    所有者='standalone compaction' if 未结束['turn'] is None else 'compaction for turn '+str(未结束['turn'])#独立或某回合
    失败(类型+' cannot cross an open '+所有者)#边界不得穿越未结束压缩

def 应用回合边界(跟踪,事件):
    """边界已被接受后推进已提交的回合光标。"""
    类型=事件['type']#事件类型
    if 类型=='turn/start':#回合开始
        跟踪['openTurn']=事件['data']['turn']#记下未结束回合
        return True#已处理
    if 类型=='turn/end':#回合结束
        跟踪['openTurn']=None#清掉未结束回合
        return True#已处理
    return False#不是回合边界

def 校验所有者(所有者,未结束回合,事件类型,失败):
    """要求有编号括号落在其确切回合内，或独立括号落在回合之间。"""
    if 所有者 is None:#独立事务
        if 未结束回合 is not None:#回合未结束却声称独立
            失败(事件类型+' is standalone but turn '+str(未结束回合)+' is open')#失败
        return#独立且无未结束回合
    if 未结束回合 is None:#无未结束回合却声称属于某回合
        失败(事件类型+' for turn '+str(所有者)+' appended outside any open turn')#失败
        return#已失败
    if 所有者!=未结束回合:#所有者与当前回合不一致
        失败(事件类型+' names turn '+str(所有者)+' but open turn is '+str(未结束回合))#失败

def 校验压缩事件(跟踪,事件,失败):
    """校验一次压缩事件，不推进已提交跟踪状态。返回待提交迁移或 None。"""
    类型=事件['type']#事件类型
    if 类型=='session/end-seed':#种子边界清括号
        return {'kind':'end-seed'}#种子边界迁移
    if 类型=='user/message' and 是否替换表面事件(事件) and 是否压缩检查点来源(事件['data']['source'] if 'source' in 事件['data'] else None):#压缩检查点替换
        校验检查点(跟踪,事件,失败)#校验检查点对齐
        return None#检查点不改跟踪括号
    if 类型!='compaction/start' and 类型!='compaction/summary' and 类型!='compaction/end':#非压缩生命周期事件
        return None#无关
    未结束=跟踪['compaction']#当前未结束事务
    数据=事件['data']#事件载荷
    if 类型=='compaction/start':#开始压缩
        校验标识(数据['compactionId'],'compaction/start compactionId',失败)#须有事务 id
        if 'sourceCommandId' in 数据 and 数据['sourceCommandId'] is not None:#带了来源命令
            校验标识(数据['sourceCommandId'],'compaction/start sourceCommandId',失败)#须非空字符串
        if 未结束 is not None:#已有未结束压缩
            所有者描述='standalone compaction' if 未结束['turn'] is None else 'turn '+str(未结束['turn'])#描述已有事务
            失败('compaction/start while '+所有者描述+' is still compacting')#禁止嵌套
        校验所有者(数据['turn'] if 'turn' in 数据 else None,跟踪['openTurn'],类型,失败)#所有者须与回合对齐
        return {#提交 start 迁移
            'kind':'start',#开始
            'compactionId':数据['compactionId'],#事务 id
            'sourceCommandId':数据['sourceCommandId'] if 'sourceCommandId' in 数据 else None,#来源命令
            'startSeq':事件['seq'],#本事件序号
            'turn':数据['turn'] if 'turn' in 数据 else None,#所有者
        }#start 迁移结束
    if 类型=='compaction/summary':#摘要事件
        校验标识(数据['compactionId'],'compaction/summary compactionId',失败)#须有事务 id
        if 'sourceCommandId' in 数据 and 数据['sourceCommandId'] is not None:#带了来源命令
            校验标识(数据['sourceCommandId'],'compaction/summary sourceCommandId',失败)#须非空字符串
        if 未结束 is None:#没有配对 start
            失败('compaction/summary has no matching compaction/start')#失败
            return None#已失败
        if 数据['compactionId']!=未结束['compactionId']:#事务 id 不一致
            失败('compaction/summary id '+str(数据['compactionId'])+' does not match compaction/start id '+str(未结束['compactionId']))#报告 id 不匹配
        校验来源命令标识('compaction/summary',数据['sourceCommandId'] if 'sourceCommandId' in 数据 else None,未结束['sourceCommandId'] if 'sourceCommandId' in 未结束 else None,失败)#来源命令须与 start 一致
        校验所有者(未结束['turn'],跟踪['openTurn'],类型,失败)#所有者须仍对齐回合
        if 未结束['summarized']:#同一事务禁止重复摘要
            失败('compaction/summary repeated within one compaction')#失败
        序号列表=数据['shadowedSeqs'] if 'shadowedSeqs' in 数据 and 数据['shadowedSeqs'] is not None else []#被遮蔽 seq 列表
        if len(序号列表)==0:#列表不得为空
            失败('compaction/summary shadowedSeqs must be non-empty')#失败
        区间=数据['shadowedRange'] if 'shadowedRange' in 数据 and 数据['shadowedRange'] is not None else {}#被遮蔽区间
        if 序号列表[0]!=区间['start'] or 序号列表[-1]!=区间['end']:#首尾须对齐区间
            失败('compaction/summary shadowedRange must match the first and last shadowedSeqs')#区间与列表不一致
        代币=数据['shadowedTokenCount']#token 计数
        代币是整数=(not isinstance(代币,bool)) and (isinstance(代币,int) or (isinstance(代币,float) and 代币.is_integer()))#排除布尔
        if (not 代币是整数) or 代币<0 or abs(代币)>安全整数上限:#token 须为非负安全整数
            失败('compaction/summary shadowedTokenCount must be a non-negative safe integer')#非法 token 计数
        return {#提交 summary 迁移
            'kind':'summary',#已摘要
            'compactionId':未结束['compactionId'],#沿用事务 id
            'sourceCommandId':未结束['sourceCommandId'] if 'sourceCommandId' in 未结束 else None,#沿用来源命令
            'startSeq':未结束['startSeq'],#沿用 start 序号
            'turn':未结束['turn'],#沿用所有者
        }#summary 迁移结束
    校验标识(数据['compactionId'],'compaction/end compactionId',失败)#end 须有事务 id
    if 'sourceCommandId' in 数据 and 数据['sourceCommandId'] is not None:#带了来源命令
        校验标识(数据['sourceCommandId'],'compaction/end sourceCommandId',失败)#须非空字符串
    if 未结束 is None:#没有配对 start
        失败('compaction/end has no matching compaction/start')#失败
        return None#已失败
    if 数据['compactionId']!=未结束['compactionId']:#事务 id 不一致
        失败('compaction/end id '+str(数据['compactionId'])+' does not match compaction/start id '+str(未结束['compactionId']))#报告 id 不匹配
    校验来源命令标识('compaction/end',数据['sourceCommandId'] if 'sourceCommandId' in 数据 else None,未结束['sourceCommandId'] if 'sourceCommandId' in 未结束 else None,失败)#来源命令须与 start 一致
    if (数据['turn'] if 'turn' in 数据 else None)!=未结束['turn']:#所有者不一致
        失败('compaction/end owner '+str(数据['turn'] if 'turn' in 数据 else None)+' does not match compaction/start owner '+str(未结束['turn']))#报告所有者不匹配
    校验所有者(未结束['turn'],跟踪['openTurn'],类型,失败)#所有者须仍对齐回合
    if ('error' not in 数据 or 数据['error'] is None) and (not 未结束['summarized']):#成功结束却未见摘要
        失败('successful compaction/end requires one compaction/summary')#成功 end 必须先有 summary
    return {'kind':'end'}#提交 end 迁移

def 应用压缩迁移(迁移):
    """应用一次已提交的压缩迁移。返回新跟踪或 None（清掉括号）。"""
    种类=迁移['kind']#迁移种类
    if 种类=='start':#开始事务
        return {#新建未摘要跟踪
            'compactionId':迁移['compactionId'],#事务 id
            'sourceCommandId':迁移['sourceCommandId'],#来源命令
            'startSeq':迁移['startSeq'],#start 序号
            'turn':迁移['turn'],#所有者
            'summarized':False,#尚未摘要
        }#start 跟踪结束
    if 种类=='summary':#已摘要
        return {#更新为已摘要跟踪
            'compactionId':迁移['compactionId'],#事务 id
            'sourceCommandId':迁移['sourceCommandId'],#来源命令
            'startSeq':迁移['startSeq'],#start 序号
            'turn':迁移['turn'],#所有者
            'summarized':True,#已见摘要
        }#summary 跟踪结束
    return None#end 或 end-seed 清掉括号

def 安装(上下文对象,失败):
    """安装压缩 start/summary/end 检查。事件所有者把预提交暂存留在本地，避免词汇表进入中央辅助。"""
    跟踪表=weakref.WeakKeyDictionary()#会话 → 跟踪
    暂存={}#事件 id → 预提交暂存

    def 种子(会话):
        """回放该会话已有事件并记下已提交跟踪。"""
        跟踪={'openTurn':None,'compaction':None}#空初始跟踪
        跟踪表[会话]=跟踪#挂到映射
        过期孤儿=继承孤儿开始序号列表(会话.events)#继承前缀里被种子作废的 start
        for 事件 in 会话.events:#重放已有事件
            未结束=跟踪['compaction']#当前括号
            if 未结束 is None or 未结束['startSeq'] not in 过期孤儿:#活括号才检查回合边界
                校验回合边界(跟踪,事件,失败)#校验回合不穿越压缩
            迁移=校验压缩事件(跟踪,事件,失败)#校验压缩事件
            if 迁移 is not None:#有迁移
                跟踪['compaction']=应用压缩迁移(迁移)#提交迁移
            应用回合边界(跟踪,事件)#推进回合光标
        return 跟踪#返回重建跟踪

    def 取跟踪(会话):
        """已有则用，否则补种子。"""
        if 会话 in 跟踪表:#已有
            return 跟踪表[会话]#已提交跟踪
        return 种子(会话)#补种子

    for 会话 in 上下文对象.sessions.列出():#为已有会话播种
        种子(会话)#种子校验
    def 会话已创建(会话,*其余):
        """新会话创建时再种子。"""
        种子(会话)#种子
    上下文对象.监听('session/created',会话已创建,{'全局':True})#全局监听
    def 会话事件(会话,事件,*其余):
        """事件真正发布后再提交压缩迁移。"""
        跟踪=取跟踪(会话)#取跟踪
        校验回合边界(跟踪,事件,失败)#校验回合边界
        if 应用回合边界(跟踪,事件):#回合边界已处理
            return#不再看压缩
        类型=事件['type']#事件类型
        if 类型!='session/end-seed' and 类型!='compaction/start' and 类型!='compaction/summary' and 类型!='compaction/end':#非压缩生命周期
            return#忽略
        候选=暂存.get(id(事件))#取出预提交暂存
        if 候选 is None or 候选['session'] is not 会话:#未预校验不得发布
            失败('compaction event published without pre-commit validation')#失败
            return#已失败
        暂存.pop(id(事件),None)#消费暂存
        跟踪['compaction']=应用压缩迁移(候选['transition'])#提交迁移
    上下文对象.监听('session/event',会话事件,{'全局':True})#全局监听
    def 内部派发(_模式,事件名,参数,*其余):
        """提交前检查 session/event。"""
        if 事件名!='session/event':#只看会话事件
            return#放过
        会话=参数[0]#第一实参是会话
        事件=参数[1]#第二实参是事件
        跟踪=取跟踪(会话)#取跟踪
        校验回合边界(跟踪,事件,失败)#校验回合边界
        迁移=校验压缩事件(跟踪,事件,失败)#校验压缩事件
        if 迁移 is not None:#有迁移则暂存
            暂存[id(事件)]={'session':会话,'transition':迁移}#预提交暂存

    上下文对象.监听('internal/dispatch',内部派发,{'全局':True})#全局监听

安装.inject=['sessions']#安装器还依赖 sessions

def 应用(上下文对象):
    """注册压缩不变量配套，返回安装成功后已登记贡献的拆除器。"""
    return 上下文对象.invariants.register(包名,安装)#登记贡献并返回拆除器

应用.name=名称#Cordis name 槽
应用.inject=注入#Cordis inject 槽
default=应用#Cordis 默认导出槽
apply=应用#Cordis插件入口
