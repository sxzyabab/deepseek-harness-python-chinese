from pywebbridge import undefined as 未定义

__all__=['绑定快照选择器']#仅中文公开名

def 是函数(值):
    'undefined 虽然有 __call__，但不是 JavaScript 函数'
    return 值 is not 未定义 and callable(值)

def 读钩(源,名):
    '对象走方法，字典走同名键'
    方法=getattr(源,名,None)#对象
    if 是函数(方法):#有方法
        return 方法#用
    if isinstance(源,dict):#字典源
        函数=源.get(名)#键
        if 是函数(函数):#有函数
            return 函数#用
    raise TypeError('快照源缺少 '+名)#不能当钩子

def 绑定快照选择器(源):
    'subscribe/getSnapshot 按源捕获进稳定闭包一次。源可以是带方法的对象，也可以是同名键的字典'
    订阅源=读钩(源,'subscribe')#订阅
    读取源=读钩(源,'getSnapshot')#读取
    def 订阅(回调):
        '稳定订阅闭包'
        return 订阅源(回调)#订
    def 取快照():
        '稳定读快照闭包'
        return 读取源()#读

    def 用选择器(选择器,相等=None):
        '无服务器快照；相等性默认 is'
        快照=取快照()#读快照
        return 选择器(快照)#选中切片
    用选择器._subscribe=订阅#挂订阅供外部
    用选择器._getSnapshot=取快照#挂快照供外部
    return 用选择器#返回钩子
