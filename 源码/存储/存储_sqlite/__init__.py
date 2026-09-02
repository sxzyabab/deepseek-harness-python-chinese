"""SQLite 存储后端：一个数据库文件托管所有被路由单元。

对齐上游 `@deepseek-ai/dsh-storage-sqlite`。注册为后端 `sqlite`。
"""
import asyncio#异步打开与关闭
from ...依赖.schemastery import 字符串字段,字典字段#配置
from ..存储.错误 import 存储错误#存储错误
from ..存储.后端 import 单元名正则,存储后端,键值面#后端词汇
from ..存储 import 存储后端服务键#生命周期键
from .结构 import 打开数据库,记录表名,存储_SQLITE_结构版本,日志模式#打开库
from .单元 import SqliteKv单元#KV 单元
__all__=[#仅中文公开名
    '存储_SQLITE_结构版本','日志模式','Sqlite存储后端',
    '名称','注入','配置','配置模式','应用','apply',
    'STORAGE_SQLITE_SCHEMA_VERSION','JournalMode',
]#公开面结束

STORAGE_SQLITE_SCHEMA_VERSION=存储_SQLITE_结构版本#上游名
JournalMode=日志模式#上游类型锚

名称='storage-sqlite'#Cordis 插件名
注入=['storage']#依赖 storage 枢纽

配置模式=字典字段({
    'path':字符串字段(),#数据库路径
    'journalMode':字符串字段(默认值='wal'),#journal 模式；打开时校验
})#配置模式结束
配置=配置模式#中文别名
Config=配置模式#上游名

class _键值面(键值面):#SQLite KV 面
    def __init__(自身,后端):#绑定后端
        自身._后端=后端#宿主
    async def open(自身,描述符):#打开单元
        return await 自身._后端._打开单元(描述符)#委托

class Sqlite存储后端(存储后端):#SQLite 后端
    """拥有一个 sqlite3 连接与打开单元表。"""
    def __init__(自身,配置):#构造
        super().__init__()#初始化
        自身.kv=_键值面(自身)#KV 面
        自身._就绪=asyncio.to_thread(打开数据库,配置['path'],配置.get('journalMode','wal'))#异步打开库
        自身._单元={}#打开中/已打开单元
        自身._关闭中=None#关闭承诺
    async def _打开单元(自身,描述符):#打开并物化单元
        if 自身._关闭中 is not None:#正在或已经关闭
            raise 存储错误('closed','sqlite storage backend is closed')#拒绝
        if 单元名正则.fullmatch(描述符.name) is None:#单元名非法
            raise Exception(f"kv unit name '{描述符.name}' violates {单元名正则.pattern}")#调用方错误
        for 表 in 描述符.tables:#每张表
            if 单元名正则.fullmatch(表) is None:#表名非法
                raise Exception(f"kv table name '{表}' in unit '{描述符.name}' violates {单元名正则.pattern}")#调用方错误
        if 描述符.name in 自身._单元:#双开
            raise Exception(f"kv unit '{描述符.name}' is already open (double-open is a caller bug)")#调用方错误
        任务=asyncio.ensure_future(自身._物化单元(描述符))#启动物化
        自身._单元[描述符.name]=任务#同步预留名
        任务.add_done_callback(lambda 未来,名=描述符.name: 自身._单元.pop(名,None) if 未来.exception() else None)#失败释放
        return await 任务#等物化
    async def _物化单元(自身,描述符):#物化记录表并构造单元
        连接=await 自身._就绪#等库打开
        行=连接.execute('SELECT version FROM units WHERE name = ?',(描述符.name,)).fetchone()#查版本戳
        if 行 is None:#尚未盖戳
            连接.execute('INSERT INTO units (name, version) VALUES (?, ?)',(描述符.name,描述符.version))#插入
        elif 行[0]!=描述符.version:#版本不匹配
            raise 存储错误(
                'version-mismatch',
                f"kv unit '{描述符.name}' is stamped version {行[0]} on the medium, incompatible with descriptor version {描述符.version}",
            )#拒绝
        for 表 in 描述符.tables:#确保记录表
            物理=记录表名(描述符.name,表)#物理名
            连接.execute(f'''
                CREATE TABLE IF NOT EXISTS "{物理}" (
                    key   TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                ) STRICT
            ''')#建表
        连接.commit()#提交 DDL
        def 释放():#关闭回调
            自身._单元.pop(描述符.name,None)#释放名
        return SqliteKv单元(连接,描述符,释放)#构造单元
    async def close(自身):#关闭后端
        if 自身._关闭中 is None:#首次
            自身._关闭中=asyncio.ensure_future(自身._执行关闭())#启动拆除
        await 自身._关闭中#等拆除
    async def _执行关闭(自身):#实际拆除
        try:#等库打开
            连接=await 自身._就绪#取连接
        except Exception:#介质从未打开
            return#无物可释
        for 任务 in list(自身._单元.values()):#关每个单元
            try:#等物化
                单元=await 任务#取单元
            except Exception:#物化失败
                continue#跳过
            await 单元.close()#关单元
        连接.close()#关库

def 应用(上下文对象,配置):#注册 sqlite 后端
    """在存储枢纽上注册 `sqlite` 后端。"""
    后端=Sqlite存储后端(配置)#构造后端
    def 副作用():#注册 effect
        注销=上下文对象.storage.backend.register('sqlite',后端)#挂到枢纽
        async def 拆除():#插件拆除
            注销()#先注销
            await 后端.close()#再关后端
        return 拆除#disposer
    上下文对象.effect(副作用,'storage-sqlite.registerBackend')#带标签登记
    上下文对象.provide(存储后端服务键('sqlite'),后端)#提供生命周期服务
    return None#无额外返回

apply=应用#Cordis 插件入口
