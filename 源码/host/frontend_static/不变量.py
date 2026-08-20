"""`@deepseek-ai/dsh-host-frontend-static` 的本包拥有不变量配套。

对齐上游 `frontend-static/src/invariant.ts`。公开面仅中文名。
无运行时不变量：唯一拥有的关系是那一个兜底席位，无法从拆除流可靠探测。
"""
from cordis.工具 import 已兑现#立刻兑现

包名='@deepseek-ai/dsh-host-frontend-static'#本包所有权名
名称='host-frontend-static-invariant'#配套插件名
注入=['invariants']#依赖 invariants

__all__=['包名','名称','注入','安装','应用']#仅中文公开名

def 安装(上下文对象,失败):#空安装器
    """无运行时检查：席位对称由组合 HMR 安全测试覆盖。"""
    return#不挂

def 应用(上下文对象):#注册不变量配套
    """登记本包的不变量配套。"""
    return 已兑现(上下文对象.invariants.register(包名,安装))#登记
