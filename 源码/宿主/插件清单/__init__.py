'当前 Loader 插件条目的只读投影'
from ...类型化远程调用.协议 import 远程服务,远程#远程服务基类与直接调用标记
from . import 类型,异常#同目录模块，导入即执行顶层

__all__=['类型','异常','插件条目标识','读取插件清单','插件清单网关']#公开名

#FiberState 的运行时镜像。数值与加载器纤程状态一致
纤程状态数值={'等待':0,#尚未加载
    '加载中':1,#正在加载
    '已激活':2,#已激活
    '失败':3,#加载失败
    '已拆除':4,#已经拆掉
    '卸载中':5,}#正在卸载
#完整公开阶段。已拆除对外是 null，不报阶段名
纤程阶段对照={纤程状态数值['等待']:'pending',#pending
    纤程状态数值['加载中']:'loading',#loading
    纤程状态数值['已激活']:'active',#active
    纤程状态数值['失败']:'failed',#failed
    纤程状态数值['已拆除']:None,#已处置
    纤程状态数值['卸载中']:'unloading',}#unloading

def 插件条目标识(原文):
    '在拥有边界把 Loader 树写出的条目 id 标成清单条目 id'
    return 原文#运行时仍是原字符串

def 读取插件清单(上下文):
    '读取当前 Loader 条目与可选预设组合。没有单独的运行时缓存'
    #非 group 条目，按加载器遍历顺序
    条目列表=[]#快照里的条目
    包表=上下文.获取服务('pluginPackages')#可选包表
    加载器=上下文.加载器#已注入的加载器
    for 条目 in 加载器.列出插件配置():#逐条
        if 条目.选项.get('group'):#组行不进入清单
            continue#跳过
        基础=条目.父组.所属树.所属上下文.基准网址#本树基准
        if 基础 is None or 包表 is None:#缺基准或包表
            展示元=None#不读展示元
        else:#两侧都在
            展示元=包表.元属于(条目.选项['name'],基础)#不加载插件
        纤程=条目.纤程#根纤程
        if 纤程 is None:#没有活根纤程
            阶段=None#对外 null
        else:#有纤程
            阶段=纤程阶段对照[纤程.状态]#数值对到阶段
        清单行={'entryId':插件条目标识(条目.编号),#带祖先前缀的条目 id
            'moduleName':条目.选项['name'],#加载器导入的模块说明符
            'enabled':not 条目.已禁用,#含禁用祖先组后的有效启用
            'fiberPhase':阶段,}#阶段名；没有纤程或已拆除时为 None
        if 展示元 is not None:#空字典也挂上
            清单行['meta']=展示元#展示元
        条目列表.append(清单行)#收下
    #可选预设组合，以及当前宿主有没有持久管理
    预设=上下文.获取服务('agentPresets')#可选预设名册
    if 上下文.获取服务('pluginManager') is None:#没有管理服务
        管理={}#快照不带该键
    else:#管理服务在场
        管理={'managementAvailable':True}#暴露持久管理
    if 预设 is None:#这套部署没有名册
        return {'entries':条目列表,**管理}#仅条目
    组合列表=预设.组合体库存清单()#各预设的组合行
    智能体预设=[]#投影后的预设组
    根基准=上下文.基准网址#预设行的展示元用这个基准
    for 组合 in 组合列表:#逐个预设
        行列表=[]#投影后的行
        for 组合行 in 组合['rows']:#组合顺序
            if 'fiberState' in 组合行:#活着的根纤程才有这个键
                纤程状态=组合行['fiberState']#0 也是 pending
            else:#没有纤程
                纤程状态=None#对外 null
            投影={}#去掉 fiberState
            for 字段名,字段值 in 组合行.items():#原字段
                if 字段名=='fiberState':#改记成 fiberPhase
                    continue#不复制
                投影[字段名]=字段值#entryId、moduleName、enabled、condition 原样留下
            if 纤程状态 is None:#没有数值
                投影['fiberPhase']=None#null
            else:#有数值
                投影['fiberPhase']=纤程阶段对照[纤程状态]#阶段名
            if 根基准 is not None and 包表 is not None:#根基准和包表都在
                行展示元=包表.元属于(组合行['moduleName'],根基准)#不加载插件
                if 行展示元 is not None:#空字典也保留
                    投影['meta']=行展示元#展示元
            行列表.append(投影)#收下
        智能体预设.append({**组合,'rows':行列表})#其余字段原样，行换成投影
    return {'entries':条目列表,'agentPresets':智能体预设,**管理}#快照

class 插件清单网关(远程服务):
    '只远程暴露加载器当前非 group 条目状态'
    inject=['加载器']#上游槽名是 loader。中文加载器登记的服务名是加载器

    def __init__(自身,上下文,配置值=None):
        '以 pluginInventory 登记。加载器传入的配置本服务不读'
        super().__init__(上下文,'pluginInventory')#远程服务键

    @远程('list')
    def list(自身):
        '每次调用直接读加载器，不另做缓存'
        return 读取插件清单(自身.所属上下文)#当前快照

default=插件清单网关#类插件默认导出
