"""`@deepseek-ai/dsh-client-ui-workspace` 的本包拥有不变量配套。

对齐上游 `ui-workspace/src/invariant.ts`。公开面仅中文名。

无运行时不变量：纯消费方插件，把展示组件注册进两个宿主声明的槽位，外加其 locale 字典——注入面是无状态 RPC 包装加上一次创建并打开调用；不发射 cordis 事件，也不拥有跨插件可变状态。
"""
from cordis.工具 import 已兑现#立刻兑现的拆除器

包名='@deepseek-ai/dsh-client-ui-workspace'#本包的不变量所有权名
名称='client-ui-workspace-invariant'#配套不变量插件名（字面量）
注入=['invariants']#依赖 invariants 服务

__all__=['包名','名称','注入','安装','应用']#仅中文公开名

def 安装(上下文对象=None,失败=None):#空安装器
    """无运行时检查：槽位注册与 locale 字典由各自账本观察。"""
    return#不挂监听

def 应用(上下文对象):#注册本包不变量配套
    """注册本包的不变量配套，返回安装成功后已登记贡献的拆除器。"""
    return 已兑现(上下文对象.invariants.register(包名,安装))#登记并包成立即兑现的承诺
