from ..模块.客户端.通告 import 取握手窗口
import os
from ..ui_对话.异常 import 注入模块样式文件,标样式模块

__all__=['菜单组','观察粘性菜单组']

样式模块='menu-group'
序号=0

class 菜单组:
    '带标题的菜单分组。标题 id 只属于这一份'
    def __init__(自身,属性=None):
        '记下标题和子行'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.根=None

    def 渲染(自身):
        '画出 group、起点哨兵和标题'
        global 序号
        if 自身.根 is not None:
            自身.根.remove()
        属性=自身.属性
        窗口=属性['window'] if 'window' in 属性 else 取握手窗口()
        文档=窗口.document
        注入模块样式文件(文档,'菜单组样式',os.path.join(os.path.dirname(__file__),'菜单组.module.css'),样式模块)
        序号=序号+1
        标题标识='menu-group-'+str(序号)
        根=文档.createElement('section')
        根.setAttribute('role','group')
        根.setAttribute('aria-labelledby',标题标识)
        根.setAttribute('data-menu-group','')
        根.className='group'
        标样式模块(根,样式模块)
        起=文档.createElement('span')
        起.setAttribute('aria-hidden','true')
        起.setAttribute('data-menu-group-start','')
        起.className='start'
        标样式模块(起,样式模块)
        题=文档.createElement('div')
        题.id=标题标识
        题.setAttribute('data-menu-group-heading','')
        题.className='heading'
        标样式模块(题,样式模块)
        题.textContent='' if 属性.get('label') is None else str(属性['label'])
        根.appendChild(起)
        根.appendChild(题)
        子=属性.get('children')
        if hasattr(子,'tagName'):
            根.appendChild(子)
        elif isinstance(子,(list,tuple)):
            for 项 in 子:
                if hasattr(项,'tagName'):
                    根.appendChild(项)
        if 'parent' in 属性 and 属性['parent'] is not None:
            属性['parent'].appendChild(根)
        自身.根=根
        return 根

def 观察粘性菜单组(视口):
    '标题在越过视口顶时标 data-stuck。没有观察器就保持透明。返回拆除函数'
    窗口=视口.ownerDocument.defaultView
    if getattr(窗口,'IntersectionObserver',None) is None or getattr(窗口,'ResizeObserver',None) is None:
        return lambda: None
    节列=视口.querySelectorAll(':scope > [data-menu-group]')
    组=[]
    下标=0
    while 下标<节列.length:
        节=节列.item(下标)
        题=节.querySelector(':scope > [data-menu-group-heading]')
        起=节.querySelector(':scope > [data-menu-group-start]')
        if 题 is not None and 起 is not None:
            组.append({'section':节,'heading':题,'start':起,'atTop':False,'above':False,'topTime':float('-inf'),'aboveTime':float('-inf')})
        下标=下标+1
    if len(组)==0:
        return lambda: None
    已拆=False
    条观察=None
    视口高=None
    def 画出(一项):
        '顶上且已越过才粘住'
        粘=一项['atTop'] and 一项['above']
        if 一项['heading'].hasAttribute('data-stuck')!=粘:
            if 粘:
                一项['heading'].setAttribute('data-stuck','')
            else:
                一项['heading'].removeAttribute('data-stuck')
    起点表={}
    节表={}
    for 一项 in 组:
        起点表[一项['start']]=一项
        节表[一项['section']]=一项
    def 起点回调(记录):
        '哨兵相对视口顶的位置'
        if 已拆:
            return
        for 条 in 记录:
            一项=起点表.get(条.target)
            if 一项 is None or 条.rootBounds is None or 条.time<一项['aboveTime']:
                continue
            一项['above']=条.boundingClientRect.top<条.rootBounds.top
            一项['aboveTime']=条.time
            画出(一项)
    起点观察=窗口.IntersectionObserver(起点回调,{'root':视口,'threshold':[0,1]})
    for 一项 in 组:
        起点观察.observe(一项['start'])
    def 尺寸回调(记录):
        '视口高度变了就重挂一条顶边观察'
        nonlocal 条观察,视口高
        if 已拆:
            return
        for 条 in 记录:
            if 条.target is not 视口:
                continue
            if 条.contentRect.height==视口高:
                continue
            视口高=条.contentRect.height
            if 条观察 is not None:
                条观察.disconnect()
            def 条回调(相交):
                '截面过顶边时更新粘住'
                if 已拆:
                    return
                for 交 in 相交:
                    一项=节表.get(交.target)
                    if 一项 is None or 交.rootBounds is None:
                        continue
                    顶=交.rootBounds.top
                    if 交.time>=一项['topTime']:
                        一项['atTop']=交.isIntersecting is True and 交.boundingClientRect.bottom>顶
                        一项['topTime']=交.time
                    if 交.time>=一项['aboveTime']:
                        一项['above']=交.boundingClientRect.top<顶
                        一项['aboveTime']=交.time
                    画出(一项)
            边距='0px 0px '+str(min(1,视口高)-视口高)+'px 0px'
            def 真正(相交,观察者=None):
                '过期的观察器不再改标题'
                if 已拆 or 条观察 is not 观察者:
                    return
                条回调(相交)
            这一份=窗口.IntersectionObserver(真正,{'root':视口,'rootMargin':边距,'threshold':0})
            条观察=这一份
            for 一项 in 组:
                这一份.observe(一项['section'])
    尺寸观察=窗口.ResizeObserver(尺寸回调)
    尺寸观察.observe(视口)
    def 拆除():
        '卸掉观察并清掉 data-stuck'
        nonlocal 已拆
        if 已拆:
            return
        已拆=True
        起点观察.disconnect()
        if 条观察 is not None:
            条观察.disconnect()
        尺寸观察.disconnect()
        for 一项 in 组:
            if 一项['heading'].hasAttribute('data-stuck'):
                一项['heading'].removeAttribute('data-stuck')
    return 拆除
