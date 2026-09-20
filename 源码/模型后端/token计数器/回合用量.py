"""把一个完整 Turn 的耐久尝试生命周期折叠为精确 token 计量。

公开面仅中文名。
缺失生命周期边界、不完整用量、不安全计数或矛盾精确总量时整轮不可披露。
"""
from ..llm.助手流 import 末次助手流块#末次 usage 块

__all__=['派生回合令牌用量']#仅中文公开名

def _是计数(值):#非负安全整数
    """值是否为非负安全整数计数。"""
    return isinstance(值,int) and not isinstance(值,bool) and 值>=0 and abs(值)<=9007199254740991#安全非负

def _安全求和(值列表):#安全求和
    """求和；溢出安全整数则失败。"""
    合计=0#累计
    for 值 in 值列表:#逐项
        合计+=值#累加
        if isinstance(合计,bool) or not isinstance(合计,int) or abs(合计)>9007199254740991:#溢出
            return None#失败
    return 合计#合计

def _消息路由(消息):#消息路由
    """从助手消息来源取提供方/模型路由。"""
    来源=消息.get('source') if isinstance(消息,dict) else None#来源
    if not isinstance(来源,dict):#非法
        return None#无
    提供方=来源.get('provider')#提供方
    模型=来源.get('model')#模型
    if isinstance(提供方,str) and 提供方!='' and isinstance(模型,str) and 模型!='':#有效对
        return {'provider':提供方,'model':模型}#路由
    return None#无

def _流用量(流):#流用量
    """从嵌入流末次 usage 块取用量。"""
    块=末次助手流块(流,'usage')#末次 usage
    if 块 is None:#无
        return None#无
    return 块.get('usage')#用量

def _归一用量(用量,路由=None):#归一用量
    """校验并归一一次尝试用量。"""
    if not isinstance(用量,dict):#非法
        return None#失败
    输入=用量.get('inputTokens')#输入
    输出=用量.get('outputTokens')#输出
    缓存读=用量.get('cacheReadTokens')#缓存读
    缓存写=用量.get('cacheWriteTokens')#缓存写
    推理=用量.get('reasoningTokens')#推理
    总量=用量.get('totalTokens')#总量
    if not _是计数(输入) or not _是计数(输出):#缺必要
        return None#失败
    if 缓存读 is not None and not _是计数(缓存读):#非法读
        return None#失败
    if 缓存写 is not None and not _是计数(缓存写):#非法写
        return None#失败
    if 推理 is not None and (not _是计数(推理) or 推理>输出):#非法推理
        return None#失败
    已知提示=_安全求和([输入,*([缓存读] if 缓存读 is not None else []),*([缓存写] if 缓存写 is not None else [])])#已知提示
    if 已知提示 is None:#溢出
        return None#失败
    if 总量 is not None:#有精确总量
        if not _是计数(总量):#非法
            return None#失败
        精确提示=总量-输出#精确提示
        if not _是计数(精确提示) or 精确提示<已知提示:#矛盾
            return None#失败
        if 缓存读 is not None and 缓存写 is not None and 精确提示!=已知提示:#双缓存须贴合
            return None#失败
        精确总量=总量#采用
    else:#无总量则须双缓存推导
        if 缓存读 is None or 缓存写 is None:#缺桶
            return None#失败
        推导=_安全求和([已知提示,输出])#推导总量
        if 推导 is None:#溢出
            return None#失败
        精确总量=推导#采用
    结果={'inputTokens':输入,'outputTokens':输出,'totalTokens':精确总量}#基线
    if 缓存读 is not None:#可选
        结果['cacheReadTokens']=缓存读#写入
    if 缓存写 is not None:#可选
        结果['cacheWriteTokens']=缓存写#写入
    if 推理 is not None:#可选
        结果['reasoningTokens']=推理#写入
    if 路由 is not None:#可选
        结果['route']=路由#写入
    return 结果#归一

def _聚合尝试(尝试列表):#聚合尝试
    """把多次归一尝试聚合成整轮用量。"""
    if len(尝试列表)==0:#空
        return None#无
    输入=_安全求和([项['inputTokens'] for 项 in 尝试列表])#输入和
    输出=_安全求和([项['outputTokens'] for 项 in 尝试列表])#输出和
    总量=_安全求和([项['totalTokens'] for 项 in 尝试列表])#总量和
    if 输入 is None or 输出 is None or 总量 is None:#溢出
        return None#失败
    缓存读列表=[项.get('cacheReadTokens') for 项 in 尝试列表]#读列表
    缓存写列表=[项.get('cacheWriteTokens') for 项 in 尝试列表]#写列表
    推理列表=[项.get('reasoningTokens') for 项 in 尝试列表]#推理列表
    缓存读=_安全求和(缓存读列表) if all(_是计数(项) for 项 in 缓存读列表) else None#汇总读
    缓存写=_安全求和(缓存写列表) if all(_是计数(项) for 项 in 缓存写列表) else None#汇总写
    推理=_安全求和(推理列表) if all(_是计数(项) for 项 in 推理列表) else None#汇总推理
    路由列表=[项.get('route') for 项 in 尝试列表]#路由
    路由=None#可选路由
    if all(项 is not None for 项 in 路由列表):#全部有归属
        唯一={}#去重
        for 项 in 路由列表:#逐路由
            唯一[f"{项['provider']}\0{项['model']}"]=项#去重键
        路由=list(唯一.values())#列表
    结果={'uncachedInputTokens':输入,'outputTokens':输出,'totalTokens':总量}#基线
    if 缓存读 is not None:#可选
        结果['cacheReadTokens']=缓存读#写入
    if 缓存写 is not None:#可选
        结果['cacheWriteTokens']=缓存写#写入
    if 推理 is not None:#可选
        结果['reasoningTokens']=推理#写入
    if 路由 is not None:#可选
        结果['routes']=路由#写入
    return 结果#聚合

def _同尝试(状态,回合,步骤):#同尝试
    """状态是否对应该回合/步骤。"""
    return 状态['turn']==回合 and 状态['step']==步骤#坐标

def 派生回合令牌用量(事件列表):#派生回合令牌用量
    """把一个完整 Turn 的耐久尝试生命周期折叠为精确 token 计量。"""
    状态={'kind':'idle'}#尝试态
    尝试列表=[]#已关闭尝试
    回合=None#当前回合
    已见结束=False#是否见 turn/end
    无效=False#是否失效

    def 关闭开放(路由=None):#关闭开放尝试
        """用样本关闭 open 态。"""
        if 状态['kind']!='open' or 'sample' not in 状态:#不可关
            return False#失败
        归一=_归一用量(状态['sample'],路由)#归一
        if 归一 is None:#非法
            return False#失败
        尝试列表.append(归一)#收下
        return True#成功

    for 事件 in 事件列表:#逐事件
        if 无效:#已失效
            break#停止
        类型=事件.get('type') if isinstance(事件,dict) else getattr(事件,'type',None)#类型
        数据=事件.get('data') if isinstance(事件,dict) else getattr(事件,'data',{})#数据
        if not isinstance(数据,dict):#归一
            数据={}#空
        if 类型=='turn/start':#回合开始
            if 回合 is not None or 状态['kind']!='idle':#非法
                无效=True#失效
            else:#记下
                回合=数据.get('turn')#回合号
            continue#下一项
        if 回合 is None:#缺回合
            无效=True#失效
            break#停止
        if 类型=='turn/end':#回合结束
            if 数据.get('turn')!=回合 or 状态['kind']!='idle' or 已见结束:#非法
                无效=True#失效
            else:#记下
                已见结束=True#已见
            continue#下一项
        if 已见结束:#结束后还有
            无效=True#失效
            break#停止
        if 类型=='step/start':#步骤开始
            if 数据.get('turn')!=回合 or 状态['kind']!='idle':#非法
                无效=True#失效
            else:#打开
                状态={'kind':'open','turn':回合,'step':数据.get('step')}#打开
            continue#下一项
        if 类型=='llm/retry-started':#重试开始
            if (数据.get('turn')!=回合
                or 状态['kind']!='settled'
                or 状态.get('by')!='retry'
                or not _同尝试(状态,数据.get('turn'),数据.get('step'))):#非法
                无效=True#失效
            else:#重开
                状态={'kind':'open','turn':回合,'step':数据.get('step')}#打开
            continue#下一项
        if 类型=='assistant/attempt':#助手尝试
            if (数据.get('turn')!=回合
                or 状态['kind']!='open'
                or not _同尝试(状态,数据.get('turn'),数据.get('step'))):#非法
                无效=True#失效
                continue#下一项
            样本=_流用量(数据.get('stream') or [])#流用量
            if 样本 is None:#回退
                样本=状态.get('sample')#已有样本
            状态={'kind':'open','turn':回合,'step':数据.get('step')}#保持 open
            if 样本 is not None:#有样本
                状态['sample']=样本#写入
            if not 关闭开放():#关闭失败
                无效=True#失效
            else:#关闭成功
                状态={'kind':'finishClosed','turn':回合,'step':数据.get('step')}#finish 关闭
            continue#下一项
        if 类型=='assistant/message':#助手消息
            if (数据.get('turn')!=回合
                or 状态['kind']!='open'
                or not _同尝试(状态,数据.get('turn'),数据.get('step'))):#非法
                无效=True#失效
                continue#下一项
            if 'usage' not in 数据:#回退流
                样本=_流用量(数据.get('stream') or [])#流用量
            else:
                样本=数据['usage']#显式用量
            if 样本 is not None:#有样本
                状态={**状态,'sample':样本}#更新
            路由=_消息路由(数据.get('message') or {})#路由
            if not 关闭开放(路由):#关闭失败
                无效=True#失效
            else:#成功
                状态={'kind':'settled','turn':回合,'step':数据.get('step'),'by':'message'}#已结算
            continue#下一项
        if 类型=='llm/retry':#重试落定
            if (数据.get('turn')!=回合 or 状态['kind']=='idle'
                or not _同尝试(状态,数据.get('turn'),数据.get('step'))):#非法
                无效=True#失效
                continue#下一项
            if 状态['kind']=='settled' or (状态['kind']=='open' and not 关闭开放()):#结算或关失败
                无效=True#失效
            if not 无效:#成功
                状态={'kind':'settled','turn':回合,'step':数据.get('step'),'by':'retry'}#重试结算
            continue#下一项
        if 类型=='step/end':#步骤结束
            if (数据.get('turn')!=回合 or 状态['kind']=='idle'
                or not _同尝试(状态,数据.get('turn'),数据.get('step'))):#非法
                无效=True#失效
                continue#下一项
            if 状态['kind']=='open' and not 关闭开放():#仍开放且关失败
                无效=True#失效
            if not 无效:#成功
                状态={'kind':'idle'}#回到 idle
    if 无效 or not 已见结束 or 状态['kind']!='idle':#不完整
        return None#不可披露
    return _聚合尝试(尝试列表)#聚合
