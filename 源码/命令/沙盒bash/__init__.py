"""消费沙箱的 bash 执行器。

对齐上游 `@deepseek-ai/dsh-bash-sandbox`（`index.ts`）。公开面仅中文名；Cordis 槽 `inject`/`default` 为协议兼容，不入 `__all__`。

把本地 bash 的精确 argv 包进 `ctx.sandbox`，沿用本地进程机制，并报告所选模式、强制执行与拒绝事实。正向的启动器拉起证据表示命令从未运行：前台调用抛出 `SANDBOX_UNAVAILABLE`，后台进程带 `runnerFailed`；其他 spawn 拒绝仍保留本地执行器语义。工具层负责审批，并传入完整的每次调用策略。
"""
from bash_local import 本地Bash执行器#本地 bash 执行器基类
from sandbox import 沙箱不可用错误#沙箱不可用错误
from .辅助 import (
    分类拒绝,#拒绝分类
    分类启动器失败,#启动器失败分类
    是否启动器拉起失败,#spawn 失败判定
    匹配特征,#特征匹配
)#导入分类辅助

__all__=['沙箱Bash执行器','默认']#仅中文公开名

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段，缺席为缺省。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

class 沙箱Bash执行器(本地Bash执行器):#沙箱 bash 执行器，继承本地执行器
    """代替本地执行器注册为 ctx.shell，并要求存在 ctx.sandbox 提供方和 ctx.sandboxPolicy；工具层不变。

    工具调用传入调用会话已解析的策略；直接调用回退到部署策略。result.sandbox 报告实际使用的模式和强制执行。
    插件配置原样沿用本地执行器的旋钮（继承 Config）。沙箱策略住在 ctx.sandboxPolicy。
    """
    inject=['subprocess','sandbox','sandboxPolicy']#Cordis 注入（协议槽）

    def __init__(自身,上下文对象,配置):#用上下文和配置构造执行器
        """用上下文和配置构造执行器。默认模式是用于模式广告的能力事实；实际工具执行携带每次调用已解析的策略。"""
        super().__init__(上下文对象,配置)#交给本地 bash 执行器初始化
        政策服务=上下文对象.sandboxPolicy#沙箱策略服务
        自身.模式=取字段(政策服务,'默认模式')#优先中文能力事实
        if 自身.模式 is None:#旧槽
            自身.模式=政策服务.defaultMode#英文协议槽回退
        #进程结算前保留的每次隔离事实。提供方可能在重叠调用之间改变强制方式和诊断方言；
        #若共用一个最新包装值，会按错误事实给进程分类。未隔离的进程没有条目。键用 id(进程)，因后台句柄是 dict。
        自身.进程事实={}#id(进程) → 隔离事实

    @property#只读属性
    def 沙箱模式(自身):#读取默认沙箱模式
        """配置的默认模式——工具层读取的能力事实。"""
        return 自身.模式#返回记下的默认模式

    def 解析(自身,请求):#把请求解析成带沙箱策略的规格
        """把完整的每次调用策略盖到规格上。工具调用提供调用会话已解析的模式和根；更底层的调用方回退到部署策略。"""
        规格=dict(super().解析(请求))#先走本地解析
        策略=取字段(请求,'sandboxPolicy')#请求上的策略
        if 策略 is None:#请求没带
            策略=自身.ctx.sandboxPolicy.resolve()#部署策略
        规格['sandboxPolicy']=策略#盖上
        return 规格#带沙箱策略的规格

    def 运行(自身,规格):#前台跑一条带沙箱策略的命令
        """前台跑一条带沙箱策略的命令。"""
        政策=取字段(规格,'sandboxPolicy')#取出本次调用的沙箱执行策略
        模式=取字段(政策,'mode')#取出本次策略的沙箱模式
        if 模式=='danger-full-access':#全权限则不隔离
            结果=super().运行(规格)#走本地执行器前台运行
            收成=dict(结果)#复制结果
            收成['sandbox']={'mode':模式,'denied':False}#报告全权限且未拒绝
            return 收成#带沙箱事实的结果
        隔离=自身.隔离(取字段(规格,'command'),政策)#把命令包进沙箱 argv
        try:#按隔离 argv 执行
            结果=自身.按参数表运行(规格,取字段(隔离,'argv'))#用隔离后的 argv 跑前台命令
        except BaseException as 错误:#捕获执行错误
            信号=取字段(规格,'signal')#规格上的中止信号
            #上游中止即使挡住了 spawn 仍算取消
            if 取字段(信号,'已中止') is True or 取字段(信号,'aborted') is True:#已中止则按取消抛出
                抛出=getattr(信号,'抛若中止',None)#中文取消抛出
                if 抛出 is None:#没有中文 API
                    抛出=getattr(信号,'throwIfAborted',None)#英文取消抛出
                if 抛出 is not None:#有抛出方法
                    抛出()#按取消抛出
            if 是否启动器拉起失败(错误,取字段(隔离,'argv')[0],取字段(规格,'workdir')):#启动器 spawn 失败
                raise 沙箱不可用错误(模式,str(错误))#命令没跑，报沙箱不可用
            raise#其他错误按本地执行器语义原样抛出
        #启动器失败优先于拒绝，因为命令根本没跑。带上匹配到的致命行，不要带它前面的信息行
        启动器失败=分类启动器失败(取字段(结果,'exitCode'),取字段(取字段(结果,'stderr'),'text'),取字段(隔离,'runnerFailureRules'))#按规则判定启动器失败
        if 启动器失败 is not None:#确有启动器失败
            raise 沙箱不可用错误(模式,取字段(启动器失败,'detail'))#用匹配到的细节报沙箱不可用
        收成=dict(结果)#复制结果
        收成['sandbox']={
            'mode':模式,#报告模式
            'denied':分类拒绝(结果,取字段(隔离,'denialSignatures')),#是否政策拒绝
            'enforcement':取字段(隔离,'enforcement'),#强制执行完整性
        }#沙箱事实
        return 收成#带沙箱事实的结果

    def 启动(自身,规格):#后台拉起一条带沙箱策略的命令
        """后台拉起一条带沙箱策略的命令。"""
        政策=取字段(规格,'sandboxPolicy')#取出本次调用的沙箱执行策略
        模式=取字段(政策,'mode')#取出本次策略的沙箱模式
        if 模式=='danger-full-access':#全权限则不隔离
            return super().启动(规格)#走本地 start
        隔离=自身.隔离(取字段(规格,'command'),政策)#把命令包进沙箱 argv
        try:#按隔离 argv 拉起
            进程=自身.按参数表启动(规格,取字段(隔离,'argv'))#用隔离后的 argv 后台启动
        except BaseException as 错误:#捕获同步启动错误
            #LocalSubprocessRuntime 通过异步 done 拒绝；这里覆盖同步抛出同一错误的替代实现
            if 是否启动器拉起失败(错误,取字段(隔离,'argv')[0],取字段(规格,'workdir')):#启动器 spawn 失败
                raise 沙箱不可用错误(模式,str(错误))#命令没跑，报沙箱不可用
            raise#其他错误按本地执行器语义原样抛出
        #startArgv 返回后同步装上事实；done 结算不可能早于 start() 返回
        自身.进程事实[id(进程)]={
            'mode':模式,#受限模式
            'enforcement':取字段(隔离,'enforcement'),#强制执行方式
            'denialSignatures':取字段(隔离,'denialSignatures'),#拒绝特征串
            'runnerFailureRules':取字段(隔离,'runnerFailureRules'),#启动器失败规则
            'runnerProgram':取字段(隔离,'argv')[0],#启动器程序是隔离 argv 的第 0 项
            'workdir':取字段(规格,'workdir'),#工作目录
        }#按进程记下本次隔离事实
        return 进程#返回已记下事实的后台进程

    def 进程已结束(自身,进程,标准误,启动失败,启动错误=None):#进程结束时盖沙箱事实
        """在 done 结算前盖上该进程的沙箱事实。全权限进程没有事实；信号致死不算拒绝。"""
        编号=id(进程)#进程身份
        if 编号 in 自身.进程事实:#有隔离事实才处理
            事实=自身.进程事实.pop(编号)#事实只用一次，用完删除
            #被拒绝的 spawn 从未开始受限启动。否则启动器失败优先于拒绝，因为它的诊断里可能含拒绝用语
            if 启动失败:#spawn 阶段就失败了
                启动器失败=是否启动器拉起失败(启动错误,事实['runnerProgram'],事实['workdir'])#看是不是启动器失败
            else:#进程已拉起
                启动器失败=分类启动器失败(取字段(进程,'exitCode'),标准误,事实['runnerFailureRules']) is not None#按规则看标准误
            沙箱={
                'mode':事实['mode'],#报告受限模式
                'denied':(not 启动器失败) and 匹配特征(取字段(进程,'exitCode'),标准误,事实['denialSignatures']),#启动器没失败且输出命中拒绝特征才算拒绝
                'enforcement':事实['enforcement'],#报告强制执行方式
            }#沙箱结算骨架
            if 启动器失败:#启动器失败时带上 runnerFailed
                沙箱['runnerFailed']=True#启动器失败
            if isinstance(进程,dict):#映射句柄（本地 bash 后台句柄）
                进程['sandbox']=沙箱#写回进程
            else:#对象句柄
                进程.sandbox=沙箱#写回进程
        super().进程已结束(进程,标准误,启动失败,启动错误)#再交给本地执行器做收尾

    def 隔离(自身,命令,政策):#把一条 shell 命令交给沙箱包装
        """经 ctx.sandbox 提供方包装一条 shell 命令。提供方错误原样传播；返回的 argv 直接交给本地执行器的子进程路径。"""
        return 自身.ctx.sandbox.confine(['bash','-c',命令],政策)#用 bash -c 包进沙箱 argv

默认=沙箱Bash执行器#中文默认导出
default=沙箱Bash执行器#Cordis 默认导出（协议槽）
