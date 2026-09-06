"""`@deepseek-ai/dsh-persona` 的本包拥有不变量配套。

对齐上游 `persona/src/invariant.ts`。公开面仅中文名。

无运行时不变量：本行不拥有事件流或可变运行时数据——它只注册一个提示词段落，
身份、完整提示词强制、遮蔽与拆除都由提示词注册表拥有。
"""
包名='@deepseek-ai/dsh-persona'#本包的不变量所有权名
名称='persona-invariant'#配套不变量插件名（字面量）
注入=['invariants']#依赖 invariants 服务

def 安装(上下文对象,失败):
    """空安装器，不挂运行时检查。"""
    return#无检查

def 应用(上下文对象):
    """注册本包的不变量配套，返回安装成功后已登记贡献的拆除器。"""
    return 上下文对象.invariants.register(包名,安装)#登记

__all__=['包名','名称','注入','安装','应用']#仅中文公开名
name=名称#Cordis 插件名
inject=注入#Cordis 依赖声明
apply=应用#Cordis 插件入口
default=应用#Cordis 默认导出
