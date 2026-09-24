"""消费沙箱的 bash 执行器。经 ctx.sandbox 包装本地 bash argv，并报告模式、强制与拒绝事实。"""
from ...沙盒.沙盒 import (
    沙箱不可用错误,
    分类运行器失败,
    是否运行器派生失败,
    匹配签名,
)
from ...工具.超时 import 若已中止则抛出,已中止
from ..本地bash import 本地Bash执行器

__all__=['沙盒Bash执行器']

class 沙盒Bash执行器(本地Bash执行器):
    """登记为 ctx.shell，要求 sandbox 与 sandboxPolicy。"""
    依赖=['subprocess','sandbox','sandboxPolicy']
    inject=依赖

    def __init__(自身,上下文,配置):
        """记下部署默认模式，供工具层广告。"""
        super().__init__(上下文,配置)
        自身.模式=上下文.sandboxPolicy.defaultMode
        自身.进程事实={}

    @property
    def 沙箱模式(自身):
        """配置的默认模式。"""
        return 自身.模式

    def 解析(自身,请求):
        """盖上按次政策；工具未给则回落部署政策。"""
        规格=super().解析(请求)
        规格['sandboxPolicy']=请求['sandboxPolicy'] if 'sandboxPolicy' in 请求 and 请求['sandboxPolicy'] is not None else 自身.ctx.sandboxPolicy.解析()
        return 规格

    def 执行(自身,规格):
        """隔离后派生；全放开仍盖 sandbox 事实。"""
        政策=规格['sandboxPolicy']
        模式=政策['mode']
        if 模式=='danger-full-access':
            def 全放开(结果):
                """全放开只盖未拒绝事实。"""
                return {**结果,'sandbox':{'mode':模式,'denied':False}}
            return 自身.装饰结果(super().执行(规格),全放开)
        已隔离=[None]
        def 准备(信号):
            """包装 bash -c。"""
            备好=自身.隔离(规格['command'],{**政策,'mode':模式},信号)
            若已中止则抛出(信号)
            已隔离[0]=备好
            return 备好['argv']
        def 已启动(进程):
            """按进程记下分类事实。"""
            事实=已隔离[0]
            自身.进程事实[进程]={
                'mode':模式,
                'enforcement':事实['enforcement'],
                'denialSignatures':事实['denialSignatures'],
                'runnerFailureRules':事实['runnerFailureRules'],
                'runnerProgram':事实['argv'][0],
                'workdir':规格['workdir'],
            }
        def 映射(结果):
            """前台投影盖沙箱事实；运行器失败改抛不可用。"""
            备好=已隔离[0]
            if 备好 is None:
                return {**结果,'sandbox':{'mode':模式,'denied':False}}
            运行器失败=分类运行器失败(结果['exitCode'],结果['stderr']['text'],备好['runnerFailureRules'])
            if 运行器失败 is not None:
                raise 沙箱不可用错误(模式,运行器失败['detail'])
            return {
                **结果,
                'sandbox':{
                    'mode':模式,
                    'denied':匹配签名(结果['exitCode'],结果['stderr']['text'],备好['denialSignatures']),
                    'enforcement':备好['enforcement'],
                },
            }
        def 映射错误(错误):
            """派生失败且证据指向运行器时改抛不可用。"""
            信号=规格['signal'] if 'signal' in 规格 else None
            if 已中止(信号):
                若已中止则抛出(信号)
            备好=已隔离[0]
            if 备好 is not None and 是否运行器派生失败(错误,备好['argv'][0],规格['workdir']):
                raise 沙箱不可用错误(模式,str(错误))
            raise 错误
        return 自身.装饰结果(自身.按参数表执行(规格,准备,已启动),映射,映射错误)

    def 装饰结果(自身,句柄,映射,映射错误=None):
        """就地包装 结果，记忆一次。"""
        原结果=句柄.结果
        缓存=[None]
        def 结果():
            """映射一次前台投影。"""
            if 缓存[0] is None:
                try:
                    缓存[0]=映射(原结果())
                except Exception as 错误:
                    if 映射错误 is not None:
                        映射错误(错误)
                    raise
            return 缓存[0]
        句柄.结果=结果
        return 句柄

    def 进程已结束(自身,进程,标准误,启动失败,启动错误=None):
        """结算前盖每进程沙箱事实。"""
        事实=自身.进程事实.pop(进程,None)
        if 事实 is not None:
            if 启动失败:
                运行器失败=是否运行器派生失败(启动错误,事实['runnerProgram'],事实['workdir'])
            else:
                运行器失败=分类运行器失败(进程.exitCode,标准误,事实['runnerFailureRules']) is not None
            沙箱={
                'mode':事实['mode'],
                'denied':(not 运行器失败) and 匹配签名(进程.exitCode,标准误,事实['denialSignatures']),
                'enforcement':事实['enforcement'],
            }
            if 运行器失败:
                沙箱['runnerFailed']=True
            进程.sandbox=沙箱
        super().进程已结束(进程,标准误,启动失败,启动错误)

    def 隔离(自身,命令,政策,信号=None):
        """经 sandbox 包装 bash -c。"""
        return 自身.ctx.sandbox.隔离(['bash','-c',命令],政策,信号)

default=沙盒Bash执行器
