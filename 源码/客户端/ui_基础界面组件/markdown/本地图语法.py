"""从整段只有一张本地图、路径带空格的段落里恢复 image 节点。
只动无法被标准解析器认成图片、且源码未转义的纯文本段；不改代码块与 position。
"""
import re#本地图语法
from ..文件类型图标 import 分类文件类型#按路径判是否图片

__all__=['恢复本地图']#仅中文公开名

_本地图=re.compile(
    r'^!\[([^\]\n]*)\]\(((?:\/(?!\/)|\.{1,2}\/|[a-z]:[\\/])[^\n<>()[\]"\']+\.[a-z\d]+)\)$',
    re.IGNORECASE|re.UNICODE,
)#整段 image 语法

def 恢复本地图(根,原文):
    """仅恢复无歧义、未转义、整段仅一张图、本地路径含空格的段落。
    根为已解析 Markdown 树（原地修改）；原文用来区分作者语法与转义示例。
    返回同一个根。
    """
    def 访问(节点):
        """深度优先：段落命中则改写，否则下钻 children。"""
        类型=节点.get('type') if isinstance(节点,dict) else getattr(节点,'type',None)#节点类型
        子表=节点.get('children') if isinstance(节点,dict) else getattr(节点,'children',None)#子节点
        if 类型=='paragraph' and isinstance(子表,list) and len(子表)==1:#整段仅一个子节点
            子=子表[0]#唯一子节点
            子型=子.get('type') if isinstance(子,dict) else getattr(子,'type',None)#子类型
            位置=子.get('position') if isinstance(子,dict) else getattr(子,'position',None)#position
            值=子.get('value') if isinstance(子,dict) else getattr(子,'value',None)#文本
            if 子型=='text' and 位置 is not None and isinstance(值,str):#未转义候选
                起=位置.get('start',{}) if isinstance(位置,dict) else getattr(getattr(位置,'start',None),'offset',None)#起
                止=位置.get('end',{}) if isinstance(位置,dict) else getattr(getattr(位置,'end',None),'offset',None)#止
                起偏=起.get('offset') if isinstance(起,dict) else 起#起偏移
                止偏=止.get('offset') if isinstance(止,dict) else 止#止偏移
                if 起偏 is not None and 止偏 is not None and 原文[起偏:止偏]==值:#未转义
                    匹配=_本地图.match(值)#全匹配
                    if 匹配 is not None:#命中语法
                        路径=匹配.group(2)#url
                        if ' ' in 路径 and 分类文件类型(路径)=='image':#含空格且是图
                            图={'type':'image','alt':匹配.group(1),'url':路径,'position':位置}#image 节点
                            if isinstance(节点,dict):#dict 树
                                节点['children']=[图]#换成 image
                            else:#对象树
                                节点.children=[图]#换成 image
        elif isinstance(子表,list):#容器继续下钻
            for 子 in 子表:#递归
                访问(子)#访问
    访问(根)#从根开始
    return 根#同一棵树
