"""计量服务与纯上下文分解投影共用的固定密度启发式令牌计价。对齐上游 `token-meter/src/estimate.ts`。公开面仅中文名。"""
from math import ceil as 上取整#上取整
from json import dumps as 编码#紧凑json
from .类型 import 取,试取#读取字段

__all__=['每令牌字符数','块开销','角色开销','计价内容','计价消息','计价系统令牌','计价工具令牌','计价请求头']#仅中文公开名

每令牌字符数=4#每令牌字符数
块开销=4#块结构开销
角色开销=4#角色开销

def 计价内容(块列表):
    """在固定密度启发式下递归计价内容块。"""
    令牌数=0#累计令牌
    for 块 in 块列表:#逐块
        种类=取(块,'type')#按块类型
        if 种类=='text' or 种类=='reasoning':#文本或推理
            令牌数+=上取整(len(取(块,'text'))/每令牌字符数)+块开销#文本密度加结构开销
        elif 种类=='tool-call':#工具调用
            令牌数+=上取整(len(取(块,'name'))/每令牌字符数)#工具名
            令牌数+=上取整(len(取(块,'arguments'))/每令牌字符数)#参数JSON
            令牌数+=块开销#结构开销
        elif 种类=='tool-result':#工具结果
            令牌数+=计价内容(取(块,'content'))+块开销#递归内容加结构开销
        else:#未知块
            令牌数+=块开销+上取整(len(编码(块,ensure_ascii=False,separators=(',',':')))/每令牌字符数)#JSON长度加结构开销
    return 令牌数#合计

def 计价消息(消息):
    """启发式计价一条模型可见消息。"""
    return 计价内容(取(消息,'content'))+角色开销#内容加角色开销

def 计价系统令牌(头):
    """计价规范请求信封的系统提示词部分。"""
    系统=None if 头 is None else 试取(头,'system')#系统提示词
    if 系统 is None:#没有系统提示词
        return 0#缺席为0
    return 上取整(len(系统)/每令牌字符数)+角色开销#密度加角色开销

def 计价工具令牌(头):
    """计价规范请求信封的工具模式部分。"""
    工具=None if 头 is None else 试取(头,'tools')#工具列表
    if 工具 is None or len(工具)==0:#没有工具
        return 0#缺席或空则为0
    return 上取整(len(编码(工具,ensure_ascii=False,separators=(',',':')))/每令牌字符数)+块开销#JSON密度加结构开销

def 计价请求头(头):
    """计价完整的非表面请求信封。"""
    return 计价系统令牌(头)+计价工具令牌(头)#系统加工具
