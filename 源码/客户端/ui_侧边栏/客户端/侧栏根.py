import os
from ...ui_基础界面组件.鱼标 import 处理鱼标
from ...ui_对话.异常 import 注入模块样式文件,模块节点,挂上

__all__=['画描边图标','绑定提示','找快捷行','快捷面','面板行','侧栏根']

#宽内容淡出 150 毫秒后卸下。滚动条在指针离开列两秒后才藏。
折叠落定毫秒=150
滚动条滞留毫秒=2000
样式模块='sidebar'

新聊路径=(
    'M2.37091 11.2501C1.58745 9.89288 1.32067 8.29835 1.61969 6.76006C1.91872 5.22177 2.76342 3.8433 3.99826 2.87846C5.2331 1.91362 6.77494 1.42737 8.33988 1.50925C9.90482 1.59113 11.3875 2.23562 12.5149 3.32406C13.6425 4.41269 14.3387 5.87206 14.4754 7.4334C14.612 8.99474 14.18 10.5529 13.2587 11.8209C12.3375 13.0888 10.9891 13.9813 9.46194 14.3337C8.18691 14.628 6.85895 14.5294 5.64989 14.0605C5.1712 13.8748 4.76962 13.4932 4.26534 13.3967C3.67413 13.2835 2.95257 13.5598 2.03794 14.3337',
    'M8 5V11',
    'M5 8H11',
)
左栏路径=(
    'M13.5 1.5H2.5C1.94772 1.5 1.5 1.94772 1.5 2.5V13.5C1.5 14.0523 1.94772 14.5 2.5 14.5H13.5C14.0523 14.5 14.5 14.0523 14.5 13.5V2.5C14.5 1.94772 14.0523 1.5 13.5 1.5Z',
    'M5.5 1.5V14.5',
)

def 画描边图标(文档,路径组,尺寸,线宽,类名,模块):
    '画出 currentColor 描边图标。类名留在 svg 上'
    图=文档.createElementNS('http://www.w3.org/2000/svg','svg')
    图.setAttribute('xmlns','http://www.w3.org/2000/svg')
    图.setAttribute('width',str(尺寸))
    图.setAttribute('height',str(尺寸))
    图.setAttribute('viewBox','0 0 16 16')
    图.setAttribute('fill','none')
    图.setAttribute('stroke-width',str(线宽))
    图.setAttribute('aria-hidden','true')
    if isinstance(类名,str) and 类名!='':
        图.setAttribute('class',类名)
    if isinstance(模块,str) and 模块!='':
        图.setAttribute('data-dsh-css',模块)
    for 路径 in 路径组:
        笔=文档.createElementNS('http://www.w3.org/2000/svg','path')
        笔.setAttribute('d',路径)
        笔.setAttribute('stroke','currentColor')
        图.appendChild(笔)
    return 图

def 绑定提示(按钮,窗口,标签,快捷键,侧,延迟):
    '悬停满延迟后在按钮旁显示提示。焦点马上显示。离开或点击就收起'
    计时=None
    泡=None
    文档=窗口.document

    def 收起():
        '清掉尚未出现的定时，并拆掉气泡'
        nonlocal 计时,泡
        if 计时 is not None:
            窗口.clearTimeout(计时)
            计时=None
        if 泡 is not None:
            泡.remove()
            泡=None

    def 显示():
        '按按钮现在的位置把气泡放到右侧或下侧'
        nonlocal 计时,泡
        计时=None
        if 泡 is not None:
            return
        节点=文档.createElement('span')
        节点.setAttribute('role','tooltip')
        文=标签
        if 快捷键 is not None and len(快捷键)>0:
            文=文+' '+' '.join(快捷键)
        节点.textContent=文
        节点.style.position='fixed'
        节点.style.zIndex='80'
        节点.style.pointerEvents='none'
        节点.style.background='var(--dsw-alias-tooltip-bg)'
        节点.style.color='var(--dsw-static-neutral-bluish-00)'
        节点.style.padding='3px 7px'
        节点.style.borderRadius='var(--dsw-radius-sm)'
        节点.style.fontSize='13px'
        节点.style.lineHeight='20px'
        节点.style.whiteSpace='pre'
        矩形=按钮.getBoundingClientRect()
        if 侧=='bottom':
            节点.style.left=str(矩形.left)+'px'
            节点.style.top=str(矩形.bottom+8)+'px'
        else:
            节点.style.left=str(矩形.right+8)+'px'
            节点.style.top=str(矩形.top)+'px'
        文档.body.appendChild(节点)
        泡=节点

    def 进入鼠标(事件):
        '悬停计时'
        nonlocal 计时
        if 计时 is not None or 泡 is not None:
            return
        计时=窗口.setTimeout(显示,延迟)

    def 进入焦点(事件):
        '键盘焦点马上显示'
        显示()

    def 点击后(事件):
        '点下去就收起'
        收起()

    def 离开(事件):
        '指针或焦点离开就收起'
        收起()

    按钮.addEventListener('mouseenter',进入鼠标)
    按钮.addEventListener('mouseleave',离开)
    按钮.addEventListener('focus',进入焦点)
    按钮.addEventListener('blur',离开)
    按钮.addEventListener('click',点击后)
    return 收起

def 找快捷行(行表,标识):
    '目录里这个命令的行。没有则 None'
    for 行 in 行表:
        if 行['id']==标识:
            return 行
    return None

def 快捷面(行):
    '无障碍串和键帽。没有这一行则都空'
    if 行 is None:
        return None,()
    return 行['aria'],tuple(行['keys'])

class 面板行:
    '全局面板的一行。按钮归这一行，图标槽画在字形位里'
    def __init__(自身,属性):
        '记下身份、宽态和父级给的动作'
        自身.属性=属性
        自身.根=None

    def 渲染(自身):
        '画出这一行。宽态带标题，轨态只留图标'
        属性=自身.属性
        文档=属性['文档']
        身份=属性['id']
        标签=属性['label']
        宽=属性['宽']
        选中=属性['选中']
        类名='panelRow panelActive' if 选中 is True else 'panelRow'
        按钮=模块节点(文档,'button',样式模块,类名)
        按钮.type='button'
        按钮.setAttribute('aria-label',标签)
        if 选中 is True:
            按钮.setAttribute('aria-current','page')
        def 点选(事件):
            '切到这个主面板'
            属性['selectPanel'](身份)
        按钮.addEventListener('click',点选)
        字形=模块节点(文档,'span',样式模块,'panelGlyph')
        字形.setAttribute('aria-hidden','true')
        尺寸=16 if 宽 is True else 18
        图标=属性['renderSlot']('sidebar.panellist',{
            'size':尺寸,
            'active':选中,
            'window':属性['窗口'],
        },{'only':身份})
        挂上(字形,图标)
        按钮.appendChild(字形)
        if 宽 is True:
            题=模块节点(文档,'span',样式模块,'panelTitle wide')
            题.textContent=标签
            按钮.appendChild(题)
        else:
            收=绑定提示(按钮,属性['窗口'],标签,None,'right',500)
            属性['提示拆除'].append(收)
        自身.根=按钮
        return 按钮

class 侧栏根:
    '侧栏列。宽态淡出后落到轨，滚动条只在指针还在列里时画'
    共享=None
    当前=None

    def __init__(自身,属性):
        '记下 props。同一列的计时和节点留在类上'
        侧栏根.当前=自身
        自身.属性=属性
        if 侧栏根.共享 is None:
            侧栏根.共享={
                '根':None,
                '已落定':None,
                '折叠标记':None,
                '落定计时':None,
                '指针在内':False,
                '滞留计时':None,
                '在听指针':False,
                '曾宽':None,
                '上次宽':None,
                '已订':False,
                '内容戳':None,
                '子':[],
                '提示拆除':[],
                '窗口':None,
                '宽度':None,
                '收起':None,
                '宽':None,
            }
        自身.状态=侧栏根.共享
        自身.根=自身.状态['根']
        自身.渲染()

    def __call__(自身,属性=None):
        '父级再次渲染时刷新这一列'
        if 属性 is not None:
            侧栏根.当前=自身
            自身.属性=属性
        return 自身.渲染()

    def 刷新外观(自身):
        '只改列的类名和宽度，不重建里面的按钮'
        状态=自身.状态
        根=状态['根']
        宽=状态['宽']
        收起=状态['收起']
        段=['root']
        if 收起 is True or 宽 is not True:
            段.append('collapsed')
            if 状态['曾宽'] is True:
                段.append('railIn')
        if 收起 is True and 宽 is True:
            段.append('fading')
        if 状态['指针在内'] is not True:
            段.append('quietBars')
        类名=' '.join(段)
        if 根.className!=类名:
            根.className=类名
        if 宽 is True:
            像素=状态['上次宽'] if 收起 is True else 状态['宽度']
            宽度文=str(像素)+'px'
            if 根.style.width!=宽度文:
                根.style.width=宽度文
        elif 根.style.width not in ('',None):
            根.style.removeProperty('width')

    def 取消滞留(自身):
        '清掉尚未到点的隐藏'
        状态=自身.状态
        句柄=状态['滞留计时']
        if 句柄 is None:
            return
        状态['窗口'].clearTimeout(句柄)
        状态['滞留计时']=None

    def 武装滞留(自身):
        '指针离开列的盒子后，两秒再把滚动条藏起来。已经排了就不再排'
        状态=自身.状态
        if 状态['滞留计时'] is not None:
            return
        def 到期():
            '到点视为指针不在列里'
            状态['滞留计时']=None
            状态['指针在内']=False
            if 状态['在听指针'] is True:
                状态['窗口'].document.removeEventListener('pointermove',自身.指针移动)
                状态['在听指针']=False
            自身.刷新外观()
        状态['滞留计时']=状态['窗口'].setTimeout(到期,滚动条滞留毫秒)

    def 进入指针(自身,事件):
        '回到列里，取消隐藏并保持滚动条'
        状态=自身.状态
        自身.取消滞留()
        if 状态['指针在内'] is True:
            return
        状态['指针在内']=True
        if 状态['在听指针'] is not True:
            状态['窗口'].document.addEventListener('pointermove',自身.指针移动)
            状态['在听指针']=True
        自身.刷新外观()

    def 离开指针(自身,事件):
        '离开列的盒子后开始计时，不立刻藏'
        自身.武装滞留()

    def 指针移动(自身,事件):
        '用列的盒子判断指针还在不在'
        列=自身.状态['根']
        if 列 is None:
            return
        矩形=列.getBoundingClientRect()
        if 矩形 is None:
            return
        横向内=事件.clientX>=矩形.left and 事件.clientX<矩形.right
        纵向内=事件.clientY>=矩形.top and 事件.clientY<矩形.bottom
        if 横向内 and 纵向内:
            自身.取消滞留()
        else:
            自身.武装滞留()

    def 渲染(自身):
        '画出或刷新这一列。根节点保持同一个'
        属性=自身.属性
        状态=自身.状态
        if 状态.get('绘制中') is True:
            状态['待重画']=True
            return 状态.get('根')
        状态['绘制中']=True
        try:
            return 自身.画出()
        finally:
            状态['绘制中']=False
            if 状态.get('待重画') is True:
                状态['待重画']=False
                自身.渲染()

    def 画出(自身):
        '按当前份额画列。同一轮里的重复通知合成一次'
        属性=自身.属性
        状态=自身.状态
        窗口=属性['window']
        文档=窗口.document
        收起=属性['collapsed'] is True
        宽度=属性['width']
        状态['窗口']=窗口
        状态['宽度']=宽度
        状态['收起']=收起
        if 状态['已落定'] is None:
            状态['已落定']=收起
            状态['折叠标记']=收起
            状态['曾宽']=收起 is not True
            状态['上次宽']=宽度
        elif 状态['折叠标记'] is not 收起:
            if 状态['落定计时'] is not None:
                窗口.clearTimeout(状态['落定计时'])
                状态['落定计时']=None
            状态['折叠标记']=收起
            if 收起 is not True:
                状态['已落定']=False
            else:
                def 落定():
                    '宽内容卸下，轨布局开始'
                    状态['落定计时']=None
                    状态['已落定']=True
                    侧栏根.当前.渲染()
                状态['落定计时']=窗口.setTimeout(落定,折叠落定毫秒)
        if 收起 is not True:
            状态['曾宽']=True
            状态['上次宽']=宽度
        窗标题=文档.documentElement.hasAttribute('data-windows-titlebar')
        达尔文=文档.documentElement.getAttribute('data-platform')=='darwin'
        if 窗标题 is True:
            宽=收起 is not True
        else:
            宽=收起 is not True or 状态['已落定'] is not True
        状态['宽']=宽
        版本号=os.environ.get('DSH_CLIENT_VERSION')
        构建版本=None
        if 版本号 is not None:
            构建版本=版本号
            提交号=os.environ.get('DSH_CLIENT_COMMIT_HASH')
            if 提交号 is not None:
                构建版本=构建版本+'-'+提交号
            if os.environ.get('DSH_CLIENT_GIT_DIRTY')=='true':
                构建版本=构建版本+'-dirty'
        def 找切换(行表):
            '折叠侧栏的命令行'
            return 找快捷行(行表,'sidebar.left.toggle')
        def 找新建(行表):
            '新建会话的命令行'
            return 找快捷行(行表,'session.new')
        def 全量(快照):
            '面板元数据原样'
            return 快照
        切换无障碍,切换键=快捷面(属性['useShortcuts'](找切换))
        新建无障碍,新建键=快捷面(属性['useShortcuts'](找新建))
        面板表=属性['usePanels'](全量)
        活动={}
        for 行数据 in 面板表:
            身份=行数据['id']
            def 是这家(信息,钉=身份):
                '这一行是不是当前主面板'
                return 信息['activePanelId']==钉
            活动[身份]=属性['usePanelInfo'](是这家) is True
        戳=(
            宽,
            达尔文,
            窗标题,
            构建版本,
            tuple((项['id'],项['label']) for 项 in 面板表),
            tuple((项['id'],活动[项['id']]) for 项 in 面板表),
            切换无障碍,
            tuple(切换键),
            新建无障碍,
            tuple(新建键),
        )
        注入模块样式文件(文档,'侧栏根样式',os.path.join(os.path.dirname(__file__),'侧栏根.module.css'),样式模块)
        根=状态['根']
        if 根 is not None:#可能是上一页留下的
            try:#断掉的节点读 isConnected 会失败
                还在=根.isConnected is True
            except Exception as 断开:#对象已经不在这一页
                还在=False
                del 断开
            if 还在 is not True:
                状态['根']=None#丢掉
                状态['内容戳']=None#内容要重画
                状态['子']=[]#旧子节点不再拆
                根=None#下面新建
        if 根 is None:
            根=模块节点(文档,'div',样式模块,'root')
            根.addEventListener('pointerenter',自身.进入指针)
            根.addEventListener('pointerleave',自身.离开指针)
            状态['根']=根
        自身.根=根
        自身.刷新外观()
        宽未变=状态['内容戳'] is not None and 状态['内容戳'][0]==宽 and 状态.get('工作区') is not None
        if 状态['内容戳']!=戳 and 宽未变:
            状态['内容戳']=戳
        if 状态['内容戳']!=戳:
            for 收提示 in list(状态['提示拆除']):
                收提示()
            状态['提示拆除'].clear()
            状态['子']=[]
            片段=文档.createDocumentFragment()
            def 装上(节点):
                '先放进片段。整列画完再一次换上，避免先拆空'
                片段.appendChild(节点)
                状态['子'].append(节点)
            提示侧='bottom' if 窗标题 is True else 'right'
            切换文='打开侧边栏' if 收起 is True else '收起侧边栏'
            def 点切换(事件):
                '展开或收起侧栏'
                属性['toggleSidebar']()
            def 点新建(事件):
                '开始新会话'
                属性['startSession']()
            def 展开侧栏():
                '收起时，轨上的浏览区请求展开'
                if 属性['collapsed'] is True:
                    属性['toggleSidebar']()
            切换钮=模块节点(文档,'button',样式模块,'iconButton toggle')
            切换钮.type='button'
            切换钮.setAttribute('aria-label',切换文)
            if 切换无障碍 is not None:
                切换钮.setAttribute('aria-keyshortcuts',切换无障碍)
            切换钮.addEventListener('click',点切换)
            轨标=模块节点(文档,'span',样式模块,'railMark')
            轨标.setAttribute('aria-hidden','true')
            轨鱼=处理鱼标(窗口,{'size':24})
            挂上(轨标,属性['renderSlot']('sidebar.brand.mark',{'size':24,'window':窗口},{'fallback':轨鱼}))
            切换钮.appendChild(轨标)
            图标边=16 if 宽 is True or 窗标题 is True else 18
            切换钮.appendChild(画描边图标(文档,左栏路径,图标边,1,'panelIcon',样式模块))
            if 宽 is not True:
                挂上(切换钮,属性['renderSlot']('sidebar.toggle.badge',{'window':窗口}))
            状态['切换钮']=切换钮
            状态['切换文']=切换文
            状态['切换提示']=绑定提示(切换钮,窗口,切换文,切换键,提示侧,500)
            状态['提示拆除'].append(状态['切换提示'])
            if 达尔文 is True:
                条=模块节点(文档,'div',样式模块,'topStrip')
                条.setAttribute('data-window-drag','true')
                条.appendChild(切换钮)
                装上(条)
            行=模块节点(文档,'div',样式模块,'logoRow')
            行.setAttribute('data-window-drag','true')
            if 宽 is True:
                身份=模块节点(文档,'span',样式模块,'brandIdentity')
                身份.setAttribute('aria-hidden','true')
                标位=模块节点(文档,'span',样式模块,'brandMark')
                品牌鱼=处理鱼标(窗口,{'size':24})
                挂上(标位,属性['renderSlot']('sidebar.brand.mark',{'size':24,'window':窗口},{'fallback':品牌鱼}))
                身份.appendChild(标位)
                名位=模块节点(文档,'span',样式模块,'brandName')
                if 构建版本 is None:
                    回退名=模块节点(文档,'span',样式模块,'fallbackBrandName')
                    回退名.textContent='DSH 本地构建'
                else:
                    回退名=模块节点(文档,'span',样式模块,'localBuildBrand')
                    题=模块节点(文档,'span',样式模块,'localBuildTitle')
                    题.textContent='DSH 本地构建'
                    版=模块节点(文档,'span',样式模块,'buildVersion')
                    版.textContent=构建版本
                    回退名.appendChild(题)
                    回退名.appendChild(版)
                挂上(名位,属性['renderSlot']('sidebar.brand.name',{'window':窗口},{'fallback':回退名}))
                身份.appendChild(名位)
                if 达尔文 is True:
                    品牌=模块节点(文档,'span',样式模块,'brand wide')
                    品牌.appendChild(身份)
                else:
                    品牌=模块节点(文档,'button',样式模块,'brand wide')
                    品牌.type='button'
                    品牌.setAttribute('aria-label','新建会话')
                    if 新建无障碍 is not None:
                        品牌.setAttribute('aria-keyshortcuts',新建无障碍)
                    品牌.addEventListener('click',点新建)
                    品牌.appendChild(身份)
                行.appendChild(品牌)
            if 达尔文 is not True:
                行.appendChild(切换钮)
            装上(行)
            新建=模块节点(文档,'button',样式模块,'newSession')
            新建.type='button'
            新建.setAttribute('aria-label','新建会话')
            if 新建无障碍 is not None:
                新建.setAttribute('aria-keyshortcuts',新建无障碍)
            新建.addEventListener('click',点新建)
            罩=模块节点(文档,'span',样式模块,'newSessionLabelMask')
            内=模块节点(文档,'span',样式模块,'newSessionContent')
            if 宽 is True:
                内.appendChild(画描边图标(文档,新聊路径,14,1.3,None,None))
                字=模块节点(文档,'span',样式模块,'newSessionLabel wide')
                字.textContent='新会话'
                内.appendChild(字)
            else:
                新边=16 if 窗标题 is True else 18
                内.appendChild(画描边图标(文档,新聊路径,新边,1,None,None))
            罩.appendChild(内)
            新建.appendChild(罩)
            if 宽 is True and len(新建键)>0:
                快捷=模块节点(文档,'span',样式模块,'newSessionShortcut')
                快捷.setAttribute('aria-hidden','true')
                键盒=文档.createElement('span')
                键盒.setAttribute('class','keys')
                for 键 in 新建键:
                    帽=文档.createElement('kbd')
                    帽.setAttribute('class','separator' if 键=='+' else 'key')
                    帽.textContent=键
                    键盒.appendChild(帽)
                快捷.appendChild(键盒)
                新建.appendChild(快捷)
            if 宽 is not True:
                状态['提示拆除'].append(绑定提示(新建,窗口,'新建会话',新建键,提示侧,500))
            装上(新建)
            if len(面板表)>0:
                导航=模块节点(文档,'nav',样式模块,'panelList')
                导航.setAttribute('aria-label','全局面板')
                for 行数据 in 面板表:
                    钮=面板行({
                        '文档':文档,
                        '窗口':窗口,
                        'id':行数据['id'],
                        'label':行数据['label'],
                        '宽':宽,
                        '选中':活动[行数据['id']],
                        'selectPanel':属性['selectPanel'],
                        'renderSlot':属性['renderSlot'],
                        '提示拆除':状态['提示拆除'],
                    }).渲染()
                    导航.appendChild(钮)
                装上(导航)
            区=模块节点(文档,'div',样式模块,'regionArea')
            挂上(区,属性['renderSlot']('sidebar.workspaces',{
                'wide':宽,
                'expandSidebar':展开侧栏,
                'window':窗口,
            }))
            状态['工作区']=区
            装上(区)
            脚=模块节点(文档,'div',样式模块,'footArea')
            动作=模块节点(文档,'div',样式模块,'footerActions')
            挂上(动作,属性['renderSlot']('sidebar.footer.action',{'wide':宽,'window':窗口}))
            设置=模块节点(文档,'div',样式模块,'settingsArea')
            挂上(设置,属性['renderSlot']('sidebar.settings',{'wide':宽,'window':窗口}))
            脚.appendChild(动作)
            脚.appendChild(设置)
            装上(脚)
            根.replaceChildren(片段)
            状态['内容戳']=戳
        elif '切换钮' in 状态 and 状态['切换钮'] is not None:
            切换文='打开侧边栏' if 收起 is True else '收起侧边栏'
            if 状态['切换文']!=切换文:
                状态['切换钮'].setAttribute('aria-label',切换文)
                if 状态['切换提示'] is not None:
                    状态['切换提示']()
                提示侧='bottom' if 窗标题 is True else 'right'
                状态['切换提示']=绑定提示(状态['切换钮'],窗口,切换文,切换键,提示侧,500)
                状态['提示拆除'].append(状态['切换提示'])
                状态['切换文']=切换文
        if 状态['已订'] is not True:
            def 重画():
                '面板、快捷键或当前面板变了就重画'
                侧栏根.当前.渲染()
            属性['usePanels']._subscribe(重画)
            属性['useShortcuts']._subscribe(重画)
            属性['usePanelInfo']._subscribe(重画)
            状态['已订']=True
        父=属性['parent'] if 'parent' in 属性 else None
        if 父 is not None and 根.parentNode is not 父:
            父.appendChild(根)
        return 根
