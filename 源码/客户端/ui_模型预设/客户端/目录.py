import threading#后台读目录

__all__=['权限目录','预设错误']#仅中文公开名

class 预设错误(Exception):
    """权限目录读失败。"""
    def __init__(自身,消息):
        """英文消息。"""
        super().__init__(消息)#消息

class 快照存储:#简易 SnapshotStore
    """值 + 订阅。"""
    def __init__(自身,初值):
        """记下初值。"""
        自身.状态=初值#当前
        自身.监听者=set()#订阅者

    def getSnapshot(自身):
        """当前值。"""
        return 自身.状态#值

    def subscribe(自身,回调):
        """登记。"""
        自身.监听者.add(回调)#加入
        def 退订():
            """取消。"""
            自身.监听者.discard(回调)#删除
        return 退订#退订器

    def set(自身,下一份):
        """写入并通知。"""
        自身.状态=下一份#覆盖
        for 回调 in list(自身.监听者):#通知
            回调()#触发

class 读任务:#一次目录读取
    """线程加等待。"""
    def __init__(自身,函数):
        """开跑。"""
        自身._结果=None#值
        自身._错误=None#失败
        自身._事件=threading.Event()#完成
        def 在线程执行():
            """执行读取。"""
            try:#读
                自身._结果=函数()#值
            except 预设错误 as 错误:#失败
                自身._错误=错误#记下
            自身._事件.set()#完成
        threading.Thread(target=在线线程执行,daemon=True).start()#后台

    def 等待(自身):
        """阻塞至完成。"""
        自身._事件.wait()#等
        if 自身._错误 is not None:#失败
            raise 自身._错误#抛
        return 自身._结果#值

class 权限目录:#进程级最新结果获胜的目录
    """整份浏览器进程一份完整权限目录。"""
    def __init__(自身,上下文):
        """先订失效源再读，关掉安装/读取竞态。"""
        自身.上下文=上下文#根
        自身.store=快照存储({'value':None})#完整快照
        自身.invalidations=快照存储({'count':0})#失效滴答
        自身.连接=上下文.获取服务('connection')#连接句柄
        自身.停目录=上下文.remote.on('permission-presets/catalog-changed',自身.目录已变)#目录变
        自身.停世代=自身.连接.generation.subscribe(自身.同步世代)#世代
        自身.世代标识=None#当前世代 id
        自身.已初始化=False#是否已同步过
        自身.纪元=0#读纪元
        自身.待决=None#进行中读取
        自身.失败=预设错误('permission catalog has no complete value')#最近失败
        自身.已拆除=False#拆除
        自身.同步世代()#首同步

    def 目录已变(自身):
        """目录通知。"""
        自身.失效()#滴答
        自身.刷新()#再读

    def 失效(自身):
        """给仍握着选项的消费者一拍。"""
        自身.invalidations.set({'count':自身.invalidations.getSnapshot()['count']+1})#加一

    def 刷新(自身):
        """对活动世代强制完整再读。"""
        if 自身.已拆除 is True:#已拆
            return#停
        快=自身.连接.generation.getSnapshot()#世代
        世代标识=快['id'] if 快 is not None and 'id' in 快 else None#id
        if 世代标识 is None:#无世代
            return#停
        if 世代标识!=自身.世代标识:#世代变了
            自身.同步世代()#同步
            return#停
        自身.开始读(世代标识)#读

    def 加载(自身):
        """命令弹出打开时取当前世代完整目录。进行中刷新先结算。"""
        if 自身.待决 is None and 自身.store.getSnapshot()['value'] is None:#还没有值
            自身.刷新()#开读
        while 自身.已拆除 is False:#直到有值或拆除
            快=自身.连接.generation.getSnapshot()#世代
            世代标识=快['id'] if 快 is not None and 'id' in 快 else None#id
            if 世代标识 is None:#无连接
                raise 预设错误('permission catalog has no active Host connection')#抛
            if 世代标识!=自身.世代标识:#世代变了
                自身.同步世代()#同步
            待决=自身.待决#进行中
            if 待决 is not None:#有
                待决.等待()#等
                continue#再看
            态=自身.store.getSnapshot()#快照
            if 态['value'] is not None:#有值
                return 态['value']#目录
            raise 自身.失败#失败
        raise 预设错误('permission catalog directory is disposed')#已拆

    def dispose(自身):
        """停订阅并收回迟到结算的写入权。"""
        if 自身.已拆除 is True:#已拆
            return#停
        自身.已拆除=True#拆
        自身.纪元+=1#作废
        自身.待决=None#清
        自身.停世代()#卸世代
        自身.停目录()#卸目录

    def 同步世代(自身):
        """世代丢失/替换时硬清旧 Host 值。"""
        if 自身.已拆除 is True:#已拆
            return#停
        快=自身.连接.generation.getSnapshot()#世代
        世代标识=快['id'] if 快 is not None and 'id' in 快 else None#id
        if 自身.已初始化 is True and 世代标识==自身.世代标识:#未变
            return#停
        if 自身.已初始化 is True:#真变了才撤选项
            自身.失效()#滴答
        自身.已初始化=True#已同步
        自身.世代标识=世代标识#记下
        自身.纪元+=1#作废旧读
        自身.待决=None#清
        自身.失败=预设错误('permission catalog has no complete value')#重置失败
        自身.store.set({'value':None})#清值
        if 世代标识 is not None:#有世代
            自身.开始读(世代标识)#读

    def 开始读(自身,世代标识):
        """独立一读；同世代最新纪元获胜。"""
        自身.纪元+=1#新纪元
        纪元=自身.纪元#本读
        自身.失败=预设错误('permission catalog has no complete value')#重置
        def 读():
            """拉完整目录。"""
            结果=自身.上下文.remote.permissionPresets.catalog().等待()#RPC
            if 结果['ok'] is not True:#失败
                错=结果['error']#错误
                raise 预设错误(str(错['code'])+': '+str(错['message']))#码+消息
            return 结果['value']#目录
        操作=读任务(读)#开跑
        def 结算():
            """写回或记下失败。"""
            try:#等
                值=操作.等待()#目录
                if 自身.接受(纪元,世代标识) is False:#过期
                    return#丢
                自身.store.set({'value':值})#写入
            except 预设错误 as 错误:#失败
                if 自身.接受(纪元,世代标识) is False:#过期
                    return#丢
                自身.失败=错误#记下
                自身.store.set({'value':None})#清
            if 自身.待决 is 操作:#仍是自己
                自身.待决=None#清
        threading.Thread(target=结算,daemon=True).start()#后台结算
        自身.待决=操作#记下

    def 接受(自身,纪元,世代标识):
        """拆除、刷新纪元、真实连接世代三重栅。"""
        if 自身.已拆除 is True:#已拆
            return False#拒
        if 纪元!=自身.纪元:#过期
            return False#拒
        if 世代标识!=自身.世代标识:#世代变
            return False#拒
        快=自身.连接.generation.getSnapshot()#活世代
        活=快['id'] if 快 is not None and 'id' in 快 else None#id
        return 活==世代标识#仍是
