from nicegui import ui as 界面
from .行 import 页行

__all__=['文本体','文本体面板']

def 文本体(内容,取标签信息):
    '产出带导航目标的源码行结构。内容为文档内容 dict'
    标签=取标签信息()['tab']#标签
    参数=标签['navigation']['params'] if 'navigation' in 标签 and 'params' in 标签['navigation'] else None
    目标=参数['line'] if 参数 is not None and 'line' in 参数 else None#目标行
    if 内容.get('kind')!='text':#非文本
        return None#无
    页节点=[]#页列表
    for 页 in 内容['pages']:#各页
        行节点=[]#行列表
        for 序号,文本 in enumerate(页行(页)):#各行
            号=页['offset']+序号#行号
            行节点.append({#行
                'kind':'line',
                'number':号,
                'text':文本,
                'target':号==目标,
            })
        页节点.append({'kind':'page','offset':页['offset'],'lines':行节点})#页
    return {'kind':'text-body','pages':页节点}#结构


def _键齐(属性):
    '内容和页签都在才画'
    return isinstance(属性,dict) and 'content' in 属性 and 'useTabInfo' in 属性

class 文本体面板:
    '带行号的源码正文'

    def __init__(自身,属性):
        '记下文档席 props。槽位只调用构造，键齐了才画'
        自身.属性=属性 if isinstance(属性,dict) else {}
        if _键齐(自身.属性):
            自身.渲染()

    def 渲染(自身):
        '按页画出目标行'
        属性=自身.属性
        if not _键齐(属性):
            return
        内容=属性['content']
        取标签=属性['useTabInfo']
        模型=文本体(内容,取标签)
        if 模型 is None:
            return
        换行=属性['wrap'] is True if 'wrap' in 属性 else False
        空白='pre-wrap' if 换行 else 'pre'
        with 界面.column().classes('text-body'):
            for 页 in 模型['pages']:
                for 行 in 页['lines']:
                    类='line target' if 行['target'] is True else 'line'
                    with 界面.row().classes(类):
                        界面.label(str(行['number'])).classes('gutter')
                        界面.label(行['text']).style('white-space:'+空白)

    def __call__(自身,属性=None):
        '对齐组件调用'
        if 属性 is not None:
            自身.属性=属性 if isinstance(属性,dict) else {}
        return 自身.渲染()
