"""消费沙箱的 PowerShell 执行器——bash_sandbox 的 pwsh 孪生。

对齐上游 `pwsh-sandbox/src/index.ts`。公开面仅中文名；无英文别名。
它把本地 pwsh 的精确 argv 包进 ctx.sandbox（Windows 上解析为 ACL 受限令牌启动器链），沿用本地进程机制，并报告所选模式、强制执行与拒绝事实。正向的启动器拉起证据表示命令从未运行：前台调用抛出 SANDBOX_UNAVAILABLE，后台进程带 runnerFailed；其他 spawn 拒绝仍保留本地执行器语义。工具层经 ctx.approval 负责升级审批流；本执行器报告工具要渲染的沙箱事实。
"""
from ..本地powershell import 本地PowerShell执行器#本地PowerShell执行器
from ..沙盒 import 沙箱不可用错误#沙箱不可用错误
from .辅助 import (
    分类拒绝,#拒绝分类
    分类启动器失败,#启动器失败分类
    是否启动器拉起失败,#spawn失败判定
    匹配特征,#特征匹配
)#导入分类辅助

__all__=('沙箱PowerShell执行器','默认')#仅中文公开名；无英文别名

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段，缺席为缺省。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 抛若已中止(信号):#规格信号已中止则抛出
    """规格上的中止信号若已触发则按取消抛出；兼容英文与中文信号面。"""
    if 信号 is None:#没有信号
        return#无事可做
    if 取字段(信号,'aborted') is not True and 取字段(信号,'已中止') is not True:#尚未中止
        return#继续
    抛出=getattr(信号,'throwIfAborted',None)#英文取消抛出
    if 抛出 is None:#没有英文API
        抛出=getattr(信号,'抛若中止',None)#中文取消抛出
    if 抛出 is not None:#有可调用的抛出面
        抛出()#按取消抛出

class 沙箱PowerShell执行器(本地PowerShell执行器):#沙箱PowerShell执行器，继承本地执行器
    """代替本地 pwsh 执行器注册为 ctx.shell，并要求存在 ctx.sandbox 提供方和 ctx.sandboxPolicy；工具层带着沙箱拒绝渲染和升级面。工具调用传入调用会话已解析的策略；直接调用回退到部署策略。result.sandbox 报告工具要渲染的模式、强制执行与拒绝事实。

    公开方法仅中文：解析、运行、启动、进程已结束、隔离。
    """
    注入=['subprocess','sandbox','sandboxPolicy']#构造前须具备子进程、沙箱与沙箱策略
    def __init__(自身,上下文对象,配置):#用上下文和配置构造执行器
        """用上下文和配置构造执行器。插件配置原样沿用本地执行器的旋钮。沙箱策略——默认模式和回退的 workspace-write 根——不在这里：它住在 ctx.sandboxPolicy，由该服务为每次强制能力解析调用会话的模式和 cwd。启动器选择同样是 ctx.sandbox 提供方的配置，不是本执行器的配置。默认模式是用于模式广告的能力事实；实际工具执行携带每次调用已解析的策略。"""
        super().__init__(上下文对象,配置)#交给本地PowerShell执行器初始化
        自身.模式=自身.ctx.sandboxPolicy.defaultMode#记下沙箱策略的默认模式
        自身.进程事实={}#按进程身份记住隔离事实；提供方可能在重叠调用之间改变强制方式和诊断方言，若共用一个最新包装值，会按错误事实给进程分类。未隔离的进程没有条目。键用 id(进程)，因本地句柄是字典不可哈希

    @property#只读属性
    def 沙箱模式(自身):#读取默认沙箱模式
        """配置的默认模式——工具层读取的能力事实。"""
        return 自身.模式#返回记下的默认模式

    def 解析(自身,请求):#把请求解析成带沙箱策略的规格
        """把完整的每次调用策略盖到规格上。工具调用提供调用会话已解析的模式和根；更底层的调用方回退到部署策略。"""
        规格=dict(super().解析(请求))#先走本地解析
        策略=取字段(请求,'sandboxPolicy')#请求上的策略
        if 策略 is None:#缺省则用部署策略
            策略=自身.ctx.sandboxPolicy.resolve()#部署策略
        规格['sandboxPolicy']=策略#盖上请求或部署策略
        return 规格#带沙箱策略的规格

    def 运行(自身,规格):#前台跑一条带沙箱策略的命令
        """前台跑一条带沙箱策略的命令。"""
        政策=取字段(规格,'sandboxPolicy')#取出本次调用的沙箱执行策略
        模式=取字段(政策,'mode')#取出本次策略的沙箱模式
        if 模式=='danger-full-access':#全权限则不隔离
            结果=super().运行(规格)#走本地执行器前台运行
            报告=dict(结果)#拷贝运行结果
            报告['sandbox']={'mode':模式,'denied':False}#报告全权限且未拒绝
            return 报告#全权限结果
        隔离政策=dict(政策)#拷贝本次政策
        隔离政策['mode']=模式#钉死已收窄的模式
        隔离=自身.隔离(规格,隔离政策)#把本次pwsh调用包进沙箱argv
        try:#按隔离argv执行
            结果=自身.按参数表运行(规格,取字段(隔离,'argv'))#用隔离后的argv跑前台命令
        except BaseException as 错误:#捕获执行错误
            抛若已中止(取字段(规格,'signal'))#上游中止即使挡住了spawn仍算取消
            if 是否启动器拉起失败(错误,取字段(隔离,'argv')[0],取字段(规格,'workdir')):#启动器spawn失败
                raise 沙箱不可用错误(模式,str(错误))#命令没跑，报沙箱不可用
            raise#其他错误按本地执行器语义原样抛出
        启动器失败=分类启动器失败(取字段(结果,'exitCode'),取字段(取字段(结果,'stderr'),'text'),取字段(隔离,'runnerFailureRules'))#按规则判定启动器失败
        if 启动器失败 is not None:#确有启动器失败
            raise 沙箱不可用错误(模式,取字段(启动器失败,'detail'))#用匹配到的细节报沙箱不可用
        报告=dict(结果)#拷贝运行结果
        报告['sandbox']={'mode':模式,'denied':分类拒绝(结果,取字段(隔离,'denialSignatures')),'enforcement':取字段(隔离,'enforcement')}#报告模式、是否拒绝与强制方式
        return 报告#带沙箱事实的结果

    def 启动(自身,规格):#后台拉起一条带沙箱策略的命令
        """后台拉起一条带沙箱策略的命令。"""
        政策=取字段(规格,'sandboxPolicy')#取出本次调用的沙箱执行策略
        模式=取字段(政策,'mode')#取出本次策略的沙箱模式
        if 模式=='danger-full-access':#全权限则不隔离
            return super().启动(规格)#走本地启动
        隔离政策=dict(政策)#拷贝本次政策
        隔离政策['mode']=模式#钉死已收窄的模式
        隔离=自身.隔离(规格,隔离政策)#把本次pwsh调用包进沙箱argv
        try:#按隔离argv拉起
            进程=自身.按参数表启动(规格,取字段(隔离,'argv'))#用隔离后的argv后台启动
        except BaseException as 错误:#捕获同步启动错误
            if 是否启动器拉起失败(错误,取字段(隔离,'argv')[0],取字段(规格,'workdir')):#启动器spawn失败
                raise 沙箱不可用错误(模式,str(错误))#命令没跑，报沙箱不可用
            raise#其他错误按本地执行器语义原样抛出
        自身.进程事实[id(进程)]={
            'mode':模式,#受限模式
            'enforcement':取字段(隔离,'enforcement'),#强制执行方式
            'denialSignatures':取字段(隔离,'denialSignatures'),#拒绝特征串
            'runnerFailureRules':取字段(隔离,'runnerFailureRules'),#启动器失败规则
            'runnerProgram':取字段(隔离,'argv')[0],#启动器程序是隔离argv的第0项
            'workdir':取字段(规格,'workdir'),#工作目录
        }#按进程记下本次隔离事实；startArgv返回后同步装上事实，promise结算不可能早于start返回
        return 进程#返回已记下事实的后台进程

    def 进程已结束(自身,进程,标准误,启动失败,启动错误=None):#进程结束时盖沙箱事实
        """在 done 结算前盖上该进程的沙箱事实。全权限进程没有事实；信号致死不算拒绝。"""
        编号=id(进程)#进程身份
        if 编号 in 自身.进程事实:#有隔离事实才处理
            事实=自身.进程事实.pop(编号)#事实只用一次，用完删除
            if 启动失败:#spawn失败则看是不是启动器失败
                启动器失败=是否启动器拉起失败(启动错误,取字段(事实,'runnerProgram'),取字段(事实,'workdir'))#被拒绝的spawn从未开始受限启动
            else:#否则按规则看标准误是否像启动器失败
                启动器失败=分类启动器失败(取字段(进程,'exitCode'),标准误,取字段(事实,'runnerFailureRules')) is not None#启动器失败优先于拒绝，因为它的诊断里可能含拒绝用语
            沙箱={
                'mode':取字段(事实,'mode'),#报告受限模式
                'denied':(not 启动器失败) and 匹配特征(取字段(进程,'exitCode'),标准误,取字段(事实,'denialSignatures')),#启动器没失败且输出命中拒绝特征才算拒绝
                'enforcement':取字段(事实,'enforcement'),#报告强制执行方式
            }#进程沙箱字段
            if 启动器失败:#启动器失败时带上runnerFailed
                沙箱['runnerFailed']=True#启动器失败
            if isinstance(进程,dict):#映射句柄
                进程['sandbox']=沙箱#写回进程
            else:#对象句柄
                进程.sandbox=沙箱#写回进程
        super().进程已结束(进程,标准误,启动失败,启动错误)#再交给本地执行器做收尾

    def 隔离(自身,规格,政策):#把一次pwsh调用交给沙箱包装
        """经 ctx.sandbox 提供方包装一次 pwsh 调用。提供方错误原样传播；返回的 argv 直接交给本地执行器的子进程路径。"""
        return 自身.ctx.sandbox.confine(自身.参数表(规格),政策)#用本地拼出的pwsh argv包进沙箱

默认=沙箱PowerShell执行器#默认导出该执行器类（中文名；无英文 default 别名）
