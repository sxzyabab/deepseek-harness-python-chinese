'读取当前远程调用的非所有者调用者'

def 主体于(调用):
    '调用外和所有者都返回空。非所有者返回其主体'
    if 调用 is None:#不在远程调用里
        return None#进程内可信代码
    对等=调用['peer'] if isinstance(调用,dict) else getattr(调用,'peer',None)#对等端
    if 对等 is None:#没有对等端
        return None#空
    主体=对等['principal'] if isinstance(对等,dict) and 'principal' in 对等 else getattr(对等,'principal',None)#主体
    if 主体 is None or 主体.get('kind')=='owner':#所有者不记到耐久输出
        return None#空
    return 主体#非所有者
