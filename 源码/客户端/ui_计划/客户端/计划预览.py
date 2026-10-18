import os
import pywebbridge
from ...ui_对话.异常 import 注入模块样式文件,标样式模块,模块节点#样式模块
from ...ui_基础界面组件.markdown.Markdown文本 import Markdown文本#正文
from ...ui_基础界面组件.文件类型图标 import 文件类型图标#标题图标
from .审阅预览 import 是否审阅预览地址#临时审阅

__all__=['计划预览','计划标题']

样式模块='plan-preview'


def 确保样式(文档):
    '预览正文和标题图标共用这一份样式'
    注入模块样式文件(
        文档,
        'dsh-plan-preview',
        os.path.join(os.path.dirname(__file__),'计划预览.module.css'),
        样式模块,
    )


def 订上(自身,名字列表):
    '标签或资源变了就重画。根被从页面拿掉就退订'
    if 自身.已订:
        return
    自身.已订=True
    def 变更():
        '重画，或在根离开页面后退订'
        if 自身.根 is not None and 自身.根.parentNode is None:
            for 退 in 自身.退订:
                退()
            自身.退订=[]
            自身.已订=False
            return
        自身.渲染()
    for 名 in 名字列表:
        钩=自身.属性.get(名)
        if 钩 is not None and hasattr(钩,'_subscribe') and callable(钩._subscribe):
            自身.退订.append(钩._subscribe(变更))


def 读计划(属性):
    '临时审阅读导航参数。已记录计划读资源当前值'
    信息=属性['useTabInfo']()
    标签=信息['tab']
    导航=标签['navigation']
    地址=导航['address']
    资源=属性['useResource'](地址)
    临时=是否审阅预览地址(地址)
    参数=导航.get('params')
    if 临时:
        if isinstance(参数,dict) and 'planReview' in 参数:
            计划=参数['planReview']
        else:
            计划=None
    else:
        计划=资源.get('value') if isinstance(资源,dict) else None
    return 标签,地址,资源,临时,计划


class 计划预览:
    '已记录计划或临时审阅的只读 Markdown'
    def __init__(自身,属性):
        '记下 props，并画出正文或状态'
        自身.属性=属性
        自身.根=None
        自身.已订=False
        自身.退订=[]
        自身.绘制中=False
        自身.待重画=False
        自身.渲染()

    def 更新(自身,属性):
        '换上最新 props'
        自身.属性=属性

    def 渲染(自身):
        '还没有正文时显示读取状态。有正文就画出 Markdown'
        if 自身.绘制中:
            自身.待重画=True
            return 自身.根
        自身.绘制中=True
        try:
            属性=自身.属性
            窗口=属性['window']
            文档=窗口.document
            确保样式(文档)
            标签,地址,资源,临时,计划=读计划(属性)
            旧=自身.根
            父=旧.parentNode if 旧 is not None else 属性.get('parent')
            if 旧 is not None:
                旧.remove()
                自身.根=None
            if 计划 is None:
                if 临时:
                    文='临时计划预览已失效，请从仍在等待审批的卡片重新打开。'
                elif isinstance(资源,dict) and 资源.get('status')=='none':
                    文='计划预览不可用'
                elif isinstance(资源,dict) and 资源.get('status')=='failed':
                    文='无法读取计划'
                else:
                    文='正在读取计划…'
                根=模块节点(文档,'div',样式模块,'message')
                根.setAttribute('role','status')
                根.appendChild(文档.createTextNode(文))
                失败=None if 临时 or not isinstance(资源,dict) else 资源.get('failure')
                if 失败 is not None:
                    if isinstance(失败,dict):
                        码=失败.get('code')
                        消息=失败.get('message')
                    elif isinstance(失败,str):
                        码=None
                        消息=失败
                    else:
                        码=getattr(失败,'code',None)
                        消息=getattr(失败,'message',None)
                    if 码=='plan/invalid-address':
                        行文='计划地址无效'
                    elif 码=='plan/unavailable':
                        行文='无法读取会话历史'
                    elif 码=='plan/not-found':
                        行文='未找到这份计划'
                    else:
                        行文='' if 消息 is None else str(消息)
                    段=文档.createElement('p')
                    段.textContent=行文
                    根.appendChild(段)
                自身.根=根
            else:
                if 'callId' in 计划:
                    预览键=计划['callId']
                else:
                    预览键=地址
                根=模块节点(文档,'section',样式模块,'preview')
                根.setAttribute('data-plan-preview','' if 预览键 is None else str(预览键))
                根.setAttribute('aria-label','' if 计划.get('title') is None else str(计划['title']))
                文档盒=模块节点(文档,'div',样式模块,'document')
                正文=Markdown文本({
                    'window':窗口,
                    'text':计划['markdown'],
                    'codeLabels':{
                        'copyLabel':'复制',
                        'copiedLabel':'复制成功',
                    },
                })
                文档盒.appendChild(正文.渲染())
                根.appendChild(文档盒)
                自身.根=根
            if 父 is not None and 自身.根 is not None:
                父.appendChild(自身.根)
            订上(自身,('useTabInfo','useResource'))
        finally:
            自身.绘制中=False
        if 自身.待重画:
            自身.待重画=False
            return 自身.渲染()
        return 自身.根


class 计划标题:
    '侧栏标签上的文件图标和计划标题'
    def __init__(自身,属性):
        '记下 props，并画出标题'
        自身.属性=属性
        自身.根=None
        自身.已订=False
        自身.退订=[]
        自身.绘制中=False
        自身.待重画=False
        自身.渲染()

    def 更新(自身,属性):
        '换上最新 props'
        自身.属性=属性

    def 渲染(自身):
        '图标后面是恢复到的标题。还没有正文时用标签上原来的字'
        if 自身.绘制中:
            自身.待重画=True
            return 自身.根
        自身.绘制中=True
        try:
            属性=自身.属性
            窗口=属性['window']
            文档=窗口.document
            确保样式(文档)
            标签,地址,资源,临时,计划=读计划(属性)
            旧=自身.根
            父=旧.parentNode if 旧 is not None else 属性.get('parent')
            if 旧 is not None:
                旧.remove()
                自身.根=None
            if 计划 is not None and 计划.get('title') is not None:
                文=计划['title']
            else:
                文=标签['title']
            包裹=文档.createElement('span')
            包裹.style.display='contents'
            图标=文件类型图标({'window':窗口,'kind':'other','size':16,'className':'titleIcon'}).渲染()
            标样式模块(图标,样式模块)
            包裹.appendChild(图标)
            包裹.appendChild(文档.createTextNode('' if 文 is None else str(文)))
            自身.根=包裹
            if 父 is not None:
                父.appendChild(包裹)
            订上(自身,('useTabInfo','useResource'))
        finally:
            自身.绘制中=False
        if 自身.待重画:
            自身.待重画=False
            return 自身.渲染()
        return 自身.根
