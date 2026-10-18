from ..模块.客户端.通告 import 取握手窗口
import os
from ..ui_对话.异常 import 注入模块样式文件,标样式模块
from .icons import 图标加载描边常规

__all__=['图像预览']

样式模块='image-preview'

class 图像预览:
    '不另做一个点击目标的图片预览。加载中和失败都有状态句'
    def __init__(自身,属性=None):
        '记下地址。换地址会重新加载'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.根=None
        自身.态='loading'
        自身.地址=None

    def 渲染(自身):
        '画出框。地址变了回到加载中'
        属性=自身.属性
        地址='' if 属性.get('src') is None else str(属性['src'])
        if 自身.地址!=地址:
            自身.地址=地址
            自身.态='loading'
            if 自身.根 is not None:
                自身.根.remove()
                自身.根=None
        if 自身.根 is not None:
            return 自身.根
        窗口=属性['window'] if 'window' in 属性 else 取握手窗口()
        文档=窗口.document
        注入模块样式文件(文档,'图像预览样式',os.path.join(os.path.dirname(__file__),'图像预览.module.css'),样式模块)
        框=文档.createElement('span')
        框.className='frame'
        标样式模块(框,样式模块)
        图=文档.createElement('img')
        图.className='image'
        标样式模块(图,样式模块)
        图.src=地址
        图.alt='' if 属性.get('alt') is None else str(属性['alt'])
        图.loading='lazy'
        图.decoding='async'
        图.referrerPolicy='no-referrer'
        状态=文档.createElement('span')
        状态.className='status'
        标样式模块(状态,样式模块)
        状态.setAttribute('role','status')
        def 刷新():
            '按加载态显示图和状态'
            if 自身.态=='failed':
                if 图.parentNode is not None:
                    图.remove()
            elif 图.parentNode is None:
                框.insertBefore(图,状态)
            if 自身.态=='ready':
                图.setAttribute('data-ready','')
                if 状态.parentNode is not None:
                    状态.remove()
            else:
                图.removeAttribute('data-ready')
                if 状态.parentNode is None:
                    框.appendChild(状态)
                while 状态.firstChild is not None:
                    状态.firstChild.remove()
                if 自身.态=='loading':
                    转=图标加载描边常规({'window':窗口,'size':16})
                    if 转 is not None:
                        状态.appendChild(转)
                    字=文档.createElement('span')
                    字.textContent='' if 属性.get('loadingLabel') is None else str(属性['loadingLabel'])
                    状态.appendChild(字)
                else:
                    字=文档.createElement('span')
                    字.textContent='' if 属性.get('failedLabel') is None else str(属性['failedLabel'])
                    状态.appendChild(字)
        def 载入(事件):
            '图出来了'
            自身.态='ready'
            刷新()
        def 失败(事件):
            '图没出来'
            自身.态='failed'
            刷新()
        图.addEventListener('load',载入)
        图.addEventListener('error',失败)
        框.appendChild(图)
        框.appendChild(状态)
        刷新()
        if 'parent' in 属性 and 属性['parent'] is not None:
            属性['parent'].appendChild(框)
        自身.根=框
        return 框
