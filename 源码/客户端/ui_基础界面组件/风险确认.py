from .模态 import 处理模态
from .按钮 import 处理按钮

__all__=['风险确认','处理风险确认']#仅中文公开名

样式表='''
.风险确认{width:min(440px,100%);max-height:calc(100dvh - 48px);overflow:hidden;display:flex;flex-direction:column}
.风险警告{display:flex;align-items:flex-start;gap:10px;color:var(--dsw-alias-label-secondary);font-size:14px;line-height:22px}
.风险警告 .材料图标{flex:none;margin-top:2px;color:var(--dsw-alias-state-error-primary)}
.风险勾{display:flex;align-items:flex-start;gap:10px;margin-top:20px;color:var(--dsw-alias-label-primary);font-size:14px;line-height:22px}
'''

def 处理风险确认(window,属性):
    '打开时画出说明、勾选和取消确认。有 parent 就挂上去'
    文档=window.document
    if 文档.getElementById('风险确认样式') is None:
        样式=文档.createElement('style')
        样式.id='风险确认样式'
        样式.textContent=样式表
        文档.head.appendChild(样式)
    已认=属性['acknowledged'] is True if 'acknowledged' in 属性 else False#已勾选
    禁用=属性['disabled'] is True if 'disabled' in 属性 else False#禁用
    说明=属性['description'] if 'description' in 属性 else None#说明
    勾文=属性['acknowledgeLabel'] if 'acknowledgeLabel' in 属性 else None#勾选文案
    变更=属性['onAcknowledgedChange'] if 'onAcknowledgedChange' in 属性 else None#变更
    体=文档.createElement('div')
    体.className='风险确认'
    警告=文档.createElement('div')
    警告.className='风险警告'
    图=文档.createElement('span')
    图.className='材料图标'
    图.setAttribute('aria-hidden','true')
    图.textContent='warning'
    警告.appendChild(图)
    if isinstance(说明,str) and 说明!='':#说明
        字=文档.createElement('span')
        字.textContent=说明
        警告.appendChild(字)
    elif 说明 is not None and hasattr(说明,'渲染'):#组件
        if hasattr(说明,'属性') and isinstance(说明.属性,dict):
            说明.属性['window']=window
        节点=说明.渲染()
        if 节点 is not None and hasattr(节点,'tagName'):
            警告.appendChild(节点)
    体.appendChild(警告)
    文=勾文 if isinstance(勾文,str) else ''#文案
    勾=文档.createElement('label')
    勾.className='风险勾'
    框=文档.createElement('input')
    框.type='checkbox'
    框.checked=已认
    框.disabled=禁用
    if 变更 is not None:
        def 改了(事件):
            '把勾选结果交给回调'
            变更(框.checked)
        框.addEventListener('change',改了)
    勾字=文档.createElement('span')
    勾字.textContent=文
    勾.appendChild(框)
    勾.appendChild(勾字)
    体.appendChild(勾)
    共用={'window':window}
    取消=处理按钮(window,{**共用,
        'variant':'outline','className':'modalAction',
        'onClick':属性['onCancel'] if 'onCancel' in 属性 else None,
        'children':属性['cancelLabel'] if 'cancelLabel' in 属性 else None,
    })
    确认=处理按钮(window,{**共用,
        'variant':'primary','className':'confirmAction',
        'disabled':禁用 is True or 已认 is False,
        'onClick':属性['onConfirm'] if 'onConfirm' in 属性 else None,
        'children':属性['confirmLabel'] if 'confirmLabel' in 属性 else None,
    })
    return 处理模态(window,{
        'window':window,
        'open':属性['open'] if 'open' in 属性 else None,
        'onClose':属性['onCancel'] if 'onCancel' in 属性 else None,
        'title':属性['title'] if 'title' in 属性 else None,
        'className':'confirmation',
        'contentClassName':'confirmationContent',
        'footer':(取消,确认),
        'children':体,
        'parent':属性['parent'] if 'parent' in 属性 else None,
    } if 'parent' in 属性 else {
        'window':window,
        'open':属性['open'] if 'open' in 属性 else None,
        'onClose':属性['onCancel'] if 'onCancel' in 属性 else None,
        'title':属性['title'] if 'title' in 属性 else None,
        'className':'confirmation',
        'contentClassName':'confirmationContent',
        'footer':(取消,确认),
        'children':体,
    })

class 风险确认:#勾选门控确认
    '属主控制 acknowledged；组合模态页脚'
    def __init__(自身,属性=None,**关键字参数):
        '合并 props。构造不画'
        自身.属性=dict(属性 if 属性 is not None else {})#基础
        自身.属性.update(关键字参数)#覆盖
        自身.根=None

    def 更新(自身,属性):
        '刷新'
        自身.属性=dict(属性)#最新

    def 渲染(自身):
        '拆掉旧确认，再画一次'
        if 自身.根 is not None:
            自身.根.remove()
        自身.根=处理风险确认(自身.属性['window'],自身.属性)
        return 自身.根

    def __call__(自身,属性=None,**关键字参数):
        '对齐 React'
        if 属性 is not None or len(关键字参数)>0:#有；判 length
            合并=dict(属性 if 属性 is not None else {})#基
            合并.update(关键字参数)#覆
            自身.更新(合并)#刷
        return 自身.渲染()
