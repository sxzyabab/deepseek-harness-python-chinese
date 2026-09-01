"""磁盘上的 JSON 单元格式。"""
import json#JSON 编解码
from ..存储.错误 import 存储错误#存储错误
__all__=['单元状态','序列化','解析','序列化记录','解析记录']#仅中文公开名

class 单元状态:#内存权威状态
    """一个单元的内存权威状态；文件是它的投影。"""
    def __init__(自身,版本,全局值,表):#构造状态
        自身.version=版本#单元版本
        自身.全局值=全局值#全局；未写为 None
        自身.tables=表#表名到记录映射

def 序列化(名称,状态):#整单元序列化
    """把单元状态序列成带尾换行的美化 JSON。"""
    表投影={}#表到对象
    for 表名,记录 in 状态.tables.items():#每张表
        表投影[表名]=dict(记录)#Map 转 dict
    文档={'unit':{'name':名称,'version':状态.version},'global':状态.全局值,'tables':表投影}#磁盘文档
    return json.dumps(文档,indent=2,ensure_ascii=False)+'\n'#美化加换行

def 解析(文本,描述符):#解析整单元文件
    """解析文件内容并校验形态与版本。"""
    try:#JSON 解析
        文档=json.loads(文本)#解析文本
    except json.JSONDecodeError as 错误:#非法 JSON
        raise 存储错误('malformed-medium',f"unit '{描述符.name}': file is not valid JSON",原因=错误) from 错误#损坏
    if not isinstance(文档,dict):#不是对象
        raise 存储错误('malformed-medium',f"unit '{描述符.name}': file is not a JSON object")#损坏
    单元头=文档.get('unit')#单元头
    if not isinstance(单元头,dict) or 单元头.get('name')!=描述符.name or not isinstance(单元头.get('version'),(int,float)):#头非法
        raise 存储错误('malformed-medium',f"unit '{描述符.name}': missing or foreign unit header")#损坏
    版本=int(单元头['version'])#取版本
    if 版本!=描述符.version:#版本不匹配
        raise 存储错误('version-mismatch',f"unit '{描述符.name}': stored version {版本} != expected {描述符.version}")#拒绝
    表对象=文档.get('tables')#表对象
    if not isinstance(表对象,dict):#tables 不是对象
        raise 存储错误('malformed-medium',f"unit '{描述符.name}': tables is not an object")#损坏
    表映射={}#结果表
    for 表名 in 描述符.tables:#按声明表
        记录=表对象.get(表名)#文件中的表
        if 记录 is None:#缺表
            表映射[表名]={}#空表
            continue#下一张
        if not isinstance(记录,dict):#表不是对象
            raise 存储错误('malformed-medium',f"unit '{描述符.name}': table '{表名}' is not an object")#损坏
        表映射[表名]=dict(记录)#复制记录
    return 单元状态(版本,文档.get('global') if 'global' in 文档 else None,表映射)#解析状态

def 序列化记录(版本,值):#单记录文档
    """序列化一条 per-record 文档。"""
    return json.dumps({'version':版本,'record':值},indent=2,ensure_ascii=False)+'\n'#美化加换行

def 解析记录(文本,版本):#解析单记录文档
    """解析 per-record 文档；外文档读作缺席。"""
    try:#JSON 解析
        文档=json.loads(文本)#解析
    except json.JSONDecodeError:#非法
        return None#外文档
    if not isinstance(文档,dict):#不是对象
        return None#外文档
    if 文档.get('version')!=版本:#版本戳不匹配
        return None#外文档
    return 文档.get('record')#记录值
