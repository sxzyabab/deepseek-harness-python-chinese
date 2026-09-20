"""当前 Loader 插件条目的只读投影。"""
from .类型 import 插件条目标识

__all__=['插件条目标识','读插件清单','名称','依赖','应用']

名称='plugin-inventory'#插件名（字面量）
依赖=['loader']

纤程状态映射={#纤程状态数值 → 对外阶段名
    0:'pending',#尚未加载
    1:'loading',#正在加载
    2:'active',#已激活
    3:'failed',#加载失败
    4:None,#已处置，对外不报阶段
    5:'unloading',#正在卸载
}

def 读插件清单(上下文):
    """读取当前 Loader 条目与可选预设组合；无单独运行时缓存。"""
    条目列表=[]#按 Loader 遍历顺序
    for 条目 in 上下文.loader.entries():
        if 条目.options.group:#group 不是清单行
            continue
        纤程=条目.fiber
        阶段=None if 纤程 is None else 纤程状态映射.get(纤程.state,None)
        条目列表.append({
            'entryId':插件条目标识(条目.id),
            'moduleName':条目.options.name,
            'enabled':not 条目.disabled,
            'fiberPhase':阶段,
        })
    预设=上下文.获取服务('agentPresets')#可选预设名册
    管理={} if 上下文.获取服务('pluginManager') is None else {'managementAvailable':True}
    if 预设 is None:
        return {'entries':条目列表,**管理}
    组合列表=预设.compositionInventory()
    智能体预设=[]
    for 组合 in 组合列表:
        行列表=[]
        for 行 in 组合['rows']:
            if isinstance(行,dict):
                纤程状态=行.get('fiberState')
                其余={键:值 for 键,值 in 行.items() if 键!='fiberState'}#对外用 fiberPhase，去掉 fiberState
            else:
                纤程状态=getattr(行,'fiberState',None)
                其余={
                    'entryId':getattr(行,'entryId',None),
                    'moduleName':getattr(行,'moduleName',None),
                    'enabled':getattr(行,'enabled',None),
                    **({} if getattr(行,'condition',None) is None else {'condition':行.condition}),
                }
            行列表.append({**其余,'fiberPhase':None if 纤程状态 is None else 纤程状态映射.get(纤程状态,None)})
        if isinstance(组合,dict):
            项={键:值 for 键,值 in 组合.items() if 键!='rows'}
        else:
            项={
                'id':组合.id,'trust':组合.trust,'isDefault':组合.isDefault,
                **({} if getattr(组合,'name',None) is None else {'name':组合.name}),
                **({} if getattr(组合,'broken',None) is None else {'broken':组合.broken}),
            }
        智能体预设.append({**项,'rows':行列表})
    return {'entries':条目列表,'agentPresets':智能体预设,**管理}

class 插件清单网关:
    """只远程暴露 Loader 当前非 group 条目状态的服务。"""
    inject=依赖

    def __init__(自身,上下文):
        """按上下文登记 pluginInventory 远程服务。"""
        自身.上下文=上下文

    def list(自身):
        """每次调用直接读 Loader，不缓存。"""
        return 读插件清单(自身.上下文)

def 应用(上下文):
    """登记插件清单远程网关。"""
    上下文.提供服务('pluginInventory',插件清单网关(上下文))

name=名称#框架槽
inject=依赖#框架槽
apply=应用#框架槽
default=插件清单网关#框架槽
