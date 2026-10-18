__all__=['输入','处理输入','样式表']#仅中文公开名

样式表='''
.输入{display:inline-flex;align-items:center;gap:6px;height:32px;padding:0 8px;border:0.5px solid var(--dsw-alias-border-l4);border-radius:var(--dsw-radius-md);background:var(--dsw-alias-bg-layer-1)}
.输入:focus-within{border-color:var(--dsw-alias-state-business-primary)}
.输入 .材料图标{width:16px;height:16px;color:var(--dsw-alias-label-tertiary)}
input.输入框{flex:1;min-width:0;height:22px;margin:0;padding:0;border:0;background:transparent;font-size:14px;line-height:22px;color:var(--dsw-alias-label-primary);outline:none}
input.输入框::placeholder{color:var(--dsw-alias-label-dimmed)}
'''

def 处理输入(window,属性):
    '画出前导图标和单行输入。有 parent 就挂上去'
    文档=window.document
    if 文档.getElementById('输入样式') is None:
        样式=文档.createElement('style')
        样式.id='输入样式'
        样式.textContent=样式表
        文档.head.appendChild(样式)
    图标=属性['icon'] if 'icon' in 属性 else None#图标
    值=属性['value'] if 'value' in 属性 and 属性['value'] is not None else ''#值
    占位=属性['placeholder'] if 'placeholder' in 属性 and 属性['placeholder'] is not None else ''#占位
    种类=属性['type'] if 'type' in 属性 and 属性['type'] is not None else 'text'#类型
    禁用=属性['disabled'] is True if 'disabled' in 属性 else False#禁用
    只读=属性['readOnly'] is True if 'readOnly' in 属性 else False#只读
    变更=属性['onChange'] if 'onChange' in 属性 else None#变更
    if 变更 is None and 'onInput' in 属性:#输入回调
        变更=属性['onInput']#改用
    类名=属性['className'] if 'className' in 属性 else None#类
    行=文档.createElement('div')
    行.className='输入'
    if isinstance(类名,str) and 类名!='':
        行.className=行.className+' '+类名
    if isinstance(图标,str) and 图标!='':
        尾=图标.rsplit('-',1)[-1]#尺寸后缀
        图标名=图标.rsplit('-',1)[0] if 尾.isdigit() else 图标#去掉尺寸后缀
        图=文档.createElement('span')
        图.className='材料图标'
        图.setAttribute('aria-hidden','true')
        图.textContent=图标名
        行.appendChild(图)
    框=文档.createElement('input')
    框.className='输入框'
    框.type='password' if 种类=='password' else 'text'
    框.value=str(值)
    框.placeholder=占位
    框.disabled=禁用
    框.readOnly=只读
    if 变更 is not None:
        def 改了(事件):
            '把当前文字交给变更回调'
            变更(框.value)
        框.addEventListener('input',改了)
    行.appendChild(框)
    if 'parent' in 属性:
        属性['parent'].appendChild(行)
    return 行

class 输入:#文本输入
    '可选前导图标的单行输入'
    def __init__(自身,属性=None,**关键字参数):
        '合并 props。构造不画'
        自身.属性=dict(属性 if 属性 is not None else {})#基础
        自身.属性.update(关键字参数)#覆盖
        自身.根=None

    def 更新(自身,属性):
        '刷新'
        自身.属性=dict(属性)#最新

    def 渲染(自身):
        '拆掉旧输入，再画一次'
        if 自身.根 is not None:
            自身.根.remove()
        自身.根=处理输入(自身.属性['window'],自身.属性)
        return 自身.根

    def __call__(自身,属性=None,**关键字参数):
        '对齐 React'
        if 属性 is not None or len(关键字参数)>0:#有；判 length
            合并=dict(属性 if 属性 is not None else {})#基
            合并.update(关键字参数)#覆
            自身.更新(合并)#刷
        return 自身.渲染()
