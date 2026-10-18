from ..模块.客户端.通告 import 取握手窗口
import os
from ..ui_对话.异常 import 注入模块样式文件,标样式模块
from .icons import 图标勾圈描边常规

__all__=['吐司','处理吐司','保持毫秒','淡出毫秒']

保持毫秒=3000
淡出毫秒=1000
样式模块='toast'

def 处理吐司(window,属性):
    '画到 body 上的顶栏公告。success 用勾圈，到时调用 onDone'
    文档=window.document
    注入模块样式文件(
        文档,
        '吐司样式',
        os.path.join(os.path.dirname(__file__),'吐司.module.css'),
        样式模块,
    )
    文='' if 属性.get('text') is None else str(属性['text'])
    语气=属性.get('tone')
    图标=属性.get('icon')
    完成=属性.get('onDone')
    保持=属性['holdMs'] if 'holdMs' in 属性 and 属性['holdMs'] is not None else 保持毫秒
    锚=属性.get('anchor')
    动作列=属性['actions'] if 'actions' in 属性 and 属性['actions'] is not None else []
    行=文档.createElement('div')
    行.className='toast'
    标样式模块(行,样式模块)
    行.setAttribute('role','alert')
    行.style.setProperty('--dsh-toast-hold',str(保持)+'ms')
    def 量左():
        '有锚时把公告水平中心对齐到锚'
        if 锚 is None:
            return
        矩形=锚.getBoundingClientRect()
        行.style.left=str(矩形.left+矩形.width/2)+'px'
    量左()
    if 锚 is not None:
        window.addEventListener('resize',量左)
    if 语气=='success':
        图盒=文档.createElement('span')
        图盒.className='icon success'
        标样式模块(图盒,样式模块)
        图盒.setAttribute('aria-hidden','true')
        图=图标勾圈描边常规({'window':window,'size':16})
        if 图 is not None:
            图盒.appendChild(图)
        行.appendChild(图盒)
    elif 图标 is not None and hasattr(图标,'tagName'):
        图盒=文档.createElement('span')
        图盒.className='icon'
        标样式模块(图盒,样式模块)
        图盒.setAttribute('aria-hidden','true')
        图盒.appendChild(图标)
        行.appendChild(图盒)
    字=文档.createElement('span')
    字.className='text'
    标样式模块(字,样式模块)
    字.appendChild(文档.createTextNode(文))
    for 动作 in 动作列:
        if 动作.get('prefix') is not None:
            字.appendChild(文档.createTextNode(str(动作['prefix'])))
        钮=文档.createElement('button')
        钮.type='button'
        钮.className='action'
        标样式模块(钮,样式模块)
        钮.textContent='' if 动作.get('label') is None else str(动作['label'])
        点=动作.get('onClick')
        def 点下(事件,点=点):
            '把这一条动作交给业主'
            if 点 is not None:
                点()
        钮.addEventListener('click',点下)
        字.appendChild(钮)
    行.appendChild(字)
    if 完成 is not None:
        def 到期():
            '保持加淡出结束后通知业主'
            完成()
        window.setTimeout(到期,保持+淡出毫秒)
    文档.body.appendChild(行)
    if 'parent' in 属性 and 属性['parent'] is not None and 属性['parent'] is not 文档.body:
        属性['parent'].appendChild(行)
    return 行

class 吐司:
    '滑入、保持、淡出。success 自带勾圈，业主在 onDone 卸载'
    def __init__(自身,属性=None,**关键字参数):
        '合并 props。构造不画'
        自身.属性=dict(属性 if 属性 is not None else {})
        自身.属性.update(关键字参数)
        自身.根=None

    def 更新(自身,属性):
        '刷新 props'
        自身.属性=dict(属性)

    def 总时长(自身):
        '保持加淡出'
        保持=自身.属性['holdMs'] if 'holdMs' in 自身.属性 and 自身.属性['holdMs'] is not None else 保持毫秒
        return 保持+淡出毫秒

    def 渲染(自身):
        '拆掉旧条，再画一次'
        if 自身.根 is not None:
            自身.根.remove()
        窗口=自身.属性['window'] if 'window' in 自身.属性 else 取握手窗口()
        自身.根=处理吐司(窗口,自身.属性)
        return 自身.根

    def __call__(自身,属性=None,**关键字参数):
        '对齐 React 调用'
        if 属性 is not None or len(关键字参数)>0:
            合并=dict(属性 if 属性 is not None else {})
            合并.update(关键字参数)
            自身.更新(合并)
        return 自身.渲染()
