"""SQLite 存储后端：一个数据库文件托管所有被路由单元。

注册为后端 `sqlite`。
"""
from ..存储.错误 import 存储错误#存储错误
from ..存储.后端 import 单元名正则,存储后端,键值面#后端词汇
from ..存储 import 存储后端服务键#生命周期键
from .结构 import 打开数据库,记录表名,存储_SQLITE_结构版本,日志模式#打开库
from .单元 import SqliteKv单元#KV 单元
from ...依赖.schemastery import 字符串字段,字典字段#配置

名称='storage-sqlite'#框架 插件名
依赖=['storage']#依赖 storage 枢纽
配置模式=字典字段(字典结构={
    'path':字符串字段(),#数据库路径
    'journalMode':字符串字段(默认值='wal'),#journal 模式；打开时校验
})#配置模式结束
配置=配置模式#中文配置

class 键值面实现(键值面):#SQLite KV 面
    """SQLite KV 面。"""
    def __init__(自身,后端):#绑定后端
        """绑定后端。"""
        自身._后端=后端#宿主

    def open(自身,描述符):#打开单元
        """打开单元。"""
        return 自身._后端._打开单元(描述符)#委托

class Sqlite存储后端(存储后端):#SQLite 后端
    """拥有一个 sqlite3 连接与打开单元表。"""
    def __init__(自身,配置值):#构造
        """构造并同步打开库。"""
        super().__init__()#初始化
        自身.kv=键值面实现(自身)#KV 面
        日志=配置值['journalMode'] if 'journalMode' in 配置值 else 'wal'#journal 模式
        自身._连接=打开数据库(配置值['path'],日志)#同步打开库
        自身._单元={}#已打开单元
        自身._已关=False#关闭标志

    def _打开单元(自身,描述符):#打开并物化单元
        """打开并物化单元。"""
        if 自身._已关:#正在或已经关闭
            raise 存储错误('closed','sqlite storage backend is closed')#拒绝
        if 单元名正则.fullmatch(描述符.name) is None:#单元名非法
            raise 存储错误('malformed-medium',"kv unit name '"+描述符.name+"' violates "+单元名正则.pattern)#调用方错误
        for 表 in 描述符.tables:#每张表
            if 单元名正则.fullmatch(表) is None:#表名非法
                raise 存储错误('malformed-medium',"kv table name '"+表+"' in unit '"+描述符.name+"' violates "+单元名正则.pattern)#调用方错误
        if 描述符.name in 自身._单元:#双开
            raise 存储错误('malformed-medium',"kv unit '"+描述符.name+"' is already open (double-open is a caller bug)")#调用方错误
        行=自身._连接.execute('SELECT version FROM units WHERE name = ?',(描述符.name,)).fetchone()#查版本戳
        if 行 is None:#尚未盖戳
            自身._连接.execute('INSERT INTO units (name, version) VALUES (?, ?)',(描述符.name,描述符.version))#插入
        elif 行[0]!=描述符.version:#版本不匹配
            raise 存储错误(
                'version-mismatch',
                "kv unit '"+描述符.name+"' is stamped version "+str(行[0])+" on the medium, incompatible with descriptor version "+str(描述符.version),
            )#拒绝
        for 表 in 描述符.tables:#确保记录表
            物理=记录表名(描述符.name,表)#物理名
            自身._连接.execute(
                'CREATE TABLE IF NOT EXISTS "'+物理+'" (key TEXT PRIMARY KEY, value TEXT NOT NULL) STRICT'
            )#建表
        自身._连接.commit()#提交 DDL
        def 释放():#关闭回调
            """释放单元名。"""
            自身._单元.pop(描述符.name,None)#释放名
        单元=SqliteKv单元(自身._连接,描述符,释放)#构造单元
        自身._单元[描述符.name]=单元#登记
        return 单元#返回

    def close(自身):#关闭后端
        """关闭全部单元并关库。"""
        if 自身._已关:#已关
            return
        自身._已关=True#标记
        for 单元 in list(自身._单元.values()):#关每个单元
            单元.close()#关单元
        自身._连接.close()#关库

def 应用(上下文,配置值):#注册 sqlite 后端
    """在存储枢纽上注册 `sqlite` 后端。"""
    后端=Sqlite存储后端(配置值)#构造后端
    def 副作用():#注册 effect
        """挂到枢纽，拆除时注销并关后端。"""
        注销=上下文.storage.backend.register('sqlite',后端)#挂到枢纽
        def 拆除():#插件拆除
            """先注销再关后端。"""
            注销()#先注销
            后端.close()#再关后端
        return 拆除#disposer
    上下文.副作用(副作用,'storage-sqlite.registerBackend')#带标签登记
    上下文.提供服务(存储后端服务键('sqlite'),后端)#提供生命周期服务
    return None#无额外返回

__all__=[#仅中文公开名
    '存储_SQLITE_结构版本','日志模式','Sqlite存储后端',
    '名称','依赖','配置','配置模式','应用',
]#公开面结束
name=名称#框架插件名
inject=依赖#框架依赖声明
Config=配置模式#框架配置模式
apply=应用#框架插件入口
default=应用#框架默认导出
