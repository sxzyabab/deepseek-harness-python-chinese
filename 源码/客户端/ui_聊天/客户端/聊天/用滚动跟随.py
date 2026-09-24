import builtins,weakref

__all__=['滚动度量','滚动跟随','用滚动跟随']

拥有者=weakref.WeakKeyDictionary()

def 滚动度量(元素):
    """读滚动口几何，不测量子节点。"""
    高=元素.clientHeight
    return {'top':元素.scrollTop,'height':高,'floor':max(0,元素.scrollHeight-高)}

class 滚动跟随:
    """一个滚动口的跟随意图；原生动画进度不算读者移动。"""
    def __init__(自身,跟随中,阈值):
        """记下初始跟随与距底阈值。"""
        自身.跟随中=跟随中
        自身.阈值=阈值
        自身.目标=None
        自身.已采样顶=None

    @staticmethod
    def 按元素(元素):
        """读取位置补偿用的已挂载控制器。"""
        return 拥有者.get(元素)

    def 绑定(自身,元素):
        """与同一滚动口的读取位置补偿共享本控制器。"""
        拥有者[元素]=自身
        def 释放():
            """卸载或关闭时解除关联。"""
            if 拥有者.get(元素) is 自身:
                del 拥有者[元素]
        return 释放

    @property
    def active(自身):
        """内容增长是否应跟随底部。"""
        return 自身.跟随中

    @property
    def animating(自身):
        """是否仍有未完成的原生跟随目标。"""
        return 自身.目标 is not None

    def 近底(自身,度量):
        """是否在跟随阈值内。度量为 dict。"""
        return 度量['floor']-度量['top']<=自身.阈值

    def 设跟随(自身,活动):
        """提交调用方拥有的跟随决定，不移动滚动口。"""
        自身.跟随中=活动
        if not 活动:
            自身.目标=None

    def 重置(自身):
        """把下一可见布局当作新的读者位置。"""
        自身.设跟随(False)
        自身.已采样顶=None

    def 采样(自身,度量,读者移动=None):
        """采纳已送达滚动；原生动画期间保留意图。"""
        if 读者移动 is None:
            读者移动=自身.已采样顶 is None or abs(度量['top']-自身.已采样顶)>0.5
        自身.已采样顶=度量['top']
        if not 自身.animating and 读者移动:
            自身.跟随中=自身.近底(度量)
        return 自身.active

    def 结算(自身,度量):
        """结算原生滚动；偏离目标则释放跟随。"""
        目标=自身.目标
        自身.目标=None
        if 目标 is None:
            读者移动=None
        else:
            读者移动=abs(度量['top']-min(目标,度量['floor']))>自身.阈值
        return 自身.采样(度量,读者移动)

    def 跳转(自身,元素,度量,顶):
        """立即定位并采纳结果跟随意图。"""
        动画中=自身.animating
        自身.目标=None
        目标=max(0,min(度量['floor'],顶))
        if 动画中:
            元素.scrollTo({'top':目标,'behavior':'instant'})
        elif 目标!=度量['top']:
            元素.scrollTop=目标
        落地={'top':元素.scrollTop,'height':度量['height'],'floor':度量['floor']}
        自身.已采样顶=落地['top']
        自身.跟随中=自身.近底(落地)
        return 落地

    def 到底(自身,元素,度量,行为):
        """跟随测得的底部；减少动效时立即定位。"""
        自身.跟随中=True
        if 行为=='instant' or 度量['top']>=度量['floor'] or (not 自身.animating and 自身.近底(度量)):
            return 自身.跳转(元素,度量,度量['floor'])
        匹配媒体=getattr(builtins,'matchMedia',None)
        if callable(匹配媒体) and 匹配媒体('(prefers-reduced-motion: reduce)').matches:
            return 自身.跳转(元素,度量,度量['floor'])
        if 自身.目标 is None:
            自身.目标=度量['floor']
            元素.scrollTo({'top':度量['floor'],'behavior':'smooth'})
        return 度量

    def 打断(自身,元素,度量):
        """读者手势前取消原生运动。"""
        if not 自身.animating:
            return
        自身.目标=None
        自身.已采样顶=度量['top']
        元素.scrollTo({'top':度量['top'],'behavior':'instant'})

def 用滚动跟随(初始,阈值):
    """铸造独立跟随控制器。"""
    return 滚动跟随(初始,阈值)
