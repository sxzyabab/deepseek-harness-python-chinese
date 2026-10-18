from ..异常 import 贴出失败,列,换根,卸根,可画,叫槽,挂上

__all__=['会话面板','处理会话面板']#仅中文公开名

def 空渲染槽(*位置参数,**关键字参数):
    '未注入槽渲染时不画'
    return None#不画

def 处理会话面板(window,属性):
    '把 main 席转发给 main.conversation。有 parent 就挂上去'
    文档=window.document
    组件=属性['组件']
    渲染槽=组件.属性['renderSlot'] if 'renderSlot' in 组件.属性 else 空渲染槽
    根=列(文档,'会话面板')
    贴出失败(组件,文档,根)
    挂上(根,叫槽(渲染槽,'main.conversation',{},window))
    if 'parent' in 属性:
        属性['parent'].appendChild(根)
    return 根

class 会话面板:
    '把 main 席转发给 main.conversation。属性为 dict'

    def __init__(自身,属性=None):
        '记下宿主注入的 props。有 window 才画'
        自身.属性=属性 if 属性 is not None else {}#props
        自身.根=None
        if 可画(自身.属性):
            自身.渲染()#槽位只调用构造，这里就要画

    def 更新(自身,属性):
        '刷新合成 props'
        自身.属性=属性 if 属性 is not None else {}

    def 渲染(自身):
        '拆掉旧根，再画一次'
        份额=dict(自身.属性) if isinstance(自身.属性,dict) else {}
        份额['组件']=自身
        if 'window' not in 份额:
            卸根(自身)
            return None
        return 换根(自身,处理会话面板,份额)

    def __call__(自身,属性=None):
        '对齐组件调用'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()
