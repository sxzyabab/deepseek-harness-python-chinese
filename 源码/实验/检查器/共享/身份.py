"""共享的品牌标识构造，不分配协议所有权。

对齐上游 `shared/identity.ts`。公开面仅中文名。
"""
__all__=['检查器标识','检查器id']#仅中文公开名

def 检查器标识(值):#品牌化标识
    """带一种检查器身份角色品牌的字符串。"""
    return 值#同串烙印

def 检查器id(值,标签):#校验并品牌化标识
    """校验并为跨边界标识打品牌。"""
    if not isinstance(值,str) or len(值)==0 or len(值)>256:#长度越界
        raise Exception(f'inspector protocol: {标签} must contain 1 to 256 characters')#英文诊断
    return 检查器标识(值)#打上角色品牌
