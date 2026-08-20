"""轨迹时长偏好源规格。



对齐上游 `ui-trajectory/src/client/duration-store.ts`。公开面仅中文名。

"""



__all__=['创建轨迹时长存储']#仅中文公开名



def 创建轨迹时长存储():#创建轨迹时长偏好仓库

    """浏览器范围内共享的实测时长偏好；带 get/set，并带 init/persist 供 register。"""

    当前=[False]#可变单元格，初值 false

    def 取():#读当前偏好

        """当前是否显示实测时长。"""

        return 当前[0]#读出

    def 设(值):#写下偏好

        """写入布尔偏好。"""

        当前[0]=bool(值)#收成布尔

    return {#句柄：运行时钩子 + store 规格

        'get':取,#读

        'set':设,#写

        'getSnapshot':取,#快照别名

        'init':lambda:False,#播种初值

        'persist':'dsh.trajectory.duration',#本地持久名

    }#句柄结束


