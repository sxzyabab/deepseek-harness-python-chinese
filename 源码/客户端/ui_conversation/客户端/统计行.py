"""会话环境读数带：回合/步/时长/吞吐/缓存/令牌。

对齐上游 `ui-conversation/src/client/chat/StatsLine.tsx`。公开面仅中文名。
"""
from .消息铬 import 格式化每秒令牌#吞吐数字
from .回合指标 import 助手步骤读数#步骤读数

__all__=['派生统计','格式化令牌','格式化时长','缓存命中百分','计费输入令牌','上下文占用','统计行']#仅中文公开名

def 取字段(对象,键,缺省=None):#读字段
    """映射或对象。"""
    if 对象 is None:#空
        return 缺省#缺
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

def 派生统计(节点们):#窗口折叠回退
    """无 sessionStats 投影时用。"""
    回合集=set()#回合
    步数=0#步
    模型毫秒=0#LLM
    工具毫秒=0#工具
    首令牌毫秒=0#TTFT 和
    首令牌步=0#TTFT 步数
    解码毫秒=0#解码
    解码令牌=0#产出
    for 节点 in (节点们 or []):#遍历
        种=取字段(节点,'kind')#kind
        if 种=='tool-result':#工具结果
            调用时=取字段(节点,'callTime')#callTime
            if 调用时 is not None:#有
                工具毫秒+=max(0,(取字段(节点,'time') or 0)-调用时)#墙钟
            continue#下
        if 种!='assistant':#非助手
            continue#跳
        回合集.add(取字段(节点,'turn'))#回合
        步数+=1#步
        计时=取字段(节点,'timing')#计时
        if 计时 is not None and 取字段(计时,'stepStartTime') is not None:#有步进
            模型毫秒+=max(0,(取字段(计时,'completedTime') or 0)-取字段(计时,'stepStartTime'))#LLM
        读数=助手步骤读数(节点)#读数
        if 读数['ttftMs'] is not None:#TTFT
            首令牌毫秒+=读数['ttftMs']#加
            首令牌步+=1#步
        if 读数['decodeMs'] is not None and 读数['outputTokens'] is not None:#吞吐样本
            解码毫秒+=读数['decodeMs']#加
            解码令牌+=读数['outputTokens']#加
    return {#统计
        'turns':len(回合集),'steps':步数,'llmMs':模型毫秒,'toolMs':工具毫秒,
        'ttftMs':首令牌毫秒,'ttftSteps':首令牌步,'decodeMs':解码毫秒,'decodeTokens':解码令牌,
    }#结束

def 格式化令牌(数):#紧凑令牌
    """517 / 12.2K / 1.2M。"""
    def 缩(值):#一位或整
        """百以上整。"""
        return str(round(值)) if 值>=100 else str(round(值*10)/10)#缩
    if 数<1000:#原样
        return str(数)#数
    if 数<1000000:#K
        return f'{缩(数/1000)}K'#K
    return f'{缩(数/1000000)}M'#M

def 格式化时长(毫秒):#紧凑时长
    """45.2s / 2m42s。"""
    秒=毫秒/1000#秒
    if 秒<60:#亚分
        return f'{round(秒*10)/10}s'#秒
    整=round(秒)#整秒
    return f'{整//60}m{整%60}s'#分秒

def 计费输入令牌(用量):#三桶和
    """uncached+cacheRead+cacheWrite。"""
    return (取字段(用量,'uncachedInputTokens') or 0)+(取字段(用量,'cacheReadTokens') or 0)+(取字段(用量,'cacheWriteTokens') or 0)#和

def 缓存命中百分(用量):#缓存命中
    """无输入则 None。"""
    分母=计费输入令牌(用量)#分母
    if 分母==0:#无
        return None#无
    return round((取字段(用量,'cacheReadTokens') or 0)/分母*100)#百分

def 上下文占用(压力):#占用读数
    """projectedTokens 优先；缺容量返回 None。"""
    if 压力 is None:#无
        return None#无
    已用=取字段(压力,'projectedTokens')#投影
    if 已用 is None:#回退样本
        已用=取字段(压力,'pressureTokens')#样本
    窗=取字段(压力,'contextWindow')#容量
    if 已用 is None or 窗 is None:#缺
        return None#无
    return {'percent':min(100,round(已用/窗*100)),'usedTokens':已用,'contextWindow':窗}#占用

class 统计行:#composer.dock 读数带
    """投影优先，窗口折叠回退。"""

    def __init__(自身,属性=None):#记下
        """记下 props。"""
        自身.属性=属性 or {}#合成

    def 更新(自身,属性):#刷新
        """刷新 props。"""
        自身.属性=属性 or {}#新

    def 渲染(自身):#结构
        """无组返回 None。"""
        属性=自身.属性#props
        翻译=取字段(属性,'t',lambda 键,**_:键)#文案
        用会话=取字段(属性,'useSession')#会话
        用投影=取字段(属性,'useProjection')#投影
        节点们=用会话(lambda s:取字段(取字段(取字段(s,'chat'),'legacy'),'nodes') or []) if callable(用会话) else []#节点
        用量=用投影('tokenUsage') if callable(用投影) else None#用量
        投影统计=用投影('sessionStats') if callable(用投影) else None#投影
        统计=投影统计 if 投影统计 is not None else 派生统计(节点们)#统计
        组们=[]#组
        if 取字段(统计,'steps',0)>0:#有步
            组们.append(翻译('stats.counts',{'turns':取字段(统计,'turns'),'steps':取字段(统计,'steps')}))#计数
            时长们=[]#时长
            if 取字段(统计,'llmMs',0)>0:#LLM
                时长们.append(翻译('stats.llm',{'duration':格式化时长(取字段(统计,'llmMs'))}))#LLM
            if 取字段(统计,'toolMs',0)>0:#工具
                时长们.append(翻译('stats.toolCall',{'duration':格式化时长(取字段(统计,'toolMs'))}))#工具
            if 时长们:#有
                组们.append(' · '.join(时长们))#时长组
            速们=[]#速
            首步=取字段(统计,'ttftSteps',0)#TTFT 步
            if 首步>0:#平均 TTFT
                速们.append(翻译('stats.ttftAverage',{'duration':格式化时长(取字段(统计,'ttftMs')/首步)}))#TTFT
            if 取字段(统计,'decodeMs',0)>0:#吞吐
                速们.append(翻译('stats.tokensPerSecond',{'throughput':格式化每秒令牌(取字段(统计,'decodeTokens')/(取字段(统计,'decodeMs')/1000))}))#吞吐
            if 速们:#有
                组们.append(' · '.join(速们))#速组
        if 用量 is not None and (计费输入令牌(用量)>0 or (取字段(用量,'outputTokens') or 0)>0):#计费
            命中=缓存命中百分(用量)#命中
            if 命中 is not None:#有
                组们.append(翻译('stats.cacheHit',{'percent':命中}))#缓存
            组们.append(翻译('stats.tokens',{'input':格式化令牌(计费输入令牌(用量)),'output':格式化令牌(取字段(用量,'outputTokens') or 0)}))#令牌
        if len(组们)==0:#空
            return None#不画
        return {'className':'root','groups':组们,'line':' | '.join(组们)}#行
