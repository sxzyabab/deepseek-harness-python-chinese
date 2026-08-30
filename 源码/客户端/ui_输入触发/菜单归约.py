"""菜单归约纯核心。每源一组；按世代闸门结算；就绪且空的组自动关闭。

对齐上游 `ui-input-trigger/src/core/menu.ts`。公开面仅中文名。零 React / DOM / cordis。
"""

__all__=['菜单关闭','铺分组','菜单归约','精确匹配']#仅中文公开名

菜单关闭={'open':False,'hit':None,'generation':0,'groups':[],'highlight':None}#关闭静息态

def 铺分组(状态,源们):#按源名铺 pending 组
    """外壳在新开菜单、派发 hit 之前走的一步。"""
    下一=dict(状态)#浅拷
    下一['groups']=[{'source':源,'status':'pending','items':[]} for 源 in 源们]#替换名册
    下一['highlight']=None#清高亮
    return 下一#带着新 pending 名册

def _关闭(状态):#关菜单，保留世代
    """使在飞结算仍可丢弃。"""
    if 状态.get('open') or 状态.get('hit') is not None or 状态.get('groups') or 状态.get('highlight') is not None:#开着或有内容
        return {'open':False,'hit':None,'generation':状态.get('generation',0),'groups':[],'highlight':None}#关但保留世代
    return 状态#已是关态则原引用

def _首高亮(组们):#默认高亮
    """第一个非空就绪组的第一项，否则 None。"""
    for 组 in 组们:#按组顺序
        if 组.get('status')=='ready' and 组.get('items'):#有项
            return {'source':组['source'],'index':0}#取该组第一项
    return None#没有可高亮项

def _有效高亮(高亮,组们):#校验高亮是否仍有效
    """高亮仍指向就绪项时原样返回，否则 None。"""
    if not 高亮:#无高亮
        return None#无
    组=next((x for x in 组们 if x.get('source')==高亮.get('source')),None)#按源名找组
    if 组 and 组.get('status')=='ready' and 高亮.get('index',0)<len(组.get('items') or []):#组就绪且下标未越界
        return 高亮#保留
    return None#失效

def _位置表(组们):#就绪项位置表
    """按组顺序把就绪项展成 (source, index) 位置表。"""
    出=[]#累计位置
    for 组 in 组们:#按组顺序
        if 组.get('status')!='ready':#未就绪则跳过
            continue#跳
        for 下标 in range(len(组.get('items') or [])):#该组每项
            出.append({'source':组['source'],'index':下标})#一个位置
    return 出#展平后的位置表

def _全就绪空(组们):#是否全部就绪且空
    """自动关闭条件。"""
    return all(g.get('status')=='ready' and not g.get('items') for g in 组们)#每组 ready 且无候选

def 菜单归约(状态,事件):#按事件归约菜单
    """过期或空操作时返回同一引用语义（此处返回原 dict）。"""
    类型=事件.get('type') if isinstance(事件,dict) else None#事件类型
    if 类型=='hit':#命中：开新世代或关闭
        命中=事件.get('hit')#本次命中
        if 命中 is None:#空命中则关菜单
            return _关闭(状态)#关
        return {#按已铺名册开新世代
            'open':True,#打开菜单
            'hit':命中,#本次命中
            'generation':状态.get('generation',0)+1,#升世代
            'groups':[{'source':g['source'],'status':'pending','items':[]} for g in 状态.get('groups') or []],#重置 pending
            'highlight':None,#清高亮
        }#结束开菜单态
    if 类型=='source-settled':#某源结算候选
        if not 状态.get('open') or 事件.get('generation')!=状态.get('generation'):#未开或世代过期
            return 状态#丢
        组们=list(状态.get('groups') or [])#拷贝
        下标=next((i for i,g in enumerate(组们) if g.get('source')==事件.get('source')),-1)#找组
        if 下标<0:#不在名册
            return 状态#丢
        项们=list(事件.get('items') or [])#缺席当空列表
        组们[下标]={'source':组们[下标]['source'],'status':'ready','items':项们}#命中组改 ready
        if _全就绪空(组们):#全部就绪且空则自动关
            return _关闭(状态)#关
        高亮=_有效高亮(状态.get('highlight'),组们) or _首高亮(组们)#保留或取首
        下一=dict(状态)#浅拷
        下一['groups']=组们#写入组
        下一['highlight']=高亮#写入高亮
        return 下一#下一态
    if 类型=='source-failed':#某源失败，静默摘组
        if not 状态.get('open') or 事件.get('generation')!=状态.get('generation'):#未开或世代过期
            return 状态#丢
        if not any(g.get('source')==事件.get('source') for g in 状态.get('groups') or []):#不在名册
            return 状态#丢
        组们=[g for g in 状态.get('groups') or [] if g.get('source')!=事件.get('source')]#摘掉失败源
        if not 组们 or _全就绪空(组们):#无组或全空则自动关
            return _关闭(状态)#关
        高亮=_有效高亮(状态.get('highlight'),组们) or _首高亮(组们)#保留或取首
        下一=dict(状态)#浅拷
        下一['groups']=组们#写入组
        下一['highlight']=高亮#写入高亮
        return 下一#下一态
    if 类型=='move':#在就绪项间移动高亮
        if not 状态.get('open'):#未开则忽略
            return 状态#原样
        位=_位置表(状态.get('groups') or [])#就绪项位置表
        if not 位:#无可移动项
            return 状态#原样
        高亮=状态.get('highlight')#当前高亮
        处=-1#高亮在表中的下标
        if 高亮:#有高亮
            处=next((i for i,p in enumerate(位) if p['source']==高亮.get('source') and p['index']==高亮.get('index')),-1)#找
        方向=事件.get('dir',1)#1 下 / -1 上
        if 处<0:#当前高亮不在就绪表
            下一位=位[0] if 方向==1 else 位[-1]#下移从头，上移从尾
        else:#环绕步进
            下一位=位[(处+方向+len(位))%len(位)]#环绕
        if 高亮 and 下一位['source']==高亮.get('source') and 下一位['index']==高亮.get('index'):#高亮未变
            return 状态#原引用
        下一=dict(状态)#浅拷
        下一['highlight']=下一位#写入新高亮
        return 下一#下一态
    if 类型=='close':#显式关闭
        return _关闭(状态)#关菜单，保留世代
    return 状态#未知事件原样

def 精确匹配(组们,源,名):#按源与精确名取候选
    """组缺席、未就绪或没有该名时为 None。"""
    组=next((g for g in 组们 if g.get('source')==源),None)#按源名找组
    if not 组 or 组.get('status')!='ready':#缺组或未就绪
        return None#无
    for 项 in 组.get('items') or []:#精确匹配名字
        项名=项.get('name') if isinstance(项,dict) else getattr(项,'name',None)#名
        if 项名==名:#命中
            return 项#候选
    return None#否则 None
