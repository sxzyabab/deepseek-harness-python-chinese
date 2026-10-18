'停靠分割树。份额用 flex，分割条可以拖。拖的过程先改预览，松手才记一条'
import pywebbridge
from ..引擎.树 import 取节点
from .标签面板 import 标签面板
from .渲染 import 类名,注入样式

__all__=['窗格树']

class 窗格树:
    '画出一个分割或一块窗格，以及它下面的全部'
    def __init__(自身,属性):
        '从给定节点往下画'
        自身.属性=属性
        自身.根=None
        自身.面板=None
        自身.子树=[]
        自身.格=[]
        自身.渲染()

    def 渲染(自身):
        '窗格交给标签面板。分割按轴排开，中间夹分割条'
        窗口=自身.属性['window']
        文档=窗口.document
        注入样式(文档)
        状态=自身.属性['state']
        节点=取节点(状态,自身.属性['nodeId'])
        回调=自身.属性['callbacks']
        if 节点['kind']=='pane':
            if 自身.根 is not None and 自身.根.parentNode is not None:
                父=自身.根.parentNode
            else:
                父=自身.属性.get('parent')
            自身.面板=标签面板({
                'window':窗口,
                'state':状态,
                'pane':节点,
                'callbacks':回调,
            })
            根=自身.面板.根
            if 自身.根 is not None and 自身.根 is not 根:
                自身.根.replaceWith(根)
            elif 父 is not None and 根.parentNode is None:
                父.appendChild(根)
            自身.根=根
            自身.子树=[]
            自身.格=[]
            return 根
        预览=自身.属性.get('preview')
        if 预览 is not None and 预览['splitId']==节点['id']:
            份额=预览['sizes']
        else:
            份额=节点['sizes']
        if 自身.根 is not None and 自身.根.parentNode is not None:
            父=自身.根.parentNode
        else:
            父=自身.属性.get('parent')
        for 树 in 自身.子树:
            树.拆除()
        根=文档.createElement('div')
        根.className=类名('split',节点['axis']=='row' and 'splitRow',节点['axis']!='row' and 'splitColumn')
        根.setAttribute('data-dockkit-split',节点['id'])
        自身.子树=[]
        自身.格=[]
        for 序号,子标识 in enumerate(节点['children']):
            if 序号>0:
                条=文档.createElement('div')
                条.className='divider'
                条.setAttribute('data-dockkit-divider',f'{节点["id"]}:{序号-1}')

                def 按下(事件,标识=节点['id'],界=序号-1):
                    '分割条按下交给表面'
                    回调['onDividerPressed'](标识,界,事件)

                条.addEventListener('pointerdown',按下)
                根.appendChild(条)
            格=文档.createElement('div')
            格.className='splitCell'
            格.setAttribute('data-dockkit-cell',f'{节点["id"]}:{序号}')
            格.style.flexGrow=str(份额[序号])
            树=窗格树({
                'window':窗口,
                'state':状态,
                'nodeId':子标识,
                'callbacks':回调,
                'preview':预览,
                'parent':格,
            })
            自身.子树.append(树)
            自身.格.append(格)
            根.appendChild(格)
        if 自身.根 is not None:
            自身.根.replaceWith(根)
        elif 父 is not None:
            父.appendChild(根)
        自身.根=根
        return 根

    def 套预览(自身,回调,预览):
        '只改这一层的份额和投放提示'
        自身.属性['callbacks']=回调
        自身.属性['preview']=预览
        if 自身.面板 is not None:
            自身.面板.套预览(回调)
            return
        状态=自身.属性['state']
        节点=取节点(状态,自身.属性['nodeId'])
        if 节点['kind']!='split':
            return
        if 预览 is not None and 预览['splitId']==节点['id']:
            份额=预览['sizes']
        else:
            份额=节点['sizes']
        for 序号,格 in enumerate(自身.格):
            if 序号<len(份额):
                格.style.flexGrow=str(份额[序号])
        for 树 in 自身.子树:
            树.套预览(回调,预览)

    def 更新(自身,属性):
        '树变了就重画'
        if 自身.面板 is not None:
            自身.面板.拆除()
            自身.面板=None
        自身.属性=属性
        return 自身.渲染()

    def 拆除(自身):
        '卸掉下面的面板'
        if 自身.面板 is not None:
            自身.面板.拆除()
        for 树 in 自身.子树:
            树.拆除()
