'把引导画到 body 上，并让应用根暂时不能点'
from ...模块.客户端.通告 import 取握手窗口
import os
from ...ui_对话.异常 import 注入模块样式文件,挂上
from .覆盖层惰性 import 取得覆盖层惰性

__all__=['上手引导表面']

样式模块='上手引导表面'

class 上手引导表面:
    '盖住应用。退出的 180 毫秒里把根的透明度还回去'
    def __init__(自身,属性):
        '记下子内容和是否正在退出'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.根=None
        自身.层=None
        自身.放开=None
        自身.根状态=None
        自身.渲染()

    def 更新(自身,属性):
        '换成新的 props'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 渲染(自身):
        '挂上舞台。退出时恢复根的透明度'
        属性=自身.属性
        窗口=属性['window'] if 'window' in 属性 else 取握手窗口()
        文档=窗口.document
        注入模块样式文件(
            文档,
            '上手引导表面样式',
            os.path.join(os.path.dirname(__file__),'上手引导表面.module.css'),
            样式模块,
        )
        if 自身.根 is None:
            自身.根=文档.createElement('div')
            自身.根.style.display='contents'
        应用根=文档.getElementById('root')
        if 应用根 is not None and 自身.放开 is None:
            自身.放开=取得覆盖层惰性(应用根)
            自身.根状态={'element':应用根,'opacity':应用根.style.opacity}
            应用根.style.opacity='0'
        退出=属性.get('exiting') is True
        if 自身.根状态 is not None:
            if 退出:
                自身.根状态['element'].style.opacity=自身.根状态['opacity']
            else:
                自身.根状态['element'].style.opacity='0'
        if 自身.层 is None:
            层=文档.createElement('div')
            层.className='onboardingOverlay'
            层.setAttribute('data-dsh-css',样式模块)
            层.setAttribute('role','presentation')
            拖=文档.createElement('div')
            拖.className='dragBand'
            拖.setAttribute('data-window-drag','')
            拖.setAttribute('aria-hidden','true')
            拖.setAttribute('data-dsh-css',样式模块)
            台=文档.createElement('div')
            台.className='onboardingStage'
            台.setAttribute('data-dsh-css',样式模块)
            层.appendChild(拖)
            层.appendChild(台)
            文档.body.appendChild(层)
            自身.层=层
            自身.台=台
        if 退出:
            自身.层.setAttribute('data-exiting','')
        else:
            自身.层.removeAttribute('data-exiting')
        while 自身.台.firstElementChild is not None:
            自身.台.firstElementChild.remove()
        子=属性.get('children')
        if isinstance(子,(list,tuple)):
            for 项 in 子:
                挂上(自身.台,项)
        else:
            挂上(自身.台,子)
        return 自身.根

    def 拆除(自身):
        '还回应用根的 inert 和透明度'
        if 自身.放开 is not None:
            自身.放开()
            自身.放开=None
        if 自身.根状态 is not None:
            自身.根状态['element'].style.opacity=自身.根状态['opacity']
            自身.根状态=None
        if 自身.层 is not None and 自身.层.parentNode is not None:
            自身.层.remove()
        自身.层=None
