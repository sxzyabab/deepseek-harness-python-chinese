"""`@deepseek-ai/dsh-sdk-jsonrpc-demo` 的本包拥有不变量配套。

对齐上游 `示例/jsonrpc-demo/src/invariant.ts`。公开面仅中文名。
无运行时不变量：本组合包不拥有独立事件流或可变数据；Loader 与已构建入口测试覆盖其接线。
"""
from cordis.工具 import 已兑现#立刻兑现的拆除器

包名='@deepseek-ai/dsh-sdk-jsonrpc-demo'#本包的不变量所有权名
名称='sdk-jsonrpc-demo-invariant'#配套不变量插件名（字面量）
注入=['invariants']#依赖 invariants 服务

__all__=['包名','名称','注入','安装','应用']#仅中文公开名

def 安装(_上下文对象,_失败):#空安装器
    """无运行时不变量：不挂运行时检查。"""
    return#空安装

def 应用(上下文对象):#注册本包不变量配套
    """注册本包的不变量配套，返回安装成功后已登记贡献的拆除器。"""
    return 已兑现(上下文对象.invariants.register(包名,安装))#登记并包成立即兑现的承诺
