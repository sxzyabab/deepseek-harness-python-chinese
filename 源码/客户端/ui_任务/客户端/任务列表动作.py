import importlib.resources as 包资源
from ..异常 import 断言穷尽
from ...ui_基础界面组件.ansi import 解析ansi行
from ...ui_基础界面组件.复制反馈 import 复制反馈毫秒
from ...ui_基础界面组件.状态点 import 状态点

样式文本=包资源.files(__package__).joinpath('任务列表动作.module.css').read_text(encoding='utf-8')
样式文本=样式文本.replace(':global([data-terminal])','[data-terminal]')

视口边距=12
菜单间隙=5
可聚焦='button:not(:disabled), a[href], [tabindex]:not([tabindex="-1"])'
武装毫秒=3000
失败毫秒=4000
空作业=()

def 确保样式(窗):
    '任务列表样式按文档只插一次'
    文档=窗.document
    if 文档.getElementById('任务列表样式') is not None:
        return
    样式=文档.createElement('style')
    样式.id='任务列表样式'
    样式.textContent=样式文本
    文档.head.appendChild(样式)

def 是否进行中(作业):
    '运行中或正在停止'
    状况=作业['status']
    return 状况=='running' or 状况=='stopping'

def 是否可观测(作业):
    '进行中，或已经留下保留输出'
    if 是否进行中(作业):
        return True
    return 作业['output']['total']>0

def 序(作业):
    '进行中按开始升序，已结束按完结降序，同一毫秒再按开始'
    开始=作业['startedAt']
    if 是否进行中(作业):
        return (0,开始,0)
    完结=作业['finishedAt'] if 'finishedAt' in 作业 and 作业['finishedAt'] is not None else 开始
    return (1,-完结,开始)

def 像素(数):
    '整像素不带小数'
    if 数==int(数):
        return str(int(数))+'px'
    return str(数)+'px'

def 下箭头(文档,类名):
    '常规一像素下箭头'
    图=文档.createElementNS('http://www.w3.org/2000/svg','svg')
    图.setAttribute('width','12')
    图.setAttribute('height','12')
    图.setAttribute('viewBox','0 0 16 16')
    图.setAttribute('fill','none')
    图.setAttribute('stroke-width','1')
    图.setAttribute('aria-hidden','true')
    if 类名 is not None and 类名!='':
        图.setAttribute('class',类名)
    路=文档.createElementNS('http://www.w3.org/2000/svg','path')
    路.setAttribute('d','M4 6L7.29289 9.29289C7.68342 9.68342 8.31658 9.68342 8.70711 9.29289L12 6')
    路.setAttribute('stroke','currentColor')
    图.appendChild(路)
    return 图

def 建文(文档,文,类名):
    '一段文字'
    节点=文档.createElement('span')
    节点.className=类名
    节点.textContent=文
    return 节点

class 作业项:
    '一行作业。进行中可两击停止，可观测时可展开输出'
    def __init__(自身,文档,列表):
        '建出 li，内容等第一次更新'
        自身.文档=文档
        自身.列表=列表
        自身.根=文档.createElement('li')
        自身.根.className='item'
        自身.作业=None
        自身.形状=None
        自身.进行=False
        自身.行按钮=None
        自身.停止按钮=None
        自身.停止文=None
        自身.时长节点=None
        自身.标签节点=None
        自身.状态节点=None
        自身.细节节点=None
        自身.次要=None
        自身.箭头=None
        自身.面板=None
        自身._面板键=None

    def 更新(自身,作业,视图,展开,现在,停止态):
        '形状变了就重建节点，否则只改文案和面板'
        自身.作业=作业
        进行=是否进行中(作业)
        可观测=是否可观测(作业)
        状况=作业['status']
        if 状况=='running':
            点='ongoing'
        elif 状况=='stopping' or 状况=='killed':
            点='warning'
        elif 状况=='completed':
            点='done'
        elif 状况=='failed':
            点='error'
        else:
            断言穷尽(状况)
        形状=(进行,可观测,状况=='running',点)
        if 形状!=自身.形状:
            自身.重建(作业,形状,进行,可观测,点)
        自身.填(作业,视图,展开,现在,停止态,进行)
        return 自身.根

    def 按下展开(自身,事件):
        '展开或收起这一行'
        键=str(自身.作业['id'])
        if 自身.列表.展开键==键:
            自身.列表.展开键=None
        else:
            自身.列表.展开键=键
        自身.列表.渲染()

    def 按下停止(自身,事件):
        '把这一行交给列表的两击停止'
        自身.列表.按下停止(自身.作业)

    def 重建(自身,作业,形状,进行,可观测,点):
        '按进行中或已结束摆这一行的骨架'
        文档=自身.文档
        根=自身.根
        while 根.firstChild is not None:
            根.firstChild.remove()
        自身.形状=形状
        自身.进行=进行
        自身.面板=None
        自身._面板键=None
        自身.细节节点=None
        自身.停止按钮=None
        自身.停止文=None
        行线=文档.createElement('div')
        if 进行:
            行线.className='rowLine rowLineLive'
        else:
            行线.className='rowLine'
        if 可观测:
            行=文档.createElement('button')
            行.type='button'
            if 进行:
                行.className='row'
            else:
                行.className='row rowSettled'
            行.addEventListener('click',自身.按下展开)
            自身.行按钮=行
        else:
            行=文档.createElement('span')
            行.className='row rowSettled rowStatic'
            自身.行按钮=None
        窗=自身.列表.属性['window']
        行.appendChild(状态点({'window':窗,'state':点,'className':'rowDot'}).渲染())
        标签=作业['label']
        种类=作业['kind']
        if 进行:
            主=文档.createElement('span')
            主.className='main'
            主行=文档.createElement('span')
            主行.className='primary'
            标签节点=建文(文档,标签,'label')
            标签节点.setAttribute('title',标签)
            主行.appendChild(标签节点)
            主.appendChild(主行)
            次要=文档.createElement('span')
            次要.className='secondary'
            次要.appendChild(建文(文档,种类,'kind'))
            时长节点=建文(文档,'','duration')
            次要.appendChild(时长节点)
            主.appendChild(次要)
            行.appendChild(主)
            盒=文档.createElement('span')
            盒.className='chevronBox'
            箭头=下箭头(文档,'chevron')
            盒.appendChild(箭头)
            行.appendChild(盒)
            自身.次要=次要
            自身.箭头=箭头
            自身.标签节点=标签节点
            自身.时长节点=时长节点
            自身.状态节点=None
        else:
            行.appendChild(建文(文档,种类,'kind'))
            标签节点=建文(文档,标签,'label')
            标签节点.setAttribute('title',标签)
            行.appendChild(标签节点)
            状态节点=建文(文档,'','status')
            行.appendChild(状态节点)
            时长节点=建文(文档,'','duration')
            行.appendChild(时长节点)
            自身.标签节点=标签节点
            自身.状态节点=状态节点
            自身.时长节点=时长节点
            自身.次要=None
            if 可观测:
                盒=文档.createElement('span')
                盒.className='chevronBox'
                箭头=下箭头(文档,'chevron')
                盒.appendChild(箭头)
                行.appendChild(盒)
                自身.箭头=箭头
            else:
                自身.箭头=None
        行线.appendChild(行)
        if 作业['status']=='running':
            钮=文档.createElement('button')
            钮.type='button'
            钮.className='stop'
            钮.addEventListener('click',自身.按下停止)
            图=文档.createElementNS('http://www.w3.org/2000/svg','svg')
            图.setAttribute('width','10')
            图.setAttribute('height','10')
            图.setAttribute('viewBox','0 0 16 16')
            图.setAttribute('fill','none')
            图.setAttribute('aria-hidden','true')
            路=文档.createElementNS('http://www.w3.org/2000/svg','path')
            路.setAttribute('d','M12.5 2.5H3.5C2.94772 2.5 2.5 2.94772 2.5 3.5V12.5C2.5 13.0523 2.94772 13.5 3.5 13.5H12.5C13.0523 13.5 13.5 13.0523 13.5 12.5V3.5C13.5 2.94772 13.0523 2.5 12.5 2.5Z')
            路.setAttribute('fill','currentColor')
            图.appendChild(路)
            钮.appendChild(图)
            停止文=文档.createElement('span')
            停止文.className='stopLabel'
            行线.appendChild(钮)
            自身.停止按钮=钮
            自身.停止文=停止文
        根.appendChild(行线)

    def 填(自身,作业,视图,展开,现在,停止态,进行):
        '改标签、时长、停止按钮和输出面板'
        标签=作业['label']
        自身.标签节点.textContent=标签
        自身.标签节点.setAttribute('title',标签)
        if 'progress' in 作业 and 作业['progress'] is not None:
            细节=作业['progress']
        elif 'detail' in 作业:
            细节=作业['detail']
        else:
            细节=None
        状况=作业['status']
        if 状况=='running':
            词='运行中'
        elif 状况=='stopping':
            词='正在停止'
        elif 状况=='completed':
            词='已完成'
        elif 状况=='killed':
            词='已取消'
        elif 状况=='failed':
            词='已失败'
        else:
            断言穷尽(状况)
        if 进行:
            次要标题=词 if 细节 is None else str(细节)
            自身.次要.setAttribute('title',次要标题)
            if 细节 is None:
                if 自身.细节节点 is not None:
                    自身.细节节点.remove()
                    自身.细节节点=None
            elif 自身.细节节点 is None:
                自身.细节节点=建文(自身.文档,str(细节),'status')
                自身.次要.insertBefore(自身.细节节点,自身.时长节点)
            else:
                自身.细节节点.textContent=str(细节)
        else:
            展示=词 if 细节 is None else str(细节)
            自身.状态节点.textContent=展示
            自身.状态节点.setAttribute('title',展示)
        if 'finishedAt' in 作业 and 作业['finishedAt'] is not None:
            完结=作业['finishedAt']
        else:
            完结=作业['startedAt']
        if 进行:
            经过=现在-作业['startedAt']
        else:
            经过=完结-作业['startedAt']
        总秒=经过//1000
        if 总秒<0:
            总秒=0
        秒=总秒%60
        分=(总秒//60)%60
        时=总秒//3600
        if 时>0:
            时长=f'{时}小时{分}分'
        elif 分>0:
            时长=f'{分}分{秒}秒'
        else:
            时长=f'{秒}秒'
        if 进行:
            时长标题=f'已运行 {时长}'
        else:
            时长标题=f'耗时 {时长}'
        自身.时长节点.textContent=时长
        自身.时长节点.setAttribute('title',时长标题)
        if 自身.行按钮 is not None:
            if 展开:
                无障碍=f'收起 {标签} 的实时输出'
            else:
                无障碍=f'展开 {标签} 的实时输出'
            自身.行按钮.setAttribute('aria-expanded','true' if 展开 else 'false')
            自身.行按钮.setAttribute('aria-label',无障碍)
        if 自身.箭头 is not None:
            if 展开:
                自身.箭头.setAttribute('class','chevron chevronOpen')
            else:
                自身.箭头.setAttribute('class','chevron')
        if 自身.停止按钮 is not None:
            if 停止态=='armed':
                自身.停止按钮.className='stop stopArmed'
                标题='再次点击确认停止'
            elif 停止态=='failed':
                自身.停止按钮.className='stop stopFailed'
                标题='停止失败'
            else:
                自身.停止按钮.className='stop'
                标题=f'停止任务 {标签}'
            自身.停止按钮.setAttribute('data-kill-state',停止态)
            自身.停止按钮.setAttribute('aria-label',标题)
            自身.停止按钮.setAttribute('title',标题)
            自身.停止按钮.disabled=停止态=='pending'
            if 停止态=='armed':
                自身.停止文.textContent='确认停止'
                if 自身.停止文.parentElement is None:
                    自身.停止按钮.appendChild(自身.停止文)
            elif 自身.停止文.parentElement is not None:
                自身.停止文.remove()
        面板键=None
        if 展开 and 视图 is not None:
            缺口=视图['gapBefore'] if 'gapBefore' in 视图 else False
            断流=视图['error'] if 'error' in 视图 else None
            文=视图['text'] if 'text' in 视图 else ''
            面板键=(进行,文,缺口,断流,标签)
        if 面板键!=自身._面板键 or (面板键 is not None and 自身.面板 is None):
            if 自身.面板 is not None:
                自身.面板.remove()
                自身.面板=None
            自身._面板键=面板键
            if 面板键 is not None:
                自身.面板=自身.画面板(视图,进行,标签)
                自身.根.appendChild(自身.面板)

    def 画面板(自身,视图,进行,标签):
        '不重复状态点，输出不封顶，复制的是命令'
        文档=自身.文档
        面板=文档.createElement('div')
        面板.className='panel'
        if 'gapBefore' in 视图 and 视图['gapBefore']:
            缺口=文档.createElement('div')
            缺口.className='notice'
            缺口.textContent='……较早的输出已丢弃……'
            面板.appendChild(缺口)
        if 'error' in 视图 and 视图['error'] is not None:
            断流=文档.createElement('div')
            断流.className='notice noticeError'
            断流.textContent='实时输出流中断：'+str(视图['error'])
            面板.appendChild(断流)
        文本=''
        if 'text' in 视图 and 视图['text'] is not None:
            文本=视图['text']
        行列表=解析ansi行(文本)
        if len(行列表)>1:
            末=行列表[-1]
            全空=True
            for 段 in 末:
                if 段['text']!='':
                    全空=False
                    break
            if 全空:
                行列表=行列表[:-1]
        空=True
        for 线 in 行列表:
            for 段 in 线:
                if 段['text'].strip()!='':
                    空=False
                    break
            if 空 is False:
                break
        有正文=(进行 is False) or (空 is False)
        终端=文档.createElement('div')
        终端.setAttribute('data-terminal','')
        if 进行:
            终端.setAttribute('data-running','')
        if 有正文:
            终端.setAttribute('data-body','')
        头=文档.createElement('div')
        命令体=标签
        if 命令体.endswith('\n'):
            命令体=命令体[:-1]
        行号=1
        for 命令行 in 命令体.split('\n'):
            行盒=文档.createElement('div')
            行盒.textContent=命令行
            行盒.setAttribute('aria-label','命令第 '+str(行号)+' 行')
            头.appendChild(行盒)
            行号=行号+1
        复制钮=文档.createElement('button')
        复制钮.type='button'
        复制钮.textContent='复制'
        def 点复制(事件):
            '复制命令'
            自身.列表.属性['window'].navigator.clipboard.writeText(自身.作业['label'])
            复制钮.textContent='已复制'
            def 恢复():
                '反馈窗口结束'
                复制钮.textContent='复制'
            自身.列表.属性['window'].setTimeout(恢复,复制反馈毫秒)
        复制钮.addEventListener('click',点复制)
        头.appendChild(复制钮)
        终端.appendChild(头)
        if 有正文 and 空:
            空文=文档.createElement('div')
            空文.textContent='（无输出）'
            终端.appendChild(空文)
        elif 有正文:
            for 线 in 行列表:
                行盒=文档.createElement('div')
                行盒.textContent=''.join(段['text'] for 段 in 线)
                终端.appendChild(行盒)
        面板.appendChild(终端)
        return 面板

class 任务列表动作:
    '会话头部的后台任务。调用本类得到根节点；没有可见作业时得到 None'
    实例表={}

    def __new__(类,属性):
        '同一会话复用一份状态，返回当前根节点'
        键=属性['sessionId']
        已=类.实例表[键] if 键 in 类.实例表 else None
        if 已 is None:
            已=object.__new__(类)
            类.实例表[键]=已
            return 已.建立(属性)
        已.更新(属性)
        return 已.渲染()

    def 建立(自身,属性):
        '记下注入面并画第一次'
        自身.属性=属性
        自身.打开=False
        自身.展开键=None
        自身.现在=0
        自身.已结束展开=None
        自身.已清空=set()
        自身.停止阶段=None
        自身.根=None
        自身.触发=None
        自身.触发点=None
        自身.计数节点=None
        自身.触发箭头=None
        自身.菜单=None
        自身.列表节点=None
        自身.进行标题=None
        自身.已结束标题=None
        自身.已结束钮=None
        自身.已结束箭头=None
        自身.已结束文=None
        自身.文档=None
        自身.项表={}
        自身._绘制中=False
        自身._待重画=False
        自身._监视会话=None
        自身._监视函数=None
        自身._停监视=None
        自身._订函数=None
        自身._退订=None
        自身._观测键=None
        自身._观测函数=None
        自身._停观测=None
        自身._钟=None
        自身._停计=None
        自身._计时标记=None
        自身._在听外部=False
        自身._在听视口=False
        自身._尺寸观察=None
        自身._父=None
        自身._进行行=[]
        自身._已结束行=[]
        return 自身.渲染()

    def 更新(自身,属性):
        '刷新合成 props'
        自身.属性=属性

    def 渲染(自身):
        '重入时记一笔，画完再补'
        if 自身._绘制中:
            自身._待重画=True
            if 自身.根 is not None and 自身.根.parentElement is None and 自身.打开 is not True and len(自身._进行行)+len(自身._已结束行)==0:
                return None
            return 自身.根
        自身._绘制中=True
        try:
            结果=自身.画出()
        finally:
            自身._绘制中=False
        if 自身._待重画:
            自身._待重画=False
            return 自身.渲染()
        return 结果

    def 拆除(自身):
        '放开名册、观察、时钟和页面监听'
        if 自身._停监视 is not None:
            自身._停监视()
            自身._停监视=None
        if 自身._停观测 is not None:
            自身._停观测()
            自身._停观测=None
        if 自身._退订 is not None:
            自身._退订()
            自身._退订=None
        自身.同步时钟(False)
        自身.取消停止计时()
        自身.关菜单()
        会话=自身.属性['sessionId']
        if 任务列表动作.实例表.get(会话) is 自身:
            del 任务列表动作.实例表[会话]

    def 画出(自身):
        '没有可见作业时不留节点。打开时把列表挂到 document.body'
        确保样式(自身.属性['window'])
        自身.文档=自身.属性['window'].document
        自身.同步订阅()
        自身.同步名册()
        行表=sorted(list(自身.读作业()),key=序)
        观测=自身.读观测()
        if 自身.展开键 is not None:
            还在=False
            for 作业 in 行表:
                if str(作业['id'])==自身.展开键:
                    还在=True
                    break
            if 还在 is not True:
                自身.展开键=None
        if 自身.停止阶段 is not None:
            还能停=False
            阶段键=自身.停止阶段['key']
            for 作业 in 行表:
                if str(作业['id'])==阶段键 and 作业['status']=='running':
                    还能停=True
                    break
            if 还能停 is not True:
                自身.停止阶段=None
        进行行=[]
        已结束行=[]
        for 作业 in 行表:
            if 是否进行中(作业):
                进行行.append(作业)
                continue
            if str(作业['id']) in 自身.已清空:
                continue
            已结束行.append(作业)
        自身._进行行=进行行
        自身._已结束行=已结束行
        可见数=len(进行行)+len(已结束行)
        if 可见数==0:
            自身.打开=False
            自身.同步观测(行表)
            自身.同步时钟(False)
            自身.同步停止计时()
            自身.关菜单()
            if 自身.根 is not None and 自身.根.parentElement is not None:
                自身._父=自身.根.parentElement
                自身.根.remove()
            return None
        自身.确保根(自身.文档)
        if 自身.根.parentElement is None and 自身._父 is not None:
            自身._父.appendChild(自身.根)
        if len(进行行)>0:
            数目=len(进行行)
            计数=f'{数目} 个后台任务运行中'
        elif 可见数==1:
            计数=f'{可见数} 个后台任务'
        else:
            计数=f'{可见数} 个后台任务'
        自身.更新触发(计数,len(进行行)>0)
        自身.同步时钟(自身.打开 and len(进行行)>0)
        自身.同步观测(行表)
        自身.同步停止计时()
        if 自身.打开:
            自身.确保菜单(自身.文档)
            if 自身.菜单.parentElement is None:
                自身.菜单.style.visibility='hidden'
                自身.菜单.style.left='0px'
                自身.菜单.style.top='0px'
                自身.文档.body.appendChild(自身.菜单)
            if 自身.已结束展开 is None:
                已结束展开=len(进行行)==0
            else:
                已结束展开=自身.已结束展开
            自身.排上(进行行,已结束行,已结束展开,观测,自身.现在)
            自身.放置()
            自身.听外部(True)
            自身.听视口(True)
        else:
            自身.关菜单()
        return 自身.根

    def 读作业(自身):
        '本会话的作业行。页面上的快照在这里读回'
        会话=自身.属性['sessionId']
        def 选行(快照):
            'rows[sessionId]'
            表=快照['rows']
            if 会话 in 表 and 表[会话] is not None:
                return 表[会话]
            return 空作业
        行=自身.属性['useJobs'](选行)
        if 行 is None:
            return 空作业
        return 行

    def 读观测(自身):
        '观察快照。页面上的快照在这里读回'
        def 选观测(快照):
            'observed'
            return 快照['observed']
        return 自身.属性['useJobs'](选观测)

    def 同步订阅(自身):
        '名册变化时重画'
        用=自身.属性['useJobs']
        if 自身._订函数 is 用:
            return
        if 自身._退订 is not None:
            自身._退订()
        def 变():
            '快照变了就重画'
            if 自身._绘制中:
                自身._待重画=True
                return
            自身.渲染()
        自身._退订=用._subscribe(变)
        自身._订函数=用

    def 同步名册(自身):
        '挂载期间保持这一会话的名册，会话换了就放开上一个'
        会话=自身.属性['sessionId']
        监视=自身.属性['watchRows']
        if 自身._监视会话==会话 and 自身._监视函数 is 监视 and 自身._停监视 is not None:
            return
        if 自身._停监视 is not None:
            自身._停监视()
        自身._停监视=监视(会话)
        自身._监视会话=会话
        自身._监视函数=监视

    def 同步观测(自身,行表):
        '只有打开且展开的可观测行才拉输出，收起或关掉就停'
        活动标识=None
        活动键=None
        if 自身.打开 and 自身.展开键 is not None:
            for 作业 in 行表:
                if str(作业['id'])==自身.展开键 and 是否可观测(作业):
                    活动标识=作业['id']
                    活动键=自身.展开键
                    break
        观测函数=自身.属性['observe']
        if 活动键==自身._观测键 and 自身._观测函数 is 观测函数:
            return
        if 自身._停观测 is not None:
            自身._停观测()
            自身._停观测=None
        自身._观测键=活动键
        自身._观测函数=观测函数
        if 活动标识 is None:
            return
        自身._停观测=观测函数(自身.属性['sessionId'],活动标识)

    def 同步时钟(自身,需要):
        '列表打开且有进行中的作业时，每秒向页面取时钟'
        窗=自身.属性['window']
        if 需要 and 自身._钟 is None:
            自身.现在=窗.Date.now()
            def 滴答():
                '采样页面时钟'
                自身.现在=自身.属性['window'].Date.now()
                自身.渲染()
            自身._钟=窗.setInterval(滴答,1000)
            return
        if 需要 is not True and 自身._钟 is not None:
            窗.clearInterval(自身._钟)
            自身._钟=None

    def 同步停止计时(自身):
        '武装等确认，失败等提示。正在停止的那下不设表'
        阶段=自身.停止阶段
        标记=None
        毫秒=None
        if 阶段 is not None and 阶段['state']=='armed':
            标记=(阶段['key'],'armed')
            毫秒=武装毫秒
        elif 阶段 is not None and 阶段['state']=='failed':
            标记=(阶段['key'],'failed')
            毫秒=失败毫秒
        if 标记==自身._计时标记:
            return
        自身.取消停止计时()
        自身._计时标记=标记
        if 毫秒 is None:
            return
        def 到():
            '到点收回停止按钮'
            自身.停止阶段=None
            自身._计时标记=None
            自身.渲染()
        自身._停计=自身.属性['window'].setTimeout(到,毫秒)

    def 取消停止计时(自身):
        '清掉武装或失败提示的表'
        if 自身._停计 is None:
            return
        自身.属性['window'].clearTimeout(自身._停计)
        自身._停计=None

    def 确保根(自身,文档):
        '触发器只建一次'
        if 自身.根 is not None:
            return
        根=文档.createElement('div')
        根.addEventListener('keydown',自身.按键)
        触发=文档.createElement('button')
        触发.type='button'
        触发.className='trigger'
        触发.addEventListener('click',自身.点触发)
        计数=文档.createElement('span')
        计数.className='count'
        触发.appendChild(计数)
        箭头=下箭头(文档,None)
        触发.appendChild(箭头)
        根.appendChild(触发)
        自身.根=根
        自身.触发=触发
        自身.计数节点=计数
        自身.触发箭头=箭头
        自身.触发点=None

    def 更新触发(自身,计数,有进行):
        '改计数、进行中的点和箭头'
        自身.计数节点.textContent=计数
        自身.触发.setAttribute('aria-label',计数)
        自身.触发.setAttribute('aria-expanded','true' if 自身.打开 else 'false')
        窗=自身.属性['window']
        if 有进行:
            if 自身.触发点 is None:
                自身.触发点=状态点({'window':窗,'state':'ongoing','className':'triggerDot'}).渲染()
                自身.触发.insertBefore(自身.触发点,自身.计数节点)
        elif 自身.触发点 is not None:
            自身.触发点.remove()
            自身.触发点=None
        if 自身.打开:
            自身.触发箭头.setAttribute('class','triggerOpen')
        else:
            自身.触发箭头.removeAttribute('class')

    def 确保菜单(自身,文档):
        '菜单和列表节点保持不变'
        if 自身.菜单 is not None:
            return
        菜单=文档.createElement('div')
        菜单.setAttribute('data-menu-material','translucent')
        菜单.className='menu'
        菜单.addEventListener('keydown',自身.按键)
        材料=文档.createElement('div')
        材料.setAttribute('aria-hidden','true')
        菜单.appendChild(材料)
        列表=文档.createElement('ul')
        列表.className='menuBody'
        列表.setAttribute('aria-label','后台任务')
        菜单.appendChild(列表)
        进行标题=文档.createElement('li')
        进行标题.className='sectionHeader'
        进行标题.setAttribute('aria-hidden','true')
        进行标题.textContent='进行中'
        已结束标题=文档.createElement('li')
        已结束标题.className='sectionHeader'
        已结束钮=文档.createElement('button')
        已结束钮.type='button'
        已结束钮.className='sectionToggle'
        已结束钮.addEventListener('click',自身.点已结束)
        已结束箭头=下箭头(文档,'sectionChevron')
        已结束文=文档.createElement('span')
        已结束钮.appendChild(已结束箭头)
        已结束钮.appendChild(已结束文)
        清空钮=文档.createElement('button')
        清空钮.type='button'
        清空钮.className='sectionClear'
        清空钮.textContent='清空'
        清空钮.addEventListener('click',自身.点清空)
        已结束标题.appendChild(已结束钮)
        已结束标题.appendChild(清空钮)
        自身.菜单=菜单
        自身.列表节点=列表
        自身.进行标题=进行标题
        自身.已结束标题=已结束标题
        自身.已结束钮=已结束钮
        自身.已结束箭头=已结束箭头
        自身.已结束文=已结束文

    def 排上(自身,进行行,已结束行,已结束展开,观测,现在):
        '按顺序摆分组和作业行。同一条作业沿用原来的节点'
        节点=[]
        在册=set()
        if len(进行行)>0:
            自身.进行标题.textContent='进行中'
            节点.append(自身.进行标题)
            for 作业 in 进行行:
                节点.append(自身.取项(作业,观测,现在))
                在册.add(str(作业['id']))
        if len(已结束行)>0:
            if 已结束展开:
                自身.已结束箭头.setAttribute('class','sectionChevron sectionChevronOpen')
            else:
                自身.已结束箭头.setAttribute('class','sectionChevron')
            自身.已结束钮.setAttribute('aria-expanded','true' if 已结束展开 else 'false')
            自身.已结束文.textContent=f'已结束 {len(已结束行)}'
            节点.append(自身.已结束标题)
            if 已结束展开:
                for 作业 in 已结束行:
                    节点.append(自身.取项(作业,观测,现在))
                    在册.add(str(作业['id']))
        for 作业 in 已结束行:
            在册.add(str(作业['id']))
        列表=自身.列表节点
        while 列表.firstChild is not None:
            列表.firstChild.remove()
        for 节点项 in 节点:
            列表.appendChild(节点项)
        失效=[]
        for 键 in 自身.项表:
            if 键 not in 在册:
                失效.append(键)
        for 键 in 失效:
            del 自身.项表[键]

    def 取项(自身,作业,观测,现在):
        '取出或建出这一行，并按当前快照填'
        键=str(作业['id'])
        项=自身.项表[键] if 键 in 自身.项表 else None
        if 项 is None:
            项=作业项(自身.文档,自身)
            自身.项表[键]=项
        视图=None
        if 是否可观测(作业) and 键 in 观测:
            视图=观测[键]
        展开=自身.展开键==键
        停止态='idle'
        if 自身.停止阶段 is not None and 自身.停止阶段['key']==键:
            停止态=自身.停止阶段['state']
        return 项.更新(作业,视图,展开,现在,停止态)

    def 放置(自身):
        '按触发器矩形把列表固定在视口里，顶边让出窗框'
        菜单=自身.菜单
        根=自身.根
        if 菜单 is None or 根 is None:
            return
        窗=自身.属性['window']
        矩形=根.getBoundingClientRect()
        宽=菜单.offsetWidth
        高=菜单.offsetHeight
        if 宽 is None:
            宽=0
        if 高 is None:
            高=0
        左=矩形.left
        顶=矩形.bottom+菜单间隙
        边=视口边距
        if 宽>0:
            左限=窗.innerWidth-宽-边
            if 左<边:
                左=边
            if 左>左限:
                左=左限
        顶最小=边
        文档根=窗.document.documentElement
        原文=窗.getComputedStyle(文档根).getPropertyValue('--dsh-frame-top-clearance').strip()
        数字=''
        for 字 in 原文:
            if 字.isdigit() or 字=='.' or (字=='-' and 数字==''):
                数字=数字+字
                continue
            if 数字!='':
                break
        if 数字!='' and 数字!='-' and 数字!='.':
            净空=float(数字)
            if 文档根.hasAttribute('data-fullscreen'):
                抬=0
            else:
                抬=净空
            候选=抬+20
            if 候选>顶最小:
                顶最小=候选
        if 高>0:
            顶限=窗.innerHeight-高-边
            if 顶<顶最小:
                顶=顶最小
            if 顶>顶限:
                顶=顶限
        菜单.style.left=像素(左)
        菜单.style.top=像素(顶)
        菜单.style.visibility=''

    def 听外部(自身,开):
        '打开时，点到触发器和列表外面就收起'
        文档=自身.属性['window'].document
        if 开:
            if 自身._在听外部:
                return
            文档.addEventListener('pointerdown',自身.外部按下)
            自身._在听外部=True
            return
        if 自身._在听外部 is not True:
            return
        文档.removeEventListener('pointerdown',自身.外部按下)
        自身._在听外部=False

    def 听视口(自身,开):
        '滚动、缩放和列表自己变高时重新放置'
        窗=自身.属性['window']
        if 开:
            if 自身._在听视口:
                return
            窗.addEventListener('scroll',自身.放置,True)
            窗.addEventListener('resize',自身.放置)
            观察器类=getattr(窗,'ResizeObserver',None)
            if 观察器类 is not None and 自身.菜单 is not None:
                自身._尺寸观察=观察器类(自身.放置)
                自身._尺寸观察.observe(自身.菜单)
            自身._在听视口=True
            return
        if 自身._在听视口 is not True:
            return
        窗.removeEventListener('scroll',自身.放置,True)
        窗.removeEventListener('resize',自身.放置)
        if 自身._尺寸观察 is not None:
            自身._尺寸观察.disconnect()
            自身._尺寸观察=None
        自身._在听视口=False

    def 外部按下(自身,事件):
        '点在列表或触发器里不算外面'
        目标=事件.target
        根内=False
        if 自身.根 is not None:
            根内=自身.根.contains(目标) is True
        菜单内=False
        if 自身.菜单 is not None:
            菜单内=自身.菜单.contains(目标) is True
        if 根内 is not True and 菜单内 is not True:
            自身.打开=False
            自身.渲染()

    def 关菜单(自身):
        '从页面上拿掉列表，并松开外部点击和视口监听'
        if 自身.菜单 is not None and 自身.菜单.parentElement is not None:
            自身.菜单.remove()
        自身.听外部(False)
        自身.听视口(False)

    def 点触发(自身,事件):
        '打开时先取页面时钟，避免第一帧把时长算成零'
        自身.现在=自身.属性['window'].Date.now()
        自身.打开=not 自身.打开
        自身.渲染()

    def 点已结束(自身,事件):
        '用户点过之后，折叠不再跟着有没有进行中的作业变'
        if 自身.已结束展开 is None:
            当前=len(自身._进行行)==0
        else:
            当前=自身.已结束展开
        自身.已结束展开=not 当前
        自身.渲染()

    def 点清空(自身,事件):
        '只在这一页藏起当前已结束的行'
        for 作业 in 自身._已结束行:
            自身.已清空.add(str(作业['id']))
        if 自身.展开键 is not None:
            for 作业 in 自身._已结束行:
                if str(作业['id'])==自身.展开键:
                    自身.展开键=None
                    break
        自身.渲染()

    def 按下停止(自身,作业):
        '第一下武装，第二下才停止。接纳之后保持进行中，直到这一行不再可停'
        键=str(作业['id'])
        阶段=自身.停止阶段
        if 阶段 is None or 阶段['key']!=键 or 阶段['state']!='armed':
            自身.停止阶段={'key':键,'state':'armed'}
            自身.渲染()
            return
        自身.停止阶段={'key':键,'state':'pending'}
        自身.渲染()
        成功=自身.属性['killJob'](自身.属性['sessionId'],键)
        当前=自身.停止阶段
        if 当前 is not None and 当前['key']==键 and 成功 is not True:
            自身.停止阶段={'key':键,'state':'failed'}
        自身.渲染()

    def 按键(自身,事件):
        'Tab 在触发器和列表之间衔接，Escape 关掉列表并回到触发器'
        if 自身.打开 is not True:
            return
        触发=自身.触发
        键名=事件.key
        if 键名=='Escape':
            事件.preventDefault()
            自身.打开=False
            自身.渲染()
            触发.focus()
            return
        if 键名!='Tab' or 触发 is None or 自身.菜单 is None:
            return
        焦点=[]
        for 项 in 自身.菜单.querySelectorAll(可聚焦):
            焦点.append(项)
        目标=事件.target
        if 目标 is 触发 or 目标==触发:
            if 事件.shiftKey:
                return
            事件.preventDefault()
            if len(焦点)>0:
                焦点[0].focus()
            return
        if len(焦点)==0:
            return
        在首=目标 is 焦点[0] or 目标==焦点[0]
        在尾=目标 is 焦点[-1] or 目标==焦点[-1]
        if 事件.shiftKey:
            if 在首:
                事件.preventDefault()
                触发.focus()
            return
        if 在尾:
            触发.focus()
