__all__=['按钮','处理按钮','变体表','尺寸表','样式表']#仅中文公开名

样式表='''
.按钮{box-sizing:border-box;display:inline-flex;align-items:center;justify-content:center;gap:4px;height:36px;min-height:36px;padding:0 14px;border:none;border-radius:var(--dsw-radius-md);background:transparent;box-shadow:none;color:var(--dsw-alias-label-primary);font-size:14px;line-height:22px;cursor:pointer}
.按钮.sm{height:28px;min-height:28px;font-size:12px;line-height:18px;padding:0 10px;border-radius:var(--dsw-radius-sm)}
.按钮.primary{background:var(--dsw-alias-button-primary-fill);color:var(--dsw-alias-label-primary-foreground)}
.按钮.primary:hover{background:var(--dsw-alias-button-primary-hover)}
.按钮.ghost:hover{background:var(--dsw-alias-interactive-bg-hover)}
.按钮.outline{border:0.5px solid var(--dsw-alias-border-l3)}
.按钮.outline:hover{background:var(--dsw-alias-interactive-bg-hover)}
.按钮.toolbar{background:var(--dsw-alias-button-tool-bar-fill)}
.按钮.toolbar:hover{background:var(--dsw-alias-button-tool-bar-hover)}
.按钮:disabled,.按钮[aria-disabled=true]{opacity:0.4}
.材料图标{display:inline-flex;align-items:center;justify-content:center}
'''

变体表=('primary','ghost','outline','toolbar')#视觉变体
尺寸表=('md','sm')#尺寸

def 处理按钮(window,属性):
    '按变体和尺寸画出按钮、图标和子内容。有 parent 就挂上去'
    文档=window.document
    if 文档.getElementById('按钮样式') is None:
        样式=文档.createElement('style')
        样式.id='按钮样式'
        样式.textContent=样式表
        文档.head.appendChild(样式)
    变体=属性.get('variant','ghost')#变体
    尺寸=属性.get('size','md')#尺寸
    if 变体 not in 变体表:#非法
        变体='ghost'#退回
    if 尺寸 not in 尺寸表:#非法
        尺寸='md'#退回
    子=属性.get('children')#子内容
    点击=属性.get('onClick')#点击
    禁用=bool(属性.get('disabled'))#禁用
    图标=属性.get('icon')#图标
    图标名=None#材料图标名
    if isinstance(图标,str) and 图标!='':
        尾=图标.rsplit('-',1)[-1]#尺寸后缀
        图标名=图标.rsplit('-',1)[0] if 尾.isdigit() else 图标#去掉尺寸后缀
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
        if hasattr(内容,'tagName'):#已是节点
            父.appendChild(内容)
            return
        if hasattr(内容,'渲染'):#组件
            if hasattr(内容,'属性') and isinstance(内容.属性,dict):
                内容.属性['window']=window
            节点=内容.渲染()
            if 节点 is not None and hasattr(节点,'tagName'):
                父.appendChild(节点)
    def 画图标(父):
        '前导图标'
        if 图标名 is None:
            return
        图=文档.createElement('span')
        图.className='材料图标'
        图.setAttribute('aria-hidden','true')
        图.textContent=图标名
        父.appendChild(图)
    文案=None#按钮文字
    if isinstance(子,str):#字面
        文案=子#用
    elif isinstance(子,(list,tuple)) and all(isinstance(项,str) for 项 in 子):#全是字
        文案=''.join(子)#拼
    类名=属性.get('className')#附加类
    类串='按钮 '+变体+' '+尺寸#基础类
    if isinstance(类名,str) and 类名!='':
        类串=类串+' '+类名#附
    if isinstance(文案,str) or 子 is None:#文字或空按钮
        钮=文档.createElement('button')
        钮.type='button'
        钮.className=类串
        钮.disabled=禁用
        画图标(钮)
        if 文案 is not None:
            字=文档.createElement('span')
            字.textContent=文案
            钮.appendChild(字)
        if 点击 is not None:
            def 点下(事件):
                '有点击回调就调用'
                点击()
            钮.addEventListener('click',点下)
        if 'parent' in 属性:
            属性['parent'].appendChild(钮)
        return 钮
    行=文档.createElement('div')
    行.className=类串
    if 禁用:
        行.setAttribute('aria-disabled','true')
    if 点击 is not None and 禁用 is False:#可点
        def 点下(事件):
            '有点击回调就调用'
            点击()
        行.addEventListener('click',点下)
    画图标(行)
    画子(子,行)
    if 'parent' in 属性:
        属性['parent'].appendChild(行)
    return 行

class 按钮:#按钮原子
    '画出按钮、图标和子内容'
    def __init__(自身,属性=None,**关键字参数):#构造
        '合并 props。构造不画'
        自身.属性=dict(属性 or {})#基础
        自身.属性.update(关键字参数)#覆盖
        自身.根=None

    def 更新(自身,属性):#props 变更
        '刷新'
        自身.属性=dict(属性)#最新

    def 渲染(自身):#画出按钮
        '拆掉旧按钮，再画一次'
        if 自身.根 is not None:
            自身.根.remove()
        自身.根=处理按钮(自身.属性['window'],自身.属性)
        return 自身.根

    def __call__(自身,属性=None,**关键字参数):#组件调用形
        '对齐 React 调用'
        if 属性 is not None or 关键字参数:
            合并=dict(属性 or {})#基础
            合并.update(关键字参数)#覆盖
            自身.更新(合并)#刷新
        return 自身.渲染()
