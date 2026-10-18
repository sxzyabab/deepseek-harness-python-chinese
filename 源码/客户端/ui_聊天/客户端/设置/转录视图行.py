from ...聊天设置 import 转录视图模式表
from ..呈现策略 import 折叠时机表
from ..文案 import 中文
from .偏好行 import 偏好行

__all__=['转录视图行']

展示标签={
    'compact':'settings.transcript.compact',
    'standard':'settings.transcript.standard',
    'detailed':'settings.transcript.detailed',
    'verbose':'settings.transcript.verbose',
}
收起标签={
    'completion':'settings.collapse.completion',
    'next-input':'settings.collapse.nextInput',
}


def 原样(值):
    '整份快照'
    return 值


class 转录视图行:
    '工作步骤展示和收起时机。两份选择各自一行'
    def __init__(自身,属性):
        '记下设置槽属性，订两份偏好，并画出两行'
        自身.属性=属性
        自身.展示行=None
        自身.收起行=None
        自身.根=None
        自身.已订=False
        自身.退订表=[]
        自身.渲染()

    def 选展示(自身,值):
        '改工作步骤展示档'
        自身.属性['setTranscriptView'](值)

    def 选收起(自身,值):
        '改收起时机'
        自身.属性['setCollapseTiming'](值)

    def 渲染(自身):
        '两行都用中文表原文。快照变了只改标签和当前值'
        属性=自身.属性
        窗口=属性['window']
        文档=窗口.document
        模式=属性['useTranscriptView'](原样)
        时机=属性['useCollapseTiming'](原样)
        if 自身.根 is None:
            自身.根=文档.createDocumentFragment()
        展示选项=[]
        for 标识 in 转录视图模式表:
            展示选项.append({'id':标识,'label':中文[展示标签[标识]]})
        收起选项=[]
        for 标识 in 折叠时机表:
            收起选项.append({'id':标识,'label':中文[收起标签[标识]]})
        展示属性={
            'window':窗口,
            'title':中文['settings.transcript.title'],
            'description':中文['settings.transcript.description'],
            'value':模式,
            'selectedLabel':中文[展示标签[模式]],
            'options':展示选项,
            'onSelect':自身.选展示,
        }
        收起属性={
            'window':窗口,
            'title':中文['settings.collapse.title'],
            'description':中文['settings.collapse.description'],
            'value':时机,
            'selectedLabel':中文[收起标签[时机]],
            'options':收起选项,
            'onSelect':自身.选收起,
        }
        if 自身.展示行 is None:
            自身.展示行=偏好行(展示属性)
            自身.收起行=偏好行(收起属性)
            自身.根.appendChild(自身.展示行.根)
            自身.根.appendChild(自身.收起行.根)
            if 'parent' in 属性 and 属性['parent'] is not None:
                属性['parent'].appendChild(自身.根)
        else:
            自身.展示行.属性=展示属性
            自身.展示行.渲染()
            自身.收起行.属性=收起属性
            自身.收起行.渲染()
        if not 自身.已订:
            for 钩 in (属性['useTranscriptView'],属性['useCollapseTiming']):
                订=getattr(钩,'_subscribe',None)
                if callable(订):
                    自身.退订表.append(订(自身.渲染))
            自身.已订=True
        return 自身.根
