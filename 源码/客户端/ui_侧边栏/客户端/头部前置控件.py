"""macOS 桌面折叠侧栏时对话 header 前置控件。"""

__all__=['头部前置控件']#仅中文公开名

class 头部前置控件:#前置席位
    """侧栏打开与新建会话控件；非 Darwin 桌面返回空。"""

    def __init__(自身,属性):
        """记下切换侧栏与开新会话。"""
        自身.属性=属性#合成 props

    def 是否达尔文桌面(自身):
        """对齐 isDarwinDesktop；宿主注入平台判定。"""
        return 自身.属性.get('darwinDesktop') is True#平台

    def 渲染(自身):
        """两枚图标按钮；非 Darwin 返回 None。"""
        if not 自身.是否达尔文桌面():#非桌面
            return None#空
        return {'toggleSidebar':自身.属性.get('toggleSidebar'),'startSession':自身.属性.get('startSession')}#动作
