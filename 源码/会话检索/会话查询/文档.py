"""共用的事件元数据与语义文档投影。对齐上游 `session-query/src/documents.ts`。"""
from ....内核.会话 import 折叠表面#模型面折叠
from ....内核.会话.表面 import 表面错误#面折叠失败
from .配置 import 会话查询错误#检索错误
from .抽取 import 抽取会话事件文本#语义文本抽取

def 构建会话事件记录(会话号,事件列表):
    """把原始日志投影成带面位置的轻量事件记录。"""
    面表=分类面位置(事件列表)#seq到面位置
    记录列表=[]#收集记录
    for 事件 in 事件列表:#逐事件
        序号=事件['seq']#序号
        记录列表.append({
            'sessionId':会话号,#所属会话
            'seq':序号,#序号
            'type':事件['type'],#类型
            'time':事件['time'],#时间
            'surface':面表[序号] if 序号 in 面表 else 'log-only',#面位置
        })#记录结束
    return 记录列表#升序记录

def 构建会话事件搜索文档(会话号,事件列表):
    """为完整原始日志构建第一方语义文档。"""
    面表=分类面位置(事件列表)#seq到面位置
    文档列表=[]#收集文档
    for 事件 in 事件列表:#逐事件
        文本=抽取会话事件文本(事件)#语义文本
        if len(文本)==0:#结构事件
            continue#跳过
        序号=事件['seq']#序号
        文档列表.append({
            'sessionId':会话号,#所属会话
            'seq':序号,#序号
            'type':事件['type'],#类型
            'time':事件['time'],#时间
            'surface':面表[序号] if 序号 in 面表 else 'log-only',#面位置
            'text':文本,#语义文本
        })#文档结束
    return 文档列表#文档列表

def 分类面位置(事件列表):
    """经规范表面折叠给原始事件日志分类。"""
    try:#折叠当前面
        折叠=折叠表面(事件列表)#可能因非法面抛出
    except 表面错误 as 错误:#折叠失败
        raise 会话查询错误('invalid session surface: '+str(错误),'SESSION_QUERY_INVALID_SURFACE',{'cause':错误})#非法面
    结果={}#seq到面位置
    for 序号 in 折叠['nodes']:#当前面节点
        结果[序号]='current'#当前
    for 替换 in 折叠['replacements']:#每条替换
        遮蔽列表=替换['shadowedSeqs'] if 'shadowedSeqs' in 替换 else []#被遮蔽序号
        for 序号 in 遮蔽列表:#被遮蔽序号
            结果[序号]='shadowed'#被替换
    return 结果#分类表
