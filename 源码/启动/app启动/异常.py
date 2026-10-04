__all__=('启动错误',)#仅中文公开名

class 启动错误(Exception):
    '应用启动粘合层失败；可附带未激活条目元数据'

    def __init__(自身,消息,条目表=None):
        '记下消息与可选条目；失败 outcome 挂为 cause'
        条目表=条目表 if 条目表 is not None else []#条目
        失败值=[]#原失败
        for 项 in 条目表:#逐条
            结果=项.get('outcome') if isinstance(项,dict) else None#结果
            if isinstance(结果,dict) and 结果.get('kind')=='failed':#失败
                错=结果.get('error')#错误值
                if isinstance(错,BaseException):#异常
                    失败值.append(错)#收下
        if len(失败值)>0:#有原失败
            super().__init__(消息)#基类
            if len(失败值)==1:#单失败
                自身.__cause__=失败值[0]#挂上
            else:#多失败
                自身.__cause__=ExceptionGroup('Plugin activation failures',失败值)#聚合
        else:#无原失败
            super().__init__(消息)#基类
        自身.entries=条目表#条目
        自身.startup=None#启动日志切片
