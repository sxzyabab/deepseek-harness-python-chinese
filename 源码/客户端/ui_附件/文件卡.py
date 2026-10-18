'待发送文件卡：类型图标、名称、大小或上传状态、移除和重试'
from ..模块.客户端.通告 import 取握手窗口
import os
from ..ui_对话.异常 import 注入模块样式文件,标样式模块
from ..ui_基础界面组件.icons import 描边图标
from ..ui_基础界面组件.文件大小 import 文件大小文本
from ..ui_基础界面组件.文件类型图标 import 文件扩展名,文件类型图标

__all__=['文件卡']

样式模块='attachment-file-card'

class 文件卡:
    '一张待发送文件。上传中显示转圈和进度，失败后整卡可重试'
    def __init__(自身,属性):
        '记下名称、字节、状态和回调'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.根=None
        自身.渲染()

    def 更新(自身,属性):
        '换上新的上传状态'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 渲染(自身):
        '画出类型图标、名称、状态、移除钮，失败时正文也可点重试'
        属性=自身.属性
        窗口=属性['window'] if 'window' in 属性 else 取握手窗口()
        文档=窗口.document
        注入模块样式文件(
            文档,
            'dsh-attachment-file-card',
            os.path.join(os.path.dirname(__file__),'文件卡.module.css'),
            样式模块,
        )
        名字='' if 属性.get('name') is None else str(属性['name'])
        字节=属性.get('bytes') if 属性.get('bytes') is not None else 0
        状态=属性.get('state')
        文案=属性.get('labels') if isinstance(属性.get('labels'),dict) else {}
        扩展=文件扩展名(名字).upper()[:8]
        if 状态=='uploading':
            元='' if 文案.get('uploading') is None else str(文案['uploading'])
        elif 状态=='error':
            元='' if 文案.get('failed') is None else str(文案['failed'])
        else:
            段=[]
            if 扩展!='':
                段.append(扩展)
            大小文=文件大小文本(字节)
            if 大小文!='':
                段.append(大小文)
            元=' '.join(段)
        可重试=状态=='error'
        卡=文档.createElement('div')
        卡.className='card failed' if 可重试 else 'card'
        标样式模块(卡,样式模块)
        卡.setAttribute('title',名字)
        图标盒=文档.createElement('span')
        图标盒.className='icon'
        标样式模块(图标盒,样式模块)
        图标盒.setAttribute('aria-hidden','true')
        if 状态=='uploading':
            转圈=文档.createElement('span')
            转圈.className='spinner'
            标样式模块(转圈,样式模块)
            图标盒.appendChild(转圈)
        else:
            类型图=文件类型图标({'window':窗口,'path':名字})
            类型图.渲染()
            if 类型图.根 is not None:
                图标盒.appendChild(类型图.根)
        if 可重试:
            def 点重试(事件=None):
                '重试这一份上传'
                属性['onRetry']()
            正文=文档.createElement('button')
            正文.type='button'
            正文.className='body retry'
            标样式模块(正文,样式模块)
            正文.setAttribute('aria-label','' if 文案.get('retry') is None else str(文案['retry']))
            正文.addEventListener('click',点重试)
        else:
            正文=文档.createElement('span')
            正文.className='body'
            标样式模块(正文,样式模块)
            正文.setAttribute('aria-label','' if 文案.get('label') is None else str(文案['label']))
        名称=文档.createElement('span')
        名称.className='name'
        标样式模块(名称,样式模块)
        名称.textContent=名字
        次行=文档.createElement('span')
        次行.className='meta metaFailed' if 可重试 else 'meta'
        标样式模块(次行,样式模块)
        次行.textContent=元
        正文.appendChild(名称)
        正文.appendChild(次行)
        def 点移除(事件=None):
            '从草稿拿掉这一份文件'
            属性['onRemove']()
        移除=文档.createElement('button')
        移除.type='button'
        移除.className='remove removeFailed' if 可重试 else 'remove'
        标样式模块(移除,样式模块)
        移除.setAttribute('aria-label','' if 文案.get('remove') is None else str(文案['remove']))
        移除.addEventListener('click',点移除)
        关闭图=描边图标({'window':窗口,'size':12},'0 0 16 16',[
            'M3.5 3.5L12.5 12.5',
            'M12.5 3.5L3.5 12.5',
        ])
        if 关闭图 is not None:
            移除.appendChild(关闭图)
        卡.appendChild(图标盒)
        卡.appendChild(正文)
        卡.appendChild(移除)
        if 状态=='uploading':
            轨=文档.createElement('span')
            轨.className='progressTrack'
            标样式模块(轨,样式模块)
            轨.setAttribute('aria-hidden','true')
            条=文档.createElement('span')
            条.className='progressBar'
            标样式模块(条,样式模块)
            进度=属性.get('progress')
            if 进度 is not None:
                比值=进度
                if 比值<0:
                    比值=0
                if 比值>1:
                    比值=1
                条.style.width=str(比值*100)+'%'
            轨.appendChild(条)
            卡.appendChild(轨)
        旧=自身.根
        if 旧 is not None and getattr(旧,'parentNode',None) is not None:
            旧.parentNode.replaceChild(卡,旧)
        自身.根=卡
        return 卡
