from ..复制反馈 import 复制反馈#复制反馈

__all__=['代码块']#仅中文公开名

class 代码块:#代码面
    """尾换行仅作终止符；复制写 trimmed。"""
    def __init__(自身,属性=None,**关键字参数):
        """合并 props。"""
        自身.属性=dict(属性 if 属性 is not None else {})#基础
        自身.属性.update(关键字参数)#覆盖
        自身.反馈=复制反馈()#复制

    def 更新(自身,属性):
        """刷新。"""
        自身.属性=dict(属性)#最新

    def 渲染(自身):
        """banner+plain/highlighted 材料。"""
        属性=自身.属性#props
        代码=属性['code'] if 'code' in 属性 and 属性['code'] is not None else ''#源
        修剪=代码[:-1] if 代码.endswith('\n') else 代码#剥终止
        语言=属性['lang'] if 'lang' in 属性 else None#语法提示
        自身.反馈.置文本(修剪)#可复制
        return {#视图
            'type':'code-block',#类型
            'code':修剪,#源
            'lang':语言,#语言
            'html':None,#宿主高亮后填
            'copied':自身.反馈.已复制,#反馈
            'copyLabel':属性['copyLabel'] if 'copyLabel' in 属性 else '复制',#闲
            'copiedLabel':属性['copiedLabel'] if 'copiedLabel' in 属性 else '复制成功',#成
            'onCopy':自身.反馈.复制,#复制
            'className':属性['className'] if 'className' in 属性 else None,#类
            'cssModule':'代码块.module.css',#样式
        }#结束

    def __call__(自身,属性=None,**关键字参数):
        """对齐 React。"""
        if 属性 is not None or len(关键字参数)>0:#有；判 length
            合并=dict(属性 if 属性 is not None else {})#基
            合并.update(关键字参数)#覆
            自身.更新(合并)#刷
        return 自身.渲染()#渲
