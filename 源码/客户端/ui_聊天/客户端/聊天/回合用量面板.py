"""回合用量与时间 IconActions 胶囊面板。

对齐上游 `ui-chat/src/client/chat/TurnUsagePanel.tsx`。公开面仅中文名。
"""
from .消息铬 import 格式化延迟秒,格式化运行时长,格式化每秒令牌#时长与吞吐
from .令牌格式 import 格式化缓存命中百分比,格式化精确令牌,格式化令牌#token 格式

__all__=['回合用量面板','回合时间面板']#仅中文公开名

面板边距=12#视口边距
面板间隙=8#触发器间隙

def 取字段(对象,键,缺省=None):#读字段
    """映射或属性。"""
    if 对象 is None:#空
        return 缺省#缺
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

def 紧凑计数(值,翻译):#紧凑计数
    """message.turnUsage.count。"""
    return 翻译('message.turnUsage.count',{'count':格式化令牌(值,翻译)})#紧凑

def 精确计数(值,翻译):#精确计数
    """精确模板。"""
    return 翻译('message.turnUsage.count',{'count':格式化精确令牌(值,翻译)})#精确

class 回合用量面板:#用量胶囊
    """数据库胶囊 + 锚定对话框结构。"""

    def __init__(自身,属性=None):#构造
        """记下。"""
        自身.属性=属性 or {}#合成
        自身.打开=False#开合

    def 更新(自身,属性):#刷新
        """刷新。"""
        自身.属性=属性 or {}#新

    def 切换(自身):#开合
        """翻转。"""
        自身.打开=not 自身.打开#翻

    def 渲染(自身):#结构树
        """用量面板。"""
        属性=自身.属性#props
        用量=取字段(属性,'usage') or {}#用量
        翻译=取字段(属性,'t',lambda 键,_=None:键)#文案
        总量令牌=取字段(用量,'totalTokens') or 0#总量
        输出=取字段(用量,'outputTokens') or 0#输出
        缓存读=取字段(用量,'cacheReadTokens')#缓存读
        命中=None if 缓存读 is None else 格式化缓存命中百分比(缓存读,总量令牌-输出,1)#命中
        路由们=取字段(用量,'routes') or []#路由
        路由串=', '.join(f"{取字段(r,'provider')}/{取字段(r,'model')}" for r in 路由们)#串
        return {'type':'turn-usage-panel','open':自身.打开,'totalLabel':翻译('message.turnUsage.consumed',{'total':紧凑计数(总量令牌,翻译)}),'cacheHit':命中,'routes':路由串,'rows':[{'label':翻译('message.turnUsage.input'),'value':精确计数((取字段(用量,'uncachedInputTokens') or 0)+(取字段(用量,'cacheReadTokens') or 0)+(取字段(用量,'cacheWriteTokens') or 0),翻译)},{'label':翻译('message.turnUsage.output'),'value':精确计数(输出,翻译)}],'onToggle':自身.切换,'margin':面板边距,'gap':面板间隙,'cssModule':'回合用量面板.module.css'}#面板

    def __call__(自身,属性=None):#调用形
        """对齐。"""
        if 属性 is not None:#有
            自身.更新(属性)#刷
        return 自身.渲染()#渲

class 回合时间面板:#时钟胶囊
    """墙钟 + TTFT/吞吐详情。"""

    def __init__(自身,属性=None):#构造
        """记下。"""
        自身.属性=属性 or {}#合成
        自身.打开=False#开合

    def 更新(自身,属性):#刷新
        """刷新。"""
        自身.属性=属性 or {}#新

    def 切换(自身):#开合
        """翻转。"""
        自身.打开=not 自身.打开#翻

    def 渲染(自身):#结构树
        """时间面板。"""
        属性=自身.属性#props
        翻译=取字段(属性,'t',lambda 键,_=None:键)#文案
        运行毫秒=取字段(属性,'runMs') or 0#墙钟
        吞吐=取字段(属性,'tokensPerSecond')#吞吐
        首令=取字段(属性,'ttftMs')#TTFT
        行们=[{'label':翻译('message.turnTime.duration'),'value':格式化运行时长(运行毫秒,翻译)}]#行
        if 首令 is not None:#有 TTFT
            行们.append({'label':翻译('message.turnTime.ttft'),'value':格式化延迟秒(首令)})#TTFT
        if 吞吐 is not None:#有吞吐
            行们.append({'label':翻译('message.turnTime.throughput'),'value':格式化每秒令牌(吞吐)})#吞吐
        return {'type':'turn-time-panel','open':自身.打开,'label':格式化运行时长(运行毫秒,翻译),'rows':行们,'onToggle':自身.切换,'cssModule':'回合用量面板.module.css'}#面板

    def __call__(自身,属性=None):#调用形
        """对齐。"""
        if 属性 is not None:#有
            自身.更新(属性)#刷
        return 自身.渲染()#渲
