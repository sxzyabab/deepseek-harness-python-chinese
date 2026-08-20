"""右对齐 `/goal` 输入气泡。



对齐上游 `ui-goal/src/client/GoalCommandInputView.tsx`。公开面仅中文名。

无普通消息动作。

"""



__all__=['目标命令输入视图']#仅中文公开名



def 取字段(对象,键,缺省=None):#从映射或对象读字段

    """从映射或对象读字段，缺席为缺省。"""

    if 对象 is None:#空

        return 缺省#缺席

    if isinstance(对象,dict):#映射

        if 键 in 对象:#自有键

            return 对象[键]#值

        return 缺省#缺席

    return getattr(对象,键,缺省)#属性



class 目标命令输入视图:#聊天节点视图

    """渲染 command-input 节点的文本气泡。"""

    def __init__(自身,属性):#构造

        """记下 props。"""

        自身.属性=属性#合成 props



    def 更新(自身,属性):#props 变更

        """刷新。"""

        自身.属性=属性#最新



    def 卸载(自身):#卸载

        """无状态。"""

        return#空



    def 视图(自身):#读视图模型

        """投影气泡。"""

        节点=取字段(自身.属性,'node') or {}#节点

        数据=取字段(节点,'data') or {}#载荷

        翻译=取字段(自身.属性,'t',lambda 键,_=None:键)#文案

        return {#视图

            'aria':翻译('commandInput.aria'),#无障碍

            'text':取字段(数据,'text'),#命令行

            'commandId':取字段(数据,'commandId'),#命令 id

            'time':取字段(数据,'time'),#时刻

        }#视图结束



    def __call__(自身,属性=None):#组件调用形

        """对齐 React 组件调用。"""

        if 属性 is not None:#有新 props

            自身.更新(属性)#刷新

        return 自身.视图()#视图


