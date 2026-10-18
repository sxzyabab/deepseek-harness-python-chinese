import importlib.resources as 包资源
import pywebbridge
from ...ui_基础界面组件.icons import 图标勾16
from ...ui_基础界面组件.锚定最大高度 import 锚定最大高度
from ...ui_基础界面组件.风险确认 import 风险确认
from .弹出层 import 过滤选项
from .选项组 import 分组选项

__all__=['弹出选择视图']

样式文本=包资源.files(__package__).joinpath('弹出选择视图.module.css').read_text(encoding='utf-8')
设计高度=320

def 登记样式(文档):
    '同一份弹出样式整个文档只插一次'
    if 文档.getElementById('弹出选择视图样式') is not None:
        return
    样式=文档.createElement('style')
    样式.id='弹出选择视图样式'
    样式.textContent=样式文本
    文档.head.appendChild(样式)

def 键名(事件):
    '从键盘事件取出 key 和是否按着 Shift'
    键=getattr(事件,'key',None)
    移位=getattr(事件,'shiftKey',None) is True
    if isinstance(键,str):
        return 键,移位
    参数=getattr(事件,'args',None)
    if isinstance(参数,dict):
        键=参数.get('key') if isinstance(参数.get('key'),str) else ''
        移位=参数.get('shiftKey') is True
        return 键,移位
    return '',False

def 观察粘性菜单组(窗口,视口):
    '标题在滚过视口顶沿时标上 data-stuck。没有观察器就保持透明'
    if not hasattr(窗口,'IntersectionObserver') or not hasattr(窗口,'ResizeObserver'):
        def 空拆():
            '没有观察器，不用拆'
            return None
        return 空拆
    节表=[]
    for 节 in 视口.querySelectorAll(':scope > [data-menu-group]'):
        标题=节.querySelector(':scope > [data-menu-group-heading]')
        起点=节.querySelector(':scope > [data-menu-group-start]')
        if 标题 is None or 起点 is None:
            continue
        节表.append({
            'section':节,
            'heading':标题,
            'start':起点,
            'atTop':False,
            'above':False,
            'topTime':float('-inf'),
            'aboveTime':float('-inf'),
        })
    if len(节表)==0:
        def 空拆():
            '没有分组，不用拆'
            return None
        return 空拆
    按节={}
    按起点={}
    for 组 in 节表:
        按节[组['section']]=组
        按起点[组['start']]=组
    已拆={'值':False}
    条带={'观察':None}
    视口高={'值':None}
    def 画出(组):
        '顶沿并且起点已在视口上方时才粘住'
        粘住=组['atTop'] is True and 组['above'] is True
        已有=组['heading'].hasAttribute('data-stuck')
        if 已有!=粘住:
            组['heading'].toggleAttribute('data-stuck',粘住)
    def 起点回调(记录表):
        '起点相对视口顶的位置'
        if 已拆['值'] is True:
            return
        for 记录 in 记录表:
            组=按起点.get(记录.target)
            if 组 is None or 记录.rootBounds is None or 记录.time<组['aboveTime']:
                continue
            组['above']=记录.boundingClientRect.top<记录.rootBounds.top
            组['aboveTime']=记录.time
            画出(组)
    起点观察=窗口.IntersectionObserver(起点回调,{
        'root':视口,
        'threshold':[0,1],
    })
    for 组 in 节表:
        起点观察.observe(组['start'])
    def 尺寸回调(记录表):
        '视口高度变了就重挂一条顶沿观察'
        if 已拆['值'] is True:
            return
        for 记录 in 记录表:
            if 记录.target is not 视口 or 记录.contentRect.height==视口高['值']:
                continue
            视口高['值']=记录.contentRect.height
            if 条带['观察'] is not None:
                条带['观察'].disconnect()
            持有={'观察':None}
            def 条带回调(交叉表,本持有=持有):
                '一节穿过顶沿细条时更新粘住。被换掉的观察器不再写'
                本观察=本持有['观察']
                if 已拆['值'] is True or 条带['观察'] is not 本观察:
                    return
                for 交叉 in 交叉表:
                    组=按节.get(交叉.target)
                    if 组 is None or 交叉.rootBounds is None:
                        continue
                    顶=交叉.rootBounds.top
                    if 交叉.time>=组['topTime']:
                        组['atTop']=交叉.isIntersecting is True and 交叉.boundingClientRect.bottom>顶
                        组['topTime']=交叉.time
                    if 交叉.time>=组['aboveTime']:
                        组['above']=交叉.boundingClientRect.top<顶
                        组['aboveTime']=交叉.time
                    画出(组)
            边距='0px 0px '+str(min(1,视口高['值'])-视口高['值'])+'px 0px'
            本观察=窗口.IntersectionObserver(条带回调,{
                'root':视口,
                'rootMargin':边距,
                'threshold':0,
            })
            持有['观察']=本观察
            条带['观察']=本观察
            for 组 in 节表:
                本观察.observe(组['section'])
    尺寸观察=窗口.ResizeObserver(尺寸回调)
    尺寸观察.observe(视口)
    def 拆():
        '断开观察并清掉粘住标记'
        if 已拆['值'] is True:
            return
        已拆['值']=True
        起点观察.disconnect()
        if 条带['观察'] is not None:
            条带['观察'].disconnect()
        尺寸观察.disconnect()
        for 组 in 节表:
            if 组['heading'].hasAttribute('data-stuck'):
                组['heading'].removeAttribute('data-stuck')
    return 拆

class 弹出选择视图:
    '斜杠命令弹出：搜索、分组选项，以及风险确认'
    def __init__(自身,属性=None,**关键字参数):
        '记下叠层 props。有窗口和弹出就画'
        自身.属性=dict(属性 if 属性 is not None else {})
        自身.属性.update(关键字参数)
        自身.根=None
        自身.卡=None
        自身.搜索框=None
        自身.状态区=None
        自身.列表区=None
        自身.退订=None
        自身.已订=None
        自身.拆指针=None
        自身.拆尺寸=None
        自身.拆粘性=None
        自身.绘制中=False
        自身.待重画=False
        自身.标题序号=0
        自身.上次焦点=None
        if 'window' in 自身.属性 and 'popup' in 自身.属性:
            自身.渲染()

    def 渲染(自身):
        '未打开不留卡片。打开时画搜索和选项，风险门打开时只画确认'
        if 'window' not in 自身.属性:
            return None
        if 自身.绘制中:
            自身.待重画=True
            return 自身.根
        自身.绘制中=True
        try:
            弹出=自身.属性.get('popup')
            自身.订(弹出)
            if 弹出 is None:
                自身.收起()
            else:
                态=弹出.state.getSnapshot()
                if 态['open'] is not True:
                    自身.收起()
                elif 态['confirming'] is not None:
                    自身.画确认(弹出,态)
                else:
                    自身.画列表(弹出,态)
        finally:
            自身.绘制中=False
        if 自身.待重画:
            自身.待重画=False
            return 自身.渲染()
        return 自身.根

    def 订(自身,弹出):
        '状态一变就重画'
        if 弹出 is 自身.已订:
            return
        if callable(自身.退订):
            自身.退订()
            自身.退订=None
        自身.已订=弹出
        if 弹出 is None:
            return
        def 重画():
            '快照变了再画一版'
            自身.渲染()
        自身.退订=弹出.state.subscribe(重画)

    def 收起(自身):
        '关掉时卸掉卡片和监听'
        自身.拆监听()
        if 自身.根 is not None:
            自身.根.remove()
        自身.根=None
        自身.卡=None
        自身.搜索框=None
        自身.状态区=None
        自身.列表区=None
        自身.上次焦点=None

    def 拆监听(自身):
        '卸掉指针、尺寸和粘性观察'
        if callable(自身.拆指针):
            自身.拆指针()
            自身.拆指针=None
        if callable(自身.拆尺寸):
            自身.拆尺寸()
            自身.拆尺寸=None
        if callable(自身.拆粘性):
            自身.拆粘性()
            自身.拆粘性=None

    def 换根(自身,节点):
        '先记住父节点，再换成这次的根'
        父=None
        if 自身.根 is not None and 自身.根.parentNode is not None:
            父=自身.根.parentNode
        elif 'parent' in 自身.属性:
            父=自身.属性['parent']
        if 自身.根 is not None and 自身.根 is not 节点:
            自身.根.remove()
        自身.根=节点
        if 节点 is not None and 父 is not None and 节点.parentNode is None:
            父.appendChild(节点)

    def 画确认(自身,弹出,态):
        '风险门打开时不留选项卡片'
        窗口=自身.属性['window']
        文档=窗口.document
        登记样式(文档)
        自身.拆监听()
        自身.卡=None
        自身.搜索框=None
        自身.状态区=None
        自身.列表区=None
        确认=态['confirming']['confirmation']
        def 认(值):
            '记下风险勾选'
            弹出.acknowledge(值)
        def 取消():
            '回到选项列表'
            弹出.cancelConfirmation()
        def 确定():
            '勾选后结算'
            弹出.confirm()
        节点=风险确认({
            'open':True,
            'title':确认['title'],
            'description':确认['description'],
            'acknowledgeLabel':确认['acknowledgeLabel'],
            'cancelLabel':确认['cancelLabel'],
            'closeLabel':'关闭',
            'confirmLabel':确认['confirmLabel'],
            'acknowledged':态['acknowledged'] is True,
            'onAcknowledgedChange':认,
            'onCancel':取消,
            'onConfirm':确定,
            'window':窗口,
        }).渲染()
        自身.换根(节点)
        自身.上次焦点=None

    def 画列表(自身,弹出,态):
        '搜索框保持不动，状态区和列表随快照重填'
        窗口=自身.属性['window']
        文档=窗口.document
        登记样式(文档)
        命令=态['command'] if isinstance(态['command'],str) else ''
        行表=过滤选项(态['options'],态['search'],态['searchMode'])
        if 自身.卡 is None or 自身.搜索框 is None or 自身.状态区 is None:
            自身.拆监听()
            卡=文档.createElement('div')
            卡.className='card'
            卡.setAttribute('data-menu-material','translucent')
            def 按键(事件):
                '上下移动，回车和 Tab 选中，Esc 和 Shift+Tab 关闭'
                自身.按键(弹出,事件)
            卡.addEventListener('keydown',按键)
            框=文档.createElement('input')
            框.className='search'
            框.type='text'
            def 改(事件):
                '把搜索框里的字交给控制器'
                目标=事件.currentTarget if hasattr(事件,'currentTarget') else 框
                弹出.setSearch(目标.value)
            框.addEventListener('input',改)
            卡.appendChild(框)
            状态区=文档.createElement('div')
            卡.appendChild(状态区)
            自身.卡=卡
            自身.搜索框=框
            自身.状态区=状态区
            自身.列表区=None
            自身.换根(卡)
            def 点外(事件):
                '点在卡片外面就关掉，焦点留给被点中的目标'
                目标=事件.target if hasattr(事件,'target') else None
                if 自身.卡 is not None and 目标 is not None and 自身.卡.contains(目标):
                    return
                弹出.dismiss()
            文档.addEventListener('pointerdown',点外,True)
            def 拆指针():
                '卸掉捕获阶段的指针监听'
                文档.removeEventListener('pointerdown',点外,True)
            自身.拆指针=拆指针
            def 尺寸(事件):
                '窗口尺寸或滚动后重新夹高度'
                自身.夹高度()
            窗口.addEventListener('resize',尺寸)
            窗口.addEventListener('scroll',尺寸,True)
            def 拆尺寸():
                '卸掉尺寸和滚动监听'
                窗口.removeEventListener('resize',尺寸)
                窗口.removeEventListener('scroll',尺寸,True)
            自身.拆尺寸=拆尺寸
        卡=自身.卡
        框=自身.搜索框
        卡.setAttribute('aria-label','/'+命令+' 选项')
        文案=态['searchLabels'] if isinstance(态['searchLabels'],dict) else None
        if 文案 is not None and isinstance(文案.get('placeholder'),str):
            框.placeholder=文案['placeholder']
        else:
            框.placeholder='搜索…'
        框.setAttribute('aria-label','筛选选项')
        if 框.value!=态['search']:
            框.value=态['search']
        框.readOnly=态['submitting'] is True
        自身.填状态(弹出,态,行表,文案)
        if 态['status']=='ready':
            if 自身.列表区 is None:
                列表=文档.createElement('div')
                列表.className='viewport'
                列表.setAttribute('role','listbox')
                卡.appendChild(列表)
                自身.列表区=列表
            自身.列表区.setAttribute('aria-label','/'+命令+' 匹配项')
            自身.填列表(弹出,态,行表)
        elif 自身.列表区 is not None:
            if callable(自身.拆粘性):
                自身.拆粘性()
                自身.拆粘性=None
            自身.列表区.remove()
            自身.列表区=None
        自身.夹高度()
        焦点键=(True,None)
        if 自身.上次焦点!=焦点键:
            框.focus()
            自身.上次焦点=焦点键
        if 态['status']=='ready':
            选中=卡.querySelector('[aria-selected="true"]')
            if 选中 is not None:
                选中.scrollIntoView({'block':'nearest'})

    def 夹高度(自身):
        '按卡片底边到视口顶的空间夹住设计高度'
        if 自身.卡 is None:
            return
        底=自身.卡.getBoundingClientRect().bottom
        自身.卡.style.maxHeight=str(锚定最大高度(底,设计高度))+'px'

    def 填状态(自身,弹出,态,行表,文案):
        '错误、加载中、应用中和空列表'
        文档=自身.属性['window'].document
        区=自身.状态区
        while 区.firstElementChild is not None:
            区.firstElementChild.remove()
        if isinstance(态['error'],str) and 态['error']!='':
            行=文档.createElement('div')
            行.className='error'
            行.setAttribute('role','alert')
            字=文档.createElement('span')
            字.className='errorText'
            字.textContent=态['error']
            行.appendChild(字)
            if 态['status']=='failed':
                钮=文档.createElement('button')
                钮.type='button'
                钮.className='retry'
                钮.textContent='重试'
                def 点重试(事件):
                    '再拉一次失败的选项'
                    弹出.retry()
                钮.addEventListener('click',点重试)
                行.appendChild(钮)
            区.appendChild(行)
        if 态['status']=='pending':
            字=文档.createElement('div')
            字.className='status'
            字.textContent='正在加载选项…'
            区.appendChild(字)
        if 态['submitting'] is True:
            字=文档.createElement('div')
            字.className='status'
            字.textContent='正在应用…'
            区.appendChild(字)
        if 态['status']=='ready' and len(行表)==0:
            if 文案 is None:
                空文='无选项'
            elif len(态['options'])==0:
                空文=文案['empty']
            else:
                空文=文案['noResults']
            字=文档.createElement('div')
            字.className='status'
            字.textContent=空文
            区.appendChild(字)

    def 填列表(自身,弹出,态,行表):
        '按过滤顺序画分组和行'
        文档=自身.属性['window'].document
        窗口=自身.属性['window']
        区=自身.列表区
        if callable(自身.拆粘性):
            自身.拆粘性()
            自身.拆粘性=None
        while 区.firstElementChild is not None:
            区.firstElementChild.remove()
        组表=分组选项(行表)
        高亮=态['active']
        序号=0
        for 组 in 组表:
            组对象=组['group']
            if 组对象 is None:
                for 选项 in 组['rows']:
                    区.appendChild(自身.画行(文档,窗口,弹出,选项,序号,序号==高亮))
                    序号+=1
                continue
            自身.标题序号+=1
            标题标识='命令组标题'+str(自身.标题序号)
            节=文档.createElement('section')
            节.setAttribute('role','group')
            节.setAttribute('aria-labelledby',标题标识)
            节.setAttribute('data-menu-group','')
            节.className='group'
            起点=文档.createElement('span')
            起点.setAttribute('aria-hidden','true')
            起点.setAttribute('data-menu-group-start','')
            起点.className='start'
            节.appendChild(起点)
            标题=文档.createElement('div')
            标题.id=标题标识
            标题.setAttribute('data-menu-group-heading','')
            标题.className='heading'
            标题.textContent=组对象['label']
            节.appendChild(标题)
            for 选项 in 组['rows']:
                节.appendChild(自身.画行(文档,窗口,弹出,选项,序号,序号==高亮))
                序号+=1
            区.appendChild(节)
        自身.拆粘性=观察粘性菜单组(窗口,区)

    def 画行(自身,文档,窗口,弹出,选项,序号,当前):
        '一行：标签、徽标、说明、当前标记'
        行=文档.createElement('div')
        行.setAttribute('role','option')
        行.setAttribute('aria-selected','true' if 当前 else 'false')
        if 'badge' in 选项 and 选项['badge'] is not None:
            行.setAttribute('aria-label',选项['label']+' '+选项['badge'])
        行.className='row rowActive' if 当前 else 'row'
        def 点(事件,下标=序号):
            '选中这一行'
            弹出.select(下标)
        def 停(事件,下标=序号):
            '悬停移动高亮'
            弹出.highlight(下标)
        行.addEventListener('click',点)
        行.addEventListener('mouseenter',停)
        标签=文档.createElement('span')
        标签.className='label'
        字=文档.createElement('span')
        字.className='labelText'
        字.textContent=选项['label']
        标签.appendChild(字)
        if 'badge' in 选项 and 选项['badge'] is not None:
            徽=文档.createElement('sup')
            徽.className='badge'
            徽.textContent=选项['badge']
            标签.appendChild(徽)
        行.appendChild(标签)
        if 'detail' in 选项 and 选项['detail'] is not None:
            详=文档.createElement('span')
            详.className='detail'
            详.textContent=选项['detail']
            行.appendChild(详)
        if 选项.get('active') is True:
            勾=文档.createElement('span')
            勾.className='check'
            图标勾16({'window':窗口,'parent':勾})
            行.appendChild(勾)
        return 行

    def 按键(自身,弹出,事件):
        '左右方向键留给搜索框自己移动光标'
        键,移位=键名(事件)
        态=弹出.state.getSnapshot()
        if 态['open'] is not True:
            return
        行表=过滤选项(态['options'],态['search'],态['searchMode'])
        if 键=='ArrowDown':
            事件.preventDefault()
            弹出.move(1)
            return
        if 键=='ArrowUp':
            事件.preventDefault()
            弹出.move(-1)
            return
        if 键=='Enter':
            事件.preventDefault()
            弹出.select(态['active'])
            return
        if 键=='Tab':
            if 移位 is not True and (态['status']!='ready' or len(行表)==0):
                return
            事件.preventDefault()
            if 移位:
                弹出.dismiss({'focusComposer':True})
            else:
                弹出.select(态['active'])
            return
        if 键=='Escape':
            事件.preventDefault()
            弹出.dismiss({'focusComposer':True})

    def __call__(自身,属性=None,**关键字参数):
        '有新属性先更新，再画出'
        if 属性 is not None or len(关键字参数)>0:
            合并=dict(属性 if 属性 is not None else {})
            合并.update(关键字参数)
            自身.属性=合并
            自身.已订=None
            自身.上次焦点=None
        return 自身.渲染()
