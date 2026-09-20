import threading#中止事件
from ....api.网关.客户端 import 取消失败,载体失败#取消失败与载体失败
from .名册 import 客户端测试运行时错误#本包异常

__all__=['远程接口包名','收集远程命名空间','远程代理插件']

远程接口包名='@deepseek-ai/dsh-api-remotes'#远程接口包名
远程前缀='remote.'#远程服务前缀
中止事件=threading.Event#中止信号类型

def 收集远程命名空间(模块表,模拟):#收集远程命名空间
    """名册模块依赖的每个 remote.<ns>，外加模拟已有规则的每个端点的命名空间。"""
    名称集=set()
    for 模块 in 模块表:
        for 服务名 in 依赖名列表(getattr(模块,'inject',None)):
            if 服务名.startswith(远程前缀):#remote. 前缀
                名称集.add(服务名[len(远程前缀):])#收下命名空间
    for 端点 in 模拟.端点列表():#模拟已登记端点
        斜杠=端点.find('/')#斜杠位置
        if 斜杠>0 and not 端点.startswith('$'):#常规端点
            名称集.add(端点[:斜杠])#收下命名空间
    return sorted(名称集)#排序

def 依赖名列表(依赖):
    """列表形原样，记录形取键，缺席为空。"""
    if 依赖 is None:
        return []
    if isinstance(依赖,list):
        return 依赖
    if isinstance(依赖,dict):
        return list(依赖.keys())
    return []

def 远程代理插件(命名空间表,模拟):#远程代理插件
    """提供命名空间代理的插件；测试客户端启动在 Loader 行之前挂上它。"""
    def 应用(上下文):#应用
        """按命名空间提供代理。"""
        连接=上下文.获取服务('connection')#取连接
        for 命名空间 in 命名空间表:#逐个
            上下文.提供服务(远程前缀+命名空间,命名空间代理(命名空间,连接,模拟))#提供代理
    return {'inject':['connection'],'apply':应用}#插件面

class 命名空间代理:#命名空间代理
    """remote.<ns>.<method>(...) 转到 Connection rpc。"""

    def __init__(自身,命名空间,连接,模拟):#构造
        """记下命名空间、连接与模拟。"""
        自身._命名空间=命名空间#命名空间
        自身._连接=连接#连接
        自身._模拟=模拟#模拟

    def __getattr__(自身,属性):#取值
        """返回调用闭包。"""
        命名空间=自身._命名空间#命名空间
        连接=自身._连接#连接
        模拟=自身._模拟#模拟
        def 调用(*值):#方法
            """按模式走流或一元。"""
            端点=命名空间+'/'+属性#端点
            参数表=list(值)#位置参数
            信号=None#中止信号
            if len(参数表)>0 and isinstance(参数表[-1],中止事件):#末尾是中止事件
                信号=参数表.pop()#弹出
            if 模拟.取模式(端点)=='stream':#流模式
                打开=getattr(连接.rpc,'open',None)#开流
                if 打开 is None:#无开流器
                    raise 客户端测试运行时错误('client-test-runtime: '+端点+' 是流端点，但载体没有进程内开流器')#诊断
                流信号=信号 if 信号 is not None else 中止事件()#缺席则新建未置位事件
                return 打开('/api',端点,{'args':参数表},流信号)#打开流
            try:#一元调用
                return 连接.rpc.call('/api',端点,{'args':参数表},信号)#同步调用
            except Exception as 错误:#拒绝折叠
                if 信号 is not None and 信号.is_set():#已中止
                    return 取消失败(端点,错误)#取消失败
                return 载体失败(端点,错误)#载体失败
        return 调用#方法
