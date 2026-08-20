# 依赖未迁：@deepseek-ai/dsh-session/types 的 SessionEvent；约定侧 ConversationLocation/TurnLocation/StepLocation 等仅部分落在 约定/会话约定.py
"""会话拥有的回合/步骤时间线与事件到位置的索引。

对齐上游 `runtime/src/client/sessions/conversation-location-index.ts`。公开面仅中文名。
"""

__all__=['对话位置数据变更','对话位置索引']#仅中文公开名

会话位置={'kind':'session'}#无回合亲和的会话级位置
未解析位置={'kind':'unresolved'}#有回合号但时间线尚未收录

def 取字段(对象,键,缺省=None):#读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

def 是安全非负整数(值):#对齐 Number.isSafeInteger 且 >=0
    """判断是否为可安全用作回合/步骤号的非负整数。"""
    if isinstance(值,bool):#布尔不是序号
        return False#拒绝
    if isinstance(值,int):#整数
        return 值>=0 and 值<=9007199254740991#安全范围
    if isinstance(值,float) and 值.is_integer():#整值浮点
        return 值>=0 and 值<=9007199254740991#安全范围
    return False#其它类型

def 读载荷位(数据,键):#读载荷字段并区分缺席
    """返回 (是否出现, 值)；缺席对齐 JS undefined，出现且为 None 对齐 null。"""
    if 数据 is None:#无载荷
        return False,None#缺席
    if isinstance(数据,dict):#映射
        if 键 not in 数据:#缺键
            return False,None#缺席
        return True,数据[键]#出现
    if not hasattr(数据,键):#无属性
        return False,None#缺席
    return True,getattr(数据,键)#出现

def 载荷坐标(事件):#从载荷读坐标
    """从事件载荷读 turn/step；turn 为 null 表示显式会话级。"""
    数据=取字段(事件,'data')#载荷
    有回合,回合原=读载荷位(数据,'turn')#回合字段
    有步骤,步骤原=读载荷位(数据,'step')#步骤字段
    if 有回合 and 回合原 is None:#显式 null → 会话级
        return {'session':True}#会话级
    结果={}#待填
    if 有回合 and 是安全非负整数(回合原):#合法非负整数回合
        结果['turn']=int(回合原)#采用
    if 有步骤 and 是安全非负整数(步骤原):#合法非负整数步骤
        结果['step']=int(步骤原)#采用
    return 结果#只带有值的字段

def 同引用列表(左,右):#逐项引用相等
    """两列表长度相同且每项同一对象。"""
    if len(左)!=len(右):#长度不同
        return False#不等
    for 下标,值 in enumerate(左):#逐项
        if 值 is not 右[下标]:#引用不同
            return False#不等
    return True#全同

def 同步骤(左,右):#步骤位置引用可复用
    """旧步骤与新步骤边界、状态、数据仓库是否可复用。"""
    if 左 is None:#旧值不存在
        return False#不可复用
    return (左.get('start') is 右.get('start')#开始同一
        and 左.get('end') is 右.get('end')#结束同一
        and 左.get('status')==右.get('status')#状态同
        and 左.get('data') is 右.get('data'))#数据仓库身份

def 同回合(左,右):#回合位置引用可复用
    """旧回合与新回合边界、状态、数据仓库与步骤列表是否可复用。"""
    if 左 is None:#旧值不存在
        return False#不可复用
    return (左.get('start') is 右.get('start')#开始同一
        and 左.get('end') is 右.get('end')#结束同一
        and 左.get('status')==右.get('status')#状态同
        and 左.get('data') is 右.get('data')#数据仓库身份
        and 同引用列表(左.get('steps') or [],右.get('steps') or []))#步骤列表

def 同位置(左,右):#解析位置是否同指
    """两侧位置是否同一种类且同一对象载荷。"""
    if 左 is None or 右 is None or 取字段(左,'kind')!=取字段(右,'kind'):#缺一方或种类不同
        return 左 is 右#仅同为 None 时 True
    种类=取字段(左,'kind')#种类
    if 种类=='session' or 种类=='unresolved':#无载荷单例
        return True#种类相同即同
    if 种类=='turn':#回合级
        return 取字段(左,'turn') is 取字段(右,'turn')#同一回合对象
    return (取字段(左,'turn') is 取字段(右,'turn')#同一回合对象
        and 取字段(左,'step') is 取字段(右,'step'))#同一步骤对象

def 步骤数据键(回合,步骤):#步骤仓库键
    """拼 `turn:step` 仓库键。"""
    return str(回合)+':'+str(步骤)#回合:步骤

def 要求步骤(数据):#步骤发布必须带 step
    """从步骤级位置数据取出步骤号；缺则抛错。"""
    if 取字段(数据,'kind')=='step' and 取字段(数据,'step') is not None:#合法步骤号
        return 取字段(数据,'step')#返回
    raise Exception('conversation Step data "'+str(取字段(数据,'key'))+'" requires a step')#缺步骤

class 对话位置数据变更:#位置数据变更
    """一个上下文的前一次与下一次位置数据发布。"""

    def __init__(自身,owner,previous,next):#铸造一次变更
        """@param owner - 占用者上下文键。
        @param previous - 变更前；无发布为 None。
        @param next - 变更后；无发布为 None。
        """
        自身.owner=owner#占用者上下文键
        自身.previous=previous#变更前
        自身.next=next#变更后

class 可变位置数据仓库:#可变位置数据仓库
    """键 → 占用者与值；单占用者写入。"""

    def __init__(自身):#空仓库
        """空条目表。"""
        自身._条目={}#键 → {owner,value}

    def 取(自身,键):#按键读值
        """@param 键 - 业务键。
        @returns 已发布值；没有则为 None。
        """
        当前=自身._条目.get(键)#当前占用
        if 当前 is None:#空槽
            return None#没有
        return 当前['value']#已发布值

    def 移除(自身,占用者,键):#仅占用者可删
        """@param 占用者 - 占用者上下文键。
        @param 键 - 业务键。
        @returns 确有删除则为 True。
        """
        当前=自身._条目.get(键)#当前占用
        if 当前 is None or 当前['owner']!=占用者:#非占用者或空槽
            return False#未删
        del 自身._条目[键]#删掉
        return True#确有删除

    def 设(自身,占用者,键,值):#占用者写入
        """@param 占用者 - 占用者上下文键。
        @param 键 - 业务键。
        @param 值 - 已发布值。
        @returns 确有变化则为 True。
        """
        当前=自身._条目.get(键)#当前占用
        if 当前 is not None and 当前['owner']!=占用者:#键已被别人占用
            raise Exception('conversation Location data "'+键+'" is already owned by '+当前['owner'])#单占用者
        if 当前 is not None and 当前['value'] is 值:#引用未变
            return False#无变化
        自身._条目[键]={'owner':占用者,'value':值}#写入
        return True#确有变化

    def 替换(自身,条目们):#整表替换
        """@param 条目们 - 新表（键 → {owner,value}）。
        @returns 是否换过。
        """
        变化=len(自身._条目)!=len(条目们)#长度先比
        if not 变化:#长度相同再逐条
            for 键,值 in 条目们.items():#新表每一条
                当前=自身._条目.get(键)#旧占用
                if 当前 is None or 当前['owner']!=值['owner'] or 当前['value'] is not 值['value']:#占用者或值变了
                    变化=True#需要换表
                    break#不必再比
        if 变化:#确需换
            自身._条目=dict(条目们)#换新表
        return 变化#是否换过

class 对话位置索引:#位置索引
    """会话拥有的回合/步骤时间线与事件到位置的索引。"""

    def __init__(自身):#空索引
        """坐标、位置、回合成员、时间线与数据仓库。"""
        自身._坐标={}#seq → 坐标
        自身._位置={}#seq → 解析位置
        自身._回合序号们={}#回合号 → 所属 seq 集合
        自身._时间线={'turnOrder':[],'turns':{}}#引用稳定的时间线
        自身._回合数据仓库={}#回合号 → 可变仓库
        自身._步骤数据仓库={}#`turn:step` → 可变仓库
        自身._当前回合=None#扫描游标：当前回合
        自身._当前步骤=None#扫描游标：当前步骤

    def 快照(自身):#读时间线
        """返回当前引用稳定的时间线。

        @returns 当前时间线快照。
        """
        return 自身._时间线#未变则同一引用

    def 替换数据(自身,条目们):#整表替换位置数据
        """替换全部定义拥有的位置值，同时保持读者身份。

        @param 条目们 - 定义拥有的位置值的完整当前集（含 owner 与 data）。
        @returns 是否有已发布位置数据变化。
        """
        回合桶={}#回合号 → 键值
        步骤桶={}#步骤键 → 键值
        for 条目 in 条目们:#按作用域分桶
            占用者=取字段(条目,'owner')#占用者
            数据=取字段(条目,'data')#位置数据
            if 取字段(数据,'kind')=='turn':#回合级
                值表=回合桶.get(取字段(数据,'turn'))#该回合已有
                if 值表 is None:#空表
                    值表={}#新建
            else:#步骤级
                值表=步骤桶.get(步骤数据键(取字段(数据,'turn'),要求步骤(数据)))#该步骤已有
                if 值表 is None:#空表
                    值表={}#新建
            当前=值表.get(取字段(数据,'key'))#同键已有占用
            if 当前 is not None and 当前['owner']!=占用者:#键已被别人占用
                raise Exception('conversation Location data "'+str(取字段(数据,'key'))+'" is already owned by '+当前['owner'])#单占用者
            值表[取字段(数据,'key')]={'owner':占用者,'value':取字段(数据,'value')}#写入本占用者
            if 取字段(数据,'kind')=='turn':#回写回合桶
                回合桶[取字段(数据,'turn')]=值表#回写
            else:#回写步骤桶
                步骤桶[步骤数据键(取字段(数据,'turn'),要求步骤(数据))]=值表#回写
        变化=False#是否有仓库变过
        for 回合 in set(list(自身._回合数据仓库.keys())+list(回合桶.keys())):#旧有与新有的回合
            变化=自身._可变回合数据(回合).替换(回合桶.get(回合) or {}) or 变化#缺则空表
        for 步骤键 in set(list(自身._步骤数据仓库.keys())+list(步骤桶.keys())):#旧有与新有的步骤
            变化=自身._可变步骤数据(步骤键).替换(步骤桶.get(步骤键) or {}) or 变化#缺则空表
        return 变化#是否有数据变化

    def 应用数据(自身,变更们):#增量应用位置数据
        """应用已变上下文的发布，不重建回合/步骤成员关系。

        @param 变更们 - 已发布上下文的增量删除与替换。
        @returns 是否有已发布位置数据变化。
        """
        变化=False#是否有仓库变过
        for 变更 in 变更们:#先删旧
            先前=取字段(变更,'previous')#变更前
            if 先前 is None:#原先无发布
                continue#跳过
            变化=自身._仓库于(先前).移除(取字段(变更,'owner'),取字段(先前,'key')) or 变化#占用者删旧键
        for 变更 in 变更们:#再写新
            随后=取字段(变更,'next')#变更后
            if 随后 is None:#现在无发布
                continue#跳过
            变化=自身._仓库于(随后).设(取字段(变更,'owner'),取字段(随后,'key'),取字段(随后,'value')) or 变化#占用者写新值
        return 变化#是否有数据变化

    def 位置于(自身,事件):#按 seq 读位置
        """解析一条事件的最新位置。

        @param 事件 - 已摄入本索引的事件。
        @returns 当前位置；无回合/步骤亲和时回退到会话级。
        """
        return 自身._位置.get(取字段(事件,'seq'),会话位置)#未索引则会话级

    def 重建(自身,条目们):#全窗口重建
        """在 replace/prepend 或边界追加之后重建时间线事实。

        @param 条目们 - 升序 seq 的完整当前窗口。
        @returns 已解析位置发生变化的 seq 集合。
        """
        旧位置=自身._位置#旧位置表，用于 diff
        回合草稿们={}#回合号 → 草稿
        坐标们={}#本趟解析出的坐标
        当前回合=None#扫描游标：当前回合
        当前步骤=None#扫描游标：当前步骤

        def 取回合草稿(回合,序号):#取或建回合草稿
            草稿=回合草稿们.get(回合)#已有草稿
            if 草稿 is None:#首次见到该回合
                草稿={'turn':回合,'firstSeq':序号,'steps':{},'start':None,'end':None}#新建
                回合草稿们[回合]=草稿#写入
            else:#已有则把最早 seq 往前推
                草稿['firstSeq']=min(草稿['firstSeq'],序号)#窗口内最早
            return 草稿#该回合草稿

        def 取步骤草稿(回合,步骤,序号):#取或建步骤草稿
            属主=取回合草稿(回合,序号)#所属回合
            草稿=属主['steps'].get(步骤)#已有步骤
            if 草稿 is None:#首次见到该步骤
                草稿={'turn':回合,'step':步骤,'firstSeq':序号,'start':None,'end':None}#新建
                属主['steps'][步骤]=草稿#写入回合
            else:#已有则把最早 seq 往前推
                草稿['firstSeq']=min(草稿['firstSeq'],序号)#窗口内最早
            return 草稿#该步骤草稿

        for 条目 in 条目们:#按窗口顺序扫
            事件=取字段(条目,'event')#原始事件
            显式=载荷坐标(事件)#载荷显式坐标
            类型=取字段(事件,'type')#事件类型
            数据=取字段(事件,'data')#事件载荷
            if 类型=='turn/start':#回合开始
                当前回合=取字段(数据,'turn')#游标进该回合
                当前步骤=None#步骤清掉
            if 类型=='step/start':#步骤开始
                当前回合=取字段(数据,'turn')#游标进该回合
                当前步骤=取字段(数据,'step')#游标进该步骤
            if 取字段(显式,'session') is not True and 取字段(显式,'turn') is not None:#载荷给出回合且非会话级
                if 当前回合!=取字段(显式,'turn'):#换回合
                    当前步骤=None#步骤作废
                当前回合=取字段(显式,'turn')#采用显式回合
                if 取字段(显式,'step') is not None:#有显式步骤
                    当前步骤=取字段(显式,'step')#采用
            if 取字段(显式,'session') is True:#会话级无回合
                回合=None#无回合
            else:#显式或游标
                回合=取字段(显式,'turn') if 取字段(显式,'turn') is not None else 当前回合#显式或游标
            if 取字段(显式,'session') is True or 类型=='turn/start' or 类型=='turn/end':#会话级与回合边界无步骤
                步骤=None#不带步骤
            else:#显式或同回合游标
                步骤=取字段(显式,'step') if 取字段(显式,'step') is not None else (当前步骤 if 回合==当前回合 else None)#显式或同回合游标
            坐标={}#本事件坐标
            if 回合 is not None:#有回合才带
                坐标['turn']=回合#写入回合
            if 回合 is not None and 步骤 is not None:#有回合且有步骤才带
                坐标['step']=步骤#写入步骤
            坐标们[取字段(事件,'seq')]=坐标#记下
            if 回合 is not None:#计入回合成员
                取回合草稿(回合,取字段(事件,'seq'))#建草稿
            if 回合 is not None and 步骤 is not None:#计入步骤成员
                取步骤草稿(回合,步骤,取字段(事件,'seq'))#建草稿
            if 类型=='turn/start':#回合开始边界
                取回合草稿(取字段(数据,'turn'),取字段(事件,'seq'))['start']=事件#挂开始事件
            elif 类型=='turn/end':#回合结束边界
                取回合草稿(取字段(数据,'turn'),取字段(事件,'seq'))['end']=事件#挂结束事件
            elif 类型=='step/start':#步骤开始边界
                取步骤草稿(取字段(数据,'turn'),取字段(数据,'step'),取字段(事件,'seq'))['start']=事件#挂开始事件
            elif 类型=='step/end':#步骤结束边界
                取步骤草稿(取字段(数据,'turn'),取字段(数据,'step'),取字段(事件,'seq'))['end']=事件#挂结束事件
            if 类型=='step/end' and 当前回合==取字段(数据,'turn') and 当前步骤==取字段(数据,'step'):#结束当前步骤
                当前步骤=None#游标离开步骤
            if 类型=='turn/end' and 当前回合==取字段(数据,'turn'):#结束当前回合
                当前回合=None#游标离开回合
                当前步骤=None#步骤一并清

        旧回合表=自身._时间线['turns']#旧回合表，用于复用引用
        新回合表={}#新回合表
        有序草稿=sorted(回合草稿们.values(),key=lambda 项:项['firstSeq'])#按首次出现排序
        for 草稿 in 有序草稿:#每个回合草稿
            旧回合=旧回合表.get(草稿['turn'])#旧回合位置
            旧步骤表={}#旧步骤号 → 位置
            if 旧回合 is not None:#有旧回合
                for 步骤位 in 旧回合.get('steps') or []:#旧步骤
                    旧步骤表[步骤位['step']]=步骤位#索引
            步骤列表=[]#本回合步骤
            for 候选 in sorted(草稿['steps'].values(),key=lambda 项:项['firstSeq']):#按首次出现排序
                if 候选['end'] is not None:#已有结束
                    状态='closed'#已关闭
                elif 候选['start'] is None:#无开始
                    状态='unknown'#未知
                else:#有开始无结束
                    状态='open'#开着
                新值={#新步骤值
                    'turn':候选['turn'],#所属回合
                    'step':候选['step'],#步骤号
                    'start':候选['start'],#开始事件
                    'end':候选['end'],#结束事件
                    'status':状态,#状态
                    'data':自身._步骤数据(候选['turn'],候选['step']),#步骤数据仓库
                }#结束步骤值
                旧步骤=旧步骤表.get(候选['step'])#旧步骤
                步骤列表.append(旧步骤 if 同步骤(旧步骤,新值) else 新值)#能复用则复用
            if 草稿['end'] is not None:#有结束
                回合状态='closed'#已关闭
            elif 草稿['start'] is None:#无开始
                回合状态='unknown'#未知
            else:#有开始无结束
                回合状态='open'#开着
            新回合值={#新回合值
                'turn':草稿['turn'],#回合号
                'start':草稿['start'],#开始事件
                'end':草稿['end'],#结束事件
                'status':回合状态,#状态
                'steps':步骤列表,#步骤列表
                'data':自身._回合数据(草稿['turn']),#回合数据仓库
            }#结束回合值
            新回合表[草稿['turn']]=旧回合 if 同回合(旧回合,新回合值) else 新回合值#能复用则复用

        新顺序=[草稿['turn'] for 草稿 in 有序草稿]#新回合顺序
        旧顺序=自身._时间线['turnOrder']#旧顺序
        if len(旧顺序)==len(新顺序) and all(旧顺序[下标]==新顺序[下标] for 下标 in range(len(新顺序))):#长度与逐项相同
            回合顺序=旧顺序#复用旧顺序数组
        else:#否则换新
            回合顺序=新顺序#新顺序
        同表=len(旧回合表)==len(新回合表)#回合表大小先比
        if 同表:#大小相同再逐条
            for 回合号,值 in 新回合表.items():#新表每一回合
                if 旧回合表.get(回合号) is not 值:#引用不同
                    同表=False#整表要换
                    break#不必再比
        if 同表 and 回合顺序 is 自身._时间线['turnOrder']:#表与顺序都没换
            自身._时间线=自身._时间线#复用整份时间线
        else:#否则发新快照
            自身._时间线={'turnOrder':回合顺序,'turns':新回合表}#新快照
        自身._坐标=坐标们#换成本趟坐标
        自身._位置={}#位置表重填
        自身._回合序号们={}#回合成员重填
        for 条目 in 条目们:#按窗口填位置
            事件=取字段(条目,'event')#事件
            序号=取字段(事件,'seq')#seq
            坐标=自身._坐标.get(序号)#本事件坐标
            if 坐标 is not None and 坐标.get('turn') is not None:#有回合
                自身._索引回合序号(坐标['turn'],序号)#计入回合成员
            自身._位置[序号]=自身._解析(序号)#解析并写入
        自身._当前回合=当前回合#留下扫描游标
        自身._当前步骤=当前步骤#留下扫描游标
        变化集=set()#位置引用变过的 seq
        for 条目 in 条目们:#与旧表 diff
            事件=取字段(条目,'event')#事件
            序号=取字段(事件,'seq')#seq
            if not 同位置(旧位置.get(序号),自身._位置.get(序号)):#位置不同指
                变化集.add(序号)#记下来
        return 变化集#变过的 seq

    def 追加边界(自身,事件):#追加边界
        """追加一条回合/步骤边界，只重访所属回合。

        @param 事件 - 连续尾部的边界事件。
        @returns 不可变位置引用发生变化的 seq 集合。
        """
        类型=取字段(事件,'type')#事件类型
        if 类型 not in ('turn/start','turn/end','step/start','step/end'):#不是边界
            raise Exception('conversation Location boundary expected, received '+str(类型))#调用方用错
        显式=载荷坐标(事件)#载荷显式坐标
        数据=取字段(事件,'data')#事件载荷
        if 类型=='turn/start':#回合开始
            自身._当前回合=取字段(数据,'turn')#游标进该回合
            自身._当前步骤=None#步骤清掉
        elif 类型=='step/start':#步骤开始
            自身._当前回合=取字段(数据,'turn')#游标进该回合
            自身._当前步骤=取字段(数据,'step')#游标进该步骤
        if 取字段(显式,'turn') is not None:#载荷给出回合
            if 自身._当前回合!=取字段(显式,'turn'):#换回合
                自身._当前步骤=None#步骤作废
            自身._当前回合=取字段(显式,'turn')#采用显式回合
            if 取字段(显式,'step') is not None:#有显式步骤
                自身._当前步骤=取字段(显式,'step')#采用
        回合号=取字段(显式,'turn') if 取字段(显式,'turn') is not None else 自身._当前回合#显式或游标
        if 回合号 is None:#边界必须有回合
            raise Exception('conversation boundary '+str(类型)+' has no turn')#无回合
        if 类型=='turn/start' or 类型=='turn/end':#回合边界无步骤
            步骤号=None#不带步骤
        else:#显式或同回合游标
            步骤号=取字段(显式,'step') if 取字段(显式,'step') is not None else (自身._当前步骤 if 回合号==自身._当前回合 else None)#显式或同回合游标
        坐标={'turn':回合号}#本事件坐标
        if 步骤号 is not None:#有步骤才带
            坐标['step']=步骤号#写入步骤
        自身._坐标[取字段(事件,'seq')]=坐标#记下
        自身._索引回合序号(回合号,取字段(事件,'seq'))#计入回合成员
        旧回合=自身._时间线['turns'].get(回合号)#旧回合位置
        步骤们=list(旧回合['steps']) if 旧回合 is not None else []#旧步骤列表或空
        if 类型=='step/start' or 类型=='step/end':#步骤边界才改步骤列表
            号码=取字段(数据,'step')#本步骤号
            旧步骤=None#旧步骤位置
            for 候选 in 步骤们:#查找
                if 候选['step']==号码:#找到
                    旧步骤=候选#记下
                    break#停
            候选步骤={#新步骤值
                'turn':回合号,#所属回合
                'step':号码,#步骤号
                'start':事件 if 类型=='step/start' else (旧步骤.get('start') if 旧步骤 is not None else None),#开始
                'end':事件 if 类型=='step/end' else (旧步骤.get('end') if 旧步骤 is not None else None),#结束
                'status':'closed' if (类型=='step/end' or (旧步骤 is not None and 旧步骤.get('end') is not None)) else 'open',#有结束则关闭
                'data':自身._步骤数据(回合号,号码),#步骤数据仓库
            }#结束步骤值
            下一步骤=旧步骤 if 同步骤(旧步骤,候选步骤) else 候选步骤#能复用则复用
            下标=-1#旧列表下标
            for 位置,步骤位 in enumerate(步骤们):#找下标
                if 步骤位['step']==号码:#找到
                    下标=位置#记下
                    break#停
            if 下标<0:#尚未有该步骤
                步骤们=步骤们+[下一步骤]#追加
            else:#替换该下标
                步骤们=[下一步骤 if 位置==下标 else 步骤位 for 位置,步骤位 in enumerate(步骤们)]#替换
        if 类型=='turn/end' or (旧回合 is not None and 旧回合.get('end') is not None):#有结束
            回合状态='closed'#已关闭
        elif 类型=='turn/start' or (旧回合 is not None and 旧回合.get('start') is not None):#有开始
            回合状态='open'#开着
        else:#否则未知
            回合状态='unknown'#未知
        候选回合={#新回合值
            'turn':回合号,#回合号
            'start':事件 if 类型=='turn/start' else (旧回合.get('start') if 旧回合 is not None else None),#开始
            'end':事件 if 类型=='turn/end' else (旧回合.get('end') if 旧回合 is not None else None),#结束
            'status':回合状态,#状态
            'steps':步骤们,#步骤列表
            'data':自身._回合数据(回合号),#回合数据仓库
        }#结束回合值
        回合=旧回合 if 同回合(旧回合,候选回合) else 候选回合#能复用则复用
        回合表=dict(自身._时间线['turns'])#浅拷回合表
        回合表[回合号]=回合#写入本回合
        if 旧回合 is None:#新回合
            回合顺序=list(自身._时间线['turnOrder'])+[回合号]#追加到顺序末尾
        else:#否则复用顺序数组
            回合顺序=自身._时间线['turnOrder']#复用
        自身._时间线={'turnOrder':回合顺序,'turns':回合表}#发新时间线快照
        变化集=set()#本回合里位置变过的 seq
        for 序号 in 自身._回合序号们.get(回合号) or []:#重访所属回合全部 seq
            先前=自身._位置.get(序号)#旧位置
            随后=自身._解析(序号)#按新时间线解析
            自身._位置[序号]=随后#写入
            if not 同位置(先前,随后):#引用变了
                变化集.add(序号)#记下
        if 类型=='step/end' and 自身._当前回合==取字段(数据,'turn') and 自身._当前步骤==取字段(数据,'step'):#结束当前步骤
            自身._当前步骤=None#游标离开步骤
        if 类型=='turn/end' and 自身._当前回合==取字段(数据,'turn'):#结束当前回合
            自身._当前回合=None#游标离开回合
            自身._当前步骤=None#步骤一并清
        return 变化集#变过的 seq

    def 追加非边界(自身,事件):#追加非边界
        """索引一条非边界尾事件，不重扫窗口。

        @param 事件 - 连续追加的事件。
        """
        显式=载荷坐标(事件)#载荷显式坐标
        if 取字段(显式,'session') is True:#显式会话级
            自身._坐标[取字段(事件,'seq')]={}#无回合无步骤
            自身._位置[取字段(事件,'seq')]=会话位置#会话级位置
            return#不必进回合索引
        if 取字段(显式,'turn') is not None:#载荷给出回合
            if 自身._当前回合!=取字段(显式,'turn'):#换回合
                自身._当前步骤=None#步骤作废
            自身._当前回合=取字段(显式,'turn')#采用显式回合
            if 取字段(显式,'step') is not None:#有显式步骤
                自身._当前步骤=取字段(显式,'step')#采用
        回合=取字段(显式,'turn') if 取字段(显式,'turn') is not None else 自身._当前回合#显式或游标
        步骤=取字段(显式,'step') if 取字段(显式,'step') is not None else (自身._当前步骤 if 回合==自身._当前回合 else None)#显式或同回合游标
        坐标={}#本事件坐标
        if 回合 is not None:#有回合才带
            坐标['turn']=回合#写入
        if 回合 is not None and 步骤 is not None:#有回合且有步骤才带
            坐标['step']=步骤#写入
        自身._坐标[取字段(事件,'seq')]=坐标#记下
        if 回合 is not None:#计入回合成员
            自身._索引回合序号(回合,取字段(事件,'seq'))#加入
        自身._位置[取字段(事件,'seq')]=自身._解析(取字段(事件,'seq'))#解析并写入

    def _索引回合序号(自身,回合,序号):#把 seq 记进回合成员
        """把序号记进回合成员集。"""
        当前=自身._回合序号们.get(回合)#已有
        if 当前 is None:#空集
            当前=set()#新建
        当前.add(序号)#加入
        自身._回合序号们[回合]=当前#写回

    def _回合数据(自身,回合):#回合数据仓库（对外）
        """取回合数据仓库（与可变仓库同一对象）。"""
        return 自身._可变回合数据(回合)#同一对象

    def _步骤数据(自身,回合,步骤):#步骤数据仓库（对外）
        """取步骤数据仓库（与可变仓库同一对象）。"""
        return 自身._可变步骤数据(步骤数据键(回合,步骤))#同一对象

    def _可变回合数据(自身,回合):#取或建回合仓库
        """取或建回合可变仓库。"""
        当前=自身._回合数据仓库.get(回合)#已有
        if 当前 is None:#新建
            当前=可变位置数据仓库()#空仓库
            自身._回合数据仓库[回合]=当前#挂上
        return 当前#可变仓库

    def _可变步骤数据(自身,键):#取或建步骤仓库
        """取或建步骤可变仓库。"""
        当前=自身._步骤数据仓库.get(键)#已有
        if 当前 is None:#新建
            当前=可变位置数据仓库()#空仓库
            自身._步骤数据仓库[键]=当前#挂上
        return 当前#可变仓库

    def _仓库于(自身,数据):#按发布选仓库
        """按位置数据发布选可变仓库。"""
        if 取字段(数据,'kind')=='turn':#回合级
            return 自身._可变回合数据(取字段(数据,'turn'))#回合仓库
        return 自身._可变步骤数据(步骤数据键(取字段(数据,'turn'),要求步骤(数据)))#步骤仓库

    def _解析(自身,序号):#由坐标解析位置
        """由坐标解析位置。"""
        坐标=自身._坐标.get(序号)#该 seq 坐标
        if 坐标 is None or 坐标.get('turn') is None:#无回合 → 会话级
            return 会话位置#会话级
        回合=自身._时间线['turns'].get(坐标['turn'])#时间线上的回合
        if 回合 is None:#有号但尚未收录
            return 未解析位置#未解析
        if 坐标.get('step') is None:#无步骤 → 回合级
            return {'kind':'turn','turn':回合}#回合级
        步骤=None#该步骤
        for 候选 in 回合.get('steps') or []:#查找
            if 候选['step']==坐标['step']:#找到
                步骤=候选#记下
                break#停
        if 步骤 is None:#找不到步骤则停在回合
            return {'kind':'turn','turn':回合}#回合级
        return {'kind':'step','turn':回合,'step':步骤}#步骤级
