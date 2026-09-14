
__all__=['创建目标激活源']#仅中文公开名

def _同快照(左,右):
    """按值比较两个空或已填充的激活快照。快照为 dict。"""
    return (
        (左['id'] if 'id' in 左 else None)==(右['id'] if 'id' in 右 else None)
        and (左['revision'] if 'revision' in 左 else None)==(右['revision'] if 'revision' in 右 else None)
        and (左['activation'] if 'activation' in 左 else None)==(右['activation'] if 'activation' in 右 else None)
    )#三字段

def _活跃引用(投影):
    """返回当前活跃 CAS 引用；目标未激活时为 None。投影为 dict 或 None。"""
    if 投影 is None:#无投影
        return None#无
    目标=投影['goal'] if 'goal' in 投影 else None#目标
    if 目标 is None:#无目标
        return None#无
    if ('phase' not in 目标) or 目标['phase']!='active':#非活跃
        return None#无
    return 目标#活跃引用

def 创建目标激活源(依赖):
    """创建登记方私有的激活源。仅在有框架钩子观察时订阅，卸载即释放。

    依赖为 dict：projection / session / getGoal / subscribeActivation / subscribeReset。
    返回带 getSnapshot/subscribe 的可观察快照源。
    """
    快照={}#当前快照
    订阅计数=0#订阅计数
    拆除器列表=[]#拆除器
    会话快照=依赖['session'].getSnapshot()#会话
    运行中=会话快照['running'] if 'running' in 会话快照 else False#running 镜像
    事件代次=0#事件代次
    投影代次=0#投影代次
    读取代次=0#读取代次
    监听集合=set()#监听集合

    def 发布(下一):
        """发布新快照。"""
        nonlocal 快照#可变
        if _同快照(快照,下一):#无变化
            return#跳过
        快照=下一#写入
        for 监听 in list(监听集合):#通知
            监听()#回调

    def 发起权威读(引用):
        """发起权威读。"""
        nonlocal 读取代次#可变
        if 引用 is None:#无引用
            return#跳过
        读取代次=读取代次+1#本读代次
        本读=读取代次#记下
        起始事件=事件代次#起始事件代
        起始投影=投影代次#起始投影代
        结果=依赖['getGoal']()#同步读目标
        if 本读!=读取代次 or 起始事件!=事件代次 or 起始投影!=投影代次:#过期
            return#丢弃
        if not isinstance(结果,dict) or ('ok' not in 结果) or 结果['ok'] is not True:#失败忽略
            return#忽略
        目标=结果['value'] if 'value' in 结果 else None#目标
        if 目标 is None:#空
            if _活跃引用(依赖['projection'].getSnapshot()) is None:#权威清空
                发布({})#清空
            return#结束
        发布({'id':目标['id'],'revision':目标['revision'],'activation':目标['activation']})#写入激活

    def 刷新投影():
        """投影刷新。"""
        nonlocal 投影代次#可变
        投影代次=投影代次+1#代次
        引用=_活跃引用(依赖['projection'].getSnapshot())#活跃
        if 引用 is None:#无活跃
            if 'id' in 快照:#曾有 id
                发布({})#清空
            return#结束
        if ('id' not in 快照) or 快照['id']!=引用['id'] or ('revision' not in 快照) or 快照['revision']!=引用['revision']:#CAS 变
            发布({'id':引用['id'],'revision':引用['revision']})#先挂 CAS 引用
        发起权威读(引用)#再权威读

    def 激活边沿(目标):
        """激活边沿。目标为 dict 或 None。"""
        nonlocal 事件代次,读取代次#可变
        事件代次=事件代次+1#代次
        读取代次=读取代次+1#作废在途读
        if 目标 is None:#清空
            发布({})#空
        else:
            发布({'id':目标['id'],'revision':目标['revision'],'activation':目标['activation']})#写入

    def 运行翻转():
        """running 翻转。"""
        nonlocal 运行中#可变
        下一=依赖['session'].getSnapshot()#会话
        下一运行=下一['running'] if 'running' in 下一 else False#running
        if 下一运行==运行中:#无变
            return#跳过
        运行中=下一运行#镜像
        发起权威读(_活跃引用(依赖['projection'].getSnapshot()))#重读

    def 连接重置():
        """连接重置。"""
        nonlocal 事件代次,投影代次#可变
        事件代次=事件代次+1#代次
        投影代次=投影代次+1#代次
        发起权威读(_活跃引用(依赖['projection'].getSnapshot()))#重读

    def 开始():
        """开始订阅。"""
        nonlocal 拆除器列表,运行中#可变
        拆除器列表=[#四路
            依赖['projection'].subscribe(刷新投影),#投影
            依赖['session'].subscribe(运行翻转),#会话
            依赖['subscribeActivation'](激活边沿),#激活
            依赖['subscribeReset'](连接重置),#重置
        ]#拆除器
        会话=依赖['session'].getSnapshot()#会话
        运行中=会话['running'] if 'running' in 会话 else False#镜像
        刷新投影()#首刷

    def 停止():
        """停止订阅。"""
        nonlocal 拆除器列表,读取代次#可变
        for 拆除 in 拆除器列表:#逐个
            拆除()#拆
        拆除器列表=[]#清空
        读取代次=读取代次+1#作废在途读

    def 取快照():
        """读当前快照。"""
        return 快照#快照

    def 订阅(监听):
        """订阅变更；首订阅启动，末订阅停止。"""
        nonlocal 订阅计数#可变
        监听集合.add(监听)#登记
        if 订阅计数==0:#首订阅
            开始()#启动
        订阅计数=订阅计数+1#计数
        def 拆除订阅():
            """去掉监听。"""
            nonlocal 订阅计数#可变
            监听集合.discard(监听)#删
            订阅计数=订阅计数-1#减
            if 订阅计数==0:#末订阅
                停止()#停止
        return 拆除订阅#拆除器

    return {'getSnapshot':取快照,'subscribe':订阅}#可观察源
