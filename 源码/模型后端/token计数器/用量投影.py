"""持久提供方报告 token 用量与上下文占用的纯折叠。对齐上游 `token-meter/src/usage-projection.ts`。公开面仅中文名。"""
from ..llm.助手流 import 末次助手流块#末次 usage 块
from .类型 import 计量错误#计量异常
from .表面投影 import 折叠表面投影#O(1)表面折叠

__all__=['用量投影定义','压力投影定义']#仅中文公开名

def 空用量桶():#空用量桶
    """空用量桶。"""
    return {'uncachedInputTokens':0,'outputTokens':0,'cacheReadTokens':0,'cacheWriteTokens':0}#四个桶为零

def 拆用量桶(用量):
    """从提供方用量拆桶。用量为 dict。"""
    缓存读=用量['cacheReadTokens'] if 'cacheReadTokens' in 用量 else None#缓存读
    缓存写=用量['cacheWriteTokens'] if 'cacheWriteTokens' in 用量 else None#缓存写
    return {
        'uncachedInputTokens':用量['inputTokens'],#未缓存输入
        'outputTokens':用量['outputTokens'],#输出含推理
        'cacheReadTokens':0 if 缓存读 is None else 缓存读,#缺省0
        'cacheWriteTokens':0 if 缓存写 is None else 缓存写,#缺省0
    }#拆桶结束

def 桶相等(左,右):
    """逐桶相等。"""
    return (
        左['uncachedInputTokens']==右['uncachedInputTokens']#未缓存输入
        and 左['outputTokens']==右['outputTokens']#输出
        and 左['cacheReadTokens']==右['cacheReadTokens']#缓存读
        and 左['cacheWriteTokens']==右['cacheWriteTokens']#缓存写
    )#逐桶

def 替换累加(累计,旧桶,新桶):
    """用新样本替换同一步旧样本后加进累计。"""
    旧未缓存=0 if 旧桶 is None else 旧桶['uncachedInputTokens']#同一步旧未缓存
    旧输出=0 if 旧桶 is None else 旧桶['outputTokens']#同一步旧输出
    旧读=0 if 旧桶 is None else 旧桶['cacheReadTokens']#同一步旧读
    旧写=0 if 旧桶 is None else 旧桶['cacheWriteTokens']#同一步旧写
    return {
        'uncachedInputTokens':累计['uncachedInputTokens']-旧未缓存+新桶['uncachedInputTokens'],#替换未缓存输入
        'outputTokens':累计['outputTokens']-旧输出+新桶['outputTokens'],#替换输出
        'cacheReadTokens':累计['cacheReadTokens']-旧读+新桶['cacheReadTokens'],#替换缓存读
        'cacheWriteTokens':累计['cacheWriteTokens']-旧写+新桶['cacheWriteTokens'],#替换缓存写
    }#新累计

class 用量视图模式:
    """用量投影线路载荷模式。"""
    @staticmethod
    def parse(值):
        """校验四个非负整数桶。值必须是 dict。"""
        if not isinstance(值,dict):#必须是对象
            raise 计量错误('tokenUsage view must be an object')#拒绝
        需要=('uncachedInputTokens','outputTokens','cacheReadTokens','cacheWriteTokens')#四个桶
        for 键 in 值:#自有键
            if 键 not in 需要:#未知键
                raise 计量错误('tokenUsage view unknown key "'+键+'"')#严格
        结果={}#输出
        for 键 in 需要:#逐桶
            if 键 not in 值:#缺键
                raise 计量错误('tokenUsage view missing key "'+键+'"')#必填
            数字=值[键]#桶值
            if isinstance(数字,bool) or not isinstance(数字,(int,float)) or 数字!=int(数字) or 数字<0:#入口校验非负整数，先排除 bool
                raise 计量错误('tokenUsage view '+键+' must be a nonnegative integer')#非负整数
            结果[键]=int(数字)#收成int
        return 结果#校验后的视图

class 压力视图模式:
    """压力投影线路载荷模式。"""
    @staticmethod
    def parse(值):
        """校验可选压力字段。值必须是 dict。"""
        if not isinstance(值,dict):#必须是对象
            raise 计量错误('contextPressure view must be an object')#拒绝
        结果={}#输出
        for 键 in 值:#自有键
            if 键 not in ('pressureTokens','projectedTokens','contextWindow'):#未知键
                raise 计量错误('contextPressure view unknown key "'+键+'"')#严格
            数字=值[键]#字段值
            if 键=='contextWindow':#窗口必须为正整数
                if isinstance(数字,bool) or not isinstance(数字,(int,float)) or 数字!=int(数字) or 数字<=0:#入口校验正整数，先排除 bool
                    raise 计量错误('contextPressure view '+键+' invalid')#类型或范围
            else:#压力与投影必须为非负整数
                if isinstance(数字,bool) or not isinstance(数字,(int,float)) or 数字!=int(数字) or 数字<0:#入口校验非负整数，先排除 bool
                    raise 计量错误('contextPressure view '+键+' invalid')#类型或范围
            结果[键]=int(数字)#收成int
        return 结果#校验后的视图

def 提示词压力(用量):
    """一次请求的提示词侧压力：输入加缓存流量，不含输出。用量为 dict。"""
    缓存读=用量['cacheReadTokens'] if 'cacheReadTokens' in 用量 else None#缓存读
    缓存写=用量['cacheWriteTokens'] if 'cacheWriteTokens' in 用量 else None#缓存写
    return 用量['inputTokens']+(0 if 缓存读 is None else 缓存读)+(0 if 缓存写 is None else 缓存写)#输入加缓存读写

def 事件用量(事件):
    """一次耐久助手结算为其尝试报告的用量（若有）。事件为 dict。"""
    种类=事件['type']#事件类型
    数据=事件['data']#载荷
    if 种类=='assistant/message' and 'usage' in 数据:#定稿带用量
        return 数据['usage']#消息上的用量
    if 种类!='assistant/message' and 种类!='assistant/attempt':#其余无
        return None#无
    块=末次助手流块(数据['stream'] if 'stream' in 数据 else [],'usage')#流末 usage
    return None if 块 is None else 块.get('usage')#用量

def 用量初态():
    """空累计、无样本。"""
    return {'totals':空用量桶(),'last':None}#初态

def 用量转移(状态,事件):
    """折一条用量事件。事件为 dict。"""
    种类=事件['type']#事件类型
    数据=事件['data']#载荷
    if 种类=='llm/retry-started':#重试已开始
        上一样本=状态['last']#最近样本
        if 上一样本 is not None and 上一样本['turn']==数据['turn'] and 上一样本['step']==数据['step']:#同一步
            return {**状态,'last':None}#关掉替换槽
        return 状态#无关则原样
    if 种类!='assistant/message' and 种类!='assistant/attempt':#非结算
        return 状态#原样
    用量=事件用量(事件)#取用量
    if 用量 is None:#无样本
        return 状态#原样
    回合=数据['turn']#回合
    步=数据['step']#步
    桶=拆用量桶(用量)#拆成四个桶
    上一样本=状态['last']#最近样本
    旧桶=None#同一步旧桶
    if 上一样本 is not None and 上一样本['turn']==回合 and 上一样本['step']==步:#同一回合同一步
        旧桶=上一样本['buckets']#用旧桶替换
    if 旧桶 is not None and 桶相等(旧桶,桶):#完全相同则不动
        return 状态#原状态
    return {'totals':替换累加(状态['totals'],旧桶,桶),'last':{'turn':回合,'step':步,'buckets':桶}}#新状态

def 用量视图(状态):
    """对外只看累计。"""
    return 状态['totals']#累计桶

用量投影定义={
    'key':'tokenUsage',#投影键
    'schema':用量视图模式,#视图模式
    'init':用量初态,#空累计
    'apply':用量转移,#折一条事件
    'view':用量视图,#对外累计
    'stateVersion':2,#状态版本（嵌入流结算）
}#用量投影定义结束

def 压力初态():
    """仅表面合计为零。"""
    return {'surfaceTokens':0}#初态

def 压力转移(状态,事件):
    """折一条压力事件。事件为 dict。"""
    折叠=折叠表面投影(状态['claim'] if 'claim' in 状态 else None,事件)#折叠表面
    下一=状态#从当前状态出发
    if 事件['type']=='request/context':#窗口记录
        数据=事件['data']#载荷
        窗口=数据['contextWindow'] if 'contextWindow' in 数据 else None#新窗口
        旧窗口=状态['contextWindow'] if 'contextWindow' in 状态 else None#旧窗口
        if 窗口!=旧窗口:#窗口变了
            if 窗口 is not None:#有新窗口
                下一={**下一,'contextWindow':窗口}#写入窗口
            else:#明确去掉窗口
                下一={键:值 for 键,值 in 下一.items() if 键!='contextWindow'}#剥掉窗口字段
    用量=事件用量(事件)#本事件用量
    if 用量 is not None:#有用量样本
        压力=提示词压力(用量)#提示词侧压力
        旧压力=下一['pressureTokens'] if 'pressureTokens' in 下一 else None#旧压力
        采样表面=下一['sampledSurfaceTokens'] if 'sampledSurfaceTokens' in 下一 else None#采样表面
        if 压力!=旧压力 or 采样表面!=下一['surfaceTokens']:#压力或采样表面变了
            下一={**下一,'pressureTokens':压力,'sampledSurfaceTokens':下一['surfaceTokens']}#在加入表面之前盖戳
    if 折叠['deltaTokens']!=0:#表面动了
        下一={**下一,'surfaceTokens':下一['surfaceTokens']+折叠['deltaTokens']}#更新表面合计
    if ('claim' not in 状态 or 状态['claim'] is None) and 折叠['claim'] is None:#声明未变
        return 下一#保持next
    无声明={键:值 for 键,值 in 下一.items() if 键!='claim'}#剥掉旧声明
    if 折叠['claim'] is None:#无则去掉
        return 无声明#不含声明
    return {**无声明,'claim':折叠['claim']}#换新声明

def 压力视图(状态):
    """对外视图。"""
    结果={}#对外字段
    if 'contextWindow' in 状态:#有窗口才带上
        结果['contextWindow']=状态['contextWindow']#窗口
    if 'pressureTokens' in 状态:#有压力才带上
        结果['pressureTokens']=状态['pressureTokens']#压力
    if 'pressureTokens' not in 状态 or 'sampledSurfaceTokens' not in 状态:#还缺样本
        return 结果#不发投影
    结果['projectedTokens']=max(0,状态['pressureTokens']+状态['surfaceTokens']-状态['sampledSurfaceTokens'])#样本加表面移动，下限0
    return 结果#视图

压力投影定义={
    'key':'contextPressure',#投影键
    'schema':压力视图模式,#视图模式
    'init':压力初态,#仅表面合计为零
    'apply':压力转移,#折一条事件
    'view':压力视图,#对外视图
    'stateVersion':4,#状态版本
}#压力投影定义结束
