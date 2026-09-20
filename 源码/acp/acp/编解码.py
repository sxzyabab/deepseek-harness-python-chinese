"""智能体框架生命周期与仅自动化 ACP 线路之间的纯翻译。"""
import json#资源链接引用里的 JSON 片段

__all__=['回合结束到停止原因','ACP提示转文本','提示含不受支持内容']#仅中文公开名

def 回合结束到停止原因(原因):
    """把框架回合结束映射到 ACP 的终态原因词表。原因为 dict。"""
    种类=原因['kind'] if isinstance(原因,dict) and 'kind' in 原因 else None#按结束种类分支
    if 种类=='completed':#正常完成
        return 'end_turn'#映射为结束回合
    if 种类=='max-tokens':#达到最大令牌
        return 'max_tokens'#映射为令牌上限
    if 种类=='aborted':#被中止
        return 'end_turn'#中止视为结束回合
    if 种类=='interrupted':#被打断
        return 'cancelled'#打断映射为已取消
    if 种类=='blocked' or 种类=='error':#阻塞与出错
        return 'end_turn'#视为结束回合
    return 'end_turn'#不可达默认仍报告结束回合

def ACP提示转文本(提示):
    """文本块按原文拼接；资源链接变成显式文本引用。提示块为 dict。"""
    片段列表=[]#按块收集
    for 块 in 提示:#逐块
        类型=块['type'] if isinstance(块,dict) and 'type' in 块 else None#块类型
        if 类型=='text':#文本块
            文本=块['text'] if 'text' in 块 else None#原文
            片段列表.append(文本 if isinstance(文本,str) else '')#原样取出文本
        elif 类型=='resource_link':#资源链接块
            名=json.dumps(块['name'] if 'name' in 块 else None,ensure_ascii=False,separators=(',',':'),allow_nan=False)#名称 JSON
            址=json.dumps(块['uri'] if 'uri' in 块 else None,ensure_ascii=False,separators=(',',':'),allow_nan=False)#URI JSON
            片段列表.append('\n[resource_link name='+名+' uri='+址+']\n')#方括号引用
    return ''.join(片段列表)#按顺序拼接

def 提示含不受支持内容(提示):
    """任一块既非 text 也非 resource_link 时为真。提示块为 dict。"""
    for 块 in 提示:#逐块
        类型=块['type'] if isinstance(块,dict) and 'type' in 块 else None#块类型
        if 类型!='text' and 类型!='resource_link':#非基线块
            return True#不受支持
    return False#全部基线
