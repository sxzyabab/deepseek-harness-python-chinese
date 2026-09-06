"""请求归一化、参数化谓词与结果展示。对齐上游 `session-query-sqlite/src/query.ts`。"""
import json,re#JSON 与空白正则
from ..会话查询 import 会话查询错误,物化会话结果过滤器,物化会话事件结果过滤器#共享检索工具
__all__=[
    'FTS高亮开始','FTS高亮结束',
    'SQLITE最大页限制','SQLITE可移植变量上限','SQLITE_FTS5外层谓词上限',
    '校验可移植绑定数','校验Fts5外层谓词数',
    '归一化会话请求','归一化事件请求',
    '构建会话Where','构建事件Where',
    '引用Fts数据','清洗Fts文本',
    '请求指纹','生成摘要',
]#公开面

FTS高亮开始='\uFDD0'#FTS5 highlight 前插标记
FTS高亮结束='\uFDD1'#FTS5 highlight 后插标记
SQLITE最大页限制=2**53-2#最大安全页大小（MAX_SAFE_INTEGER-1）
SQLITE可移植变量上限=32766#可移植绑定上限
SQLITE_FTS5外层谓词上限=14#FTS5 外层谓词预算
空白=re.compile(r'\s+',re.ASCII)#ASCII 空白
单空白=re.compile(r'\s',re.ASCII)#单空白

def 校验可移植绑定数(计数):
    """拒绝超出可移植绑定上限。"""
    if 计数>SQLITE可移植变量上限:#超限
        raise 会话查询错误(
            "session-search request exceeds SQLite's portable "+str(SQLITE可移植变量上限)+"-variable limit; reduce filter values",
            'SESSION_QUERY_INVALID_FILTER',
        )#拒绝

def 校验Fts5外层谓词数(计数):
    """拒绝超出 FTS5 外层谓词预算。"""
    if 计数>SQLITE_FTS5外层谓词上限:#超限
        raise 会话查询错误(
            'session-search request exceeds the supported SQLite FTS5 outer-predicate budget of '+str(SQLITE_FTS5外层谓词上限)+'; reduce filters',
            'SESSION_QUERY_INVALID_FILTER',
        )#拒绝

def 归一化查询(值):
    """校验并清洗查询文本。"""
    if not isinstance(值,str):#非文本
        raise 会话查询错误('session-search query must be text','SESSION_QUERY_INVALID_QUERY')#拒绝
    查询=值.strip()#去首尾空白
    查询=空白.sub(' ',查询,count=0)#折叠空白
    if len(查询)==0:#空查询
        raise 会话查询错误('session-search query must contain non-whitespace text','SESSION_QUERY_INVALID_QUERY')#拒绝
    if '\0' in 查询:#NUL
        raise 会话查询错误('session-search query must not contain NUL','SESSION_QUERY_INVALID_QUERY')#拒绝
    return 清洗Fts文本(查询)#清洗保留字符

def 物化游标(游标):
    """物化可选游标。"""
    if 游标 is None:#无游标
        return None#缺席
    if not isinstance(游标,str):#非文本
        raise 会话查询错误('session-search cursor must be text','SESSION_QUERY_INVALID_CURSOR')#拒绝
    return 游标#原样

def 归一化限制(值,限制):
    """归一化页大小。"""
    限制值=限制['defaultLimit'] if 值 is None else 值#默认
    最大限制=min(限制['maxLimit'],SQLITE最大页限制)#封顶
    if isinstance(限制值,bool) or (not isinstance(限制值,int)) or 限制值<1 or 限制值>最大限制:#非法
        raise 会话查询错误(
            'session-search limit must be an integer between 1 and '+str(最大限制),
            'SESSION_QUERY_INVALID_LIMIT',
        )#拒绝
    return 限制值#合法限制

def 物化元数据过滤器(过滤器列表):
    """物化事件元数据过滤器并拒绝 text 子句。"""
    if not isinstance(过滤器列表,list):#非数组
        raise 会话查询错误('session-search filters must be an array','SESSION_QUERY_INVALID_FILTER')#拒绝
    for 子句 in 过滤器列表:#逐子句
        种类=子句['kind'] if 'kind' in 子句 else None#判别
        if 种类 in ('seq','time','type','surface'):#允许
            continue#下一
        if 种类=='text':#不允许
            raise 会话查询错误(
                'session-search metadata filters do not accept text clauses',
                'SESSION_QUERY_INVALID_FILTER',
            )#拒绝
        未知过滤器(子句)#未知
    return 物化会话事件结果过滤器(过滤器列表)#物化

def 归一化会话请求(请求,限制):
    """校验并规范化跨会话请求。"""
    会话过滤器=物化会话结果过滤器(请求['sessionFilters'] if 'sessionFilters' in 请求 and 请求['sessionFilters'] is not None else [])#物化会话过滤
    事件过滤器=物化元数据过滤器(请求['eventFilters'] if 'eventFilters' in 请求 and 请求['eventFilters'] is not None else [])#物化事件过滤
    游标=物化游标(请求['cursor'] if 'cursor' in 请求 else None)#游标
    结果={
        'query':归一化查询(请求['query']),
        'sessionFilters':会话过滤器,
        'eventFilters':事件过滤器,
        'limit':归一化限制(请求['limit'] if 'limit' in 请求 else None,限制),
    }#归一化体
    if 游标 is not None:#有游标
        结果['cursor']=游标#附上
    return 结果#返回

def 归一化事件请求(请求,限制):
    """校验并规范化单会话请求。"""
    if 'sessionId' not in 请求 or not isinstance(请求['sessionId'],str):#非法会话 id
        raise 会话查询错误('session-search session id must be text','SESSION_QUERY_INVALID_FILTER')#拒绝
    过滤器列表=物化元数据过滤器(请求['filters'] if 'filters' in 请求 and 请求['filters'] is not None else [])#物化过滤
    游标=物化游标(请求['cursor'] if 'cursor' in 请求 else None)#游标
    结果={
        'sessionId':请求['sessionId'],
        'query':归一化查询(请求['query']),
        'filters':过滤器列表,
        'limit':归一化限制(请求['limit'] if 'limit' in 请求 else None,限制),
    }#归一化体
    if 游标 is not None:#有游标
        结果['cursor']=游标#附上
    return 结果#返回

def 追加列表绑定(参数列表,值列表):
    """追加 IN 列表绑定并返回占位符串。"""
    校验可移植绑定数(len(参数列表)+len(值列表))#检查上限
    for 值 in 值列表:#逐值
        参数列表.append(值)#追加
    return ','.join(['?']*len(值列表))#占位符

def 追加列表(子句列表,参数列表,列,值列表):
    """追加等值 IN 子句。"""
    if len(值列表)==0:#空列表
        子句列表.append('0')#永假
        return#结束
    子句列表.append(列+' IN ('+追加列表绑定(参数列表,值列表)+')')#IN 子句

def 追加可空列表(子句列表,参数列表,列,值列表):
    """追加可空 IN 子句。"""
    if len(值列表)==0:#空列表
        子句列表.append('0')#永假
        return#结束
    具体=[值 for 值 in 值列表 if 值 is not None]#非空值
    部分=[]#OR 部分
    if len(具体)>0:#有具体值
        部分.append(列+' IN ('+追加列表绑定(参数列表,具体)+')')#IN
    if None in 值列表:#要 NULL
        部分.append(列+' IS NULL')#IS NULL
    子句列表.append('('+' OR '.join(部分)+')')#包起来

def 追加区间(子句列表,参数列表,列,区间):
    """追加数值区间子句。"""
    起点=区间['from'] if 'from' in 区间 else None#下界
    终点=区间['to'] if 'to' in 区间 else None#上界
    if 起点 is not None:#有下界
        校验可移植绑定数(len(参数列表)+1)#检查
        子句列表.append('CAST('+列+' AS INTEGER) >= ?')#>=
        参数列表.append(起点)#绑定
    if 终点 is not None:#有上界
        校验可移植绑定数(len(参数列表)+1)#检查
        子句列表.append('CAST('+列+' AS INTEGER) <= ?')#<=
        参数列表.append(终点)#绑定

def 构建会话Where(过滤器列表):
    """编译逻辑会话谓词。"""
    子句列表=[]#SQL 子句
    参数列表=[]#绑定
    for 过滤器 in 过滤器列表:#逐过滤器
        种类=过滤器['kind']#判别
        if 种类=='id':#按 id
            追加列表(子句列表,参数列表,'session_id',过滤器['values'])#IN
        elif 种类=='cwd':#按 cwd
            追加可空列表(子句列表,参数列表,'cwd',过滤器['values'])#可空 IN
        elif 种类=='created-at':#按创建时间
            追加区间(子句列表,参数列表,'created_at',过滤器)#区间
        elif 种类=='parent':#按父会话
            追加可空列表(子句列表,参数列表,'parent_session',过滤器['values'])#可空 IN
        elif 种类=='availability':#按可用性
            可用性=list(dict.fromkeys(过滤器['values']))#去重保序
            if len(可用性)==0:#空
                子句列表.append('0')#永假
            elif len(可用性)==1:#单一
                值=可用性[0]#唯一值
                if 值=='live':#活
                    子句列表.append('live = 1')#活
                elif 值=='persisted':#已持久
                    子句列表.append('persisted = 1')#持久
                else:#未知
                    未知可用性(值)#拒绝
        else:#未知
            未知过滤器(过滤器)#拒绝
    校验Fts5外层谓词数(len(子句列表))#谓词预算
    return {'sql':' AND '.join(子句列表),'params':参数列表,'predicateCount':len(子句列表)}#片段

def 构建事件Where(过滤器列表):
    """编译事件元数据谓词。"""
    子句列表=[]#SQL 子句
    参数列表=[]#绑定
    for 过滤器 in 过滤器列表:#逐过滤器
        种类=过滤器['kind']#判别
        if 种类=='seq':#按序号
            追加区间(子句列表,参数列表,'seq',过滤器)#区间
        elif 种类=='time':#按时间
            追加区间(子句列表,参数列表,'time',过滤器)#区间
        elif 种类=='type':#按类型
            追加列表(子句列表,参数列表,'type',过滤器['values'])#IN
        elif 种类=='surface':#按面
            追加列表(子句列表,参数列表,'surface',过滤器['values'])#IN
        else:#未知
            未知过滤器(过滤器)#拒绝
    校验Fts5外层谓词数(len(子句列表))#谓词预算
    return {'sql':' AND '.join(子句列表),'params':参数列表,'predicateCount':len(子句列表)}#片段

def 引用Fts数据(查询):
    """把调用方文本引用成单个 FTS5 短语。"""
    return '"'+查询.replace(chr(34),chr(34)+chr(34))+'"'#双引号转义

def 清洗Fts文本(文本):
    """去掉保留标记碰撞。"""
    return 文本.replace('\0','\uFFFD').replace(FTS高亮开始,'\uFFFD').replace(FTS高亮结束,'\uFFFD')#替换

def 过滤器指纹键(项):
    """过滤器稳定排序键。"""
    return json.dumps(项,ensure_ascii=False,separators=(',',':'),allow_nan=False,sort_keys=True)#键

def 规范过滤器(过滤器列表):
    """规范过滤器排序用于指纹。"""
    规范=[]#输出
    for 过滤器 in 过滤器列表:#逐过滤器
        if 'values' in 过滤器:#列表型
            规范.append({**过滤器,'values':sorted(过滤器['values'],key=比较可空键)})#排序值
        else:#区间型
            规范.append({
                'kind':过滤器['kind'],
                'from':过滤器['from'] if 'from' in 过滤器 and 过滤器['from'] is not None else None,
                'to':过滤器['to'] if 'to' in 过滤器 and 过滤器['to'] is not None else None,
            })#区间
    return sorted(规范,key=过滤器指纹键)#稳定排序

def 比较可空键(值):
    """可空字符串排序键：None 最小。"""
    return (值 is not None,值 if 值 is not None else '')#None 在前

def 请求指纹(请求):
    """生成游标绑定的稳定请求身份。"""
    if 'sessionId' in 请求:#事件范围
        return json.dumps({
            'scope':'events','sessionId':请求['sessionId'],
            'query':请求['query'],'filters':规范过滤器(请求['filters']),
            'limit':请求['limit'],
        },ensure_ascii=False,separators=(',',':'),allow_nan=False,sort_keys=True)#事件指纹
    return json.dumps({
        'scope':'sessions','query':请求['query'],
        'sessionFilters':规范过滤器(请求['sessionFilters']),
        'eventFilters':规范过滤器(请求['eventFilters']),
        'limit':请求['limit'],
    },ensure_ascii=False,separators=(',',':'),allow_nan=False,sort_keys=True)#会话指纹

def 规范化标记文本(标记文本):
    """去掉 FTS 标记并折叠空白。"""
    字符列表=[]#输出字符
    匹配起点=None#首个匹配位置
    for 字符 in 标记文本:#逐字符
        if 字符==FTS高亮开始:#开始
            if 匹配起点 is None:#首个
                匹配起点=len(''.join(字符列表).encode('utf-8'))#记下字节
            continue#跳过
        if 字符==FTS高亮结束:#结束
            continue#跳过
        if 单空白.match(字符) is not None:#空白
            if len(字符列表)>0 and 字符列表[-1]!=' ':#避免重复空格
                字符列表.append(' ')#单空格
        else:#普通字符
            字符列表.append(字符)#收下
    if len(字符列表)>0 and 字符列表[-1]==' ':#尾空格
        字符列表.pop()#去掉
    文本=''.join(字符列表)#纯文本
    return {'text':文本,'matchStart':匹配起点 if 匹配起点 is not None else 0}#结果

def 按字节截取(文本,起点字节,长度字节):
    """按 UTF-8 字节窗口截取，切点落在字符边界。"""
    已用=0#已用字节
    跳过=0#跳过字节
    输出=''#结果
    for 字符 in 文本:#逐码点
        宽=len(字符.encode('utf-8'))#本字符字节
        if 跳过+宽<=起点字节:#仍在窗口前
            跳过+=宽#累计跳过
            continue#下一
        if 已用+宽>长度字节:#超窗口
            break#停
        输出+=字符#追加
        已用+=宽#累计
    return 输出#片段

def 生成摘要(标记文本,最大字节):
    """生成不超过最大 UTF-8 字节的摘要。"""
    清洗=规范化标记文本(标记文本)#去标记
    干净文本=清洗['text']#纯文本
    匹配起点=清洗['matchStart']#匹配起点字节
    总字节=len(干净文本.encode('utf-8'))#总字节
    if 总字节<=最大字节:#够短
        return 干净文本#原样
    if 最大字节==1:#极短
        return '…'#省略号
    省略=len('…'.encode('utf-8'))#省略号字节
    匹配索引=min(匹配起点,max(0,总字节-1))#夹住
    起点=max(0,匹配索引-最大字节//3)#窗口起点
    前缀='…' if 起点>0 else ''#前省略
    后缀='…'#后省略
    内容长度=最大字节-len(前缀.encode('utf-8'))-len(后缀.encode('utf-8'))#可用长度
    if 内容长度<1:#放不下
        起点=匹配索引#从匹配开始
        后缀=''#无后缀
        内容长度=最大字节-len(前缀.encode('utf-8'))#重算
    elif 匹配索引>=起点+内容长度:#匹配在窗外
        起点=匹配索引-内容长度+1#右移
    终点=min(总字节,起点+内容长度)#窗口终点
    if 终点==总字节:#到末尾
        后缀=''#无后缀
        内容长度=最大字节-len(前缀.encode('utf-8'))#重算
        起点=max(0,终点-内容长度)#左移
        终点=min(总字节,起点+内容长度)#再夹
    return 前缀+按字节截取(干净文本,起点,终点-起点)+后缀#拼摘要

def 未知可用性(值):
    """未知可用性值。"""
    raise 会话查询错误(
        'session availability filter contains unknown value "'+str(值)+'"',
        'SESSION_QUERY_INVALID_FILTER',
    )#拒绝

def 未知过滤器(过滤器):
    """未知过滤器种类。"""
    种类=过滤器['kind'] if 'kind' in 过滤器 else None#种类
    描述='"'+种类+'"' if isinstance(种类,str) else '(missing)'#描述
    raise 会话查询错误(
        'session filter contains unknown kind '+描述,
        'SESSION_QUERY_INVALID_FILTER',
    )#拒绝
