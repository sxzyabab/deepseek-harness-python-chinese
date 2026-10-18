'一份交付文件的身份、侧栏预览和原生动作'
import os
import re
import pywebbridge
from ...ui_对话.异常 import 注入模块样式文件,标样式模块
from ...ui_基础界面组件.文件类型图标 import 文件扩展名,文件类型图标
from ....工具.工作区路径 import 解析工作区路径
from ..已呈现 import 路径末段
from .呈现打开 import 成功停留毫秒,成功淡出毫秒
from .文案 import 中文,填入

__all__=['已呈现文件卡']

样式模块='Deliverables'
样式路径=os.path.join(os.path.dirname(__file__),'产出清单.module.css')
尾注=re.compile(r'\s*(?:\([^()]*\)|（[^（）]*）)\s*$')


def 确保样式(文档):
    '交付卡样式只插一次'
    注入模块样式文件(文档,'dsh-deliverables',样式路径,样式模块)


def 元素(文档,标签,类名=None):
    '带官方类名和样式模块'
    节点=文档.createElement(标签)
    if isinstance(类名,str) and 类名!='':
        节点.className=类名
    return 标样式模块(节点,样式模块)


def 挂上(父,节点):
    '字符串、节点或带渲染的界面'
    if 节点 is None:
        return
    if isinstance(节点,(list,tuple)):
        for 项 in 节点:
            挂上(父,项)
        return
    if hasattr(节点,'tagName'):
        父.appendChild(节点)
        return
    if hasattr(节点,'渲染'):
        画出=节点.渲染()
        if 画出 is not None and hasattr(画出,'tagName'):
            父.appendChild(画出)


class 已呈现文件卡:
    '预览按钮和文件动作分开，按钮不套按钮'
    def __init__(自身,属性):
        '记下这一份文件'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.根=None
        自身.渲染()

    def 更新(自身,属性):
        '换上新的 props'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 渲染(自身):
        '文件名、状态和动作'
        属性=自身.属性
        窗口=属性['window']
        文档=窗口.document
        确保样式(文档)
        文件=属性['file']
        阶段=属性.get('phase')
        宿主=属性.get('host')
        成功=阶段=='opened' or 阶段=='revealed'
        揭示='directory'
        if isinstance(宿主,dict) and 宿主.get('fileManager'):
            揭示=宿主['fileManager']
        名称=路径末段(文件['path'])
        扩展=文件扩展名(名称).upper()
        元数据=扩展 if 扩展 else 中文['presented.file']
        if 阶段 is None:
            说明=文件.get('description')
            if isinstance(说明,str):
                裁=尾注.sub('',说明).strip()
                状态文=裁 if 裁!='' else 元数据
            else:
                状态文=元数据
        elif 揭示=='directory' and 阶段=='revealed':
            状态文=中文['presented.directoryOpened']
        elif 揭示=='directory' and 阶段=='revealing':
            状态文=中文['presented.directoryOpening']
        elif 揭示=='directory' and 阶段=='revealError':
            状态文=中文['presented.directoryError']
        else:
            状态文=中文['presented.'+阶段]
        根=元素(文档,'div','file')
        根.setAttribute('data-presented-file','')
        预览=元素(文档,'button','cardPreview')
        预览.setAttribute('type','button')
        预览.setAttribute('title',解析工作区路径(属性.get('cwd'),文件['path']))
        预览.setAttribute('aria-label',填入(中文['presented.previewCard'],{'name':文件['path']}))

        def 点预览(事件,打开=属性.get('onPreview')):
            '在侧栏预览'
            if callable(打开):
                打开()

        预览.addEventListener('click',点预览)
        根.appendChild(预览)
        图标盒=元素(文档,'span','fileIcon')
        图标盒.appendChild(文件类型图标({'window':窗口,'path':文件['path'],'size':20}).渲染())
        根.appendChild(图标盒)
        体=元素(文档,'div','fileBody')
        细节=元素(文档,'div','details')
        名=元素(文档,'span','fileName')
        名.textContent=名称
        描述=元素(文档,'span','description')
        描述.setAttribute('data-presented-description','')
        if 阶段 is not None:
            描述.setAttribute('role','status')
        if 阶段 in ('error','revealError','nativeUnavailable'):
            描述.setAttribute('data-error','true')
        次=元素(文档,'span','secondaryText')
        if 成功:
            次.setAttribute('data-success','')
            次.style.animationDelay=str(成功停留毫秒)+'ms'
            次.style.animationDuration=str(成功淡出毫秒)+'ms'
        次.textContent=状态文
        提示=元素(文档,'span','previewHint')
        提示.textContent=中文['presented.preview']
        描述.appendChild(次)
        描述.appendChild(提示)
        细节.appendChild(名)
        细节.appendChild(描述)
        体.appendChild(细节)
        动作盒=元素(文档,'div','actions')
        挂上(动作盒,属性.get('actions'))
        体.appendChild(动作盒)
        根.appendChild(体)
        旧=自身.根
        父=None if 旧 is None else 旧.parentNode
        if 旧 is not None and 旧 is not 根:
            if 父 is not None:
                父.replaceChild(根,旧)
            else:
                旧.remove()
        自身.根=根
        return 根
