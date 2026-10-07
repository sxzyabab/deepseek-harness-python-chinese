__all__=['解析cdp请求','cdp错误','发送cdp失败','响应cdp请求']#仅中文公开名

def 是否普通对象(值):#普通对象判定
    '映射且非空'
    return isinstance(值,dict)#字典即普通对象

def 解析cdp请求(值):#解析CDP请求
    '在路由前解析一条 DevTools 请求'
    if not 是否普通对象(值):#非对象
        raise ValueError('inspector CDP: 请求无效')#抛错
    请求id=值.get('id')#id
    方法=值.get('method')#方法
    参数=值.get('params')#参数
    if not isinstance(请求id,int) or isinstance(请求id,bool) or 请求id<0:#id非法
        raise ValueError('inspector CDP: 请求无效')#抛错
    if 请求id>9007199254740991:#超安全整数
        raise ValueError('inspector CDP: 请求无效')#抛错
    if not isinstance(方法,str) or len(方法)==0:#method非法
        raise ValueError('inspector CDP: 请求无效')#抛错
    if 参数 is not None and not 是否普通对象(参数):#params非法
        raise ValueError('inspector CDP: 请求无效')#抛错
    return {'id':请求id,'method':方法,'params':参数 if 参数 is not None else {}}#请求对象

def cdp错误(请求id,码,信息):#构造错误响应
    '构造稳定的 CDP 错误响应'
    return {'id':请求id,'error':{'code':码,'message':信息}}#错误信封

def 发送cdp失败(传输,请求,错误):#发送失败
    '使用域错误码发送一次失败的 CDP 操作'
    信息=str(错误)#错误详情
    传输.发送(cdp错误(请求['id'],-32000,信息))#发送

def 响应cdp请求(传输,请求,操作):#响应CDP请求
    '通过一条传输结算一次 CDP 操作；操作返回期约，兑现值是 result 字典'
    def 发送结果(结果):#操作兑现后调用
        '回写成功响应'
        传输.发送({'id':请求['id'],'result':结果})#成功
    def 发送失败(错误):#操作被拒绝后调用
        '回写失败响应'
        发送cdp失败(传输,请求,错误)#失败
    操作().然后(发送结果,发送失败)#操作兑现或拒绝后回写
