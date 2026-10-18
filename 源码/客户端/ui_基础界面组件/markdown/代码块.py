from ..复制反馈 import 复制反馈#复制反馈

__all__=['代码块','处理代码块','样式表']#仅中文公开名

样式表='''
.代码块{position:relative;width:100%;margin:16px 0;color:var(--dsw-alias-label-primary);background:var(--dsw-alias-markdown-code-block);border-radius:var(--dsw-radius-lg);overflow:hidden}
.代码横幅{width:100%;display:flex;align-items:center;justify-content:space-between;flex-wrap:nowrap;gap:12px;padding:9px 14px;box-sizing:border-box;background:var(--dsw-alias-markdown-code-block-banner)}
.代码语言{min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-family:var(--ds-font-family-code);font-size:11px;line-height:18px;color:var(--dsw-alias-label-primary)}
button.代码复制{height:auto;min-height:0;padding:0;border:0;background:transparent;box-shadow:none;color:inherit;font-size:11px;line-height:18px;cursor:pointer}
.代码块 pre{margin:0;padding:16px;overflow-x:auto;white-space:pre-wrap;word-break:break-all;background:var(--dsw-alias-markdown-code-block);font:var(--dsw-font-markdown-code-block)}
'''

def 处理代码块(window,属性):
    '画出语言、源码和复制。有 parent 就挂上去'
    文档=window.document
    if 文档.getElementById('代码块样式') is None:
        样式=文档.createElement('style')
        样式.id='代码块样式'
        样式.textContent=样式表
        文档.head.appendChild(样式)
    代码=属性['code'] if 'code' in 属性 and 属性['code'] is not None else ''#源
    修剪=代码[:-1] if 代码.endswith('\n') else 代码#剥终止
    语言=属性['lang'] if 'lang' in 属性 else None#语法提示
    组件=属性['组件'] if '组件' in 属性 else None
    if 组件 is not None:
        组件.反馈.置文本(修剪)#可复制
    闲=属性['copyLabel'] if 'copyLabel' in 属性 else '复制'#闲
    成=属性['copiedLabel'] if 'copiedLabel' in 属性 else '复制成功'#成
    if 闲 is None:#缺
        闲='复制'#默认
    if 成 is None:#缺
        成='复制成功'#默认
    根=文档.createElement('div')
    根.className='代码块'
    类名=属性['className'] if 'className' in 属性 else None#类
    if isinstance(类名,str) and 类名!='':
        根.className=根.className+' '+类名
    def 清空(节点):
        while 节点.firstElementChild is not None:
            节点.firstElementChild.remove()
    def 重画():
        '刷新复制文案'
        清空(根)
        已复制=组件.反馈.已复制 if 组件 is not None else False
        复制文=成 if 已复制 else 闲#文案
        def 点复制(事件):
            '写入剪贴板并换成已复制文案'
            if 组件 is not None:
                组件.反馈.复制()
            重画()
        幅=文档.createElement('div')
        幅.className='代码横幅'
        if 语言 is not None:#语言
            语=文档.createElement('span')
            语.className='代码语言'
            语.textContent=str(语言)
            幅.appendChild(语)
        钮=文档.createElement('button')
        钮.type='button'
        钮.className='代码复制'
        钮.textContent=复制文
        钮.addEventListener('click',点复制)
        幅.appendChild(钮)
        根.appendChild(幅)
        预=文档.createElement('pre')
        码=文档.createElement('code')
        码.textContent=修剪
        if isinstance(语言,str) and 语言!='':
            码.className='language-'+语言
        预.appendChild(码)
        根.appendChild(预)
    重画()#首画
    if 'parent' in 属性:
        属性['parent'].appendChild(根)
    return 根

class 代码块:#代码面
    '尾换行仅作终止符；复制写 trimmed'
    def __init__(自身,属性=None,**关键字参数):
        '合并 props。构造不画'
        自身.属性=dict(属性 if 属性 is not None else {})#基础
        自身.属性.update(关键字参数)#覆盖
        自身.反馈=复制反馈()#复制
        自身.根=None

    def 更新(自身,属性):
        '刷新'
        自身.属性=dict(属性)#最新

    def 渲染(自身):
        '拆掉旧块，再画一次'
        if 自身.根 is not None:
            自身.根.remove()
        绘制=dict(自身.属性)
        绘制['组件']=自身
        自身.根=处理代码块(自身.属性['window'],绘制)
        return 自身.根

    def __call__(自身,属性=None,**关键字参数):
        '对齐 React'
        if 属性 is not None or len(关键字参数)>0:#有；判 length
            合并=dict(属性 if 属性 is not None else {})#基
            合并.update(关键字参数)#覆
            自身.更新(合并)#刷
        return 自身.渲染()
