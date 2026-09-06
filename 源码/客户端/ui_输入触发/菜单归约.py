"""菜单归约纯核心。每源一组；按世代闸门结算；就绪且空的组自动关闭。

对齐上游 `ui-input-trigger/src/core/menu.ts`。公开面仅中文名。零 React / DOM / cordis。
"""

__all__=['菜单关闭','铺分组','菜单归约','精确匹配']#仅中文公开名

菜单关闭={'open':False,'hit':None,'generation':0,'groups':[],'highlight':None}#关闭静息态

def 铺分组(状态,源列表):#按源名铺 pending 组
    """外壳在新开菜单、派发 hit 之前走的一步。"""
    下一=dict(状态)#浅拷
    下一['groups']=[{'source':源,'status':'pending','items':[]} for 源 in 源列表]#替换名册
    下一['highlight']=None#清高亮
    return 下一#带着新 pending 名册

def _关闭(状态):#关菜单，保留世代
    """使在飞结算仍可丢弃。"""
    if 状态['open'] or 状态['hit'] is not None or len(状态['groups'])>0 or 状态['highlight'] is not None:#开着或有内容
        return {'open':False,'hit':None,'generation':状态['generation'],'groups':[],'highlight':None}#关但保留世代
    return 状态#已是关态则原引用

def _首高亮(组列表):#默认高亮
    """第一个非空就绪组的第一项，否则 None。"""
    for 组 in 组列表:#按组顺序
        if 组['status']=='ready' and len(组['items'])>0:#有项；length 语义
            return {'source':组['source'],'index':0}#取该组第一项
    return None#没有可高亮项

def _有效高亮(高亮,组列表):#校验高亮是否仍有效
    """高亮仍指向就绪项时原样返回，否则 None。"""
    if 高亮 is None:#无高亮
        return None#无
    组=next((x for x in 组列表 if x['source']==高亮['source']),None)#按源名找组
    if 组 is not None and 组['status']=='ready' and 高亮['index']<len(组['items']):#组就绪且下标未越界
        return 高亮#保留
    return None#失效

def _位置表(组列表):#就绪项位置表
    """按组顺序把就绪项展成 (source, index) 位置表。"""
    出=[]#累计位置
    for 组 in 组列表:#按组顺序
        if 组['status']!='ready':#未就绪则跳过
            continue#跳
        for 下标 in range(len(组['items'])):#该组每项
            出.append({'source':组['source'],'index':下标})#一个位置
    return 出#展平后的位置表

def _全就绪空(组列表):#是否全部就绪且空
    """自动关闭条件。"""
    return all(g['status']=='ready' and len(g['items'])==0 for g in 组列表)#每组 ready 且无候选

def 菜单归约(状态,事件):#按事件归约菜单
    """过期或空操作时返回同一引用语义（此处返回原 dict）。"""
    类型=事件['type']#事件类型
    if 类型=='hit':#命中：开新世代或关闭
        命中=事件['hit'] if 'hit' in 事件 else None#本次命中
        if 命中 is None:#空命中则关菜单
            return _关闭(状态)#关
        return {#按已铺名册开新世代
            'open':True,#打开菜单
            'hit':命中,#本次命中
            'generation':状态['generation']+1,#升世代
            'groups':[{'source':g['source'],'status':'pending','items':[]} for g in 状态['groups']],#重置 pending
            'highlight':None,#清高亮
        }#结束开菜单态
    if 类型=='source-settled':#某源结算候选
        if not 状态['open'] or 事件['generation']!=状态['generation']:#未开或世代过期
            return 状态#丢
        组列表=list(状态['groups'])#拷贝
        下标=next((i for i,g in enumerate(组列表) if g['source']==事件['source']),-1)#找组
        if 下标<0:#不在名册
            return 状态#丢
        项列表=list(事件['items'] if 'items' in 事件 and 事件['items'] is not None else [])#项
        组列表[下标]={'source':组列表[下标]['source'],'status':'ready','items':项列表}#命中组改 ready
        if _全就绪空(组列表):#全部就绪且空则自动关
            return _关闭(状态)#关
        高亮=_有效高亮(状态['highlight'],组列表)#保留
        if 高亮 is None:#失效则取首
            高亮=_首高亮(组列表)#取首
        下一=dict(状态)#浅拷
        下一['groups']=组列表#写入组
        下一['highlight']=高亮#写入高亮
        return 下一#下一态
    if 类型=='source-failed':#某源失败，静默摘组
        if not 状态['open'] or 事件['generation']!=状态['generation']:#未开或世代过期
            return 状态#丢
        if not any(g['source']==事件['source'] for g in 状态['groups']):#不在名册
            return 状态#丢
        组列表=[g for g in 状态['groups'] if g['source']!=事件['source']]#摘掉失败源
        if len(组列表)==0 or _全就绪空(组列表):#无组或全空则自动关；length 语义
            return _关闭(状态)#关
        高亮=_有效高亮(状态['highlight'],组列表)#保留
        if 高亮 is None:#失效则取首
            高亮=_首高亮(组列表)#取首
        下一=dict(状态)#浅拷
        下一['groups']=组列表#写入组
        下一['highlight']=高亮#写入高亮
        return 下一#下一态
    if 类型=='move':#在就绪项间移动高亮
        if not 状态['open']:#未开则忽略
            return 状态#原样
        位=_位置表(状态['groups'])#就绪项位置表
        if len(位)==0:#无可移动项；length 语义
            return 状态#原样
        高亮=状态['highlight']#当前高亮
        处=-1#高亮在表中的下标
        if 高亮 is not None:#有高亮
            处=next((i for i,p in enumerate(位) if p['source']==高亮['source'] and p['index']==高亮['index']),-1)#找
        方向=事件['dir'] if 'dir' in 事件 else 1#1 下 / -1 上
        if 处<0:#当前高亮不在就绪表
            下一位=位[0] if 方向==1 else 位[-1]#下移从头，上移从尾
        else:#环绕步进
            下一位=位[(处+方向+len(位))%len(位)]#环绕
        if 高亮 is not None and 下一位['source']==高亮['source'] and 下一位['index']==高亮['index']:#高亮未变
            return 状态#原引用
        下一=dict(状态)#浅拷
        下一['highlight']=下一位#写入新高亮
        return 下一#下一态
    if 类型=='close':#显式关闭
        return _关闭(状态)#关菜单，保留世代
    return 状态#未知事件原样

def 精确匹配(组列表,源,名):#按源与精确名取候选
    """组缺席、未就绪或没有该名时为 None。"""
    组=next((g for g in 组列表 if g['source']==源),None)#按源名找组
    if 组 is None or 组['status']!='ready':#缺组或未就绪
        return None#无
    for 项 in 组['items']:#精确匹配名字
        if 项['name']==名:#命中
            return 项#候选
    return None#否则 None
