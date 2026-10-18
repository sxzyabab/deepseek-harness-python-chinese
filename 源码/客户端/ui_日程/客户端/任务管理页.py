'跨会话的自动化任务页。这里不建任务，新建会去开一条会话'
from ...模块.客户端.通告 import 取握手窗口
import os
from ...ui_对话.异常 import 注入模块样式文件,标样式模块
from ...ui_基础界面组件.按钮 import 处理按钮
from ...ui_基础界面组件.输入 import 处理输入
from .管理文案 import 管理中文
from .目录反馈 import 目录反馈
from .任务详情 import 任务详情,任务详情控制器
from .相对时钟 import 现在毫秒,安装相对时钟
from .日程格式 import 任务名,格式化日程频率,下次运行两段,时区标签
from .任务管理图标 import 画时钟

__all__=['任务管理页']

样式模块='task-manager-page'

def 确保样式(文档):
    '任务页样式只插一次'
    注入模块样式文件(文档,'日程任务管理页样式',os.path.join(os.path.dirname(__file__),'任务管理页.module.css'),样式模块)

def 标(节点):
    '挂上样式模块'
    if 节点 is not None:
        标样式模块(节点,样式模块)
    return 节点

class 任务管理页:
    '搜索、状态筛选，旁边是选中任务的详情'
    def __new__(类,属性=None):
        '整页只有一份'
        if not hasattr(类,'实例') or 类.实例 is None:
            自身=object.__new__(类)
            自身.属性=属性
            自身.根=None
            自身.搜索=''
            自身.筛选='all'
            自身.选中=None
            自身.控制=任务详情控制器()
            自身.详情=None
            自身.现在=现在毫秒()
            自身.停时钟=None
            自身.已订=False
            类.实例=自身
        else:
            自身=类.实例
            自身.属性=属性
        return 自身.渲染()

    def 渲染(自身):
        '按目录、搜索和筛选重画列表'
        属性=自身.属性
        窗口=属性.get('window') or 取握手窗口()
        属性['window']=窗口
        文档=窗口.document
        确保样式(文档)
        if 自身.停时钟 is None:
            def 重画():
                '列表上的距离跟着走'
                自身.现在=现在毫秒()
                自身.渲染()
            自身.停时钟=安装相对时钟(重画)
        if not 自身.已订 and callable(属性.get('useCatalog')) and hasattr(属性['useCatalog'],'_subscribe'):
            def 变更():
                '目录变了就重画'
                自身.渲染()
            属性['useCatalog']._subscribe(变更)
            自身.已订=True
        def 取(快照):
            '整份目录'
            return 快照
        目录=属性['useCatalog'](取)
        记录=目录.get('records') or []
        查询=自身.搜索.strip().lower()
        行=[]
        for 项 in 记录:
            if 自身.筛选!='all' and 项.get('status')!=自身.筛选:
                continue
            名=任务名(项).lower()
            指令=(项.get('prompt') or '').lower()
            会话=str(项.get('sessionId') or '').lower()
            if 查询 and 查询 not in 名 and 查询 not in 指令 and 查询 not in 会话:
                continue
            行.append(项)
        def 时间键(项):
            '按计划时间排序'
            return 取握手窗口().Date.parse(项.get('scheduledAt') or '')
        行.sort(key=时间键)
        if 自身.根 is None:
            自身.根=文档.createElement('section')
            自身.根.className='page'
            标(自身.根)
            自身.根.setAttribute('aria-label',管理中文['title'])
            自身.根.setAttribute('data-testid','task-manager-page')
        根=自身.根
        while 根.firstChild is not None:
            根.removeChild(根.firstChild)
        快照=自身.控制.快照(属性,目录,自身.选中)
        选中任务=快照['task']
        if 选中任务 is not None:
            根.className='page hasDetails'
        else:
            根.className='page'
        标(根)
        列=文档.createElement('div')
        列.className='listPane'
        标(列)
        滚=文档.createElement('div')
        滚.className='pageScroll'
        标(滚)
        内容=文档.createElement('div')
        内容.className='pageContent'
        标(内容)
        头=文档.createElement('div')
        头.className='pageHeading'
        标(头)
        题=文档.createElement('h1')
        题.tabIndex=-1
        题.textContent=管理中文['title']
        头.appendChild(题)
        新建=处理按钮(窗口,{
            'variant':'primary','size':'sm','className':'newButton',
            'children':管理中文['new.action'],'onClick':属性.get('onNewTask'),'window':窗口,
        })
        标(新建)
        头.appendChild(新建)
        内容.appendChild(头)
        筛=文档.createElement('div')
        筛.className='filterTabs'
        标(筛)
        筛.setAttribute('role','group')
        筛.setAttribute('aria-label',管理中文['statusFilter.label'])
        for 值,文 in (('all','statusFilter.all'),('active','status.active'),('inactive','status.inactive')):
            钮=文档.createElement('button')
            钮.type='button'
            钮.className='filterTab filterTabActive' if 自身.筛选==值 else 'filterTab'
            标(钮)
            钮.setAttribute('aria-pressed','true' if 自身.筛选==值 else 'false')
            钮.textContent=管理中文[文]
            def 点筛(事件,值=值):
                '换状态筛选'
                自身.筛选=值
                自身.渲染()
            钮.addEventListener('click',点筛)
            筛.appendChild(钮)
        内容.appendChild(筛)
        搜盒=文档.createElement('div')
        搜盒.className='searchField'
        标(搜盒)
        输入=处理输入(窗口,{
            'type':'search','window':窗口,
            'aria-label':管理中文['search.label'],
            'placeholder':管理中文['search.placeholder'],
            'value':自身.搜索,
        })
        def 改搜(事件):
            '按名字、指令或会话过滤'
            自身.搜索=事件.target.value
            自身.渲染()
        if 输入 is not None:
            框=输入.querySelector('input')
            if 框 is not None:
                框.setAttribute('aria-label',管理中文['search.label'])
                框.addEventListener('input',改搜)
            搜盒.appendChild(输入)
        if 自身.搜索!='':
            def 清空():
                '清掉搜索'
                自身.搜索=''
                自身.渲染()
            清=处理按钮(窗口,{'size':'sm','className':'searchClear','children':管理中文['search.clear'],'onClick':清空,'window':窗口})
            标(清)
            清.setAttribute('aria-label',管理中文['search.clear'])
            搜盒.appendChild(清)
        内容.appendChild(搜盒)
        表=文档.createElement('div')
        表.className='list'
        标(表)
        if 选中任务 is None:
            反馈=目录反馈({'window':窗口,'status':目录.get('status'),'populated':len(行)>0,'onRetry':属性.get('onRetry')})
            if 反馈 is not None:
                表.appendChild(反馈)
        if 目录.get('status')=='ready' and len(行)==0:
            空=文档.createElement('div')
            空.className='empty'
            标(空)
            空.setAttribute('role','status')
            空.appendChild(画时钟(文档,24))
            空题=文档.createElement('h2')
            if 自身.筛选=='inactive' and 自身.搜索.strip()=='':
                空题.textContent=管理中文['list.emptyInactive']
            elif len(记录)==0:
                空题.textContent=管理中文['list.empty']
            else:
                空题.textContent=管理中文['list.noMatches']
            空.appendChild(空题)
            空钮=处理按钮(窗口,{'variant':'outline','className':'emptyAction','children':管理中文['empty.action'],'onClick':属性.get('onNewTask'),'window':窗口})
            标(空钮)
            空.appendChild(空钮)
            表.appendChild(空)
        列表=文档.createElement('ul')
        列表.className='listRows'
        标(列表)
        列表.setAttribute('aria-label',管理中文['list.label'])
        系统=窗口.Intl.DateTimeFormat().resolvedOptions().timeZone
        def 标时区(区,系统=系统):
            '列表频率里的时区'
            return 时区标签(区,管理中文)
        时区={'system':系统,'label':标时区}
        for 项 in 行:
            条=文档.createElement('li')
            钮=文档.createElement('button')
            钮.type='button'
            类名='row'
            if 自身.选中==项.get('id'):
                类名=类名+' selectedRow'
            if 项.get('status')=='inactive':
                类名=类名+' endedRow'
            钮.className=类名
            标(钮)
            钮.setAttribute('aria-label',任务名(项))
            钮.appendChild(画时钟(文档,16))
            体=文档.createElement('span')
            体.className='rowContent'
            标(体)
            名=文档.createElement('span')
            名.className='rowTitle'
            标(名)
            名.textContent=任务名(项)
            体.appendChild(名)
            摘=文档.createElement('span')
            摘.className='rowSummary'
            标(摘)
            if 项.get('status')=='inactive':
                态=文档.createElement('span')
                态.className='metadata'
                标(态)
                态.textContent=管理中文['status.inactive']
                摘.appendChild(态)
            频=文档.createElement('span')
            频.className='metadata'
            标(频)
            频.textContent=格式化日程频率(项,管理中文,时区)
            摘.appendChild(频)
            if 项.get('status')=='active':
                两段=下次运行两段(项.get('scheduledAt') or '',管理中文['time.locale'],自身.现在,管理中文)
                下=文档.createElement('span')
                下.className='metadata'
                标(下)
                下.appendChild(文档.createTextNode(管理中文['list.nextPrefix']))
                时=文档.createElement('time')
                时.setAttribute('dateTime',项.get('scheduledAt') or '')
                时.textContent=两段['absolute']
                下.appendChild(时)
                下.appendChild(文档.createTextNode(' '))
                相对=文档.createElement('span')
                相对.className='nextRunRelative'
                标(相对)
                相对.textContent=两段['relative']
                下.appendChild(相对)
                摘.appendChild(下)
            体.appendChild(摘)
            钮.appendChild(体)
            def 点行(事件,标识=项.get('id')):
                '打开这一条的详情'
                自身.选中=标识
                自身.控制.设页('rule')
                自身.渲染()
            钮.addEventListener('click',点行)
            条.appendChild(钮)
            列表.appendChild(条)
        表.appendChild(列表)
        内容.appendChild(表)
        滚.appendChild(内容)
        列.appendChild(滚)
        根.appendChild(列)
        if 选中任务 is not None:
            详情属性=dict(快照['props'])
            详情属性['window']=窗口
            详情属性['task']=选中任务
            详情属性['authoritative']=快照['record'] is not None
            详情属性['onDeleted']=自身.关掉
            详情属性['onClose']=自身.关掉
            if 自身.详情 is None:
                自身.详情=任务详情(详情属性)
            节点=自身.详情(详情属性)
            if 节点 is not None:
                根.appendChild(节点)
        elif 目录.get('status')=='ready' and 自身.选中 is not None and 选中任务 is None:
            自身.选中=None
        return 根

    def 关掉(自身):
        '回到列表'
        自身.选中=None
        自身.渲染()
