"""外观行槽位仓库：主题服务快照的镜像。

对齐上游 `ui-theme/src/client/settings-store.ts`。公开面仅中文名。
插件 apply 的变更监听是唯一写入方；行组件经 useStore 读取。
"""

__all__=['创建外观行仓','外观行状态']#仅中文公开名

def 创建外观行仓():#创建外观行仓库
    """默认 system、修订 -1；sync 按修订守卫丢弃过期。"""
    状态={'preference':'system','revision':-1}#初始
    监听们=set()#订阅者

    def 通知():#通知
        """通知全部监听。"""
        for 听 in list(监听们):#快照
            听()#触发

    def 同步(偏好,修订):#按快照同步
        """修订不大于当前则丢弃。"""
        if 修订<=状态['revision']:#旧
            return#丢
        状态['preference']=偏好#偏好
        状态['revision']=修订#修订
        通知()#通知

    return {#仓句柄
        'getSnapshot':lambda:dict(状态),#快照拷贝
        'subscribe':lambda 听:(监听们.add(听) or (lambda:监听们.discard(听))),#订阅
        'sync':同步,#同步
        'init':状态,#初始态引用
    }#结束

外观行状态=dict#状态形别名（preference/revision）
