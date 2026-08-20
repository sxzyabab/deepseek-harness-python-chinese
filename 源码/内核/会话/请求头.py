"""针对完整 request/header 会话事件的请求头重建工具。对齐上游 `session/src/request-header.ts`。公开面仅中文名。"""
import json#JSON
from llm.调用配置 import 调用配置相等#导入调用配置相等比较

__all__=['归一请求头','请求头是否相等','折叠请求头']#仅中文公开名

def 取字段(对象,键):#读取字段
    """读取映射或对象上的字段。"""
    if isinstance(对象,dict):#映射
        return 对象[键]#映射键
    return getattr(对象,键)#对象属性

def 试取(对象,键):#读取可选字段
    """读取可选字段，缺席为 None。"""
    if 对象 is None:#无对象
        return None#缺席
    if isinstance(对象,dict):#映射
        return 对象.get(键)#映射键
    return getattr(对象,键,None)#对象属性

def 转json(值):#紧凑 JSON
    """按 JS JSON.stringify 的紧凑形态编码。"""
    return json.dumps(值,separators=(',',':'),ensure_ascii=False)#紧凑 JSON

def 归一请求头(头):#归一请求头
    """把请求头归一成规范形态：空系统提示词与空工具列表变成缺省字段。"""
    适配器默认=试取(头,'adapterDefaults')#适配器默认旗标
    结果={'config':取字段(头,'config')}#调用配置
    if isinstance(适配器默认,dict) and (试取(适配器默认,'reasoningEffort') is True or 试取(适配器默认,'maxTokens') is True):#有真旗标
        结果['adapterDefaults']=适配器默认#有真旗标才带 adapterDefaults
    系统=试取(头,'system')#系统提示
    if 系统 is not None and isinstance(系统,str) and len(系统)>0:#非空系统提示
        结果['system']=系统#非空系统提示才带
    工具们=试取(头,'tools')#工具列表
    if 工具们 is not None and len(工具们)>0:#非空工具列表
        结果['tools']=工具们#非空工具列表才带
    return 结果#规范头

def 同一模式(甲,乙):#模式是否相等
    """经同一路径组装的工具模式的规范 JSON 相等。"""
    return 转json(甲)==转json(乙)#按 JSON 比较

def 请求头是否相等(甲,乙):#请求头是否相等
    """规范请求头的逐字段相等。工具模式按顺序比较。"""
    甲默认=试取(甲,'adapterDefaults')#甲方默认
    乙默认=试取(乙,'adapterDefaults')#乙方默认
    if not isinstance(甲默认,dict):#甲方无表
        甲默认={}#缺省空表
    if not isinstance(乙默认,dict):#乙方无表
        乙默认={}#缺省空表
    if not 调用配置相等(取字段(甲,'config'),取字段(乙,'config')):#配置不同
        return False#配置不同
    if 试取(甲默认,'reasoningEffort')!=试取(乙默认,'reasoningEffort'):#推理力度旗标不同
        return False#推理力度旗标不同
    if 试取(甲默认,'maxTokens')!=试取(乙默认,'maxTokens'):#token 旗标不同
        return False#token 旗标不同
    if 试取(甲,'system')!=试取(乙,'system'):#系统提示不同
        return False#系统提示不同
    甲方工具=试取(甲,'tools')#甲方工具
    乙方工具=试取(乙,'tools')#乙方工具
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

def 折叠请求头(事件们,起始=None):#折叠请求头
    """把一份日志的请求头事件折成最后一次快照之后生效的纪元请求头。"""
    状态=起始#当前折叠状态
    for 事件 in 事件们:#扫描事件
        if 试取(事件,'type')=='request/header':#遇到请求头
            状态=归一请求头(取字段(取字段(事件,'data'),'header'))#遇到请求头则归一覆盖
    return 状态#最近规范头
