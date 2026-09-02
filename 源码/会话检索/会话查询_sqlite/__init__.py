"""在优先活会话语料上用 SQLite FTS5 做全文检索的具体会话检索服务。对齐上游 `@deepseek-ai/dsh-session-query-sqlite`。"""
import base64,hashlib,json,threading,uuid#编码、哈希、JSON、并发与实例 id
from ...依赖 import cordis#Cordis
from ...依赖.schemastery import 字典字段,字符串字段,枚举字段,整数字段#配置
服务=cordis.服务#Cordis服务基类
from ...模型后端.llm import 结构化克隆#拆离克隆
from ..会话查询 import (
    会话查询引擎,会话查询错误,会话查询默认持久检查并发,会话查询读取窗口上限,
    断言会话头兼容,构建会话事件搜索文档,会话搜索游标,
)#基类与共享
from .模式 import (
    会话查询sqlite应用标识,SESSION_QUERY_SQLITE_APPLICATION_ID,
    会话查询sqlite模式版本,SESSION_QUERY_SQLITE_SCHEMA_VERSION,
    日志模式,打开检索数据库,
)#schema
from .查询 import (
    FTS高亮开始,FTS_HIGHLIGHT_START,FTS高亮结束,FTS_HIGHLIGHT_END,
    SQLITE最大页限制,SQLITE_MAX_PAGE_LIMIT,
    断言可移植绑定数,断言Fts5外层谓词数,
    归一化会话请求,归一化事件请求,
    构建会话Where,构建事件Where,
    引用Fts数据,清洗Fts文本,请求指纹,生成摘要,
)#query

名称='session-query-sqlite'#Cordis插件名
注入=['sessions']#依赖会话服务
会话查询sqlite路径键='launcherSessionQueryPath'#启动器索引路径键
SESSION_QUERY_SQLITE_PATH_KEY=会话查询sqlite路径键#上游名
会话查询sqlite默认页大小=20#默认页大小
SESSION_QUERY_SQLITE_DEFAULT_LIMIT=会话查询sqlite默认页大小#上游名
会话查询sqlite最大页大小=100#最大页大小
SESSION_QUERY_SQLITE_MAX_LIMIT=会话查询sqlite最大页大小#上游名
会话查询sqlite摘要码点=240#默认摘要码点数
SESSION_QUERY_SQLITE_SNIPPET_CHARS=会话查询sqlite摘要码点#上游名
稳定观察尝试次数=2#稳定观察最多尝试次数

配置模式=字典字段({
    'path':字符串字段(),
    'openAt':枚举字段('startup','first-search','never',默认值='startup'),
    'journalMode':枚举字段(*日志模式,默认值='wal'),
    'defaultLimit':整数字段(默认值=会话查询sqlite默认页大小),
    'maxLimit':整数字段(默认值=会话查询sqlite最大页大小),
    'snippetChars':整数字段(默认值=会话查询sqlite摘要码点),
    'readWindowMax':整数字段(默认值=会话查询读取窗口上限),
    'persistedInspectConcurrency':整数字段(默认值=会话查询默认持久检查并发),
})#配置模式

__all__=[
    '名称','注入','配置模式','应用','apply',
    'Sqlite会话查询引擎','会话查询sqlite路径键','SESSION_QUERY_SQLITE_PATH_KEY',
    '会话查询sqlite默认页大小','SESSION_QUERY_SQLITE_DEFAULT_LIMIT',
    '会话查询sqlite最大页大小','SESSION_QUERY_SQLITE_MAX_LIMIT',
    '会话查询sqlite摘要码点','SESSION_QUERY_SQLITE_SNIPPET_CHARS',
    '会话查询sqlite应用标识','SESSION_QUERY_SQLITE_APPLICATION_ID',
    '会话查询sqlite模式版本','SESSION_QUERY_SQLITE_SCHEMA_VERSION',
]#公开面

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 是否thenable(值):#判定可等待对象
    """判定值是否可等待。"""
    if 值 is None:#空不是
        return False#不是
    return callable(getattr(值,'wait',None)) or callable(getattr(值,'等待',None))#Future或thenable

def 解开(值):#承诺则等待否则原样
    """承诺则等待，否则原样返回。"""
    if 是否thenable(值):#可等待
        if callable(getattr(值,'wait',None)):#Future风格
            return 值.wait()#等待
        return 值.等待()#thenable
    return 值#同步值

def 信号已中止(信号):#信号是否已中止
    """信号是否已中止。"""
    if 信号 is None:#无信号
        return False#未中止
    return getattr(信号,'aborted',False) is True or getattr(信号,'已中止',False) is True#中英旗标

def 信号抛出若已中止(信号):#已取消则抛出
    """已取消则抛出。"""
    if 信号已中止(信号):#已中止
        raise 会话查询错误('session-search aborted','SESSION_QUERY_ABORTED')#取消

def 错误信息(错误):#错误消息
    """错误消息。"""
    return 错误 if isinstance(错误,str) else (错误.args[0] if isinstance(错误,BaseException) and len(错误.args)>0 else 'unknown error')#消息

def 配置非法(细节):#非法配置
    """非法配置。"""
    return 会话查询错误(f'session-search SQLite config: {细节}','SESSION_QUERY_INVALID_CONFIG')#拒绝

def 索引已关闭():#索引已关闭
    """索引已关闭。"""
    return 会话查询错误('session-search SQLite index is closed','SESSION_QUERY_INDEX_FAILED')#拒绝

def 非法游标(原因):#非法游标
    """非法游标。"""
    return 会话查询错误('session-search cursor is invalid','SESSION_QUERY_INVALID_CURSOR',{'cause':原因})#拒绝

def 解析配置(配置):#解析运行时配置
    """解析并校验运行时配置。"""
    已解析={
        'path':取字段(配置,'path'),
        'openAt':取字段(配置,'openAt','startup'),
        'journalMode':取字段(配置,'journalMode','wal'),
        'defaultLimit':取字段(配置,'defaultLimit',会话查询sqlite默认页大小),
        'maxLimit':取字段(配置,'maxLimit',会话查询sqlite最大页大小),
        'snippetChars':取字段(配置,'snippetChars',会话查询sqlite摘要码点),
        'readWindowMax':取字段(配置,'readWindowMax',会话查询读取窗口上限),
        'persistedInspectConcurrency':取字段(配置,'persistedInspectConcurrency',会话查询默认持久检查并发),
    }#默认值
    if (not isinstance(已解析['path'],str)) or 已解析['path'].strip()=='':#空路径
        raise 配置非法('path must not be blank')#拒绝
    if 已解析['openAt'] not in ('startup','first-search','never'):#非法 openAt
        raise 配置非法('openAt is not supported')#拒绝
    for 名 in ('defaultLimit','maxLimit'):#页大小
        值=已解析[名]#取值
        if (not isinstance(值,int)) or 值<1 or 值>SQLITE最大页限制:#非法
            raise 配置非法(f'{名} must be an integer between 1 and {SQLITE最大页限制}')#拒绝
    if (not isinstance(已解析['snippetChars'],int)) or 已解析['snippetChars']<1:#摘要
        raise 配置非法('snippetChars must be a positive integer')#拒绝
    if (not isinstance(已解析['readWindowMax'],int)) or 已解析['readWindowMax']<0:#窗口
        raise 配置非法('readWindowMax must be a non-negative integer')#拒绝
    if (not isinstance(已解析['persistedInspectConcurrency'],int)) or 已解析['persistedInspectConcurrency']<1:#并发
        raise 配置非法('persistedInspectConcurrency must be a positive safe integer')#拒绝
    if 已解析['defaultLimit']>已解析['maxLimit']:#默认大于最大
        raise 配置非法('defaultLimit must be less than or equal to maxLimit')#拒绝
    if 已解析['journalMode'] not in 日志模式:#journal
        raise 配置非法('journalMode is not supported')#拒绝
    return 已解析#解析结果

def 头绑定(头):#会话头 INSERT 绑定
    """会话头 INSERT 绑定顺序。"""
    return [
        取字段(头,'id'),取字段(头,'version'),取字段(头,'createdAt'),
        取字段(头,'cwd'),取字段(头,'parentSession'),取字段(头,'seedLength'),
        取字段(头,'delegationDepth'),取字段(头,'agentPreset'),
    ]#绑定列表

def 行头(行):#行→会话头
    """SQLite 行转会话头。"""
    头={'version':行['version'],'id':行['session_id'],'createdAt':行['created_at']}#基础
    if 行['cwd'] is not None:#cwd
        头['cwd']=行['cwd']#带上
    if 行['parent_session'] is not None:#父
        头['parentSession']=行['parent_session']#带上
    if 行['seed_length'] is not None:#seed
        头['seedLength']=行['seed_length']#带上
    if 行['delegation_depth'] is not None:#深度
        头['delegationDepth']=行['delegation_depth']#带上
    if 行['agent_preset'] is not None:#预设
        头['agentPreset']=行['agent_preset']#带上
    return 头#会话头

def 观察会话(头,事件们):#观察一条会话
    """观察一条会话并生成指纹。"""
    分离头=结构化克隆(头)#拆离头
    分离事件=[结构化克隆(事件) for 事件 in 事件们]#拆离事件
    文档们=构建会话事件搜索文档(取字段(分离头,'id'),分离事件)#建文档
    指纹=base64.urlsafe_b64encode(hashlib.sha256(json.dumps(
        {'header':分离头,'events':分离事件},sort_keys=True,separators=(',',':')).encode('utf-8'),
    ).digest()).decode('ascii').rstrip('=')#指纹
    return {'header':分离头,'documents':文档们,'fingerprint':指纹}#观察

def 观察活会话(会话):#观察活会话
    """观察活会话。"""
    return 观察会话(取字段(会话,'header'),取字段(会话,'events'))#委托

def 物化持久快照(快照们):#快照→映射
    """物化持久快照映射。"""
    if not isinstance(快照们,list):#非数组
        raise Exception('persistence snapshots must be an array')#拒绝
    结果={}#id→条目
    for 快照 in 快照们:#逐快照
        if not isinstance(取字段(快照,'revision'),str):#修订非法
            raise Exception('persistence snapshot revision must be a string')#拒绝
        头=结构化克隆(取字段(快照,'header'))#克隆头
        标识=取字段(头,'id')#会话 id
        if 标识 in 结果:#重复
            raise Exception(f'persistence listed duplicate session "{标识}"')#拒绝
        结果[标识]={'header':头,'revision':取字段(快照,'revision')}#收下
    return 结果#映射

def 相同持久快照(前,后):#持久快照是否相同
    """持久快照映射是否相同。"""
    if len(前)!=len(后):#大小不同
        return False#不同
    for 标识,第一条 in 前.items():#逐条
        第二条=后.get(标识)#对应
        if 第二条 is None or 第一条['revision']!=第二条['revision'] or not 相同头(第一条['header'],第二条['header']):#不同
            return False#不同
    return True#相同

def 相同会话id集(前,后):#活会话 id 集是否相同
    """活会话 id 集是否相同。"""
    if len(前)!=len(后):#大小不同
        return False#不同
    for 标识 in 前:#逐 id
        if 标识 not in 后:#缺失
            return False#不同
    return True#相同

def 相同头(左,右):#会话头是否相同
    """会话头字段是否相同。"""
    return (
        取字段(左,'version')==取字段(右,'version')
        and 取字段(左,'id')==取字段(右,'id')
        and 取字段(左,'createdAt')==取字段(右,'createdAt')
        and 取字段(左,'cwd')==取字段(右,'cwd')
        and 取字段(左,'parentSession')==取字段(右,'parentSession')
        and 取字段(左,'seedLength')==取字段(右,'seedLength')
        and (取字段(左,'delegationDepth') or 0)==(取字段(右,'delegationDepth') or 0)
        and 取字段(左,'agentPreset')==取字段(右,'agentPreset')
    )#全等

def 分页(行们,限制,转换,下一游标,偏移):#分页包装
    """分页包装。"""
    还有更多=len(行们)>限制#是否还有
    结果={'items':[转换(行) for 行 in 行们[:限制]]}#当前页
    if 还有更多:#还有下一页
        结果['nextCursor']=会话搜索游标(下一游标(偏移+限制))#游标
    return 结果#页

def 编码游标(载荷):#编码游标
    """编码不透明游标。"""
    文本=json.dumps(载荷,sort_keys=True,separators=(',',':'))#JSON
    return 会话搜索游标(base64.urlsafe_b64encode(文本.encode('utf-8')).decode('ascii').rstrip('='))#base64url

def 解码游标(游标,实例,范围,指纹,世代,偏移期望=None):#解码游标
    """解码并校验游标。"""
    try:#解析
        填充=游标+'='*((4-len(游标)%4)%4)#补齐
        载荷=json.loads(base64.urlsafe_b64decode(填充.encode('ascii')).decode('utf-8'))#解码
    except BaseException as 错误:#坏游标
        raise 非法游标(错误)#拒绝
    if (
        取字段(载荷,'version')!=1
        or 取字段(载荷,'instance')!=实例
        or 取字段(载荷,'scope')!=范围
        or 取字段(载荷,'fingerprint')!=指纹
        or not isinstance(取字段(载荷,'offset'),int)
        or 取字段(载荷,'offset')<0
    ):#身份不匹配
        raise 非法游标(Exception('cursor does not belong to this normalized request'))#拒绝
    if 取字段(载荷,'generation')!=世代:#语料变了
        raise 会话查询错误(
            'session-search cursor is stale because its relevant corpus changed',
            'SESSION_QUERY_STALE_CURSOR',
        )#过期
    return 取字段(载荷,'offset')#偏移

def 选中文档sql():#FTS 候选 CTE
    """选中文档 SQL CTE。"""
    return '''WITH candidates AS (
      SELECT
        pd.session_id AS session_id,
        ps.version AS version,
        ps.created_at AS created_at,
        ps.cwd AS cwd,
        ps.parent_session AS parent_session,
        ps.seed_length AS seed_length,
        ps.delegation_depth AS delegation_depth,
        ps.agent_preset AS agent_preset,
        0 AS live,
        1 AS persisted,
        CAST(pd.seq AS INTEGER) AS seq,
        pd.type AS type,
        CAST(pd.time AS INTEGER) AS time,
        pd.surface AS surface,
        highlight(persisted_docs, 0, ?, ?) AS marked_text,
        CAST(pd.codepoint_length AS INTEGER) AS document_length
      FROM persisted_docs AS pd
      JOIN persisted_sessions AS ps ON ps.id = pd.session_id
      WHERE persisted_docs MATCH ?
        AND ? = 1
        AND NOT EXISTS (SELECT 1 FROM live_sessions AS ls WHERE ls.id = pd.session_id)
      UNION ALL
      SELECT
        ld.session_id AS session_id,
        ls.version AS version,
        ls.created_at AS created_at,
        ls.cwd AS cwd,
        ls.parent_session AS parent_session,
        ls.seed_length AS seed_length,
        ls.delegation_depth AS delegation_depth,
        ls.agent_preset AS agent_preset,
        1 AS live,
        CASE WHEN ? = 1 THEN ls.persisted ELSE 0 END AS persisted,
        CAST(ld.seq AS INTEGER) AS seq,
        ld.type AS type,
        CAST(ld.time AS INTEGER) AS time,
        ld.surface AS surface,
        highlight(live_docs, 0, ?, ?) AS marked_text,
        CAST(ld.codepoint_length AS INTEGER) AS document_length
      FROM temp.live_docs AS ld
      JOIN temp.live_sessions AS ls ON ls.id = ld.session_id
      WHERE live_docs MATCH ?
    ), matched AS (
      SELECT *,
        (
          length(CAST(marked_text AS BLOB))
          - length(CAST(replace(marked_text, ?, '') AS BLOB))
        ) / ? AS match_count
      FROM candidates
    )'''#CTE

def 选中文档参数(查询,持久可见):#FTS 绑定参数
    """选中文档绑定参数。"""
    表达式=引用Fts数据(查询)#短语
    可见=1 if 持久可见 else 0#可见旗标
    标记字节=len(FTS高亮开始.encode('utf-8'))#标记字节长
    return [
        FTS高亮开始,FTS高亮结束,表达式,可见,可见,
        FTS高亮开始,FTS高亮结束,表达式,
        FTS高亮开始,标记字节,
    ]#参数

class Sqlite会话查询引擎(会话查询引擎):#SQLite FTS5 检索实现
    """在优先活会话语料上用 SQLite FTS5 做全文检索。"""
    inject=['sessions']#依赖会话

    def __init__(自身,上下文,配置):#构造并替换 sessionQuery
        """构造 SQLite 检索后端。"""
        已解析=解析配置(配置)#先解析配置
        super().__init__(上下文,已解析)#登记基类服务
        自身.配置=已解析#记下配置
        自身._实例=str(uuid.uuid4())#实例 id
        自身._就绪=False#是否已打开
        自身._库=None#sqlite 连接
        自身._持久化绑定={'identity':object(),'service':None}#可选持久化
        自身._上次持久化身份=None#上次持久化身份
        自身._持久化纪元=0#持久化纪元
        自身._全局世代=0#全局世代
        自身._本地世代=0#本地世代
        自身._已关闭=False#关闭旗标
        自身._锁=threading.Lock()#串行化锁
        def 持久化安装(子上下文):#可选注入持久化
            """记下当前持久化服务。"""
            服务=子上下文.sessionPersistence#取出
            绑定={'identity':object(),'service':服务}#新绑定
            自身._持久化绑定=绑定#换上
            def 摘掉():#拆除
                if 自身._持久化绑定 is 绑定:#仍是本绑定
                    自身._持久化绑定={'identity':object(),'service':None}#清空
            子上下文.effect(摘掉,'sessionQuerySqlite.persistenceBinding')#effect
        纤程=上下文.inject(['sessionPersistence'],持久化安装)#可选注入
        上下文.effect(lambda:纤程.dispose(),'sessionQuerySqlite.optionalPersistence')#拆 fiber
        上下文.effect(lambda:自身.close(),'sessionQuerySqlite.close')#关闭
        自身.__dict__[服务.初始化]=自身._初始化#Service.init

    def _初始化(自身):#Service.init
        """启动时按 openAt 打开索引。"""
        if 自身.配置['openAt']=='startup':#启动打开
            自身._确保就绪(None)#打开

    def 搜索会话(自身,请求,执行上下文=None):#全文搜索会话
        """跨会话 FTS 检索。"""
        自身._断言检索已启用()#openAt never 则拒绝
        已归一=归一化会话请求(请求,自身.配置)#归一化
        信号=取字段(执行上下文,'signal') if 执行上下文 is not None else None#取消信号
        return 自身._串行化(信号,lambda:自身._搜索会话页(已归一,信号))#串行

    def 搜索事件(自身,请求,执行上下文=None):#全文搜索单会话事件
        """单会话 FTS 检索。"""
        自身._断言检索已启用()#openAt never 则拒绝
        已归一=归一化事件请求(请求,自身.配置)#归一化
        信号=取字段(执行上下文,'signal') if 执行上下文 is not None else None#取消信号
        return 自身._串行化(信号,lambda:自身._搜索事件页(已归一,信号))#串行

    def close(自身):#关闭索引
        """关闭索引。"""
        with 自身._锁:#串行
            自身._已关闭=True#标记关闭
            if 自身._库 is not None:#有库
                自身._库.close()#关连接
                自身._库=None#清空
        return None#完成

    def _断言检索已启用(自身):#openAt never 检查
        """openAt never 时拒绝全文检索。"""
        if 自身.配置['openAt']!='never':#已启用
            return#通过
        raise 会话查询错误(
            'session search is disabled: this deployment configures the session-query index with openAt "never"',
            'SESSION_QUERY_SEARCH_DISABLED',
        )#禁用

    def _串行化(自身,信号,操作):#串行执行
        """串行执行检索操作。"""
        if 自身._已关闭:#已关
            raise 索引已关闭()#拒绝
        with 自身._锁:#加锁
            if 自身._已关闭:#双检
                raise 索引已关闭()#拒绝
            信号抛出若已中止(信号)#取消
            return 操作()#执行

    def _确保就绪(自身,信号):#打开索引
        """惰性打开索引。"""
        if 自身._就绪:#已开
            return#通过
        try:#打开
            自身._库=打开检索数据库(自身.配置['path'],自身.配置['journalMode'])#打开
            行=自身._库.execute('SELECT global_generation FROM search_state WHERE singleton = 1').fetchone()#读世代
            自身._全局世代=行['global_generation']#记下
            自身._本地世代=行['global_generation']#本地对齐
            自身._就绪=True#标记就绪
        except BaseException as 错误:#打开失败
            if isinstance(错误,会话查询错误) and 取字段(错误,'code')=='SESSION_QUERY_ABORTED':#取消
                raise 错误#原样
            raise 会话查询错误(
                f'session-search SQLite index failed to open: {错误信息(错误)}',
                'SESSION_QUERY_INDEX_FAILED',
                {'cause':错误},
            )#包装
        信号抛出若已中止(信号)#打开后检查取消

    def _搜索会话页(自身,已归一,信号):#执行会话检索页
        """执行一页会话检索。"""
        自身._确保就绪(信号)#打开
        持久化绑定=自身._对账(信号)#对账索引
        信号抛出若已中止(信号)#对账后检查
        世代=str(自身._全局世代)#当前世代
        指纹=请求指纹(已归一)#请求指纹
        偏移=0 if 取字段(已归一,'cursor') is None else 解码游标(
            取字段(已归一,'cursor'),自身._实例,'sessions',指纹,世代,
        )#游标偏移
        行们=自身._查询会话(已归一,偏移,持久化绑定)#查行
        return 分页(
            行们,取字段(已归一,'limit'),lambda 行:自身._会话命中(行),
            lambda 游标偏移:编码游标({
                'version':1,'instance':自身._实例,'scope':'sessions',
                'fingerprint':指纹,'generation':世代,'offset':游标偏移,
            }),偏移,
        )#分页

    def _搜索事件页(自身,已归一,信号):#执行事件检索页
        """执行一页事件检索。"""
        自身._确保就绪(信号)#打开
        持久化绑定=自身._对账(信号)#对账索引
        信号抛出若已中止(信号)#对账后检查
        目标=自身._目标观察(取字段(已归一,'sessionId'),持久化绑定)#目标世代
        指纹=请求指纹(已归一)#请求指纹
        偏移=0 if 取字段(已归一,'cursor') is None else 解码游标(
            取字段(已归一,'cursor'),自身._实例,'events',指纹,取字段(目标,'generation'),
        )#游标偏移
        行们=自身._查询事件(已归一,偏移,持久化绑定)#查行
        页=分页(
            行们,取字段(已归一,'limit'),lambda 行:自身._事件命中(行),
            lambda 游标偏移:编码游标({
                'version':1,'instance':自身._实例,'scope':'events',
                'fingerprint':指纹,'generation':取字段(目标,'generation'),'offset':游标偏移,
            }),偏移,
        )#分页
        页['session']=取字段(目标,'header')#附上会话头
        return 页#返回

    def _要求库(自身):#取已打开库
        """取已打开库。"""
        if 自身._库 is None:#未开
            raise 索引已关闭()#拒绝
        return 自身._库#连接

    def _主世代(自身):#读全局世代
        """读全局世代。"""
        行=自身._要求库().execute('SELECT global_generation FROM search_state WHERE singleton = 1').fetchone()#读
        return 行['global_generation']#世代

    def _删除会话(自身,来源,标识):#删索引会话
        """从持久或活索引删会话。"""
        库=自身._要求库()#连接
        if 来源=='persisted':#持久
            库.execute('DELETE FROM persisted_docs WHERE session_id = ?',(标识,))#删文档
            库.execute('DELETE FROM persisted_sessions WHERE id = ?',(标识,))#删头
        else:#活
            库.execute('DELETE FROM temp.live_docs WHERE session_id = ?',(标识,))#删文档
            库.execute('DELETE FROM temp.live_sessions WHERE id = ?',(标识,))#删头

    def _替换持久会话(自身,条目,修订,世代):#写持久会话
        """写持久会话与文档。"""
        自身._删除会话('persisted',取字段(取字段(条目,'header'),'id'))#先删
        库=自身._要求库()#连接
        库.execute('''
            INSERT INTO persisted_sessions
              (id, version, created_at, cwd, parent_session, seed_length, delegation_depth, agent_preset, revision, generation)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''',(*头绑定(取字段(条目,'header')),修订,世代))#写头
        插入=库.cursor()#文档游标
        for 文档 in 取字段(条目,'documents'):#逐文档
            文本=清洗Fts文本(取字段(文档,'text'))#清洗
            插入.execute(
                'INSERT INTO persisted_docs (text, session_id, seq, type, time, surface, codepoint_length) VALUES (?, ?, ?, ?, ?, ?, ?)',
                (文本,取字段(文档,'sessionId'),取字段(文档,'seq'),取字段(文档,'type'),
                 取字段(文档,'time'),取字段(文档,'surface'),len(list(文本))),
            )#插入
        库.commit()#提交

    def _替换活会话(自身,条目,世代,已持久):#写活会话
        """写活会话与文档。"""
        自身._删除会话('live',取字段(取字段(条目,'header'),'id'))#先删
        库=自身._要求库()#连接
        库.execute('''
            INSERT INTO temp.live_sessions
              (id, version, created_at, cwd, parent_session, seed_length, delegation_depth, agent_preset, fingerprint, persisted, generation)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''',(*头绑定(取字段(条目,'header')),取字段(条目,'fingerprint'),1 if 已持久 else 0,世代))#写头
        插入=库.cursor()#文档游标
        for 文档 in 取字段(条目,'documents'):#逐文档
            文本=清洗Fts文本(取字段(文档,'text'))#清洗
            插入.execute(
                'INSERT INTO temp.live_docs (text, session_id, seq, type, time, surface, codepoint_length) VALUES (?, ?, ?, ?, ?, ?, ?)',
                (文本,取字段(文档,'sessionId'),取字段(文档,'seq'),取字段(文档,'type'),
                 取字段(文档,'time'),取字段(文档,'surface'),len(list(文本))),
            )#插入
        库.commit()#提交

    def _对账(自身,信号):#索引与语料对账
        """把索引与当前语料对账。"""
        信号抛出若已中止(信号)#入口检查
        库=自身._要求库()#连接
        持久行们=库.execute('SELECT id, revision, generation FROM persisted_sessions').fetchall()#持久索引
        活行们=库.execute('SELECT id, fingerprint, persisted, generation FROM temp.live_sessions').fetchall()#活索引
        持久按id={行['id']:行 for 行 in 持久行们}#id→行
        活按id={行['id']:行 for 行 in 活行们}#id→行
        观察=自身._观察稳定(持久按id,信号)#稳定观察
        信号抛出若已中止(信号)#观察后检查
        持久服务=取字段(取字段(观察,'persistenceBinding'),'service')#持久化服务
        持久变更=[] if 持久服务 is None else [
            条目 for 条目 in 取字段(观察,'persisted').values() if 取字段(条目,'loaded') is not None
        ]#要写的持久
        持久删除=[] if 持久服务 is None else [
            行 for 行 in 持久行们 if 行['id'] not in 取字段(观察,'persisted')
        ]#要删持久
        活变更=[
            条目 for 条目 in 取字段(观察,'live').values()
            if (
                活按id.get(取字段(取字段(条目,'header'),'id')) is None
                or 活按id[取字段(取字段(条目,'header'),'id')]['fingerprint']!=取字段(条目,'fingerprint')
                or 活按id[取字段(取字段(条目,'header'),'id')]['persisted']!=(1 if 取字段(取字段(条目,'header'),'id') in 取字段(观察,'persisted') else 0)
            )
        ]#要写的活
        活删除=[行 for 行 in 活行们 if 行['id'] not in 取字段(观察,'live')]#要删活
        指针变更=自身._上次持久化身份 is not None and 自身._上次持久化身份 is not 取字段(取字段(观察,'persistenceBinding'),'identity')#持久化换了
        有写入=len(持久变更)>0 or len(持久删除)>0 or len(活变更)>0 or len(活删除)>0#是否要写
        下一主世代=自身._主世代()#读主世代
        下一本地世代=自身._本地世代#本地世代
        if len(持久变更)>0 or len(持久删除)>0:#持久有变
            下一主世代+=1#主世代+1
        活替换=[]#活替换批次
        for 条目 in 活变更:#逐活变更
            下一本地世代=max(下一本地世代,下一主世代)+1#本地世代递增
            活替换.append({
                'entry':条目,'generation':下一本地世代,
                'persisted':取字段(取字段(条目,'header'),'id') in 取字段(观察,'persisted'),
            })#记下
        if 有写入:#要写索引
            try:#事务
                库.execute('BEGIN IMMEDIATE')#开始
                for 行 in 持久删除:#删持久
                    自身._删除会话('persisted',行['id'])#删
                for 条目 in 持久变更:#写持久
                    if 取字段(条目,'loaded') is None:#缺 loaded
                        raise Exception(f'missing loaded revision for session "{取字段(取字段(条目,"header"),"id")}"')#拒绝
                    自身._替换持久会话(取字段(条目,'loaded'),取字段(条目,'revision'),下一主世代)#写
                if len(持久变更)>0 or len(持久删除)>0:#主世代变了
                    库.execute('UPDATE search_state SET global_generation = ? WHERE singleton = 1',(下一主世代,))#更新
                for 行 in 活删除:#删活
                    自身._删除会话('live',行['id'])#删
                for 批次 in 活替换:#写活
                    自身._替换活会话(取字段(批次,'entry'),取字段(批次,'generation'),取字段(批次,'persisted'))#写
                库.execute('COMMIT')#提交
            except BaseException as 错误:#失败
                try:#回滚
                    库.execute('ROLLBACK')#回滚
                except BaseException:#双故障
                    pass#忽略
                raise 会话查询错误(
                    f'session-search reconciliation failed: {错误信息(错误)}',
                    'SESSION_QUERY_INDEX_FAILED',
                    {'cause':错误},
                )#包装
        if 有写入 or 指针变更:#语料世代变了
            自身._全局世代+=1#全局+1
        if 指针变更:#持久化服务换了
            自身._持久化纪元+=1#纪元+1
        自身._本地世代=下一本地世代#记下本地世代
        自身._上次持久化身份=取字段(取字段(观察,'persistenceBinding'),'identity')#记下身份
        return 取字段(观察,'persistenceBinding')#返回绑定

    def _观察稳定(自身,已索引,信号):#稳定观察语料
        """稳定观察活/持久语料。"""
        for 尝试 in range(稳定观察尝试次数):#最多两次
            信号抛出若已中止(信号)#入口检查
            持久化绑定=自身._持久化绑定#快照绑定
            持久化=取字段(持久化绑定,'service')#持久化服务
            初始活=set(取字段(取字段(会话,'header'),'id') for 会话 in 自身.ctx.sessions.list())#初始活 id
            持久映射={}#持久观察
            if 持久化 is not None:#有持久化
                try:#观察持久
                    可复用索引=自身._上次持久化身份 is None or 自身._上次持久化身份 is 取字段(持久化绑定,'identity')#可复用
                    前快照=解开(持久化.listSnapshots(信号))#列快照
                    信号抛出若已中止(信号)#列出后检查
                    持久映射=物化持久快照(前快照)#物化
                    for 条目 in 持久映射.values():#逐持久条目
                        标识=取字段(取字段(条目,'header'),'id')#id
                        if 可复用索引 and 已索引.get(标识) is not None and 已索引[标识]['revision']==取字段(条目,'revision'):#可跳过
                            continue#跳过 inspect
                        if 标识 in 初始活 or 自身.ctx.sessions.get(标识) is not None:#活影子
                            continue#跳过 inspect
                        信号抛出若已中止(信号)#inspect 前检查
                        已加载=解开(持久化.inspect(标识,信号))#inspect
                        信号抛出若已中止(信号)#inspect 后检查
                        断言会话头兼容(取字段(条目,'header'),取字段(已加载,'meta'))#头兼容
                        条目['loaded']=观察会话(取字段(已加载,'meta'),取字段(已加载,'events'))#记下 loaded
                    信号抛出若已中止(信号)#后快照前检查
                    后快照=解开(持久化.listSnapshots(信号))#再列快照
                    信号抛出若已中止(信号)#列出后检查
                    后映射=物化持久快照(后快照)#物化
                    if not 相同持久快照(持久映射,后映射):#快照抖动
                        continue#重试
                    if 自身._持久化绑定 is not 持久化绑定:#绑定换了
                        continue#重试
                except BaseException as 错误:#持久观察失败
                    if isinstance(错误,会话查询错误) and 取字段(错误,'code')=='SESSION_QUERY_ABORTED':#取消
                        raise 错误#原样
                    if 信号已中止(信号):#信号取消
                        raise 会话查询错误('session-search aborted','SESSION_QUERY_ABORTED',{'cause':错误})#取消
                    if 自身._持久化绑定 is not 持久化绑定:#绑定换了
                        continue#重试
                    if isinstance(错误,会话查询错误):#已是检索错误
                        raise 错误#原样
                    raise 会话查询错误(
                        f'session-search persistence observation failed: {错误信息(错误)}',
                        'SESSION_QUERY_PERSISTENCE_FAILED',
                        {'cause':错误},
                    )#包装
            活映射={}#活观察
            for 会话 in 自身.ctx.sessions.list():#逐活会话
                已观察=观察活会话(会话)#观察
                耐久=持久映射.get(取字段(取字段(已观察,'header'),'id'))#对应持久
                if 耐久 is not None:#同时持久
                    断言会话头兼容(取字段(已观察,'header'),取字段(耐久,'header'))#头兼容
                活映射[取字段(取字段(已观察,'header'),'id')]=已观察#收下
            if not 相同会话id集(初始活,活映射):#活集抖动
                continue#重试
            return {'persistenceBinding':持久化绑定,'persisted':持久映射,'live':活映射}#稳定
        raise 会话查询错误(
            'session-search persistence observation did not stabilize after one retry',
            'SESSION_QUERY_PERSISTENCE_FAILED',
        )#未稳定

    def _查询会话(自身,请求,偏移,持久化绑定):#查会话命中行
        """查会话命中行。"""
        选中=选中文档sql()#CTE
        会话where=构建会话Where(取字段(请求,'sessionFilters'))#会话谓词
        事件where=构建事件Where(取字段(请求,'eventFilters'))#事件谓词
        断言Fts5外层谓词数(取字段(会话where,'predicateCount')+取字段(事件where,'predicateCount'))#预算
        条件=[取字段(会话where,'sql'),取字段(事件where,'sql')]#WHERE 片段
        条件文本=' AND '.join([片段 for 片段 in 条件 if 片段])#拼 WHERE
        绑定=[
            *选中文档参数(取字段(请求,'query'),取字段(持久化绑定,'service') is not None),
            *取字段(会话where,'params'),*取字段(事件where,'params'),
            取字段(请求,'limit')+1,偏移,
        ]#全部绑定
        断言可移植绑定数(len(绑定))#绑定上限
        语句=f'''
            {选中},
            filtered AS (
              SELECT * FROM matched {'' if 条件文本=='' else f'WHERE {条件文本}'}
            ),
            ranked AS (
              SELECT *, ROW_NUMBER() OVER (
                PARTITION BY session_id
                ORDER BY match_count DESC, document_length ASC, time DESC, seq DESC
              ) AS event_rank
              FROM filtered
            )
            SELECT * FROM ranked
            WHERE event_rank = 1
            ORDER BY match_count DESC, document_length ASC, time DESC, session_id ASC, seq DESC
            LIMIT ? OFFSET ?
        '''#完整语句
        return 自身._要求库().execute(语句,绑定).fetchall()#查行

    def _查询事件(自身,请求,偏移,持久化绑定):#查事件命中行
        """查事件命中行。"""
        选中=选中文档sql()#CTE
        事件where=构建事件Where(取字段(请求,'filters'))#事件谓词
        断言Fts5外层谓词数(1+取字段(事件where,'predicateCount'))#预算
        条件=['session_id = ?',取字段(事件where,'sql')]#WHERE 片段
        条件文本=' AND '.join([片段 for 片段 in 条件 if 片段])#拼 WHERE
        绑定=[
            *选中文档参数(取字段(请求,'query'),取字段(持久化绑定,'service') is not None),
            取字段(请求,'sessionId'),*取字段(事件where,'params'),
            取字段(请求,'limit')+1,偏移,
        ]#全部绑定
        断言可移植绑定数(len(绑定))#绑定上限
        语句=f'''
            {选中}
            SELECT * FROM matched
            WHERE {条件文本}
            ORDER BY match_count DESC, document_length ASC, time DESC, seq DESC
            LIMIT ? OFFSET ?
        '''#完整语句
        return 自身._要求库().execute(语句,绑定).fetchall()#查行

    def _目标观察(自身,会话号,持久化绑定):#目标会话世代
        """取目标会话头与游标世代。"""
        库=自身._要求库()#连接
        活行=库.execute('''
            SELECT id AS session_id, version, created_at, cwd, parent_session, seed_length, delegation_depth, agent_preset, generation
            FROM temp.live_sessions WHERE id = ?
        ''',(会话号,)).fetchone()#活索引
        if 活行 is not None:#活命中
            return {'header':行头(活行),'generation':f'live:{活行["generation"]}'}#活世代
        if 取字段(持久化绑定,'service') is not None:#可查持久
            持久行=库.execute('''
                SELECT id AS session_id, version, created_at, cwd, parent_session, seed_length, delegation_depth, agent_preset, generation
                FROM persisted_sessions WHERE id = ?
            ''',(会话号,)).fetchone()#持久索引
            if 持久行 is not None:#持久命中
                return {
                    'header':行头(持久行),
                    'generation':f'persisted:{自身._持久化纪元}:{持久行["generation"]}',
                }#持久世代
        raise 会话查询错误(f'session "{会话号}" not found','SESSION_QUERY_SESSION_NOT_FOUND')#未找到

    def _会话命中(自身,行):#行→会话命中
        """行→会话命中。"""
        return {
            'header':行头(行),
            'live':行['live']==1,
            'persisted':行['persisted']==1,
            'bestMatch':自身._事件命中(行),
        }#命中

    def _事件命中(自身,行):#行→事件命中
        """行→事件命中。"""
        return {
            'sessionId':行['session_id'],
            'seq':行['seq'],
            'type':行['type'],
            'time':行['time'],
            'surface':行['surface'],
            'snippet':生成摘要(行['marked_text'],自身.配置['snippetChars']),
        }#命中

def 应用(上下文,配置):#安装 SQLite 检索后端
    """挂载 SQLite FTS5 会话检索实现。"""
    Sqlite会话查询引擎(上下文,配置)#构造服务

apply=应用#Cordis插件入口
默认=Sqlite会话查询引擎#默认导出
default=Sqlite会话查询引擎#上游名
