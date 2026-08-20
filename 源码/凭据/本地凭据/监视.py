"""凭证文档的文件系统监视，对齐 chokidar 的忽略初扫与写入稳定窗口。"""
import os,threading,time#路径、线程与稳定计时

class 路径监视器:#单路径监视器
    """监视一个目标路径。文件缺席时仍跟踪该路径；写入稳定后发出 `all`，启动后发出 `ready`。"""
    def __init__(自身,路径,选项):#用路径与选项构造监视器
        """用路径与监视选项构造监视器。"""
        自身.路径=路径#监视目标
        自身.选项=选项#原始选项，供检视
        完成=选项.get('awaitWriteFinish') if isinstance(选项,dict) else None#写入稳定配置
        if not isinstance(完成,dict):#缺席则空表
            完成={}#空稳定配置
        自身.稳定阈值=完成.get('stabilityThreshold',100)#稳定窗口毫秒
        自身.轮询间隔=完成.get('pollInterval',10)#轮询间隔毫秒
        自身._回调={'all':[],'ready':[],'error':[]}#事件回调表
        自身._锁=threading.Lock()#回调与就绪旗标锁
        自身._已就绪=False#是否已发出 ready
        自身._停止=threading.Event()#拆除旗标
        自身._线程=threading.Thread(target=自身._运行)#监视线程
        自身._线程.daemon=True#不挡住退出
        自身._线程.start()#启动

    def on(自身,事件,回调):#登记事件回调
        """登记事件回调。若 `ready` 已经发生，立即补发一次。"""
        立刻=False#是否立刻补发 ready
        with 自身._锁:#回调表锁
            自身._回调.setdefault(事件,[]).append(回调)#登记
            if 事件=='ready' and 自身._已就绪:#已经就绪
                立刻=True#锁外调用
        if 立刻:#补发
            回调()#立刻通知
        return 自身#链式

    def close(自身):#关闭监视器
        """停止接事件并等待监视线程退出。"""
        自身._停止.set()#请求停止
        if 自身._线程.is_alive() and threading.current_thread() is not 自身._线程:#不能 join 自己
            自身._线程.join()#等到退出

    def _发出(自身,事件,*位置参数):#扇出事件
        """扇出事件到已登记回调。"""
        with 自身._锁:#拷贝回调
            列表=list(自身._回调.get(事件) or [])#当前回调
        for 回调 in 列表:#逐个调用
            回调(*位置参数)#发出

    def _快照(自身):#当前存在性与身份
        """读取目标的存在性、mtime 与大小；缺席为 missing。"""
        try:
            信息=os.stat(自身.路径)#取状态
            return ('file',信息.st_mtime_ns,信息.st_size)#文件快照
        except OSError:
            return ('missing',None,None)#缺席

    def _运行(自身):#监视循环
        """轮询目标，写入稳定后发出 `all`。"""
        上次=自身._快照()#初扫快照，ignoreInitial 所以不发 all
        with 自身._锁:#标记就绪
            自身._已就绪=True#已就绪
        自身._发出('ready')#就绪对账
        while not 自身._停止.is_set():#直到拆除
            间隔=max(float(自身.轮询间隔),1.0)/1000.0#至少 1ms
            if 自身._停止.wait(间隔):#等到停止或超时
                break#已拆除
            try:
                现在=自身._快照()#当前快照
                if 现在==上次:#未变
                    continue#继续轮询
                观察=现在#待稳定快照
                if 自身.稳定阈值>0:#需要稳定窗口
                    稳定开始=time.monotonic()#窗口起点
                    while not 自身._停止.is_set():#等到稳定或拆除
                        轮询=max(float(自身.轮询间隔),1.0)/1000.0#轮询秒
                        if 自身._停止.wait(轮询):#拆除
                            break#离开稳定等待
                        又=自身._快照()#再采样
                        if 又!=观察:#仍在变
                            观察=又#更新观察
                            稳定开始=time.monotonic()#重置窗口
                            continue#再等
                        if (time.monotonic()-稳定开始)*1000>=自身.稳定阈值:#已稳定
                            break#离开稳定等待
                if 自身._停止.is_set():#拆除则不再发布
                    break#离开循环
                上次=观察#接受新快照
                自身._发出('all','change',自身.路径)#任意文件系统事件
            except Exception as 错误:
                自身._发出('error',错误)#监视出错

def 监视(路径,选项=None):#创建监视器
    """监视规范化后的文档路径。"""
    if 选项 is None:#缺省选项
        选项={}#空选项
    return 路径监视器(路径,选项)#监视器
