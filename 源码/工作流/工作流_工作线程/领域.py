"""把离开脚本领域的值在跨过 worker 边界之前物化为普通 JSON，并在不拒绝运行的前提下渲染脚本抛出值。遍历拒绝 JSON 无法保全的值，但信任模型写的工作流脚本：getter 与代理陷阱可能运行，领域执行不是安全边界。worker 提供宿主循环隔离与强制终止，不是敌意值收容。"""
import math#有限数判定

class 物化错误(Exception):#领域物化失败
    """由从领域物化抛出；调用方把它包进正确的工作流错误码。"""
    def __init__(自身,路径,原因):#记下路径与原因
        """记下路径与原因。"""
        Exception.__init__(自身,路径+': '+原因)#拼成错误消息
        自身.path=路径#英文路径
        自身.路径=路径#中文路径
        自身.reason=原因#英文原因
        自身.原因=原因#中文原因
        自身.name='MaterializeError'#固定错误名

def 渲染抛出(错误):#把抛出值收成可记录字符串
    """把抛出值渲染成失败文本且永不抛错：优先 stack（宿主或领域——领域错误的 stack 是普通字符串读取），再回退到 message，然后 str()。读取这些属性可能跑脚本代码（getter、toString）——在本模块的信任前提下可接受；若那段代码自己抛错，则返回固定标签。"""
    try:#尝试读取 stack/message 或强制转字符串
        堆栈=getattr(错误,'stack',None) if 错误 is not None else None#尝试读堆栈
        if isinstance(堆栈,str) and len(堆栈)>0:#有非空堆栈则用它
            return 堆栈#返回堆栈
        消息=getattr(错误,'message',None) if 错误 is not None else None#尝试读消息
        if isinstance(消息,str) and len(消息)>0:#有非空消息则用它
            return 消息#返回消息
        if isinstance(错误,BaseException) and str(错误):#异常的字符串形式
            return str(错误)#返回字符串
        return str(错误)#最后强制转字符串
    except Exception:#访问器或 toString 自己抛错
        # 抛出值上的访问器/toString 抛错——渲染必须完备（drive() 永不拒绝约定），因此回退到固定标签。
        return '[unrenderable thrown value]'#转换失败时返回固定标签

def 是否普通原型(值):#判断是否为普通对象原型链
    """对象的原型链是否表示普通数据对象。在 Python 中：dict 视为普通对象；其它自定义类型拒绝。Date/Map/类实例会被拒绝。"""
    return isinstance(值,dict)#仅普通字典

def 从领域物化(值,根='value'):#从领域物化到宿主 JSON
    """把 value（通常来自脚本领域）拷成普通宿主 JSON 数据。根上的 None/缺席原样返回；嵌套缺席以及 JSON 无法无损表示的值带着出事路径失败。属性访问器正常运行，抛错的读取会带上已渲染失败被包起来。"""
    if 值 is None:#根 None 在本端口中当作 null 原样返回（上游根 undefined 原样；Python 无 undefined，None 即 null）
        return None#原样返回
    try:#走递归物化
        return 物化(值,根,set())#带环检测集合递归拷贝
    except 物化错误:#已是物化错误则原样抛出
        raise#原样抛出
    except Exception as 错误:#物化或属性读取失败
        # 属性读取跑了脚本代码并抛错；收成完备错误，好让调用方守住狭窄的物化错误约定。
        raise 物化错误(根,'reading the value threw: '+渲染抛出(错误))#包装成物化错误

def 物化(值,路径,已见):#按类型递归物化一个值
    """按类型递归物化一个值。"""
    if isinstance(值,bool):#布尔（须在 int 之前判定）
        return 值#原样返回
    if isinstance(值,str):#字符串
        return 值#原样返回
    if isinstance(值,int) and not isinstance(值,bool):#整数
        return 值#原样返回
    if isinstance(值,float):#浮点
        if not math.isfinite(值):#非有限数字拒绝
            raise 物化错误(路径,'non-finite numbers are not JSON data')#非有限拒绝
        return 值#有限数字原样返回
    if isinstance(值,(bytes,bytearray)):#字节不是 JSON
        raise 物化错误(路径,'bytes are not JSON data')#字节拒绝
    if callable(值) and not isinstance(值,(list,dict)):#函数
        raise 物化错误(路径,'functions are not plain JSON data')#函数不是普通 JSON
    if 值 is None:#null
        return None#原样返回
    if isinstance(值,list):#数组路径
        对象标识=id(值)#环检测键
        if 对象标识 in 已见:#环拒绝
            raise 物化错误(路径,'circular references are not JSON data')#环拒绝
        已见.add(对象标识)#进入环检测集合
        try:#拷贝数组
            return 物化数组(值,路径,已见)#数组路径
        finally:#无论成败都离开环检测
            已见.discard(对象标识)#退出环检测集合
    if isinstance(值,dict):#普通对象路径
        对象标识=id(值)#环检测键
        if 对象标识 in 已见:#环拒绝
            raise 物化错误(路径,'circular references are not JSON data')#环拒绝
        已见.add(对象标识)#进入环检测集合
        try:#拷贝对象
            return 物化对象(值,路径,已见)#普通对象路径
        finally:#无论成败都离开环检测
            已见.discard(对象标识)#退出环检测集合
    raise 物化错误(路径,'only plain objects and arrays are JSON data (exotic prototype)')#奇异类型拒绝

def 物化数组(值,路径,已见):#物化数组
    """物化数组；空洞与非索引属性拒绝。"""
    输出=[]#宿主侧副本
    for 索引 in range(len(值)):#按索引逐项拷贝
        输出.append(物化(值[索引],路径+'['+str(索引)+']',已见))#递归物化该项
    return 输出#返回数组副本

def 物化对象(值,路径,已见):#物化普通对象
    """物化普通对象；符号键与奇异原型拒绝。"""
    if not 是否普通原型(值):#原型链不是普通对象
        raise 物化错误(路径,'only plain objects and arrays are JSON data (exotic prototype)')#奇异原型拒绝
    输出={}#宿主侧副本
    for 键 in 值.keys():#逐个可枚举字符串键拷贝
        if not isinstance(键,str):#非字符串键
            raise 物化错误(路径,'symbol-keyed properties are not plain JSON data')#非字符串键拒绝
        # 直接写入自有数据属性，避免特殊键改写原型语义。
        输出[键]=物化(值[键],路径+'.'+键,已见)#递归物化该字段
    return 输出#返回对象副本
