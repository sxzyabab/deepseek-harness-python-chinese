import builtins

__all__=['观察控件行']

def 观察控件行(行):
    """仅当展开控件无法同行时折叠模型文本；每次通知同步测量。"""
    def 测量():
        """按展开需求测量，含折叠期间已改文本。"""
        行.removeAttribute('data-model-compact')
        样式=builtins.getComputedStyle(行)
        可用=行.getBoundingClientRect().width-float(样式.paddingLeft)-float(样式.paddingRight)
        宽度表=[子.getBoundingClientRect().width for 子 in 行.children]
        宽度表=[宽 for 宽 in 宽度表 if 宽>0]
        间隙=float(样式.columnGap)
        需要=sum(宽度表)+max(0,len(宽度表)-1)*间隙
        行.toggleAttribute('data-model-compact',需要>可用)
    尺寸观察=builtins.ResizeObserver(测量)
    尺寸观察.observe(行)
    for 子 in 行.children:
        尺寸观察.observe(子)
    变动观察=builtins.MutationObserver(测量)
    变动观察.observe(行,{
        'subtree':True,'childList':True,'characterData':True,
        'attributes':True,'attributeFilter':['hidden'],
    })
    字体=builtins.document.fonts
    字体.addEventListener('loadingdone',测量)
    测量()
    def 拆除():
        """断开布局观察与字体监听。"""
        尺寸观察.disconnect()
        变动观察.disconnect()
        字体.removeEventListener('loadingdone',测量)
    return 拆除
