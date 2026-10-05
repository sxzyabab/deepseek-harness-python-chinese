from math import isfinite as 是有限浮点,copysign as 复制符号#有限浮点判定与符号复制
__all__=['最大安全整数','是否有限数','是否整值数','是否正有限数','是否正安全整数','是否非负安全整数','是否有限json数字']#仅中文公开名

最大安全整数=2**53-1#双精度浮点可无损表示的最大整数，JSON互操作的整数上限

def 是否有限数(值)->bool:
    '整数或浮点且有限，排除布尔'
    if isinstance(值,bool):#布尔是int的子类，必须先排除
        return False#布尔不是数字
    if isinstance(值,int):#整数恒有限
        return True#整数有限
    if isinstance(值,float):#浮点需排除无穷与非数
        return 是有限浮点(值)#有限即真
    return False#其余类型不是数字

def 是否整值数(值)->bool:
    '整数或数值为整数的浮点，排除布尔；外来JSON数字常以整值浮点出现'
    if isinstance(值,bool):#布尔是int的子类，必须先排除
        return False#布尔不是数字
    if isinstance(值,int):#整数直接通过
        return True#是整数
    if isinstance(值,float):#浮点需数值为整数，无穷与非数都不是
        return 值.is_integer()#整值即真
    return False#其余类型不是数字

def 是否正有限数(值)->bool:
    '大于零的有限整数或浮点，排除布尔'
    if 是否有限数(值):#先确认是有限数
        return 值>0#再要求为正
    return False#不是有限数

def 是否正安全整数(值)->bool:
    '整值数且落在1到最大安全整数之间，排除布尔'
    if 是否整值数(值):#先确认是整值数
        return 0<值<=最大安全整数#正且不超过安全上限
    return False#不是整值数

def 是否非负安全整数(值)->bool:
    '整值数且落在0到最大安全整数之间，排除布尔'
    if 是否整值数(值):#先确认是整值数
        return 0<=值<=最大安全整数#非负且不超过安全上限
    return False#不是整值数

def 是否有限json数字(值)->bool:
    '可无损写入JSON的数字：有限且不是负零，排除布尔'
    if not 是否有限数(值):#不是有限数
        return False#不能写入JSON
    if isinstance(值,float):#只有浮点会出现负零
        return not(值==0.0 and 复制符号(1.0,值)<0)#负零会在往返中丢失符号
    return True#整数无损
