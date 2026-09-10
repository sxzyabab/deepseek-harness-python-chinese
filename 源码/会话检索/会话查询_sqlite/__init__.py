"""在优先活会话语料上用 SQLite FTS5 做全文检索的具体会话检索服务。对齐上游 `@deepseek-ai/dsh-session-query-sqlite`。"""
import base64,hashlib,json,threading,uuid#编码、哈希、JSON、并发与实例 id
from ...依赖 import cordis#Cordis
from ...依赖.schemastery import 字典字段,字符串字段,枚举字段,整数字段#配置
服务=cordis.服务#Cordis服务基类
from ...模型后端.llm import 结构化克隆#拆离克隆
from ..会话查询 import (
    会话查询引擎,会话查询错误,会话查询默认持久检查并发,会话查询读取窗口上限,
    校验会话头兼容,构建会话事件搜索文档,会话搜索游标,
)#基类与共享
from .模式 import (
    会话查询sqlite应用标识,
    会话查询sqlite模式版本,
    日志模式,打开检索数据库,
)#schema
from .查询 import (
    FTS高亮开始,FTS高亮结束,
    SQLITE最大页限制,
    校验可移植绑定数,校验Fts5外层谓词数,
    归一化会话请求,归一化事件请求,
    构建会话Where,构建事件Where,
    引用Fts数据,清洗Fts文本,请求指纹,生成摘要,
)#query
from ..会话查询.配置 import 已中止,若已中止则抛出#中止

名称='session-query-sqlite'#Cordis插件名
注入=['sessions']#依赖会话服务
会话查询sqlite路径键='launcherSessionQueryPath'#启动器索引路径键
会话查询sqlite默认页限制=20#默认页大小
会话查询sqlite最大页限制=100#最大页大小
会话查询sqlite摘要码点=240#默认摘要码点数
稳定观察尝试次数=2#稳定观察最多尝试次数

配置模式=字典字段({
    'path':字符串字段(),
    'openAt':枚举字段('startup','first-search','never',默认值='startup'),
    'journalMode':枚举字段(*日志模式,默认值='wal'),
    'defaultLimit':整数字段(默认值=会话查询sqlite默认页限制),
    'maxLimit':整数字段(默认值=会话查询sqlite最大页限制),
    'snippetChars':整数字段(默认值=会话查询sqlite摘要码点),
    'readWindowMax':整数字段(默认值=会话查询读取窗口上限),
    'persistedInspectConcurrency':整数字段(默认值=会话查询默认持久检查并发),
})#配置模式

__all__=[
    '名称','注入','配置模式','应用',
    'Sqlite会话查询引擎','会话查询sqlite路径键',
    '会话查询sqlite默认页限制',
    '会话查询sqlite最大页限制',
    '会话查询sqlite摘要码点',
    '会话查询sqlite应用标识',
    '会话查询sqlite模式版本',
]#公开面

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
        'path':配置['path'] if 'path' in 配置 else None,
        'openAt':配置['openAt'] if 'openAt' in 配置 else 'startup',
        'journalMode':配置['journalMode'] if 'journalMode' in 配置 else 'wal',
        'defaultLimit':配置['defaultLimit'] if 'defaultLimit' in 配置 else 会话查询sqlite默认页限制,
        'maxLimit':配置['maxLimit'] if 'maxLimit' in 配置 else 会话查询sqlite最大页限制,
        'snippetChars':配置['snippetChars'] if 'snippetChars' in 配置 else 会话查询sqlite摘要码点,
        'readWindowMax':配置['readWindowMax'] if 'readWindowMax' in 配置 else 会话查询读取窗口上限,
        'persistedInspectConcurrency':配置['persistedInspectConcurrency'] if 'persistedInspectConcurrency' in 配置 else 会话查询默认持久检查并发,
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

def 头绑定(头,继承事件数):#会话头 INSERT 绑定
    """会话头 INSERT 绑定顺序；仅 isSeeded 时把 inheritedEventCount 写入 seed_length 列。"""
    return [
        头['id'],头['version'],头['createdAt'],
        头['cwd'] if 'cwd' in 头 else None,头['parentSession'] if 'parentSession' in 头 else None,
        继承事件数 if 头.get('isSeeded') else None,
        头['delegationDepth'] if 'delegationDepth' in 头 else None,头['agentPreset'] if 'agentPreset' in 头 else None,
    ]#绑定列表

def 行头(行):#行→会话头
    """SQLite 行转会话头。"""
    头={'version':行['version'],'id':行['session_id'],'createdAt':行['created_at'],'isSeeded':行['seed_length'] is not None}#基础：seed_length 非空即种子
    if 行['cwd'] is not None:#cwd
        头['cwd']=行['cwd']#带上
    if 行['parent_session'] is not None:#父
        头['parentSession']=行['parent_session']#带上
    if 行['delegation_depth'] is not None:#深度
        头['delegationDepth']=行['delegation_depth']#带上
    if 行['agent_preset'] is not None:#预设
        头['agentPreset']=行['agent_preset']#带上
    return 头#会话头

def 观察会话(头,继承事件数,事件列表):#观察一条会话
    """观察一条会话并生成指纹。"""
    分离头=结构化克隆(头)#拆离头
    分离事件=[结构化克隆(事件) for 事件 in 事件列表]#拆离事件
    文档列表=构建会话事件搜索文档(分离头['id'],分离事件)#建文档
    指纹=base64.urlsafe_b64encode(hashlib.sha256(json.dumps(
        {'header':分离头,'inheritedEventCount':继承事件数,'events':分离事件},ensure_ascii=False,separators=(',',':'),allow_nan=False,sort_keys=True).encode('utf-8'),
    ).digest()).decode('ascii').rstrip('=')#指纹
    return {'header':分离头,'inheritedEventCount':继承事件数,'documents':文档列表,'fingerprint':指纹}#观察

def 观察活会话(会话):#观察活会话
    """观察活会话。"""
    return 观察会话(会话.header,getattr(会话,'inheritedEventCount',0),会话.events)#委托

def 物化持久快照(快照列表):#快照→映射
    """物化持久快照映射。"""
    if not isinstance(快照列表,list):#非数组
        raise 会话查询错误('persistence snapshots must be an array','SESSION_QUERY_PERSISTENCE_FAILED')#拒绝
    结果={}#id→条目
    for 快照 in 快照列表:#逐快照
        if 'revision' not in 快照 or not isinstance(快照['revision'],str):#修订非法
            raise 会话查询错误('persistence snapshot revision must be a string','SESSION_QUERY_PERSISTENCE_FAILED')#拒绝
        头=结构化克隆(快照['header'])#克隆头
        标识=头['id']#会话 id
        if 标识 in 结果:#重复
            raise 会话查询错误('persistence listed duplicate session "'+str(标识)+'"','SESSION_QUERY_PERSISTENCE_FAILED')#拒绝
        结果[标识]={'header':头,'revision':快照['revision']}#收下
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
        左['version']==右['version']
        and 左['id']==右['id']
        and 左['createdAt']==右['createdAt']
        and (左['cwd'] if 'cwd' in 左 else None)==(右['cwd'] if 'cwd' in 右 else None)
        and (左['parentSession'] if 'parentSession' in 左 else None)==(右['parentSession'] if 'parentSession' in 右 else None)
        and (左.get('isSeeded') is True)==(右.get('isSeeded') is True)
        and (左['delegationDepth'] if 'delegationDepth' in 左 and 左['delegationDepth'] is not None else 0)==(右['delegationDepth'] if 'delegationDepth' in 右 and 右['delegationDepth'] is not None else 0)
        and (左['agentPreset'] if 'agentPreset' in 左 else None)==(右['agentPreset'] if 'agentPreset' in 右 else None)
    )#全等

def 分页(行列表,限制,转换,下一游标,偏移):#分页包装
    """分页包装。"""
    还有更多=len(行列表)>限制#是否还有
    结果={'items':[转换(行) for 行 in 行列表[:限制]]}#当前页
    if 还有更多:#还有下一页
        结果['nextCursor']=会话搜索游标(下一游标(偏移+限制))#游标
    return 结果#页

def 编码游标(载荷):#编码游标
    """编码不透明游标。"""
    文本=json.dumps(载荷,ensure_ascii=False,separators=(',',':'),allow_nan=False,sort_keys=True)#JSON
    return 会话搜索游标(base64.urlsafe_b64encode(文本.encode('utf-8')).decode('ascii').rstrip('='))#base64url

def 解码游标(游标,实例,范围,指纹,世代,偏移期望=None):#解码游标
    """解码并校验游标。"""
    try:#解析
        填充=游标+'='*((4-len(游标)%4)%4)#补齐
        载荷=json.loads(base64.urlsafe_b64decode(填充.encode('ascii')).decode('utf-8'))#解码
    except BaseException as 错误:#坏游标
        raise 非法游标(错误)#拒绝
    if (
        载荷['version']!=1
        or 载荷['instance']!=实例
        or 载荷['scope']!=范围
        or 载荷['fingerprint']!=指纹
        or isinstance(载荷['offset'],bool) or not isinstance(载荷['offset'],int)
        or 载荷['offset']<0
    ):#身份不匹配
        raise 非法游标(会话查询错误('cursor does not belong to this normalized request','SESSION_QUERY_INVALID_CURSOR'))#拒绝
    if 载荷['generation']!=世代:#语料变了
        raise 会话查询错误(
            'session-search cursor is stale because its relevant corpus changed',
            'SESSION_QUERY_STALE_CURSOR',
        )#过期
    return 载荷['offset']#偏移

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
    可见=1 if 持久可见 else 0#可见标志
    标记字节=len(FTS高亮开始.encode('utf-8'))#标记字节长
    return [
        FTS高亮开始,FTS高亮结束,表达式,可见,可见,
        FTS高亮开始,FTS高亮结束,表达式,
        FTS高亮开始,标记字节,
    ]#参数

class Sqlite会话查询引擎(会话查询引擎):#SQLite FTS5 检索实现
    """在优先活会话语料上用 SQLite FTS5 做全文检索。"""
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
        自身._已关闭=False#关闭标志
        自身._锁=threading.Lock()#串行化锁
        def 持久化安装(子上下文):#可选注入持久化
            """记下当前持久化服务。"""
            服务=子上下文.sessionPersistence#取出
            绑定={'identity':object(),'service':服务}#新绑定
            自身._持久化绑定=绑定#换上
            def 摘掉():#拆除
                if 自身._持久化绑定 is 绑定:#仍是本绑定
                    自身._持久化绑定={'identity':object(),'service':None}#清空
            子上下文.副作用(摘掉,'sessionQuerySqlite.persistenceBinding')#effect
        纤程=上下文.依赖启动(['sessionPersistence'],持久化安装)#可选注入
        def 拆除纤程():
            """拆除可选持久化 fiber。"""
            纤程.dispose()#拆除
        上下文.副作用(拆除纤程,'sessionQuerySqlite.optionalPersistence')#拆 fiber
        def 关闭效果():
            """关闭索引。"""
            自身.关闭()#关闭
        上下文.副作用(关闭效果,'sessionQuerySqlite.close')#关闭
        自身.__dict__[服务.初始化]=自身._初始化#Service.init

    def _初始化(自身):#Service.init
        """启动时按 openAt 打开索引。"""
        if 自身.配置['openAt']=='startup':#启动打开
            自身._确保就绪(None)#打开

    def 搜索会话(自身,请求,执行上下文=None):#全文搜索会话
        """跨会话 FTS 检索。"""
        自身._校验检索已启用()#openAt never 则拒绝
        已归一=归一化会话请求(请求,自身.配置)#归一化
        信号=执行上下文['signal'] if 执行上下文 is not None and 'signal' in 执行上下文 else None#取消信号
        def 跑会话页():
            """跑一页会话检索。"""
            return 自身._搜索会话页(已归一,信号)#页
        return 自身._串行化(信号,跑会话页)#串行

    def 搜索事件(自身,请求,执行上下文=None):#全文搜索单会话事件
        """单会话 FTS 检索。"""
        自身._校验检索已启用()#openAt never 则拒绝
        已归一=归一化事件请求(请求,自身.配置)#归一化
        信号=执行上下文['signal'] if 执行上下文 is not None and 'signal' in 执行上下文 else None#取消信号
        def 跑事件页():
            """跑一页事件检索。"""
            return 自身._搜索事件页(已归一,信号)#页
        return 自身._串行化(信号,跑事件页)#串行

    def 关闭(自身):#关闭索引
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
            若已中止则抛出(信号)#取消
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
            if isinstance(错误,会话查询错误) and 错误.code=='SESSION_QUERY_ABORTED':#取消
                raise 错误#原样
            raise 会话查询错误(
                f'session-search SQLite index failed to open: {错误信息(错误)}',
                'SESSION_QUERY_INDEX_FAILED',
                {'cause':错误},
            )#包装
        若已中止则抛出(信号)#打开后检查取消

    def _搜索会话页(自身,已归一,信号):#执行会话检索页
        """执行一页会话检索。"""
        自身._确保就绪(信号)#打开
        持久化绑定=自身._对账(信号)#对账索引
        若已中止则抛出(信号)#对账后检查
        世代=str(自身._全局世代)#当前世代
        指纹=请求指纹(已归一)#请求指纹
        游标=已归一['cursor'] if 'cursor' in 已归一 else None#游标
        偏移=0 if 游标 is None else 解码游标(游标,自身._实例,'sessions',指纹,世代)#游标偏移
        行列表=自身._查询会话(已归一,偏移,持久化绑定)#查行
        def 会话下一游标(游标偏移):
            """编码会话续页游标。"""
            return 编码游标({
                'version':1,'instance':自身._实例,'scope':'sessions',
                'fingerprint':指纹,'generation':世代,'offset':游标偏移,
            })#游标
        return 分页(行列表,已归一['limit'],自身._会话命中,会话下一游标,偏移)#分页

    def _搜索事件页(自身,已归一,信号):#执行事件检索页
        """执行一页事件检索。"""
        自身._确保就绪(信号)#打开
        持久化绑定=自身._对账(信号)#对账索引
        若已中止则抛出(信号)#对账后检查
        目标=自身._目标观察(已归一['sessionId'],持久化绑定)#目标世代
        指纹=请求指纹(已归一)#请求指纹
        游标=已归一['cursor'] if 'cursor' in 已归一 else None#游标
        偏移=0 if 游标 is None else 解码游标(游标,自身._实例,'events',指纹,目标['generation'])#游标偏移
        行列表=自身._查询事件(已归一,偏移,持久化绑定)#查行
        def 事件下一游标(游标偏移):
            """编码事件续页游标。"""
            return 编码游标({
                'version':1,'instance':自身._实例,'scope':'events',
                'fingerprint':指纹,'generation':目标['generation'],'offset':游标偏移,
            })#游标
        页=分页(行列表,已归一['limit'],自身._事件命中,事件下一游标,偏移)#分页
        页['session']=目标['header']#附上会话头
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
        自身._删除会话('persisted',条目['header']['id'])#先删
        库=自身._要求库()#连接
        库.execute('''
            INSERT INTO persisted_sessions
              (id, version, created_at, cwd, parent_session, seed_length, delegation_depth, agent_preset, revision, generation)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''',(*头绑定(条目['header'],条目['inheritedEventCount'] if 'inheritedEventCount' in 条目 else 0),修订,世代))#写头
        插入=库.cursor()#文档游标
        for 文档 in 条目['documents']:#逐文档
            文本=清洗Fts文本(文档['text'])#清洗
            插入.execute(
                'INSERT INTO persisted_docs (text, session_id, seq, type, time, surface, codepoint_length) VALUES (?, ?, ?, ?, ?, ?, ?)',
                (文本,文档['sessionId'],文档['seq'],文档['type'],
                 文档['time'],文档['surface'],len(文本.encode('utf-8'))),
            )#插入
        库.commit()#提交

    def _替换活会话(自身,条目,世代,已持久):#写活会话
        """写活会话与文档。"""
        自身._删除会话('live',条目['header']['id'])#先删
        库=自身._要求库()#连接
        库.execute('''
            INSERT INTO temp.live_sessions
              (id, version, created_at, cwd, parent_session, seed_length, delegation_depth, agent_preset, fingerprint, persisted, generation)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''',(*头绑定(条目['header'],条目['inheritedEventCount'] if 'inheritedEventCount' in 条目 else 0),条目['fingerprint'],1 if 已持久 else 0,世代))#写头
        插入=库.cursor()#文档游标
        for 文档 in 条目['documents']:#逐文档
            文本=清洗Fts文本(文档['text'])#清洗
            插入.execute(
                'INSERT INTO temp.live_docs (text, session_id, seq, type, time, surface, codepoint_length) VALUES (?, ?, ?, ?, ?, ?, ?)',
                (文本,文档['sessionId'],文档['seq'],文档['type'],
                 文档['time'],文档['surface'],len(文本.encode('utf-8'))),
            )#插入
        库.commit()#提交

    def _对账(自身,信号):#索引与语料对账
        """把索引与当前语料对账。"""
        若已中止则抛出(信号)#入口检查
        库=自身._要求库()#连接
        持久行列表=库.execute('SELECT id, revision, generation FROM persisted_sessions').fetchall()#持久索引
        活行列表=库.execute('SELECT id, fingerprint, persisted, generation FROM temp.live_sessions').fetchall()#活索引
        持久按id={行['id']:行 for 行 in 持久行列表}#id→行
        活按id={行['id']:行 for 行 in 活行列表}#id→行
        观察=自身._观察稳定(持久按id,信号)#稳定观察
        若已中止则抛出(信号)#观察后检查
        持久服务=观察['persistenceBinding']['service']#持久化服务
        持久变更=[] if 持久服务 is None else [
            条目 for 条目 in 观察['persisted'].values() if 条目['loaded'] if 'loaded' in 条目 else None is not None
        ]#要写的持久
        持久删除=[] if 持久服务 is None else [
            行 for 行 in 持久行列表 if 行['id'] not in 观察['persisted']
        ]#要删持久
        活变更=[
            条目 for 条目 in 观察['live'].values()
            if (
                活按id.get(条目['header']['id']) is None
                or 活按id[条目['header']['id']]['fingerprint']!=条目['fingerprint']
                or 活按id[条目['header']['id']]['persisted']!=(1 if 条目['header']['id'] in 观察['persisted'] else 0)
            )
        ]#要写的活
        活删除=[行 for 行 in 活行列表 if 行['id'] not in 观察['live']]#要删活
        指针变更=自身._上次持久化身份 is not None and 自身._上次持久化身份 is not 观察['persistenceBinding']['identity']#持久化换了
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
                'persisted':条目['header']['id'] in 观察['persisted'],
            })#记下
        if 有写入:#要写索引
            try:#事务
                库.execute('BEGIN IMMEDIATE')#开始
                for 行 in 持久删除:#删持久
                    自身._删除会话('persisted',行['id'])#删
                for 条目 in 持久变更:#写持久
                    if 条目['loaded'] if 'loaded' in 条目 else None is None:#缺 loaded
                        raise 会话查询错误('missing loaded revision for session "'+str(条目['header']['id'])+'"','SESSION_QUERY_INDEX_FAILED')#拒绝
                    自身._替换持久会话(条目['loaded'] if 'loaded' in 条目 else None,条目['revision'],下一主世代)#写
                if len(持久变更)>0 or len(持久删除)>0:#主世代变了
                    库.execute('UPDATE search_state SET global_generation = ? WHERE singleton = 1',(下一主世代,))#更新
                for 行 in 活删除:#删活
                    自身._删除会话('live',行['id'])#删
                for 批次 in 活替换:#写活
                    自身._替换活会话(批次['entry'],批次['generation'],批次['persisted'])#写
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
        自身._上次持久化身份=观察['persistenceBinding']['identity']#记下身份
        return 观察['persistenceBinding']#返回绑定

    def _观察稳定(自身,已索引,信号):#稳定观察语料
        """稳定观察活/持久语料。"""
        for 尝试 in range(稳定观察尝试次数):#最多两次
            若已中止则抛出(信号)#入口检查
            持久化绑定=自身._持久化绑定#快照绑定
            持久化=持久化绑定['service']#持久化服务
            初始活=set(会话.header['id'] for 会话 in 自身.ctx.sessions.list())#初始活 id
            持久映射={}#持久观察
            if 持久化 is not None:#有持久化
                try:#观察持久
                    可复用索引=自身._上次持久化身份 is None or 自身._上次持久化身份 is 持久化绑定['identity']#可复用
                    前快照=持久化.列出快照(信号)#列快照
                    若已中止则抛出(信号)#列出后检查
                    持久映射=物化持久快照(前快照)#物化
                    for 条目 in 持久映射.values():#逐持久条目
                        标识=条目['header']['id']#id
                        if 可复用索引 and 已索引.get(标识) is not None and 已索引[标识]['revision']==条目['revision']:#可跳过
                            continue#跳过 inspect
                        if 标识 in 初始活 or 自身.ctx.sessions.get(标识) is not None:#活影子
                            continue#跳过 inspect
                        若已中止则抛出(信号)#inspect 前检查
                        已加载=持久化.检查(标识,信号)#inspect
                        若已中止则抛出(信号)#inspect 后检查
                        校验会话头兼容(条目['header'],已加载['meta'])#头兼容
                        条目['loaded']=观察会话(已加载['meta'],已加载['inheritedEventCount'] if 'inheritedEventCount' in 已加载 else 0,已加载['events'])#记下 loaded
                    若已中止则抛出(信号)#后快照前检查
                    后快照=持久化.列出快照(信号)#再列快照
                    若已中止则抛出(信号)#列出后检查
                    后映射=物化持久快照(后快照)#物化
                    if not 相同持久快照(持久映射,后映射):#快照抖动
                        continue#重试
                    if 自身._持久化绑定 is not 持久化绑定:#绑定换了
                        continue#重试
                except BaseException as 错误:#持久观察失败
                    if isinstance(错误,会话查询错误) and 错误.code=='SESSION_QUERY_ABORTED':#取消
                        raise 错误#原样
                    if 已中止(信号):#信号取消
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
                耐久=持久映射.get(已观察['header']['id'])#对应持久
                if 耐久 is not None:#同时持久
                    校验会话头兼容(已观察['header'],耐久['header'])#头兼容
                活映射[已观察['header']['id']]=已观察#收下
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
        会话where=构建会话Where(请求['sessionFilters'])#会话谓词
        事件where=构建事件Where(请求['eventFilters'])#事件谓词
        校验Fts5外层谓词数(会话where['predicateCount']+事件where['predicateCount'])#预算
        条件=[会话where['sql'],事件where['sql']]#WHERE 片段
        条件文本=' AND '.join([片段 for 片段 in 条件 if 片段])#拼 WHERE
        绑定=[
            *选中文档参数(请求['query'],持久化绑定['service'] is not None),
            *会话where['params'],*事件where['params'],
            请求['limit']+1,偏移,
        ]#全部绑定
        校验可移植绑定数(len(绑定))#绑定上限
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
        事件where=构建事件Where(请求['filters'])#事件谓词
        校验Fts5外层谓词数(1+事件where['predicateCount'])#预算
        条件=['session_id = ?',事件where['sql']]#WHERE 片段
        条件文本=' AND '.join([片段 for 片段 in 条件 if 片段])#拼 WHERE
        绑定=[
            *选中文档参数(请求['query'],持久化绑定['service'] is not None),
            请求['sessionId'],*事件where['params'],
            请求['limit']+1,偏移,
        ]#全部绑定
        校验可移植绑定数(len(绑定))#绑定上限
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
        if 持久化绑定['service'] is not None:#可查持久
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

应用.name=名称#Cordis name 槽
应用.inject=注入#Cordis inject 槽
应用.Config=配置模式#Cordis Config 槽
apply=应用#Cordis插件入口
default=Sqlite会话查询引擎#Cordis 默认导出槽
Sqlite会话查询引擎.inject=['sessions']#Cordis inject 槽
