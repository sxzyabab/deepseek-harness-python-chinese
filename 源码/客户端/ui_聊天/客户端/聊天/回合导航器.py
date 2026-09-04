"""回合导航轨：固定间距标记，悬停预览，溢出框内滚。

对齐上游 `ui-chat/src/client/chat/TurnNavigator.tsx`。公开面仅中文名。
"""

__all__=['回合导航器','标记间距','轨内边','淡出带']#仅中文公开名

标记间距=10#相邻标记间距
轨内边=6#首末内边
淡出带=24#端蒙版淡出

def 取字段(对象,键,缺省=None):#读字段
    """映射或属性。"""
    if 对象 is None:#空
        return 缺省#缺
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

def 项位样式(索引):#索引到位
    """自然位置 px。"""
    return {'--turn-natural-position':f'{索引*标记间距}px'}#位

def 框样式(数量,滚动顶):#框 CSS 变量
    """自然高与滚动。"""
    return {'--turn-natural-height':f'{(max(0,数量-1)*标记间距)+2*轨内边}px','--turn-rail-inset':f'{轨内边}px','--turn-scroll-top':f'{滚动顶}px'}#框

class 回合导航器:#导航轨
    """标记列表 + 预览 + 导航回调。"""

    def __init__(自身,属性=None):#构造
        """记下。"""
        自身.属性=属性 or {}#合成
        自身.预览回合=None#预览
        自身.滚动顶=0#顶

    def 更新(自身,属性):#刷新
        """刷新。"""
        自身.属性=属性 or {}#新

    def 渲染(自身):#结构树
        """轨。"""
        属性=自身.属性#props
        项们=list(取字段(属性,'items') or [])#项
        活动=取字段(属性,'activeTurn')#活动
        忙=取字段(属性,'busyTurn')#忙
        导航=取字段(属性,'onNavigate')#导航
        翻译=取字段(属性,'t',lambda 键,_=None:键)#文案
        标记=[]#标记
        for 索引,项 in enumerate(项们):#扫
            回合=取字段(项,'turn')#回合
            锚=取字段(项,'anchor') or {}#锚
            标记.append({'turn':回合,'prompt':取字段(项,'prompt'),'response':取字段(项,'response'),'active':回合==活动,'busy':回合==忙,'preview':回合==自身.预览回合,'anchorKind':取字段(锚,'kind'),'style':项位样式(索引),'ariaLabel':翻译('chat.turnNavigation.jumpLoad' if 取字段(锚,'kind')=='unloaded' else 'chat.turnNavigation.jump',{'turn':回合}),'onNavigate':(lambda 目标=项:导航(目标)) if callable(导航) else None})#标
        return {'type':'turn-navigator','label':翻译('chat.turnNavigation.label'),'frameStyle':框样式(len(项们),自身.滚动顶),'marks':标记,'previewTurn':自身.预览回合,'cssModule':'回合导航器.module.css'}#轨

    def __call__(自身,属性=None):#调用形
        """对齐。"""
        if 属性 is not None:#有
            自身.更新(属性)#刷
        return 自身.渲染()#渲
