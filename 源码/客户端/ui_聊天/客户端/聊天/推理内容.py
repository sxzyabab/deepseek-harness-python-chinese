from ....ui_基础界面组件.markdown.Markdown文本 import Markdown文本
from ..markdown标签 import markdown标签

__all__=['推理内容','默认推理体']


class 推理内容:
    '紧凑推理正文。没人给标签就用聊天的中文原文'
    def __init__(自身,属性):
        '记下文本和是否还在流式输出'
        自身.属性=属性
        自身.根=None
        自身.渲染()

    def 渲染(自身):
        '交给共享 Markdown。标签缺省时用复制、代码块、脚注的中文'
        属性=自身.属性
        窗口=属性['window']
        标签=属性['labels'] if 属性.get('labels') is not None else markdown标签()
        正文=Markdown文本({
            'window':窗口,
            'text':属性.get('text') or '',
            'streaming':属性.get('running') is True,
            'labels':标签,
            'variant':'compact',
        })
        自身.根=正文.渲染() if hasattr(正文,'渲染') else 正文
        if 'parent' in 属性 and 属性['parent'] is not None and 自身.根 is not None:
            属性['parent'].appendChild(自身.根)
        return 自身.根


class 默认推理体:
    '默认推理体只是再画一次官方推理内容工厂'
    def __init__(自身,属性):
        '记下工厂渲染器'
        自身.属性=属性
        自身.根=None
        自身.渲染()

    def 渲染(自身):
        '把原文和是否在跑交给 reasoning.content'
        属性=自身.属性
        渲染=属性.get('renderFactorySlot')
        if not callable(渲染):
            return None
        自身.根=渲染('conversation.chat.reasoning.content',{
            'text':属性.get('text') or '',
            'running':属性.get('running') is True,
            'window':属性.get('window'),
        })
        return 自身.根
