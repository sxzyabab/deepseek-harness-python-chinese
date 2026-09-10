"""没有更具体文档渲染器时的纯源码展示。

对齐上游 `ui-sidebar-documentpreview/src/client/text/TextBody.tsx`。公开面仅中文名。
无 React：正文为视图模型，产出结构树 dict。
"""
from .行 import 页行#行辅助

__all__=['文本体']#仅中文公开名


def 文本体(内容,取标签信息):
    """产出带导航目标的源码行结构。内容为文档内容 dict。"""
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
