__all__=['连接横幅','处理连接横幅','默认标签']#仅中文公开名

默认标签='连接已断开，正在重连…'#内置文案

def 处理连接横幅(window,属性):
    '断线时画出横幅。已连接返回 None。有 parent 就挂上去'
    文档=window.document
    重连=属性['reconnecting'] is True if 'reconnecting' in 属性 else False#重连
    if 重连 is False:#已连
        return None#静默
    文=属性['label'] if 'label' in 属性 else 默认标签#文案
    if 文 is None:#缺
        文=默认标签#内置
    标=文档.createElement('div')
    标.className='连接横幅'
    标.textContent=文
    if 'parent' in 属性:
        属性['parent'].appendChild(标)
    return 标

class 连接横幅:#重连顶条
    '受控：reconnecting 为假则返回 None'
    def __init__(自身,属性=None,**关键字参数):
        '合并 props。构造不画'
        自身.属性=dict(属性 if 属性 is not None else {})#基础
        自身.属性.update(关键字参数)#覆盖
        自身.根=None

    def 更新(自身,属性):
        '刷新'
        自身.属性=dict(属性)#最新

    def 渲染(自身):
        '拆掉旧横幅，再画一次'
        if 自身.根 is not None:
            自身.根.remove()
        自身.根=处理连接横幅(自身.属性['window'],自身.属性)
        return 自身.根

    def __call__(自身,属性=None,**关键字参数):
        '对齐 React'
        if 属性 is not None or len(关键字参数)>0:#有；判 length
            合并=dict(属性 if 属性 is not None else {})#基
            合并.update(关键字参数)#覆
            自身.更新(合并)#刷
        return 自身.渲染()
