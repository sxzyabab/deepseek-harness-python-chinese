"""一次性会话全文只读模型的 SQLite 模式。"""
import os,sqlite3#路径与 sqlite3
__all__=[
    '会话查询sqlite应用标识',
    '会话查询sqlite模式版本',
    '会话查询sqlite错误',
    '日志模式','打开检索数据库',
]#公开面

会话查询sqlite模式版本=8#当前派生索引模式版本
会话查询sqlite应用标识=0x44534851#应用 id，防止误重置无关库
日志模式=('wal','delete','truncate','persist')#支持的 journal 模式
派生用户表=set([
    'search_state','persisted_sessions','persisted_docs',
    'persisted_docs_data','persisted_docs_idx','persisted_docs_content',
    'persisted_docs_docsize','persisted_docs_config',
])#派生索引允许的用户表

class 会话查询sqlite错误(Exception):
    """会话查询 sqlite 模式包的异常基类。"""

def 创建数据库文件(路径):
    """独占创建缺失库文件；已存在则保留 mode。"""
    try:#wx 创建
        描述符=os.open(路径,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)#仅所有者
        os.close(描述符)#关掉
    except FileExistsError:#已存在
        pass#保留已有 mode
    except OSError as 错误:#其它错
        if getattr(错误,'errno',None)!=17:#非 EEXIST
            raise 错误#原样抛

def 列出用户表(连接):
    """列出非 sqlite_ 前缀的用户表。"""
    行列表=连接.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT GLOB 'sqlite_*' ORDER BY name",
    ).fetchall()#查表
    名称列表=[]#表名列表
    for 行 in 行列表:#逐行
        名称列表.append(行[0])#表名
    return 名称列表#表名列表

def 校验派生用户表(路径,用户表列表):
    """拒绝带未知用户表的派生索引。"""
    未知=[]#未知表
    for 名称 in 用户表列表:#逐表
        if 名称 not in 派生用户表:#未知
            未知.append(名称)#收集
    if len(未知)>0:#有未知
        raise 会话查询sqlite错误('session-search database at "'+路径+'" has unrecognized user tables: '+', '.join(未知))#拒绝

def 引用标识符(值):
    """SQL 标识符引用。"""
    引号=chr(34)#双引号
    return 引号+值.replace(引号,引号+引号)+引号#双引号转义

def 重置派生模式(连接,用户表列表):
    """丢弃不兼容派生表。"""
    for 名称 in 用户表列表:#逐表
        连接.execute('DROP TABLE IF EXISTS '+引用标识符(名称))#删表
    连接.execute('PRAGMA user_version = 0')#清版本

def 确保持久模式(连接):
    """创建/校验持久层 schema。"""
    连接.execute('PRAGMA application_id = '+str(会话查询sqlite应用标识))#盖应用 id
    连接.executescript('''
        CREATE TABLE IF NOT EXISTS search_state (
            singleton         INTEGER PRIMARY KEY CHECK (singleton = 1),
            global_generation INTEGER NOT NULL
        ) STRICT;
        INSERT OR IGNORE INTO search_state (singleton, global_generation) VALUES (1, 0);
        CREATE TABLE IF NOT EXISTS persisted_sessions (
            id             TEXT PRIMARY KEY,
            version        INTEGER NOT NULL,
            created_at     INTEGER NOT NULL,
            cwd            TEXT,
            parent_session TEXT,
            seed_length    INTEGER,
            delegation_depth INTEGER,
            agent_preset  TEXT,
            revision       TEXT NOT NULL,
            generation     INTEGER NOT NULL
        ) STRICT;
        CREATE VIRTUAL TABLE IF NOT EXISTS persisted_docs USING fts5(
            text,
            session_id UNINDEXED,
            seq UNINDEXED,
            type UNINDEXED,
            time UNINDEXED,
            surface UNINDEXED,
            codepoint_length UNINDEXED,
            tokenize = 'unicode61'
        );
    ''')#持久表
    连接.execute('PRAGMA user_version = '+str(会话查询sqlite模式版本))#盖版本

def 确保临时模式(连接):
    """创建/校验连接级临时 schema。"""
    连接.executescript('''
        CREATE TEMP TABLE IF NOT EXISTS live_sessions (
            id             TEXT PRIMARY KEY,
            version        INTEGER NOT NULL,
            created_at     INTEGER NOT NULL,
            cwd            TEXT,
            parent_session TEXT,
            seed_length    INTEGER,
            delegation_depth INTEGER,
            agent_preset  TEXT,
            fingerprint    TEXT NOT NULL,
            persisted      INTEGER NOT NULL CHECK (persisted IN (0, 1)),
            generation     INTEGER NOT NULL
        ) STRICT;
        CREATE VIRTUAL TABLE IF NOT EXISTS temp.live_docs USING fts5(
            text,
            session_id UNINDEXED,
            seq UNINDEXED,
            type UNINDEXED,
            time UNINDEXED,
            surface UNINDEXED,
            codepoint_length UNINDEXED,
            tokenize = 'unicode61'
        );
    ''')#临时表

def 打开检索数据库(路径,日志模式值='wal'):
    """打开、校验并初始化持久与连接级临时 schema。"""
    if 日志模式值 not in 日志模式:#非法 journal
        raise 会话查询sqlite错误('session-query-sqlite: invalid journalMode '+repr(日志模式值))#配置错误
    if 路径==':memory:':#内存库
        实际=路径#原样
    else:#文件库
        实际=os.path.abspath(路径)#规范路径
    if 实际!=':memory:':#文件库
        os.makedirs(os.path.dirname(实际) or '.',mode=0o700,exist_ok=True)#建父目录
        创建数据库文件(实际)#独占创建
    连接=sqlite3.connect(实际,check_same_thread=False)#打开连接
    连接.row_factory=sqlite3.Row#行映射
    try:#校验与初始化
        应用行=连接.execute('PRAGMA application_id').fetchone()#读应用 id
        版本行=连接.execute('PRAGMA user_version').fetchone()#读 user_version
        if 应用行 is not None:#有行
            应用id=应用行[0]#application_id
        else:#缺席
            应用id=0#零
        if 版本行 is not None:#有行
            版本=版本行[0]#user_version
        else:#缺席
            版本=0#零
        用户表列表=列出用户表(连接)#列用户表
        if 应用id!=0 and 应用id!=会话查询sqlite应用标识:#别的应用
            raise 会话查询sqlite错误('session-search database at "'+实际+'" belongs to another application')#拒绝
        if 应用id==0 and len(用户表列表)>0:#非空且未标记
            raise 会话查询sqlite错误('session-search database at "'+实际+'" is not an empty or recognized derived index')#拒绝
        if 应用id==会话查询sqlite应用标识:#已标记派生库
            校验派生用户表(实际,用户表列表)#只允许派生表
            if 版本!=会话查询sqlite模式版本:#版本不兼容
                重置派生模式(连接,用户表列表)#原地重置
        连接.execute('PRAGMA journal_mode = '+日志模式值.upper())#journal（校验后才改）
        确保持久模式(连接)#持久 schema
        确保临时模式(连接)#临时 schema
        连接.commit()#提交
        return 连接#返回句柄
    except BaseException as 错误:#打开失败含 KeyboardInterrupt，必须关连接
        连接.close()#关连接
        raise 错误#再抛
