import queue,threading#应答通道
from ...内核.作用域 import 操作任务#一次等待
from ...工具.超时 import 若已中止则抛出,已中止,等待中止#中止

__all__=['请求','应答']#仅中文公开名

def 请求(目标,方法,参数=None,信号=None):#发一条
    """发一条请求并在应答通道关闭前取回结果。目标是收件队列。"""
    若已中止则抛出(信号)#中止
    应答箱=queue.Queue()#应答
    任务=操作任务()#一次
    def 中止时():#取消
        """按原因拒绝。"""
        原因=getattr(信号,'reason',None) if 信号 is not None else None#原因
        if isinstance(原因,BaseException):#异常
            任务.拒绝(原因)#原因
        else:#包装
            任务.拒绝(Exception('Stagehand Worker request canceled'))#取消
    def 监视():#等中止
        """置位后拒绝。"""
        等待中止(信号)#等
        中止时()#拒绝
    if 信号 is not None:#有信号
        threading.Thread(target=监视,daemon=True).start()#监视
    def 收():#收应答
        """等应答。"""
        try:#收
            原始=应答箱.get()#应答
            if not isinstance(原始,dict) or 'ok' not in 原始:#畸形
                任务.拒绝(Exception('Stagehand Worker reply channel closed'))#关闭
                return#完
            if 原始['ok'] is True:#成功
                任务.兑现(原始.get('value'))#兑现
            else:#失败
                任务.拒绝(Exception(原始.get('error') if isinstance(原始.get('error'),str) else 'Stagehand Worker request canceled'))#拒绝
        except Exception as 错误:#失败
            任务.拒绝(错误)#拒绝
    threading.Thread(target=收,daemon=True).start()#收
    try:#投递
        目标.put({'method':方法,'args':参数,'reply':应答箱})#投递
    except Exception as 错误:#失败
        任务.拒绝(错误)#拒绝
    return 任务.等待()#等

def 应答(原始,执行):#答一条
    """校验并应答一条请求。原始是 dict。"""
    if not isinstance(原始,dict):#非法
        raise Exception('Stagehand Worker request')#失败
    方法=原始.get('method')#方法
    参数=原始.get('args')#参数
    应答箱=原始.get('reply')#通道
    if not isinstance(方法,str) or 应答箱 is None:#非法
        raise Exception('Stagehand Worker request')#失败
    try:#执行
        值=执行(方法,参数)#执行
        应答箱.put({'ok':True,'value':值})#成功
    except Exception as 错误:#失败
        应答箱.put({'ok':False,'error':str(错误) if str(错误) else type(错误).__name__})#失败
