__all__=['披露行','处理披露行','样式表']#仅中文公开名

样式表='''
.披露行{display:flex;flex-direction:column;width:100%;min-width:0}
button.披露头{width:100%;height:calc(24px + var(--dsh-content-font-delta,0px));min-height:0;padding:0;border:0;justify-content:flex-start;align-items:center;gap:6px;border-radius:var(--dsw-radius-sm);background:transparent;box-shadow:none;color:var(--dsw-alias-label-tertiary);font-size:var(--dsh-content-font-size-secondary,13px);font-weight:400;line-height:calc(24px + var(--dsh-content-font-delta,0px));cursor:pointer;display:flex;text-align:left}
button.披露头:hover{color:var(--dsw-alias-label-secondary);background:transparent}
'''

def 处理披露行(window,属性):
    '画出标题，打开时画出子内容。有 parent 就挂上去'
    文档=window.document
    if 文档.getElementById('披露行样式') is None:
        样式=文档.createElement('style')
        样式.id='披露行样式'
        样式.textContent=样式表
        文档.head.appendChild(样式)
    可展=属性['expandable'] is True if 'expandable' in 属性 else False#可展
    打开=属性['open'] is True if 'open' in 属性 else False#开
    保持=属性['keepContentWhenOpen'] is True if 'keepContentWhenOpen' in 属性 else False#开时仍画折叠内容
    标题=属性['title'] if 'title' in 属性 else ''#标题
    if 标题 is None:#缺
        标题=''#空
    图标=属性['icon'] if 'icon' in 属性 else None#图标
    折叠=属性['collapsedContent'] if 'collapsedContent' in 属性 else None#折叠侧
    子=属性['children'] if 'children' in 属性 else None#展开子
    切换=属性['onToggle'] if 'onToggle' in 属性 else None#切换
    根=文档.createElement('div')
    根.className='披露行'
    类名=属性['className'] if 'className' in 属性 else None#根类
    if isinstance(类名,str) and 类名!='':
        根.className=根.className+' '+类名
    态={'开':打开}#本地开合
    def 清空(节点):
        while 节点.firstElementChild is not None:
            节点.firstElementChild.remove()
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
    def 重画():
        '按开合重画'
        清空(根)
        前='▾ ' if 态['开'] else '▸ '#箭头
        行类=属性['rowClassName'] if 'rowClassName' in 属性 else None#行类
        if 可展:#可展
            def 点切换(事件):
                '翻转并通知'
                态['开']=not 态['开']#翻
                if 切换 is not None:
                    切换()#调用
                重画()#重画
            钮=文档.createElement('button')
            钮.type='button'
            钮.className='披露头'
            钮.textContent=前+标题
            if isinstance(行类,str) and 行类!='':#行类
                钮.className=钮.className+' '+行类
            钮.addEventListener('click',点切换)
            根.appendChild(钮)
        elif 标题!='':#仅标题
            题=文档.createElement('div')
            题.textContent=标题
            根.appendChild(题)
        if isinstance(图标,str) and 图标!='':#图标
            尾=图标.rsplit('-',1)[-1]#尺寸后缀
            图标名=图标.rsplit('-',1)[0] if 尾.isdigit() else 图标#去掉尺寸后缀
            图=文档.createElement('span')
            图.className='材料图标'
            图.setAttribute('aria-hidden','true')
            图.textContent=图标名
            根.appendChild(图)
        if 态['开'] is False or 保持 is True:#折叠侧
            画子(折叠,根)#折叠内容
        if 态['开'] is True:#展开
            画子(子,根)#子内容
    重画()#首画
    if 'parent' in 属性:
        属性['parent'].appendChild(根)
    return 根

class 披露行:#披露头+受控展开体
    '结构化视图；宿主渲染真实 DOM'
    def __init__(自身,属性=None,**关键字参数):
        '合并 props。构造不画'
        自身.属性=dict(属性 if 属性 is not None else {})#基础
        自身.属性.update(关键字参数)#覆盖
        自身.根=None

    def 更新(自身,属性):
        '刷新'
        自身.属性=dict(属性)#最新

    def 渲染(自身):
        '拆掉旧行，再画一次'
        if 自身.根 is not None:
            自身.根.remove()
        自身.根=处理披露行(自身.属性['window'],自身.属性)
        return 自身.根

    def __call__(自身,属性=None,**关键字参数):
        '对齐 React'
        if 属性 is not None or len(关键字参数)>0:#有；判 length
            合并=dict(属性 if 属性 is not None else {})#基
            合并.update(关键字参数)#覆
            自身.更新(合并)#刷
        return 自身.渲染()
