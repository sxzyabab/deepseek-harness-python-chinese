"""Node 原生 Inspector 协议返回值的小型校验器。"""
#对齐上游 worker/realms/host/values.ts

__all__=['是否原生记录','要求原生记录','可选原生字段']#仅中文公开名

def 是否原生记录(值):#是否原生记录
    """测试原生协议值是否为非数组对象记录。"""
    return isinstance(值,dict)#普通对象

def 要求原生记录(值,标签):#要求原生记录
    """要求一个原生协议对象记录。"""
    if not 是否原生记录(值):#非对象
        raise ValueError(f'{标签} must be an object')#抛错
    return 值#返回

def 可选原生字段(键,值):#可选原生字段
    """仅在原生请求提供了值时包含可选字段。"""
    return {} if 值 is None else {键:值}#有则含
