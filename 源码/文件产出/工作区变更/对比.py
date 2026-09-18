"""两侧整文件文本的逐行对比；超时后退化为整文件替换。"""
import difflib#标准库行差异
from concurrent.futures import ThreadPoolExecutor as 线程池,TimeoutError as 期货超时#带超时的对比线程
__all__=['对比文本']#仅中文公开名

#常量
上下文行数=3#统一差异默认上下文行数

def 已终止文本(文本):#保证末行有换行
    """补上末尾换行，使末行只按内容比较；空文本为零行。"""
    return 文本 if 文本=='' or 文本.endswith('\n') else 文本+'\n'#补换行

def 行列表(文本):#已终止文本的内容行
    """已终止文本的内容行；空文本为零行。"""
    return [] if 文本=='' else 文本[0:-1].split('\n')#去掉末换行再切

def 计算补丁(旧文本,新文本):#生成差异块表
    """按行生成带三行上下文的统一差异块；两侧相同则空表。"""
    旧行=行列表(旧文本)#旧侧
    新行=行列表(新文本)#新侧
    if 旧行==新行:#完全相同
        return []#无块
    匹配=difflib.SequenceMatcher(a=旧行,b=新行,autojunk=False)#按行匹配
    块表=[]#收集块
    for 组 in 匹配.get_grouped_opcodes(上下文行数):#按上下文分组
        正文=[]#块体行
        旧计数=0#旧侧行数
        新计数=0#新侧行数
        for 标记,旧起,旧止,新起,新止 in 组:#逐段
            if 标记=='equal':#上下文
                for 行 in 旧行[旧起:旧止]:#未变行
                    正文.append(' '+行)#空格前缀
                旧计数+=旧止-旧起#累加
                新计数+=新止-新起#累加
            elif 标记=='replace':#替换
                for 行 in 旧行[旧起:旧止]:#删
                    正文.append('-'+行)#减号
                for 行 in 新行[新起:新止]:#加
                    正文.append('+'+行)#加号
                旧计数+=旧止-旧起#累加
                新计数+=新止-新起#累加
            elif 标记=='delete':#删除
                for 行 in 旧行[旧起:旧止]:#删
                    正文.append('-'+行)#减号
                旧计数+=旧止-旧起#累加
            elif 标记=='insert':#插入
                for 行 in 新行[新起:新止]:#加
                    正文.append('+'+行)#加号
                新计数+=新止-新起#累加
        旧起始下标=组[0][1]#组内旧起点
        新起始下标=组[0][3]#组内新起点
        旧起始=旧起始下标+1 if 旧计数>0 else (1 if 旧起始下标==0 else 旧起始下标)#1基；空侧从1
        新起始=新起始下标+1 if 新计数>0 else (1 if 新起始下标==0 else 新起始下标)#1基；空侧从1
        块表.append({'oldStart':旧起始,'oldLines':旧计数,'newStart':新起始,'newLines':新计数,'lines':正文})#一块
    return 块表#文件序

def 粗糙块表(旧文本,新文本):#整文件替换块
    """超时退化：删掉全部旧行再加全部新行。"""
    旧行=行列表(旧文本)#旧
    新行=行列表(新文本)#新
    正文=['-'+行 for 行 in 旧行]+['+'+行 for 行 in 新行]#整侧替换
    return [{'oldStart':1,'oldLines':len(旧行),'newStart':1,'newLines':len(新行),'lines':正文}]#单块

def 对比文本(之前,之后,超时毫秒):#逐行对比
    """逐行对比两侧文本；某侧 None 表示文件不存在；超时则粗糙替换。"""
    旧文本=已终止文本('' if 之前 is None else 之前)#旧侧
    新文本=已终止文本('' if 之后 is None else 之后)#新侧
    粗糙=False#是否超时退化
    try:#限时计算
        with 线程池(max_workers=1) as 池:#单线程池
            未来=池.submit(计算补丁,旧文本,新文本)#提交
            块表=未来.result(timeout=超时毫秒/1000.0)#等待
    except 期货超时:#超时
        粗糙=True#标记
        块表=粗糙块表(旧文本,新文本)#退化
    新增=0#加行合计
    删除=0#删行合计
    for 块 in 块表:#逐块
        for 行 in 块['lines']:#逐行
            if 行.startswith('+'):#新增
                新增+=1#加一
            elif 行.startswith('-'):#删除
                删除+=1#加一
    return {'hunks':块表,'coarse':粗糙,'added':新增,'deleted':删除}#对比结果
