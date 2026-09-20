import json,re#解析参数与语言提示

__all__=['编程工具调用名','代码程序']#仅中文公开名

编程工具调用名='run_code'#线协议工具名
类型脚本提示=re.compile(r'\bTypeScript\b',re.ASCII|re.IGNORECASE)#schema 里的 TypeScript
python提示=re.compile(r'\bPython\b',re.ASCII|re.IGNORECASE)#schema 里的 Python

def 记录对象(值):
    """对象记录；数组与标量不是。"""
    if isinstance(值,dict):#映射
        return 值#记录
    return None#非记录

def 解析记录(原文):
    """把 JSON 对象串解析成记录。"""
    if 原文 is None:#缺席
        return None#无
    try:#入口校验
        return 记录对象(json.loads(原文))#对象才收下
    except (TypeError,ValueError,json.JSONDecodeError):#非 JSON
        return None#无

def 已记录语言(schema原文):
    """从调用时可见的 schema 读语言提示；源码与当前运行时不猜。"""
    schema=解析记录(schema原文)#schema 对象
    参数=None#parameters
    if schema is not None and 'parameters' in schema:#有 parameters
        参数=记录对象(schema['parameters'])#记下
    属性=None#properties
    if 参数 is not None and 'properties' in 参数:#有 properties
        属性=记录对象(参数['properties'])#记下
    代码=None#code 字段
    if 属性 is not None and 'code' in 属性:#有 code
        代码=记录对象(属性['code'])#记下
    描述=None#description
    if 代码 is not None and 'description' in 代码:#有 description
        描述=代码['description']#记下
    if not isinstance(描述,str):#无描述
        return None#未知
    类型脚本=类型脚本提示.search(描述) is not None#TypeScript
    python=python提示.search(描述) is not None#Python
    if 类型脚本==python:#同时有或同时无
        return None#未知
    return 'typescript' if 类型脚本 else 'python'#线协议语言值

def 代码程序(单元格):
    """从已记录工具参数与 schema 取出可回放的 PTC 程序。其它工具或非法参数则无。"""
    种类=单元格['kind'] if 'kind' in 单元格 else None#格种类
    if 种类!='tool' and 种类!='subtool':#非工具格
        return None#无
    if 'toolName' not in 单元格 or 单元格['toolName']!=编程工具调用名:#非 run_code
        return None#无
    if 'inputDetail' not in 单元格 or 单元格['inputDetail'] is None:#无参数原文
        return None#无
    参数=解析记录(单元格['inputDetail'])#参数
    if 参数 is None or 'code' not in 参数 or not isinstance(参数['code'],str):#缺 code
        return None#无
    if 'description' in 参数 and 参数['description'] is not None and not isinstance(参数['description'],str):#描述非法
        return None#无
    描述=''#默认空
    if 'description' in 参数 and isinstance(参数['description'],str) and 参数['description'].strip()!='':#非空描述
        描述=参数['description']#用描述
    else:#用源码首行
        for 行 in 参数['code'].splitlines():#按行
            净=行.strip()#去空白
            if 净!='':#有内容
                描述=净#首行
                break#停
    schema原文=单元格['schemaDetail'] if 'schemaDetail' in 单元格 else None#调用时 schema
    return {#程序
        'rawInput':单元格['inputDetail'],#原始参数
        'source':参数['code'],#源码
        'description':描述,#描述
        'arguments':参数,#参数记录
        'language':已记录语言(schema原文),#语言或无
    }#结束
