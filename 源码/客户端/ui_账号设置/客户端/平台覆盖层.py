'桌面平台页。远程内容和凭证在原生子视图里'
from ...模块.客户端.通告 import 取握手窗口
import os
from ...ui_对话.异常 import 注入模块样式文件
from ...ui_基础界面组件 import 按钮
from ...ui_基础界面组件.icons import 图标左chevron14
from .覆盖层惰性 import 取得覆盖层惰性
from .文案 import 中文

__all__=['平台覆盖层']

样式模块='平台覆盖层'

def 接上(结果,成功,失败):
    '原生桥的打开和改尺寸返回期约'
    if 结果 is None:
        return
    if hasattr(结果,'然后'):
        结果.然后(成功,失败)
        return
    然后=getattr(结果,'then',None)
    if callable(然后):
        然后(成功,失败)

class 平台覆盖层:
    '整窗的平台容器。失败可以重试'
    def __init__(自身,属性):
        '记下原生桥和返回动作'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.根=None
        自身.层=None
        自身.视口=None
        自身.返回钮=None
        自身.尝试=0
        自身.状态='loading'
        自身.已开键=None
        自身.惰性=[]
        自身.先前焦点=None
        自身.拆除器=[]
        自身.绘制中=False
        自身.待重画=False
        自身.渲染()

    def 更新(自身,属性):
        '换成新的 props'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 渲染(自身):
        '绘制中再来一次只记一笔'
        if 自身.绘制中:
            自身.待重画=True
            return 自身.根
        自身.绘制中=True
        try:
            自身.画出()
        finally:
            自身.绘制中=False
        if 自身.待重画:
            自身.待重画=False
            return 自身.渲染()
        return 自身.根

    def 画出(自身):
        '打开原生页，尺寸变化时同步边界。同一页只改加载状态'
        属性=自身.属性
        键=(id(属性.get('bridge')),属性.get('page'),自身.尝试)
        if 自身.层 is not None and 自身.已开键==键:
            自身.改状态()
            return
        自身.释放()
        自身.已开键=键
        窗口=属性['window'] if 'window' in 属性 else 取握手窗口()
        文档=窗口.document
        注入模块样式文件(
            文档,
            '平台覆盖层样式',
            os.path.join(os.path.dirname(__file__),'平台覆盖层.module.css'),
            样式模块,
        )
        if 自身.根 is None:
            自身.根=文档.createElement('div')
            自身.根.style.display='contents'
        层=文档.createElement('div')
        层.className='overlay'
        层.setAttribute('data-dsh-css',样式模块)
        层.setAttribute('role','dialog')
        层.setAttribute('aria-modal','true')
        层.setAttribute('aria-label',属性.get('backLabel') or 中文['backToHarness'])
        头=文档.createElement('header')
        头.className='header'
        头.setAttribute('data-dsh-css',样式模块)
        头.setAttribute('data-window-drag','')
        控=文档.createElement('div')
        控.className='controls'
        控.setAttribute('data-dsh-css',样式模块)
        灯=文档.createElement('span')
        灯.className='trafficLights'
        灯.setAttribute('aria-hidden','true')
        灯.setAttribute('data-dsh-css',样式模块)
        返回=文档.createElement('button')
        返回.className='back'
        返回.setAttribute('data-dsh-css',样式模块)
        返回.appendChild(图标左chevron14({'window':窗口,'size':16}))
        返回.appendChild(文档.createTextNode(属性.get('backLabel') or 中文['backToHarness']))
        def 点返回(_事件=None):
            '回到 Harness'
            关=属性.get('onClose')
            if 关 is not None:
                关()
        返回.addEventListener('click',点返回)
        控.appendChild(灯)
        控.appendChild(返回)
        头.appendChild(控)
        视口=文档.createElement('div')
        视口.className='viewport'
        视口.setAttribute('data-dsh-css',样式模块)
        if 自身.状态!='loaded':
            态=文档.createElement('div')
            态.className='status'
            态.setAttribute('role','status')
            态.setAttribute('data-dsh-css',样式模块)
            if 自身.状态=='failed':
                失败=文档.createElement('span')
                失败.className='failure'
                失败.setAttribute('data-dsh-css',样式模块)
                失败.textContent=属性.get('failureLabel') or 中文['platformFailed']
                def 重试():
                    '再开一次'
                    自身.尝试+=1
                    自身.状态='loading'
                    自身.渲染()
                钮=按钮({
                    'window':窗口,
                    'variant':'outline',
                    'className':'retry',
                    'onClick':重试,
                    'children':属性.get('retryLabel') or 中文['platformRetry'],
                })
                钮根=钮.渲染()
                钮根.setAttribute('data-dsh-css',样式模块)
                态.appendChild(失败)
                态.appendChild(钮根)
            else:
                态.setAttribute('aria-label',属性.get('loadingLabel') or 中文['loading'])
                转=文档.createElement('span')
                转.className='spinner'
                转.setAttribute('aria-hidden','true')
                转.setAttribute('data-dsh-css',样式模块)
                态.appendChild(转)
            视口.appendChild(态)
        层.appendChild(头)
        层.appendChild(视口)
        文档.body.appendChild(层)
        自身.层=层
        自身.视口=视口
        自身.返回钮=返回
        焦点=文档.activeElement
        if getattr(焦点,'tagName',None) is not None:
            自身.先前焦点=焦点
        for 子 in list(文档.body.children):
            if 子 is not 层 and getattr(子,'tagName',None) is not None:
                自身.惰性.append(取得覆盖层惰性(子))
        返回.focus()
        桥=属性.get('bridge')
        页=属性.get('page')
        已关={'值':False}
        def 边界():
            '视口在页面上的矩形'
            矩形=视口.getBoundingClientRect()
            return {'x':矩形.x,'y':矩形.y,'width':矩形.width,'height':矩形.height}
        def 失败(_错误=None):
            '打开或改尺寸失败'
            if 已关['值']:
                return
            自身.状态='failed'
            自身.改状态()
        def 已开(_值=None):
            '文档加载完'
            if 已关['值']:
                return
            自身.状态='loaded'
            自身.改状态()
        if 桥 is not None:
            接上(桥.open(页,边界()),已开,失败)
            def 改尺寸(_条目=None):
                '视口变了就告诉原生视图'
                if 已关['值']:
                    return
                def 已改(_值=None):
                    '尺寸已经交给原生视图'
                    return None
                接上(桥.setBounds(边界()),已改,失败)
            观察=窗口.ResizeObserver(改尺寸)
            观察.observe(视口)
            def 拆观察():
                '卸下并关掉原生文档'
                已关['值']=True
                观察.disconnect()
                关掉=桥.close()
                def 忽略(_错误=None):
                    '窗口拆掉时接收端可能已经不在'
                    return None
                接上(关掉,忽略,忽略)
            自身.拆除器.append(拆观察)

    def 改状态(自身):
        '只换视口里的加载、失败或空白，不重开原生页'
        视口=自身.视口
        if 视口 is None:
            return
        while 视口.firstElementChild is not None:
            视口.firstElementChild.remove()
        if 自身.状态=='loaded':
            return
        属性=自身.属性
        窗口=属性['window'] if 'window' in 属性 else 取握手窗口()
        文档=窗口.document
        态=文档.createElement('div')
        态.className='status'
        态.setAttribute('role','status')
        态.setAttribute('data-dsh-css',样式模块)
        if 自身.状态=='failed':
            失败=文档.createElement('span')
            失败.className='failure'
            失败.setAttribute('data-dsh-css',样式模块)
            失败.textContent=属性.get('failureLabel') or 中文['platformFailed']
            def 重试():
                '再开一次'
                自身.尝试+=1
                自身.状态='loading'
                自身.渲染()
            钮=按钮({
                'window':窗口,
                'variant':'outline',
                'className':'retry',
                'onClick':重试,
                'children':属性.get('retryLabel') or 中文['platformRetry'],
            })
            钮根=钮.渲染()
            钮根.setAttribute('data-dsh-css',样式模块)
            态.appendChild(失败)
            态.appendChild(钮根)
        else:
            态.setAttribute('aria-label',属性.get('loadingLabel') or 中文['loading'])
            转=文档.createElement('span')
            转.className='spinner'
            转.setAttribute('aria-hidden','true')
            转.setAttribute('data-dsh-css',样式模块)
            态.appendChild(转)
        视口.appendChild(态)
        if 自身.返回钮 is not None:
            自身.返回钮.focus()

    def 释放(自身):
        '恢复背景 inert，并关掉上一轮原生页'
        for 拆 in 自身.拆除器:
            拆()
        自身.拆除器=[]
        for 放 in 自身.惰性:
            放()
        自身.惰性=[]
        if 自身.层 is not None and 自身.层.parentNode is not None:
            自身.层.remove()
        自身.层=None
        自身.视口=None
        自身.已开键=None
        焦点=自身.先前焦点
        if 焦点 is not None and getattr(焦点,'isConnected',None) is True:
            焦点.focus()
        自身.先前焦点=None

    def 拆除(自身):
        '卸下覆盖层'
        自身.释放()
