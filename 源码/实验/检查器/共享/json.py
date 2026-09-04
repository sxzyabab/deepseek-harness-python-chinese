"""检查器跨界消息一律承认的 JSON 值。

对齐上游 `shared/json.ts`。公开面仅中文名。
"""
import json#序列化

__all__=[#仅中文公开名
    '检查器json标量','检查器json值','检查器json对象',
    '是否json值','要求json对象','json字节长度','是否普通对象',
]#公开面结束

检查器json标量=type(None)|bool|int|float|str#JSON标量

class 检查器json对象(dict):#JSON对象面
    """检查器传输接受的 JSON 兼容对象。"""

检查器json值=检查器json标量|list|检查器json对象#JSON兼容值

def 是否普通对象(值):#是否为普通对象
    """检验是否为带字符串自有键的普通对象。"""
    if not isinstance(值,dict) or isinstance(值,检查器json对象) is False and type(值) is not dict:#非dict
        if not isinstance(值,dict):#非映射
            return False#否
    if isinstance(值,list):#数组
        return False#否
    return isinstance(值,dict)#普通dict

def 访问json(值,祖先):#递归访问JSON形状
    """带祖先集合递归访问。"""
    if 值 is None or isinstance(值,(str,bool)):#标量真
        return True#真
    if isinstance(值,(int,float)):#数
        if isinstance(值,bool):#bool是int子类
            return True#已在上
        if not (值==值 and 值 not in (float('inf'),float('-inf'))):#非有限
            return False#否
        if 值==0 and str(值)=='-0':#负零
            return False#否
        return True#有限数
    if not isinstance(值,(dict,list)) or id(值) in 祖先:#非对象或环
        return False#否
    祖先.add(id(值))#记入祖先
    try:#访问子项
        if isinstance(值,list):#数组分支
            return all(访问json(项,祖先) for 项 in 值)#逐项
        if not 是否普通对象(值):#非普通对象
            return False#否
        for 键,子 in 值.items():#逐键
            if not isinstance(键,str):#仅字符串键
                return False#否
            if not 访问json(子,祖先):#值非法
                return False#否
        return True#对象合法
    finally:#无论成败
        祖先.discard(id(值))#退出祖先

def 是否json值(值):#是否为可过线JSON值
    """检验能否无损穿过 MessagePort 与 JSON WebSocket。"""
    return 访问json(值,set())#带祖先集合

def 要求json对象(值,标签):#要求普通JSON对象
    """要求普通 JSON 对象并以收窄后类型返回。"""
    if not 是否普通对象(值) or not 是否json值(值):#非普通或非JSON
        raise Exception(f'inspector protocol: {标签} must be a JSON object')#英文诊断
    return 值#已收窄

def json字节长度(值):#JSON线上字节长度
    """计算 JSON 线上值的 UTF-8 字节长度。"""
    return len(json.dumps(值,ensure_ascii=False,separators=(',',':')).encode('utf-8'))#序列化后量
