import json,os,re#JSON、路径与正则
from ...会话.会话格式.文件名 import 会话格式日志文件名,解析会话格式日志文件名#持久日志名

__all__=[#仅中文公开名
    '会话夹具文件名','写者快照名','解析会话夹具名','会话夹具文件列表','会话夹具名列表',
    '会话头版本','断言会话夹具版本','持久会话文件名','解析持久会话文件名',
    '最新持久会话路径','断言持久会话版本',
]#公开面结束

夹具文件模式=re.compile(r'^session(?:\.([1-9]\d*))?(?:\.v([1-9]\d*))?\.jsonl$')#夹具文件名模式

def 断言非负安全整数(值,标签):#断言非负安全整数
    """值须为非负安全整数。"""
    if not isinstance(值,int) or isinstance(值,bool) or 值<0:#非法
        raise Exception(f'{标签} must be a non-negative safe integer')#抛错

def 会话夹具文件名(索引,版本):#构造夹具名
    """返回一份父/序与世代的规范夹具文件名。"""
    断言非负安全整数(索引,'session fixture index')#校验索引
    断言非负安全整数(版本,'Session format version')#校验版本
    序段='' if 索引==0 else f'.{索引}'#序段
    世代段='' if 版本==0 else f'.v{版本}'#世代段
    return f'session{序段}{世代段}.jsonl'#拼名

def 写者快照名(索引):#写者快照名
    """为保留的历史回放角色命名原生写者预言。"""
    断言非负安全整数(索引,'writer snapshot index')#校验索引
    return f"writer{'' if 索引==0 else f'.{索引}'}.expected.jsonl"#拼名

def 解析会话夹具名(名称):#解析夹具名
    """解析一份规范录制会话夹具文件名。"""
    匹配=夹具文件模式.match(名称)#匹配
    if 匹配 is None:#不匹配
        if 名称.startswith('session') and 名称.endswith('.jsonl'):#像夹具但非法
            raise Exception(f'invalid session fixture name: {名称}')#非法名
        return None#无关文件
    索引=0 if 匹配.group(1) is None else int(匹配.group(1))#索引
    版本=0 if 匹配.group(2) is None else int(匹配.group(2))#版本
    return {'index':索引,'version':版本,'name':名称}#解析结果

def 会话夹具文件列表(名称列表):#选择夹具文件
    """为每个父/序夹具角色选出最高世代。"""
    已选={}#按索引选最高
    身份集=set()#世代身份去重
    for 名称 in 名称列表:#逐名
        夹具=解析会话夹具名(名称)#解析
        if 夹具 is None:#无关
            continue#跳过
        身份=f"{夹具['index']}/{夹具['version']}"#身份
        if 身份 in 身份集:#重复
            raise Exception(f'duplicate session fixture generation: {名称}')#重复世代
        身份集.add(身份)#登记
        先前=已选.get(夹具['index'])#已选
        if 先前 is None or 夹具['version']>先前['version']:#更高则换
            已选[夹具['index']]=夹具#登记
    if 0 not in 已选:#缺父
        raise Exception('缺少父会话夹具')#缺父
    有序=sorted(已选.values(),key=lambda 项:项['index'])#按索引排序
    for 偏移,夹具 in enumerate(有序):#检查连续
        if 夹具['index']!=偏移:#不连续
            raise Exception(f"session fixture roles must be contiguous: expected index {偏移}, found {夹具['name']}")#报错
    return 有序#有序列表

def 会话夹具名列表(名称列表):#夹具名列表
    """校验并排序情景目录已选 Session 夹具文件名。"""
    return [项['name'] for 项 in 会话夹具文件列表(名称列表)]#取名

def 会话头版本(内容,标签):#读头版本
    """从一份 Session JSONL 头读取声明的物理世代。"""
    行=next((候选 for 候选 in 内容.splitlines() if 候选.strip()!=''),None)#首非空行
    if 行 is None:#空
        raise Exception(f'{标签}: session fixture is empty')#空文件
    try:#解析JSON
        值=json.loads(行)#解析
    except Exception as 错误:#非法JSON
        raise Exception(f'{标签}: session header contains invalid JSON') from 错误#报错
    if not isinstance(值,dict) or 值.get('type')!='session':#非session头
        raise Exception(f'{标签}: first record must be a Session header')#报错
    版本=值.get('version')#版本字段
    if not isinstance(版本,int) or isinstance(版本,bool) or 版本<0:#非法版本
        raise Exception(f'{标签}: Session header version must be a non-negative safe integer')#报错
    return 版本#返回版本

def 断言会话夹具版本(名称,内容):#断言夹具版本
    """要求夹具规范文件名世代等于其头声明。"""
    夹具=解析会话夹具名(名称)#解析名
    if 夹具 is None:#非夹具
        raise Exception(f'not a session fixture name: {名称}')#非夹具
    首行=next((候选 for 候选 in 内容.splitlines() if 候选.strip()!=''),None)#首非空行
    if 首行 is not None:#有内容
        try:#试解析
            投影=json.loads(首行)#解析
        except Exception:#非法则空
            投影=None#放弃
        if isinstance(投影,dict) and 投影.get('type')=='session' and 'version' not in 投影:#无version字段
            if 夹具['version']!=0:#文件名非v0
                raise Exception(f'{名称}: a versionless projected Session header is format v0')#冲突
            return 0#v0
    头版本=会话头版本(内容,名称)#读头版本
    if 头版本!=夹具['version']:#不一致
        raise Exception(
            f"{名称}: filename declares Session format v{夹具['version']}, header declares v{头版本}",
        )#报错
    return 头版本#返回

def 持久会话文件名(版本,压缩='raw'):#持久化文件名
    """返回一份世代与压缩的规范持久化基名。"""
    return f"{会话格式日志文件名(版本)}{'.zstd' if 压缩=='zstd' else ''}"#拼名

def 解析持久会话文件名(名称):#解析持久名
    """从 Session 自有目录解析规范持久化基名。"""
    压缩='zstd' if 名称.endswith('.zstd') else 'raw'#压缩
    基名=名称[:-len('.zstd')] if 压缩=='zstd' else 名称#去后缀
    版本=解析会话格式日志文件名(基名)#版本
    if 版本 is None:#非规范
        return None#非规范
    return {'version':版本,'compression':压缩,'name':名称}#结果

def 最新持久会话路径(路径列表,压缩='raw'):#最新持久路径
    """为每个物理 Session 目录选一条最高世代持久化路径。"""
    已选={}#按目录选最高
    for 路径 in 路径列表:#逐路径
        解析=解析持久会话文件名(os.path.basename(路径))#解析基名
        if 解析 is None or 解析['compression']!=压缩:#跳过
            continue#跳过
        目录=os.path.dirname(路径)#目录
        先前=已选.get(目录)#已选
        if 先前 is None or 解析['version']>先前['version']:#更高则换
            已选[目录]={'path':路径,'version':解析['version']}#登记
    return sorted(项['path'] for 项 in 已选.values())#排序路径

def 断言持久会话版本(名称,内容):#断言持久版本
    """要求持久化基名世代等于其 Session 头。"""
    持久=解析持久会话文件名(名称)#解析名
    if 持久 is None:#非规范
        raise Exception(f'not a canonical Session persistence filename: {名称}')#非规范
    头版本=会话头版本(内容,名称)#读头
    if 头版本!=持久['version']:#不一致
        raise Exception(
            f"{名称}: filename declares Session format v{持久['version']}, header declares v{头版本}",
        )#报错
    return 头版本#返回
