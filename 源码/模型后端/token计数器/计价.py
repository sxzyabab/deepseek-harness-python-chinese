"""计量服务与纯上下文分解投影共用的固定密度启发式令牌计价。公开面仅中文名。"""
from math import ceil as 上取整#上取整
from json import dumps as 编码#紧凑json

__all__=['每令牌字符数','块开销','角色开销','计价结构块','计价内容','计价系统消息','计价消息','计价工具令牌']#仅中文公开名

每令牌字符数=4#每令牌字符数
块开销=4#块结构开销
角色开销=4#角色开销

def 计价结构块(块):
    """一块在有类型计价臂之外的结构 JSON 价格。图像引用剥掉 offloaded。块为 dict。"""
    计价块=块
    if ('type' in 块) and 块['type']=='image':
        计价块={键:值 for 键,值 in 块.items() if 键!='offloaded'}
    return 块开销+上取整(len(编码(计价块,ensure_ascii=False,separators=(',',':'),allow_nan=False))/每令牌字符数)

def 计价内容(块列表):
    """在固定密度启发式下递归计价内容块。块为 dict。"""
    令牌数=0
    for 块 in 块列表:
        种类=块['type']
        if 种类=='text' or 种类=='reasoning':
            令牌数+=上取整(len(块['text'])/每令牌字符数)+块开销
        elif 种类=='tool-call':
            令牌数+=上取整(len(块['name'])/每令牌字符数)
            令牌数+=上取整(len(块['arguments'])/每令牌字符数)
            令牌数+=块开销
        else:
            令牌数+=计价结构块(块)
    return 令牌数

def 计价系统消息(消息):
    """计价已渲染系统提示词：system/message 表面节点的文本。消息为 dict。"""
    内容=消息['content']#内容块
    if len(内容)==0:#空内容
        return 0#无系统提示词
    字符数=0#累计字符
    for 块 in 内容:#逐块
        if 块['type']=='text':#文本
            字符数+=len(块['text'])#文本长度
        else:#其余按JSON
            字符数+=len(编码(块,ensure_ascii=False,separators=(',',':'),allow_nan=False))#JSON长度
    return 上取整(字符数/每令牌字符数)+角色开销#密度加角色开销

def 计价消息(消息):
    """启发式计价一条模型可见消息。消息为 dict。"""
    if 消息.get('role')=='system':#系统角色
        return 计价系统消息(消息)#专用路径
    return 计价内容(消息['content'])+角色开销#内容加角色开销

def 计价工具令牌(头):
    """计价规范请求信封的工具模式部分。头为 dict。"""
    if 头 is None or 'tools' not in 头:#没有工具键
        return 0#缺席为0
    工具=头['tools']#工具列表
    if 工具 is None or len(工具)==0:#没有工具
        return 0#缺席或空则为0
    return 上取整(len(编码(工具,ensure_ascii=False,separators=(',',':'),allow_nan=False))/每令牌字符数)+块开销#JSON密度加结构开销
