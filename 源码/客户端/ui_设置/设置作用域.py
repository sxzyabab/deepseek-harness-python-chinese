import threading
from copy import deepcopy as 深拷贝#排队前拷操作
from ...依赖.cordis.服务 import 服务#Cordis 服务基类

__all__=['快照存储','设置作用域控制器','设置作用域绑定器','设置错误']#仅中文公开名

class 设置错误(Exception):
    """本包设置作用域失败。"""
    def __init__(自身,消息):
        """记下英文消息。"""
        super().__init__(消息)#消息原样英文

class 快照存储:
    """行快照 + 订阅；对齐 createSnapshotStore。"""
    def __init__(自身,初值):
        """记下初值。"""
        自身.状态=dict(初值)#状态副本
        自身.监听者=set()#订阅者

    def getSnapshot(自身):
        """返回当前状态引用。"""
        return 自身.状态#状态

    def subscribe(自身,回调):
        """登记变更回调。"""
        自身.监听者.add(回调)#加入
        def 退订():
            """取消。"""
            自身.监听者.discard(回调)#删除
        return 退订#退订器

    def update(自身,变换):
        """调用变换(state)。"""
        变换(自身.状态)#变换
        for 回调 in list(自身.监听者):#通知
            回调()#触发

    def set(自身,下一份):
        """用新快照覆盖。"""
        自身.状态=dict(下一份)#覆盖
        for 回调 in list(自身.监听者):#通知
            回调()#触发

class 设置作用域控制器:
    """一份命名空间在共享描述镜像上的派生视图，加上该命名空间的串行 Host 写入。"""
    def __init__(自身,上下文,规格,镜像,持久化,模式):
        """记下提供方上下文、规格、共享镜像、持久化与模式服务。"""
        自身.上下文=上下文#提供方上下文，写走 remote.settings
        自身.规格=规格#命名空间身份与可选解码器
        自身.镜像=镜像#共享描述镜像
        自身.持久化=持久化#host 走线上，memory 仅进程内
        自身.模式=模式#设置自有模式操作
        自身.store=快照存储({#初始快照
            'status':'loading' if 持久化=='host' else 'unavailable',#宿主则加载中
            'value':None,#尚未解码
            'base':None,#尚未拿到 base
            'user':None,#尚未拿到用户层
            'revision':None,#尚未拿到修订
            'writable':False,#尚未得知可写
            'mode':持久化,#持久化模式
        })#仓库结束
        自身.写世代=0#写世代
        自身.已拆除=False#是否已拆除
        自身.退订=None#镜像订阅拆除器
        自身.待决修订=None#已被取代的写答出的修订栅栏
        自身.队锁=threading.Lock()#写队列锁
        自身.队尾=threading.Event()#当前队尾
        自身.队尾.set()#空闲已完成
        if 持久化=='host':#宿主则从镜像派生
            自身.退订=镜像.subscribe(自身.推导)#镜像变则派生
            自身.推导()#立即派生一次

    def getSnapshot(自身):
        """返回当前同步快照。"""
        return 自身.store.getSnapshot()#仓库

    def subscribe(自身,监听):
        """观察快照替换。"""
        return 自身.store.subscribe(监听)#转交

    def set(自身,字段,值):
        """排队写一个字段；阻塞至写入与可能的恢复读结算。"""
        自身.mutate([{'op':'set','path':[字段],'value':值}])#编成 set

    def unset(自身,字段):
        """排队清除一个字段；阻塞至清除与可能的恢复读结算。"""
        自身.mutate([{'op':'unset','path':[字段]}])#编成 unset

    def mutate(自身,操作表,期望修订=None):
        """排队一次原子命名空间变更；阻塞至变更与可能的恢复读结算。"""
        自有操作=深拷贝(操作表)#排队时拷贝
        自身.写世代+=1#抬写世代
        世代=自身.写世代#本写
        def 执行():
            """过线 mutate，仅最新结算折入镜像。"""
            修订=期望修订#调用方栅栏
            if 修订 is None:#未固定
                修订=自身.待决修订#先取被取代写的修订
            if 修订 is None:#仍无
                修订=自身.getSnapshot()['revision']#镜像修订
            应答=自身.上下文.remote.settings.mutate(自身.规格['namespace'],自有操作,修订).等待()#过线
            if 应答['ok'] is not True:#业务失败
                自身.恢复(世代)#最新写才恢复读
                return#不再发布
            if 自身.已拆除 is True:#已拆
                return#丢弃
            if 世代==自身.写世代:#仍是最新写
                自身.待决修订=None#清待决
                自身.镜像.接纳视图(应答['value'])#折入镜像
            else:#已被后续写取代
                自身.待决修订=应答['value']['revision']#后继写先用此栅栏
        自身.排队(执行)#串行

    def 恢复(自身,世代):
        """最新失败写才重载 Host 状态；被取代的失败把恢复留给后者。"""
        if 自身.已拆除 is True or 世代!=自身.写世代:#过期
            return#留给最新写
        自身.待决修订=None#清待决
        自身.镜像.加载()#阻塞至镜像重读

    def dispose(自身):
        """停排队、停派生，并等待当前线上调用结算。"""
        with 自身.队锁:#与排队互斥
            自身.已拆除=True#标记已拆除
            尾=自身.队尾#当前队尾
        自身.写世代+=1#压制在飞写
        if 自身.退订 is not None:#有订阅
            自身.退订()#取消
        尾.wait()#等当前写结束

    def 排队(自身,操作):
        """把一次写串到队尾；失败不卡住后继。"""
        if 自身.持久化=='memory':#进程本地不写
            return#跳过
        本个=threading.Event()#本操作完成
        with 自身.队锁:#链入
            if 自身.已拆除 is True:#已拆
                return#跳过
            前一个=自身.队尾#等待前者
            自身.队尾=本个#新队尾
        前一个.wait()#等前者
        try:#执行
            if 自身.已拆除 is True:#等待期间被拆
                return#跳过
            操作()#过线
        finally:#队尾保持已完成，一次失败不得卡住后继
            本个.set()#唤醒后继与 dispose

    def 推导(自身):
        """从共享镜像快照选出本命名空间，不碰导线读。"""
        if 自身.已拆除 is True:#已拆
            return#停
        镜像快照=自身.镜像.getSnapshot()#共享快照
        if 镜像快照['view'] is None:#镜像尚无文档
            return#保持 loading
        可写=镜像快照['view']['writable']#文档可写
        视图=None#本命名空间
        for 候选 in 镜像快照['view']['namespaces']:#查找
            if 候选['ns']==自身.规格['namespace']:#命中
                视图=候选#记下
                break#找到
        if 视图 is None:#应答里没有
            def 标不可用(态):
                """命名空间未暴露。"""
                态['status']='unavailable'#不可用
                态['writable']=可写#记下可写
            自身.store.update(标不可用)#写入
            return#结束
        解码=自身.解码(视图)#分区值
        def 写入快照(态):
            """更新修订层与可选值。"""
            态['revision']=视图['revision']#修订
            态['base']=视图['base']#base
            态['user']=视图['user']#user
            态['writable']=可写#可写
            if 解码 is None:#解码失败保持原 status/value
                return#不动
            态['status']='ready'#就绪
            态['value']=解码#分区值
        自身.store.update(写入快照)#写入

    def 解码(自身,视图):
        """有自定义解码器则用之，否则 schema 校验普通对象。"""
        解码器=自身.规格['decode'] if 'decode' in 自身.规格 else None#自定义
        视图值=视图['value']#分区值
        if 解码器 is not None:#有
            return 解码器(视图值)#自定义
        if not isinstance(视图值,dict):#非普通对象
            return None#拒绝
        try:#再水合并校验
            失败=自身.模式.校验(自身.模式.再水合(视图['schema']),视图值)#校验
        except Exception:#信封非法；schema 异常契约未定
            return None#当作非法
        return 视图值 if 失败 is None else None#通过才返回

class 设置作用域绑定器(服务):
    """设置域基础服务。持有偏好的功能经本服务到达设置传输。"""
    def __init__(自身,上下文,配置):
        """服务名 settingsScope；记下共享镜像、模式与持久化。"""
        super().__init__(上下文,'settingsScope')#登记服务
        自身.镜像=配置['镜像']#共享描述镜像
        自身.模式=配置['模式']#模式服务
        自身.持久化=配置['持久化']#host 或 memory
        自身.拥有方=上下文#提供方纤程，写不走调用方 ctx

    def describe(自身):
        """跨命名空间表面所用的共享描述面。"""
        return 自身.镜像#同一份快照

    def bind(自身,规格):
        """在调用方插件生命周期上绑定一个命名空间作用域，不自作导线读。"""
        上下文=自身.所属上下文#调用方上下文
        控制器=设置作用域控制器(自身.拥有方,规格,自身.镜像,自身.持久化,自身.模式)#写走提供方 remote.settings
        def 装生命周期():
            """确保镜像已读；拆除时等控制器静止。"""
            threading.Thread(target=自身.镜像.确保,daemon=True).start()#不阻塞激活
            def 拆除():
                """等当前线上调用结束。"""
                控制器.dispose()#静止
            return 拆除#拆除器
        上下文.副作用(装生命周期,f"ui-settings: {规格['namespace']} settings scope")#副作用
        return 控制器#交给调用方
