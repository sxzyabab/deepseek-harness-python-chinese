"""`@deepseek-ai/dsh-llm-pi-ai` 的本包拥有不变量配套。

对齐上游 `llm-pi-ai/src/invariant.ts`。公开面仅中文名；无英文别名。

无运行时不变量：适配器注册与配置校验拥有可变值关系；本包不暴露独立事件序列。
"""
包名='@deepseek-ai/dsh-llm-pi-ai'#本包的不变量所有权名
名称='llm-pi-ai-invariant'#配套不变量插件名
注入=['invariants']#依赖 invariants 服务

__all__=['包名','名称','注入','安装','应用']#仅中文公开名

def 安装(上下文对象,失败):#空安装器
    """无运行时不变量：适配器注册与配置校验拥有可变值关系。"""
    return#不挂运行时检查

def 应用(上下文对象):#注册本包不变量配套
    """注册本包的不变量配套，返回拆除器。"""
    return 上下文对象.invariants.注册(包名,安装)#同步登记

name=名称#框架槽
inject=注入#框架槽
apply=应用#框架槽
