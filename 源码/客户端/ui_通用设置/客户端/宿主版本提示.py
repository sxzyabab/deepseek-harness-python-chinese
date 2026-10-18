import os
from ...ui_对话.异常 import 注入模块样式文件,标样式模块,模块节点
from ...ui_基础界面组件.按钮 import 处理按钮
from ...ui_基础界面组件.模态 import 处理模态
from .文案 import 中文

__all__=['宿主版本提示']

样式模块='hostRelease'

def 过渡文字(起,止,未知):
    '两端版本不同就写版本，否则写提交。缺的一端或字段用未解析'
    起版=起.get('version') if isinstance(起,dict) else None
    止版=止.get('version') if isinstance(止,dict) else None
    字段='commit' if 起版==止版 else 'version'
    def 取(端):
        '这一端要显示的字'
        if isinstance(端,dict) is False:
            return 未知
        值=端.get(字段)
        if 值 is None:
            return 未知
        return str(值)
    return 取(起),取(止)

class 版本过渡:
    '一行版本过渡。完成的淡化起点，未完成的淡化终点'
    def __init__(自身,属性):
        '记下份额并画出'
        自身.属性=属性
        自身.根=None
        自身.渲染()

    def 渲染(自身):
        '四个格子交给外面的网格'
        属性=自身.属性
        窗口=属性['window']
        文档=窗口.document
        完成=属性['done'] is True
        片段=文档.createDocumentFragment()
        名=模块节点(文档,'span',样式模块,'label')
        名.textContent=属性['label']
        片段.appendChild(名)
        起类='release solid' if 完成 is False else 'release faded'
        起=模块节点(文档,'span',样式模块,起类)
        起.textContent=属性['from']
        片段.appendChild(起)
        线类='line done' if 完成 else 'line pending'
        线=模块节点(文档,'span',样式模块,线类)
        线.setAttribute('aria-hidden','true')
        片段.appendChild(线)
        止类='release solid' if 完成 else 'release faded'
        止=模块节点(文档,'span',样式模块,止类)
        止.textContent=属性['to']
        片段.appendChild(止)
        自身.根=片段
        return 片段

class 宿主版本提示:
    '宿主换成另一发行版时询问是否刷新。关掉对话框就留在本页'
    def __init__(自身,属性):
        '记下份额并画出'
        自身.属性=属性
        自身.根=None
        自身.已订=False
        自身.退订=[]
        自身.绘制中=False
        自身.待重画=False
        自身.渲染()

    def 更新(自身,属性):
        '换份额'
        自身.属性=属性

    def 拆订阅(自身):
        '退掉发行变化'
        for 退 in 自身.退订:
            退()
        自身.退订=[]
        自身.已订=False

    def 渲染(自身):
        '没有变化就不画。服务行是已完成的切换，页面行要等刷新'
        if 自身.绘制中:
            自身.待重画=True
            return 自身.根
        自身.绘制中=True
        try:
            属性=自身.属性
            窗口=属性['window']
            文档=窗口.document
            注入模块样式文件(
                文档,
                '宿主版本提示样式',
                os.path.join(os.path.dirname(__file__),'宿主版本提示.module.css'),
                样式模块,
            )
            def 全量(值):
                '当前发行变化'
                return 值
            变化=属性['useReleaseChange'](全量)
            if 自身.根 is None:
                自身.根=文档.createElement('div')
                自身.根.style.display='contents'
            else:
                while 自身.根.firstChild is not None:
                    自身.根.firstChild.remove()
            if 变化 is not None:
                未知=中文['hostRelease.unknown']
                服务起,服务止=过渡文字(变化.get('previous'),变化.get('host'),未知)
                页面起,页面止=过渡文字(变化.get('page'),变化.get('host'),未知)
                格=模块节点(文档,'div',样式模块,'transitions')
                格.appendChild(版本过渡({
                    'window':窗口,
                    'label':中文['hostRelease.service'],
                    'from':服务起,
                    'to':服务止,
                    'done':True,
                }).渲染())
                格.appendChild(版本过渡({
                    'window':窗口,
                    'label':中文['hostRelease.page'],
                    'from':页面起,
                    'to':页面止,
                    'done':False,
                }).渲染())
                稍后=处理按钮(窗口,{
                    'variant':'outline',
                    'children':中文['hostRelease.later'],
                    'onClick':属性['dismissRelease'],
                })
                稍后.setAttribute('data-modal-autofocus','')
                刷新=处理按钮(窗口,{
                    'variant':'primary',
                    'children':中文['hostRelease.reload'],
                    'onClick':属性['reloadPage'],
                })
                罩=处理模态(窗口,{
                    'open':True,
                    'title':中文['hostRelease.title'],
                    'description':中文['hostRelease.description'],
                    'closeLabel':中文['hostRelease.later'],
                    'onClose':属性['dismissRelease'],
                    'className':'dialog',
                    'footer':[稍后,刷新],
                    'children':格,
                })
                卡=罩.querySelector('.模态')
                if 卡 is not None:
                    标样式模块(卡,样式模块)
                自身.根.appendChild(罩)
            if 自身.已订 is False:
                自身.已订=True
                钩=属性['useReleaseChange']
                if hasattr(钩,'_subscribe') and callable(钩._subscribe):
                    def 变更():
                        '发行变化了就重画。已经不在页面上就退订'
                        if 自身.绘制中:
                            自身.待重画=True
                            return
                        if 自身.根 is None or 自身.根.parentNode is None:
                            自身.拆订阅()
                            return
                        自身.渲染()
                    退=钩._subscribe(变更)
                    if callable(退):
                        自身.退订.append(退)
        finally:
            自身.绘制中=False
        if 自身.待重画:
            自身.待重画=False
            return 自身.渲染()
        return 自身.根

    def 拆除(自身):
        '退掉发行变化'
        自身.拆订阅()
