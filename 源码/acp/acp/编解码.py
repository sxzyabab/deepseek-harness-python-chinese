"""智能体框架生命周期与仅自动化 ACP 线路之间的纯翻译。

对齐上游 `acp/acp/src/codec.ts`。公开面仅中文名。
"""
import json#资源链接引用里的 JSON 片段

__all__=['回合结束到停止原因','ACP提示转文本','提示含不受支持内容']#仅中文公开名

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段，缺席为缺省。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 回合结束到停止原因(原因):#把回合结束映射为 ACP 停止原因
    """把框架回合结束映射到 ACP 的终态原因词表。"""
    种类=取字段(原因,'kind')#按结束种类分支
    if 种类=='completed':#正常完成
        return 'end_turn'#映射为结束回合
    if 种类=='max-tokens':#达到最大令牌
        return 'max_tokens'#映射为令牌上限
    # cancelled 留给显式客户端取消与拆除；钩子或其他所有者中止的回合是普通静默，报告 end_turn。
    if 种类=='aborted':#被中止
        return 'end_turn'#中止视为结束回合
    if 种类=='interrupted':#被打断
        return 'cancelled'#打断映射为已取消
    if 种类=='blocked' or 种类=='error':#阻塞与出错
        return 'end_turn'#视为结束回合
    return 'end_turn'#不可达默认仍报告结束回合

def ACP提示转文本(提示):#把 ACP 提示块展平为文本
    """文本块按原文拼接；资源链接变成显式文本引用。"""
    片段们=[]#按块收集
    for 块 in 提示:#逐块
        类型=取字段(块,'type')#块类型
        if 类型=='text':#文本块
            片段们.append(取字段(块,'text') or '')#原样取出文本
        elif 类型=='resource_link':#资源链接块
            名=json.dumps(取字段(块,'name'),ensure_ascii=False)#名称 JSON
            址=json.dumps(取字段(块,'uri'),ensure_ascii=False)#URI JSON
            片段们.append('\n[resource_link name='+名+' uri='+址+']\n')#方括号引用
    return ''.join(片段们)#按顺序拼接

def 提示含不受支持内容(提示):#检查是否含不受支持的提示块
    """任一块既非 text 也非 resource_link 时为真。"""
    for 块 in 提示:#逐块
        类型=取字段(块,'type')#块类型
        if 类型!='text' and 类型!='resource_link':#非基线块
            return True#不受支持
    return False#全部基线
