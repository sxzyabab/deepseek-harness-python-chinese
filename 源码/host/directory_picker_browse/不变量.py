"""browse 目录选择后端的本包拥有不变量配套。

对齐上游 `directory-picker-browse/src/invariant.ts`。公开面仅中文名。
无运行时不变量：每次 list/create 都是一次无状态文件系统往返。
"""
from cordis.工具 import 已兑现#立刻兑现

包名='@deepseek-ai/dsh-host-directory-picker-browse'#本包所有权名
名称='host-directory-picker-browse-invariant'#配套插件名
注入=['invariants']#依赖 invariants

__all__=['包名','名称','注入','安装','应用']#仅中文公开名

def 安装(上下文对象,失败):#空安装器
    """无运行时检查：权威状态在文件系统本身。"""
    return#不挂

def 应用(上下文对象):#注册不变量配套
    """注册本包不变量配套。"""
    return 已兑现(上下文对象.invariants.register(包名,安装))#登记
