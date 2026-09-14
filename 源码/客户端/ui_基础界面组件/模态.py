__all__=['模态','保持毫秒']#仅中文公开名

保持毫秒=0#无自动关闭

class 模态:#全视口对话框
    """受控打开；关则返回 None。"""
    def __init__(自身,属性=None,**关键字参数):
        """合并 props。"""
        自身.属性=dict(属性 if 属性 is not None else {})#基础
        自身.属性.update(关键字参数)#覆盖

    def 更新(自身,属性):
        """刷新。"""
        自身.属性=dict(属性)#最新

    def 渲染(自身):
        """打开时出遮罩+卡片。"""
        属性=自身.属性#props
        打开=属性['open'] is True if 'open' in 属性 else False#开
        if 打开 is False:#关
            return None#不画
        无头=属性['headless'] is True if 'headless' in 属性 else False#无铬
        return {#模态
            'type':'modal',#类型
            'title':属性['title'] if 'title' in 属性 else '',#标题/aria
            'closeLabel':属性['closeLabel'] if 'closeLabel' in 属性 else 'Close',#关按钮
            'description':属性['description'] if 'description' in 属性 else None,#说明
            'children':属性['children'] if 'children' in 属性 else None,#体
            'footer':属性['footer'] if 'footer' in 属性 else None,#脚
            'className':属性['className'] if 'className' in 属性 else None,#卡类
            'contentClassName':属性['contentClassName'] if 'contentClassName' in 属性 else None,#内容类
            'headless':无头,#无头
            'onClose':属性['onClose'] if 'onClose' in 属性 else None,#关闭
            'cssModule':'模态.module.css',#样式
        }#视图结束

    def __call__(自身,属性=None,**关键字参数):
        """对齐 React。"""
        if 属性 is not None or len(关键字参数)>0:#有；判 length
            合并=dict(属性 if 属性 is not None else {})#基
            合并.update(关键字参数)#覆
            自身.更新(合并)#刷
        return 自身.渲染()#渲
