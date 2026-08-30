"""包内智能体生命周期不变量。

对齐上游 `agent/src/invariant.ts`。公开面仅中文名；Cordis 加载槽 `name`/`inject`/`apply` 为协议兼容别名，不入 `__all__`。配套插件名字面量 `agent-invariant` 不译。
"""
from ...依赖 import cordis#外部依赖胶水
from ..作用域 import 弱身份表#按身份存取的弱表

__all__=('包名','名称','注入','安装','应用')#仅中文公开名

包名='@deepseek-ai/dsh-agent'#本包名
名称='agent-invariant'#配套插件名（字面量不译）
注入=['invariants']#依赖 invariants 服务
name=名称#Cordis 插件名槽
inject=注入#Cordis 依赖声明槽

def 取字段(对象,键):#读取映射或对象上的字段
    """读取映射或对象上的字段。"""
    if isinstance(对象,dict):#映射
        return 对象[键]#映射键
    return getattr(对象,键)#对象属性

def 安装(上下文对象,失败):#把智能体贡献安装进子注册光纤
    """把智能体贡献安装进其子注册光纤。"""
    上次状态=弱身份表()#每个智能体上次状态
    def 状态变迁(_载体,载荷,*其余):#监听状态变迁
        """监听状态变迁。"""
        智能体=取字段(载荷,'agent')#变迁主体
        状态=取字段(载荷,'status')#刚进入的状态
        先前=上次状态.取(智能体)#取出上次状态
        if 先前==状态:#同一状态再次发出
            失败('agent/status repeated '+str(状态)+' (no-op transition)')#空转视为失败
        上次状态.设(智能体,状态)#记下本次状态
    上下文对象.on('agent/status',状态变迁,{'global':True})#全局监听

def 应用(上下文对象,配置=None):#登记智能体不变量配套
    """登记智能体不变量配套，返回已兑现拆除器。配置位由 Cordis 传入，此处忽略。"""
    return 已兑现(上下文对象.invariants.register(包名,安装))#登记贡献并返回拆除器

apply=应用#Cordis 插件入口槽
