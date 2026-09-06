"""连接断开顶条。

对齐上游 `ui-primitives/src/ConnectionBanner.tsx`。公开面仅中文名。
属主订阅连接态并传入 reconnecting；仅实际断线回退时显示。属性为 dict。
"""

__all__=['连接横幅','默认标签']#仅中文公开名

默认标签='连接已断开，正在重连…'#内置文案

class 连接横幅:#重连顶条
    """受控：reconnecting 为假则返回 None。"""
    def __init__(自身,属性=None,**关键字参数):
        """合并 props。"""
        自身.属性=dict(属性 if 属性 is not None else {})#基础
        自身.属性.update(关键字参数)#覆盖

    def 更新(自身,属性):
        """刷新。"""
        自身.属性=dict(属性)#最新

    def 渲染(自身):
        """断线时出横幅。"""
        属性=自身.属性#props
        重连=属性['reconnecting'] is True if 'reconnecting' in 属性 else False#重连
        if 重连 is False:#已连
            return None#静默
        return {#横幅
            'type':'connection-banner',#类型
            'label':属性['label'] if 'label' in 属性 else 默认标签,#文案
            'cssModule':'连接横幅.module.css',#样式
        }#结束

    def __call__(自身,属性=None,**关键字参数):
        """对齐 React。"""
        if 属性 is not None or len(关键字参数)>0:#有；判 length
            合并=dict(属性 if 属性 is not None else {})#基
            合并.update(关键字参数)#覆
            自身.更新(合并)#刷
        return 自身.渲染()#渲
