__all__=['胶囊','处理胶囊','样式表']#仅中文公开名

样式表='''
.胶囊{display:inline-flex;align-items:center;gap:4px;height:24px;padding:0 8px;border:none;border-radius:999px;font-size:12px;line-height:18px;color:var(--dsw-alias-label-secondary);background:var(--dsw-alias-bg-layer-2)}
button.胶囊{min-height:24px;cursor:pointer}
button.胶囊:hover{background:var(--dsw-alias-interactive-bg-hover)}
.胶囊.选中,button.胶囊.选中{color:var(--dsw-alias-label-primary);background:var(--dsw-alias-button-ghost-active-fill);box-shadow:inset 0 0 0 1px var(--dsw-alias-button-ghost-active-border)}
'''

def 处理胶囊(window,属性):
    '有点击画按钮，否则画标签。有 parent 就挂上去'
    文档=window.document
    if 文档.getElementById('胶囊样式') is None:
        样式=文档.createElement('style')
        样式.id='胶囊样式'
        样式.textContent=样式表
        文档.head.appendChild(样式)
    点击=属性.get('onClick')#点击
    可点=点击 is not None
    子=属性.get('children')#子内容
    选中=bool(属性.get('active'))#选中
    def 画子(内容,父):
        '字符串做标签，组件自己画'
        if 内容 is None:#无
            return
        if isinstance(内容,str):#文案
            标=文档.createElement('span')
            标.textContent=内容
            父.appendChild(标)
            return
        if isinstance(内容,(list,tuple)):#多项
            for 项 in 内容:#逐项
                画子(项,父)#递归
            return
        if hasattr(内容,'tagName'):
            父.appendChild(内容)
            return
        if hasattr(内容,'渲染'):#组件
            if hasattr(内容,'属性') and isinstance(内容.属性,dict):
                内容.属性['window']=window
            节点=内容.渲染()
            if 节点 is not None and hasattr(节点,'tagName'):
                父.appendChild(节点)
    类名=属性.get('className')#附加类
    类串='胶囊'+(' 选中' if 选中 else '')#基础类
    if isinstance(类名,str) and 类名!='':
        类串=类串+' '+类名#附
    文案=None#文字
    if isinstance(子,str):#字面
        文案=子#用
    elif isinstance(子,(list,tuple)) and all(isinstance(项,str) for 项 in 子):#全是字
        文案=''.join(子)#拼
    if 可点:#按钮
        if isinstance(文案,str) or 子 is None:#文字或空胶囊
            钮=文档.createElement('button')
            钮.type='button'
            钮.className=类串
            钮.textContent='' if 文案 is None else 文案
            def 点下(事件):
                '调用点击'
                点击()
            钮.addEventListener('click',点下)
            if 'parent' in 属性:
                属性['parent'].appendChild(钮)
            return 钮
        行=文档.createElement('div')
        行.className=类串
        def 点下(事件):
            '调用点击'
            点击()
        行.addEventListener('click',点下)
        画子(子,行)
        if 'parent' in 属性:
            属性['parent'].appendChild(行)
        return 行
    if isinstance(文案,str) or 子 is None:#纯文字或空胶囊
        标=文档.createElement('span')
        标.className=类串
        标.textContent='' if 文案 is None else 文案
        if 'parent' in 属性:
            属性['parent'].appendChild(标)
        return 标
    行=文档.createElement('div')
    行.className=类串
    画子(子,行)
    if 'parent' in 属性:
        属性['parent'].appendChild(行)
    return 行

class 胶囊:#标签芯片
    '画出胶囊文案；有点击时做成按钮'
    def __init__(自身,属性=None,**关键字参数):#构造
        '合并 props。构造不画'
        自身.属性=dict(属性 or {})#基础
        自身.属性.update(关键字参数)#覆盖
        自身.根=None

    def 更新(自身,属性):#props 变更
        '刷新'
        自身.属性=dict(属性)#最新

    def 渲染(自身):#画出胶囊
        '拆掉旧胶囊，再画一次'
        if 自身.根 is not None:
            自身.根.remove()
        自身.根=处理胶囊(自身.属性['window'],自身.属性)
        return 自身.根

    def __call__(自身,属性=None,**关键字参数):#组件调用形
        '对齐 React 调用'
        if 属性 is not None or 关键字参数:
            合并=dict(属性 or {})#基础
            合并.update(关键字参数)#覆盖
            自身.更新(合并)#刷新
        return 自身.渲染()
