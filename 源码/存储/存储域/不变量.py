"""`@deepseek-ai/dsh-storage-domain` 的本包拥有不变量配套。"""
from concurrent.futures import Future as _原生Future#单次操作结果
from ...依赖 import cordis#外部依赖胶水

class _操作任务:#单次异步结果
    def __init__(自身):#构造未决任务
        自身._future=_原生Future()#底层 Future
    def 兑现(自身,值=None):#成功结算
        if not 自身._future.done():#尚未结算
            自身._future.set_result(值)#写入结果
        return 值#返回兑现值
    def wait(自身,超时=None):#阻塞等待
        return 自身._future.result(timeout=超时)#取结果或抛错
    def 等待(自身,超时=None):#兼容外来调用
        return 自身.wait(超时)#转发

def 已兑现(值=None):#立刻兑现的操作任务
    任务=_操作任务()#新任务
    任务.兑现(值)#立刻成功
    return 任务#已完成

包名='@deepseek-ai/dsh-storage-domain'#本包的不变量所有权名
名称='storage-domain-invariant'#配套不变量插件名
注入=['invariants']#依赖 invariants 服务
name=名称#Cordis 插件名
inject=注入#Cordis 依赖声明

def 安装(上下文对象,失败):#安装变更事件与内存状态一致检查
    """每条 `domain/changed` 必须与发出该事件的域的权威内存状态一致。"""
    def 监听变更(变更):#监听域变更
        域=上下文对象.storage.form('domain').get(变更['domain'])#按名取已打开的域
        if 域 is None:#域未打开
            失败(f"domain/changed for '{变更['domain']}' emitted while that domain is not open")#未打开却发出则失败
        if 变更['table']=='':#全局写入
            if getattr(域,'global').get()!=变更['value']:#快照与内存全局值不同；global 是关键字只能 getattr
                失败(f"domain/changed global value for '{变更['domain']}' differs from the in-memory global")#全局值分叉
            return#全局路径结束
        当前=域.table(变更['table']).get(变更['key'])#取表中该键的当前记录
        if 变更['operation']=='deleted':#删除
            if 当前 is not None:#内存里记录仍在
                失败(f"domain/changed deletion of '{变更['domain']}'.'{变更['table']}'['{变更['key']}'] emitted while the record is still in memory")#删除事件与内存冲突
            return#删除路径结束
        if 变更['operation']=='put' and 当前!=变更['value']:#载荷与内存记录不同
            失败(f"domain/changed value for '{变更['domain']}'.'{变更['table']}'['{变更['key']}'] differs from the in-memory record")#put 值分叉
    上下文对象.on('domain/changed',监听变更,{'global':True})#全局监听

安装.inject=['storage']#安装前需要 storage 服务

def 应用(上下文对象):#注册本包不变量配套
    """注册本包的不变量配套，返回安装成功后已登记贡献的拆除器。"""
    return 已兑现(上下文对象.invariants.register(包名,安装))#登记并包成立即兑现的承诺

apply=应用#Cordis 插件入口
