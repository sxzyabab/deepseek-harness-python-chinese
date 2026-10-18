import json
import re

__all__=['编程工具调用名','代码程序']

编程工具调用名='run_code'#PTC 入口的记录名
类型脚本提示=re.compile(r'\bTypeScript\b',re.I)#schema 里的语言提示
python提示=re.compile(r'\bPython\b',re.I)#schema 里的语言提示

def 记录对象(值):
    '对象记录；数组与标量不是'
    if isinstance(值,dict):
        return 值
    return None

def 解析记录(原文):
    '把 JSON 对象串解析成记录'
    if 原文 is None:
        return None
    try:
        return 记录对象(json.loads(原文))
    except json.JSONDecodeError:
        return None

def 代码程序(格):
    '从已记录工具参数与 schema 取出可回放的 PTC 程序。其它工具或非法参数则无'
    if 格.get('kind') not in ('tool','subtool'):
        return None
    if 格.get('toolName')!=编程工具调用名 or 格.get('inputDetail') is None:
        return None
    参数=解析记录(格.get('inputDetail'))
    if 参数 is None or not isinstance(参数.get('code'),str):
        return None
    if 'description' in 参数 and 参数['description'] is not None and not isinstance(参数['description'],str):
        return None
    说明=参数.get('description')
    if isinstance(说明,str) and 说明.strip()!='':
        描述=说明
    else:
        描述=''
        for 行 in 参数['code'].splitlines():
            if 行.strip()!='':
                描述=行.strip()
                break
    模式=解析记录(格.get('schemaDetail'))
    属性=记录对象((记录对象(None if 模式 is None else 模式.get('parameters')) or {}).get('properties'))
    代码说明=None if 属性 is None else 记录对象(属性.get('code'))
    描述文本=None if 代码说明 is None else 代码说明.get('description')
    语言=None
    if isinstance(描述文本,str):
        是类型脚本=类型脚本提示.search(描述文本) is not None
        是python=python提示.search(描述文本) is not None
        if 是类型脚本!=是python:
            语言='typescript' if 是类型脚本 else 'python'
    return {
        'rawInput':格['inputDetail'],
        'source':参数['code'],
        'description':描述,
        'arguments':参数,
        'language':语言,
    }
