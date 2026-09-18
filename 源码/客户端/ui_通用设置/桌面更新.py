__all__=['桌面更新源']#仅中文公开名

忙阶段=('checking','downloading','verifying','installing')#忙阶段

class 桌面更新源:#观察可选桌面 preload
    """两侧栏共用一份订阅。"""
    def __init__(自身,桥):
        """桥缺席则只持失败/打开中默认态。"""
        自身.桥=桥#桥
        自身.活=True#仍活
        自身.已收=False#已收推送
        自身.快照={'failed':False,'opening':False}#视图
        自身.监听=set()#订阅
        自身.退订=None#退订
        if 桥 is None:#无桥
            return#停
        def 推送(呈现):
            """写呈现。"""
            if 自身.活 is False:#已拆
                return#停
            自身.已收=True#记
            下=dict(自身.快照)#拷
            下['presentation']=呈现#呈现
            下['failed']=False#清失败
            自身.发布(下)#发
        自身.退订=桥['subscribe'](推送) if isinstance(桥,dict) else 桥.subscribe(推送)#订
        def 首拉成功(呈现):
            """无推送则写首态。"""
            if 自身.活 and 自身.已收 is False:#仍待
                下=dict(自身.快照)#拷
                下['presentation']=呈现#写
                自身.发布(下)#发
        def 首拉失败():
            """首拉失败。"""
            if 自身.活 and 自身.已收 is False:#仍待
                下=dict(自身.快照)#拷
                下['failed']=True#失败
                自身.发布(下)#发
        状态=桥['status'] if isinstance(桥,dict) else 桥.status#状态法
        try:#首拉
            首拉成功(状态())#同步
        except Exception:#失败
            首拉失败()#标

    def 发布(自身,快照):
        """写快照并通知。"""
        自身.快照=快照#写
        for 听 in list(自身.监听):#通知
            听()#触发

    def getSnapshot(自身):
        """当前视图。"""
        return 自身.快照#快照

    def subscribe(自身,监听):
        """订阅。"""
        自身.监听.add(监听)#加
        def 退():
            """退订。"""
            自身.监听.discard(监听)#删
        return 退#退

    def open(自身):
        """触发一次用户动作。"""
        if 自身.活 is False or 自身.桥 is None:#无
            return#停
        态=自身.快照#当前
        呈现=态.get('presentation')#呈现
        if 态.get('opening') or (呈现 is not None and 呈现.get('phase') in 忙阶段):#忙
            return#停
        下=dict(态)#拷
        下['opening']=True#打开中
        自身.发布(下)#发
        打开=自身.桥['open'] if isinstance(自身.桥,dict) else 自身.桥.open#打开
        try:#跑
            打开()#打开
        except Exception:#失败
            if 自身.活:#仍活
                败=dict(自身.快照)#拷
                败['failed']=True#失败
                自身.发布(败)#发
        finally:#收场
            if 自身.活:#仍活
                收=dict(自身.快照)#拷
                收['opening']=False#清
                自身.发布(收)#发

    def dispose(自身):
        """拆除。"""
        自身.活=False#死
        if 自身.退订 is not None:#有
            自身.退订()#退
