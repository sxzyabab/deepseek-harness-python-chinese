"""bash 能力 seam 的本包拥有不变量配套。对齐上游 `shell/src/invariant.ts`。公开面仅中文名。

无运行时不变量：本无状态 Service Definition 拥有请求/结果类型，执行器与策略拥有观察。
"""
from cordis.工具 import 已兑现#导入立刻兑现的拆除器

包名='@deepseek-ai/dsh-shell'#本包的不变量所有权名
名称='shell-invariant'#配套不变量插件名
注入=['invariants']#依赖 invariants 服务
name=名称#Cordis插件名（协议槽）
inject=注入#Cordis依赖声明（协议槽）

__all__=['包名','名称','注入','安装','应用']#仅中文公开名

def 安装(*位置参数):#空安装器，不挂运行时检查
    """空安装器，不挂运行时检查。"""
    return#不挂运行时检查

def 应用(上下文对象):#应用不变量配套插件
    """注册 bash 不变量配套，返回安装成功后已登记贡献的拆除器。"""
    return 已兑现(上下文对象.invariants.register(包名,安装))#登记空贡献并返回拆除器

apply=应用#Cordis插件入口（协议槽）
