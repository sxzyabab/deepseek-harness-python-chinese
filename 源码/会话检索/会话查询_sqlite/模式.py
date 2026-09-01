"""一次性会话全文只读模型的 SQLite 模式。对齐上游 `session-query-sqlite/src/schema.ts`。"""
import os,sqlite3#路径与 sqlite3
__all__=[
    '会话查询sqlite应用标识','SESSION_QUERY_SQLITE_APPLICATION_ID',
    '会话查询sqlite模式版本','SESSION_QUERY_SQLITE_SCHEMA_VERSION',
    '日志模式','打开检索数据库',
]#公开面

会话查询sqlite模式版本=8#当前派生索引模式版本
SESSION_QUERY_SQLITE_SCHEMA_VERSION=会话查询sqlite模式版本#上游名
会话查询sqlite应用标识=0x44534851#应用 id，防止误重置无关库
SESSION_QUERY_SQLITE_APPLICATION_ID=会话查询sqlite应用标识#上游名
日志模式=('wal','delete','truncate','persist')#支持的 journal 模式
派生用户表=set([
    'search_state','persisted_sessions','persisted_docs',
    'persisted_docs_data','persisted_docs_idx','persisted_docs_content',
    'persisted_docs_docsize','persisted_docs_config',
])#派生索引允许的用户表

def _创建数据库文件(路径):#独占创建缺失库文件
    """独占创建缺失库文件；已存在则保留 mode。"""
    try:#wx 创建
        描述符=os.open(路径,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)#仅所有者
        os.close(描述符)#关掉
    except FileExistsError:#已存在
        pass#保留已有 mode
    except OSError as 错误:#其它错
        if getattr(错误,'errno',None)!=17:#非 EEXIST
            raise 错误#原样抛

def _列出用户表(连接):#列出非 sqlite_ 表
    """列出非 sqlite_ 前缀的用户表。"""
    行们=连接.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT GLOB 'sqlite_*' ORDER BY name",
    ).fetchall()#查表
    return [行[0] for 行 in 行们]#表名列表

def _断言派生用户表(路径,用户表们):#拒绝未知用户表
    """拒绝带未知用户表的派生索引。"""
    未知=[名称 for 名称 in 用户表们 if 名称 not in 派生用户表]#未知表
    if len(未知)>0:#有未知
        raise Exception(f'session-search database at "{路径}" has unrecognized user tables: {", ".join(未知)}')#拒绝

def _引用标识符(值):#SQL 标识符引用
    """SQL 标识符引用。"""
    return f'"{值.replace(chr(34), chr(34)+chr(34))}"'#双引号转义

def _重置派生模式(连接,用户表们):#丢弃不兼容派生表
    """丢弃不兼容派生表。"""
    for 名称 in 用户表们:#逐表
        连接.execute(f'DROP TABLE IF EXISTS {_引用标识符(名称)}')#删表
    连接.execute('PRAGMA user_version = 0')#清版本

def _确保持久模式(连接):#持久层 schema
    """创建/校验持久层 schema。"""
    连接.execute(f'PRAGMA application_id = {会话查询sqlite应用标识}')#盖应用 id
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
    连接.execute(f'PRAGMA user_version = {会话查询sqlite模式版本}')#盖版本

def _确保临时模式(连接):#连接级临时 schema
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

def 打开检索数据库(路径,日志模式值='wal'):#打开并初始化检索库
    """
    打开、校验并初始化持久与连接级临时 schema。
    :param 路径: 专用派生索引路径或 `:memory:`；缺失文件系统路径按仅所有者创建。
    :param 日志模式值: 已校验的 SQLite journal 模式。
    :returns: 由检索服务拥有的已初始化数据库连接。
    """
    if 日志模式值 not in 日志模式:#非法 journal
        raise Exception(f'session-query-sqlite: invalid journalMode {日志模式值!r}')#配置错误
    实际=路径 if 路径==':memory:' else os.path.abspath(路径)#规范路径
    if 实际!=':memory:':#文件库
        os.makedirs(os.path.dirname(实际) or '.',mode=0o700,exist_ok=True)#建父目录
        _创建数据库文件(实际)#独占创建
    连接=sqlite3.connect(实际,check_same_thread=False)#打开连接
    连接.row_factory=sqlite3.Row#行映射
    try:#校验与初始化
        应用行=连接.execute('PRAGMA application_id').fetchone()#读应用 id
        版本行=连接.execute('PRAGMA user_version').fetchone()#读 user_version
        应用id=应用行[0] if 应用行 is not None else 0#application_id
        版本=版本行[0] if 版本行 is not None else 0#user_version
        用户表们=_列出用户表(连接)#列用户表
        if 应用id!=0 and 应用id!=会话查询sqlite应用标识:#别的应用
            raise Exception(f'session-search database at "{实际}" belongs to another application')#拒绝
        if 应用id==0 and len(用户表们)>0:#非空且未标记
            raise Exception(f'session-search database at "{实际}" is not an empty or recognized derived index')#拒绝
        if 应用id==会话查询sqlite应用标识:#已标记派生库
            _断言派生用户表(实际,用户表们)#只允许派生表
            if 版本!=会话查询sqlite模式版本:#版本不兼容
                _重置派生模式(连接,用户表们)#原地重置
        连接.execute(f'PRAGMA journal_mode = {日志模式值.upper()}')#journal（校验后才改）
        _确保持久模式(连接)#持久 schema
        _确保临时模式(连接)#临时 schema
        连接.commit()#提交
        return 连接#返回句柄
    except BaseException as 错误:#打开失败
        连接.close()#关连接
        raise 错误#再抛
