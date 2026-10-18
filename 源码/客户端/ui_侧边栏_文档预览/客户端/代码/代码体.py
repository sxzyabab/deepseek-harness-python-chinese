from ....模块.客户端.通告 import 取握手窗口
import os
from .....工具.工作区路径 import 解析文件地址
from ....ui_对话.异常 import 注入模块样式文件,模块节点
from ....ui_基础界面组件.markdown.代码块 import 代码块
from ....ui_基础界面组件.代码高亮语法 import 路径语言
from .文案 import 中文

__all__=['代码体']

样式模块='code-body'

class 代码体:
    '累积的源文本和高亮。字节内容不画'
    def __init__(自身,属性=None):
        '记下文档 props'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.根=None
        if 'content' in 自身.属性 and 'window' in 自身.属性:
            自身.渲染()

    def 更新(自身,属性):
        '换成新的 props'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 渲染(自身):
        '一块稳定的代码块。不是文本就空'
        if 自身.根 is not None:
            自身.根.remove()
            自身.根=None
        属性=自身.属性
        内容=属性['content']
        if 内容['kind']!='text':
            return None
        文件=解析文件地址(属性['resourceAddress'])
        if not isinstance(文件,dict):
            raise ValueError('ui-sidebar-documentpreview: not a file address "'+str(属性['resourceAddress'])+'"')
        窗口=属性['window'] if 'window' in 属性 else 取握手窗口()
        文档=窗口.document
        注入模块样式文件(
            文档,
            '代码体样式',
            os.path.join(os.path.dirname(__file__),'代码体.module.css'),
            样式模块,
        )
        根=模块节点(文档,'div',样式模块,'renderer')
        根.setAttribute('data-code-preview','')
        根.setAttribute('data-wrap','true' if 属性.get('wrap') is True else 'false')
        块=代码块({
            'window':窗口,
            'className':'code',
            'contentRef':属性.get('scrollportRef'),
            'code':内容['text'],
            'lang':路径语言(文件['path']),
            'streaming':内容.get('eof') is not True,
            'wrap':属性.get('wrap') is True,
            'lineNumbers':True,
            'copyLabel':中文['copy'],
            'copiedLabel':中文['copied'],
            'toolbarLabels':{
                'codeLabel':'代码块',
                'wrapLabel':'自动换行',
                'unwrapLabel':'取消自动换行',
            },
        }).渲染()
        标=块
        if 标 is not None:
            根.appendChild(标)
        if 'parent' in 属性 and 属性['parent'] is not None:
            属性['parent'].appendChild(根)
        自身.根=根
        return 自身.根

    def __call__(自身,属性=None):
        '再次调用时先换 props 再画'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()
