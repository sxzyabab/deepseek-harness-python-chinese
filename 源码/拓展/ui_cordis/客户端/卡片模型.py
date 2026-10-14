import json
from json import JSONDecodeError#JSON 解析失败

__all__=['首行','定义卡片','运行卡片','动作卡片','调用状态']#仅中文公开名

def 首行(文本):
    '折叠错误摘要用'
    换行=文本.find('\n')
    return 文本 if 换行==-1 else 文本[:换行]

def 串字段(源,键):
    '从 dict 读非空串，否则 None'
    if 源 is None or 键 not in 源:
        return None
    值=源[键]
    return 值 if isinstance(值,str) and len(值)>0 else None

def 对象字段(源,键):
    '从 dict 读对象字段'
    if 源 is None or 键 not in 源:
        return None
    值=源[键]
    return 值 if isinstance(值,dict) else None

def 解析参数(原文):
    '截断 JSON 当缺席'
    try:
        解析=json.loads(原文)
        return 解析 if isinstance(解析,dict) else None
    except (JSONDecodeError,TypeError,ValueError):
        return None

def 结果文本(块):
    '压平 content；否则错误名:码。块为工具调用 dict'
    if 'content' in 块 and 块['content'] is not None:
        内容=块['content']
    else:
        内容=[]
    段=[]
    for 项 in 内容:
        if isinstance(项,dict) and 'type' in 项 and 项['type']=='text':
            段.append(项['text'] if 'text' in 项 and 项['text'] is not None else '')
        elif isinstance(项,(dict,list)):
            段.append(json.dumps(项,ensure_ascii=False,separators=(',',':'),allow_nan=False,indent=2))
        else:
            段.append(str(项))
    文本='\n'.join(段)
    if len(文本)>0:
        return 文本
    错=块['error'] if 'error' in 块 else None
    if 错 is None:
        return None
    名=错['name'] if isinstance(错,dict) and 'name' in 错 else ''
    码=错['code'] if isinstance(错,dict) and 'code' in 错 else ''
    return 名+': '+码#名:码

def 调用状态(块):
    'running / ok / error / stopped。块为 dict'
    if 'kind' not in 块:
        return 'running'
    错=块['error'] if 'error' in 块 else None
    if isinstance(错,dict) and 'code' in 错 and 错['code']=='interrupted':
        return 'stopped'
    if 'isError' in 块 and 块['isError']:
        return 'error'
    return 'ok'

def 元对象(块):
    '未落定/出错/非对象则 None'
    if 'kind' not in 块:
        return None
    if 'isError' in 块 and 块['isError']:
        return None
    元=块['meta'] if 'meta' in 块 else None
    return 元 if isinstance(元,dict) else None

def 定义卡片(块):
    '从调用/结果块推导定义卡。块为 dict'
    已落定='kind' in 块
    if 已落定 and 'call' in 块 and 块['call'] is not None and 'argsRaw' in 块['call']:
        原文=块['call']['argsRaw']
        if 原文 is None:
            原文=''
    elif 'argsRaw' in 块 and 块['argsRaw'] is not None:
        原文=块['argsRaw']
    else:
        原文=''
    参=解析参数(原文)
    码=对象字段(参,'code') if 参 is not None else None
    态=调用状态(块)
    出=结果文本(块) if 已落定 else None
    元=元对象(块)
    原名=首行(原文) if len(原文)>0 else None
    参名=串字段(参,'name') if 参 is not None else None
    return {
        'pluginId':串字段(元,'pluginId') if 元 is not None else None,
        'packageId':串字段(元,'packageId') if 元 is not None else None,
        'name':参名 if 参名 is not None else 原名,
        'purpose':串字段(参,'purpose') if 参 is not None else None,
        'hostCode':串字段(码,'host') if 码 is not None else None,
        'clientCode':串字段(码,'client') if 码 is not None else None,
        'output':出,
        'errorSummary':首行(出) if 态=='error' and 出 is not None else None,
        'state':态,
    }

def 运行卡片(块):
    '推导运行卡。块为 dict'
    已落定='kind' in 块
    if 已落定 and 'call' in 块 and 块['call'] is not None and 'argsRaw' in 块['call']:
        原文=块['call']['argsRaw']
        if 原文 is None:
            原文=''
    elif 'argsRaw' in 块 and 块['argsRaw'] is not None:
        原文=块['argsRaw']
    else:
        原文=''
    参=解析参数(原文)
    元=元对象(块)
    态=调用状态(块)
    出=结果文本(块) if 已落定 else None
    原模式=串字段(参,'mode') if 参 is not None else None
    参插件=串字段(参,'pluginId') if 参 is not None else None
    参包=串字段(参,'packageId') if 参 is not None else None
    元插件=串字段(元,'pluginId') if 元 is not None else None
    元包=串字段(元,'packageId') if 元 is not None else None
    return {
        'pluginId':元插件 if 元插件 is not None else 参插件,
        'packageId':元包 if 元包 is not None else 参包,
        'pluginRunId':串字段(元,'pluginRunId') if 元 is not None else None,
        'mode':原模式 if 原模式 in ('run','update') else None,
        'seq':块['seq'] if 已落定 and 'seq' in 块 else None,
        'output':出,
        'errorSummary':首行(出) if 态=='error' and 出 is not None else None,
        'state':态,
    }

def 动作卡片(块):
    '推导停止或移除卡。块为 dict'
    已落定='kind' in 块
    if 已落定 and 'call' in 块 and 块['call'] is not None and 'argsRaw' in 块['call']:
        原文=块['call']['argsRaw']
        if 原文 is None:
            原文=''
    elif 'argsRaw' in 块 and 块['argsRaw'] is not None:
        原文=块['argsRaw']
    else:
        原文=''
    参=解析参数(原文)
    态=调用状态(块)
    出=结果文本(块) if 已落定 else None
    插件=None
    if 参 is not None:
        插件=串字段(参,'pluginId')#优先 pluginId
        if 插件 is None:
            插件=串字段(参,'id')
    return {
        'pluginId':插件,
        'output':出,
        'errorSummary':首行(出) if 态=='error' and 出 is not None else None,
        'state':态,
    }
