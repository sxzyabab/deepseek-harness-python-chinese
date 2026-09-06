"""瞬时顶栏吐司。

对齐上游 `ui-primitives/src/Toast.tsx`。公开面仅中文名。
HOLD_MS+FADE_MS 必须与吐司.module.css 动画一致。属性为 dict。
"""

__all__=['吐司','保持毫秒','淡出毫秒']#仅中文公开名

保持毫秒=3000#全不透明保持
淡出毫秒=1000#淡出时长

class 吐司:#顶栏公告
    """滑入-保持-淡出；业主在 onDone 卸载。"""
    def __init__(自身,属性=None,**关键字参数):
        """合并 props。"""
        自身.属性=dict(属性 if 属性 is not None else {})#基础
        自身.属性.update(关键字参数)#覆盖

    def 更新(自身,属性):
        """刷新。"""
        自身.属性=dict(属性)#最新

    def 总时长(自身):
        """保持+淡出。"""
        return 保持毫秒+淡出毫秒#毫秒

    def 渲染(自身):
        """公告条视图。"""
        属性=自身.属性#props
        return {#吐司
            'type':'toast',#类型
            'text':属性['text'] if 'text' in 属性 else '',#文案
            'icon':属性['icon'] if 'icon' in 属性 else None,#图标
            'anchor':属性['anchor'] if 'anchor' in 属性 else None,#水平锚
            'onDone':属性['onDone'] if 'onDone' in 属性 else None,#完成
            'holdMs':保持毫秒,#保持
            'fadeMs':淡出毫秒,#淡出
            'cssModule':'吐司.module.css',#样式
        }#视图结束

    def __call__(自身,属性=None,**关键字参数):
        """对齐 React。"""
        if 属性 is not None or len(关键字参数)>0:#有；判 length
            合并=dict(属性 if 属性 is not None else {})#基
            合并.update(关键字参数)#覆
            自身.更新(合并)#刷
        return 自身.渲染()#渲
