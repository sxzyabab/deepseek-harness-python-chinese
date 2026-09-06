"""Cordis 生命周期工具调用的可回放稳定视图模型。

对齐上游 `ui-cordis/src/client/card-model.ts`。公开面仅中文名。
纯数据推导，无 DOM / React。
"""
import json#解析参数
from json import JSONDecodeError#JSON 解析失败

__all__=['首行','定义卡片','运行卡片','动作卡片','调用状态']#仅中文公开名

def 首行(文本):
    """折叠错误摘要用。"""
    换行=文本.find('\n')#找换行
    return 文本 if 换行==-1 else 文本[:换行]#切

def 串字段(源,键):
    """从 dict 读非空串，否则 None。"""
    if 源 is None or 键 not in 源:#缺席
        return None#缺席
    值=源[键]#值
    return 值 if isinstance(值,str) and len(值)>0 else None#空当缺席

def 对象字段(源,键):
    """从 dict 读对象字段。"""
    if 源 is None or 键 not in 源:#缺席
        return None#缺席
    值=源[键]#值
    return 值 if isinstance(值,dict) else None#非对象缺席

def 解析参数(原文):
    """截断 JSON 当缺席。"""
    try:#可能截断
        解析=json.loads(原文)#解析
        return 解析 if isinstance(解析,dict) else None#须对象
    except (JSONDecodeError,TypeError,ValueError):#截断前缀或非 JSON
        return None#缺席

def 结果文本(块):
    """压平 content；否则错误名:码。块为工具调用 dict。"""
    if 'content' in 块 and 块['content'] is not None:#有内容表
        内容=块['content']#块表
    else:#缺席当空
        内容=[]#空
    段=[]#段
    for 项 in 内容:#逐项
        if isinstance(项,dict) and 'type' in 项 and 项['type']=='text':#文本
            段.append(项['text'] if 'text' in 项 and 项['text'] is not None else '')#正文
        elif isinstance(项,(dict,list)):#其它结构
            段.append(json.dumps(项,ensure_ascii=False,separators=(',',':'),allow_nan=False,indent=2))#JSON
        else:#原语
            段.append(str(项))#字符串化
    文本='\n'.join(段)#拼
    if len(文本)>0:#有
        return 文本#正文
    错=块['error'] if 'error' in 块 else None#错
    if 错 is None:#无错
        return None#缺席
    名=错['name'] if isinstance(错,dict) and 'name' in 错 else ''#名
    码=错['code'] if isinstance(错,dict) and 'code' in 错 else ''#码
    return 名+': '+码#名:码

def 调用状态(块):
    """running / ok / error / stopped。块为 dict。"""
    if 'kind' not in 块:#无 kind 则未落定
        return 'running'#进行中
    错=块['error'] if 'error' in 块 else None#错
    if isinstance(错,dict) and 'code' in 错 and 错['code']=='interrupted':#中断
        return 'stopped'#已停
    if 'isError' in 块 and 块['isError']:#出错
        return 'error'#出错
    return 'ok'#成功

def 元对象(块):
    """未落定/出错/非对象则 None。"""
    if 'kind' not in 块:#未落定
        return None#无
    if 'isError' in 块 and 块['isError']:#出错
        return None#无
    元=块['meta'] if 'meta' in 块 else None#meta
    return 元 if isinstance(元,dict) else None#对象

def 定义卡片(块):
    """从调用/结果块推导定义卡。块为 dict。"""
    已落定='kind' in 块#落定
    if 已落定 and 'call' in 块 and 块['call'] is not None and 'argsRaw' in 块['call']:#落定后从 call 取
        原文=块['call']['argsRaw']#call
        if 原文 is None:#显式空
            原文=''#空串
    elif 'argsRaw' in 块 and 块['argsRaw'] is not None:#进行中
        原文=块['argsRaw']#原文
    else:#缺席
        原文=''#空
    参=解析参数(原文)#解析
    码=对象字段(参,'code') if 参 is not None else None#code
    态=调用状态(块)#状态
    出=结果文本(块) if 已落定 else None#结果
    元=元对象(块)#meta
    原名=首行(原文) if len(原文)>0 else None#回退名
    参名=串字段(参,'name') if 参 is not None else None#参名
    return {#卡
        'pluginId':串字段(元,'pluginId') if 元 is not None else None,#插件
        'packageId':串字段(元,'packageId') if 元 is not None else None,#包
        'name':参名 if 参名 is not None else 原名,#名
        'purpose':串字段(参,'purpose') if 参 is not None else None,#用途
        'hostCode':串字段(码,'host') if 码 is not None else None,#宿主码
        'clientCode':串字段(码,'client') if 码 is not None else None,#客户端码
        'output':出,#结果
        'errorSummary':首行(出) if 态=='error' and 出 is not None else None,#错摘要
        'state':态,#状态
    }#结束

def 运行卡片(块):
    """推导运行卡。块为 dict。"""
    已落定='kind' in 块#落定
    if 已落定 and 'call' in 块 and 块['call'] is not None and 'argsRaw' in 块['call']:#落定后从 call 取
        原文=块['call']['argsRaw']#call
        if 原文 is None:#显式空
            原文=''#空串
    elif 'argsRaw' in 块 and 块['argsRaw'] is not None:#进行中
        原文=块['argsRaw']#原文
    else:#缺席
        原文=''#空
    参=解析参数(原文)#解析
    元=元对象(块)#meta
    态=调用状态(块)#状态
    出=结果文本(块) if 已落定 else None#结果
    原模式=串字段(参,'mode') if 参 is not None else None#模式
    参插件=串字段(参,'pluginId') if 参 is not None else None#参插件
    参包=串字段(参,'packageId') if 参 is not None else None#参包
    元插件=串字段(元,'pluginId') if 元 is not None else None#元插件
    元包=串字段(元,'packageId') if 元 is not None else None#元包
    return {#卡
        'pluginId':元插件 if 元插件 is not None else 参插件,#插件
        'packageId':元包 if 元包 is not None else 参包,#包
        'pluginRunId':串字段(元,'pluginRunId') if 元 is not None else None,#运行
        'mode':原模式 if 原模式 in ('run','update') else None,#合法模式
        'seq':块['seq'] if 已落定 and 'seq' in 块 else None,#序号
        'output':出,#结果
        'errorSummary':首行(出) if 态=='error' and 出 is not None else None,#错
        'state':态,#状态
    }#结束

def 动作卡片(块):
    """推导停止或移除卡。块为 dict。"""
    已落定='kind' in 块#落定
    if 已落定 and 'call' in 块 and 块['call'] is not None and 'argsRaw' in 块['call']:#落定后从 call 取
        原文=块['call']['argsRaw']#call
        if 原文 is None:#显式空
            原文=''#空串
    elif 'argsRaw' in 块 and 块['argsRaw'] is not None:#进行中
        原文=块['argsRaw']#原文
    else:#缺席
        原文=''#空
    参=解析参数(原文)#解析
    态=调用状态(块)#状态
    出=结果文本(块) if 已落定 else None#结果
    插件=None#插件 id
    if 参 is not None:#有参数
        插件=串字段(参,'pluginId')#优先 pluginId
        if 插件 is None:#回落 id
            插件=串字段(参,'id')#id
    return {#卡
        'pluginId':插件,#插件
        'output':出,#结果
        'errorSummary':首行(出) if 态=='error' and 出 is not None else None,#错
        'state':态,#状态
    }#结束
