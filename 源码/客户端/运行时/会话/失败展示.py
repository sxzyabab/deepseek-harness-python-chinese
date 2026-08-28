"""把持久化失败转成 GUI 里可以安全展示的文案。

对齐上游 `runtime/src/client/sessions/failure-display.ts`。公开面仅中文名。
"""
import json#整份 JSON 回退

__all__=['展示失败文案']#仅中文公开名

def 取字段(对象,键,缺省=None):#读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

def 展示失败文案(失败):#失败值 → 展示文案
    """把持久化失败转成 GUI 里可以安全展示的文案。

    @param 失败 - 会话事件保全的失败值。
    @returns 给客户端投影用的展示安全文案。
    """
    if 失败 is None:#空
        return str(失败)#字符串化
    if isinstance(失败,(str,bytes,int,float,bool)):#标量
        return str(失败)#直接字符串化
    if isinstance(失败,dict):#记录
        码=失败.get('code')#错误码
        消息=失败.get('message')#消息
    elif hasattr(失败,'__dict__') or hasattr(失败,'code') or hasattr(失败,'message'):#一般对象
        码=取字段(失败,'code')#错误码
        消息=取字段(失败,'message')#消息
    else:#其它
        return str(失败)#直接字符串化
    # 提供方 AUTH 消息可能回显脱敏或仍部分保留的凭证。
    # 原始诊断留在会话日志里，但绝不投影进 UI 状态。
    if 码=='AUTH':#鉴权失败
        return 'API key is invalid'#固定文案
    if isinstance(消息,str):#有 message
        return 消息#用它
    return json.dumps(失败,ensure_ascii=False,default=str)#否则整份 JSON
