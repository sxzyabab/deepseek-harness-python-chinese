"""共用的事件元数据与语义文档投影。对齐上游 `session-query/src/documents.ts`。"""
from ....内核.会话 import 折叠表面#模型面折叠
from .配置 import 会话查询错误#检索错误
from .抽取 import 抽取会话事件文本#语义文本抽取

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 构建会话事件记录(会话号,事件们):#构建轻量事件记录
    """把原始日志投影成带面位置的轻量事件记录。"""
    面表=分类面位置(事件们)#seq到面位置
    记录们=[]#收集记录
    for 事件 in 事件们:#逐事件
        序号=取字段(事件,'seq')#序号
        记录们.append({#轻量记录
            'sessionId':会话号,#所属会话
            'seq':序号,#序号
            'type':取字段(事件,'type'),#类型
            'time':取字段(事件,'time'),#时间
            'surface':面表.get(序号,'log-only'),#面位置
        })#记录结束
    return 记录们#升序记录

def 构建会话事件搜索文档(会话号,事件们):#构建检索文档
    """为完整原始日志构建第一方语义文档。"""
    面表=分类面位置(事件们)#seq到面位置
    文档们=[]#收集文档
    for 事件 in 事件们:#逐事件
        文本=抽取会话事件文本(事件)#语义文本
        if len(文本)==0:#结构事件
            continue#跳过
        序号=取字段(事件,'seq')#序号
        文档们.append({#可检索文档
            'sessionId':会话号,#所属会话
            'seq':序号,#序号
            'type':取字段(事件,'type'),#类型
            'time':取字段(事件,'time'),#时间
            'surface':面表.get(序号,'log-only'),#面位置
            'text':文本,#语义文本
        })#文档结束
    return 文档们#文档列表

def 分类面位置(事件们):#按seq分类面位置
    """经规范表面折叠给原始事件日志分类。"""
    try:#折叠当前面
        折叠=折叠表面(事件们)#可能因非法面抛出
    except Exception as 错误:#折叠失败
        消息=取字段(错误,'message',str(错误)) if isinstance(错误,BaseException) else 'unknown error'#可打印消息
        raise 会话查询错误(f'invalid session surface: {消息}','SESSION_QUERY_INVALID_SURFACE',{'cause':错误})#非法面
    结果={}#seq到面位置
    for 序号 in 取字段(折叠,'nodes',[]):#当前面节点
        结果[序号]='current'#当前
    for 替换 in 取字段(折叠,'replacements',[]):#每条替换
        for 序号 in 取字段(替换,'shadowedSeqs',[]):#被遮蔽序号
            结果[序号]='shadowed'#被替换
    return 结果#分类表
