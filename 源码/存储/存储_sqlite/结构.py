"""SQLite 存储后端的 schema 与打开时辅助。"""
import os,sqlite3#路径与 sqlite3
from ..存储.错误 import 存储错误#存储错误
__all__=['存储_SQLITE_结构版本','日志模式','打开数据库','记录表名']#仅中文公开名

存储_SQLITE_结构版本=1#物理布局版本
STORAGE_SQLITE_SCHEMA_VERSION=存储_SQLITE_结构版本#上游名
日志模式=('wal','delete','truncate','persist')#允许的 journal 模式

def _创建数据库文件(路径):#独占创建库文件
    try:#wx 创建
        描述符=os.open(路径,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)#独占
        os.close(描述符)#关掉
    except FileExistsError:#已存在
        pass#保留已有 mode
    except OSError as 错误:#其它错
        if getattr(错误,'errno',None)!=17:#非 EEXIST
            raise 错误#原样抛

def _配置数据库(连接,路径,日志模式值):#pragma 与元数据表
    连接.execute('PRAGMA foreign_keys = ON')#外键
    连接.execute(f'PRAGMA journal_mode = {日志模式值.upper()}')#journal
    行=连接.execute('PRAGMA user_version').fetchone()#读版本
    盘上版本=行[0] if 行 is not None else 0#user_version
    if 盘上版本 not in (0,存储_SQLITE_结构版本):#不兼容
        raise 存储错误(
            'version-mismatch',
            f'storage database at "{路径}" has schema version {盘上版本}, incompatible with this build ({存储_SQLITE_结构版本})',
        )#拒绝
    连接.executescript('''
        CREATE TABLE IF NOT EXISTS units (
            name    TEXT PRIMARY KEY,
            version INTEGER NOT NULL
        ) STRICT;
        CREATE TABLE IF NOT EXISTS unit_globals (
            unit  TEXT PRIMARY KEY REFERENCES units(name),
            value TEXT NOT NULL
        ) STRICT;
    ''')#元数据表
    if 盘上版本==0:#新库
        连接.execute(f'PRAGMA user_version = {存储_SQLITE_结构版本}')#盖戳
    连接.commit()#提交

def 打开数据库(路径,日志模式值='wal'):#打开并配置库
    """打开 SQLite 库；`:memory:` 跳过文件系统准备。"""
    if 日志模式值 not in 日志模式:#非法 journal
        raise Exception(f'storage-sqlite: invalid journalMode {日志模式值!r}')#配置错误
    实际=路径 if 路径==':memory:' else os.path.abspath(路径)#规范路径
    if 实际!=':memory:':#文件库
        os.makedirs(os.path.dirname(实际) or '.',mode=0o700,exist_ok=True)#建父目录
        _创建数据库文件(实际)#独占创建
    连接=sqlite3.connect(实际,check_same_thread=False)#打开连接
    try:#配置
        _配置数据库(连接,实际,日志模式值)#pragma 与表
        return 连接#返回句柄
    except BaseException as 错误:#配置失败
        连接.close()#关连接
        raise 错误#再抛

def 记录表名(单元,表):#物理记录表名
    return f'u_{单元}_{表}'#u_<unit>_<table>
