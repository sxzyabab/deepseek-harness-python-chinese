"""当前 Cordis Loader 插件条目的只读投影。"""
from typing import NotRequired,TypedDict#结构类型

__all__=['插件条目标识','读插件清单','名称','注入','应用','默认']#仅中文公开名

名称='plugin-inventory'#插件名
注入=['loader']#硬依赖

class 插件清单条目(TypedDict):#一条非 group Loader 条目
    entryId:str#品牌化条目 id
    moduleName:str#模块说明符
    enabled:bool#有效启用
    fiberPhase:str|None#根 Fiber 阶段

class 智能体预设插件行(TypedDict):#预设组合行
    entryId:str|None#行 id
    moduleName:str#模块名
    enabled:bool|str#有效启用或 conditional
    condition:NotRequired[str]#条件表达式
    fiberPhase:str|None#fiber 阶段

class 智能体预设插件组(TypedDict):#预设分组
    id:str#预设 id
    trust:str#信任级别
    name:NotRequired[str]#显示名
    isDefault:bool#是否默认
    broken:NotRequired[str]#损坏原因
    rows:list#组合行

class 插件清单快照(TypedDict):#一次 list 投影
    entries:list#非 group 条目
    managementAvailable:NotRequired[bool]#是否暴露持久管理
    agentPresets:NotRequired[list]#可选预设组合

光纤状态映射={#FiberState 数值 → 对外阶段
    0:'pending',#尚未加载
    1:'loading',#正在加载
    2:'active',#已激活
    3:'failed',#加载失败
    4:None,#已处置
    5:'unloading',#正在卸载
}#映射结束

def 插件条目标识(值):
    """在拥有边界把 Loader 树条目 id 打上品牌。"""
    return 值#品牌化条目 id

def 读插件清单(上下文):
    """读取当前 Loader 条目与可选预设组合；无单独运行时缓存。"""
    条目列表=[]#按 Loader 顺序
    for 条目 in 上下文.loader.entries():#遍历 Loader 树
        if 条目.options.group:#group 不是清单行
            continue#跳过
        光纤=条目.fiber#根 Fiber
        阶段=None if 光纤 is None else 光纤状态映射.get(光纤.state,None)#阶段
        条目列表.append({#对外投影
            'entryId':插件条目标识(条目.id),#品牌 id
            'moduleName':条目.options.name,#模块名
            'enabled':not 条目.disabled,#有效启用
            'fiberPhase':阶段,#阶段
        })#append结束
    预设=上下文.获取服务('agentPresets')#可选预设名册
    管理={} if 上下文.获取服务('pluginManager') is None else {'managementAvailable':True}#管理能力
    if 预设 is None:#无名册
        return {'entries':条目列表,**管理}#条目+管理
    组合列表=预设.compositionInventory()#读组合
    智能体预设=[]#按预设投影
    for 组合 in 组合列表:#每组
        行列表=[]#行投影
        for 行 in 组合['rows']:#每行
            光纤状态=行.get('fiberState') if isinstance(行,dict) else getattr(行,'fiberState',None)#fiber
            其余={键:行[键] for 键 in 行 if 键!='fiberState'} if isinstance(行,dict) else {#去掉 fiberState
                'entryId':getattr(行,'entryId',None),#行 id
                'moduleName':getattr(行,'moduleName',None),#模块
                'enabled':getattr(行,'enabled',None),#启用
                **({} if getattr(行,'condition',None) is None else {'condition':行.condition}),#条件
            }#其余
            if isinstance(行,dict):#映射
                其余={键:值 for 键,值 in 行.items() if 键!='fiberState'}#去掉
            行列表.append({**其余,'fiberPhase':None if 光纤状态 is None else 光纤状态映射.get(光纤状态,None)})#投影
        项={键:组合[键] for 键 in 组合 if 键!='rows'} if isinstance(组合,dict) else {#预设身份
            'id':组合.id,'trust':组合.trust,'isDefault':组合.isDefault,#必填
            **({} if getattr(组合,'name',None) is None else {'name':组合.name}),#名
            **({} if getattr(组合,'broken',None) is None else {'broken':组合.broken}),#损坏
        }#身份
        if isinstance(组合,dict):#映射
            项={键:值 for 键,值 in 组合.items() if 键!='rows'}#身份
        智能体预设.append({**项,'rows':行列表})#一组
    return {'entries':条目列表,'agentPresets':智能体预设,**管理}#整份快照

class 插件清单网关:
    """只远程暴露 Loader 当前非 group 条目状态的服务。"""
    注入=['loader']#类级 inject

    def __init__(自身,上下文):
        """按上下文登记 pluginInventory 远程服务。"""
        自身.上下文=上下文#保存

    def list(自身):
        """每次调用直接读 Loader。"""
        return 读插件清单(自身.上下文)#委托纯读取

def 应用(上下文):
    """登记插件清单远程网关。"""
    上下文.提供服务('pluginInventory',插件清单网关(上下文))#挂服务

name=名称#框架槽
inject=注入#框架槽
apply=应用#框架槽
default=插件清单网关#框架槽
