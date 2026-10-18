from .覆盖层顶边距 import 覆盖层顶边距

__all__=['锚定边距','锚定最大高度','使用锚定最大高度']#仅中文公开名

锚定边距=12#与视口顶安全距

def 锚定最大高度(底边,设计封顶,边距=锚定边距):#夹取
    '按底边到视口顶的空间夹取；永不超设计封顶'
    边距=覆盖层顶边距(边距)
    可用=底边-边距#可用高度
    if 可用<0:#负
        可用=0#地板
    return 设计封顶 if 可用>设计封顶 else 可用#夹

def 使用锚定最大高度(元素,设计封顶,边距=锚定边距):
    '按元素底边夹高度，并在滚动和缩放时重测。滚动用捕获阶段。返回拆除函数'
    窗口=元素.ownerDocument.defaultView
    def 适配():
        '读当前底边，把 maxHeight 写回元素'
        底=元素.getBoundingClientRect().bottom
        元素.style.maxHeight=str(锚定最大高度(底,设计封顶,边距))+'px'
    适配()
    窗口.addEventListener('resize',适配)
    窗口.addEventListener('scroll',适配,True)
    def 拆除():
        '卸掉滚动和缩放'
        窗口.removeEventListener('resize',适配)
        窗口.removeEventListener('scroll',适配,True)
    return 拆除
