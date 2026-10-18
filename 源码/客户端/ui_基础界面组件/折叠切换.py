from ..模块.客户端.通告 import 取握手窗口

__all__=['折叠切换']

class 折叠切换:
    '头尾封顶的展开按钮。文案由调用方的 labels 提供'
    def __init__(自身,属性=None):
        '记下展开态和标签'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.根=None

    def 渲染(自身):
        '画出展开或收起按钮'
        if 自身.根 is not None:
            自身.根.remove()
        属性=自身.属性
        窗口=属性['window'] if 'window' in 属性 else 取握手窗口()
        文档=窗口.document
        已展开=属性.get('expanded') is True
        隐藏=属性.get('hidden') if 属性.get('hidden') is not None else 0
        标签=属性['labels'] if 'labels' in 属性 and isinstance(属性['labels'],dict) else {}
        钮=文档.createElement('button')
        钮.type='button'
        类名=属性.get('className')
        if isinstance(类名,str) and 类名!='':
            钮.className=类名
        钮.setAttribute('aria-expanded','true' if 已展开 else 'false')
        if 已展开:
            钮.setAttribute('aria-label','' if 标签.get('collapseAria') is None else str(标签['collapseAria']))
            钮.textContent='' if 标签.get('collapse') is None else str(标签['collapse'])
        else:
            展=标签.get('expandAria')
            钮.setAttribute('aria-label',展(隐藏) if callable(展) else ('' if 展 is None else str(展)))
            正文=标签.get('expand')
            钮.textContent=正文(隐藏) if callable(正文) else ('' if 正文 is None else str(正文))
        def 点下(事件):
            '交给 onToggle'
            切=属性.get('onToggle')
            if 切 is not None:
                切()
        钮.addEventListener('click',点下)
        if 'parent' in 属性 and 属性['parent'] is not None:
            属性['parent'].appendChild(钮)
        自身.根=钮
        return 自身.根
