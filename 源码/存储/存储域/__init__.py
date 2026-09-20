"""域数据形态：带 schema 校验、会发出变更事件的 KV 域。

消费方只依赖本包，不直接碰后端。
"""
from ...依赖.schemastery import 字典字段,字符串字段#配置校验
from ..存储 import 存储后端服务键#后端服务键
from .错误 import 域错误#域错误
from .规范 import 定义域,域表,描述符投影#spec 工厂
from .域 import 域实现#域实现

名称='storage-domain'#框架 插件名
依赖=['storage']#依赖 storage 枢纽
配置模式=字典字段(字典结构={
    'backend':字符串字段(),#默认后端必填
    'routes':字典字段(键值结构=(字符串字段(),字符串字段()),默认值={}),#按域路由
})#配置模式结束

def 解析记录(域名,表,键,解析):#跑一次 schema 解析
    """跑一次 schema 解析。"""
    try:#解析
        return 解析()#跑 schema
    except BaseException as 错误:#schema 失败
        槽位='global' if 表=='' else "record '"+键+"' in table '"+表+"'"#槽位描述
        raise 域错误('invalid-record',"domain '"+域名+"': stored "+槽位+' does not match its schema',{'table':表,'key':键},错误)#invalid-record

def 解析表值(表spec,原始):#校验一条表记录
    """校验一条表记录。"""
    模式=表spec['valueSchema']#值模式
    if hasattr(模式,'parse'):#有 parse
        return 模式.parse(原始)#校验
    return 原始#无模式则原样

def 解析全局值(全局spec,原始):#校验已存全局
    """校验已存全局。"""
    模式=全局spec['schema']#全局模式
    if hasattr(模式,'parse'):#有 parse
        return 模式.parse(原始)#校验
    return 原始#无模式则原样

class 域设施:#已挂载的域设施
    """在已路由后端上打开已声明域；强制每个域名只能开一次。"""
    def __init__(自身,上下文,配置):#构造设施
        """记下上下文与配置。配置是 dict。"""
        自身._上下文=上下文#插件上下文
        自身._配置=配置#已校验配置
        自身._域={}#已打开域
        自身._预留=set()#预留名

    def open(自身,spec):#打开一个已声明域
        """打开一个已声明域。spec 是 dict。"""
        if spec['name'] in 自身._预留:#名字已预留
            raise 域错误('already-open',"domain '"+spec['name']+"' is already open")#已打开
        自身._预留.add(spec['name'])#预留名字
        try:#打开流程
            路由=自身._配置['routes'] if 'routes' in 自身._配置 else {}#按域路由
            后端名=路由[spec['name']] if spec['name'] in 路由 else 自身._配置['backend']#解析后端名
            后端=自身._上下文.storage.backend.get(后端名)#取后端
            if 后端.kv is None:#没有 kv 面
                raise 域错误('facet-unsupported',"backend '"+后端名+"' routed for domain '"+spec['name']+"' has no kv facet")#facet 不支持
            单元=后端.kv.open(描述符投影(spec))#打开单元
            try:#加载并构造
                快照=单元.loadAll()#加载全部
                表记录={}#已校验表
                for 表名,表spec in spec['tables'].items():#每张表
                    记录={}#本表记录
                    原始表=快照['tables'][表名] if 表名 in 快照['tables'] else {}#本表原始
                    if 原始表 is None:#缺席当空
                        原始表={}#空
                    for 键,原始 in 原始表.items():#每条原始记录
                        def 解析本条(原始值=原始,规格=表spec):#闭包校验
                            """校验本条记录。"""
                            return 解析表值(规格,原始值)#校验
                        记录[键]=解析记录(spec['name'],表名,键,解析本条)#校验后放入
                    表记录[表名]=记录#记下本表
                全局spec=spec['global'] if 'global' in spec else None#全局 spec
                if 全局spec is None:#未声明全局
                    全局值=None#无全局
                elif 快照['global'] is None:#从未写入
                    全局值=全局spec['initial']#用 initial
                else:#有已存全局
                    def 解析全局():#闭包校验
                        """校验已存全局。"""
                        return 解析全局值(全局spec,快照['global'])#校验
                    全局值=解析记录(spec['name'],'','',解析全局)#校验
                def 关闭钩子():#关闭钩子
                    """从表删除并释放预留。"""
                    自身._域.pop(spec['name'],None)#从表删除
                    自身._预留.discard(spec['name'])#释放预留
                域=域实现(自身._上下文,spec,单元,表记录,全局值,关闭钩子)#构造域
                自身._域[spec['name']]=域#登记已打开域
                return 域#返回类型化句柄
            except BaseException as 错误:#加载或构造失败
                单元.close()#关掉刚打开的单元
                raise 错误#原样抛出
        except BaseException as 错误:#整次 open 失败
            自身._预留.discard(spec['name'])#释放预留
            raise 错误#原样抛出

    def get(自身,名称):#按名取已打开域
        """按名取已打开域。"""
        return 自身._域[名称] if 名称 in 自身._域 else None#查表

    def closeAll(自身):#关闭全部域
        """关闭全部域。"""
        for 域 in list(自身._域.values()):#逐个关
            域.close()#关域

def 应用(上下文,配置):#安装域形态
    """把域数据形态挂到存储枢纽上。"""
    路由=配置['routes'] if 'routes' in 配置 else {}#按域路由
    后端列表=list({配置['backend'],*路由.values()})#去重后端
    后端服务=[存储后端服务键(名称) for 名称 in 后端列表]#转服务键
    def 安装(域上下文):#注入后端后挂载
        """等后端就绪后挂载。"""
        设施=域设施(域上下文,配置)#构造设施
        def 挂载():#挂载 effect
            """挂到枢纽，拆除时关全部域。"""
            卸载=域上下文.storage.mount('domain',设施)#挂到枢纽
            def 拆除():#拆除
                """关全部域再卸形态。"""
                设施.closeAll()#关全部域
                卸载()#卸形态
            return 拆除#返回 disposer
        域上下文.副作用(挂载)#登记副作用
        域上下文.提供服务('storageDomain',设施)#提供服务
    上下文.依赖启动(后端服务,安装)#等后端就绪后安装

__all__=[#仅中文公开名
    '域错误','定义域','域表','描述符投影','域设施',
    '名称','依赖','配置模式','应用',
]#公开面结束
name=名称#框架槽
inject=依赖#框架槽
Config=配置模式#框架槽
apply=应用#框架槽
default=应用#框架槽
