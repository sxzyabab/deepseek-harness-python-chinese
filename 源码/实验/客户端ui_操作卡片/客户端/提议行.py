'propose_action 的一行过程：卡片标题，以及这张卡片有没有显示出来'
import os
from ....客户端.模块.客户端.通告 import 取握手窗口
from ....客户端.ui_对话.异常 import 注入模块样式文件,标样式模块,模块节点
from ....客户端.ui_基础界面组件.披露行 import 披露行

__all__=['提议行']

样式模块='action-propose'


def 窗口于(属性):
    '宿主窗口。没有时用当前页'
    if isinstance(属性,dict) and 'window' in 属性:
        return 属性['window']
    return 取握手窗口()


def 确保样式(文档):
    '把过程行样式模块插进文档'
    注入模块样式文件(
        文档,
        '操作卡片提议行样式',
        os.path.join(os.path.dirname(__file__),'提议行.module.css'),
        样式模块,
    )


def 建(文档,标签名,类名):
    '造出带官方类名和样式模块标记的节点'
    return 模块节点(文档,标签名,样式模块,类名)


def 换根(自身,新根):
    '已经在页面上就替换'
    旧=自身.根
    if 旧 is not None and 旧.parentNode is not None and 旧 is not 新根:
        旧.parentNode.replaceChild(新根,旧)
    自身.根=新根
    return 新根


def 行状态(属性):
    '准备中的调用还没有完整参数'
    if 属性.get('phase')=='preparing':
        return 'preparing'
    if 属性.get('phase')=='start':
        return 'running'
    块=属性.get('block')
    if isinstance(块,dict) and isinstance(块.get('error'),dict) and 块['error'].get('code')=='interrupted':
        return 'stopped'
    if isinstance(块,dict) and 块.get('isError') is True:
        return 'error'
    return 'ok'


def 原因文本(属性):
    '只有被拒绝的结果才展开原因'
    if 属性.get('phase')!='result':
        return ''
    块=属性.get('block')
    if not isinstance(块,dict) or 块.get('isError') is not True:
        return ''
    内容=块.get('content')
    if not isinstance(内容,list):
        return ''
    行=[]
    for 项 in 内容:
        if isinstance(项,dict) and 项.get('type')=='text' and isinstance(项.get('text'),str):
            行.append(项['text'])
    return '\n'.join(行)


class 提议行:
    '按记录的参数和结果画一行。只有被拒绝的调用能展开'
    def __init__(自身,属性=None):
        '默认收起'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.展开=False
        自身.根=None
        if 'window' in 自身.属性:
            自身.渲染()

    def 更新(自身,属性):
        '换调用份额'
        自身.属性=属性

    def 点切换(自身,事件=None):
        '展开或收起原因'
        自身.展开=not 自身.展开
        自身.渲染()

    def 渲染(自身):
        '标题旁边是状态和卡片标题'
        属性=自身.属性
        窗口=窗口于(属性)
        文档=窗口.document
        确保样式(文档)
        译=属性['t']
        块=属性.get('block') if isinstance(属性.get('block'),dict) else {}
        状态=行状态(属性)
        参数=块.get('args')
        标题=''
        if 参数 is not None and callable(getattr(参数,'text',None)):
            读到=参数.text('title')
            标题='' if 读到 is None else str(读到)
        elif isinstance(参数,dict):
            标题='' if 参数.get('title') is None else str(参数.get('title'))
        原因=原因文本(属性)
        根=建(文档,'div',None)
        根.setAttribute('data-tool','propose_action')
        根.setAttribute('data-state',状态)
        摘要=建(文档,'span','summary')
        状态文=文档.createElement('span')
        状态文.textContent=译('row.'+状态)
        标题文=建(文档,'span','title')
        标题文.textContent=标题
        摘要.appendChild(状态文)
        摘要.appendChild(标题文)
        原因节点=建(文档,'pre','reason')
        原因节点.textContent=原因
        子=[]
        子.append(原因节点)
        检查=属性.get('inspect')
        if callable(检查):
            检查按钮=文档.createElement('button')
            检查按钮.type='button'
            检查按钮.className='inspect'
            标样式模块(检查按钮,样式模块)
            检查按钮.textContent=译('row.inspect')
            检查按钮.addEventListener('click',检查)
            子.append(检查按钮)
        行=披露行({
            'window':窗口,
            'title':译('row.title'),
            'running':状态 in ('preparing','running'),
            'open':自身.展开 and 原因!='',
            'expandable':原因!='',
            'expandOnRowClick':True,
            'keepContentWhenOpen':True,
            'onToggle':自身.点切换,
            'collapsedContent':摘要,
            'children':子,
        }).渲染()
        根.appendChild(行)
        return 换根(自身,根)
