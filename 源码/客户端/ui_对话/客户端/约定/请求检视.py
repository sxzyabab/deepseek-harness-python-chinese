"""请求提示检视：对照系统节点规范化 request/header。

对齐上游 `ui-conversation/src/client/contract/request-inspection.ts`。公开面仅中文名。
先前与系统节点为 dict 或 None；事件为 dict。
"""
import json#工具目录比对

__all__=['检视请求提示']#仅中文公开名

def 检视请求提示(先前,事件,系统):
    """对照生效中的系统节点规范化一条请求头，并分类模型可见提示变更。

    历史内更新已在自身位置呈现文本，故头对该更新不报告系统变更。
    先前为前一条已加载请求头的提示（dict 或 None）；
    事件为 request/header 会话事件；
    系统为有效系统提示节点（dict 或 None）。
    """
    头=事件['data']['header']#请求头
    原始工具=头['tools'] if 'tools' in 头 else None#原始工具
    工具表=原始工具 if isinstance(原始工具,list) else []#工具数组或空
    系统文本=系统['text'] if 系统 is not None and 'text' in 系统 else ''#来自表面节点
    提示={'config':头['config'],'system':系统文本,'tools':工具表}#规范提示
    原因=事件['data']['reason'] if 'reason' in 事件['data'] else None#原因
    if 先前 is None and 原因!='initial':#无先前且非初始
        return {'prompt':提示}#只返回提示
    系统变=先前 is not None and 先前['system']!=提示['system'] and (系统 is None or 系统.get('update') is not True)#系统是否变
    工具变=先前 is not None and json.dumps(先前['tools'],ensure_ascii=False,separators=(',',':'))!=json.dumps(提示['tools'],ensure_ascii=False,separators=(',',':'))#工具是否变
    if 先前 is not None and (not 系统变) and (not 工具变):#无变更
        return {'prompt':提示}#只返回提示
    出处=系统 if 系统 is not None and (先前 is None or 系统变) else 事件#变更出处
    if 先前 is None:#初始
        种='initial'#初始
    elif 系统变 and 工具变:#两者
        种='system-and-tools'#两者
    elif 系统变:#仅系统
        种='system'#系统
    else:#仅工具
        种='tools'#工具
    变更={'seq':出处['seq'],'time':出处['time'],'kind':种}#变更
    if 先前 is not None:#有先前
        变更['previous']=先前#带上
    return {'prompt':提示,'change':变更}#带变更
