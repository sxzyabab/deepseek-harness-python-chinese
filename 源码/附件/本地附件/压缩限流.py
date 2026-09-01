"""实例拥有的原生图像变换并发上限。对齐上游 attachment-local/src/compression-limiter.ts。"""
import threading#线程与条件变量
__all__=['压缩限流器']#仅中文公开名

class 压缩限流器:#FIFO 压缩任务限流
    """异步压缩工作的 FIFO 限流器。"""
    def __init__(自身,并发度):#正的最大活跃任务数
        自身._并发度=并发度#槽位数
        自身._活跃=0#当前活跃数
        自身._等待=[]#等待启动的回调
        自身._锁=threading.Lock()#互斥

    def 运行(自身,任务):#占一槽运行任务
        """在实例槽可用后运行任务并返回结果。"""
        完成=threading.Event()#完成事件
        结果箱={'值':None,'错':None}#结果或错误
        def 启动():#真正启动任务
            try:#跑任务
                结果箱['值']=任务()#同步执行
            except BaseException as 错误:#失败
                结果箱['错']=错误 if isinstance(错误,Exception) else Exception('Image compression task rejected with a non-Error value.',{'cause':错误})#规范化
            finally:#释放槽
                with 自身._锁:#持锁
                    自身._活跃-=1#减活跃
                    if len(自身._等待)>0:#还有等待者
                        自身._等待.pop(0)()#启动下一个
                完成.set()#通知完成
        with 自身._锁:#决定立即或排队
            if 自身._活跃<自身._并发度:#有空槽
                自身._活跃+=1#占槽
                threading.Thread(target=启动,daemon=True).start()#后台启动
            else:#排队
                自身._等待.append(lambda: threading.Thread(target=启动,daemon=True).start())#入队启动器
        完成.wait()#等到本任务完成
        if 结果箱['错'] is not None:#失败
            raise 结果箱['错']#上抛
        return 结果箱['值']#返回结果
