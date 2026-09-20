import threading
from .设置作用域 import 快照存储#共享快照仓库

__all__=['设置描述镜像']#仅中文公开名

class 设置描述镜像:
    """Host 设置文档的客户端镜像：浏览器内唯一的 settings.describe 读取方。"""
    def __init__(自身,上下文,持久化='host'):
        """记下上下文与持久化；host 空闲，memory 不可用。"""
        自身.上下文=上下文#提供方插件上下文
        自身.持久化=持久化#host 走线上，memory 仅进程内
        自身.store=快照存储({#初始快照
            'status':'idle' if 持久化=='host' else 'unavailable',#host 空闲
            'view':None,#尚无视图
            'error':None,#无错
        })#仓库结束
        自身.飞行中=None#飞行中完成事件
        自身.需重跑=False#是否需重跑
        自身.世代=0#代际
        自身.跑线程=None#占槽执行运行的线程
        自身.槽锁=threading.Lock()#飞行槽锁

    def getSnapshot(自身):
        """返回当前同步快照（稳定引用直至下次变更）。"""
        return 自身.store.getSnapshot()#委托仓库

    def subscribe(自身,监听):
        """观察快照替换，返回退订器。"""
        return 自身.store.subscribe(监听)#委托仓库

    def 加载(自身):
        """从 Host 刷新。飞行中读期间的调用在其结算后标一次重跑。"""
        if 自身.持久化=='memory':#memory 无导线
            return#跳过
        with 自身.槽锁:#占槽
            if 自身.飞行中 is not None:#已有飞行
                自身.需重跑=True#标重跑
                完成=自身.飞行中#共享飞行
                重入=threading.current_thread() is 自身.跑线程#发布快照同步重入则不能等
                主跑=False#只等或重入返回
            else:#无飞行
                完成=threading.Event()#本读完成
                自身.飞行中=完成#先占槽再开跑
                自身.跑线程=threading.current_thread()#记下占槽线程
                重入=False#本线程主跑
                主跑=True#本线程跑
        if 主跑 is False:#共享飞行
            if 重入 is True:#store.set 同步重入
                return#只标重跑，避免同线程自等
            完成.wait()#等结算
            return
        try:#执行读循环
            自身.运行()#跑
        finally:#飞行槽必须在观察到需重跑为假的同一同步段清除
            with 自身.槽锁:#清槽
                if 自身.飞行中 is 完成:#仍是本读
                    自身.飞行中=None#清飞行
                if 自身.跑线程 is threading.current_thread():#仍是本线程占槽
                    自身.跑线程=None#清占槽线程
            完成.set()#唤醒等待方

    def 确保(自身):
        """一旦持有答案（或镜像终端不可用）即返回，仅从 idle 读取。"""
        if 自身.持久化=='memory':#memory 跳过
            return#无导线
        with 自身.槽锁:#看槽
            if 自身.飞行中 is not None:#已有飞行
                完成=自身.飞行中#共享
                重入=threading.current_thread() is 自身.跑线程#同步重入不能等
                要加载=False#只等
            else:#无飞行
                完成=None#无事件
                重入=False#无飞行
                要加载=自身.getSnapshot()['status']=='idle'#空闲则加载
        if 完成 is not None:#共享飞行
            if 重入 is True:#store.set 同步重入
                return#已有飞行覆盖本次
            完成.wait()#等结算
            return
        if 要加载 is True:#空闲
            自身.加载()#启动读

    def 接纳视图(自身,视图):
        """无导线读地把一次写答案的命名空间视图折进持有视图，并使仍在飞的读失效。"""
        先前=自身.store.getSnapshot()#先前快照
        自身.世代+=1#推进代际
        with 自身.槽锁:#标重跑
            if 自身.飞行中 is not None:#飞行中
                自身.需重跑=True#重跑以免发布写提交前取到的文档
        if 先前['view'] is None:#无文档不发部分
            return
        空间表=先前['view']['namespaces']#原命名空间列表
        命中=False#是否已有同 ns
        for 行 in 空间表:#查找
            if 行['ns']==视图['ns']:#同 ns
                命中=True#命中
                break#找到
        if 命中 is True:#替换同 ns
            新空间=[]#新列表
            for 行 in 空间表:#逐行
                新空间.append(视图 if 行['ns']==视图['ns'] else 行)#替换或原样
        else:#追加
            新空间=list(空间表)#浅拷
            新空间.append(视图)#追加
        新视图=dict(先前['view'])#视图浅拷
        新视图['namespaces']=新空间#折入列表
        下一=dict(先前)#快照浅拷
        下一['view']=新视图#写入视图
        自身.store.set(下一)#发布

    def 命名空间(自身,ns):
        """在持有视图上按 ns 查找行；未回答或未登记时为 None。"""
        视图=自身.store.getSnapshot()['view']#持有视图
        if 视图 is None:#尚无
            return None#缺席
        for 行 in 视图['namespaces']:#逐行
            if 行['ns']==ns:#命中
                return 行#视图行
        return None#未登记

    def 运行(自身):
        """串行 describe 读循环；需重跑则再读，代际变了则丢弃本次答案。"""
        while True:#直到无需重跑
            先前=自身.store.getSnapshot()#循环前状态
            if 先前['status']=='idle':#空闲则标加载
                加载中=dict(先前)#浅拷
                加载中['status']='loading'#加载中
                自身.store.set(加载中)#发布；可能同步重入加载
            with 自身.槽锁:#导线读发出前立即清除
                自身.需重跑=False#更早标的加载由本次读覆盖
            自身.世代+=1#捕获代际
            世代=自身.世代#本读代际
            try:#导线 describe
                应答=自身.上下文.remote.settings.describe().等待()#线上读
                if 应答['ok'] is True:#成功
                    成果={'view':应答['value']}#视图
                else:#业务失败
                    成果={'failure':应答['error']['message']}#失败文案
            except Exception as 错误:#抛错记入快照，不打断飞行槽
                成果={'failure':str(错误)}#失败文案
            if 世代!=自身.世代:#写答案使写提交前取到的文档读失效
                continue#重跑
            if 'view' in 成果:#成功
                自身.store.set({'status':'ready','view':成果['view'],'error':None})#就绪
            else:#失败
                持有=自身.store.getSnapshot()#持有态
                自身.store.set({#尚无答案回 idle 让确保重试；有则继续服务
                    'status':'idle' if 持有['view'] is None else 'ready',#无视图回 idle
                    'view':持有['view'],#保留视图
                    'error':成果['failure'],#记下失败
                })#结束 set
            with 自身.槽锁:#与清槽同一同步段观察需重跑
                if 自身.需重跑 is True:#读中途又有加载
                    continue#再读
                自身.飞行中=None#清飞行槽
                return
