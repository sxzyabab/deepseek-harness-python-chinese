'当前 Loader 插件条目的只读投影'
from ...启动.app启动.包元 import 读插件元
from ...类型化远程调用.协议 import 远程服务,远程 as _远程
from .类型 import 插件条目标识
from . import (
    远程,
)

__all__=['插件条目标识','读插件清单','名称','依赖','插件清单网关']

名称='plugin-inventory'#插件名（字面量）
依赖=['加载器']#宿主加载器服务键

纤程状态映射={#纤程状态数值 → 对外阶段名
    0:'pending',#尚未加载
    1:'loading',#正在加载
    2:'active',#已激活
    3:'failed',#加载失败
    4:None,#已处置，对外不报阶段
    5:'unloading',#正在卸载
}

def 取展示元(包表,模块名,基础):
    '包表在场且基准网址不是 None 时读展示元；空字典也保留'
    if 包表 is None or 基础 is None or not isinstance(模块名,str):#缺一侧
        return None#不读
    读=getattr(包表,'元属于',None)#服务方法
    if callable(读):#走服务
        return 读(模块名,基础)#元
    return 读插件元(模块名,基础)#直接读

def 条目字段(条目):
    '中文加载器条目或英文 entries 行，收成同一组字段'
    if hasattr(条目,'选项'):#宿主加载器
        选项=条目.选项#选项表
        分组=选项['group'] if isinstance(选项,dict) and 'group' in 选项 else None#组标记
        模块名=选项.get('name') if isinstance(选项,dict) else None#模块名
        纤程=条目.纤程#纤程
        状态值=None if 纤程 is None else getattr(纤程,'状态',None)#数值阶段
        return {#字段
            '是组':分组 is not None and 分组 is not False,#空字典也算组
            '编号':条目.编号,#带祖先前缀
            '模块名':模块名,#模块名
            '启用':not 条目.已禁用,#有效启用
            '状态值':状态值,#纤程状态
            '基础':条目.父组.所属树.所属上下文.基准网址,#本树基准
        }#结束
    选项=getattr(条目,'options',None)#英文形
    if isinstance(选项,dict):#字典选项
        分组=选项['group'] if 'group' in 选项 else None#组标记
        模块名=选项.get('name')#模块名
    else:#对象选项
        分组=None if 选项 is None else getattr(选项,'group',None)#组标记
        模块名=None if 选项 is None else getattr(选项,'name',None)#模块名
    纤程=getattr(条目,'fiber',None)#纤程
    状态值=None if 纤程 is None else getattr(纤程,'state',getattr(纤程,'状态',None))#阶段
    父=getattr(条目,'parent',None)#父
    树=None if 父 is None else getattr(父,'tree',None)#树
    树上下文=None if 树 is None else getattr(树,'ctx',None)#树上下文
    基础=None if 树上下文 is None else getattr(树上下文,'baseUrl',getattr(树上下文,'基准网址',None))#基准
    return {#字段
        '是组':分组 is not None and 分组 is not False,#空字典也算组
        '编号':getattr(条目,'id',None),#条目 id
        '模块名':模块名,#模块名
        '启用':not getattr(条目,'disabled',False),#有效启用
        '状态值':状态值,#纤程状态
        '基础':基础,#基准
    }#结束

def 读插件清单(上下文):
    '读取当前 Loader 条目与可选预设组合；无单独运行时缓存'
    条目列表=[]#按 Loader 遍历顺序
    包表=上下文.获取服务('pluginPackages')#可选包表
    加载器=上下文.获取服务('加载器')#宿主服务键
    if 加载器 is None:#英文别名
        加载器=上下文.获取服务('loader')#别名
    if 加载器 is None:#两边都没有
        raise RuntimeError('plugin-inventory: loader service is absent')#缺加载器
    列出=getattr(加载器,'列出插件配置',None)#中文枚举
    行源=列出() if callable(列出) else 加载器.entries()#英文 entries
    for 条目 in 行源:#逐条
        字段=条目字段(条目)#归一
        if 字段['是组']:#group 不是清单行
            continue#跳过
        状态值=字段['状态值']#数值
        阶段=None if 状态值 is None else 纤程状态映射.get(状态值,None)#对外阶段
        元=取展示元(包表,字段['模块名'],字段['基础'])#展示元
        行={#清单行
            'entryId':插件条目标识(字段['编号']),#条目 id
            'moduleName':字段['模块名'],#模块名
            'enabled':字段['启用'],#有效启用
            'fiberPhase':阶段,#阶段
        }#行结束
        if 元 is not None:#空字典也挂上
            行['meta']=元#展示元
        条目列表.append(行)#收下
    预设=上下文.获取服务('agentPresets')#可选预设名册
    管理={} if 上下文.获取服务('pluginManager') is None else {'managementAvailable':True}#管理面
    if 预设 is None:#无预设
        return {'entries':条目列表,**管理}#仅条目
    读组合=getattr(预设,'组合体库存清单',None)#中文清单
    if not callable(读组合):#退回英文名
        读组合=预设.compositionInventory#英文清单
    组合列表=读组合()#组合
    智能体预设=[]#预设组；空列表也要返回
    根基准=上下文.基准网址 if hasattr(上下文,'基准网址') else getattr(上下文,'baseUrl',None)#展示元基准
    for 组合 in 组合列表:#逐组
        if isinstance(组合,dict):#字典组合
            行源=组合['rows'] if 'rows' in 组合 else []#缺 rows 当空表
        else:#对象组合
            行源=组合.rows if getattr(组合,'rows',None) is not None else []#空列表保留
        行列表=[]#投影行
        for 行 in 行源:#逐行
            if isinstance(行,dict):#字典行
                纤程状态=行.get('fiberState')#数值或 None；0 是 pending
                其余={键:值 for 键,值 in 行.items() if 键!='fiberState'}#对外用 fiberPhase
            else:#对象行
                纤程状态=getattr(行,'fiberState',None)#数值或 None
                其余={#行字段
                    'entryId':getattr(行,'entryId',None),#行 id
                    'moduleName':getattr(行,'moduleName',None),#模块名
                    'enabled':getattr(行,'enabled',None),#启用
                    **({} if getattr(行,'condition',None) is None else {'condition':行.condition}),#空串条件也保留
                }#结束
            模块名=其余['moduleName'] if 'moduleName' in 其余 else None#模块名
            行元=取展示元(包表,模块名,根基准)#展示元
            投影={**其余,'fiberPhase':None if 纤程状态 is None else 纤程状态映射.get(纤程状态,None)}#阶段
            if 行元 is not None:#空字典也挂上
                投影['meta']=行元#展示元
            行列表.append(投影)#收下
        if isinstance(组合,dict):#字典组合
            项={键:值 for 键,值 in 组合.items() if 键 not in ('rows','trust')}#快照组不含 rows 与 trust
        else:#对象组合
            项={#组字段
                'id':组合.id,#预设 id
                'isDefault':组合.isDefault,#是否默认
                **({} if getattr(组合,'name',None) is None else {'name':组合.name}),#空名也保留
                **({} if getattr(组合,'broken',None) is None else {'broken':组合.broken}),#损坏原因
            }#结束
        智能体预设.append({**项,'rows':行列表})#空行表也挂上
    return {'entries':条目列表,'agentPresets':智能体预设,**管理}#快照

class 插件清单网关(远程服务):
    '只远程暴露 Loader 当前非 group 条目状态的服务'
    inject=依赖#等加载器
    name=名称#插件名

    def __init__(自身,上下文,配置值=None):
        '登记 pluginInventory。加载器按位传入配置，本服务没有配置字段'
        super().__init__(上下文,'pluginInventory')#远程服务键
        自身.配置=配置值#原样留下，list 不读它

    @_远程
    def list(自身):
        '每次调用直接读 Loader，不缓存'
        return 读插件清单(自身.所属上下文)#投影

name=名称#框架槽
inject=依赖#框架槽
default=插件清单网关#类插件
