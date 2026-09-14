from ..作用域 import 弱身份表#按身份存取的弱表

__all__=('包名','名称','注入','安装','应用')#仅中文公开名

包名='@deepseek-ai/dsh-agent'#本包名
名称='agent-invariant'#配套插件名（字面量不译）
注入=['invariants']#依赖 invariants 服务

def 安装(上下文对象,失败):
    """把智能体贡献安装进其子注册光纤。"""
    上次状态=弱身份表()#每个智能体上次状态
    def 状态变迁(_载体,载荷,*其余):
        """监听状态变迁。"""
        智能体=载荷['agent']#变迁主体
        状态=载荷['status']#刚进入的状态
        先前=上次状态.取(智能体)#取出上次状态
        if 先前==状态:
            失败('agent/status 重复了 '+str(状态)+'（空转变迁）')#空转视为失败
        上次状态.设(智能体,状态)#记下本次状态
    上下文对象.监听('agent/status',状态变迁,{'全局':True})#全局监听

def 应用(上下文对象,配置=None):
    """登记智能体不变量配套，返回拆除器。配置位由 Cordis 传入，此处忽略。"""
    return 上下文对象.invariants.register(包名,安装)#登记贡献并返回拆除器

应用.name=名称#Cordis name 槽
应用.inject=注入#Cordis inject 槽
default=应用#Cordis 默认导出槽
