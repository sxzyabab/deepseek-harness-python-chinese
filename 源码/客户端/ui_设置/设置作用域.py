from ...依赖 import cordis#外部依赖胶水
服务=cordis.服务#Cordis 服务基类
from 客户端.schema_form import 再水合模式,校验草稿#再水合与校验

__all__=['快照存储','设置作用域控制器','设置作用域绑定器','设置错误']#仅中文公开名

class 设置错误(Exception):
    """本包设置作用域失败。"""
    def __init__(自身,消息):
        """记下英文消息。"""
        super().__init__(消息)#消息原样英文

class 快照存储:#简易快照存储
    """行快照 + 订阅；对齐 createSnapshotStore。"""
    def __init__(自身,初值):#播种
        """记下初值。"""
        自身.状态=dict(初值)#状态副本
        自身.监听者=set()#订阅者

    def getSnapshot(自身):#读快照
        """返回当前状态引用。"""
        return 自身.状态#状态

    def subscribe(自身,回调):#订阅
        """登记变更回调。"""
        自身.监听者.add(回调)#加入
        def 退订():#退订
            """取消。"""
            自身.监听者.discard(回调)#删除
        return 退订#退订器

    def update(自身,变换):#就地变换并通知
        """调用变换(state)。"""
        变换(自身.状态)#变换
        for 回调 in list(自身.监听者):#通知
            回调()#触发

    def set(自身,下一份):#整体替换
        """用新快照覆盖。"""
        自身.状态=dict(下一份)#覆盖
        for 回调 in list(自身.监听者):#通知
            回调()#触发

class 设置作用域控制器:#一个命名空间的宿主读写控制器
    """把一个命名空间的宿主读写串行化到快照存储之后。mutate/describe 返回任务，入队改为同步阻塞。"""
    def __init__(自身,接口,规格,持久化='host'):#按持久化模式播种
        """记下接口、规格与持久化模式。"""
        自身.接口=接口#设置线上接口
        自身.规格=规格#命名空间身份与可选解码器
        自身.持久化=持久化#host 走线上，memory 仅进程内
        自身.store=快照存储({#初始快照
            'status':'loading' if 持久化=='host' else 'unavailable',#宿主则加载中
            'value':None,#尚未解码
            'base':None,#尚未拿到 base
            'user':None,#尚未拿到用户层
            'revision':None,#尚未拿到修订
            'writable':False,#尚未得知可写
            'mode':持久化,#持久化模式
        })#仓库结束
        自身.读世代=0#读世代
        自身.写世代=0#写世代
        自身.已拆除=False#是否已拆除

    def getSnapshot(自身):#读当前快照
        """返回当前同步快照。"""
        return 自身.store.getSnapshot()#仓库

    def subscribe(自身,监听):#订阅快照
        """观察快照替换。"""
        return 自身.store.subscribe(监听)#转交

    def load(自身):#排队刷新
        """阻塞执行一次宿主刷新。"""
        自身.读世代+=1#抬读世代
        世代=自身.读世代#本请求
        if 自身.持久化=='memory' or 自身.已拆除:#跳过
            return None#空
        自身.读取(世代)#本次读

    def set(自身,字段,值):#排队写一个字段
        """阻塞执行一次字段写入。"""
        return 自身.写入({'op':'set','path':[字段],'value':值})#编成 set

    def unset(自身,字段):#排队清除一个字段
        """阻塞执行一次字段清除。"""
        return 自身.写入({'op':'unset','path':[字段]})#编成 unset

    def dispose(自身):#拆除
        """抬世代压制在飞操作。"""
        自身.已拆除=True#标记已拆除
        自身.读世代+=1#抬读
        自身.写世代+=1#抬写

    def 写入(自身,操作):#一次路径变更
        """抬读世代压制在飞读，仅最新写可发布。"""
        自身.读世代+=1#抬读
        自身.写世代+=1#抬写
        世代=自身.写世代#本写
        if 自身.持久化=='memory' or 自身.已拆除:#跳过
            return None#空
        快照=自身.getSnapshot()#当前快照
        修订=快照['revision'] if 'revision' in 快照 else None#乐观锁
        载荷={'ns':自身.规格['namespace'],'ops':[操作]}#载荷
        if 修订 is not None:#有修订
            载荷['expectedRevision']=修订#栅栏
        try:#调用 mutate
            应答=自身.接口.settings.mutate(载荷).等待()#过线
        except Exception:#传输失败；RPC 异常契约未定
            if not 自身.已拆除 and 世代==自身.写世代:#最新写
                自身.读世代+=1#抬读
                自身.读取(自身.读世代)#恢复读
            return#不再发布
        结果=应答['result']#业务结果
        if not 结果['ok']:#业务失败
            if not 自身.已拆除 and 世代==自身.写世代:#最新写
                自身.读世代+=1#抬读
                自身.读取(自身.读世代)#恢复读
            return#不再发布
        自身.接纳(结果['value'],世代==自身.写世代)#仅最新写发布

    def 读取(自身,世代):#拉命名空间描述
        """describe 后按世代接纳。"""
        try:#调用 describe
            应答=自身.接口.settings.describe({}).等待()#描述全部
        except Exception:#传输失败；RPC 异常契约未定
            return#不改快照
        结果=应答['result']#业务结果
        if not 结果['ok'] or 自身.已拆除:#失败或已拆
            return#丢弃
        值袋=结果['value'] if 'value' in 结果 and 结果['value'] is not None else {}#值
        可写=值袋['writable'] if 'writable' in 值袋 else None#全局可写
        视图=None#本命名空间
        空间列表=值袋['namespaces'] if 'namespaces' in 值袋 and 值袋['namespaces'] is not None else []#命名空间列表
        for 候选 in 空间列表:#找
            if 候选['ns']==自身.规格['namespace']:#命中
                视图=候选#记下
                break#找到
        发布=世代==自身.读世代#是否最新读
        if 视图 is None:#应答里没有
            if 发布:#仍最新
                def 标不可用(态):#标不可用
                    """命名空间不可用。"""
                    态['status']='unavailable'#不可用
                    态['writable']=可写#记下可写
                自身.store.update(标不可用)#写入
            return#结束
        自身.接纳(视图,发布,可写)#有视图则接纳

    def 接纳(自身,视图,发布,可写=None):#把视图写入快照
        """仅发布时解码分区值。"""
        解码=自身.解码(视图) if 发布 else None#仅发布时解码
        def 写入快照(态):#写入修订层与可选值
            """更新快照字段。"""
            态['revision']=视图['revision'] if 'revision' in 视图 else None#修订
            态['base']=视图['base'] if 'base' in 视图 else None#base
            态['user']=视图['user'] if 'user' in 视图 else None#user
            if 可写 is not None:#有可写
                态['writable']=可写#更新
            if 解码 is None:#不发布或解码失败
                return#不动 status/value
            态['status']='ready'#就绪
            态['value']=解码#分区值
        自身.store.update(写入快照)#写入

    def 解码(自身,视图):#把视图值收成分区
        """有自定义解码器则用之，否则 schema 校验普通对象。"""
        解码器=自身.规格['decode'] if 'decode' in 自身.规格 else None#自定义
        视图值=视图['value'] if 'value' in 视图 else None#视图值
        if 解码器 is not None:#有
            return 解码器(视图值)#自定义
        if not isinstance(视图值,dict):#非普通对象
            return None#拒绝
        try:#再水合并校验
            失败=校验草稿(再水合模式(视图['schema']),视图值)#校验
        except Exception:#信封非法；schema 异常契约未定
            return None#当作非法
        return 视图值 if 失败 is None else None#通过才返回

class 设置作用域绑定器(服务):#设置作用域绑定服务
    """持有偏好的功能经本服务到达设置传输。"""
    def __init__(自身,上下文):#注册为 settingsScope
        """服务名 settingsScope。"""
        super().__init__(上下文,'settingsScope')#登记服务

    def bind(自身,规格):#绑定一个命名空间作用域
        """生命周期跟调用方纤程。"""
        上下文=自身.所属上下文#调用方上下文
        连接=上下文.获取服务('connection')#连接句柄
        控制器=设置作用域控制器(#本命名空间控制器
            连接.api,#线上接口
            规格,#规格
            'host' if 连接.isLoopback else 'memory',#回环走宿主
        )#控制器结束
        def 装失效():#挂到调用方纤程
            """订失效并初次后台读。"""
            def 刷新(命名空间=None):#失效时刷新
                """可按命名空间过滤。"""
                if 命名空间 is not None and 命名空间!=规格['namespace']:#别的 ns
                    return#忽略
                控制器.load()#触发刷新
            远程=上下文.获取服务('remote')#远程面
            def 连接重置时刷新():#连接重置
                """整表刷新。"""
                刷新()#刷新
            拆表=[#拆除器
                远程.$on('settings/document-updated',刷新),#文档更新
                上下文.监听('connection/reset',连接重置时刷新),#连接重置
            ]#拆表结束
            控制器.load()#初次后台读
            def 拆除():#纤程拆除
                """先拆订阅再拆控制器。"""
                for 拆 in 拆表:#逐个
                    拆()#取消
                控制器.dispose()#静止
            return 拆除#拆除器
        上下文.副作用(装失效,f"ui-settings: {规格['namespace']} settings scope")#副作用
        return 控制器#交给调用方
