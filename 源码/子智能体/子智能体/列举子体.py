"""只读枚举耐久子智能体子体与后代树，直接来自活会话存储与可选会话持久化——无查询服务。头与快照为 dict，会话为对象。"""
from typing import Literal,NotRequired,TypedDict#字面量、可选字段与结构类型
from .错误 import 子智能体错误#导入子智能体错误

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

def 已中止(信号):
    """信号是否已中止。无信号视为未中止。"""
    if 信号 is None:#无信号
        return False#未中止
    return 信号._事件.is_set()#Event 置位

def 断言列举未取消(信号):
    """在下一个取消检查点停下列举。"""
    if 已中止(信号):#已取消
        raise 子智能体错误('subagent listing was cancelled','CANCELLED')#稳定取消失败

def 语料排序键(记录):
    """按耐久创建时间再按 id 比较兄弟。记录为 dict，头为 dict。"""
    头=记录['header']#头
    创建=头['createdAt'] if 'createdAt' in 头 else 0#时间
    标识=str(头['id'] if 'id' in 头 else '')#id
    return (创建,标识)#排序键

def 同一生命周期(元,期望):
    """一份检查过的日志是否仍属于枚举到的生命周期。元与期望为 dict。"""
    for 键 in 生命周期证人键:#逐键
        左=元[键] if 键 in 元 else None#元值
        右=期望[键] if 键 in 期望 else None#期望值
        if 左!=右:#不相等
            return False#分叉
    return True#同一生命周期

def 子体行(标识,身份,活动,有子体):
    """把一份已提供身份物化为子体行。身份为 dict。"""
    if 身份['mode']=='one-shot':#一次性行
        行={'kind':'child','id':标识,'mode':'one-shot','activity':活动,'hasChildren':有子体}#一次性
        if 'label' in 身份 and 身份['label'] is not None:#有标签才展开
            行['label']=身份['label']#展开
        return 行#一次性行
    return {'kind':'child','id':标识,'mode':'continuable','label':身份['label'],'activity':活动,'hasChildren':有子体}#可续跑行

def 读子智能体身份(快照):
    """从投影快照 dict 读 subagent 单元。"""
    if 快照 is None:#无快照
        return None#无身份
    if 'values' not in 快照:#无值表
        return None#无身份
    值表=快照['values']#值表
    if 'subagent' not in 值表:#无单元
        return None#无身份
    return 值表['subagent']#身份

def 准备列举(上下文对象,信号=None):
    """一次性解析列举服务并建造一份活优先会话语料。"""
    投影=上下文对象.获取服务('sessionProjections')#投影注册表
    if 投影 is None:#未挂载投影
        raise 子智能体错误(#配置错误
            'listing subagents requires the sessionProjections registry (load @deepseek-ai/dsh-session-projection)',#文案
            'SUBAGENT_CONTROL_PROJECTIONS_UNAVAILABLE',#错误码
        )#结束
    会话存储=上下文对象.获取服务('sessions')#会话存储
    if 会话存储 is None:#未挂载存储
        raise 子智能体错误(#配置错误
            'listing subagents requires the session store (load @deepseek-ai/dsh-session)',#文案
            'SUBAGENT_CONTROL_SESSION_STORE_UNAVAILABLE',#错误码
        )#结束
    断言列举未取消(信号)#取消检查点
    持久化=上下文对象.获取服务('sessionPersistence')#可选持久化
    缓存=上下文对象.获取服务('sessionProjectionCache')#可选投影缓存
    持久头列表=[]#持久化头
    if 持久化 is not None:#有持久化
        try:#尝试列举持久化头
            持久头列表=list(持久化.列出(信号))#列出头
        except Exception as 错误:#列举失败
            断言列举未取消(信号)#取消则改抛子智能体错误
            raise 错误#否则原样抛出
        断言列举未取消(信号)#列举后取消检查点
    语料={}#活优先语料
    for 头 in 持久头列表:#先放持久化
        语料[头['id']]={'header':头,'live':None}#冷记录
    for 会话 in 会话存储.列出():#再用活会话覆盖
        头=会话.header#会话头
        语料[头['id']]={'header':头,'live':会话}#活记录赢
    子智能体父集合=set()#有子智能体后代的父
    for 记录 in 语料.values():#扫描语料
        头=记录['header']#头
        if ('origin' in 头 and 头['origin']=='subagent'
            and 'parentSession' in 头 and 头['parentSession'] is not None):#子智能体且有父
            子智能体父集合.add(头['parentSession'])#记下父
    return {'projections':投影,'persistence':持久化,'cache':缓存,'corpus':语料,'subagentParents':子智能体父集合}#列举运行时

def 解析冷身份(持久化,投影,缓存,头,有子体,信号=None):
    """沿剩余梯子解析一个冷候选。头为 dict。"""
    子标识=头['id']#候选id
    if 缓存 is not None:#有缓存
        缓存身份=None#缓存身份
        try:#读缓存快照
            快照=缓存.缓存快照(头)#读快照
            缓存身份=读子智能体身份(快照)#读subagent单元
        except Exception:#缓存行损坏
            缓存身份=None#当作未命中
        种子长度=头['seedLength'] if 'seedLength' in 头 and 头['seedLength'] is not None else 0#种子长度
        序号=-1#缺省
        if 缓存身份 is not None and 'seq' in 缓存身份:#有序号
            序号=缓存身份['seq']#序号
        if 缓存身份 is not None and 序号>=种子长度:#自身后缀身份
            return 子体行(子标识,缓存身份,'inactive',有子体)#冷子体行
    断言列举未取消(信号)#检查前取消检查点
    try:#持久化检查
        已检=持久化.检查(子标识,信号)#读头与事件
    except Exception:#检查失败
        断言列举未取消(信号)#取消则改抛
        return {'kind':'diagnostic','id':子标识,'reason':'unavailable'}#瞬时不可用
    断言列举未取消(信号)#检查后取消检查点
    元=已检['meta']#检查头
    if not 同一生命周期(元,头):#生命周期证人分叉
        return {'kind':'diagnostic','id':子标识,'reason':'corrupt'}#损坏诊断
    try:#经注册表折叠分离日志
        事件列表=已检['events'] if 'events' in 已检 and 已检['events'] is not None else []#事件
        已折=投影.恢复({},事件列表,0,头)#从零恢复
        身份=读子智能体身份(已折['snapshot'] if 'snapshot' in 已折 else None)#读subagent单元
    except Exception:#任一单元拒绝损坏载荷
        return {'kind':'diagnostic','id':子标识,'reason':'corrupt'}#损坏诊断
    if 身份 is None:#折叠无身份
        return {'kind':'diagnostic','id':子标识,'reason':'corrupt'}#已结算无身份
    return 子体行(子标识,身份,'inactive',有子体)#冷子体行

def 解析候选行(候选列表,列举,信号=None):
    """以有界冷读为对齐候选解析投影行。候选为 dict。"""
    投影=列举['projections']#投影注册表
    持久化=列举['persistence']#可选持久化
    缓存=列举['cache']#可选投影缓存
    子智能体父集合=列举['subagentParents']#有后代的父
    行列表=[None]*len(候选列表)#按索引占位
    冷读=[]#待冷读作业
    for 下标,候选 in enumerate(候选列表):#先处理活候选
        子标识=候选['header']['id']#候选id
        if 候选['live'] is None:#冷候选
            冷读.append({'index':下标,'header':候选['header']})#排队冷读
            continue#本候选结束
        try:#折叠活快照
            快照=投影.快照(候选['live'])#读水位
            身份=读子智能体身份(快照)#读subagent单元
        except Exception:#任意单元折叠/模式拒绝
            行列表[下标]={'kind':'diagnostic','id':子标识,'reason':'corrupt'}#损坏诊断
            continue#本候选结束
        if 身份 is None:#创建窗口省略
            continue#省略
        行列表[下标]=子体行(子标识,身份,'running',子标识 in 子智能体父集合)#活子体行
    if 持久化 is not None and len(冷读)>0:#需要冷读
        队列=list(冷读)#作业队列
        while len(队列)>0:#串行消化
            作业=队列.pop(0)#取作业
            作业头=作业['header']#头
            行列表[作业['index']]=解析冷身份(#解析冷身份
                持久化,投影,缓存,作业头,#服务与头
                作业头['id'] in 子智能体父集合,信号,#是否有后代与取消
            )#结束
    断言列举未取消(信号)#全部解析后取消检查点
    return 行列表#对齐行

def 后代候选(语料,根会话标识):
    """无递归地从完整树建造按来源分类的候选。语料值为 dict，头为 dict。"""
    子女={}#父到子女
    for 记录 in 语料.values():#建邻接
        头=记录['header']#头
        if 'parentSession' not in 头 or 头['parentSession'] is None:#无父跳过
            continue#跳过
        父标识=头['parentSession']#直接父
        if 父标识 not in 子女:#新建列表
            子女[父标识]=[记录]#新建
        else:#已有兄弟
            子女[父标识].append(记录)#追加
    for 兄弟 in 子女.values():#兄弟排序
        兄弟.sort(key=语料排序键)#按时间再id
    定位=[]#结果
    栈=[{'record':记录,'parentId':根会话标识,'depth':1} for 记录 in reversed(子女[根会话标识] if 根会话标识 in 子女 else [])]#根的直接子女反转压栈
    已访问=set([根会话标识])#已访问，含根
    while len(栈)>0:#迭代前序
        位置=栈.pop()#弹出一帧
        标识=位置['record']['header']['id']#当前id
        if 标识 in 已访问:#环或重复跳过
            continue#跳过
        已访问.add(标识)#记下
        if 'origin' in 位置['record']['header'] and 位置['record']['header']['origin']=='subagent':#只收子智能体
            定位.append(位置)#收下
        后代=子女[标识] if 标识 in 子女 else []#其子女
        for 记录 in reversed(list(后代)):#反转压栈以保持顺序
            栈.append({'record':记录,'parentId':标识,'depth':位置['depth']+1})#更深一档
    return 定位#带位置候选

def 列举子体(上下文对象,父会话标识,信号=None):
    """从 ctx.sessions 与可选会话持久化的活优先合并中，枚举一个父的按来源分类的直接子体。"""
    列举=准备列举(上下文对象,信号)#准备运行时与语料
    候选列表=[]#直接子
    for 记录 in 列举['corpus'].values():#扫描语料
        头=记录['header']#头
        if ('parentSession' in 头 and 头['parentSession']==父会话标识
            and 'origin' in 头 and 头['origin']=='subagent'):#直接子且来源是子智能体
            候选列表.append(记录)#收下
    候选列表.sort(key=语料排序键)#按创建时间再按id
    行列表=解析候选行(候选列表,列举,信号)#解析投影行
    return [行 for 行 in 行列表 if 行 is not None]#去掉省略项

def 列举后代(上下文对象,根会话标识,信号=None):
    """以稳定前序枚举一个根下每个有会话的子智能体。"""
    列举=准备列举(上下文对象,信号)#准备运行时与语料
    定位=后代候选(列举['corpus'],根会话标识)#带位置的候选
    行列表=解析候选行([位置['record'] for 位置 in 定位],列举,信号)#解析投影行
    条目列表=[]#结果
    for 下标,位置 in enumerate(定位):#按位置对齐行
        行=行列表[下标]#对应投影行
        if 行 is not None:#有解释结果
            条目=dict(行)#复制行
            条目['parentId']=位置['parentId']#附上树位置
            条目['depth']=位置['depth']#相对深度
            条目列表.append(条目)#收下
    return 条目列表#后代条目
