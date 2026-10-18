'右栏根：每个还留着的会话一棵子树，只有前台那棵显示'
from ....模块.客户端.通告 import 取握手窗口
import os
from ....ui_对话.异常 import 注入模块样式文件,标样式模块

__all__=['右栏根','会话视图壳']

样式路径=os.path.join(os.path.dirname(__file__),'右侧侧栏.module.css')
样式模块='sidebar-right'


def _窗口(属性):
    '调用方带来的窗口，否则用桥上的窗口'
    if isinstance(属性,dict) and 属性.get('window') is not None:
        return 属性['window']
    return 取握手窗口()


def _订(钩子,回调):
    '选择器钩子上挂着的订阅'
    订=getattr(钩子,'_subscribe',None)
    if callable(订):
        return 订(回调)
    return None


class 会话视图壳:
    '一个会话的包裹。挂上时向视图集报到，卸下时释放'

    def __init__(自身,窗口,视图,可见,属性):
        '画出这一会话的槽'
        自身.窗口=窗口
        自身.视图=视图
        自身.可见=可见
        自身.属性=属性
        自身.根=None
        自身.卸挂载=None
        自身.渲染()

    def 渲染(自身):
        '隐藏的会话留在树上，只是 hidden'
        文档=自身.窗口.document
        注入模块样式文件(文档,'右侧侧栏样式',样式路径,样式模块)
        if 自身.根 is None:
            自身.根=文档.createElement('div')
            自身.根.className='session'
            标样式模块(自身.根,样式模块)
        活动=自身.可见 and 自身.视图.get('selected') is True
        if 活动:
            自身.根.removeAttribute('hidden')
        else:
            自身.根.setAttribute('hidden','')
        自身.根.setAttribute('data-sidebar-right-session',str(自身.视图.get('sessionId')))
        挂载=自身.属性.get('mountView')
        if callable(挂载) and 自身.卸挂载 is None:
            自身.卸挂载=挂载(自身.视图.get('reference'))
        while 自身.根.firstChild is not None:
            自身.根.firstChild.remove()
        提供=自身.属性.get('SessionProvider')
        画槽=自身.属性.get('renderSlot')
        份额={
            'width':自身.属性.get('width'),
            'viewportWidth':自身.属性.get('viewportWidth'),
            'canShow':自身.属性.get('canShow'),
            'active':活动,
            'retainTab':自身.视图.get('retainTab'),
            'window':自身.窗口,
            'parent':自身.根,
        }
        子=None
        if callable(画槽):
            子=画槽('rightbar.session',份额)
        if callable(提供):
            子=提供({'session':自身.视图.get('reference'),'children':子,'window':自身.窗口,'parent':自身.根})
        if 子 is not None and getattr(子,'parentNode',None) is None and hasattr(子,'tagName'):
            自身.根.appendChild(子)
        elif 子 is not None and getattr(子,'根',None) is not None and getattr(子.根,'parentNode',None) is None:
            自身.根.appendChild(子.根)
        return 自身.根

    def 拆除(自身):
        '这一棵根卸载'
        if callable(自身.卸挂载):
            自身.卸挂载()
            自身.卸挂载=None


class 右栏根:
    '主列是对话时显示选中的会话，后台还有正文的会话留在树上'

    def __init__(自身,属性=None):
        '记下份额并画出'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.根=None
        自身.壳表={}
        自身._退订=[]
        自身.渲染()
        自身._订阅()

    def __call__(自身,属性=None):
        '再次绘制'
        if 属性 is not None:
            自身.属性=属性
        return 自身.渲染()

    def _订阅(自身):
        '视图或主面板变了就重画'
        def 变更():
            '还挂着才重画'
            if 自身.根 is not None and getattr(自身.根,'isConnected',True) is False:
                for 退 in 自身._退订:
                    退()
                自身._退订.clear()
                return
            自身.渲染()
        for 名 in ('useViews','usePanelInfo'):
            退=_订(自身.属性.get(名),变更)
            if 退 is not None:
                自身._退订.append(退)

    def 渲染(自身):
        '每个视图一棵壳'
        窗口=_窗口(自身.属性)
        文档=窗口.document
        if 自身.根 is None:
            自身.根=文档.createElement('div')
        用面板=自身.属性.get('usePanelInfo')
        可见=True
        if callable(用面板):
            def 取可见(信息):
                '主列没有别的面板才看得见'
                if not isinstance(信息,dict):
                    return True
                return 信息.get('activePanelId') is None
            可见=用面板(取可见) is not False
        用视图=自身.属性.get('useViews')
        视图表=()
        if callable(用视图):
            def 原样(值):
                '视图名单'
                return 值
            读到=用视图(原样)
            if isinstance(读到,(list,tuple)):
                视图表=读到
        还在=set()
        for 视图 in 视图表:
            标识=视图.get('sessionId')
            还在.add(标识)
            壳=自身.壳表.get(标识)
            if 壳 is None:
                壳=会话视图壳(窗口,视图,可见,自身.属性)
                自身.壳表[标识]=壳
                if 壳.根 is not None:
                    自身.根.appendChild(壳.根)
            else:
                壳.可见=可见
                壳.属性=自身.属性
                壳.视图=视图
                壳.渲染()
        for 标识 in list(自身.壳表):
            if 标识 not in 还在:
                自身.壳表[标识].拆除()
                节点=自身.壳表[标识].根
                if 节点 is not None:
                    节点.remove()
                del 自身.壳表[标识]
        父=自身.属性.get('parent')
        if 父 is not None and getattr(自身.根,'parentNode',None) is None:
            父.appendChild(自身.根)
        return 自身
