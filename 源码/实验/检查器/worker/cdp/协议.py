"""Worker 拥有的最小 CDP 请求与传输类型。"""
#对齐上游 worker/cdp/protocol.ts

from .....内核.智能体循环.辅助 import 解开,在线程跑#可等待则等待|后台跑

__all__=['解析cdp请求','cdp错误','发送cdp失败','响应cdp请求']#仅中文公开名

def 是否普通对象(值):#普通对象判定
    """映射且非空。"""
    return isinstance(值,dict)#字典即普通对象

def 解析cdp请求(值):#解析CDP请求
    """在路由前解析一条 DevTools 请求。"""
    if not 是否普通对象(值):#非对象
        raise ValueError('inspector CDP: invalid request')#抛错
    请求id=值.get('id')#id
    方法=值.get('method')#方法
    参数=值.get('params')#参数
    if not isinstance(请求id,int) or isinstance(请求id,bool) or 请求id<0:#id非法
        raise ValueError('inspector CDP: invalid request')#抛错
    if 请求id>9007199254740991:#超安全整数
        raise ValueError('inspector CDP: invalid request')#抛错
    if not isinstance(方法,str) or len(方法)==0:#method非法
        raise ValueError('inspector CDP: invalid request')#抛错
    if 参数 is not None and not 是否普通对象(参数):#params非法
        raise ValueError('inspector CDP: invalid request')#抛错
    return {'id':请求id,'method':方法,'params':参数 if 参数 is not None else {}}#请求对象

def cdp错误(请求id,码,信息):#构造错误响应
    """构造稳定的 CDP 错误响应。"""
    return {'id':请求id,'error':{'code':码,'message':信息}}#错误信封

def 发送cdp失败(传输,请求,错误):#发送失败
    """使用域错误码发送一次失败的 CDP 操作。"""
    信息=错误.args[0] if isinstance(错误,Exception) and 错误.args else str(错误)#错误信息
    if isinstance(错误,Exception) and hasattr(错误,'message'):#有message
        信息=str(错误)#统一
    传输.发送(cdp错误(请求['id'],-32000,信息 if isinstance(错误,Exception) else str(错误)))#发送

def 响应cdp请求(传输,请求,操作):#响应CDP请求
    """通过一条传输结算一次 CDP 操作。"""
    def 结算():#结算体
        """等待操作并回写。"""
        try:#执行
            结果=解开(操作())#可等待则等待
            传输.发送({'id':请求['id'],'result':结果})#成功
        except Exception as 错误:#失败
            发送cdp失败(传输,请求,错误)#失败
    在线程跑(结算)#后台结算
