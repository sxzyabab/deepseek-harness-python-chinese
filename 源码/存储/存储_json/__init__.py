"""JSON 存储后端：在配置根下以原子整文件重写发布人类可读文档。

对齐上游 `@deepseek-ai/dsh-storage-json`。在存储枢纽上注册为后端 `json`。
"""
import asyncio,os#异步与路径
from ...依赖 import schemastery#配置
字符串字段=schemastery.字符串字段#字符串配置
对象字段=schemastery.对象字段#对象配置
from ..存储.错误 import 存储错误#存储错误
from ..存储.后端 import 单元名正则,存储后端,键值面#后端词汇
from ..存储 import 存储后端服务键#生命周期键
from .单单元 import 打开单单元#single 布局
from .按记录单元 import 打开按记录单元#per-record 布局
__all__=['Json存储后端','名称','注入','配置','配置模式','应用','apply']#仅中文公开名

名称='storage-json'#Cordis 插件名
注入=['storage']#依赖 storage 枢纽

配置模式=对象字段({'root':字符串字段().required()})#必填根目录
配置=配置模式#中文别名
Config=配置模式#上游名

def _校验描述符(描述符):#校验单元与表名
    if 单元名正则.fullmatch(描述符.name) is None:#单元名非法
        raise 存储错误('malformed-medium',f"invalid unit name '{描述符.name}'")#拒绝
    for 表 in 描述符.tables:#每张表
        if 单元名正则.fullmatch(表) is None:#表名非法
            raise 存储错误('malformed-medium',f"invalid table name '{表}' in unit '{描述符.name}'")#拒绝

class _键值面(键值面):#JSON 后端 KV 面
    def __init__(自身,后端):#绑定后端
        自身._后端=后端#宿主后端
    async def open(自身,描述符):#打开单元
        return await 自身._后端._打开(描述符)#委托

class Json存储后端(存储后端):#JSON 存储后端
    """拥有文件树根并服务 `kv` 面。"""
    def __init__(自身,根):#记下根目录
        super().__init__()#初始化后端
        自身._根=根#根路径
        自身.kv=_键值面(自身)#KV 面
        自身._已打开={}#已打开单元
        自身._打开中={}#在途打开
        自身._已关=False#关闭旗标
    async def _打开(自身,描述符):#实际打开
        if 自身._已关:#已关
            raise 存储错误('closed','json backend is closed')#拒绝
        _校验描述符(描述符)#校验名
        if 描述符.name in 自身._已打开 or 描述符.name in 自身._打开中:#双开
            raise Exception(f"unit '{描述符.name}' is already open; a unit has exactly one live handle")#调用方错误
        任务=asyncio.ensure_future(自身._打开单元(描述符))#启动打开
        自身._打开中[描述符.name]=任务#预留槽
        try:#等打开
            return await 任务#返回单元
        finally:#摘掉在途
            自身._打开中.pop(描述符.name,None)#摘掉
    async def _打开单元(自身,描述符):#打开并登记
        os.makedirs(自身._根,mode=0o700,exist_ok=True)#确保根目录
        关闭回调=lambda: 自身._已打开.pop(描述符.name,None)#释放槽
        if getattr(描述符,'layout',None)=='per-record':#per-record
            单元=await 打开按记录单元(描述符,自身._根,关闭回调)#打开目录树
        else:#single 默认
            单元=await 打开单单元(描述符,自身._根,关闭回调)#打开整文件
        if 自身._已关:#打开途中后端关了
            await 单元.close()#关掉刚打开的
            raise 存储错误('closed','json backend is closed')#拒绝
        自身._已打开[描述符.name]=单元#登记
        return 单元#返回
    async def close(自身):#关闭后端
        if not 自身._已关:#首次
            自身._已关=True#标记
        await asyncio.gather(*list(自身._打开中.values()),return_exceptions=True)#等在途打开
        for 单元 in list(自身._已打开.values()):#关每个单元
            await 单元.close()#关闭

def 应用(上下文对象,配置):#注册 json 后端
    """在存储枢纽上注册 `json` 后端。"""
    后端=Json存储后端(配置['root'])#构造后端
    def 副作用():#注册 effect
        注销=上下文对象.storage.backend.register('json',后端)#挂到枢纽
        async def 拆除():#插件拆除
            注销()#先注销
            await 后端.close()#再关后端
        return 拆除#disposer
    上下文对象.effect(副作用)#登记
    上下文对象.provide(存储后端服务键('json'),后端)#提供生命周期服务
    return None#无额外返回

apply=应用#Cordis 插件入口
