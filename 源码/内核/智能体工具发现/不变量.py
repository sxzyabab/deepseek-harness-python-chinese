"""`@deepseek-ai/dsh-agent-tool-presentation` 的包内不变量配套。

对齐上游 `agent-tool-presentation/src/invariant.ts`。公开面仅中文名；Cordis 加载槽 `name`/`inject`/`apply` 为协议兼容别名，不入 `__all__`。

无运行时不变量：本包只对 `ctx.tools` 做一次作用域调用，自身不拥有事件或快照；它建立的关系——某个 Agent 组装使用哪种展示——由工具注册表持有，并由 `dsh-tools` 在那里观察。
"""
from cordis.工具 import 已兑现#导入立刻兑现的拆除器

包名='@deepseek-ai/dsh-agent-tool-presentation'#本包名（登记到 invariants 的所有权键）
名称='tool-presentation-invariant'#配套插件名（字面量对齐上游）
注入=['invariants']#配套预占包所有权前必须具备的服务
name=名称#Cordis 插件名槽
inject=注入#Cordis 依赖声明槽

__all__=('包名','名称','注入','安装','应用')#仅中文公开名

def 安装(*位置参数):#空安装器，不挂运行时检查
    """空安装器。展示关系由工具注册表持有，本包不另挂检查。位置参数由登记约定传入，此处忽略。"""
    return#不挂运行时检查

def 应用(上下文对象):#登记空贡献并返回拆除器
    """注册本包的不变量配套，返回安装成功后已登记贡献的拆除器。"""
    return 已兑现(上下文对象.invariants.register(包名,安装))#登记空贡献并返回拆除器

apply=应用#Cordis 插件入口槽
