"""语言行槽位仓库：语言服务快照的镜像。



对齐上游 `locale/src/client/settings-store.ts`。公开面仅中文名。

"""



__all__=['创建语言行仓库']#仅中文公开名



def 创建语言行仓库():#声明语言行状态与写入面

    """返回语言行仓库句柄（纯映射 + sync 动作）。"""

    状态={'active':'','options':[],'revision':-1}#空选项，修订 -1

    监听者=set()#变更订阅



    def 取快照():#读当前快照

        """返回当前状态映射。"""

        return 状态#当前状态



    def 订阅(回调):#登记监听

        """登记变更回调，返回退订。"""

        监听者.add(回调)#加入

        def 退订():#取消

            """取消订阅。"""

            监听者.discard(回调)#删除

        return 退订#退订器



    def 同步(当前,选项,修订):#按快照同步

        """旧修订丢弃；否则写入并通知。"""

        if 修订<=状态['revision']:#旧修订

            return#丢弃

        状态['active']=当前#当前语言

        状态['options']=list(选项)#选项

        状态['revision']=修订#记下修订

        for 回调 in list(监听者):#通知

            回调()#触发



    return {#仓库句柄

        'getSnapshot':取快照,#读快照

        'subscribe':订阅,#订阅

        'actions':{'sync':同步},#写入面

        'spec':{'init':lambda:状态},#规格形

    }#句柄结束


