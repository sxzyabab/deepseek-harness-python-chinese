from nicegui import ui as 界面

__all__=['文档标题']#仅中文公开名


class 文档标题:#浏览器标题投影
    '把选定持久会话标题投影到文档标题；卸载时恢复产品标题'

    def __init__(自身,属性):
        '记下 props'
        自身.属性=属性 if 属性 is not None else {}#合成 props
        自身._上次标题=None#上次写入

    def 更新(自身,属性):
        '刷新合成 props'
        自身.属性=属性 if 属性 is not None else {}

    def 读是否显示会话标题(自身):
        '仅 Conversation（无全局面板）时显示会话标题'
        用面板=自身.属性['usePanelInfo'] if 'usePanelInfo' in 自身.属性 else None
        if 用面板 is None:
            return True#默认 Conversation
        def 选面板(信息):
            '无活动面板才显示会话标题'
            if 'activePanelId' in 信息:
                return 信息['activePanelId'] is None
            return True
        return 用面板(选面板)#无活动面板

    def 读会话标题(自身,显示会话标题):
        '取当前会话标题'
        用会话=自身.属性['useSessions'] if 'useSessions' in 自身.属性 else None
        if 用会话 is None or 显示会话标题 is not True:#无或非会话主面
            return None
        def 选(状态):
            '有当前会话则返回其 title'
            当前=状态['current'] if 'current' in 状态 else None
            if 当前 is None:
                return None
            表=状态['byId'] if 'byId' in 状态 and 状态['byId'] is not None else {}
            项=表[当前] if 当前 in 表 else None
            if 项 is None:
                return None
            return 项['title'] if 'title' in 项 else None
        return 用会话(选)

    def 渲染(自身):
        '把标题写到页面'
        产品=自身.属性['productTitle'] if 'productTitle' in 自身.属性 else ''
        显示=自身.读是否显示会话标题()
        会话标题=自身.读会话标题(显示)
        标题=产品 if 会话标题 is None else str(会话标题)+' — '+str(产品)
        自身._上次标题=标题
        if 标题=='':
            return
        界面.page_title(标题)

    def __call__(自身,属性=None):
        '对齐 React 组件调用'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()
