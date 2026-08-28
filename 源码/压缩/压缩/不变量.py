"""本包拥有的压缩日志流不变量。"""
import weakref#会话与事件弱表
from ...依赖 import cordis#外部依赖胶水
已兑现=cordis.工具.已兑现#立刻兑现的拆除器
from ..会话 import 是否替换表面事件#替换表面事件判断
from .检查点 import 是否压缩检查点来源#压缩检查点来源判断

包名='@deepseek-ai/dsh-compaction'#本包的不变量所有权名
名称='compaction-invariant'#配套不变量插件名
注入=['invariants']#依赖invariants服务
name=名称#Cordis插件名
inject=注入#Cordis依赖声明
def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段，缺席为缺省。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

安全整数上限=9007199254740991#JS Number.MAX_SAFE_INTEGER

def 是否安全整数(值):#对齐 Number.isSafeInteger
    """对齐 JS Number.isSafeInteger，排除布尔。"""
    if isinstance(值,bool):#布尔不是数字
        return False#布尔不是整数
    if isinstance(值,int):#整数
        return abs(值)<=安全整数上限#落在安全范围
    if isinstance(值,float) and 值.is_integer():#整值浮点
        return abs(值)<=安全整数上限#落在安全范围
    return False#其它类型

def 校验标识(值,标签,失败):#校验非空字符串 id
    """要求耐久不透明身份为非空字符串。"""
    if not isinstance(值,str) or len(值)==0:#空或非字符串
        失败(标签+' must be a non-empty string')#失败

def 校验来源命令标识(事件类型,值,期望,失败):#校验来源命令 id 与 start 一致
    """保持可选发起命令身份在同一事务内稳定。"""
    if 值 is not None:#有值则须非空字符串
        校验标识(值,事件类型+' sourceCommandId',失败)#校验形态
    if 值!=期望:#与 start 不一致
        失败(事件类型+' sourceCommandId '+str(值)+' does not match compaction/start sourceCommandId '+str(期望))#报告不匹配

def 校验检查点(跟踪,事件,失败):#校验压缩检查点
    """相对未结束压缩事务校验一次替换检查点。"""
    出处=取字段(取字段(事件,'data'),'source')#消息出处
    校验标识(取字段(出处,'compactionId'),'compaction checkpoint compactionId',失败)#检查点须带事务 id
    检查点命令=取字段(出处,'sourceCommandId')#可选来源命令
    if 检查点命令 is not None:#检查点带了来源命令
        校验标识(检查点命令,'compaction checkpoint sourceCommandId',失败)#须非空字符串
    未结束=取字段(跟踪,'compaction')#当前未结束事务
    if 未结束 is None:#没有配对 start
        失败('compaction checkpoint has no matching compaction/start')#没有配对 start
        return#已失败
    if 取字段(出处,'compactionId')!=取字段(未结束,'compactionId'):#事务 id 不一致
        失败('compaction checkpoint id '+str(取字段(出处,'compactionId'))+' does not match compaction/start id '+str(取字段(未结束,'compactionId')))#报告 id 不匹配
    校验来源命令标识('compaction checkpoint',检查点命令,取字段(未结束,'sourceCommandId'),失败)#来源命令须与 start 一致

def 继承孤儿开始序号们(事件们):#收集被种子边界作废的未配对 start
    """后续种子边界已使未配对压缩 start 过期。"""
    过期=set()#过期 seq
    未结束开始=None#当前未结束 start
    for 事件 in 事件们:#顺序扫描
        类型=取字段(事件,'type')#事件类型
        if 类型=='compaction/start':#新开压缩
            未结束开始=取字段(事件,'seq')#记下 start 序号
        elif 类型=='compaction/end':#正常结束
            未结束开始=None#配对完成
        elif 类型=='session/end-seed':#种子边界
            if 未结束开始 is not None:#未配对 start 作废
                过期.add(未结束开始)#记入过期集合
            未结束开始=None#边界后不再持有
    return 过期#返回过期集合

def 校验回合边界(跟踪,事件,失败):#校验回合边界不穿越未结束压缩
    """每个回合边界两侧不得跨过未结束的压缩括号。"""
    类型=取字段(事件,'type')#事件类型
    if (类型!='turn/start' and 类型!='turn/end') or 取字段(跟踪,'compaction') is None:#非回合边界或没有未结束压缩
        return#无需检查
    未结束=取字段(跟踪,'compaction')#未结束事务
    所有者='standalone compaction' if 取字段(未结束,'turn') is None else 'compaction for turn '+str(取字段(未结束,'turn'))#独立或某回合
    失败(类型+' cannot cross an open '+所有者)#边界不得穿越未结束压缩

def 应用回合边界(跟踪,事件):#应用回合边界
    """边界已被接受后推进已提交的回合光标。"""
    类型=取字段(事件,'type')#事件类型
    if 类型=='turn/start':#回合开始
        跟踪['openTurn']=取字段(取字段(事件,'data'),'turn')#记下未结束回合
        return True#已处理
    if 类型=='turn/end':#回合结束
        跟踪['openTurn']=None#清掉未结束回合
        return True#已处理
    return False#不是回合边界

def 校验所有者(所有者,未结束回合,事件类型,失败):#校验压缩所有者与当前回合
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

def 校验压缩事件(跟踪,事件,失败):#校验压缩相关事件
    """校验一次压缩事件，不推进已提交跟踪状态。返回待提交迁移或 None。"""
    类型=取字段(事件,'type')#事件类型
    if 类型=='session/end-seed':#种子边界清括号
        return {'kind':'end-seed'}#种子边界迁移
    if 类型=='user/message' and 是否替换表面事件(事件) and 是否压缩检查点来源(取字段(取字段(事件,'data'),'source')):#压缩检查点替换
        校验检查点(跟踪,事件,失败)#校验检查点对齐
        return None#检查点不改跟踪括号
    if 类型!='compaction/start' and 类型!='compaction/summary' and 类型!='compaction/end':#非压缩生命周期事件
        return None#无关
    未结束=取字段(跟踪,'compaction')#当前未结束事务
    数据=取字段(事件,'data')#事件载荷
    if 类型=='compaction/start':#开始压缩
        校验标识(取字段(数据,'compactionId'),'compaction/start compactionId',失败)#须有事务 id
        if 取字段(数据,'sourceCommandId') is not None:#带了来源命令
            校验标识(取字段(数据,'sourceCommandId'),'compaction/start sourceCommandId',失败)#须非空字符串
        if 未结束 is not None:#已有未结束压缩
            所有者描述='standalone compaction' if 取字段(未结束,'turn') is None else 'turn '+str(取字段(未结束,'turn'))#描述已有事务
            失败('compaction/start while '+所有者描述+' is still compacting')#禁止嵌套
        校验所有者(取字段(数据,'turn'),取字段(跟踪,'openTurn'),类型,失败)#所有者须与回合对齐
        return {#提交 start 迁移
            'kind':'start',#开始
            'compactionId':取字段(数据,'compactionId'),#事务 id
            'sourceCommandId':取字段(数据,'sourceCommandId'),#来源命令
            'startSeq':取字段(事件,'seq'),#本事件序号
            'turn':取字段(数据,'turn'),#所有者
        }#start 迁移结束
    if 类型=='compaction/summary':#摘要事件
        校验标识(取字段(数据,'compactionId'),'compaction/summary compactionId',失败)#须有事务 id
        if 取字段(数据,'sourceCommandId') is not None:#带了来源命令
            校验标识(取字段(数据,'sourceCommandId'),'compaction/summary sourceCommandId',失败)#须非空字符串
        if 未结束 is None:#没有配对 start
            失败('compaction/summary has no matching compaction/start')#失败
            return None#已失败
        if 取字段(数据,'compactionId')!=取字段(未结束,'compactionId'):#事务 id 不一致
            失败('compaction/summary id '+str(取字段(数据,'compactionId'))+' does not match compaction/start id '+str(取字段(未结束,'compactionId')))#报告 id 不匹配
        校验来源命令标识('compaction/summary',取字段(数据,'sourceCommandId'),取字段(未结束,'sourceCommandId'),失败)#来源命令须与 start 一致
        校验所有者(取字段(未结束,'turn'),取字段(跟踪,'openTurn'),类型,失败)#所有者须仍对齐回合
        if 取字段(未结束,'summarized'):#同一事务禁止重复摘要
            失败('compaction/summary repeated within one compaction')#失败
        序号们=取字段(数据,'shadowedSeqs') or []#被遮蔽 seq 列表
        if len(序号们)==0:#列表不得为空
            失败('compaction/summary shadowedSeqs must be non-empty')#失败
        区间=取字段(数据,'shadowedRange') or {}#被遮蔽区间
        if 序号们[0]!=取字段(区间,'start') or 序号们[-1]!=取字段(区间,'end'):#首尾须对齐区间
            失败('compaction/summary shadowedRange must match the first and last shadowedSeqs')#区间与列表不一致
        代币=取字段(数据,'shadowedTokenCount')#token 计数
        if (not 是否安全整数(代币)) or 代币<0:#token 须为非负安全整数
            失败('compaction/summary shadowedTokenCount must be a non-negative safe integer')#非法 token 计数
        return {#提交 summary 迁移
            'kind':'summary',#已摘要
            'compactionId':取字段(未结束,'compactionId'),#沿用事务 id
            'sourceCommandId':取字段(未结束,'sourceCommandId'),#沿用来源命令
            'startSeq':取字段(未结束,'startSeq'),#沿用 start 序号
            'turn':取字段(未结束,'turn'),#沿用所有者
        }#summary 迁移结束
    校验标识(取字段(数据,'compactionId'),'compaction/end compactionId',失败)#end 须有事务 id
    if 取字段(数据,'sourceCommandId') is not None:#带了来源命令
        校验标识(取字段(数据,'sourceCommandId'),'compaction/end sourceCommandId',失败)#须非空字符串
    if 未结束 is None:#没有配对 start
        失败('compaction/end has no matching compaction/start')#失败
        return None#已失败
    if 取字段(数据,'compactionId')!=取字段(未结束,'compactionId'):#事务 id 不一致
        失败('compaction/end id '+str(取字段(数据,'compactionId'))+' does not match compaction/start id '+str(取字段(未结束,'compactionId')))#报告 id 不匹配
    校验来源命令标识('compaction/end',取字段(数据,'sourceCommandId'),取字段(未结束,'sourceCommandId'),失败)#来源命令须与 start 一致
    if 取字段(数据,'turn')!=取字段(未结束,'turn'):#所有者不一致
        失败('compaction/end owner '+str(取字段(数据,'turn'))+' does not match compaction/start owner '+str(取字段(未结束,'turn')))#报告所有者不匹配
    校验所有者(取字段(未结束,'turn'),取字段(跟踪,'openTurn'),类型,失败)#所有者须仍对齐回合
    if 取字段(数据,'error') is None and (not 取字段(未结束,'summarized')):#成功结束却未见摘要
        失败('successful compaction/end requires one compaction/summary')#成功 end 必须先有 summary
    return {'kind':'end'}#提交 end 迁移

def 应用压缩迁移(迁移):#把迁移写进跟踪
    """应用一次已提交的压缩迁移。返回新跟踪或 None（清掉括号）。"""
    种类=取字段(迁移,'kind')#迁移种类
    if 种类=='start':#开始事务
        return {#新建未摘要跟踪
            'compactionId':取字段(迁移,'compactionId'),#事务 id
            'sourceCommandId':取字段(迁移,'sourceCommandId'),#来源命令
            'startSeq':取字段(迁移,'startSeq'),#start 序号
            'turn':取字段(迁移,'turn'),#所有者
            'summarized':False,#尚未摘要
        }#start 跟踪结束
    if 种类=='summary':#已摘要
        return {#更新为已摘要跟踪
            'compactionId':取字段(迁移,'compactionId'),#事务 id
            'sourceCommandId':取字段(迁移,'sourceCommandId'),#来源命令
            'startSeq':取字段(迁移,'startSeq'),#start 序号
            'turn':取字段(迁移,'turn'),#所有者
            'summarized':True,#已见摘要
        }#summary 跟踪结束
    return None#end 或 end-seed 清掉括号

def 安装(上下文对象,失败):#安装压缩不变量
    """安装压缩 start/summary/end 检查。事件所有者把预提交暂存留在本地，避免词汇表进入中央辅助。"""
    跟踪表=weakref.WeakKeyDictionary()#会话 → 跟踪
    暂存={}#事件 id → 预提交暂存

    def 种子(会话对象):#从已有事件重建跟踪
        """回放该会话已有事件并记下已提交跟踪。"""
        跟踪={'openTurn':None,'compaction':None}#空初始跟踪
        跟踪表[会话对象]=跟踪#挂到映射
        过期孤儿=继承孤儿开始序号们(取字段(会话对象,'events'))#继承前缀里被种子作废的 start
        for 事件 in 取字段(会话对象,'events'):#重放已有事件
            # 构造期种子修复边界可能早于证明继承孤儿已过期的 end-seed 标记。重放该继承前缀时，不让即将被清除的括号否决其修复。
            未结束=取字段(跟踪,'compaction')#当前括号
            if 未结束 is None or 取字段(未结束,'startSeq') not in 过期孤儿:#活括号才检查回合边界
                校验回合边界(跟踪,事件,失败)#校验回合不穿越压缩
            迁移=校验压缩事件(跟踪,事件,失败)#校验压缩事件
            if 迁移 is not None:#有迁移
                跟踪['compaction']=应用压缩迁移(迁移)#提交迁移
            应用回合边界(跟踪,事件)#推进回合光标
        return 跟踪#返回重建跟踪

    def 取跟踪(会话对象):#取或重建跟踪
        """已有则用，否则补种子。"""
        if 会话对象 in 跟踪表:#已有
            return 跟踪表[会话对象]#已提交跟踪
        return 种子(会话对象)#补种子

    for 会话对象 in 上下文对象.sessions.list():#为已有会话播种
        种子(会话对象)#种子校验
    def 会话已创建(会话对象,*其余):#新会话创建时再种子
        """新会话创建时再种子。"""
        种子(会话对象)#种子
    上下文对象.on('session/created',会话已创建,{'global':True})#全局监听
    def 会话事件(会话对象,事件,*其余):#已提交事件推进跟踪
        """事件真正发布后再提交压缩迁移。"""
        跟踪=取跟踪(会话对象)#取跟踪
        校验回合边界(跟踪,事件,失败)#校验回合边界
        if 应用回合边界(跟踪,事件):#回合边界已处理
            return#不再看压缩
        类型=取字段(事件,'type')#事件类型
        if 类型!='session/end-seed' and 类型!='compaction/start' and 类型!='compaction/summary' and 类型!='compaction/end':#非压缩生命周期
            return#忽略
        候选=暂存.get(id(事件))#取出预提交暂存
        if 候选 is None or 候选['session'] is not 会话对象:#未预校验不得发布
            失败('compaction event published without pre-commit validation')#失败
            return#已失败
        暂存.pop(id(事件),None)#消费暂存
        跟踪['compaction']=应用压缩迁移(候选['transition'])#提交迁移
    上下文对象.on('session/event',会话事件,{'global':True})#全局监听
    def 内部派发(_模式,事件名,参数,*其余):#派发前预校验
        """提交前检查 session/event。"""
        if 事件名!='session/event':#只看会话事件
            return#放过
        会话对象=参数[0]#第一实参是会话
        事件=参数[1]#第二实参是事件
        跟踪=取跟踪(会话对象)#取跟踪
        校验回合边界(跟踪,事件,失败)#校验回合边界
        迁移=校验压缩事件(跟踪,事件,失败)#校验压缩事件
        if 迁移 is not None:#有迁移则暂存
            暂存[id(事件)]={'session':会话对象,'transition':迁移}#预提交暂存

    上下文对象.on('internal/dispatch',内部派发,{'global':True})#全局监听

安装.inject=['sessions']#安装器还依赖 sessions
def 应用(上下文对象):#注册压缩不变量配套
    """注册压缩不变量配套，返回安装成功后已登记贡献的拆除器。"""
    return 已兑现(上下文对象.invariants.register(包名,安装))#登记并包成立即兑现的承诺

apply=应用#Cordis插件入口
