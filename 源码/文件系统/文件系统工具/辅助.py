"""本包共享的字段读取、承诺展开与数字判定。"""
import math#有限数判定
from ...依赖 import cordis#外部依赖胶水
def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从 dict 自有键或对象属性读取字段；对象为 None 或键缺席时返回缺省。工具参数、规范结果与 Cordis 服务都走这条路径。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 试取(对象,键):#读取可选字段
    """读取可选字段；缺席统一为 None，避免调用方各自写缺省。"""
    return 取字段(对象,键,None)#缺席为空

def 解开(值):#承诺则等待否则原样
    """若值是 thenable（Cordis 承诺），阻塞等待其兑现；同步值原样返回。工具执行路径对提供方异步方法统一走这里。"""
    if 是否thenable(值):#可等待
        return 值.等待()#等待承诺
    return 值#同步值

def 是否整数(值):#对齐JS Number.isInteger
    """对齐 JS Number.isInteger，排除布尔。"""
    if isinstance(值,bool):#布尔不是数字
        return False#布尔不是整数
    if isinstance(值,int):#整数
        return True#整数
    if isinstance(值,float):#浮点
        return 值.is_integer()#整值浮点
    return False#其它类型

def 是否有限数(值):#对齐JS Number.isFinite
    """对齐 JS Number.isFinite，排除布尔。"""
    if isinstance(值,bool):#布尔不是数字
        return False#布尔不是有限数
    if isinstance(值,(int,float)):#整数或浮点
        return math.isfinite(值)#有限
    return False#其它类型
