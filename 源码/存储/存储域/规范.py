"""域声明词汇。spec 是域身份、布局与记录 schema 的唯一来源。"""
import re#正则
from ..存储.后端 import 单元名正则,键值单元描述符#单元名与描述符
__all__=['定义域','域表','描述符投影']#仅中文公开名

def 域表(schema):#声明一张表
    """声明一张表，值由 schema 在持久边界校验。"""
    return {'valueSchema':schema}#表声明

def _safe_parse_成功(schema,值):#判断 schema 是否接受某值
    if hasattr(schema,'safeParse'):#zod 风格
        结果=schema.safeParse(值)#安全解析
        if isinstance(结果,dict):#字典结果
            return 结果.get('success',False)#取 success
        return getattr(结果,'success',False)#对象结果
    try:#无 safeParse 则试 parse
        schema.parse(值)#解析
        return True#接受
    except Exception:#拒绝
        return False#不接受

def 定义域(spec):#钉住并校验域 spec
    """校验域声明字段；错误配置在模块加载时大声失败。"""
    名称=spec['name']#域名
    if 单元名正则.fullmatch(名称) is None:#域名不合法
        raise Exception(f"domain name '{名称}' must match {单元名正则.pattern}")#域名失败
    版本=spec['version']#版本
    if not isinstance(版本,int) or 版本<0:#非非负整数
        raise Exception(f"domain '{名称}' version must be a non-negative integer, got {版本}")#版本失败
    布局=spec.get('layout')#可选布局
    if 布局 is not None and 布局 not in ('single','per-record'):#非法布局
        raise Exception(f"domain '{名称}' layout must be 'single' or 'per-record', got {布局}")#布局失败
    for 表名 in spec.get('tables',{}):#每张表名
        if 单元名正则.fullmatch(表名) is None:#表名不合法
            raise Exception(f"domain '{名称}' table name '{表名}' must match {单元名正则.pattern}")#表名失败
    全局=spec.get('global')#可选全局
    if 全局 is not None and _safe_parse_成功(全局['schema'],None):#全局接受 null
        raise Exception(
            f"domain '{名称}' global schema must not accept null: "
            "null is the medium's \"never written\" sentinel, so a stored null could not round-trip"
        )#拒绝可空全局
    return spec#原样返回

def 描述符投影(spec):#投影到后端单元描述符
    """把域 spec 投影成 `KvFacet.open` 用的描述符。"""
    布局=spec.get('layout')#可选布局
    return 键值单元描述符(
        spec['name'],
        spec['version'],
        list(spec['tables'].keys()),
        spec.get('global') is not None,
        布局 if 布局 is not None else None,
    )#描述符
