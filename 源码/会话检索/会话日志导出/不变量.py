"""`@deepseek-ai/dsh-session-log-export` 的本包拥有不变量配套。对齐上游 `session-log-export/src/invariant.ts`。"""
包名='@deepseek-ai/dsh-session-log-export'#本包的不变量所有权名
名称='session-export-invariant'#配套不变量插件名（字面量）
注入=['invariants']#依赖 invariants 服务

__all__=['包名','名称','注入','安装','应用']#仅中文公开名

def 安装(_上下文对象,_失败):
    """无运行时不变量：命令注册表拥有生命周期配对，ApiProxy 拥有 ZIP 完整性。"""
    return#空安装

def 应用(上下文对象):
    """注册本包的不变量配套，返回安装成功后已登记贡献的拆除器。"""
    return 上下文对象.invariants.register(包名,安装)#登记

应用.name=名称#Cordis name 槽
应用.inject=注入#Cordis inject 槽
default=应用#Cordis 默认导出槽
