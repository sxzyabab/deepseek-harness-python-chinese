'时刻选择器共用的锚点弹层。点在触发器和面板外面就关'
import os
import pywebbridge
from ...ui_对话.异常 import 注入模块样式文件,标样式模块
from ...ui_基础界面组件.锚定位置 import 使用锚定位置
from ...ui_基础界面组件.点外关闭 import 点外关闭

__all__=['选择器弹出']

样式模块='picker-popover'

def 确保样式(文档):
    '选择器弹层样式只插一次'
    注入模块样式文件(文档,'日程选择器弹出样式',os.path.join(os.path.dirname(__file__),'选择器弹出.module.css'),样式模块)

class 选择器弹出:
    '面板挂到 body。内容类放在内层，好让另一份样式模块生效'
    def __init__(自身,属性):
        '记下锚和关闭'
        自身.属性=属性
        自身.根=None
        自身.内容=None
        自身.拆位置=None
        自身.拆外面=None

    def 关闭(自身):
        '卸掉定位和点外监听'
        if callable(自身.拆位置):
            自身.拆位置()
            自身.拆位置=None
        if callable(自身.拆外面):
            自身.拆外面()
            自身.拆外面=None
        if 自身.根 is not None and 自身.根.parentNode is not None:
            自身.根.parentNode.removeChild(自身.根)
        自身.根=None
        自身.内容=None

    def 打开(自身):
        '量好之前先藏起来，避免闪在原点'
        if 自身.根 is not None:
            return 自身.内容
        属性=自身.属性
        窗口=属性['window']
        文档=窗口.document
        确保样式(文档)
        面板=文档.createElement('div')
        面板.className='panel'
        标样式模块(面板,样式模块)
        面板.setAttribute('role','dialog')
        面板.setAttribute('aria-label',属性.get('label') or '')
        面板.style.visibility='hidden'
        面板.style.left='0px'
        面板.style.top='0px'
        def 挡住(事件):
            '面板里的点击不冒到打开它的行'
            事件.stopPropagation()
        面板.addEventListener('click',挡住)
        内容=文档.createElement('div')
        类名=属性.get('className')
        if isinstance(类名,str) and 类名!='':
            内容.className=类名
        内容模块=属性.get('内容模块')
        if isinstance(内容模块,str) and 内容模块!='':
            标样式模块(内容,内容模块)
        面板.appendChild(内容)
        文档.body.appendChild(面板)
        锚=属性.get('anchor')
        自身.拆位置=使用锚定位置({
            'open':True,'anchor':锚,'panel':面板,'window':窗口,
            'side':'bottom','align':'start','gap':4,'margin':12,
        })
        def 置关(打开):
            '点外面就交给业主关'
            if 打开 is False and callable(属性.get('onClose')):
                属性['onClose']()
        锚根=锚
        自身.拆外面=点外关闭(锚根,True,置关,面板)
        自身.根=面板
        自身.内容=内容
        return 内容

    def __call__(自身,属性=None):
        '换属性'
        if 属性 is not None:
            自身.属性=属性
        return 自身.根
