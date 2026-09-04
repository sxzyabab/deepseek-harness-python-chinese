"""回合级过程披露控制器。

对齐上游 `ui-chat/src/client/chat/TurnProcessNodeView.tsx`。公开面仅中文名。
"""

__all__=['回合过程节点视图']#仅中文公开名

def 取字段(对象,键,缺省=None):#读字段
    """映射或属性。"""
    if 对象 is None:#空
        return 缺省#缺
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

class 回合过程节点视图:#turn-process 键
    """可折叠过程披露按钮。"""

    def __init__(自身,属性=None):#构造
        """记下。"""
        自身.属性=属性 or {}#合成

    def 更新(自身,属性):#刷新
        """刷新。"""
        自身.属性=属性 or {}#新

    def 渲染(自身):#结构树
        """不可折叠则 None。"""
        属性=自身.属性#props
        节点=取字段(属性,'node') or {}#节点
        数据=取字段(节点,'data') or 节点#数据
        过程=取字段(属性,'turnProcess')#过程面
        翻译=取字段(属性,'t',lambda 键,_=None:键)#文案
        if 过程 is None:#缺所有者
            raise ValueError('turn-process node requires Turn process owner state')#缺
        if not 取字段(过程,'foldable'):#不可折
            return None#不画
        开=bool(取字段(过程,'open'))#开合
        标签们=[]#片段
        工具数=取字段(数据,'toolCallCount') or 0#工具
        if 工具数>0:#有工具
            标签们.append(翻译('message.turnProcess.toolCalls.one' if 工具数==1 else 'message.turnProcess.toolCalls.other',{'count':工具数}))#工具
        消息数=取字段(数据,'messageCount') or 0#消息
        if 消息数>0:#有消息
            标签们.append(翻译('message.turnProcess.messages.one' if 消息数==1 else 'message.turnProcess.messages.other',{'count':消息数}))#消息
        子数=取字段(数据,'subagentCount') or 0#子代理
        if 子数>0:#有子
            标签们.append(翻译('message.turnProcess.subagents.one' if 子数==1 else 'message.turnProcess.subagents.other',{'count':子数}))#子
        标签=翻译('message.turnProcess.thoughtForAWhile') if len(标签们)==0 else 翻译('message.turnProcess.separator').join(标签们)#标签
        def 点击():#翻转开合
            """先聚焦语义由宿主处理。"""
            设=取字段(过程,'setOpen')#设
            if callable(设):#有
                设(not 开)#翻
        return {'type':'turn-process','open':开,'label':标签,'turn':取字段(数据,'turn'),'messageCount':消息数,'toolCallCount':工具数,'subagentCount':子数,'onClick':点击,'cssModule':'回合过程节点视图.module.css'}#按钮

    def __call__(自身,属性=None):#调用形
        """对齐。"""
        if 属性 is not None:#有
            自身.更新(属性)#刷
        return 自身.渲染()#渲
