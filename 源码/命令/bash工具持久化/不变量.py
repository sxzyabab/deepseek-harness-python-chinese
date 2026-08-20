"""`@deepseek-ai/dsh-tool-bash-persistent` 的本包拥有不变量配套。

对齐上游 `tool-bash-persistent/src/invariant.ts`。公开面仅中文名。

无运行时不变量：适配器私有的所有者到 shell 缓存没有可观察事件或数据关系。生命周期测试证明其清理，而不仅为不变量增加公开 API。
"""
from cordis.工具 import 已兑现#立刻兑现的拆除器

包名='@deepseek-ai/dsh-tool-bash-persistent'#本包的不变量所有权名
名称='tool-bash-persistent-invariant'#配套不变量插件名（字面量）
注入=['invariants']#依赖 invariants 服务

__all__=['包名','名称','注入','安装','应用']#仅中文公开名

def 安装(*位置参数):#空安装器，不挂运行时检查
    """空安装器。所有者到 shell 的缓存无私有可观察关系，不另挂检查。位置参数由登记约定传入，此处忽略。"""
    return#不挂运行时检查

def 应用(上下文对象):#登记空贡献并返回拆除器
    """注册本包的不变量配套，返回安装成功后已登记贡献的拆除器。"""
    return 已兑现(上下文对象.invariants.register(包名,安装))#登记空贡献并返回拆除器
