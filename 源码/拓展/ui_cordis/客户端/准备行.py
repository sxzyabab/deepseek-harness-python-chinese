from ....客户端.模块.客户端.通告 import 取握手窗口
from ....客户端.ui_对话.异常 import 标样式模块
from ....客户端.ui_基础界面组件.文字闪烁 import 文字闪烁

__all__=['准备行']

def 节点(文档,标签,类名,样式模块):
    '带本卡片样式模块的节点'
    元素=文档.createElement(标签)#元素
    if isinstance(类名,str) and 类名!='':#有类
        元素.className=类名#官方类名
    if isinstance(样式模块,str) and 样式模块!='':#有模块
        标样式模块(元素,样式模块)#接上样式
    return 元素#节点

class 准备行:
    '参数还没到时的工具前缀。不展开，标题按运行中闪烁'
    def __init__(自身,属性):
        '记下属性并画出'
        自身.属性=属性#宿主交来的属性
        自身.根=None#还没画
        自身.渲染()#首画

    def 更新(自身,属性):
        '换成新属性'
        自身.属性=属性#新属性

    def 拆除(自身):
        '没有订阅'
        return

    def 渲染(自身):
        '外层标工具名和准备中，里面是图标和标题'
        属性=自身.属性#当前属性
        if 'window' in 属性 and 属性['window'] is not None:#调用方窗口
            窗口=属性['window']#用它
        else:#没有单独窗口
            窗口=取握手窗口()#当前页
        文档=窗口.document#文档
        样式模块=属性.get('样式模块')#卡片样式模块
        外=文档.createElement('div')#数据属性在外层
        外.setAttribute('data-tool',属性.get('toolName') or '')#工具名
        外.setAttribute('data-state','preparing')#准备中
        外.setAttribute('aria-label','准备调用 Cordis 工具')#无障碍名
        卡=节点(文档,'div',属性.get('className'),样式模块)#卡片
        行=节点(文档,'div',属性.get('rowClassName'),样式模块)#一行
        行.style.display='flex'#披露行的横排。本节点挂的是卡片样式
        行.style.alignItems='center'#垂直居中
        行.style.minWidth='0'#允许收缩
        前导=文档.createElement('span')#图标座
        前导.style.display='inline-flex'#横排图标
        前导.style.marginRight='6px'#与标题的间距
        图标=属性.get('icon')#调用方画好的图标
        if 图标 is not None and hasattr(图标,'tagName'):#是节点
            前导.appendChild(图标)#放上
        行.appendChild(前导)#图标
        标题类=属性.get('titleClassName')#标题类
        题=节点(文档,'span',标题类,样式模块)#标题
        题.textContent=属性.get('title') or ''#中文标题
        闪=文字闪烁({'window':窗口,'active':True,'children':题})#运行中扫光
        闪根=闪.渲染()#闪烁节点
        if 闪根 is not None:#画出来了
            行.appendChild(闪根)#标题
        卡.appendChild(行)#行
        外.appendChild(卡)#卡片
        旧=自身.根#上一棵
        父=None#挂载点
        if 旧 is not None:#换掉
            父=旧.parentNode#记住位置
            旧.remove()#拆掉
        自身.根=外#新根
        if 父 is None and 'parent' in 属性:#宿主指定的父节点
            父=属性['parent']#用它
        if 父 is not None and 外.parentNode is not 父:#还没挂上
            父.appendChild(外)#挂上
        return 外#节点
