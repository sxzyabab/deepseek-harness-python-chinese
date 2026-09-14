import math,os#有限数判定与路径
from typing import NotRequired,TypedDict#可选字段与结构类型
from .错误 import 子智能体错误#缝内失败
无启动能力={#冻结的无能力广告
    'outputSchema':False,#不支持输出模式
    'depthLimit':False,#不支持深度上限
    'toolFilter':False,#不支持工具过滤
    'persona':False,#不支持人设
}#NO_START_CAPABILITIES结束

class 跑结果结算(TypedDict):#settleRunResult 的输入
    attempt:object#回合尝试；返回终态结果
    collectOutput:object#取消或失败赢得结算时提供方暴露的快照
    cancelled:object#本地取消是否在观察到尝试结局之前已结算
    onError:NotRequired[object]#压成停止原因的失败的诊断槽
    signal:object#请求的取消信号
    onAbort:object#启动时登记的中止回调

class 子进程运行句柄零件(TypedDict):#subprocessRunHandle 的输入
    id:object#父作用域跑 id
    result:object#已压平、永不拒绝的结果任务
    signal:object#请求的取消信号
    onAbort:object#启动时登记的中止回调
    requestCancel:object#结算本地取消
    teardown:object#把子进程拆除到静止

def 断言正有限(前缀,名称,值):
    """断言已配置的计时界限是正有限数（它约束拆除或 shutdown 等待；零、负数或 NaN 会跳过或卡死它）。"""
    if isinstance(值,bool) or not isinstance(值,(int,float)) or not math.isfinite(值) or 值<=0:#非法界限
        raise 子智能体错误(前缀+': '+名称+' must be a positive finite number','INVALID_TIMEOUT')#拒绝

def 是否可进入目录(路径):
    """path 是否命名 harness 能进入的已存在目录。搜索权限探测要紧。"""
    try:#stat与access都可能抛文件系统错误
        if not os.path.isdir(路径):#不是目录
            return False#不可用
        if not os.access(路径,os.X_OK):#无进入权限
            return False#不可用
        return True#可进入
    except OSError:#文件系统访问错误
        return False#不可用

def 断言可用工作目录(前缀,标签,工作目录):
    """断言 cwd 真能承载子体：必须是绝对路径且是已存在可进入目录。"""
    if not os.path.isabs(工作目录):#必须绝对
        raise 子智能体错误(前缀+': '+标签+' must be an absolute path: '+工作目录,'INVALID_CWD')#拒绝相对路径
    if not 是否可进入目录(工作目录):#必须可进入目录
        raise 子智能体错误(前缀+': '+标签+' is not an accessible directory: '+工作目录,'INVALID_CWD')#拒绝不可用路径
    return 工作目录#原样返回

def 校验已配置工作目录(前缀,工作目录):
    """在插件加载时一次性校验已配置的 cwd 覆盖。"""
    if 工作目录 is None:#未配置
        return None#省略
    if 工作目录=='':#空字符串非法
        raise 子智能体错误(前缀+': config cwd must not be empty — omit the key to inherit the parent session cwd','INVALID_CWD')#拒绝空cwd
    return 断言可用工作目录(前缀,'config cwd',os.path.abspath(工作目录))#解析并校验

def 解析子工作目录(前缀,已配置,父工作目录):
    """在 start 时解析子体工作目录：已配置的部署覆盖（加载时已校验），否则用父会话的工作区 cwd。"""
    if 已配置 is not None:#已有部署覆盖
        return 已配置#覆盖
    if 父工作目录 is None:#父也没有
        raise 子智能体错误(前缀+': no working directory for the child — configure `cwd` or delegate from a parent session that has one','NO_CWD')#必须给出cwd
    return 断言可用工作目录(前缀,'parent session cwd',父工作目录)#校验父cwd

def 结算运行结果(零件):
    """按缝约定结算进程外跑结果：发布后 result 永不拒绝。零件为 dict。"""
    try:#尝试回合
        结果=零件['attempt']()#等待尝试
        if 零件['cancelled']():#取消已赢
            return {'output':零件['collectOutput'](),'stopReason':'aborted'}#压成中止
        return 结果#否则原结果
    except Exception as 错误:#尝试拒绝
        if 零件['cancelled']():#取消优先
            return {'output':零件['collectOutput'](),'stopReason':'aborted'}#压成中止
        try:#诊断槽不得拒绝跑结果
            if 'onError' in 零件 and 零件['onError'] is not None:#有槽
                零件['onError'](错误,'error')#通知诊断
        except Exception:#诊断槽抛出
            pass#诊断槽不能拒绝跑结果
        return {'output':零件['collectOutput'](),'stopReason':'error'}#压成错误

class 子进程运行句柄实例:
    """持有者所有的远程一次性跑：协议字段 id/localAgent/result 保持与上游 SubagentRun 一致；拆除入口仅中文 销毁。"""
    def __init__(自身,标识,结果,拆除):
        """记下身份、永不拒绝的结果，以及幂等拆除闭包。"""
        自身.id=标识#父作用域跑 id
        自身.localAgent=None#远程无本地智能体
        自身.result=结果#永不拒绝的结果任务
        自身._拆除=拆除#记忆化拆除闭包

    def 销毁(自身):
        """取消剩余工作并等待后端拆除到静止。幂等。"""
        return 自身._拆除()#同一任务

def 子进程运行句柄(零件):
    """为进程外子体发布缝跑句柄。销毁() 幂等（一份记忆化拆除）。零件为 dict。"""
    拆除盒=[None]#记忆化拆除
    def 拆除():
        """结算本地取消，再等待后端拆除；已启动则复用同一任务。"""
        if 拆除盒[0] is not None:#已拆除则复用
            return 拆除盒[0]#同一任务
        零件['requestCancel']()#结算本地取消
        拆除盒[0]=零件['teardown']()#启动后端拆除
        return 拆除盒[0]#返回同一任务
    return 子进程运行句柄实例(零件['id'],零件['result'],拆除)#缝句柄
