"""域数据形态（`ctx.storage.domain`）：schema 校验、会发出变更事件的 KV 域。

域层的唯一实现——消费方依赖本包，从不直接碰后端。公开面仅中文名。
"""
from ...依赖 import schemastery#配置校验
from ..存储 import 存储后端服务键#后端服务键
from .错误 import 域错误#域错误
from .规范 import 定义域,域表,描述符投影#spec 工厂
from .域 import 域实现#域实现
__all__=[#仅中文公开名
    '域错误','定义域','域表','描述符投影','域设施',
    '名称','注入','配置模式','应用','apply',
]#公开面结束

名称='storage-domain'#Cordis 插件名
注入=['storage']#依赖 storage 枢纽

配置模式=schemastery.对象字段({
    'backend':schemastery.字符串字段(),#默认后端必填
    'routes':schemastery.字典字段(schemastery.字符串字段()).default({}),#按域路由
})#配置模式结束

def _解析记录(域名,表,键,解析):#跑一次 schema 解析
    try:#解析
        return 解析()#跑 schema
    except Exception as 错误:#schema 失败
        槽位='global' if 表=='' else f"record '{键}' in table '{表}'"#槽位描述
        raise 域错误('invalid-record',f"domain '{域名}': stored {槽位} does not match its schema",{'table':表,'key':键},错误)#invalid-record

class 域设施:#已挂载的域设施
    """在已路由后端上打开已声明域；强制每个域名只能开一次。"""
    def __init__(自身,上下文对象,配置):#构造设施
        自身._上下文=上下文对象#插件上下文
        自身._配置=配置#已校验配置
        自身._域={}#已打开域
        自身._预留=set()#预留名

    async def open(自身,spec):#打开一个已声明域
        """打开一个已声明域。"""
        if spec['name'] in 自身._预留:#名字已预留
            raise 域错误('already-open',f"domain '{spec['name']}' is already open")#已打开
        自身._预留.add(spec['name'])#预留名字
        try:#打开流程
            后端名=自身._配置.get('routes',{}).get(spec['name'],自身._配置['backend'])#解析后端名
            后端=自身._上下文.storage.backend.get(后端名)#取后端
            if 后端.kv is None:#没有 kv 面
                raise 域错误('facet-unsupported',f"backend '{后端名}' routed for domain '{spec['name']}' has no kv facet")#facet 不支持
            单元=await 后端.kv.open(描述符投影(spec))#打开单元
            try:#加载并构造
                快照=await 单元.loadAll()#加载全部
                表记录={}#已校验表
                for 表名,表spec in spec['tables'].items():#每张表
                    记录={}#本表记录
                    for 键,原始 in (快照['tables'].get(表名,{}) or {}).items():#每条原始记录
                        记录[键]=_解析记录(spec['name'],表名,键,lambda:表spec['valueSchema'].parse(原始) if hasattr(表spec['valueSchema'],'parse') else 原始)#校验后放入
                    表记录[表名]=记录#记下本表
                全局spec=spec.get('global')#全局 spec
                if 全局spec is None:#未声明全局
                    全局值=None#无全局
                elif 快照['global'] is None:#从未写入
                    全局值=全局spec['initial']#用 initial
                else:#有已存全局
                    全局值=_解析记录(spec['name'],'','',lambda:全局spec['schema'].parse(快照['global']) if hasattr(全局spec['schema'],'parse') else 快照['global'])#校验
                def 关闭钩子():#关闭钩子
                    自身._域.pop(spec['name'],None)#从表删除
                    自身._预留.discard(spec['name'])#释放预留
                域=域实现(自身._上下文,spec,单元,表记录,全局值,关闭钩子)#构造域
                自身._域[spec['name']]=域#登记已打开域
                return 域#返回类型化句柄
            except BaseException as 错误:#加载或构造失败
                await 单元.close()#关掉刚打开的单元
                raise 错误#原样抛出
        except BaseException as 错误:#整次 open 失败
            自身._预留.discard(spec['name'])#释放预留
            raise 错误#原样抛出

    def get(自身,名称):#按名取已打开域
        return 自身._域.get(名称)#查表

    async def closeAll(自身):#关闭全部域
        await __import__('asyncio').gather(*[域.close() for 域 in list(自身._域.values())])#并行关

def 应用(上下文对象,配置):#安装域形态
    """把域数据形态挂到存储枢纽上。"""
    后端列表=list({配置['backend'],*配置.get('routes',{}).values()})#去重后端
    后端服务=[存储后端服务键(名称) for 名称 in 后端列表]#转服务键
    def 安装(域上下文):#注入后端后挂载
        设施=域设施(域上下文,配置)#构造设施
        def 挂载():#挂载 effect
            卸载=域上下文.storage.mount('domain',设施)#挂到枢纽
            async def 拆除():#拆除
                await 设施.closeAll()#关全部域
                卸载()#卸形态
            return 拆除#返回 disposer
        域上下文.effect(挂载)#登记 effect
        域上下文.provide('storageDomain',设施)#提供服务
    上下文对象.inject(后端服务,安装)#等后端就绪后安装

apply=应用#Cordis 插件入口
