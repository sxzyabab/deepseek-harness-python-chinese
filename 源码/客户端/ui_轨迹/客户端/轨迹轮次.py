import importlib.resources as 包资源
import pywebbridge
from .轨迹轮次头 import 轨迹轮次头#粘性头

样式文本=包资源.files(__package__).joinpath('轨迹轮次.module.css').read_text(encoding='utf-8')

class 轨迹轮次:
    '粘性头加正文'
    def __init__(自身,属性):
        '记下属性并画出轮次'
        自身.属性=属性
        自身.根=None
        自身.渲染()

    def __call__(自身,属性=None):
        '属性变了就重画'
        if 属性 is not None:
            自身.属性=属性
        return 自身.渲染()

    def 渲染(自身):
        '画出一轮：头和正文'
        属性=自身.属性
        窗口=属性['window']
        文档=窗口.document
        if 文档.getElementById('轨迹轮次样式') is None:
            样式=文档.createElement('style')
            样式.id='轨迹轮次样式'
            样式.textContent=样式文本
            文档.head.appendChild(样式)
        旧=自身.根
        父=None if 旧 is None else 旧.parentNode
        if 旧 is not None:
            旧.remove()
        根=文档.createElement('section')
        根.className='root'
        根.setAttribute('data-turn',str(属性.get('turn') or 1))
        头=轨迹轮次头({'window':窗口,'turn':属性.get('turn') or 1,'parent':根})
        体=文档.createElement('div')
        体.className='body'
        for 子 in 属性.get('children') or []:
            if 子 is not None:
                体.appendChild(子)
        根.appendChild(体)
        自身.根=根
        自身.头=头
        if 父 is None and 属性.get('parent') is not None:
            父=属性['parent']
        if 父 is not None and 根.parentNode is not 父:
            父.appendChild(根)
        return 根
