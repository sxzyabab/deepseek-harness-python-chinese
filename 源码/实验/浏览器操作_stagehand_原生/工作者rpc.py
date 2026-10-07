import queue,threading#应答通道
from ...基础设施.js特性 import PromiseEX as 期约#请求的异步结果
from ...工具.超时 import 等待中止#中止类已禁用
from .异常 import stagehand排空错误#SDK 未排空

__all__=['请求','应答']#仅中文公开名

def 请求(目标,方法,参数=None,信号=None):#发一条
    '发一条请求，返回期约：兑现值是应答值，应答通道异常或信号中止则拒绝。目标是收件队列'
    若已中止则抛出(信号)#调用前已中止则不发出
    应答箱=queue.Queue()#工作者把应答放进这里
    应答结果=期约()#工作者应答后结算
    竞争表=[应答结果]#先结算的一路决定请求结果
    def 收取应答():#收应答
        '阻塞到工作者应答，按应答内容结算应答结果'
        原始=应答箱.get()#阻塞取出唯一一条应答
        if not isinstance(原始,dict) or 'ok' not in 原始:#应答格式不对
            应答结果.拒绝(stagehand排空错误('Stagehand 工作者应答通道已关闭'))#等同通道被对端关闭
        elif 原始['ok'] is True:#对端执行成功
            应答结果.解决(原始.get('value'))#取回对端结果
        elif isinstance(原始.get('error'),str):#对端失败且带消息
            应答结果.拒绝(stagehand排空错误(原始['error']))#按对端消息拒绝
        else:#对端失败但没有消息
            应答结果.拒绝(stagehand排空错误('Stagehand 工作者请求已取消'))#按取消处理
    threading.Thread(target=收取应答,daemon=True).start()#后台收取应答
    if 信号 is not None:#调用方给了中止信号
        中止结果=期约()#信号置位时结算
        def 监视中止():#等中止
            '信号置位后按中止原因拒绝中止结果'
            等待中止(信号)#阻塞到信号置位
            原因=getattr(信号,'reason',None)#信号携带的中止原因
            if isinstance(原因,BaseException):#原因本身是异常
                中止结果.拒绝(原因)#原样拒绝
            else:#原因不是异常
                中止结果.拒绝(stagehand排空错误('Stagehand 工作者请求已取消'))#包成取消错误
        threading.Thread(target=监视中止,daemon=True).start()#后台监视中止
        竞争表.append(中止结果)#中止与应答竞速
    目标.put({'method':方法,'args':参数,'reply':应答箱})#投递请求
    return 期约.竞速(竞争表)#先结算的一路决定结果

def 应答(原始,执行):#答一条
    '校验并应答一条请求。原始是 dict'
    if not isinstance(原始,dict):#非法
        raise stagehand排空错误('Stagehand 工作者请求')
    方法=原始.get('method')#方法
    参数=原始.get('args')#参数
    应答箱=原始.get('reply')#通道
    if not isinstance(方法,str) or 应答箱 is None:#非法
        raise stagehand排空错误('Stagehand 工作者请求')
    try:#执行
        值=执行(方法,参数)#执行
        应答箱.put({'ok':True,'value':值})#成功
    except Exception as 错误:#失败
        应答箱.put({'ok':False,'error':str(错误) if str(错误) else type(错误).__name__})#失败
