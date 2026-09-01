"""与提供方无关的逻辑会话与事件文本纯谓词。对齐上游 `session-query/src/filters.ts`。"""
import re#文本过滤器正则
from .配置 import 会话查询错误#检索错误

def 过滤会话结果(记录们,过滤器们=[]):#过滤会话记录
    """套用与运算的逻辑会话过滤器，并保持输入顺序。"""
    谓词们=[会话谓词(子句) for 子句 in 过滤器们]#编译谓词
    结果=[]#匹配记录
    for 记录 in 记录们:#逐条
        if all(谓词(记录) for 谓词 in 谓词们):#全部命中
            结果.append(记录)#收下
    return 结果#保持顺序

def 过滤会话事件文档(文档们,过滤器们=[]):#过滤事件文档
    """对语义文档套用与运算的事件过滤器。"""
    谓词们=[事件谓词(子句) for 子句 in 过滤器们]#编译谓词
    结果=[]#匹配文档
    for 文档 in 文档们:#逐条
        if all(谓词(文档) for 谓词 in 谓词们):#全部命中
            结果.append(文档)#收下
    return 结果#保持顺序

def 物化会话结果过滤器(过滤器们):#物化会话过滤器
    """在跨过异步边界之前复制并校验逻辑会话过滤器。"""
    断言数组(过滤器们)#必须是数组
    副本=[]#脱离副本
    for 子句 in 过滤器们:#逐子句
        种类=取字段(子句,'kind')#判别标签
        if 种类=='id':#按id
            副本.append({'kind':'id','values':复制字符串列表('id',取字段(子句,'values'))})#复制
        elif 种类=='cwd':#按工作目录
            副本.append({'kind':'cwd','values':复制可空字符串列表('cwd',取字段(子句,'values'))})#复制
        elif 种类=='created-at':#按创建时间
            副本.append(复制区间('created-at',子句))#复制区间
        elif 种类=='parent':#按父会话
            副本.append({'kind':'parent','values':复制可空字符串列表('parent',取字段(子句,'values'))})#复制
        elif 种类=='availability':#按可用性
            值们=复制字符串列表('availability',取字段(子句,'values'))#复制
            断言允许值('availability',值们,['live','persisted'])#只允许活或已持久
            副本.append({'kind':'availability','values':值们})#收下
        else:#未知
            未知过滤器(子句)#大声失败
    return 副本#脱离副本

def 物化会话事件结果过滤器(过滤器们):#物化事件过滤器
    """在跨过异步边界之前复制并校验事件过滤器。"""
    断言数组(过滤器们)#必须是数组
    副本=[]#脱离副本
    for 子句 in 过滤器们:#逐子句
        种类=取字段(子句,'kind')#判别标签
        if 种类 in ('seq','time'):#区间类
            副本.append(复制区间(种类,子句))#复制区间
        elif 种类=='type':#按类型
            副本.append({'kind':'type','values':复制字符串列表('type',取字段(子句,'values'))})#复制
        elif 种类=='surface':#按面位置
            值们=复制字符串列表('surface',取字段(子句,'values'))#复制
            断言允许值('surface',值们,['current','shadowed','log-only'])#三种面
            副本.append({'kind':'surface','values':值们})#收下
        elif 种类=='text':#按字面文本
            文本=取字段(子句,'text')#文本
            if not isinstance(文本,str):#必须是字符串
                raise 非法过滤('text filter text must be a string')#拒绝
            副本.append({'kind':'text','text':文本})#复制
        else:#未知
            未知过滤器(子句)#大声失败
    return 副本#脱离副本

def 编译会话文本过滤器(文本):#编译文本过滤器
    """编译字面、大小写不敏感、空白灵活的语义文本匹配。"""
    修剪=文本.strip()#去两端空白
    if len(修剪)==0:#不能只剩空白
        raise 会话查询错误('session text filter must contain non-whitespace text','SESSION_QUERY_INVALID_FILTER')#拒绝
    片段=[re.escape(段) for 段 in re.split(r'\s+',修剪)]#按空白分词并转义
    模式='\\s+'.join(片段)#词间允许空白
    return re.compile(模式,re.IGNORECASE|re.UNICODE)#大小写不敏感

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 会话谓词(子句):#编译会话谓词
    """编译一条逻辑会话过滤器为谓词。"""
    种类=取字段(子句,'kind')#判别标签
    if 种类=='id':#按id
        值们=取字段(子句,'values')#id列表
        return lambda 记录: 取字段(取字段(记录,'header'),'id') in 值们#id在列表
    if 种类=='cwd':#按工作目录
        值们=取字段(子句,'values')#cwd列表
        return lambda 记录: (取字段(取字段(记录,'header'),'cwd') or None) in 值们#cwd或null
    if 种类=='created-at':#按创建时间
        区间=校验区间('created-at',子句)#校验区间
        return lambda 记录: 落在区间内(取字段(取字段(记录,'header'),'createdAt'),区间)#时间区间
    if 种类=='parent':#按父会话
        值们=取字段(子句,'values')#父id列表
        return lambda 记录: (取字段(取字段(记录,'header'),'parentSession') or None) in 值们#父或null
    if 种类=='availability':#按可用性
        值们=取字段(子句,'values')#可用性列表
        断言允许值('availability',值们,['live','persisted'])#只允许活或已持久
        return lambda 记录: any(
            (值=='live' and 取字段(记录,'live')) or (值=='persisted' and 取字段(记录,'persisted'))
            for 值 in 值们
        )#任一命中
    return 未知过滤器(子句)#未知kind

def 事件谓词(子句):#编译事件谓词
    """编译一条事件过滤器为谓词。"""
    种类=取字段(子句,'kind')#判别标签
    if 种类=='seq':#按序号
        区间=校验区间('seq',子句)#校验区间
        return lambda 文档: 落在区间内(取字段(文档,'seq'),区间)#序号区间
    if 种类=='time':#按时间
        区间=校验区间('time',子句)#校验区间
        return lambda 文档: 落在区间内(取字段(文档,'time'),区间)#时间区间
    if 种类=='type':#按类型
        值们=取字段(子句,'values')#类型列表
        return lambda 文档: 取字段(文档,'type') in 值们#类型在列表
    if 种类=='surface':#按面位置
        值们=取字段(子句,'values')#面列表
        断言允许值('surface',值们,['current','shadowed','log-only'])#三种面
        return lambda 文档: 取字段(文档,'surface') in 值们#面在列表
    if 种类=='text':#按字面文本
        模式=编译会话文本过滤器(取字段(子句,'text'))#编译正则
        return lambda 文档: 模式.search(取字段(文档,'text')) is not None#语义文本匹配
    return 未知过滤器(子句)#未知kind

def 复制字符串列表(名,值们):#复制字符串列表
    """复制并校验字符串列表。"""
    if not isinstance(值们,list) or any(not isinstance(值,str) for 值 in 值们):#必须是字符串数组
        raise 非法过滤(f'{名} filter values must be an array of strings')#拒绝
    return list(值们)#浅拷贝

def 复制可空字符串列表(名,值们):#复制可空字符串列表
    """复制并校验字符串或 null 列表。"""
    if not isinstance(值们,list) or any(值 is not None and not isinstance(值,str) for 值 in 值们):#字符串或null
        raise 非法过滤(f'{名} filter values must be an array of strings or null')#拒绝
    return list(值们)#浅拷贝

def 断言数组(值):#断言过滤器是数组
    """过滤器必须是数组。"""
    if not isinstance(值,list):#非数组
        raise 非法过滤('filters must be an array')#拒绝

def 复制区间(种类,区间):#复制区间过滤器
    """复制并校验区间过滤器。"""
    副本={'kind':种类}#带kind
    if 取字段(区间,'from') is not None:#有下界
        副本['from']=取字段(区间,'from')#下界
    if 取字段(区间,'to') is not None:#有上界
        副本['to']=取字段(区间,'to')#上界
    校验区间(种类,副本)#校验副本
    return 副本#返回副本

def 未知过滤器(子句):#未知过滤器kind
    """未知过滤器 kind 大声失败。"""
    种类=取字段(子句,'kind')#取出kind
    展示=f'"{种类}"' if isinstance(种类,str) else '(missing)'#可打印kind
    raise 非法过滤(f'unknown filter kind {展示}')#抛出

def 断言允许值(名,值们,允许):#断言值落在允许表
    """断言过滤器值落在允许表。"""
    for 值 in 值们:#逐个检查
        if 值 not in 允许:#不在允许表
            raise 会话查询错误(f'session {名} filter contains unknown value "{值}"','SESSION_QUERY_INVALID_FILTER')#拒绝

def 校验区间(名,区间):#校验区间
    """校验闭区间端点。"""
    下界=取字段(区间,'from')#下界
    上界=取字段(区间,'to')#上界
    if 下界 is not None and not isinstance(下界,(int,float)):#下界必须有限
        raise 非法区间(名,'from must be finite')#拒绝
    if 上界 is not None and not isinstance(上界,(int,float)):#上界必须有限
        raise 非法区间(名,'to must be finite')#拒绝
    if 下界 is not None and 上界 is not None and 下界>上界:#颠倒区间
        raise 非法区间(名,'from must be less than or equal to to')#拒绝
    return 区间#返回原区间

def 落在区间内(值,区间):#值是否落在闭区间
    """值是否落在闭区间内。"""
    下界=取字段(区间,'from')#下界
    上界=取字段(区间,'to')#上界
    if 下界 is not None and 值<下界:#低于下界
        return False#不命中
    if 上界 is not None and 值>上界:#高于上界
        return False#不命中
    return True#命中

def 非法区间(名,细节):#包装区间错误
    """包装区间错误。"""
    return 非法过滤(f'{名} filter {细节}')#统一过滤错误

def 非法过滤(细节):#包装过滤错误
    """包装过滤错误。"""
    return 会话查询错误(f'session {细节}','SESSION_QUERY_INVALID_FILTER')#非法过滤
