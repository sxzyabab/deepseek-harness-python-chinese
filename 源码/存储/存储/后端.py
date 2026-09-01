"""存储枢纽面向后端的词汇与规范约定。"""
import re#正则
__all__=[#仅中文公开名
    '单元名正则','存储后端','键值面','键值单元描述符','键值单元',
]#公开面结束

单元名正则=re.compile(r'^[a-z][a-z0-9_]*$')#单元名和表名允许格式

class 键值单元:#已打开单元协议（结构约定）
    """一个已打开单元。对本层而言值是不透明 JSON：无 schema、无事件、无域含义。"""
    async def loadAll(自身):#读取当前完整快照
        raise NotImplementedError('KvUnit.loadAll')#子类实现
    async def putRecord(自身,表,键,值):#耐久 upsert 一条记录
        raise NotImplementedError('KvUnit.putRecord')#子类实现
    async def deleteRecord(自身,表,键):#耐久删除一条记录
        raise NotImplementedError('KvUnit.deleteRecord')#子类实现
    async def setGlobal(自身,值):#耐久写入全局单例
        raise NotImplementedError('KvUnit.setGlobal')#子类实现
    async def close(自身):#排空并释放单元
        raise NotImplementedError('KvUnit.close')#子类实现

class 键值面:#键值数据形态
    """键值数据形态：整单元快照加上按记录的耐久写入。"""
    async def open(自身,描述符):#打开一个单元
        raise NotImplementedError('KvFacet.open')#子类实现

class 存储后端:#一个已注册后端
    """一个已注册后端。后端恰好拥有一份介质，生命周期由所有面共享。"""
    def __init__(自身):#初始化可选键值面
        自身.kv=None#键值面；不能服务时缺席
    async def close(自身):#释放介质
        raise NotImplementedError('StorageBackend.close')#子类实现

class 键值单元描述符:#一个 KV 单元的静态身份与形态
    """一个 KV 单元的静态身份与形态，从其拥有方 spec 投影。"""
    def __init__(自身,名称,版本,表列表,有全局,布局=None):#构造描述符
        自身.name=名称#单元名
        自身.version=版本#单元格式版本
        自身.tables=表列表#表名列表
        自身.hasGlobal=有全局#是否携带全局单例槽
        自身.layout=布局#介质布局：single 或 per-record
