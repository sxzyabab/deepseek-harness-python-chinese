from ...依赖.schemastery import 自然数字段
from ...typert.协议 import 远程服务,远程 as _远程
from .观察 import 观察作业输出
from .表行列表 import 流出作业表行
from .类型 import 远程错误

__all__=['包名','名称','依赖','默认','配置','后台任务控制器']

包名='@deepseek-ai/dsh-api-job-controller'
名称='job-controller'
依赖=['jobs','typert']

观察冲洗缺省毫秒=100
观察最大帧缺省字节=64*1024

配置={
    'observeFlushMs':自然数字段(最小=1,默认值=观察冲洗缺省毫秒),
    'observeMaxFrameBytes':自然数字段(最小=1,默认值=观察最大帧缺省字节),
}

def _流方法(方法):
    """标为流式 Remote。"""
    方法._typert_remote_marker={'invocation':{'kind':'direct','mode':'stream'}}
    return 方法

class 后台任务控制器(远程服务):
    """宿主作业 Remote 拥有者。"""
    def __init__(自身,上下文,配置值=None):
        """登记 job 命名空间。"""
        super().__init__(上下文,'jobController',{'namespace':'job'})
        if 配置值 is None:
            配置值={}
        自身._冲洗毫秒=配置值['observeFlushMs'] if 'observeFlushMs' in 配置值 else 观察冲洗缺省毫秒
        自身._最大帧字节=配置值['observeMaxFrameBytes'] if 'observeMaxFrameBytes' in 配置值 else 观察最大帧缺省字节

    @_流方法
    def list(自身,请求,信号):
        """流式给出本会话可见作业整表。"""
        yield from 流出作业表行(自身.ctx.jobs,请求,{'flushMs':自身._冲洗毫秒},信号)

    @_流方法
    def follow(自身,请求,信号):
        """从绝对偏移跟随保留输出。"""
        yield from 观察作业输出(自身.ctx.jobs,请求,{'flushMs':自身._冲洗毫秒,'maxFrameBytes':自身._最大帧字节},信号)

    @_远程('kill')
    def kill(自身,请求):
        """人类终止可见作业。"""
        作业表=自身.ctx.jobs
        try:
            作业表.get(请求['jobId'],请求['sessionId'])
        except Exception as 错误:
            raise 远程错误('job/not-found',str(错误),{'sessionId':请求['sessionId'],'jobId':请求['jobId']},原因=错误)
        结局=作业表.kill(请求['jobId'],请求['sessionId'],'cancelled by the user')
        return {'outcome':结局}

默认=后台任务控制器
Config=配置
name=名称
inject=依赖
default=默认
后台任务控制器.inject=依赖
后台任务控制器.Config=配置
