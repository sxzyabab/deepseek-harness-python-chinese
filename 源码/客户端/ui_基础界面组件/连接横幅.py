from nicegui import ui as 界面

__all__=['连接横幅','默认标签']#仅中文公开名

默认标签='连接已断开，正在重连…'#内置文案

class 连接横幅:#重连顶条
    '受控：reconnecting 为假则返回 None'
    def __init__(自身,属性=None,**关键字参数):
        '合并 props'
        自身.属性=dict(属性 if 属性 is not None else {})#基础
        自身.属性.update(关键字参数)#覆盖

    def 更新(自身,属性):
        '刷新'
        自身.属性=dict(属性)#最新

    def 渲染(自身):
        '断线时画出横幅'
        属性=自身.属性#props
        重连=属性['reconnecting'] is True if 'reconnecting' in 属性 else False#重连
        if 重连 is False:#已连
            return None#静默
        文=属性['label'] if 'label' in 属性 else 默认标签#文案
        if 文 is None:#缺
            文=默认标签#内置
        界面.label(文).classes('连接横幅')#横幅

    def __call__(自身,属性=None,**关键字参数):
        '对齐 React'
        if 属性 is not None or len(关键字参数)>0:#有；判 length
            合并=dict(属性 if 属性 is not None else {})#基
            合并.update(关键字参数)#覆
            自身.更新(合并)#刷
        return 自身.渲染()
