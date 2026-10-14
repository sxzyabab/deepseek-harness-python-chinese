from nicegui import ui as 界面
from ..复制反馈 import 复制反馈#复制反馈

__all__=['代码块','样式表']#仅中文公开名

样式表='''
.代码块{position:relative;width:100%;margin:16px 0;color:var(--dsw-alias-label-primary);background:var(--dsw-alias-markdown-code-block);border-radius:var(--dsw-radius-lg);overflow:hidden}
.代码横幅{width:100%;align-items:center;justify-content:space-between;flex-wrap:nowrap;gap:12px;padding:9px 14px;box-sizing:border-box;background:var(--dsw-alias-markdown-code-block-banner)}
.代码语言{min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-family:var(--ds-font-family-code);font-size:11px;line-height:18px;color:var(--dsw-alias-label-primary)}
button.q-btn.代码复制{height:auto;min-height:0;padding:0;background:transparent !important;box-shadow:none !important;color:inherit !important;font-size:11px;line-height:18px}
.代码块 pre,.代码块 .q-markdown pre{margin:0 !important;padding:16px;overflow-x:auto;white-space:pre-wrap;word-break:break-all;background:var(--dsw-alias-markdown-code-block);font:var(--dsw-font-markdown-code-block)}
'''

样式已登记=False

def 登记样式():
    '同一段样式整个进程只登记一次'
    global 样式已登记
    if 样式已登记 is True:
        return
    界面.add_css(样式表)
    样式已登记=True

class 代码块:#代码面
    '尾换行仅作终止符；复制写 trimmed'
    def __init__(自身,属性=None,**关键字参数):
        '合并 props'
        自身.属性=dict(属性 if 属性 is not None else {})#基础
        自身.属性.update(关键字参数)#覆盖
        自身.反馈=复制反馈()#复制

    def 更新(自身,属性):
        '刷新'
        自身.属性=dict(属性)#最新

    def 渲染(自身):
        '画出语言、源码和复制'
        登记样式()
        属性=自身.属性#props
        代码=属性['code'] if 'code' in 属性 and 属性['code'] is not None else ''#源
        修剪=代码[:-1] if 代码.endswith('\n') else 代码#剥终止
        语言=属性['lang'] if 'lang' in 属性 else None#语法提示
        自身.反馈.置文本(修剪)#可复制
        闲=属性['copyLabel'] if 'copyLabel' in 属性 else '复制'#闲
        成=属性['copiedLabel'] if 'copiedLabel' in 属性 else '复制成功'#成
        if 闲 is None:#缺
            闲='复制'#默认
        if 成 is None:#缺
            成='复制成功'#默认
        根=界面.column().classes('代码块')#块
        类名=属性['className'] if 'className' in 属性 else None#类
        if isinstance(类名,str) and 类名!='':
            根.classes(类名)#附
        def 重画():
            '刷新复制文案'
            根.clear()
            with 根:#内容
                复制文=成 if 自身.反馈.已复制 else 闲#文案
                def 点复制():
                    '写入剪贴板并换成已复制文案'
                    自身.反馈.复制()#复制
                    重画()#重画
                with 界面.row().classes('代码横幅'):#横幅
                    if 语言 is not None:#语言
                        界面.label(str(语言)).classes('代码语言')#语言
                    界面.button(复制文,on_click=点复制).props('flat no-caps').classes('代码复制')#复制
                if isinstance(语言,str) and 语言!='':
                    界面.code(修剪,language=语言)#源码
                else:#纯文本
                    界面.code(修剪)#源码
        重画()#首画

    def __call__(自身,属性=None,**关键字参数):
        '对齐 React'
        if 属性 is not None or len(关键字参数)>0:#有；判 length
            合并=dict(属性 if 属性 is not None else {})#基
            合并.update(关键字参数)#覆
            自身.更新(合并)#刷
        return 自身.渲染()
