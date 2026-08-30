"""只读枚举耐久子智能体子体与后代树，直接来自活会话存储与可选会话持久化——无查询服务。"""
from typing import Literal,NotRequired,TypedDict#字面量、可选字段与结构类型
from ...依赖 import cordis#外部依赖胶水
from .错误 import 子智能体错误#导入子智能体错误

冷读并发上限=4#冷读并发上限
生命周期证人键=('version','id','createdAt','cwd','parentSession','seedLength','delegationDepth')#生命周期证人键

class 子智能体列举一次性子体(TypedDict):#列举结果的一次性子体臂
    kind:Literal['child']#子体条目
    id:str#耐久子会话 id
    activity:Literal['running','inactive']#存储快照活动
    hasChildren:bool#是否有耐久 origin:subagent 的直接后代
    mode:Literal['one-shot']#终态一次性子体
    label:NotRequired[str]#可选耐久创建标签

class 子智能体列举可续跑子体(TypedDict):#列举结果的可续跑子体臂
    kind:Literal['child']#子体条目
    id:str#耐久子会话 id
    activity:Literal['running','inactive']#存储快照活动
    hasChildren:bool#是否有耐久 origin:subagent 的直接后代
    mode:Literal['continuable']#可恢复对话
    label:str#耐久创建标签

class 子智能体列举诊断(TypedDict):#列举结果的诊断臂
    kind:Literal['diagnostic']#诊断条目
    id:str#候选的会话 id
    reason:Literal['corrupt','unsupported','unavailable']#候选没有 child 行的原因

子智能体列举条目=子智能体列举一次性子体|子智能体列举可续跑子体|子智能体列举诊断#listChildren 结果一条

class 子智能体后代列举一次性(子智能体列举一次性子体):#后代列举的一次性子体
    parentId:str#本候选在枚举树中的耐久直接父
    depth:int#相对所请求根的边距

class 子智能体后代列举可续跑(子智能体列举可续跑子体):#后代列举的可续跑子体
    parentId:str#本候选在枚举树中的耐久直接父
    depth:int#相对所请求根的边距

class 子智能体后代列举诊断(子智能体列举诊断):#后代列举的诊断
    parentId:str#本候选在枚举树中的耐久直接父
    depth:int#相对所请求根的边距

子智能体后代列举条目=子智能体后代列举一次性|子智能体后代列举可续跑|子智能体后代列举诊断#listDescendants 结果一条

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 解开(值):#承诺则等待否则原样
    """承诺则等待，否则原样返回。"""
    if 是否thenable(值):#可等待
        return 值.等待()#等待承诺
    return 值#同步值

def 信号已中止(信号):#对齐 AbortSignal.aborted
    """英文 aborted 或中文 已中止 任一为真则视为已中止。"""
    if 信号 is None:#无信号
        return False#未中止
    if getattr(信号,'aborted',False) is True:#英文旗标
        return True#已中止
    if getattr(信号,'已中止',False) is True:#中文旗标
        return True#已中止
    return False#未中止

def 断言列举未取消(信号):#取消检查点
    """在下一个取消检查点停下列举。"""
    if 信号已中止(信号):#已取消
        raise 子智能体错误('subagent listing was cancelled','CANCELLED')#稳定取消失败

def 比较语料记录(甲,乙):#语料排序
    """按耐久创建时间再按 id 比较兄弟。"""
    甲头=甲['header']#甲头
    乙头=乙['header']#乙头
    差=取字段(甲头,'createdAt',0)-取字段(乙头,'createdAt',0)#时间差
    if 差!=0:#时间不同
        return -1 if 差<0 else 1#按时间
    甲id=str(取字段(甲头,'id') or '')#甲id
    乙id=str(取字段(乙头,'id') or '')#乙id
    if 甲id<乙id:#id更小
        return -1#甲先
    if 甲id>乙id:#id更大
        return 1#乙先
    return 0#相等

def 同一生命周期(元,期望):#生命周期证人比较
    """一份检查过的日志是否仍属于枚举到的生命周期。"""
    for 键 in 生命周期证人键:#逐键
        if 取字段(元,键)!=取字段(期望,键):#不相等
            return False#分叉
    return True#同一生命周期

def 子体行(标识,身份,活动,有子体):#建造子体行
    """把一份已提供身份物化为子体行。"""
    if 身份.get('mode')=='one-shot':#一次性行
        行={'kind':'child','id':标识,'mode':'one-shot','activity':活动,'hasChildren':有子体}#一次性
        if 'label' in 身份 and 身份['label'] is not None:#有标签才展开
            行['label']=身份['label']#展开
        return 行#一次性行
    return {'kind':'child','id':标识,'mode':'continuable','label':身份['label'],'activity':活动,'hasChildren':有子体}#可续跑行

def 准备列举(上下文对象,信号=None):#准备列举运行时
    """一次性解析列举服务并建造一份活优先会话语料。"""
    投影=上下文对象.get('sessionProjections') if hasattr(上下文对象,'get') else None#投影注册表
    # 在任何读取之前检查，即使候选为零：模式/标签是行的强约定，缺少折叠能力是确定性的部署配置错误。
    if 投影 is None:#未挂载投影
        raise 子智能体错误(#配置错误
            'listing subagents requires the sessionProjections registry (load @deepseek-ai/dsh-session-projection)',#文案
            'SUBAGENT_CONTROL_PROJECTIONS_UNAVAILABLE',#错误码
        )#SubagentError结束
    # 严格全局读取，绝不用 ctx.sessions 属性代理。
    会话们=上下文对象.get('sessions') if hasattr(上下文对象,'get') else None#会话存储
    if 会话们 is None:#未挂载存储
        raise 子智能体错误(#配置错误
            'listing subagents requires the session store (load @deepseek-ai/dsh-session)',#文案
            'SUBAGENT_CONTROL_SESSION_STORE_UNAVAILABLE',#错误码
        )#SubagentError结束
    断言列举未取消(信号)#取消检查点
    持久化=上下文对象.get('sessionPersistence') if hasattr(上下文对象,'get') else None#可选持久化
    # 仅可选加速：缺少缓存服务只表示每个冷候选走权威准备档。
    缓存=上下文对象.get('sessionProjectionCache') if hasattr(上下文对象,'get') else None#可选投影缓存
    持久头们=[]#持久化头
    if 持久化 is not None:#有持久化
        try:#尝试列举持久化头
            列举=getattr(持久化,'list',None) or getattr(持久化,'列出',None)#列举方法
            持久头们=list(解开(列举(信号)))#列出头
        except Exception as 错误:#列举失败
            # 后端可能在观察到转发信号后以自己的中止失败拒绝；取消仍是稳定的子智能体失败。
            断言列举未取消(信号)#取消则改抛子智能体错误
            raise 错误#否则原样抛出
        断言列举未取消(信号)#列举后取消检查点
    # 活优先合并，不做头调和：活记录整份赢下其 id。
    语料={}#活优先语料
    for 头 in 持久头们:#先放持久化
        语料[取字段(头,'id')]={'header':头,'live':None}#冷记录
    列出=getattr(会话们,'list',None) or getattr(会话们,'列出',None)#活列方法
    for 会话 in 列出():#再用活会话覆盖
        头=取字段(会话,'header')#会话头
        语料[取字段(头,'id')]={'header':头,'live':会话}#活记录赢
    子智能体父们=set()#有子智能体后代的父
    for 记录 in 语料.values():#扫描语料
        头=记录['header']#头
        if 取字段(头,'origin')=='subagent' and 取字段(头,'parentSession') is not None:#子智能体且有父
            子智能体父们.add(取字段(头,'parentSession'))#记下父
    return {'projections':投影,'persistence':持久化,'cache':缓存,'corpus':语料,'subagentParents':子智能体父们}#列举运行时

def 解析冷身份(持久化,投影,缓存,头,有子体,信号=None):#解析冷身份
    """沿剩余梯子解析一个冷候选。"""
    子标识=取字段(头,'id')#候选id
    if 缓存 is not None:#有缓存
        缓存身份=None#缓存身份
        try:#读缓存快照
            快照方法=getattr(缓存,'cachedSnapshot',None) or getattr(缓存,'缓存快照',None)#缓存方法
            快照=快照方法(头) if 快照方法 is not None else None#读快照
            缓存身份=取字段(取字段(快照,'values'),'subagent') if 快照 is not None else None#读subagent单元
        except Exception:#缓存行损坏
            # 与下面的准备折叠不同，抛错的缓存读取不下判决：缓存是派生数据。
            缓存身份=None#当作未命中
        # 子体自身描述符一旦追加就不可变，因此仅当序号门证明身份折自自身后缀时缓存身份才是终态。
        种子长度=取字段(头,'seedLength') or 0#种子长度
        if 缓存身份 is not None and 取字段(缓存身份,'seq',-1)>=种子长度:#自身后缀身份
            return 子体行(子标识,缓存身份,'inactive',有子体)#冷子体行
    断言列举未取消(信号)#检查前取消检查点
    try:#持久化检查
        检查=getattr(持久化,'inspect',None) or getattr(持久化,'检查',None)#检查方法
        已检=解开(检查(子标识,信号))#读头与事件
    except Exception:#检查失败
        # 按子体隔离：子体消失或其后端读取失败——一条诊断行，列举本身仍成功。
        断言列举未取消(信号)#取消则改抛
        return {'kind':'diagnostic','id':子标识,'reason':'unavailable'}#瞬时不可用
    断言列举未取消(信号)#检查后取消检查点
    元=取字段(已检,'meta')#检查头
    # 会话 id 命名的是槽位，不是生命周期。
    if not 同一生命周期(元,头):#生命周期证人分叉
        return {'kind':'diagnostic','id':子标识,'reason':'corrupt'}#损坏诊断
    try:#经注册表折叠分离日志
        恢复=getattr(投影,'restore',None) or getattr(投影,'恢复',None)#恢复方法
        已折=恢复({},取字段(已检,'events') or [],0)#从零恢复
        身份=取字段(取字段(取字段(已折,'snapshot'),'values'),'subagent')#读subagent单元
    except Exception:#任一单元拒绝损坏载荷
        return {'kind':'diagnostic','id':子标识,'reason':'corrupt'}#损坏诊断
    if 身份 is None:#折叠无身份
        return {'kind':'diagnostic','id':子标识,'reason':'corrupt'}#已结算无身份
    return 子体行(子标识,身份,'inactive',有子体)#冷子体行

def 解析候选行(候选们,列举,信号=None):#解析候选行
    """以有界冷读为对齐候选解析投影行。"""
    投影=列举['projections']#投影注册表
    持久化=列举['persistence']#可选持久化
    缓存=列举['cache']#可选投影缓存
    子智能体父们=列举['subagentParents']#有后代的父
    行们=[None]*len(候选们)#按索引占位
    冷读=[]#待冷读作业
    for 下标,候选 in enumerate(候选们):#先处理活候选
        子标识=取字段(候选['header'],'id')#候选id
        if 候选.get('live') is None:#冷候选
            冷读.append({'index':下标,'header':候选['header']})#排队冷读
            continue#本候选结束
        # 注册表水位缓存零日志读取提供活值；活子体尚无身份是建立提供方追加描述符之前的创建窗口。
        try:#折叠活快照
            快照方法=getattr(投影,'snapshot',None) or getattr(投影,'快照',None)#快照方法
            快照=快照方法(候选['live'])#读水位
            身份=取字段(取字段(快照,'values'),'subagent')#读subagent单元
        except Exception:#任意单元折叠/模式拒绝
            # 这是本子体的确定性数据损坏；降级为一条 corrupt 诊断。
            行们[下标]={'kind':'diagnostic','id':子标识,'reason':'corrupt'}#损坏诊断
            continue#本候选结束
        # 单元的可序列化无值哨兵是 null；undefined 只表示键在 JSON 边界被丢掉。两者都是无值。
        if 身份 is None:#创建窗口省略
            continue#省略
        行们[下标]=子体行(子标识,身份,'running',子标识 in 子智能体父们)#活子体行
    # 冷候选只在持久化列出它们时存在。
    if 持久化 is not None and len(冷读)>0:#需要冷读
        队列=list(冷读)#作业队列
        while len(队列)>0:#串行消化（Python端口用串行替代有界并发工人）
            作业=队列.pop(0)#取作业
            行们[作业['index']]=解析冷身份(#解析冷身份
                持久化,投影,缓存,作业['header'],#服务与头
                取字段(作业['header'],'id') in 子智能体父们,信号,#是否有后代与取消
            )#resolveColdIdentity结束
    断言列举未取消(信号)#全部解析后取消检查点
    return 行们#对齐行

def 后代候选(语料,根会话标识):#后代候选
    """无递归地从完整树建造按来源分类的候选。"""
    子女={}#父到子女
    for 记录 in 语料.values():#建邻接
        父标识=取字段(记录['header'],'parentSession')#直接父
        if 父标识 is None:#无父跳过
            continue#跳过
        if 父标识 not in 子女:#新建列表
            子女[父标识]=[记录]#新建
        else:#已有兄弟
            子女[父标识].append(记录)#追加
    for 兄弟 in 子女.values():#兄弟排序
        兄弟.sort(key=lambda 记录:(取字段(记录['header'],'createdAt',0),str(取字段(记录['header'],'id') or '')))#按时间再id
    定位=[]#结果
    栈=[{'record':记录,'parentId':根会话标识,'depth':1} for 记录 in reversed(子女.get(根会话标识) or [])]#根的直接子女反转压栈
    已访问=set([根会话标识])#已访问，含根
    while len(栈)>0:#迭代前序
        位置=栈.pop()#弹出一帧
        标识=取字段(位置['record']['header'],'id')#当前id
        if 标识 in 已访问:#环或重复跳过
            continue#跳过
        已访问.add(标识)#记下
        if 取字段(位置['record']['header'],'origin')=='subagent':#只收子智能体
            定位.append(位置)#收下
        后代=子女.get(标识) or []#其子女
        for 记录 in reversed(list(后代)):#反转压栈以保持顺序
            栈.append({'record':记录,'parentId':标识,'depth':位置['depth']+1})#更深一档
    return 定位#带位置候选

def 列举子体(上下文对象,父会话标识,信号=None):#枚举直接子体
    """从 ctx.sessions 与可选会话持久化的活优先合并中，枚举一个父的按来源分类的直接子体。"""
    列举=准备列举(上下文对象,信号)#准备运行时与语料
    候选们=[记录 for 记录 in 列举['corpus'].values()
        if 取字段(记录['header'],'parentSession')==父会话标识
        and 取字段(记录['header'],'origin')=='subagent']#直接子且来源是子智能体
    候选们.sort(key=lambda 记录:(取字段(记录['header'],'createdAt',0),str(取字段(记录['header'],'id') or '')))#按创建时间再按id
    行们=解析候选行(候选们,列举,信号)#解析投影行
    return [行 for 行 in 行们 if 行 is not None]#去掉省略项

def 列举后代(上下文对象,根会话标识,信号=None):#枚举后代树
    """以稳定前序枚举一个根下每个有会话的子智能体。"""
    列举=准备列举(上下文对象,信号)#准备运行时与语料
    定位=后代候选(列举['corpus'],根会话标识)#带位置的候选
    行们=解析候选行([位置['record'] for 位置 in 定位],列举,信号)#解析投影行
    条目们=[]#结果
    for 下标,位置 in enumerate(定位):#按位置对齐行
        行=行们[下标]#对应投影行
        if 行 is not None:#有解释结果
            条目=dict(行)#复制行
            条目['parentId']=位置['parentId']#附上树位置
            条目['depth']=位置['depth']#相对深度
            条目们.append(条目)#收下
    return 条目们#后代条目
