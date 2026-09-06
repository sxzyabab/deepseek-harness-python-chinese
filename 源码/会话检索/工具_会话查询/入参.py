"""模型参数模式、归一化与过滤器构造。对齐上游 `tool-session-query/src/input.ts`。"""
import re#正则
from datetime import datetime,timedelta,timezone#写死 ISO 解析
from ..会话查询 import 会话查询错误#检索错误

会话搜索参数={
    'query':{'type':'string','required':True,'description':'Literal full-text query over prior session history.'},
    'session_ids':{'type':'array','items':{'type':'string'},'description':'Optional session ids to include.'},
    'created_at_from':{'type':'string','description':'Inclusive timezone-qualified ISO 8601 creation-time lower bound.'},
    'created_at_to':{'type':'string','description':'Inclusive timezone-qualified ISO 8601 creation-time upper bound.'},
    'parent_session_ids':{'type':'array','items':{'type':'string'},'description':'Optional direct parent session ids.'},
    'include_root_sessions':{'type':'boolean','description':'Include sessions with no parent in the parent filter.'},
    'availability':{'type':'array','items':{'type':'string','enum':['live','persisted']},'description':'Require at least one selected source availability.'},
    'event_seq_from':{'type':'integer','description':'Inclusive event sequence lower bound.'},
    'event_seq_to':{'type':'integer','description':'Inclusive event sequence upper bound.'},
    'event_time_from':{'type':'string','description':'Inclusive timezone-qualified ISO 8601 event-time lower bound.'},
    'event_time_to':{'type':'string','description':'Inclusive timezone-qualified ISO 8601 event-time upper bound.'},
    'event_types':{'type':'array','items':{'type':'string'},'description':'Event types to include.'},
    'event_surfaces':{'type':'array','items':{'type':'string','enum':['current','shadowed','log-only']},'description':'Event surfaces to include.'},
}#会话搜索参数

事件搜索参数={
    'session_id':{'type':'string','description':'Target session id. Omit for the current session.'},
    'query':{'type':'string','required':True,'description':'Literal full-text query over the target session.'},
    'seq_from':{'type':'integer','description':'Inclusive event sequence lower bound.'},
    'seq_to':{'type':'integer','description':'Inclusive event sequence upper bound.'},
    'time_from':{'type':'string','description':'Inclusive timezone-qualified ISO 8601 event-time lower bound.'},
    'time_to':{'type':'string','description':'Inclusive timezone-qualified ISO 8601 event-time upper bound.'},
    'event_types':{'type':'array','items':{'type':'string'},'description':'Event types to include.'},
    'surfaces':{'type':'array','items':{'type':'string','enum':['current','shadowed','log-only']},'description':'Event surfaces to include.'},
}#事件搜索参数

目标会话参数={'session_id':{'type':'string','description':'Target session id. Omit for the current session.'}}#目标会话参数
空白=re.compile(r'\s+',re.ASCII)#ASCII 空白
ISO时间戳=re.compile(r'^([0-9]{4})-([0-9]{2})-([0-9]{2})T([0-9]{2}):([0-9]{2})(?::([0-9]{2})(?:\.([0-9]+))?)?(Z|([+-])([0-9]{2}):([0-9]{2}))\Z',re.ASCII)#ISO形态

def 构建会话过滤器(参数):
    """从模型参数构建会话过滤器。"""
    过滤器列表=[]#收集子句
    if 'session_ids' in 参数 and 参数['session_ids'] is not None:#给了会话id
        校验非空数组('session_ids',参数['session_ids'])#不得空数组
        过滤器列表.append({'kind':'id','values':参数['session_ids']})#按id过滤
    创建区间=时间戳区间('created_at',参数['created_at_from'] if 'created_at_from' in 参数 else None,参数['created_at_to'] if 'created_at_to' in 参数 else None)#创建时间区间
    if 创建区间 is not None:#有区间
        过滤器列表.append({'kind':'created-at',**创建区间})#加上
    if 'availability' in 参数 and 参数['availability'] is not None:#给了可用性
        校验非空数组('availability',参数['availability'])#不得空数组
        过滤器列表.append({'kind':'availability','values':参数['availability']})#按可用性过滤
    return 过滤器列表#返回子句

def 物化父会话号列表(值列表):
    """物化并去重父会话 id。"""
    if 值列表 is None:#缺省则无
        return None#无
    校验非空数组('parent_session_ids',值列表)#不得空数组
    return list(dict.fromkeys(值列表))#去重

def 构建事件过滤器(输入):
    """从入参构建事件过滤器。"""
    过滤器列表=[]#收集子句
    序号=序号区间(输入['seqFrom'] if 'seqFrom' in 输入 else None,输入['seqTo'] if 'seqTo' in 输入 else None)#序号区间
    if ('from' in 序号) or ('to' in 序号):#有端点
        过滤器列表.append({'kind':'seq',**序号})#加上
    时间=时间戳区间('time',输入['timeFrom'] if 'timeFrom' in 输入 else None,输入['timeTo'] if 'timeTo' in 输入 else None)#时间区间
    if 时间 is not None:#有区间
        过滤器列表.append({'kind':'time',**时间})#加上
    if 'eventTypes' in 输入 and 输入['eventTypes'] is not None:#给了类型
        校验非空数组('event_types',输入['eventTypes'])#不得空数组
        过滤器列表.append({'kind':'type','values':输入['eventTypes']})#按类型过滤
    if 'surfaces' in 输入 and 输入['surfaces'] is not None:#给了面位置
        校验非空数组('surfaces',输入['surfaces'])#不得空数组
        过滤器列表.append({'kind':'surface','values':输入['surfaces']})#按面过滤
    return 过滤器列表#返回子句

def 规范化查询(值):
    """规范化查询文本。"""
    查询=空白.sub(' ',值.strip(),count=0)#压空白
    if len(查询)==0:#不能只剩空白
        raise 会话查询错误('session-search query must contain non-whitespace text','SESSION_QUERY_INVALID_QUERY')#拒绝
    if '\0' in 查询:#不得含NUL
        raise 会话查询错误('session-search query must not contain NUL','SESSION_QUERY_INVALID_QUERY')#拒绝
    return 查询#返回规范化查询

def 序号区间(下界,上界):
    """规范化序号区间。"""
    if 下界 is not None:#有下界
        校验非负安全整数('sequence lower bound',下界)#校验
    if 上界 is not None:#有上界
        校验非负安全整数('sequence upper bound',上界)#校验
    if 下界 is not None and 上界 is not None and 下界>上界:#颠倒
        raise 非法区间('sequence','from must be less than or equal to to')#拒绝
    结果={}#区间对象
    if 下界 is not None:#写下界
        结果['from']=下界#下界
    if 上界 is not None:#写上界
        结果['to']=上界#上界
    return 结果#返回区间

def 时间戳区间(名,下界文本,上界文本):
    """解析 ISO 8601 时间区间。"""
    if 下界文本 is None and 上界文本 is None:#两端都缺
        return None#无区间
    下界=None if 下界文本 is None else 解析iso时间戳(名+'_from',下界文本)#下界
    上界=None if 上界文本 is None else 解析iso时间戳(名+'_to',上界文本)#上界
    if 下界 is not None and 上界 is not None and 比较时间戳(下界,上界)>0:#颠倒
        raise 非法区间(名,'from must be less than or equal to to')#拒绝
    结果={}#毫秒区间
    if 下界 is not None:#写下界
        结果['from']=时间戳下界(下界)#下界毫秒
    if 上界 is not None:#写上界
        结果['to']=时间戳上界(上界)#上界毫秒
    return 结果#返回区间

def 解析iso时间戳(名,值):
    """解析带时区 ISO 8601 时间；格式在翻译时写死，不用 fromisoformat。"""
    匹配=ISO时间戳.match(值)#匹配
    if 匹配 is None:#形态不对
        raise 非法区间(名,'must be an ISO 8601 timestamp with Z or a numeric offset')#拒绝
    try:#按捕获组构造
        年=int(匹配.group(1))#年
        月=int(匹配.group(2))#月
        日=int(匹配.group(3))#日
        时=int(匹配.group(4))#时
        分=int(匹配.group(5))#分
        秒=int(匹配.group(6)) if 匹配.group(6) is not None else 0#秒
        小数=匹配.group(7) if 匹配.group(7) is not None else ''#小数秒
        微秒文本=(小数+'000000')[:6]#微秒
        微秒=int(微秒文本) if 微秒文本!='' else 0#微秒
        if 匹配.group(8)=='Z':#UTC
            区=timezone.utc#UTC
        else:#数字偏移
            符号=匹配.group(9)#正负
            偏时=int(匹配.group(10))#时
            偏分=int(匹配.group(11))#分
            偏移=timedelta(hours=偏时,minutes=偏分)#偏移
            if 符号=='-':#西向
                偏移=-偏移#取负
            区=timezone(偏移)#固定偏移
        时刻=datetime(年,月,日,时,分,秒,微秒,tzinfo=区)#时刻
    except ValueError:#非法日历
        raise 非法区间(名,'must be a valid ISO 8601 timestamp')#拒绝
    毫秒=int(时刻.timestamp()*1000)#毫秒
    余数=小数[3:].rstrip('0') if len(小数)>3 else ''#亚毫秒余数
    return {'millisecond':毫秒,'remainder':余数}#精确时间

def 比较时间戳(左,右):
    """比较两份精确时间。"""
    if 左['millisecond']!=右['millisecond']:#毫秒不同
        return (左['millisecond']>右['millisecond'])-(左['millisecond']<右['millisecond'])#比较
    长度=max(len(左['remainder']),len(右['remainder']))#对齐长度
    for 下标 in range(长度):#逐位比
        左位=左['remainder'][下标] if 下标<len(左['remainder']) else '0'#缺位当0
        右位=右['remainder'][下标] if 下标<len(右['remainder']) else '0'#缺位当0
        if 左位!=右位:#不同
            return (左位>右位)-(左位<右位)#比较
    return 0#相等

def 时间戳下界(时间戳):
    """闭区间下界毫秒。"""
    return 时间戳['millisecond'] if 时间戳['remainder']=='' else 时间戳['millisecond']+1#闭区间下界

def 时间戳上界(时间戳):
    """闭区间上界毫秒。"""
    return 时间戳['millisecond']#闭区间上界

def 非法区间(名,细节):
    """包装区间错误。"""
    return 会话查询错误('session '+名+' range '+细节,'SESSION_QUERY_INVALID_FILTER')#包装区间错误

def 校验非负安全整数(名,值):
    """断言非负整数；外来 JSON 入口排除布尔。"""
    if isinstance(值,bool) or (not isinstance(值,int)) or 值<0:#非法
        raise 会话查询错误(名+' must be a non-negative safe integer','SESSION_QUERY_INVALID_FILTER')#拒绝

def 校验非空数组(名,值列表):
    """校验非空数组。"""
    if not isinstance(值列表,list) or len(值列表)==0:#空数组
        raise 会话查询错误(名+' must contain at least one value when supplied','SESSION_QUERY_INVALID_FILTER')#拒绝

工具入参={
    'sessionSearchParameters':会话搜索参数,
    'eventSearchParameters':事件搜索参数,
    'targetSessionParameter':目标会话参数,
    'buildSessionFilters':构建会话过滤器,
    'materializeParentSessionIds':物化父会话号列表,
    'buildEventFilters':构建事件过滤器,
    'normalizeQuery':规范化查询,
    'sequenceRange':序号区间,
    'assertNonNegativeSafeInteger':校验非负安全整数,
}#工具入参面
