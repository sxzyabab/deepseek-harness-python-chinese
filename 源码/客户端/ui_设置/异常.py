'本包不另立异常类。空路径和未保存沿上游原文在调用处抛出。校验失败的路径前缀在这里拼。'

def 抛校验失败(消息,路径=None):
    '按 schemastery 的 ValidationError 拼上路径前缀后抛出'
    前缀='$'#根
    if 路径 is not None:#有路径
        for 段 in 路径:#逐段
            if isinstance(段,str):#对象键
                前缀=前缀+'.'+段
            else:#数组下标
                前缀=前缀+'['+str(段)+']'
    if 前缀.startswith('.'):#上游会剥掉开头的点
        前缀=前缀[1:]
    if 前缀=='$':#根上不加前缀
        全文=消息
    else:#带路径
        全文=前缀+' '+消息
    raise Exception(全文)
