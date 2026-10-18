'稳定的标签格子。选中、搬家、浮动都不改这张标签的祖先，避免把已经连上的网页视图挪走'
import pywebbridge
from ..异常 import 停靠错误
from ..引擎.树 import 查找标签窗格,浮动矩形,取节点,取窗格
from .浮动层 import 浮动头,使用浮动手势
from .标签面板 import 标签条,投放提示,标签面板
from .渲染 import 类名,标有无,标值,挂上,清空,注入样式

__all__=['标签布局']

class 标签宿主:
    '一张标签的格子。浮动和停靠共用这一份正文'
    def __init__(自身,属性):
        '画出格子、页眉和正文'
        自身.属性=属性
        自身.根=None
        自身.节=None
        自身.身=None
        自身.条=None
        自身.头=None
        自身.提示=None
        自身.到过=False
        自身.渲染()

    def 渲染(自身):
        '按现在是不是选中、是不是浮动来摆'
        窗口=自身.属性['window']
        文档=窗口.document
        注入样式(文档)
        状态=自身.属性['state']
        回调=自身.属性['callbacks']
        标签=自身.属性['tab']
        窗格=自身.属性['pane']
        浮动=窗格['host']=='float'
        选定=浮动 or 窗格['activeTabId']==标签['id']
        活动=自身.属性.get('active')
        if 活动 is None:
            活动=True
        可见=活动 and 选定 and (浮动 or 状态['expanded'])
        保留=False
        if 自身.属性.get('keepMounted') is not None:
            保留=自身.属性['keepMounted'](标签)
        if 可见:
            自身.到过=True
        手势=自身.属性['floats']
        抬=手势['预览']['值']
        if 浮动 and 抬 is not None and 抬['paneId']==窗格['id']:
            矩形=抬['rect']
            层=len(状态['floats'])+1
        elif 浮动:
            矩形=浮动矩形(窗格)
            层=状态['floats'].index(窗格['id'])+1 if 窗格['id'] in 状态['floats'] else 1
        else:
            矩形=None
            层=0
        列=自身.属性['column']
        if 自身.根 is None:
            自身.根=文档.createElement('div')
        else:
            清空(自身.根)
            if 自身.条 is not None:
                自身.条.拆除()
                自身.条=None
            if 自身.头 is not None:
                自身.头.拆除()
                自身.头=None
        自身.根.className=类名('tabCell',浮动 and 'floatingCell')
        自身.根.hidden=not 选定
        自身.根.setAttribute('data-dockkit-host','float' if 浮动 else 'dock')
        标值(自身.根,'data-dockkit-column',None if 浮动 else 列)
        if 浮动:
            自身.根.style.gridColumn='1'
            自身.根.style.order=str(层)
        else:
            自身.根.style.gridColumn=str(列*2+1)
            自身.根.style.order='0'
        自身.根.style.gridRow='1'
        节=文档.createElement('section')
        节.tabIndex=-1
        节.className=类名('tabHost',浮动 and 'float',(not 浮动) and 'pane')
        标值(节,'aria-hidden',None if 可见 else 'true')
        节.setAttribute('data-dockkit-content',标签['id'])
        标值(节,'data-dockkit-pane',窗格['id'] if (not 浮动 and 选定) else None)
        标有无(节,'data-dockkit-pane-active',(not 浮动) and 状态['activePaneId']==窗格['id'])
        标值(节,'data-dockkit-float',窗格['id'] if 浮动 else None)
        标有无(节,'data-dockkit-float-active',浮动 and 状态['activePaneId']==窗格['id'])
        标值(节,'data-dockkit-column',None if 浮动 else 列)
        if 矩形 is not None:
            节.style.left=f'{矩形["x"]}px'
            节.style.top=f'max(var(--dsh-dockkit-float-top, 0px), {矩形["y"]}px)'
            节.style.width=f'{矩形["width"]}px'
            节.style.height=f'{矩形["height"]}px'
        节.inert=not 可见

        def 按节(事件):
            '浮动面板按下去就抬起'
            if 窗格['host']=='float':
                手势['抬起'](窗格['id'])

        def 点节(事件):
            '停靠窗格点一下，还不是活动窗格就聚焦'
            if 窗格['host']!='float' and 状态['activePaneId']!=窗格['id']:
                回调['onFocusPane'](窗格['id'])

        节.addEventListener('pointerdown',按节)
        节.addEventListener('click',点节)
        头盒=文档.createElement('div')
        头盒.className='tabHostHeader'
        if 选定:
            if 浮动:
                自身.头=浮动头({
                    'window':窗口,
                    'paneId':窗格['id'],
                    'tab':标签,
                    'labels':回调['labels'],
                    'intents':自身.属性['intents'],
                    'renderTabTitle':回调.get('renderTabTitle'),
                    'canCloseTab':回调.get('canCloseTab'),
                    'drag':手势['拖'],
                    'parent':头盒,
                })
            else:
                自身.条=标签条({
                    'window':窗口,
                    'state':状态,
                    'pane':窗格,
                    'callbacks':回调,
                    'parent':头盒,
                })
        节.appendChild(头盒)
        身=文档.createElement('div')
        身.className=类名('tabHostBody',浮动 and 'floatBody',(not 浮动) and 'paneBody')

        def 焦点进来(事件):
            '正文拿到焦点时，浮动的抬起，停靠的聚焦窗格'
            if not 可见:
                return
            if 浮动:
                手势['抬起'](窗格['id'])
            elif 状态['activePaneId']!=窗格['id']:
                回调['onFocusPane'](窗格['id'])

        身.addEventListener('focus',焦点进来,True)
        if 自身.到过 and (保留 or (活动 and 选定)):
            挂上(身,回调['renderTab'](标签))
        if not 浮动:
            自身.提示=投放提示({'window':窗口,'pane':窗格,'callbacks':回调})
            身.appendChild(自身.提示.根)
        节.appendChild(身)
        if 浮动:
            角=文档.createElement('div')
            角.className='floatResize'
            角.setAttribute('data-dockkit-float-resize',窗格['id'])

            def 按角(事件):
                '右下角开始缩放'
                手势['拖']('resize',窗格['id'],事件)

            角.addEventListener('pointerdown',按角)
            节.appendChild(角)
        自身.根.appendChild(节)
        自身.节=节
        自身.身=身
        if not 可见:
            焦点=文档.activeElement
            if 焦点 is not None and hasattr(焦点,'blur') and 节.contains(焦点):
                焦点.blur()
        盒=自身.属性.get('focusRequest')
        请求=None if 盒 is None else 盒.get('当前')
        if 可见 and 请求 is not None and 请求.get('tabId')==标签['id']:
            盒['当前']=None
            焦点=文档.activeElement
            来源=请求.get('origin')
            if 焦点 is None or 焦点 is 文档.body or 焦点 is 文档.documentElement or 焦点 is 来源:
                条带=节.querySelector('[data-dockkit-strip]')
                if 条带 is not None:
                    for 芯片 in 条带.querySelectorAll('[data-dockkit-tab]'):
                        if 芯片.getAttribute('data-dockkit-tab')==标签['id']:
                            芯片.focus({'preventScroll':True})
                            break
        if 'parent' in 自身.属性 and 自身.根.parentNode is None:
            自身.属性['parent'].appendChild(自身.根)
        return 自身.根

    def 套预览(自身,回调):
        '投放预览只改条带和提示'
        自身.属性['callbacks']=回调
        if 自身.条 is not None:
            自身.条.属性['callbacks']=回调
            自身.条.套预览()
        if 自身.提示 is not None:
            自身.提示.更新({
                'window':自身.属性['window'],
                'pane':自身.属性['pane'],
                'callbacks':回调,
            })

    def 套浮动(自身):
        '浮动预览只改几何和叠放'
        窗格=自身.属性['pane']
        if 窗格['host']!='float' or 自身.节 is None:
            return
        状态=自身.属性['state']
        抬=自身.属性['floats']['预览']['值']
        if 抬 is not None and 抬['paneId']==窗格['id']:
            矩形=抬['rect']
            层=len(状态['floats'])+1
        else:
            矩形=浮动矩形(窗格)
            层=状态['floats'].index(窗格['id'])+1
        自身.节.style.left=f'{矩形["x"]}px'
        自身.节.style.top=f'max(var(--dsh-dockkit-float-top, 0px), {矩形["y"]}px)'
        自身.节.style.width=f'{矩形["width"]}px'
        自身.节.style.height=f'{矩形["height"]}px'
        自身.根.style.order=str(层)

    def 拆除(自身):
        '卸掉条带和页眉'
        if 自身.条 is not None:
            自身.条.拆除()
        if 自身.头 is not None:
            自身.头.拆除()

class 标签布局:
    '一块窗格，或左右两块。浮动标签也在这棵稳定的格子里'
    def __init__(自身,属性):
        '画出格子。不是一行一块或两块就拒绝'
        自身.属性=属性
        自身.根=None
        自身.宿主={}
        自身.空面板=[]
        if 'focusRequest' in 属性 and 属性['focusRequest'] is not None:
            自身.焦点=属性['focusRequest']
        else:
            自身.焦点={'当前':None}
        自身.手势=None
        自身.渲染()

    def 渲染(自身):
        '按标签标识排序挂格子，空窗格单独补一条'
        窗口=自身.属性['window']
        文档=窗口.document
        注入样式(文档)
        状态=自身.属性['state']
        回调=自身.属性['callbacks']
        根节点=取节点(状态,状态['rootId'])
        if 根节点['kind']=='split' and (根节点['axis']!='row' or len(根节点['children'])!=2):
            raise 停靠错误('DockLayout requires one pane or two horizontally split panes')
        if 根节点['kind']=='pane':
            窗格列=[根节点]
            份额=[1]
        else:
            窗格列=[]
            for 标识 in 根节点['children']:
                窗格列.append(取窗格(状态,标识))
            预览=自身.属性.get('preview')
            if 预览 is not None and 预览['splitId']==根节点['id']:
                份额=预览['sizes']
            else:
                份额=根节点['sizes']
        if 自身.手势 is not None:
            自身.手势['拆除']()
        def 预览变了():
            '浮动几何跟着预览走'
            for 宿主 in 自身.宿主.values():
                宿主.套浮动()
        自身.手势=使用浮动手势(状态,自身.属性['intents'],窗口,预览变了)
        包回调=dict(回调)
        def 聚焦标签(标签标识):
            '换了选中正文才请求把焦点送回芯片'
            if 查找标签窗格(状态,标签标识)['activeTabId']==标签标识:
                自身.焦点['当前']=None
            else:
                自身.焦点['当前']={'tabId':标签标识,'origin':文档.activeElement}
            回调['onFocusTab'](标签标识)
        包回调['onFocusTab']=聚焦标签
        if 自身.根 is None:
            自身.根=文档.createElement('div')
            自身.根.className='tabLayout'
        else:
            清空(自身.根)
            for 宿主 in 自身.宿主.values():
                宿主.拆除()
            自身.宿主={}
            自身.空面板=[]
        列文=[]
        for 大小 in 份额:
            列文.append(f'minmax(0, {大小}fr)')
        自身.根.style.gridTemplateColumns=' 0px '.join(列文)
        if 根节点['kind']=='split':
            自身.根.setAttribute('data-dockkit-split',根节点['id'])
        else:
            自身.根.removeAttribute('data-dockkit-split')
        标签列=list(状态['tabs'].values())
        def 按标识(标签):
            '按标签标识排序，避免顺序变化挪动网页视图的祖先'
            return 标签['id']
        标签列.sort(key=按标识)
        for 标签 in 标签列:
            窗格=查找标签窗格(状态,标签['id'])
            列=0
            for 序号,候选 in enumerate(窗格列):
                if 候选['id']==窗格['id']:
                    列=序号
            宿主=标签宿主({
                'window':窗口,
                'state':状态,
                'callbacks':包回调,
                'intents':自身.属性['intents'],
                'tab':标签,
                'pane':窗格,
                'column':列,
                'floats':自身.手势,
                'focusRequest':自身.焦点,
                'keepMounted':自身.属性.get('keepMounted'),
                'active':自身.属性.get('active',True),
                'parent':自身.根,
            })
            自身.宿主[标签['id']]=宿主
        for 窗格 in 窗格列:
            if len(窗格['tabs'])!=0:
                continue
            空=文档.createElement('div')
            空.className='emptyTabHost'
            空.setAttribute('data-dockkit-empty','')
            位=窗格列.index(窗格)
            空.style.gridColumn=str(位*2+1)
            空.style.gridRow='1'
            自身.根.appendChild(空)
            自身.空面板.append(标签面板({
                'window':窗口,
                'state':状态,
                'pane':窗格,
                'callbacks':回调,
                'parent':空,
            }))
        if 根节点['kind']=='split':
            条=文档.createElement('div')
            条.className=类名('divider','tabLayoutDivider')
            条.setAttribute('data-dockkit-divider',f'{根节点["id"]}:0')
            条.style.gridColumn='2'
            条.style.gridRow='1'

            def 按下(事件):
                '中间这条分割条'
                回调['onDividerPressed'](根节点['id'],0,事件)

            条.addEventListener('pointerdown',按下)
            自身.根.appendChild(条)
        if 'parent' in 自身.属性 and 自身.根.parentNode is None:
            自身.属性['parent'].appendChild(自身.根)
        return 自身.根

    def 套预览(自身,回调,预览):
        '分割预览改轨道，投放预览改每张标签的条带'
        自身.属性['callbacks']=回调
        自身.属性['preview']=预览
        状态=自身.属性['state']
        根节点=取节点(状态,状态['rootId'])
        if 根节点['kind']=='split':
            if 预览 is not None and 预览['splitId']==根节点['id']:
                份额=预览['sizes']
            else:
                份额=根节点['sizes']
            列文=[]
            for 大小 in 份额:
                列文.append(f'minmax(0, {大小}fr)')
            自身.根.style.gridTemplateColumns=' 0px '.join(列文)
        for 宿主 in 自身.宿主.values():
            宿主.套预览(回调)
        for 面板 in 自身.空面板:
            面板.套预览(回调)

    def 更新(自身,属性):
        '布局变了就重画格子'
        自身.属性=属性
        return 自身.渲染()

    def 拆除(自身):
        '卸掉手势和格子'
        if 自身.手势 is not None:
            自身.手势['拆除']()
        for 宿主 in 自身.宿主.values():
            宿主.拆除()
