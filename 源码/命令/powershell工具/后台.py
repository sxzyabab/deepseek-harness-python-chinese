"""后台 pwsh 进程句柄的通用任务适配——与 `tool_bash` 后台适配同形、且与具体 shell 无关。

对齐上游 `tool-pwsh/src/background.ts`。公开面仅中文名；无英文别名。
"""
import threading#后台转发结算线程
from concurrent.futures import Future as _原生Future#单次操作结果

__all__=('进程结果','做成任务完成')#仅中文公开名

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

def _是否thenable(值):#判定可等待对象
    if 值 is None:#空不是
        return False#不是
    if callable(getattr(值,'wait',None)):#Future 风格
        return True#可等待
    return callable(getattr(值,'等待',None))#外来 thenable

def _等待(值):#统一阻塞到结算
    if callable(getattr(值,'wait',None)):#Future 风格
        return 值.wait()#等待
    return 值.等待()#外来 thenable

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 解开(值):#可等待则等待否则原样
    """可等待则等待，否则原样返回。"""
    if _是否thenable(值):#可等待
        return _等待(值)#等待
    return 值#同步值

def 进程结果(进程):#映射后台进程结果
    """把已结算的后台进程映射到通用任务结果词：`killed` 仍是 `killed`（详情为已知信号），其余为带退出码详情的 `completed`。非零命令退出只报告、不算失败，与前台渲染一致。"""
    if 取字段(进程,'status')=='killed':#被杀死
        信号=取字段(进程,'signal')#终止信号
        if 信号 is not None:#有信号
            return {'status':'killed','detail':'signal: '+str(信号)}#写入信号
        return {'status':'killed','detail':'killed before exit'}#提前杀死
    退出码=取字段(进程,'exitCode')#退出码
    if 退出码 is None:#尚未记下则按0
        退出码=0#默认0
    return {'status':'completed','detail':'exit code: '+str(退出码)}#其余一律completed

def 做成任务完成(进程):#进程结算后兑现为通用任务结果
    """把进程 done 映射成通用任务结果。"""
    结果=操作任务()#映射后的完成任务
    def 转发():#等到原进程结算再投影
        """等到原进程结算再投影。"""
        try:#正常结算
            解开(取字段(进程,'done'))#等到进程关闭
            结果.兑现(进程结果(进程))#投影为任务结果
        except BaseException as 错误:#结算失败
            结果.拒绝(错误)#原样拒绝
    工作=threading.Thread(target=转发)#后台转发线程
    工作.daemon=True#不挡住退出
    工作.start()#启动转发
    return 结果#交给 jobs 的 done
