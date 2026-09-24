import json
from ...启动.app启动.配置数据架构.投影器 import 创建配置投影器,装载器表达式数据架构
from ...启动.app启动.配置数据架构.原生 import 是否原生配置数据架构
from .呈现 import 巡检错误

__all__=['查询现场配置']

默认页大小=25
最大页大小=100

def 是否整数(值):
    """排除布尔的整数判定。"""
    if isinstance(值,bool):
        return False
    if isinstance(值,int):
        return True
    return isinstance(值,float) and 值.is_integer()

def 现场配置(条目):
    """从一条加载器插件配置投影目录行。"""
    列出={'id':条目.编号,'patchId':条目.选项['id'],'name':条目.选项['name']}
    if 条目.子组 is not None or 条目.子树 is not None:
        列出['status']='tree'
        return 列出
    纤程=条目.纤程
    if 纤程 is None or 纤程.编号 is None or 条目.已禁用:
        列出['status']='inactive'
        return 列出
    运行时=纤程.运行时
    配置模式=None if 运行时 is None else 运行时.配置模式
    if 配置模式 is None:
        列出['status']='absent'
        return 列出
    if not 是否原生配置数据架构(配置模式):
        列出['status']='unsupported'
        return 列出
    列出['status']='schema'
    列出['native']=配置模式
    return 列出

def 目录行(现场):
    """去掉原生图，只留目录字段。"""
    return {'id':现场['id'],'patchId':现场['patchId'],'name':现场['name'],'status':现场['status']}

def 解析查询(输入):
    """读取模型给出的查询字段。"""
    字段=输入 if isinstance(输入,dict) else {}
    def 文本(键):
        """非空字符串或省略。"""
        if 键 not in 字段:
            return None
        值=字段[键]
        if not isinstance(值,str) or 值=='':
            raise 巡检错误(键+' 必须是非空字符串')
        return 值
    偏移=字段['offset'] if 'offset' in 字段 else 0
    限额=字段['limit'] if 'limit' in 字段 else 默认页大小
    if not 是否整数(偏移) or 偏移<0:
        raise 巡检错误('offset 必须是非负整数')
    偏移=int(偏移)
    if not 是否整数(限额) or 限额<1 or 限额>最大页大小:
        raise 巡检错误('limit 必须是 1 到 '+str(最大页大小)+' 的整数')
    限额=int(限额)
    return {'entry':文本('entry'),'name':文本('name'),'offset':偏移,'limit':限额}

def 包目录(上下文,条目):
    """经配置档包查找解析插件名对应的包目录。"""
    基准网址=条目.父组.所属树.所属上下文.基准网址
    目录=None
    if 基准网址 is not None:
        插件包=上下文.获取服务('pluginPackages',False)
        if 插件包 is not None:
            包=插件包.包属于(条目.选项['name'],基准网址)
            if 包 is not None:
                目录=包['dir']
    if 目录 is None:
        return {}
    return {'packageDir':目录}

def 转json(值):
    """投影输出按 JSON 构造。"""
    return json.loads(json.dumps(值,ensure_ascii=False,separators=(',',':'),allow_nan=False))

def 查询现场配置(上下文,输入=None):
    """回答 Config.listConfigs：一页目录，或一条目的投影模式。"""
    加载器=上下文.获取服务('加载器',False)
    if 加载器 is None:
        raise 巡检错误('Config 巡检需要挂载本配置档的加载器；本宿主组合没有加载器')
    查询=解析查询(输入)
    条目表=[现场配置(项) for 项 in 加载器.列出插件配置()]
    if 查询['entry'] is None:
        匹配=条目表 if 查询['name'] is None else [候选 for 候选 in 条目表 if 候选['name']==查询['name']]
        页=[目录行(项) for 项 in 匹配[查询['offset']:查询['offset']+查询['limit']]]
        结束=查询['offset']+len(页)
        return {'entries':页,'total':len(匹配),'nextOffset':结束 if 结束<len(匹配) else None}
    条目=None
    for 候选 in 条目表:
        if 候选['id']==查询['entry']:
            条目=候选
            break
    if 条目 is None:
        raise 巡检错误('未知条目 id '+json.dumps(查询['entry'],ensure_ascii=False,separators=(',',':'),allow_nan=False))
    列出行=dict(目录行(条目))
    列出行.update(包目录(上下文,加载器.解析(查询['entry'])))
    if 'native' not in 条目:
        return 列出行
    投影=创建配置投影器()
    结果=投影(条目['native'],'config')
    模式=结果['schema']
    定义=dict(结果['definitions'])
    定义['loaderExpression']=装载器表达式数据架构
    文档={'$schema':'https://json-schema.org/draft/2020-12/schema','$defs':定义}
    文档.update(模式)
    列出行['acceptsMissing']=结果['acceptsMissing']
    列出行['limitations']=结果['limitations']
    列出行['schema']=文档
    return 转json(列出行)
