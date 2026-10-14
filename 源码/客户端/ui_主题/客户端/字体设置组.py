from nicegui import ui as 界面
from .字号行 import 字号行
from .字体族行 import 字体族行

__all__=['字体设置组']

class 字体设置组:
    '正文字号行，展开后是三种字体和代码、终端字号。每次挂上时收起'
    def __init__(自身,属性):
        '记下写入面。展开状态每次新建都是收起。槽位只调用构造，键齐了就画。'
        自身.属性=属性
        自身.展开=False
        if isinstance(属性,dict) and 't' in 属性 and 'useStore' in 属性 and 'setFontSize' in 属性 and 'setFontFamily' in 属性:
            自身.渲染()

    def 更新(自身,属性):
        '刷新合成 props'
        自身.属性=属性

    def 渲染(自身):
        '先画正文字号和展开钮，区域里放其余四行'
        区域号='font-settings-more'
        展开态={'open':自身.展开,'controls':区域号}
        区域=界面.column()
        区域.set_visibility(自身.展开)
        区域.props('id='+区域号)
        def 切换():
            '展开或收起其余字体行'
            自身.展开=not 自身.展开
            展开态['open']=自身.展开
            区域.set_visibility(自身.展开)
        展开态['onToggle']=切换
        def 写字号(角色):
            '收成该角色的单参写入'
            def 写入(像素,某=角色):
                自身.属性['setFontSize'](某,像素)
            return 写入
        def 写字体(角色):
            '收成该角色的字体列表写入'
            def 写入(值,某=角色):
                自身.属性['setFontFamily'](某,值)
            return 写入
        共用={'t':自身.属性['t'],'useStore':自身.属性['useStore']}
        字号行({**共用,'role':'text','setFontSize':写字号('text'),'expander':展开态}).渲染()
        with 区域:
            字体族行({**共用,'role':'text','setFontFamily':写字体('text')}).渲染()
            字体族行({**共用,'role':'code','setFontFamily':写字体('code')}).渲染()
            字号行({**共用,'role':'code','setFontSize':写字号('code')}).渲染()
            字体族行({**共用,'role':'terminal','setFontFamily':写字体('terminal')}).渲染()
            字号行({**共用,'role':'terminal','setFontSize':写字号('terminal')}).渲染()

    def __call__(自身,属性=None):
        '对齐组件调用'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()
