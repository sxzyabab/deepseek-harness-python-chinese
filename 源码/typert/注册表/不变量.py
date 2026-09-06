"""`@deepseek-ai/dsh-typert-registry` 的本包拥有不变量配套。

对齐上游 `registry/src/invariant.ts`。公开面仅中文名。

无运行时不变量：模式与包反射记录在登记与拆除内一起变更，没有可交叉核对的独立事件或第二数据源；重复身份在拥有该操作的边界失败。
"""
包名='@deepseek-ai/dsh-typert-registry'#本包的不变量所有权名
名称='typert-registry-invariant'#配套不变量插件名（字面量）
注入=['invariants']#依赖 invariants 服务

def 安装(上下文对象,失败):
    """无运行时检查：注册与拆除同边界变更，无第二数据源。"""
    return#空安装

def 应用(上下文对象):
    """注册本包的不变量配套，返回安装成功后已登记贡献的拆除器。"""
    return 上下文对象.invariants.register(包名,安装)#登记

__all__=['包名','名称','注入','安装','应用']#仅中文公开名
name=名称#Cordis 插件名
inject=注入#Cordis 依赖声明
apply=应用#Cordis 插件入口
default=应用#Cordis 默认导出
