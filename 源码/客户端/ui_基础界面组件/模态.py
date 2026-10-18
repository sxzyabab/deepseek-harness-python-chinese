__all__=['模态','处理模态','保持毫秒','样式表']#仅中文公开名

样式表='''
.模态罩{position:fixed;inset:0;z-index:1200;display:flex;align-items:center;justify-content:center;background:rgb(0 0 0 / 32%)}
.模态{box-sizing:border-box;display:flex;flex-direction:column;gap:0;width:min(380px,100%);padding:0 0 24px;overflow:hidden;border-radius:var(--dsw-radius-panel);background:var(--dsw-alias-bg-layer-2);box-shadow:var(--dsw-elevation-prominent);color:var(--dsw-alias-label-primary)}
.模态头{width:100%;display:flex;align-items:center;justify-content:space-between;flex-wrap:nowrap;gap:8px;padding:22px 14px 12px 24px;box-sizing:border-box}
.模态题{margin:0;font-size:16px;line-height:24px;font-weight:500;color:var(--dsw-alias-label-primary)}
button.模态关{width:28px;height:28px;min-width:28px;min-height:28px;padding:0;border:0;border-radius:var(--dsw-radius-sm);background:transparent;box-shadow:none;color:var(--dsw-alias-label-secondary);cursor:pointer}
button.模态关:hover{background:var(--dsw-alias-interactive-bg-hover)}
.模态述{margin:0;padding:0 24px;font-size:14px;line-height:22px;color:var(--dsw-alias-label-primary)}
.模态体{width:100%;min-width:0;margin-top:20px;padding:0 24px;box-sizing:border-box;display:flex;flex-direction:column}
.模态脚{width:100%;display:flex;align-items:center;justify-content:flex-end;flex-wrap:nowrap;gap:8px;padding:0 24px;box-sizing:border-box}
'''

保持毫秒=0#无自动关闭

def 处理模态(window,属性):
    '打开时画出标题、正文和页脚。关则返回 None。有 parent 就挂上去'
    文档=window.document
    if 文档.getElementById('模态样式') is None:
        样式=文档.createElement('style')
        样式.id='模态样式'
        样式.textContent=样式表
        文档.head.appendChild(样式)
    打开=属性['open'] is True if 'open' in 属性 else False#开
    if 打开 is False:#关
        return None#不画
    无头=属性['headless'] is True if 'headless' in 属性 else False#无铬
    标题=属性['title'] if 'title' in 属性 else ''#标题
    if 标题 is None:#缺
        标题=''#空
    关文=属性['closeLabel'] if 'closeLabel' in 属性 else 'Close'#关按钮
    if 关文 is None or 关文=='':#缺
        关文='Close'#默认
    说明=属性['description'] if 'description' in 属性 else None#说明
    子=属性['children'] if 'children' in 属性 else None#体
    脚=属性['footer'] if 'footer' in 属性 else None#脚
    关闭=属性['onClose'] if 'onClose' in 属性 else None#关闭
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
    罩=文档.createElement('div')
    罩.className='模态罩'
    卡=文档.createElement('div')
    卡.className='模态'
    类名=属性['className'] if 'className' in 属性 else None#卡类
    if isinstance(类名,str) and 类名!='':
        卡.className=卡.className+' '+类名
    内容类=属性['contentClassName'] if 'contentClassName' in 属性 else None#内容类
    体=文档.createElement('div')
    if isinstance(内容类,str) and 内容类!='':
        体.className=内容类
    if 无头 is False:
        头=文档.createElement('div')
        头.className='模态头'
        if isinstance(标题,str) and 标题!='':#标题
            题=文档.createElement('div')
            题.className='模态题'
            题.textContent=标题
            头.appendChild(题)
        elif hasattr(标题,'渲染'):#组件标题
            画子(标题,头)
        def 点关(事件):
            '调用关闭'
            if 关闭 is not None:
                关闭()
        关钮=文档.createElement('button')
        关钮.type='button'
        关钮.className='模态关'
        关钮.textContent=关文
        关钮.addEventListener('click',点关)
        头.appendChild(关钮)
        体.appendChild(头)
        if isinstance(说明,str) and 说明!='':#说明
            述=文档.createElement('div')
            述.className='模态述'
            述.textContent=说明
            体.appendChild(述)
        elif 说明 is not None and hasattr(说明,'渲染'):#组件说明
            画子(说明,体)
    正文=文档.createElement('div')
    正文.className='模态体'
    画子(子,正文)
    体.appendChild(正文)
    if 脚 is not None:
        脚盒=文档.createElement('div')
        脚盒.className='模态脚'
        画子(脚,脚盒)
        体.appendChild(脚盒)
    卡.appendChild(体)
    罩.appendChild(卡)
    if 'parent' in 属性:
        属性['parent'].appendChild(罩)
    return 罩

class 模态:#全视口对话框
    '受控打开；关则返回 None'
    def __init__(自身,属性=None,**关键字参数):
        '合并 props。构造不画'
        自身.属性=dict(属性 if 属性 is not None else {})#基础
        自身.属性.update(关键字参数)#覆盖
        自身.根=None

    def 更新(自身,属性):
        '刷新'
        自身.属性=dict(属性)#最新

    def 渲染(自身):
        '拆掉旧对话框，再画一次'
        if 自身.根 is not None:
            自身.根.remove()
        自身.根=处理模态(自身.属性['window'],自身.属性)
        return 自身.根

    def __call__(自身,属性=None,**关键字参数):
        '对齐 React'
        if 属性 is not None or len(关键字参数)>0:#有；判 length
            合并=dict(属性 if 属性 is not None else {})#基
            合并.update(关键字参数)#覆
            自身.更新(合并)#刷
        return 自身.渲染()
