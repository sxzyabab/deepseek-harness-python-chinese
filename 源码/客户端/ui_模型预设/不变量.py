"""`@deepseek-ai/dsh-client-ui-permission-presets` 的本包拥有不变量配套。

对齐上游 `ui-permission-presets/src/invariant.ts`。公开面仅中文名。

无运行时不变量：命令与槽位贡献的生命周期由 HMR 安全规格证明。
"""
from ...依赖 import cordis#外部依赖胶水
包名='@deepseek-ai/dsh-client-ui-permission-presets'#本包的不变量所有权名
名称='client-ui-permission-presets-invariant'#配套不变量插件名（字面量）
注入=['invariants']#依赖 invariants 服务

__all__=['包名','名称','注入','安装','应用']#仅中文公开名

def 安装(上下文对象,失败):#空安装器
    """无运行时检查：仅浏览器侧 Settings 控制器不拥有宿主事件。"""
    return#不挂监听

def 应用(上下文对象):#注册本包不变量配套
    """注册本包的不变量配套，返回安装成功后已登记贡献的拆除器。"""
    return 已兑现(上下文对象.invariants.register(包名,安装))#登记
