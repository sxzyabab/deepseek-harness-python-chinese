"""把脚本 VM 值物化为普通 JSON，并渲染抛出值。获取器与代理陷阱可能在隔离 Node 进程内执行；进程隔离与取消属于 PTC，不属于 VM。"""
import math#有限数判定
__all__=['物化错误','渲染抛出','从领域物化']#仅中文公开名

class 物化错误(Exception):#从领域物化失败
    """由从领域物化抛出；调用方再包成对应工作流错误码。"""
    def __init__(自身,路径,原因):#记下路径与原因
        """路径是出错位置，原因是英文说明。"""
        super().__init__(路径+': '+原因)#拼消息
        自身.name='MaterializeError'#固定错误名
        自身.路径=路径#出错路径
        自身.原因=原因#原因

def 渲染抛出(错误):#把抛出值收成失败文本
    """永不抛：优先 stack，其次 message，再 String()。读这些属性可能跑脚本代码；若那代码自己抛，返回固定标签。"""
    try:#优先栈
        栈=getattr(错误,'stack',None)#栈
        if type(栈) is str and len(栈)>0:#有栈
            return 栈#栈
        消息=getattr(错误,'message',None)#消息字段
        if type(消息) is str and len(消息)>0:#有消息
            return 消息#消息
        return str(错误)#强制转
    except (物化错误,TypeError,ValueError,AttributeError):#渲染失败
        return '[unrenderable thrown value]'#固定标签

def 有朴素原型(值):#普通数据对象原型链
    """原型为 None，或其原型的原型为 None（领域的 Object.prototype）。Date/Map/类实例链更长，拒绝。"""
    原型=type(值)#Python 无 JS 原型链；dict/list 为朴素
    if 原型 is dict or 原型 is list:#朴素容器
        return True
    return False#否

def 从领域物化(值,根='value'):#拷到宿主 JSON
    """把值（通常来自 vm 领域）拷成普通宿主 JSON。根 undefined 原样返回；嵌套 undefined 与 JSON 不能无损表示的值按出错路径失败。"""
    if 值 is None:#Python 无 undefined；None 当 JSON null
        return None#null
    try:#物化
        return 物化(值,根,set())#递归
    except 物化错误:#原样
        raise#再抛
    except BaseException as 错误:#属性读取抛了
        raise 物化错误(根,'reading the value threw: '+渲染抛出(错误))#包成物化错误

def 物化(值,路径,已见):#一值
    """按类型物化一个值。"""
    种类=type(值)#运行时类型
    if 种类 is bool or 种类 is str:#布尔或字符串
        return 值#原样
    if 种类 is int or 种类 is float:#数字
        if not math.isfinite(值):#非有限
            raise 物化错误(路径,'non-finite numbers are not JSON data')#拒绝
        return 值#数字
    if 种类 not in (dict,list) and 值 is not None:#其它
        if callable(值):#函数
            raise 物化错误(路径,'functions are not plain JSON data')#拒绝
        raise 物化错误(路径,'symbols are not plain JSON data')#其余拒绝
    if 值 is None:#null
        return None#null
    标识=id(值)#身份
    if 标识 in 已见:#环
        raise 物化错误(路径,'circular references are not JSON data')#拒绝
    已见.add(标识)#入环集
    try:#物化容器
        if 种类 is list:#数组
            return 物化数组(值,路径,已见)#数组
        return 物化对象(值,路径,已见)#对象
    finally:#出环集
        已见.discard(标识)#离开

def 物化数组(值,路径,已见):#稠密数组
    """拒绝稀疏与非下标自有属性。"""
    结果=[]#拷贝
    下标=0#从 0
    while 下标<len(值):#逐项
        结果.append(物化(值[下标],路径+'['+str(下标)+']',已见))#项
        下标+=1#推进
    return 结果#数组

def 物化对象(值,路径,已见):#普通对象
    """只接受朴素 dict；用 define 语义写下自有键，含 __proto__。"""
    if not 有朴素原型(值):#奇异原型
        raise 物化错误(路径,'only plain objects and arrays are JSON data (exotic prototype)')#拒绝
    结果={}#拷贝
    for 键 in 值.keys():#自有键
        if type(键) is not str:#非字符串键
            raise 物化错误(路径,'symbol-keyed properties are not plain JSON data')#拒绝
        结果[键]=物化(值[键],路径+'.'+键,已见)#属性
    return 结果#对象
