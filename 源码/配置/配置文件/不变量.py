"""`@deepseek-ai/dsh-settings-file` 的本包拥有不变量配套。"""
from ...依赖 import cordis#外部依赖胶水
已兑现=cordis.工具.已兑现#立刻兑现的拆除器

包名='@deepseek-ai/dsh-settings-file'#本包的不变量所有权名
名称='settings-file-invariant'#配套不变量插件名
注入=['invariants']#依赖invariants服务
name=名称#Cordis插件名
inject=注入#Cordis依赖声明

def 安装(子上下文=None,失败=None):#空安装器
    """无运行时不变量：本提供方的约定是文件往返、监视时机与原子写入行为——由包测试证明的IO效果；进程内提交关系由`@deepseek-ai/dsh-settings`拥有。"""
    return None#不挂运行时检查

def 应用(上下文对象):#对外导出配套入口
    """注册本包的不变量配套，返回安装成功后已登记贡献的拆除器。"""
    return 已兑现(上下文对象.invariants.register(包名,安装))#向不变量服务登记安装器

apply=应用#Cordis插件入口
