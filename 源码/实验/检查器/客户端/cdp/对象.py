"""Client 本地对象句柄与 CDP 兼容的 RemoteObject 序列化。

对齐上游 `client/cdp/objects.ts`。公开面仅中文名。
"""
from ...共享.桥接.标识 import 客户端远程对象句柄#句柄
from ...共享.json import 是否json值#JSON
from ...共享.cordis.对象注册表 import 识别领域对象#语义引用
from .错误 import 客户端运行时执行错误#执行错误

__all__=['客户端对象分配','客户端运行时对象选项','客户端对象存储']#仅中文公开名

最大类原型深度=32#类名原型遍历上限

class 客户端对象存储:#Client对象存储
    """每个 DevTools 会话拥有的全部存活 Client 对象引用。"""
    def __init__(自身,最大对象):#构造
        """保存上限。"""
        自身.最大对象=最大对象#上限
        自身.对象={}#对象表
        自身.组={}#组表
        自身.分配={}#分配表
        自身.下一序号=1#下一序号

    def 开始分配(自身):#开始分配
        """开始跟踪一次独立结算操作分配的句柄。"""
        分配=object()#身份
        自身.分配[id(分配)]=set()#登记
        return 分配#返回

    def 提交分配(自身,分配):#提交分配
        """保留操作的句柄并释放其分配簿记。"""
        自身.分配.pop(id(分配),None)#删除簿记

    def 回滚(自身,分配):#回滚分配
        """精确丢弃一次失败操作分配的句柄。"""
        句柄们=自身.分配.pop(id(分配),set())#取出
        for 句柄 in 句柄们:#释放
            自身.释放(句柄)#释放

    def 获取(自身,句柄):#获取
        """解析一个句柄。"""
        对象=自身.对象.get(句柄)#查表
        if 对象 is None:#已释放
            raise 客户端运行时执行错误('object-not-found','Client RemoteObject was released')#已释放
        return 对象['value']#返回值

    def 取组(自身,句柄):#取组
        """读取经一个句柄到达的值所继承的对象组。"""
        对象=自身.对象.get(句柄)#查表
        if 对象 is None:#已释放
            raise 客户端运行时执行错误('object-not-found','Client RemoteObject was released')#已释放
        return 对象.get('group')#返回组

    def 登记(自身,值,组=None,分配=None):#登记句柄
        """登记句柄。"""
        if len(自身.对象)>=自身.最大对象:#超限
            raise 客户端运行时执行错误('result-too-large','Client Runtime object table is full')#超限
        句柄=客户端远程对象句柄(f'object-{自身.下一序号}')#句柄
        自身.下一序号+=1#递增
        自身.对象[句柄]={'value':值,'group':组}#写入
        if 组 is not None:#有组
            自身.组.setdefault(组,set()).add(句柄)#入组
        if 分配 is not None:#有分配
            自身.分配.setdefault(id(分配),set()).add(句柄)#记分配
        return 句柄#返回

    def 序列化(自身,值,选项=None,分配=None):#序列化
        """将存活值转换为 JSON 安全的 RemoteObject 协议。"""
        if 选项 is None:#缺省
            选项={}#空
        原始=序列化原始(值)#尝试原始
        if 原始 is not None:#原始
            return 原始#原始
        if 选项.get('returnByValue') is True:#按值
            return {'descriptor':{'type':'function' if callable(值) else 'object','value':按值序列化(值),'description':描述(值)}}#结果
        类型='function' if callable(值) else ('symbol' if type(值).__name__=='symbol' else 'object')#类型
        子类型=子类型Of(值) if 类型=='object' else None#子类型
        语义=识别领域对象(值)#语义引用
        结果={'descriptor':{'type':类型,'className':类名(值),'description':描述(值)},'object':{'handle':自身.登记(值,选项.get('group'),分配)}}#结果
        if 子类型 is not None:#子类型
            结果['descriptor']['subtype']=子类型#子类型
        if 语义 is not None:#语义
            结果['semanticReference']=语义#语义
        return 结果#返回

    def 释放(自身,句柄):#释放
        """精确释放一个句柄。"""
        对象=自身.对象.pop(句柄,None)#删除
        if 对象 is None:#幂等
            return#返回
        组=对象.get('group')#组
        if 组 is None:#无组
            return#返回
        成员=自身.组.get(组)#组成员
        if 成员 is not None:#移除
            成员.discard(句柄)#移除
            if len(成员)==0:#空组
                自身.组.pop(组,None)#空组删除

    def 释放组(自身,组):#释放组
        """释放一个 DevTools 对象组中的每个句柄。"""
        成员=自身.组.pop(组,None)#成员
        if 成员 is None:#无
            return#返回
        for 句柄 in 成员:#删对象
            自身.对象.pop(句柄,None)#删对象

    def 清空(自身):#清空
        """清空全部对象。"""
        自身.对象.clear()#清对象
        自身.组.clear()#清组
        自身.分配.clear()#清分配

def 序列化原始(值):#尝试原始
    """尝试原始。"""
    if 值 is None:#null
        return {'descriptor':{'type':'object','subtype':'null','value':None}}#null
    if isinstance(值,bool):#布尔
        return {'descriptor':{'type':'boolean','value':值}}#布尔
    if isinstance(值,str):#字符串
        return {'descriptor':{'type':'string','value':值}}#字符串
    if isinstance(值,(int,float)) and not isinstance(值,bool):#数字
        if 值!=值:#NaN
            return {'descriptor':{'type':'number','unserializableValue':'NaN'}}#NaN
        if 值==float('inf'):#Infinity
            return {'descriptor':{'type':'number','unserializableValue':'Infinity'}}#Inf
        if 值==float('-inf'):# -Infinity
            return {'descriptor':{'type':'number','unserializableValue':'-Infinity'}}#-Inf
        return {'descriptor':{'type':'number','value':值}}#数
    return None#非原始

def 按值序列化(值):#按值
    """按值。"""
    if 是否json值(值):#JSON
        return 值#原样
    return str(值)#转串

def 描述(值):#描述
    """描述。"""
    try:#转串
        return str(值)#转串
    except Exception:#失败
        return type(值).__name__#类名

def 类名(值):#类名
    """类名。"""
    return type(值).__name__#类名

def 子类型Of(值):#子类型
    """子类型。"""
    if isinstance(值,list):#数组
        return 'array'#数组
    if isinstance(值,dict):#映射
        return None#普通对象
    if isinstance(值,Exception):#错误
        return 'error'#错误
    return None#无
