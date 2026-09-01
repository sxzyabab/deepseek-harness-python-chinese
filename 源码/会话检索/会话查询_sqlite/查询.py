"""请求归一化、参数化谓词与结果展示。对齐上游 `session-query-sqlite/src/query.ts`。"""
import json,re#JSON 与空白正则
from ..会话查询 import 会话查询错误,物化会话结果过滤器,物化会话事件结果过滤器#共享检索工具
__all__=[
    'FTS高亮开始','FTS_HIGHLIGHT_START','FTS高亮结束','FTS_HIGHLIGHT_END',
    'SQLITE最大页限制','SQLITE_MAX_PAGE_LIMIT',
    'SQLITE可移植变量上限','SQLITE_PORTABLE_VARIABLE_LIMIT',
    'SQLITE_FTS5外层谓词上限','SQLITE_FTS5_OUTER_PREDICATE_LIMIT',
    '断言可移植绑定数','assertPortableBindingCount',
    '断言Fts5外层谓词数','assertFts5OuterPredicateCount',
    '归一化会话请求','normalizeSessionRequest',
    '归一化事件请求','normalizeEventRequest',
    '构建会话Where','buildSessionWhere','构建事件Where','buildEventWhere',
    '引用Fts数据','quoteFtsData','清洗Fts文本','sanitizeFtsText',
    '请求指纹','requestFingerprint','生成摘要','makeSnippet',
]#公开面

FTS高亮开始='\uFDD0'#FTS5 highlight 前插标记
FTS_HIGHLIGHT_START=FTS高亮开始#上游名
FTS高亮结束='\uFDD1'#FTS5 highlight 后插标记
FTS_HIGHLIGHT_END=FTS高亮结束#上游名
SQLITE最大页限制=2**53-2#最大安全页大小（MAX_SAFE_INTEGER-1）
SQLITE_MAX_PAGE_LIMIT=SQLITE最大页限制#上游名
SQLITE可移植变量上限=32766#可移植绑定上限
SQLITE_PORTABLE_VARIABLE_LIMIT=SQLITE可移植变量上限#上游名
SQLITE_FTS5外层谓词上限=14#FTS5 外层谓词预算
SQLITE_FTS5_OUTER_PREDICATE_LIMIT=SQLITE_FTS5外层谓词上限#上游名

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 断言可移植绑定数(计数):#拒绝超绑定
    """拒绝超出可移植绑定上限。"""
    if 计数>SQLITE可移植变量上限:#超限
        raise 会话查询错误(
            f"session-search request exceeds SQLite's portable {SQLITE可移植变量上限}-variable limit; reduce filter values",
            'SESSION_QUERY_INVALID_FILTER',
        )#拒绝

def 断言Fts5外层谓词数(计数):#拒绝超谓词
    """拒绝超出 FTS5 外层谓词预算。"""
    if 计数>SQLITE_FTS5外层谓词上限:#超限
        raise 会话查询错误(
            f'session-search request exceeds the supported SQLite FTS5 outer-predicate budget of {SQLITE_FTS5外层谓词上限}; reduce filters',
            'SESSION_QUERY_INVALID_FILTER',
        )#拒绝

assertPortableBindingCount=断言可移植绑定数#上游名
assertFts5OuterPredicateCount=断言Fts5外层谓词数#上游名

def 归一化查询(值):#归一化查询文本
    """校验并清洗查询文本。"""
    if not isinstance(值,str):#非文本
        raise 会话查询错误('session-search query must be text','SESSION_QUERY_INVALID_QUERY')#拒绝
    查询=值.strip()#去首尾空白
    查询=re.sub(r'\s+',' ',查询,flags=re.UNICODE)#折叠空白
    if len(查询)==0:#空查询
        raise 会话查询错误('session-search query must contain non-whitespace text','SESSION_QUERY_INVALID_QUERY')#拒绝
    if '\0' in 查询:#NUL
        raise 会话查询错误('session-search query must not contain NUL','SESSION_QUERY_INVALID_QUERY')#拒绝
    return 清洗Fts文本(查询)#清洗保留字符

def 物化游标(游标):#物化游标
    """物化可选游标。"""
    if 游标 is None:#无游标
        return None#缺席
    if not isinstance(游标,str):#非文本
        raise 会话查询错误('session-search cursor must be text','SESSION_QUERY_INVALID_CURSOR')#拒绝
    return 游标#原样

def 归一化限制(值,限制):#归一化页大小
    """归一化页大小。"""
    限制值=值 if 值 is not None else 取字段(限制,'defaultLimit')#默认
    最大限制=min(取字段(限制,'maxLimit'),SQLITE最大页限制)#封顶
    if (not isinstance(限制值,int)) or 限制值<1 or 限制值>最大限制:#非法
        raise 会话查询错误(
            f'session-search limit must be an integer between 1 and {最大限制}',
            'SESSION_QUERY_INVALID_LIMIT',
        )#拒绝
    return 限制值#合法限制

def 物化元数据过滤器(过滤器们):#物化事件元数据过滤器
    """物化事件元数据过滤器并拒绝 text 子句。"""
    if not isinstance(过滤器们,list):#非数组
        raise Exception('session-search filters must be an array')#拒绝
    for 子句 in 过滤器们:#逐子句
        种类=取字段(子句,'kind')#判别
        if 种类 in ('seq','time','type','surface'):#允许
            continue#下一
        if 种类=='text':#不允许
            raise 会话查询错误(
                'session-search metadata filters do not accept text clauses',
                'SESSION_QUERY_INVALID_FILTER',
            )#拒绝
        未知过滤器(子句)#未知
    return 物化会话事件结果过滤器(过滤器们)#物化

def 归一化会话请求(请求,限制):#归一化跨会话请求
    """校验并规范化跨会话请求。"""
    会话过滤器=物化会话结果过滤器(取字段(请求,'sessionFilters') or [])#物化会话过滤
    事件过滤器=物化元数据过滤器(取字段(请求,'eventFilters') or [])#物化事件过滤
    游标=物化游标(取字段(请求,'cursor'))#游标
    结果={
        'query':归一化查询(取字段(请求,'query')),
        'sessionFilters':会话过滤器,
        'eventFilters':事件过滤器,
        'limit':归一化限制(取字段(请求,'limit'),限制),
    }#归一化体
    if 游标 is not None:#有游标
        结果['cursor']=游标#附上
    return 结果#返回

def 归一化事件请求(请求,限制):#归一化单会话请求
    """校验并规范化单会话请求。"""
    if not isinstance(取字段(请求,'sessionId'),str):#非法会话 id
        raise 会话查询错误('session-search session id must be text','SESSION_QUERY_INVALID_FILTER')#拒绝
    过滤器们=物化元数据过滤器(取字段(请求,'filters') or [])#物化过滤
    游标=物化游标(取字段(请求,'cursor'))#游标
    结果={
        'sessionId':取字段(请求,'sessionId'),
        'query':归一化查询(取字段(请求,'query')),
        'filters':过滤器们,
        'limit':归一化限制(取字段(请求,'limit'),限制),
    }#归一化体
    if 游标 is not None:#有游标
        结果['cursor']=游标#附上
    return 结果#返回

normalizeSessionRequest=归一化会话请求#上游名
normalizeEventRequest=归一化事件请求#上游名

def 追加列表绑定(参数们,值们):#追加 IN 绑定
    """追加 IN 列表绑定并返回占位符串。"""
    断言可移植绑定数(len(参数们)+len(值们))#检查上限
    for 值 in 值们:#逐值
        参数们.append(值)#追加
    return ','.join(['?']*len(值们))#占位符

def 追加列表(子句们,参数们,列,值们):#等值 IN 子句
    """追加等值 IN 子句。"""
    if len(值们)==0:#空列表
        子句们.append('0')#永假
        return#结束
    子句们.append(f'{列} IN ({追加列表绑定(参数们,值们)})')#IN 子句

def 追加可空列表(子句们,参数们,列,值们):#可空 IN 子句
    """追加可空 IN 子句。"""
    if len(值们)==0:#空列表
        子句们.append('0')#永假
        return#结束
    具体=[值 for 值 in 值们 if 值 is not None]#非空值
    部分=[]#OR 部分
    if len(具体)>0:#有具体值
        部分.append(f'{列} IN ({追加列表绑定(参数们,具体)})')#IN
    if None in 值们:#要 NULL
        部分.append(f'{列} IS NULL')#IS NULL
    子句们.append(f'({" OR ".join(部分)})')#包起来

def 追加区间(子句们,参数们,列,区间):#数值区间子句
    """追加数值区间子句。"""
    起点=取字段(区间,'from')#下界
    终点=取字段(区间,'to')#上界
    if 起点 is not None:#有下界
        断言可移植绑定数(len(参数们)+1)#检查
        子句们.append(f'CAST({列} AS INTEGER) >= ?')#>=
        参数们.append(起点)#绑定
    if 终点 is not None:#有上界
        断言可移植绑定数(len(参数们)+1)#检查
        子句们.append(f'CAST({列} AS INTEGER) <= ?')#<=
        参数们.append(终点)#绑定

def 构建会话Where(过滤器们):#编译会话谓词
    """编译逻辑会话谓词。"""
    子句们=[]#SQL 子句
    参数们=[]#绑定
    for 过滤器 in 过滤器们:#逐过滤器
        种类=取字段(过滤器,'kind')#判别
        if 种类=='id':#按 id
            追加列表(子句们,参数们,'session_id',取字段(过滤器,'values'))#IN
        elif 种类=='cwd':#按 cwd
            追加可空列表(子句们,参数们,'cwd',取字段(过滤器,'values'))#可空 IN
        elif 种类=='created-at':#按创建时间
            追加区间(子句们,参数们,'created_at',过滤器)#区间
        elif 种类=='parent':#按父会话
            追加可空列表(子句们,参数们,'parent_session',取字段(过滤器,'values'))#可空 IN
        elif 种类=='availability':#按可用性
            可用性=list(dict.fromkeys(取字段(过滤器,'values')))#去重保序
            if len(可用性)==0:#空
                子句们.append('0')#永假
            elif len(可用性)==1:#单一
                值=可用性[0]#唯一值
                if 值=='live':#活
                    子句们.append('live = 1')#活
                elif 值=='persisted':#已持久
                    子句们.append('persisted = 1')#持久
                else:#未知
                    未知可用性(值)#拒绝
        else:#未知
            未知过滤器(过滤器)#拒绝
    断言Fts5外层谓词数(len(子句们))#谓词预算
    return {'sql':' AND '.join(子句们),'params':参数们,'predicateCount':len(子句们)}#片段

def 构建事件Where(过滤器们):#编译事件谓词
    """编译事件元数据谓词。"""
    子句们=[]#SQL 子句
    参数们=[]#绑定
    for 过滤器 in 过滤器们:#逐过滤器
        种类=取字段(过滤器,'kind')#判别
        if 种类=='seq':#按序号
            追加区间(子句们,参数们,'seq',过滤器)#区间
        elif 种类=='time':#按时间
            追加区间(子句们,参数们,'time',过滤器)#区间
        elif 种类=='type':#按类型
            追加列表(子句们,参数们,'type',取字段(过滤器,'values'))#IN
        elif 种类=='surface':#按面
            追加列表(子句们,参数们,'surface',取字段(过滤器,'values'))#IN
        else:#未知
            未知过滤器(过滤器)#拒绝
    断言Fts5外层谓词数(len(子句们))#谓词预算
    return {'sql':' AND '.join(子句们),'params':参数们,'predicateCount':len(子句们)}#片段

buildSessionWhere=构建会话Where#上游名
buildEventWhere=构建事件Where#上游名

def 引用Fts数据(查询):#引用 FTS 短语
    """把调用方文本引用成单个 FTS5 短语。"""
    return f'"{查询.replace(chr(34), chr(34)+chr(34))}"'#双引号转义

quoteFtsData=引用Fts数据#上游名

def 清洗Fts文本(文本):#清洗 FTS 文本
    """去掉保留标记碰撞。"""
    return 文本.replace('\0','\uFFFD').replace(FTS高亮开始,'\uFFFD').replace(FTS高亮结束,'\uFFFD')#替换

sanitizeFtsText=清洗Fts文本#上游名

def 规范过滤器(过滤器们):#规范过滤器用于指纹
    """规范过滤器排序用于指纹。"""
    规范=[]#输出
    for 过滤器 in 过滤器们:#逐过滤器
        if 'values' in 过滤器:#列表型
            规范.append({**过滤器,'values':sorted(取字段(过滤器,'values'),key=比较可空)})#排序值
        else:#区间型
            规范.append({
                'kind':取字段(过滤器,'kind'),
                'from':取字段(过滤器,'from') if 取字段(过滤器,'from') is not None else None,
                'to':取字段(过滤器,'to') if 取字段(过滤器,'to') is not None else None,
            })#区间
    return sorted(规范,key=lambda 项:json.dumps(项,sort_keys=True))#稳定排序

def 比较可空(左,右):#可空字符串比较
    """可空字符串比较键。"""
    if 左==右:#相等
        return 0#相等
    if 左 is None:#NULL 更小
        return -1#前
    if 右 is None:#NULL 更小
        return 1#后
    return (左>右)-(左<右)#字典序

def 请求指纹(请求):#请求指纹
    """生成游标绑定的稳定请求身份。"""
    if 'sessionId' in 请求:#事件范围
        return json.dumps({
            'scope':'events','sessionId':取字段(请求,'sessionId'),
            'query':取字段(请求,'query'),'filters':规范过滤器(取字段(请求,'filters')),
            'limit':取字段(请求,'limit'),
        },sort_keys=True,separators=(',',':'))#事件指纹
    return json.dumps({
        'scope':'sessions','query':取字段(请求,'query'),
        'sessionFilters':规范过滤器(取字段(请求,'sessionFilters')),
        'eventFilters':规范过滤器(取字段(请求,'eventFilters')),
        'limit':取字段(请求,'limit'),
    },sort_keys=True,separators=(',',':'))#会话指纹

requestFingerprint=请求指纹#上游名

def 规范化标记文本(标记文本):#去标记并找匹配起点
    """去掉 FTS 标记并折叠空白。"""
    字符们=[]#输出字符
    匹配起点=None#首个匹配位置
    for 字符 in 标记文本:#逐字符
        if 字符==FTS高亮开始:#开始
            if 匹配起点 is None:#首个
                匹配起点=len(字符们)#记下
            continue#跳过
        if 字符==FTS高亮结束:#结束
            continue#跳过
        if re.match(r'\s',字符,flags=re.UNICODE):#空白
            if len(字符们)>0 and 字符们[-1]!=' ':#避免重复空格
                字符们.append(' ')#单空格
        else:#普通字符
            字符们.append(字符)#收下
    if len(字符们)>0 and 字符们[-1]==' ':#尾空格
        字符们.pop()#去掉
    return {'text':''.join(字符们),'matchStart':匹配起点 if 匹配起点 is not None else 0}#结果

def 生成摘要(标记文本,最大码点):#生成摘要片段
    """生成不超过最大码点的摘要。"""
    清洗=规范化标记文本(标记文本)#去标记
    干净文本=取字段(清洗,'text')#纯文本
    匹配起点=取字段(清洗,'matchStart')#匹配起点
    字符们=list(干净文本)#码点列表
    if len(字符们)<=最大码点:#够短
        return 干净文本#原样
    if 最大码点==1:#极短
        return '…'#省略号
    匹配索引=min(匹配起点,len(字符们)-1)#夹住
    起点=max(0,匹配索引-最大码点//3)#窗口起点
    前缀='…' if 起点>0 else ''#前省略
    后缀='…'#后省略
    内容长度=最大码点-len(前缀)-len(后缀)#可用长度
    if 内容长度<1:#放不下
        起点=匹配索引#从匹配开始
        后缀=''#无后缀
        内容长度=最大码点-len(前缀)#重算
    elif 匹配索引>=起点+内容长度:#匹配在窗外
        起点=匹配索引-内容长度+1#右移
    终点=min(len(字符们),起点+内容长度)#窗口终点
    if 终点==len(字符们):#到末尾
        后缀=''#无后缀
        内容长度=最大码点-len(前缀)#重算
        起点=max(0,终点-内容长度)#左移
    终点=min(len(字符们),起点+内容长度)#再夹
    return f'{前缀}{"".join(字符们[起点:终点])}{后缀}'#拼摘要

makeSnippet=生成摘要#上游名

def 未知可用性(值):#未知可用性值
    """未知可用性值。"""
    raise 会话查询错误(
        f'session availability filter contains unknown value "{值}"',
        'SESSION_QUERY_INVALID_FILTER',
    )#拒绝

def 未知过滤器(过滤器):#未知过滤器种类
    """未知过滤器种类。"""
    种类=取字段(过滤器,'kind')#种类
    描述=f'"{种类}"' if isinstance(种类,str) else '(missing)'#描述
    raise 会话查询错误(
        f'session filter contains unknown kind {描述}',
        'SESSION_QUERY_INVALID_FILTER',
    )#拒绝
