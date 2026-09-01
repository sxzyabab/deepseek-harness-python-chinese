"""`@deepseek-ai/dsh-session-query-sqlite` 的包内不变量配套。"""
from ...依赖 import cordis#外部依赖胶水
包名='@deepseek-ai/dsh-session-query-sqlite'#本包名
名称='session-query-sqlite-invariant'#配套插件名
注入=['invariants']#依赖不变量服务
name=名称#Cordis 插件名
inject=注入#Cordis 依赖声明

def 已兑现(值=None):#立刻兑现的操作任务
    """把值包成立即兑现的 thenable。"""
    class _任务:#同步任务
        def wait(自身,超时=None):#阻塞等待
            return 值#原样返回
        def 等待(自身,超时=None):#中文别名
            return 值#原样返回
    return _任务()#已完成

def 安装(子上下文=None,失败=None):#空安装器
    """无运行时不变量：索引一致性由重建与对账测试钉住。"""
    return None#不挂运行时检查

def 应用(上下文对象):#登记不变量配套
    return 已兑现(上下文对象.invariants.register(包名,安装))#登记安装器

apply=应用#Cordis 插件入口
