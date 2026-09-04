"""由 Worker 侧 Chrome DevTools 连接拥有的不透明标识符。"""
#对齐上游 worker/cdp/ids.ts

__all__=['cdp字符串id','cdp数字id']#仅中文公开名

def cdp字符串id(值,标签):#字符串id打品牌
    """校验并为 CDP 适配器分配或接受的字符串 id 打上品牌。"""
    if len(值)==0 or len(值)>16384:#长度非法
        raise ValueError(f'inspector CDP: {标签} must contain 1 to 16384 characters')#抛错
    return 值#返回品牌id

def cdp数字id(值,标签):#数字id打品牌
    """校验并为 CDP 适配器分配的正数数字 id 打上品牌。"""
    if not isinstance(值,int) or isinstance(值,bool) or 值<1:#非法
        raise ValueError(f'inspector CDP: {标签} must be a positive integer')#抛错
    if 值>9007199254740991:#超安全整数
        raise ValueError(f'inspector CDP: {标签} must be a positive integer')#抛错
    return 值#返回品牌id
