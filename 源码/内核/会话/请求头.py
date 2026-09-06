"""针对完整 request/header 会话事件的请求头重建工具。对齐上游 `session/src/request-header.ts`。公开面仅中文名。"""
import json#JSON
from ...模型后端.llm.调用配置 import 调用配置相等#导入调用配置相等比较

__all__=['归一请求头','请求头是否相等','折叠请求头']#仅中文公开名

def 转json(值):
    """按 JS JSON.stringify 的紧凑形态编码。"""
    return json.dumps(值,ensure_ascii=False,separators=(',',':'),allow_nan=False)#紧凑 JSON

def 归一请求头(头):
    """把请求头归一成规范形态：空系统提示词与空工具列表变成缺省字段。"""
    适配器默认=头['adapterDefaults'] if 'adapterDefaults' in 头 else None#适配器默认旗标
    结果={'config':头['config']}#调用配置
    if isinstance(适配器默认,dict) and (('reasoningEffort' in 适配器默认 and 适配器默认['reasoningEffort'] is True) or ('maxTokens' in 适配器默认 and 适配器默认['maxTokens'] is True)):#有真旗标
        结果['adapterDefaults']=适配器默认#有真旗标才带 adapterDefaults
    系统=头['system'] if 'system' in 头 else None#系统提示
    if 系统 is not None and isinstance(系统,str) and len(系统)>0:#非空系统提示
        结果['system']=系统#非空系统提示才带
    工具列表=头['tools'] if 'tools' in 头 else None#工具列表
    if 工具列表 is not None and len(工具列表)>0:#非空工具列表
        结果['tools']=工具列表#非空工具列表才带
    return 结果#规范头

def 同一模式(甲,乙):
    """经同一路径组装的工具模式的规范 JSON 相等。"""
    return 转json(甲)==转json(乙)#按 JSON 比较

def 请求头是否相等(甲,乙):
    """规范请求头的逐字段相等。工具模式按顺序比较。"""
    甲默认=甲['adapterDefaults'] if 'adapterDefaults' in 甲 else None#甲方默认
    乙默认=乙['adapterDefaults'] if 'adapterDefaults' in 乙 else None#乙方默认
    if not isinstance(甲默认,dict):#甲方无表
        甲默认={}#缺省空表
    if not isinstance(乙默认,dict):#乙方无表
        乙默认={}#缺省空表
    if not 调用配置相等(甲['config'],乙['config']):#配置不同
        return False#配置不同
    甲力度=甲默认['reasoningEffort'] if 'reasoningEffort' in 甲默认 else None#甲方力度
    乙力度=乙默认['reasoningEffort'] if 'reasoningEffort' in 乙默认 else None#乙方力度
    if 甲力度!=乙力度:#推理力度旗标不同
        return False#推理力度旗标不同
    甲上限=甲默认['maxTokens'] if 'maxTokens' in 甲默认 else None#甲方 token
    乙上限=乙默认['maxTokens'] if 'maxTokens' in 乙默认 else None#乙方 token
    if 甲上限!=乙上限:#token 旗标不同
        return False#token 旗标不同
    甲系统=甲['system'] if 'system' in 甲 else None#甲方系统提示
    乙系统=乙['system'] if 'system' in 乙 else None#乙方系统提示
    if 甲系统!=乙系统:#系统提示不同
        return False#系统提示不同
    甲方工具=甲['tools'] if 'tools' in 甲 else None#甲方工具
    乙方工具=乙['tools'] if 'tools' in 乙 else None#乙方工具
    if 甲方工具 is None:#缺省
        甲方工具=[]#缺省空表
    if 乙方工具 is None:#缺省
        乙方工具=[]#缺省空表
    if len(甲方工具)!=len(乙方工具):#长度不同
        return False#长度不同
    下标=0#逐项
    while 下标<len(甲方工具):#逐项比较
        if not 同一模式(甲方工具[下标],乙方工具[下标]):#模式不同
            return False#模式不同
        下标+=1#下一项
    return True#长度与逐项模式都同

def 折叠请求头(事件列表,起始=None):
    """把一份日志的请求头事件折成最后一次快照之后生效的纪元请求头。"""
    状态=起始#当前折叠状态
    for 事件 in 事件列表:#扫描事件
        if ('type' in 事件 and 事件['type']=='request/header'):#遇到请求头
            数据=事件['data']#载荷
            状态=归一请求头(数据['header'])#遇到请求头则归一覆盖
    return 状态#最近规范头
