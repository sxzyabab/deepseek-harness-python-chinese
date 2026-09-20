"""与提供方无关的逻辑会话与事件文本纯谓词。"""
import re#文本过滤器正则
from .配置 import 会话查询错误#检索错误

空白切分=re.compile(r'\s+',re.ASCII)#ASCII 空白

def 过滤会话结果(记录列表,过滤器列表=None):
    """套用与运算的逻辑会话过滤器，并保持输入顺序。"""
    子句列表=[] if 过滤器列表 is None else 过滤器列表#缺省空
    谓词列表=[会话谓词(子句) for 子句 in 子句列表]#编译谓词
    结果=[]#匹配记录
    for 记录 in 记录列表:#逐条
        if all(谓词(记录) for 谓词 in 谓词列表):#全部命中
            结果.append(记录)#收下
    return 结果#保持顺序

def 过滤会话事件文档(文档列表,过滤器列表=None):
    """对语义文档套用与运算的事件过滤器。"""
    子句列表=[] if 过滤器列表 is None else 过滤器列表#缺省空
    谓词列表=[事件谓词(子句) for 子句 in 子句列表]#编译谓词
    结果=[]#匹配文档
    for 文档 in 文档列表:#逐条
        if all(谓词(文档) for 谓词 in 谓词列表):#全部命中
            结果.append(文档)#收下
    return 结果#保持顺序

def 物化会话结果过滤器(过滤器列表):
    """在跨过异步边界之前复制并校验逻辑会话过滤器。"""
    校验数组(过滤器列表)#必须是数组
    副本=[]#脱离副本
    for 子句 in 过滤器列表:#逐子句
        种类=子句['kind']#判别标签
        if 种类=='id':#按id
            副本.append({'kind':'id','values':复制字符串列表('id',子句['values'])})#复制
        elif 种类=='cwd':#按工作目录
            副本.append({'kind':'cwd','values':复制可空字符串列表('cwd',子句['values'])})#复制
        elif 种类=='created-at':#按创建时间
            副本.append(复制区间('created-at',子句))#复制区间
        elif 种类=='parent':#按父会话
            副本.append({'kind':'parent','values':复制可空字符串列表('parent',子句['values'])})#复制
        elif 种类=='availability':#按可用性
            值列表=复制字符串列表('availability',子句['values'])#复制
            校验允许值('availability',值列表,['live','persisted'])#只允许活或已持久
            副本.append({'kind':'availability','values':值列表})#收下
        else:#未知
            未知过滤器(子句)#大声失败
    return 副本#脱离副本

def 物化会话事件结果过滤器(过滤器列表):
    """在跨过异步边界之前复制并校验事件过滤器。"""
    校验数组(过滤器列表)#必须是数组
    副本=[]#脱离副本
    for 子句 in 过滤器列表:#逐子句
        种类=子句['kind']#判别标签
        if 种类 in ('seq','time'):#区间类
            副本.append(复制区间(种类,子句))#复制区间
        elif 种类=='type':#按类型
            副本.append({'kind':'type','values':复制字符串列表('type',子句['values'])})#复制
        elif 种类=='surface':#按面位置
            值列表=复制字符串列表('surface',子句['values'])#复制
            校验允许值('surface',值列表,['current','shadowed','log-only'])#三种面
            副本.append({'kind':'surface','values':值列表})#收下
        elif 种类=='text':#按字面文本
            文本=子句['text']#文本
            if not isinstance(文本,str):#必须是字符串
                raise 非法过滤('text filter text must be a string')#拒绝
            副本.append({'kind':'text','text':文本})#复制
        else:#未知
            未知过滤器(子句)#大声失败
    return 副本#脱离副本

def 编译会话文本过滤器(文本):
    """编译字面、大小写不敏感、空白灵活的语义文本匹配。"""
    修剪=文本.strip()#去两端空白
    if len(修剪)==0:#不能只剩空白
        raise 会话查询错误('session text filter must contain non-whitespace text','SESSION_QUERY_INVALID_FILTER')#拒绝
    片段=[re.escape(段) for 段 in 空白切分.split(修剪)]#按空白分词并转义
    模式='\\s+'.join(片段)#词间允许空白
    return re.compile(模式,re.IGNORECASE|re.ASCII)#大小写不敏感 ASCII 空白

def 会话谓词(子句):
    """编译一条逻辑会话过滤器为谓词。"""
    种类=子句['kind']#判别标签
    if 种类=='id':#按id
        值列表=子句['values']#id列表
        def 按标识(记录):
            """id 在列表。"""
            return 记录['header']['id'] in 值列表#id在列表
        return 按标识#谓词
    if 种类=='cwd':#按工作目录
        值列表=子句['values']#cwd列表
        def 按目录(记录):
            """cwd 或 null。"""
            头=记录['header']#头
            目录=头['cwd'] if 'cwd' in 头 else None#cwd
            return 目录 in 值列表#cwd或null
        return 按目录#谓词
    if 种类=='created-at':#按创建时间
        区间=校验区间('created-at',子句)#校验区间
        def 按创建(记录):
            """创建时间区间。"""
            return 落在区间内(记录['header']['createdAt'],区间)#时间区间
        return 按创建#谓词
    if 种类=='parent':#按父会话
        值列表=子句['values']#父id列表
        def 按父(记录):
            """父或 null。"""
            头=记录['header']#头
            父=头['parentSession'] if 'parentSession' in 头 else None#父
            return 父 in 值列表#父或null
        return 按父#谓词
    if 种类=='availability':#按可用性
        值列表=子句['values']#可用性列表
        校验允许值('availability',值列表,['live','persisted'])#只允许活或已持久
        def 按可用性(记录):
            """任一可用性命中。"""
            for 值 in 值列表:#逐值
                if 值=='live' and 记录['live']:#活
                    return True#命中
                if 值=='persisted' and 记录['persisted']:#已持久
                    return True#命中
            return False#未命中
        return 按可用性#谓词
    return 未知过滤器(子句)#未知kind

def 事件谓词(子句):
    """编译一条事件过滤器为谓词。"""
    种类=子句['kind']#判别标签
    if 种类=='seq':#按序号
        区间=校验区间('seq',子句)#校验区间
        def 按序号(文档):
            """序号区间。"""
            return 落在区间内(文档['seq'],区间)#序号区间
        return 按序号#谓词
    if 种类=='time':#按时间
        区间=校验区间('time',子句)#校验区间
        def 按时间(文档):
            """时间区间。"""
            return 落在区间内(文档['time'],区间)#时间区间
        return 按时间#谓词
    if 种类=='type':#按类型
        值列表=子句['values']#类型列表
        def 按类型(文档):
            """类型在列表。"""
            return 文档['type'] in 值列表#类型在列表
        return 按类型#谓词
    if 种类=='surface':#按面位置
        值列表=子句['values']#面列表
        校验允许值('surface',值列表,['current','shadowed','log-only'])#三种面
        def 按面(文档):
            """面在列表。"""
            return 文档['surface'] in 值列表#面在列表
        return 按面#谓词
    if 种类=='text':#按字面文本
        模式=编译会话文本过滤器(子句['text'])#编译正则
        def 按文本(文档):
            """语义文本匹配。"""
            return 模式.search(文档['text']) is not None#语义文本匹配
        return 按文本#谓词
    return 未知过滤器(子句)#未知kind

def 复制字符串列表(名,值列表):
    """复制并校验字符串列表。"""
    if not isinstance(值列表,list) or any(not isinstance(值,str) for 值 in 值列表):#必须是字符串数组
        raise 非法过滤(名+' filter values must be an array of strings')#拒绝
    return list(值列表)#浅拷贝

def 复制可空字符串列表(名,值列表):
    """复制并校验字符串或 null 列表。"""
    if not isinstance(值列表,list) or any(值 is not None and not isinstance(值,str) for 值 in 值列表):#字符串或null
        raise 非法过滤(名+' filter values must be an array of strings or null')#拒绝
    return list(值列表)#浅拷贝

def 校验数组(值):
    """过滤器必须是数组。"""
    if not isinstance(值,list):#非数组
        raise 非法过滤('filters must be an array')#拒绝

def 复制区间(种类,区间):
    """复制并校验区间过滤器。"""
    副本={'kind':种类}#带kind
    if 'from' in 区间 and 区间['from'] is not None:#有下界
        副本['from']=区间['from']#下界
    if 'to' in 区间 and 区间['to'] is not None:#有上界
        副本['to']=区间['to']#上界
    校验区间(种类,副本)#校验副本
    return 副本#返回副本

def 未知过滤器(子句):
    """未知过滤器 kind 大声失败。"""
    种类=子句['kind'] if 'kind' in 子句 else None#取出kind
    展示='"'+种类+'"' if isinstance(种类,str) else '(missing)'#可打印kind
    raise 非法过滤('unknown filter kind '+展示)#抛出

def 校验允许值(名,值列表,允许):
    """断言过滤器值落在允许表。"""
    for 值 in 值列表:#逐个检查
        if 值 not in 允许:#不在允许表
            raise 会话查询错误('session '+名+' filter contains unknown value "'+str(值)+'"','SESSION_QUERY_INVALID_FILTER')#拒绝

def 校验区间(名,区间):
    """校验闭区间端点。"""
    下界=区间['from'] if 'from' in 区间 else None#下界
    上界=区间['to'] if 'to' in 区间 else None#上界
    if 下界 is not None and (isinstance(下界,bool) or not isinstance(下界,(int,float))):#下界必须有限
        raise 非法区间(名,'from must be finite')#拒绝
    if 上界 is not None and (isinstance(上界,bool) or not isinstance(上界,(int,float))):#上界必须有限
        raise 非法区间(名,'to must be finite')#拒绝
    if 下界 is not None and 上界 is not None and 下界>上界:#颠倒区间
        raise 非法区间(名,'from must be less than or equal to to')#拒绝
    return 区间#返回原区间

def 落在区间内(值,区间):
    """值是否落在闭区间内。"""
    下界=区间['from'] if 'from' in 区间 else None#下界
    上界=区间['to'] if 'to' in 区间 else None#上界
    if 下界 is not None and 值<下界:#低于下界
        return False#不命中
    if 上界 is not None and 值>上界:#高于上界
        return False#不命中
    return True#命中

def 非法区间(名,细节):
    """包装区间错误。"""
    return 非法过滤(名+' filter '+细节)#统一过滤错误

def 非法过滤(细节):
    """包装过滤错误。"""
    return 会话查询错误('session '+细节,'SESSION_QUERY_INVALID_FILTER')#非法过滤
