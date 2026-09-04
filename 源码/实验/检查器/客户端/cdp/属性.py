"""Client 侧属性枚举。

对齐上游 `client/cdp/properties.ts`。公开面仅中文名。
"""
from .错误 import 客户端运行时执行错误#执行错误

__all__=['获取客户端属性']#仅中文公开名

def 获取客户端属性(对象存储,命令,最大属性,分配):#取属性
    """枚举一个保留的 Client 对象的属性。"""
    句柄=命令.get('handle')#句柄
    try:#取值
        值=对象存储.获取(句柄)#取值
    except 客户端运行时执行错误:#已释放
        raise#上抛
    属性们=[]#属性列表
    if isinstance(值,dict):#映射
        for 名,子 in list(值.items())[:最大属性]:#逐键
            属性们.append({'name':str(名),'value':对象存储.序列化(子,{},分配),'configurable':True,'enumerable':True,'isOwn':True})#属性
    elif isinstance(值,(list,tuple)):#序列
        for 索引,子 in enumerate(list(值)[:最大属性]):#逐项
            属性们.append({'name':str(索引),'value':对象存储.序列化(子,{},分配),'configurable':True,'enumerable':True,'isOwn':True})#属性
    return {'properties':属性们}#属性结果
