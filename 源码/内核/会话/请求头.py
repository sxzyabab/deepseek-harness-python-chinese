import json
from ...模型后端.llm.调用配置 import 调用配置相等

__all__=['归一请求头','请求头是否相等','折叠请求头']

def 转json(值):
    """按 JS JSON.stringify 的紧凑形态编码。"""
    return json.dumps(值,ensure_ascii=False,separators=(',',':'),allow_nan=False)

def 归一请求头(头):
    """把请求头归一成规范形态：空工具列表变成缺省字段，与请求构建方式一致。"""
    适配器默认=头['adapterDefaults'] if 'adapterDefaults' in 头 else None
    结果={'config':头['config']}
    if isinstance(适配器默认,dict) and (('reasoningEffort' in 适配器默认 and 适配器默认['reasoningEffort'] is True) or ('maxTokens' in 适配器默认 and 适配器默认['maxTokens'] is True)):
        结果['adapterDefaults']=适配器默认
    工具列表=头['tools'] if 'tools' in 头 else None
    if 工具列表 is not None and len(工具列表)>0:
        结果['tools']=工具列表
    return 结果

def 同一模式(甲,乙):
    """经同一路径组装的工具模式的规范 JSON 相等。"""
    return 转json(甲)==转json(乙)

def 请求头是否相等(甲,乙):
    """规范请求头的逐字段相等。工具模式按顺序比较。"""
    甲默认=甲['adapterDefaults'] if 'adapterDefaults' in 甲 else None
    乙默认=乙['adapterDefaults'] if 'adapterDefaults' in 乙 else None
    if not isinstance(甲默认,dict):
        甲默认={}
    if not isinstance(乙默认,dict):
        乙默认={}
    if not 调用配置相等(甲['config'],乙['config']):
        return False
    甲力度=甲默认['reasoningEffort'] if 'reasoningEffort' in 甲默认 else None
    乙力度=乙默认['reasoningEffort'] if 'reasoningEffort' in 乙默认 else None
    if 甲力度!=乙力度:
        return False
    甲上限=甲默认['maxTokens'] if 'maxTokens' in 甲默认 else None
    乙上限=乙默认['maxTokens'] if 'maxTokens' in 乙默认 else None
    if 甲上限!=乙上限:
        return False
    甲方工具=甲['tools'] if 'tools' in 甲 else None
    乙方工具=乙['tools'] if 'tools' in 乙 else None
    if 甲方工具 is None:
        甲方工具=[]
    if 乙方工具 is None:
        乙方工具=[]
    if len(甲方工具)!=len(乙方工具):
        return False
    下标=0
    while 下标<len(甲方工具):
        if not 同一模式(甲方工具[下标],乙方工具[下标]):
            return False
        下标+=1
    return True

def 折叠请求头(事件列表,起始=None):
    """把一份日志的请求头事件折成最后一次快照之后生效的纪元请求头。"""
    状态=起始
    for 事件 in 事件列表:
        if ('type' in 事件 and 事件['type']=='request/header'):
            数据=事件['data']
            状态=归一请求头(数据['header'])
    return 状态
