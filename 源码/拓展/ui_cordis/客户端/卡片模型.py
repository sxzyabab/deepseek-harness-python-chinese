"""Cordis 生命周期工具调用的可回放稳定视图模型。

对齐上游 `ui-cordis/src/client/card-model.ts`。公开面仅中文名。
纯数据推导，无 DOM / React。
"""
import json#解析参数

__all__=['首行','定义卡片','运行卡片','动作卡片','调用状态']#仅中文公开名

def 取字段(对象,键,缺省=None):#读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

def 首行(文本):#取第一物理行
    """折叠错误摘要用。"""
    换行=文本.find('\n')#找换行
    return 文本 if 换行==-1 else 文本[:换行]#切

def 串字段(源,键):#非空字符串
    """读非空串，否则 None。"""
    值=源.get(键) if isinstance(源,dict) else None#值
    return 值 if isinstance(值,str) and 值!='' else None#空当缺席

def 对象字段(源,键):#对象字段
    """读对象字段。"""
    值=源.get(键) if isinstance(源,dict) else None#值
    return 值 if isinstance(值,dict) and 值 is not None else None#非对象缺席

def 解析参数(原文):#解析 JSON
    """截断 JSON 当缺席。"""
    try:#可能截断
        解析=json.loads(原文)#解析
        return 解析 if isinstance(解析,dict) and 解析 is not None else None#须对象
    except Exception:#截断前缀
        return None#缺席

def 结果文本(块):#结果正文
    """压平 content；否则错误名:码。"""
    内容=取字段(块,'content') or []#块表
    段=[]#段
    for 项 in 内容:#逐项
        if 取字段(项,'type')=='text':#文本
            段.append(取字段(项,'text') or '')#正文
        else:#其它
            段.append(json.dumps(项,ensure_ascii=False,indent=2) if isinstance(项,(dict,list)) else str(项))#JSON
    文本='\n'.join(段)#拼
    if 文本!='':#有
        return 文本#正文
    错=取字段(块,'error')#错
    if 错 is None:#无错
        return None#缺席
    return f"{取字段(错,'name')}: {取字段(错,'code')}"#名:码

def 调用状态(块):#推导状态
    """running / ok / error / stopped。"""
    if isinstance(块,dict):#映射
        if 'kind' not in 块:#无 kind
            return 'running'#进行中
    elif not hasattr(块,'kind'):#对象无
        return 'running'#进行中
    错=取字段(块,'error')#错
    if 取字段(错,'code')=='interrupted':#中断
        return 'stopped'#已停
    return 'error' if 取字段(块,'isError') else 'ok'#出错或成功

def 元对象(块):#成功 meta
    """未落定/出错/非对象则 None。"""
    if isinstance(块,dict) and 'kind' not in 块:#未落定
        return None#无
    if 取字段(块,'isError'):#出错
        return None#无
    元=取字段(块,'meta')#meta
    return 元 if isinstance(元,dict) and 元 is not None else None#对象

def 定义卡片(块):#cordis_define
    """从调用/结果块推导定义卡。"""
    已落定=isinstance(块,dict) and 'kind' in 块#落定
    if 已落定:#落定
        原文=取字段(取字段(块,'call'),'argsRaw') or ''#call
    else:#进行中
        原文=取字段(块,'argsRaw') or ''#原文
    参=解析参数(原文)#解析
    码=对象字段(参,'code') if 参 else None#code
    态=调用状态(块)#状态
    出=结果文本(块) if 已落定 else None#结果
    元=元对象(块)#meta
    原名=首行(原文) if 原文!='' else None#回退名
    return {#卡
        'pluginId':串字段(元,'pluginId') if 元 else None,#插件
        'packageId':串字段(元,'packageId') if 元 else None,#包
        'name':(串字段(参,'name') or 原名) if 参 else 原名,#名
        'purpose':串字段(参,'purpose') if 参 else None,#用途
        'hostCode':串字段(码,'host') if 码 else None,#宿主码
        'clientCode':串字段(码,'client') if 码 else None,#客户端码
        'output':出,#结果
        'errorSummary':首行(出) if 态=='error' and 出 else None,#错摘要
        'state':态,#状态
    }#结束

def 运行卡片(块):#cordis_run
    """推导运行卡。"""
    已落定=isinstance(块,dict) and 'kind' in 块#落定
    if 已落定:#落定
        原文=取字段(取字段(块,'call'),'argsRaw') or ''#call
    else:#进行中
        原文=取字段(块,'argsRaw') or ''#原文
    参=解析参数(原文)#解析
    元=元对象(块)#meta
    态=调用状态(块)#状态
    出=结果文本(块) if 已落定 else None#结果
    原模式=串字段(参,'mode') if 参 else None#模式
    参插件=串字段(参,'pluginId') if 参 else None#参插件
    参包=串字段(参,'packageId') if 参 else None#参包
    return {#卡
        'pluginId':(串字段(元,'pluginId') or 参插件) if 元 else 参插件,#插件
        'packageId':(串字段(元,'packageId') or 参包) if 元 else 参包,#包
        'pluginRunId':串字段(元,'pluginRunId') if 元 else None,#运行
        'mode':原模式 if 原模式 in ('run','update') else None,#合法模式
        'seq':取字段(块,'seq') if 已落定 else None,#序号
        'output':出,#结果
        'errorSummary':首行(出) if 态=='error' and 出 else None,#错
        'state':态,#状态
    }#结束

def 动作卡片(块):#stop/undefine
    """推导停止或移除卡。"""
    已落定=isinstance(块,dict) and 'kind' in 块#落定
    if 已落定:#落定
        原文=取字段(取字段(块,'call'),'argsRaw') or ''#call
    else:#进行中
        原文=取字段(块,'argsRaw') or ''#原文
    参=解析参数(原文)#解析
    态=调用状态(块)#状态
    出=结果文本(块) if 已落定 else None#结果
    return {#卡
        'pluginId':(串字段(参,'pluginId') or 串字段(参,'id')) if 参 else None,#插件
        'output':出,#结果
        'errorSummary':首行(出) if 态=='error' and 出 else None,#错
        'state':态,#状态
    }#结束
