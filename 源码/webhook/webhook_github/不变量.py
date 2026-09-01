"""`@deepseek-ai/dsh-webhook-github` 的本包拥有不变量配套。对齐上游 `webhook-github/src/invariant.ts`。"""
from ...依赖 import cordis#外部依赖胶水
包名='@deepseek-ai/dsh-webhook-github'#本包的不变量所有权名
名称='webhook-github-invariant'#配套不变量插件名（字面量）
注入=['invariants']#依赖 invariants 服务

__all__=['包名','名称','注入','安装','应用']#仅中文公开名

def 已兑现(值=None):#立刻兑现的操作任务
    """把值包成立即兑现的 thenable。"""
    class _任务:#同步任务
        def wait(自身,超时=None):#阻塞等待
            return 值#原样返回
        def 等待(自身,超时=None):#中文别名
            return 值#原样返回
    return _任务()#已完成

def 安装(_上下文对象,_失败):#空安装器
    """无运行时不变量：认证与输入校验在精确 HTTP 操作边界完成。"""
    return#空安装

def 应用(上下文对象):#注册本包不变量配套
    """注册本包的不变量配套，返回安装成功后已登记贡献的拆除器。"""
    return 已兑现(上下文对象.invariants.register(包名,安装))#登记并包成立即兑现的承诺

apply=应用#Cordis插件入口
