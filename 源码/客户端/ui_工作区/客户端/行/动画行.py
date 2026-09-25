"""侧栏按键行的提交驱动位移动画与进出淡入淡出。
首指针或键盘输入后才武装；父级为退出叠层提供定位容器。
"""

__all__=['动画行','行淡入毫秒','行滑动毫秒','样式表']#仅中文公开名

行淡入毫秒=100#进出淡入时长
行滑动毫秒=200#位移动画时长

样式表='''#对齐 AnimatedRows.module.css
.exits{position:absolute;inset:0;contain:strict;overflow:clip;pointer-events:none}
'''#样式表结束

def 同行键(先前键,下一键):
    """行键表是否同序同员。"""
    if len(先前键)!=len(下一键):#长度不同
        return False#异
    for 下标,键 in enumerate(先前键):#逐项
        if 键!=下一键[下标]:#异
            return False#异
    return True#同

def 相交(行矩,视口矩):
    """行矩形与视口是否相交。"""
    return (行矩['bottom']>视口矩['top'] and 行矩['top']<视口矩['bottom']
            and 行矩['right']>视口矩['left'] and 行矩['left']<视口矩['right'])#相交

class 动画行:#keyed 行列表动画容器
    """仅在成员或顺序变化时动画；降运动偏好时跳过。"""

    def __init__(自身,属性):
        """记下 props 与动画账本。"""
        自身.属性=属性 if 属性 is not None else {}#props
        自身.已武装=False#待首交互
        自身.列表节点=None#树列表 DOM
        自身.叠层节点=None#退出叠层 DOM
        自身.移动表={}#元素 → 动画
        自身.退出表={}#键 → {element,animation}

    def 更新(自身,属性):
        """换 props；调用方在提交后应调 提交后更新。"""
        自身.属性=属性 if 属性 is not None else {}#最新

    def 武装(自身):
        """指针或键盘捕获后武装。"""
        自身.已武装=True#武装

    def 绑定列表(自身,节点):
        """记下列表根。"""
        自身.列表节点=节点#列表

    def 绑定叠层(自身,节点):
        """记下退出叠层。"""
        自身.叠层节点=节点#叠层

    def 更新前快照(自身,先前属性):
        """提交前读位置；不满足动画条件则 None。"""
        列表=自身.列表节点#列表
        属性=自身.属性#当前
        if (not 自身.已武装
            or 同行键(先前属性.get('rowKeys',[]),属性.get('rowKeys',[]))
            or 先前属性.get('resetKey')!=属性.get('resetKey')
            or not 先前属性.get('ready')
            or not 属性.get('ready')
            or 列表 is None
            or not hasattr(列表,'animate')):#不动画
            return None#空
        媒=getattr(列表,'ownerDocument',None) or getattr(列表,'document',None)#文档
        if 媒 is not None and hasattr(媒,'defaultView') and 媒.defaultView is not None:#有窗
            匹配=媒.defaultView.matchMedia('(prefers-reduced-motion: reduce)')#降运动
            if 匹配.matches:#降
                return None#空
        视口=列表.getBoundingClientRect()#视口
        if hasattr(视口,'to_dict'):#自定义
            视口=视口.to_dict()#字典
        elif not isinstance(视口,dict):#DOMRect
            视口={'top':视口.top,'bottom':视口.bottom,'left':视口.left,'right':视口.right}#矩
        位置=自身._读位置()#位置
        下键=set(属性.get('rowKeys',[]))#下一批键
        移除={}#移出可见
        for 键,行 in 位置.items():#逐行
            if 键 in 下键 or not 相交(行['rect'],视口):#仍在或不可见
                continue#跳
            克隆=行['element'].cloneNode(True)#克隆
            克隆.removeAttribute('data-row-key')#去键
            克隆.inert=True#惰性
            缩进=行['element'].ownerDocument.defaultView.getComputedStyle(行['element']).getPropertyValue('--dsh-workspace-indent') if hasattr(行['element'],'ownerDocument') else ''#缩进
            if hasattr(克隆.style,'setProperty'):#有
                克隆.style.setProperty('--dsh-workspace-indent',缩进)#带缩进
            移除[键]={**行,'element':克隆}#记下
        return {'positions':位置,'removed':移除}#快照

    def 提交后更新(自身,先前属性,快照):
        """按快照播移动与退出；无快照则在结构变时清动画。"""
        if 快照 is None:#无动画
            属性=自身.属性#当前
            if (not 同行键(先前属性.get('rowKeys',[]),属性.get('rowKeys',[]))
                or 先前属性.get('resetKey')!=属性.get('resetKey')
                or 先前属性.get('ready')!=属性.get('ready')):#结构变
                自身.清空()#清
            return#止
        自身._取消移动()#停旧移动
        列表=自身.列表节点#列表
        叠层=自身.叠层节点#叠层
        视口矩=列表.getBoundingClientRect()#视口
        原点矩=叠层.getBoundingClientRect()#叠层原点
        def 矩字典(矩):
            """DOMRect → dict。"""
            if isinstance(矩,dict):#已是
                return 矩#原样
            return {'top':矩.top,'bottom':矩.bottom,'left':矩.left,'right':矩.right,'width':矩.width,'height':矩.height}#字典
        视口=矩字典(视口矩)#视口
        原点=矩字典(原点矩)#原点
        位置=自身._读位置()#新位置
        for 键,行 in 位置.items():#逐存活
            自身._卸退出(键)#卸同键退出
            先前行=快照['positions'].get(键)#先前
            if (not 相交(行['rect'],视口)
                and (先前行 is None or not 相交(先前行['rect'],视口))):#双不可见
                continue#跳
            if 先前行 is None:#新入
                自身._移动(行['element'],[{'opacity':0},{'opacity':1}],行淡入毫秒)#淡入
                continue#下一项
            横偏=先前行['rect']['left']-行['rect']['left']#dx
            纵偏=先前行['rect']['top']-行['rect']['top']#dy
            if 横偏==0 and 纵偏==0 and 先前行['opacity']==1:#无位无透明
                continue#跳
            自身._移动(行['element'],[#滑动
                {'transform':f'translate({横偏}px, {纵偏}px)','opacity':先前行['opacity']},
                {'transform':'translate(0, 0)','opacity':1},
            ],行滑动毫秒)#滑动
        for 键,行 in 快照['removed'].items():#退出
            元素=行['element']#克隆
            自身._卸退出(键)#卸旧
            样式=元素.style#样式
            样式.position='absolute'#绝对
            样式.margin='0'#无边
            样式.transform='none'#无变换
            样式.boxSizing='border-box'#盒
            样式.left=f"{行['rect']['left']-原点['left']}px"#左
            样式.top=f"{行['rect']['top']-原点['top']}px"#上
            样式.width=f"{行['rect']['width']}px"#宽
            样式.height=f"{行['rect']['height']}px"#高
            叠层.append(元素)#挂叠层
            动画=元素.animate([{'opacity':行['opacity']},{'opacity':0}],{'duration':行淡入毫秒,'easing':'ease-out','fill':'forwards'})#淡出
            自身.退出表[键]={'element':元素,'animation':动画}#记下
            def 完(_键=键):
                """淡出完卸。"""
                自身._卸退出(_键)#卸
            动画.onfinish=完#完

    def 卸载(自身):
        """清全部动画。"""
        自身.清空()#清

    def _读位置(自身):
        """列表内 data-row-key 行的矩形与透明度。"""
        列表=自身.列表节点#列表
        行表=列表.querySelectorAll('[data-row-key]')#行
        结果={}#键 → 位
        for 元素 in 行表:#逐行
            键=getattr(元素.dataset,'rowKey',None)#键
            if 键 is None:#无
                continue#跳
            矩=元素.getBoundingClientRect()#矩形
            if not isinstance(矩,dict):#DOMRect
                矩={'top':矩.top,'bottom':矩.bottom,'left':矩.left,'right':矩.right,'width':矩.width,'height':矩.height}#字典
            透明=1#默认
            if 元素 in 自身.移动表:#移动中
                透明=float(元素.ownerDocument.defaultView.getComputedStyle(元素).opacity) if hasattr(元素,'ownerDocument') else 1#读透明
            结果[键]={'element':元素,'rect':矩,'opacity':透明}#记下
        return 结果#位置

    def _移动(自身,元素,关键帧,时长):
        """播一段移动并记账。"""
        动画=元素.animate(关键帧,{'duration':时长,'easing':'ease-out'})#播
        自身.移动表[元素]=动画#记
        def 完():
            """完后卸。"""
            if 元素 in 自身.移动表:#仍在
                del 自身.移动表[元素]#卸
            动画.cancel()#取消残留
        动画.onfinish=完#完

    def _取消移动(自身):
        """停全部移动。"""
        for 动画 in list(自身.移动表.values()):#逐个
            动画.onfinish=None#断
            动画.cancel()#停
        自身.移动表.clear()#清

    def _卸退出(自身,键):
        """卸一条退出克隆。"""
        退出=自身.退出表.get(键)#项
        if 退出 is None:#无
            return#止
        退出['animation'].onfinish=None#断
        退出['animation'].cancel()#停
        退出['element'].remove()#卸 DOM
        del 自身.退出表[键]#去账

    def 清空(自身):
        """停移动并卸全部退出。"""
        自身._取消移动()#停移动
        for 键 in list(自身.退出表.keys()):#逐退出
            自身._卸退出(键)#卸

    def 渲染(自身):
        """树列表 + 退出叠层结构。"""
        属性=自身.属性#props
        return {#片段
            'type':'fragment',#片段
            'children':[#子
                {#列表
                    'type':'div','className':属性.get('className',''),'role':'tree',
                    'props':{'aria-label':属性.get('label','')},
                    'ref':自身.绑定列表,
                    'onPointerDownCapture':自身.武装,
                    'onKeyDownCapture':自身.武装,
                    'children':属性.get('children'),
                },#列表结束
                {#叠层
                    'type':'div','className':'exits','props':{'aria-hidden':True},
                    'ref':自身.绑定叠层,
                },#叠层结束
            ],#子结束
            'styleSheet':样式表,#样式
        }#片段结束
