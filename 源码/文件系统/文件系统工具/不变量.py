"""`@deepseek-ai/dsh-tool-fs` 的本包拥有不变量配套。对齐上游 `tool-fs/src/invariant.ts`。公开面仅中文名；Cordis 协议槽保留英文别名，不入 `__all__`。"""
from ...依赖 import cordis#外部依赖胶水
已兑现=cordis.工具.已兑现#立刻兑现的拆除器

包名='@deepseek-ai/dsh-tool-fs'#本包的不变量所有权名
名称='tool-fs-invariant'#配套不变量插件名
注入=['invariants']#依赖invariants服务
name=名称#Cordis插件名（协议槽）
inject=注入#Cordis依赖声明（协议槽）

__all__=['包名','名称','注入','安装','应用']#仅中文公开名

def 安装(子上下文=None,失败=None):#空安装器，不挂运行时检查
    """无运行时不变量：此面向模型的适配器没有独立生命周期流；执行关系由其调用的能力 seam 拥有。"""
    return None#不挂运行时检查；子上下文与失败由登记约定传入

def 应用(上下文对象):#注册本包不变量配套
    """注册本包的不变量配套，返回安装成功后已登记贡献的拆除器。"""
    return 已兑现(上下文对象.invariants.register(包名,安装))#登记并包成立即兑现的承诺

apply=应用#Cordis插件入口（协议槽）
