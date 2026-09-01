"""一个已打开的 SQLite KV 单元。"""
import json#值列 JSON
from ..存储.错误 import 存储错误#存储错误
from .结构 import 记录表名#物理表名
__all__=['SqliteKv单元']#仅中文公开名

class SqliteKv单元:#SQLite KvUnit
    def __init__(自身,连接,描述符,关闭回调):#构造
        自身._连接=连接#库连接
        自身._描述符=描述符#描述符
        自身._关闭回调=关闭回调#释放槽
        自身._已关=False#关闭旗标
        自身._sql={}#表 SQL 缓存
        for 表 in 描述符.tables:#每张表
            物理=记录表名(描述符.name,表)#物理名
            自身._sql[表]={#SQL 文本
                'upsert':f'INSERT INTO "{物理}" (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value',
                'remove':f'DELETE FROM "{物理}" WHERE key = ?',
                'selectAll':f'SELECT key, value FROM "{物理}"',
            }#缓存
        if 描述符.hasGlobal:#全局语句
            自身._全局写入='INSERT INTO unit_globals (unit, value) VALUES (?, ?) ON CONFLICT(unit) DO UPDATE SET value = excluded.value'#upsert
            自身._全局读取='SELECT value FROM unit_globals WHERE unit = ?'#select
        else:#无全局
            自身._全局写入=None#无
            自身._全局读取=None#无
    async def loadAll(自身):#读全快照
        return await 自身._结算(自身._加载全部同步)#包装同步
    def _加载全部同步(自身):#同步加载
        表={}#结果表
        for 表名,sql in 自身._sql.items():#每张表
            记录={}#记录 dict
            for 键,值文本 in 自身._连接.execute(sql['selectAll']):#全表扫描
                记录[键]=自身._解析值(值文本,f"table '{表名}' key '{键}'")#解析 JSON
            表[表名]=记录#记下
        全局=None#默认无
        if 自身._全局读取 is not None:#有全局
            行=自身._连接.execute(自身._全局读取,(自身._描述符.name,)).fetchone()#查全局
            if 行 is not None:#有行
                全局=自身._解析值(行[0],'global slot')#解析
        return {'tables':表,'global':全局}#快照
    async def putRecord(自身,表,键,值):#写记录
        def 操作():#同步写
            自身._连接.execute(自身._sql[表]['upsert'],(键,json.dumps(值,ensure_ascii=False)))#upsert
        return await 自身._结算(操作)#包装
    async def deleteRecord(自身,表,键):#删记录
        def 操作():#同步删
            自身._连接.execute(自身._sql[表]['remove'],(键,))#delete
        return await 自身._结算(操作)#包装
    async def setGlobal(自身,值):#写全局
        def 操作():#同步写全局
            if 自身._全局写入 is None:#未声明
                raise Exception(f"kv unit '{自身._描述符.name}' declared no global slot")#调用方错误
            自身._连接.execute(自身._全局写入,(自身._描述符.name,json.dumps(值,ensure_ascii=False)))#upsert
        return await 自身._结算(操作)#包装
    async def close(自身):#关闭单元
        if not 自身._已关:#首次
            自身._已关=True#标记
            自身._关闭回调()#释放槽
        return None#已决议
    def _解析值(自身,文本,槽):#解析 value 列
        try:#JSON 解析
            return json.loads(文本)#解析
        except json.JSONDecodeError as 错误:#坏 JSON
            raise 存储错误('malformed-medium',f"kv unit '{自身._描述符.name}' holds unparsable JSON at {槽}",原因=错误) from 错误#损坏
    async def _结算(自身,操作):#同步原语包成 async
        try:#跑操作
            自身._确保打开()#关闭守卫
            操作()#同步执行
            自身._连接.commit()#提交写
            return None#无返回值
        except Exception as 错误:#失败
            if isinstance(错误,Exception):#真异常
                raise 错误#原样抛
            raise Exception(str(错误)) from 错误#包装
    def _确保打开(自身):#打开守卫
        if 自身._已关:#已关
            raise 存储错误('closed',f"kv unit '{自身._描述符.name}' is closed")#拒绝
