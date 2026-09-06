"""域声明词汇。spec 是域身份、布局与记录 schema 的唯一来源。"""
from ..存储.后端 import 单元名正则,键值单元描述符#单元名与描述符
from .错误 import 域错误#域声明失败
__all__=['定义域','域表','描述符投影']#仅中文公开名

def 域表(schema):
    """声明一张表，值由 schema 在持久边界校验。"""
    return {'valueSchema':schema}#表声明

def 模式接受空(模式):
    """判断 schema 是否接受 None。None 是介质从未写入哨兵，全局槽不得接受。"""
    try:#试解析空
        模式.parse(None)#schemastery 边界
        return True#接受
    except Exception:#拒绝形态随 schema 实现，未钉成一类
        return False#不接受

def 定义域(spec):
    """校验域声明字段；错误配置在模块加载时大声失败。spec 是 dict。"""
    名称=spec['name']#域名
    if 单元名正则.fullmatch(名称) is None:#域名不合法
        raise 域错误('malformed-medium',"domain name '"+名称+"' must match "+单元名正则.pattern)#域名失败
    版本=spec['version']#版本
    if isinstance(版本,bool) or (not isinstance(版本,int)) or 版本<0:#非非负整数
        raise 域错误('malformed-medium',"domain '"+名称+"' version must be a non-negative integer, got "+str(版本))#版本失败
    布局=spec['layout'] if 'layout' in spec else None#可选布局
    if 布局 is not None and 布局 not in ('single','per-record'):#非法布局
        raise 域错误('malformed-medium',"domain '"+名称+"' layout must be 'single' or 'per-record', got "+str(布局))#布局失败
    表列表=spec['tables'] if 'tables' in spec else {}#表声明
    for 表名 in 表列表:#每张表名
        if 单元名正则.fullmatch(表名) is None:#表名不合法
            raise 域错误('malformed-medium',"domain '"+名称+"' table name '"+表名+"' must match "+单元名正则.pattern)#表名失败
    全局=spec['global'] if 'global' in spec else None#可选全局
    if 全局 is not None and 模式接受空(全局['schema']):#全局接受 null
        raise 域错误(
            'malformed-medium',
            "domain '"+名称+"' global schema must not accept null: "
            +"null is the medium's \"never written\" sentinel, so a stored null could not round-trip",
        )#拒绝可空全局
    return spec#原样返回

def 描述符投影(spec):
    """把域 spec 投影成 `KvFacet.open` 用的描述符。spec 是 dict。"""
    布局=spec['layout'] if 'layout' in spec else None#可选布局
    return 键值单元描述符(
        spec['name'],
        spec['version'],
        list(spec['tables'].keys()),
        ('global' in spec) and spec['global'] is not None,
        布局 if 布局 is not None else None,
    )#描述符
