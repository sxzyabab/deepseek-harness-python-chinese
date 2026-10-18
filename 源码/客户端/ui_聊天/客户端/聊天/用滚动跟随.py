from ....模块.客户端.通告 import 取握手窗口
__all__=['滚动度量','滚动跟随','用滚动跟随']

跟随主人={}


def 滚动度量(元素):
    '只读滚动口，不量子节点'
    高=元素.clientHeight or 0
    顶=元素.scrollTop or 0
    总=元素.scrollHeight or 0
    return {'top':顶,'height':高,'floor':max(0,总-高)}


def 减少动效():
    '用户要求减少动效时不做平滑滚动'
    try:
        匹配=取握手窗口().matchMedia('(prefers-reduced-motion: reduce)')
        return bool(getattr(匹配,'matches',False))
    except Exception:
        return False


class 滚动跟随:
    '一份滚动口的贴底意图。原生动画过程不算读者移动'
    def __init__(自身,跟随,阈值):
        '记下初始意图和贴底容差'
        自身.跟随=跟随 is True
        自身.阈值=阈值
        自身.目标=None
        自身.采样顶=None

    def 绑定(自身,元素):
        '让阅读补偿能找到这份控制器'
        跟随主人[id(元素)]=自身

        def 松开():
            '卸掉时只清自己的登记'
            if 跟随主人.get(id(元素)) is 自身:
                跟随主人.pop(id(元素),None)

        return 松开

    def 活动(自身):
        '内容长高时要不要跟着地板'
        return 自身.跟随

    def 动画中(自身):
        '还有没落地的原生滚动目标'
        return 自身.目标 is not None

    def 靠近底(自身,度量):
        '离地板不超过容差'
        return abs(度量['floor']-度量['top'])<=自身.阈值

    def 设跟随(自身,活动):
        '外部提交意图，不自己滚动'
        自身.跟随=活动 is True
        if not 自身.跟随:
            自身.目标=None

    def 重置(自身):
        '下一帧布局当作新的阅读位置'
        自身.设跟随(False)
        自身.采样顶=None

    def 采样(自身,度量,读者移动=None):
        '动画进行中不因为位移改意图'
        if 读者移动 is None:
            读者移动=自身.采样顶 is None or abs(度量['top']-自身.采样顶)>0.5
        自身.采样顶=度量['top']
        if not 自身.动画中() and 读者移动:
            自身.跟随=自身.靠近底(度量)
        return 自身.活动()

    def 结算(自身,度量):
        '原生滚动结束。没落到目标上就放开跟随'
        目标=自身.目标
        自身.目标=None
        移动=None
        if 目标 is not None:
            移动=abs(度量['top']-min(目标,度量['floor']))>自身.阈值
        return 自身.采样(度量,移动)

    def 跳到(自身,元素,度量,顶):
        '立刻定位，并按落地位置决定是否贴底'
        动画=自身.动画中()
        自身.目标=None
        目标=max(0,min(度量['floor'],顶))
        if 动画:
            元素.scrollTo({'top':目标,'behavior':'instant'})
        elif 目标!=度量['top']:
            元素.scrollTop=目标
        落地={'top':元素.scrollTop,'height':度量['height'],'floor':度量['floor']}
        自身.采样顶=落地['top']
        自身.跟随=自身.靠近底(落地)
        return 落地

    def 到底(自身,元素,度量,行为):
        '跟到地板。平滑请求在动画没结束前不改当前位置'
        自身.跟随=True
        if 度量['top']==度量['floor']:
            return 自身.跳到(元素,度量,度量['floor'])
        if 行为=='instant' and 自身.动画中():
            if 自身.目标!=度量['floor']:
                自身.目标=度量['floor']
                元素.scrollTo({'top':度量['floor'],'behavior':'smooth'})
            return 度量
        if 行为=='instant' or (not 自身.动画中() and 自身.靠近底(度量)):
            return 自身.跳到(元素,度量,度量['floor'])
        if 减少动效():
            return 自身.跳到(元素,度量,度量['floor'])
        if 自身.目标 is None:
            自身.目标=度量['floor']
            元素.scrollTo({'top':度量['floor'],'behavior':'smooth'})
        return 度量

    def 打断(自身,元素,度量):
        '读者动手前停掉还没完的原生动画'
        if not 自身.动画中():
            return
        自身.目标=None
        自身.采样顶=度量['top']
        元素.scrollTo({'top':度量['top'],'behavior':'instant'})


def 按元素取跟随(元素):
    '阅读补偿按元素找回控制器'
    return 跟随主人.get(id(元素))


def 用滚动跟随(初始,阈值):
    '一份不随采样重画的控制器'
    return 滚动跟随(初始,阈值)
