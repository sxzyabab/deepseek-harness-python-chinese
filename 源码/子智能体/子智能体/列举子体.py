from typing import Literal,NotRequired,TypedDict#字面量、可选字段与结构类型
from .异常 import 子智能体错误#导入子智能体错误

class 子智能体列举一次性子体(TypedDict):#列举结果的一次性子体臂
    kind:Literal['child']#子体条目
    id:str#耐久子会话 id
    activity:Literal['running','inactive']#目录观察时是否驻留
    hasChildren:bool#子目录是否含直接子
    mode:Literal['one-shot']#终态一次性子体
    label:NotRequired[str]#可选耐久创建标签

class 子智能体列举外部子体(TypedDict):#没有本地子会话的外部执行
    kind:Literal['child']#子体条目
    id:str#提供方身份
    activity:Literal['running','inactive']#目录观察时是否驻留
    hasChildren:bool#外部执行是叶子
    mode:Literal['external']#外部
    label:NotRequired[str]#可选标签

class 子智能体列举可续跑子体(TypedDict):#列举结果的可续跑子体臂
    kind:Literal['child']#子体条目
    id:str#耐久子会话 id
    activity:Literal['running','inactive']#目录观察时是否驻留
    hasChildren:bool#子目录是否含直接子
    mode:Literal['continuable']#可恢复对话
    label:str#耐久创建标签

class 子智能体列举诊断(TypedDict):#列举结果的诊断臂
    kind:Literal['diagnostic']#诊断条目
    id:str#候选的会话 id
    reason:Literal['corrupt','unsupported','unavailable']#候选没有 child 行的原因

子智能体列举条目=子智能体列举一次性子体|子智能体列举外部子体|子智能体列举可续跑子体|子智能体列举诊断#listDescendants 结果一条

class 子智能体后代列举外部(子智能体列举外部子体):#后代列举的外部执行
    parentId:str#本候选在枚举树中的耐久直接父
    depth:int#相对所请求根的边距

class 子智能体后代列举一次性(子智能体列举一次性子体):#后代列举的一次性子体
    parentId:str#本候选在枚举树中的耐久直接父
    depth:int#相对所请求根的边距

class 子智能体后代列举可续跑(子智能体列举可续跑子体):#后代列举的可续跑子体
    parentId:str#本候选在枚举树中的耐久直接父
    depth:int#相对所请求根的边距

class 子智能体后代列举诊断(子智能体列举诊断):#后代列举的诊断
    parentId:str#本候选在枚举树中的耐久直接父
    depth:int#相对所请求根的边距

子智能体后代列举条目=子智能体后代列举一次性|子智能体后代列举外部|子智能体后代列举可续跑|子智能体后代列举诊断#listDescendants 结果一条

def 已中止(信号):
    '信号是否已中止。无信号视为未中止'
    if 信号 is None:#无信号
        return False#未中止
    if hasattr(信号,'is_set'):#线程事件
        return bool(信号.is_set())#置位
    return bool(信号._事件.is_set())#工具中止信号

def 断言列举未取消(信号):
    '在下一个取消检查点停下列举'
    if 已中止(信号):#已取消
        raise 子智能体错误('subagent listing was cancelled','CANCELLED')#稳定取消失败

def _目录值(观察):
    '从一次会话观察取出 subagentCatalog'
    投影=观察.projections#投影块
    if not isinstance(投影,dict):#没有投影
        return None#缺席
    值=投影['values'] if 'values' in 投影 else 投影#活路径包在 values 里
    if not isinstance(值,dict) or 'subagentCatalog' not in 值:#没有目录
        return None#缺席
    return 值['subagentCatalog']#目录行

def 列举子体(上下文,父会话标识,信号=None):
    '经活优先会话观察读取父的耐久直接子目录'
    查询=上下文.获取服务('sessionQuery')#查询服务
    if 查询 is None:#没装
        raise 子智能体错误(
            'listing subagents requires the sessionQuery service (load @deepseek-ai/dsh-session-query)',
            'SUBAGENT_CONTROL_QUERY_UNAVAILABLE',
        )#拒绝
    选项={} if 信号 is None else {'signal':信号}#取消
    观察=查询.observeSession(父会话标识,选项)#点观察
    try:#用完即关
        条目=_目录值(观察)#目录
        if 条目 is None:#没登记投影
            raise 子智能体错误(
                'listing subagents requires the registered subagentCatalog projection',
                'SUBAGENT_CONTROL_PROJECTIONS_UNAVAILABLE',
            )#拒绝
        return list(条目)#父目录事件顺序
    finally:#释放观察
        观察.close()#关

def 列举后代(上下文,根会话标识,信号=None):
    '按父目录稳定前序走可达目录。外部是叶子；unknown 仍往下走并记 unsupported'
    会话表=上下文.获取服务('sessions')#会话存储
    if 会话表 is None:#没装
        raise 子智能体错误(
            'listing subagents requires the session store (load @deepseek-ai/dsh-session)',
            'SUBAGENT_CONTROL_SESSION_STORE_UNAVAILABLE',
        )#拒绝
    def 读子(标识):
        '读一个父的直接子，取消则停'
        断言列举未取消(信号)#读前
        try:#读目录
            孩子们=列举子体(上下文,标识,信号)#直接子
        except 子智能体错误:#服务缺失原样上抛
            断言列举未取消(信号)#取消优先
            raise#上抛
        断言列举未取消(信号)#读后
        return 孩子们#目录行
    栈=[{'entry':条目,'parentId':根会话标识,'depth':1} for 条目 in reversed(读子(根会话标识))]#根的直接子反转压栈
    已访问=set([根会话标识])#已访问
    结果=[]#前序
    while len(栈)>0:#迭代
        位置=栈.pop()#弹出
        条目=位置['entry']#目录行
        if 条目['id'] in 已访问:#环
            continue#跳过
        已访问.add(条目['id'])#记下
        try:#读子目录；外部不读
            孩子们=[] if 条目['mode']=='external' else 读子(条目['id'])#子
        except 子智能体错误:#缝错误上抛
            raise#上抛
        except BaseException as 错误:#分支读失败
            码=getattr(错误,'code',None)#错误码
            原因='corrupt' if 码 in ('SESSION_QUERY_CORRUPT_SESSION','SESSION_QUERY_SOURCE_CONFLICT') else 'unavailable'#分类
            结果.append({'kind':'diagnostic','id':条目['id'],'parentId':位置['parentId'],'depth':位置['depth'],'reason':原因})#诊断
            continue#停这一支
        if 条目['mode']=='unknown':#未知模式
            结果.append({'kind':'diagnostic','id':条目['id'],'parentId':位置['parentId'],'depth':位置['depth'],'reason':'unsupported'})#仍遍历
        else:#子行
            行={键:值 for 键,值 in 条目.items() if 键!='createdAt'}#去掉创建时刻
            取=会话表.get if hasattr(会话表,'get') else 会话表.获取#驻留查找
            行['kind']='child'#子
            行['parentId']=位置['parentId']#父
            行['depth']=位置['depth']#深度
            行['activity']='inactive' if 取(条目['id']) is None else 'running'#是否驻留
            行['hasChildren']=len(孩子们)>0#有直接子
            结果.append(行)#收下
        for 孩子 in reversed(list(孩子们)):#反转压栈以保持目录顺序
            栈.append({'entry':孩子,'parentId':条目['id'],'depth':位置['depth']+1})#更深
    return 结果#后代
