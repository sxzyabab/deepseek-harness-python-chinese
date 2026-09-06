"""右对齐 `/goal` 输入气泡。

对齐上游 `ui-goal/src/client/GoalCommandInputView.tsx`。公开面仅中文名。
无普通消息动作。
"""

__all__=['目标命令输入视图']#仅中文公开名

def 缺省翻译(键,_插值=None):#无文案函数
    """原样返回键。"""
    return 键#键

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
        节点=自身.属性['node'] if 'node' in 自身.属性 and 自身.属性['node'] is not None else {}#节点
        数据=节点['data'] if 'data' in 节点 and 节点['data'] is not None else {}#载荷
        翻译=自身.属性['t'] if 't' in 自身.属性 and 自身.属性['t'] is not None else 缺省翻译#文案
        return {#视图
            'aria':翻译('commandInput.aria'),#无障碍
            'text':数据['text'] if 'text' in 数据 else None,#命令行
            'commandId':数据['commandId'] if 'commandId' in 数据 else None,#命令 id
            'time':数据['time'] if 'time' in 数据 else None,#时刻
        }#视图结束

    def __call__(自身,属性=None):#组件调用形
        """对齐 React 组件调用。"""
        if 属性 is not None:#有新 props
            自身.更新(属性)#刷新
        return 自身.视图()#视图
