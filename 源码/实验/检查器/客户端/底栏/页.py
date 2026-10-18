'布局底槽里的窗口本地 NodeJS 诊断页'
from .....客户端.模块.客户端.通告 import 取握手窗口
import os
from .....客户端.ui_基础界面组件.按钮 import 按钮
from .....客户端.ui_基础界面组件.提示泡 import 提示泡
from .....客户端.存储 import 创建快照存储
from .文案 import 中文,英文
from .缩放 import 检查器缩放柄
from .键盘 import 绑定检查器键盘

__all__=['检查器页','登记检查器页']

命令标识='inspector.toggle'
样式标识='dsh-experimental-inspector-bottom'
下一面板号=[0]


class 检查器页:
    '底栏：缩放、收起，以及首次打开后保留的诊断页'
    def __init__(自身,属性):
        '默认高度为视口的 45%'
        自身.属性=属性
        自身.高度=45
        自身.根=None
        自身.框=None
        自身.释放键盘=None
        自身.提示=None
        自身.退订=None
        自身.已订=False
        自身.绘制中=False
        自身.待重画=False
        下一面板号[0]+=1
        自身.面板标识='inspector-panel-'+str(下一面板号[0])
        自身.渲染()

    def 更新(自身,属性):
        '换份额。渲染器接着会再画'
        自身.属性=属性

    def 拆除(自身):
        '退掉面板订阅，并拆掉键盘转发'
        退=自身.退订
        自身.退订=None
        if 退 is not None:
            退()
        释放=自身.释放键盘
        自身.释放键盘=None
        if 释放 is not None:
            释放()
        if 自身.提示 is not None and 自身.提示.卸 is not None:
            自身.提示.卸()
            自身.提示=None

    def 改高度(自身,值):
        '记下高度并写到当前面板'
        自身.高度=值
        if 自身.根 is not None:
            自身.根.style.setProperty('--inspector-height',f'{值}dvh')

    def 渲染(自身):
        '可见时出分隔条。离开 unopened 后保留诊断页'
        if 自身.绘制中:
            自身.待重画=True
            return 自身.根
        自身.绘制中=True
        try:
            窗口=取握手窗口()
            文档=窗口.document
            已有样式=文档.getElementById(样式标识)
            if 已有样式 is None:
                样式节点=文档.createElement('style')
                样式节点.id=样式标识
                样式路径=os.path.join(os.path.dirname(__file__),'页.module.css')
                with open(样式路径,'r',encoding='utf-8') as 样式文件:
                    样式节点.textContent=样式文件.read()
                文档.head.appendChild(样式节点)
            钩子=自身.属性.get('usePanel')
            if 自身.已订 is False and 钩子 is not None:
                自身.已订=True
                订=getattr(钩子,'_subscribe',None)
                if callable(订):
                    def 变更():
                        '面板开关变化时重画'
                        自身.渲染()
                    自身.退订=订(变更)

            def 原样(值):
                '面板状态原样取回'
                return 值

            if callable(钩子):
                状态=钩子(原样)
            else:
                状态='unopened'
            可见=状态=='visible'
            if 自身.根 is None:
                自身.根=文档.createElement('section')
                自身.根.id=自身.面板标识
                自身.根.className='panel'
                自身.根.setAttribute('data-inspector-panel','')
            自身.根.setAttribute('aria-label','NodeJS 诊断')
            自身.根.style.setProperty('--inspector-height',f'{自身.高度}dvh')
            自身.根.hidden=not 可见
            if 自身.提示 is not None and 自身.提示.卸 is not None:
                自身.提示.卸()
                自身.提示=None
            子=自身.根.firstChild
            while 子 is not None:
                下=子.nextSibling
                if 子 is not 自身.框:
                    子.remove()
                子=下
            if 可见:
                柄=检查器缩放柄({
                    'height':自身.高度,
                    'onResize':自身.改高度,
                    'label':'调整 NodeJS 诊断面板高度',
                    'panelId':自身.面板标识,
                })
                if 自身.框 is None:
                    自身.根.appendChild(柄.根)
                else:
                    自身.根.insertBefore(柄.根,自身.框)
            头=文档.createElement('header')
            头.className='header'
            字=文档.createElement('span')
            字.textContent='NodeJS 诊断'
            头.appendChild(字)
            图=文档.createElementNS('http://www.w3.org/2000/svg','svg')
            图.setAttribute('width','14')
            图.setAttribute('height','14')
            图.setAttribute('viewBox','0 0 16 16')
            图.setAttribute('fill','none')
            图.setAttribute('aria-hidden','true')
            图.setAttribute('stroke-width','1')
            for 线 in ('M2.5 2.5L13.5 13.5','M13.5 2.5L2.5 13.5'):
                路径=文档.createElementNS('http://www.w3.org/2000/svg','path')
                路径.setAttribute('d',线)
                路径.setAttribute('stroke','currentColor')
                图.appendChild(路径)
            钮=按钮({
                'window':窗口,
                'variant':'ghost',
                'size':'sm',
                'className':'close',
                'onClick':自身.属性['close'],
            })
            钮.渲染()
            钮.根.setAttribute('aria-label','收起')
            钮.根.appendChild(图)
            头.appendChild(钮.根)
            自身.提示=提示泡({
                'window':窗口,
                'label':'收起',
                'side':'top',
                'portal':True,
                'children':钮.根,
            })
            自身.提示.渲染()
            if 自身.框 is None:
                自身.根.appendChild(头)
            else:
                自身.根.insertBefore(头,自身.框)
            if 状态!='unopened' and 自身.框 is None:
                框=文档.createElement('iframe')
                框.className='page'
                框.src=自身.属性['frontendUrl']
                框.title='NodeJS 诊断'
                框.setAttribute('name','dsh-nodejs-inspector')
                框.setAttribute('referrerpolicy','no-referrer')
                框.setAttribute('data-inspector-devtools','')
                自身.框=框
                自身.根.appendChild(框)
                自身.释放键盘=自身.属性['bindFrame'](框)
            elif 状态=='unopened' and 自身.框 is not None:
                if 自身.释放键盘 is not None:
                    自身.释放键盘()
                    自身.释放键盘=None
                自身.框.remove()
                自身.框=None
        finally:
            自身.绘制中=False
        if 自身.待重画:
            自身.待重画=False
            return 自身.渲染()
        return 自身.根


def 登记检查器页(上下文,源标识):
    '为一个 Client 源登记底栏内容和窗口本地切换命令'
    查询='disableLocaleInfoBar=true&clientSourceId='+str(源标识)
    前端网址='inspector/devtools/devtools_app.html?'+查询

    def 卸词典():
        '登记底栏中英文案表。页面上的字不走英文表'
        return 上下文.locale.register('inspectorPanel',{'zh':中文,'en':英文})

    上下文.副作用(卸词典,'inspector: bottom dictionaries')

    def 挂():
        '快捷键与底栏槽一起装、一起卸'
        面板=创建快照存储('unopened')
        打开者={'元素':None}

        def 关闭():
            '可见时收起，并把焦点还给打开它的元素'
            if 面板.getSnapshot()!='visible':
                return
            面板.set('hidden')
            元素=打开者['元素']
            if 元素 is not None and getattr(元素,'isConnected',False):
                元素.focus()

        def 读绑定():
            '当前生效绑定，含用户覆盖'
            目录=上下文.shortcuts.catalog.getSnapshot()
            for 行 in 目录 or []:
                if 行.get('id')==命令标识:
                    return 行.get('binding')
            return None

        def 切换标签():
            '快捷键目录上的中文'
            return '展开或收起 NodeJS 诊断'

        def 解决(事件):
            '展开或收起'
            def 运行():
                '可见则关闭，否则记下焦点来源再展开'
                if 面板.getSnapshot()=='visible':
                    关闭()
                    return
                目标=事件.get('target') if isinstance(事件,dict) else None
                打开者['元素']=目标 if 目标 is not None and hasattr(目标,'focus') else None
                面板.set('visible')
            return {'status':'handled','run':运行}

        默认键={'code':'Period','modifiers':['primary','shift']}
        默认={}
        for 运行时 in ('desktop','web'):
            for 系统 in ('macos','windows','linux'):
                默认[运行时+':'+系统]=dict(默认键)
        yield 上下文.shortcuts.register({
            'id':命令标识,
            'label':切换标签,
            'aliases':['inspector','nodejs','devtools'],
            'defaults':默认,
            'regions':['page','editable','terminal'],
            'modals':[],
            'resolve':解决,
        })

        def 注入():
            '底栏看到的地址、关闭和键盘转发'
            def 绑框(框):
                '把当前快捷键绑定装到诊断页'
                return 绑定检查器键盘(框,读绑定)
            return {
                'frontendUrl':前端网址,
                'close':关闭,
                'hooks':{'panel':面板},
                'bindFrame':绑框,
            }

        yield 上下文.slots.register({
            'name':'shell.bottom',
            'locale':'inspectorPanel',
            'inject':注入,
        },检查器页)

    return 上下文.slots.inject('shell.bottom',挂)
