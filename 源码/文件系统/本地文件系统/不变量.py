"""@deepseek-ai/dsh-fs-local 的本包拥有不变量配套。"""
from concurrent.futures import Future as _原生Future#单次操作结果

包名='@deepseek-ai/dsh-fs-local'#本包的不变量所有权名
名称='fs-local-invariant'#配套不变量插件名
注入=['invariants']#依赖invariants服务
name=名称#Cordis插件名
inject=注入#Cordis依赖声明

__all__=['包名','名称','注入','安装','应用']#仅中文公开名

class 操作任务:#单次异步结果
    def __init__(自身):#构造未决任务
        自身._future=_原生Future()#底层 Future
    def 兑现(自身,值=None):#成功结算
        if not 自身._future.done():#尚未结算
            自身._future.set_result(值)#写入结果
        return 值#返回兑现值
    def 拒绝(自身,错误):#失败结算
        if not 自身._future.done():#尚未结算
            if isinstance(错误,BaseException):#已是异常
                自身._future.set_exception(错误)#原样拒绝
            else:#非异常
                自身._future.set_exception(Exception(错误))#包装拒绝
    def wait(自身,超时=None):#阻塞等待
        return 自身._future.result(timeout=超时)#取结果或抛错
    def 等待(自身,超时=None):#兼容外来调用
        return 自身.wait(超时)#转发

def 安装(子上下文=None,失败=None):#空安装器，不挂运行时检查
    """无运行时不变量：本包不暴露独立事件序列或可变数据关系，超出其拥有 seam 已强制的约定。"""
    return None#空配套

def 应用(上下文对象):#注册本包不变量配套
    """注册本包的不变量配套，返回安装成功后已登记贡献的拆除器。"""
    拆除器=上下文对象.invariants.register(包名,安装)#登记本包空安装器
    任务=操作任务()#对齐上游 Promise.resolve
    任务.兑现(拆除器)#已决议拆除器
    return 任务#返回可等待结果

apply=应用#Cordis插件入口
