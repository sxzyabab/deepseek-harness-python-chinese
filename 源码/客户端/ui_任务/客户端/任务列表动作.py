import importlib.resources as 包资源
import re as 正则
from nicegui import ui as 界面
from ....基础设施.通用工具 import 当前毫秒
from ...ui_基础界面组件.终端块 import 终端块
from ...ui_基础界面组件.状态点 import 状态点
from ..异常 import 去掉敏感,作业列表错误,页面失败文案

__all__=['任务列表动作']

视口边距=12
武装毫秒=3_000
失败毫秒=4_000
空作业=()

def 读样式():
    '读同目录样式。打不开时只报样式读不到，不含路径'
    try:
        return 包资源.files(__package__).joinpath('任务列表动作.module.css').read_text(encoding='utf-8')
    except OSError:
        raise OSError('样式读不到') from None

def 去注释(原文):
    '去掉块注释，避免注释里的花括号打断规则'
    出=[]
    下标=0
    长度=len(原文)
    while 下标<长度:
        if 原文.startswith('/*',下标):
            止=原文.find('*/',下标+2)
            if 止<0:
                break
            下标=止+2
            continue
        出.append(原文[下标])
        下标+=1
    return ''.join(出)

def 挂到根(原文,根):
    '类选择器只作用在任务列表根下'
    文=正则.sub(r':global\(([^)]*)\)',r'\1',去注释(原文))
    def 换(匹配):
        选择器=匹配.group(1).strip()
        体=匹配.group(2)
        if 选择器.startswith('@'):
            return 选择器+'{'+体+'}'
        条=[]
        for 片 in 选择器.split(','):
            片=片.strip()
            if 片=='':
                continue
            条.append('.'+根+' '+片)
            条.append('.'+根+片)
        if len(条)==0:
            return ''
        return ', '.join(条)+'{'+体+'}'
    return 正则.sub(r'([^{]+)\{([^}]*)\}',换,文)

样式表=挂到根(读样式(),'任务列表')
界面.add_css(样式表,shared=True)

def 是否进行中(作业):
    '运行中或停止中'
    状况=作业['status'] if 'status' in 作业 else None
    return 状况=='running' or 状况=='stopping'

def 是否可观测(作业):
    '进行中或已留输出'
    if 是否进行中(作业):
        return True
    输出=作业['output'] if 'output' in 作业 else {}
    总量=输出['total'] if isinstance(输出,dict) and 'total' in 输出 else 0
    return 总量>0

def 作业细节(作业):
    '进行中用 progress，结束后用 detail'
    if 'progress' in 作业 and 作业['progress'] is not None:
        return 作业['progress']
    return 作业['detail'] if 'detail' in 作业 else None

def 点状态(状况):
    '状况点语义'
    if 状况=='running':
        return 'ongoing'
    if 状况=='stopping' or 状况=='killed':
        return 'warning'
    if 状况=='completed':
        return 'done'
    if 状况=='failed':
        return 'error'
    raise 作业列表错误(去掉敏感('unhandled job status: '+repr(状况)))

def 状况文案(状况,翻译):
    '状况标签'
    if 状况=='running':
        return 翻译('status.running')
    if 状况=='stopping':
        return 翻译('status.stopping')
    if 状况=='completed':
        return 翻译('status.completed')
    if 状况=='killed':
        return 翻译('status.killed')
    if 状况=='failed':
        return 翻译('status.failed')
    raise 作业列表错误(去掉敏感('unhandled job status: '+repr(状况)))

def 格式化时长(经过毫秒,翻译):
    '最多相邻两档；最宽到小时'
    总秒=max(0,经过毫秒//1000)
    秒=总秒%60
    分=(总秒//60)%60
    时=总秒//3600
    if 时>0:
        return 翻译('duration.hours',{'hours':时,'minutes':分})
    if 分>0:
        return 翻译('duration.minutes',{'minutes':分,'seconds':秒})
    return 翻译('duration.seconds',{'seconds':秒})

def 终端文案(翻译):
    '内嵌终端面板文案'
    def 信号(值):
        '信号文案'
        return 翻译('terminal.signal',{'signal':值})
    def 退出码(码):
        '退出码文案'
        return 翻译('terminal.exitCode',{'code':码})
    def 展开无障碍(隐藏):
        '展开无障碍'
        return 翻译('terminal.expandAria',{'n':隐藏})
    def 展开(隐藏):
        '展开文案'
        return 翻译('terminal.expand',{'n':隐藏})
    return {
        'signal':信号,
        'exitCode':退出码,
        'noExitCode':翻译('terminal.noExitCode'),
        'running':翻译('terminal.running'),
        'failed':翻译('terminal.failed'),
        'done':翻译('terminal.done'),
        'copy':翻译('terminal.copy'),
        'copied':翻译('terminal.copied'),
        'noOutput':翻译('terminal.noOutput'),
        'collapseAria':翻译('terminal.collapseAria'),
        'collapse':翻译('terminal.collapse'),
        'expandAria':展开无障碍,
        'expand':展开,
    }

def 排序作业(作业表):
    '进行中按开始升序，已结束按完结降序'
    def 键(作业):
        '进行中在前'
        进行=是否进行中(作业)
        开始=作业['startedAt'] if 'startedAt' in 作业 else 0
        完结=作业['finishedAt'] if 'finishedAt' in 作业 and 作业['finishedAt'] is not None else 开始
        if 进行:
            return (0,开始,开始)
        return (1,-完结,开始)
    return sorted(作业表,key=键)

def 键齐(属性):
    '名册钩子、文案、会话和监视都在才画'
    if not isinstance(属性,dict):
        return False
    for 键 in ('useJobs','t','sessionId','watchRows'):
        if 键 not in 属性:
            return False
    return True

def 引号(文本):
    '属性值里不留引号'
    if not isinstance(文本,str):
        return ''
    return 文本.replace('"','')

class 任务列表动作:
    '会话头部后台作业列表和输出。不持有作业登记表。'
    def __init__(自身,属性):
        '记下槽注入面。键齐了才在构造末尾画。'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.打开=False
        自身.展开键=None
        自身.现在=当前毫秒()
        自身.已结束展开=None
        自身.已清空=set()
        自身.停止阶段=None
        自身._已订=False
        自身._绘制中=False
        自身._待重画=False
        if 键齐(自身.属性):
            自身.渲染()

    def 更新(自身,属性):
        '刷新合成 props'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 当前行(自身):
        '本会话作业行'
        用作业=自身.属性['useJobs']
        会话标识=自身.属性['sessionId']
        def 选行(快照):
            'rows[sessionId]'
            if not isinstance(快照,dict):
                return 空作业
            表=快照['rows'] if 'rows' in 快照 else {}
            if not isinstance(表,dict) or 会话标识 not in 表:
                return 空作业
            return 表[会话标识]
        行=用作业(选行)
        if 行 is None:
            return 空作业
        return 行

    def 观测视图(自身):
        '观测快照'
        用作业=自身.属性['useJobs']
        def 选观测(快照):
            'observed'
            if not isinstance(快照,dict):
                return {}
            return 快照['observed'] if 'observed' in 快照 else {}
        return 用作业(选观测)

    def 确保监视(自身):
        '挂载后保持本会话名册流，只订一次'
        if getattr(自身,'_已监视',False):
            return
        自身._已监视=True
        监视=自身.属性['watchRows'] if 'watchRows' in 自身.属性 else None
        if not callable(监视):
            return
        停止=监视(自身.属性['sessionId'])
        if callable(停止):
            自身._停监视=停止

    def 确保订阅(自身):
        '名册变化时重画已挂上的列表'
        if 自身._已订:
            return
        用=自身.属性['useJobs'] if 'useJobs' in 自身.属性 else None
        订=getattr(用,'_subscribe',None)
        if not callable(订):
            return
        自身._已订=True
        def 变(*_参数):
            '快照变了就重画'
            if 自身._绘制中:
                自身._待重画=True
                return
            if getattr(自身,'_壳',None) is not None:
                自身.重画()
        订(变)

    def 同步观测(自身,行表):
        '展开可观测行时订输出，收起或换行时退订'
        目标=None
        if 自身.打开 and 自身.展开键 is not None:
            for 作业 in 行表:
                if str(作业['id'])==自身.展开键 and 是否可观测(作业):
                    目标=作业['id']
                    break
        if getattr(自身,'_观测键',None)==目标:
            return
        停止=getattr(自身,'_停观测',None)
        if callable(停止):
            停止()
        自身._停观测=None
        自身._观测键=目标
        if 目标 is None or 'observe' not in 自身.属性:
            return
        结果=自身.属性['observe'](自身.属性['sessionId'],目标)
        if callable(结果):
            自身._停观测=结果

    def 确保时钟(自身,需要):
        '列表打开且有进行中作业时每秒重画时长'
        钟=getattr(自身,'_钟',None)
        槽=getattr(自身,'_计时槽',None)
        if 需要 and 钟 is None and 槽 is not None:
            def 滴答():
                '采样时钟并重画打开的列表'
                自身.现在=当前毫秒()
                if 自身.打开:
                    自身.重画()
            with 槽:
                自身._钟=界面.timer(1.0,滴答)
        if not 需要 and 钟 is not None:
            钟.active=False
            自身._钟=None

    def 排停止计时(自身,毫秒):
        '武装或失败提示到时后收回停止按钮'
        旧=getattr(自身,'_停计',None)
        if 旧 is not None:
            旧.active=False
        槽=getattr(自身,'_计时槽',None)
        if 槽 is None:
            return
        def 到():
            '进行中的停止请求留给作业状态自己收掉'
            阶段=自身.停止阶段
            if 阶段 is not None and 阶段['state']!='pending':
                自身.停止阶段=None
                自身.重画()
        with 槽:
            自身._停计=界面.timer(毫秒/1000,到,once=True)

    def 画作业(自身,作业,翻译,观测):
        '标签、种类、细节、时长；可观测时展开终端'
        键=str(作业['id'])
        进行=是否进行中(作业)
        可观测=是否可观测(作业)
        细节=作业细节(作业)
        状况=状况文案(作业['status'],翻译)
        标签=作业['label'] if 'label' in 作业 and 作业['label'] is not None else 状况
        种类=作业['kind'] if 'kind' in 作业 and 作业['kind'] is not None else ''
        结束于=作业['finishedAt'] if 'finishedAt' in 作业 and 作业['finishedAt'] is not None else 作业['startedAt']
        if 进行:
            经过=自身.现在-作业['startedAt']
            时长键='duration.title.live'
        else:
            经过=结束于-作业['startedAt']
            时长键='duration.title.done'
        时长=格式化时长(经过,翻译)
        展开=自身.展开键==键
        def 切换(当前=键):
            '展开或收起这一行'
            自身.切换展开(当前)
            自身.重画()
        with 界面.element('div').classes('item'):
            行类='rowLine rowLineLive' if 进行 else 'rowLine'
            with 界面.element('div').classes(行类):
                if 可观测:
                    行类名='row' if 进行 else 'row rowSettled'
                    无障碍键='row.collapseAria' if 展开 else 'row.expandAria'
                    行=界面.element('button').classes(行类名)
                    行.props(
                        'type=button aria-expanded='
                        +('true' if 展开 else 'false')
                        +' aria-label="'+引号(翻译(无障碍键,{'label':标签}))+'"'
                    )
                    行.on('click',切换)
                else:
                    行=界面.element('span').classes('row rowSettled rowStatic')
                with 行:
                    状态点({'state':点状态(作业['status']),'size':8,'className':'rowDot'}).渲染()
                    if 进行:
                        with 界面.element('span').classes('main'):
                            with 界面.element('span').classes('primary'):
                                界面.label(str(标签)).classes('label')
                            次要=界面.element('span').classes('secondary')
                            次要标题=str(细节) if 细节 is not None else 状况
                            次要.tooltip(次要标题)
                            with 次要:
                                if 种类!='':
                                    界面.label(str(种类)).classes('kind')
                                if 细节 is not None:
                                    界面.label(str(细节)).classes('status')
                                时长标=界面.label(时长).classes('duration')
                                时长标.tooltip(翻译(时长键,{'duration':时长}))
                        箭头类='chevron chevronOpen' if 展开 else 'chevron'
                        with 界面.element('span').classes('chevronBox'):
                            界面.icon('expand_more',size='12px').classes(箭头类)
                    else:
                        if 种类!='':
                            界面.label(str(种类)).classes('kind')
                        界面.label(str(标签)).classes('label')
                        次要=状况 if 细节 is None else str(细节)
                        界面.label(次要).classes('status')
                        时长标=界面.label(时长).classes('duration')
                        时长标.tooltip(翻译(时长键,{'duration':时长}))
                        if 可观测:
                            箭头类='chevron chevronOpen' if 展开 else 'chevron'
                            with 界面.element('span').classes('chevronBox'):
                                界面.icon('expand_more',size='12px').classes(箭头类)
                if 作业['status']=='running':
                    阶段=自身.停止阶段
                    if 阶段 is not None and 阶段['key']==键:
                        停止态=阶段['state']
                    else:
                        停止态='idle'
                    if 停止态=='armed':
                        停止类='stop stopArmed'
                        停止标题=翻译('kill.confirm')
                    elif 停止态=='failed':
                        停止类='stop stopFailed'
                        停止标题=翻译('kill.failed')
                    else:
                        停止类='stop'
                        停止标题=翻译('kill.stop',{'label':标签})
                    def 停止(当前=作业):
                        '两击停止'
                        自身.按停止(当前)
                    停钮=界面.element('button').classes(停止类)
                    停钮.props('type=button aria-label="'+引号(停止标题)+'" title="'+引号(停止标题)+'"')
                    停钮.on('click',停止)
                    with 停钮:
                        界面.icon('stop',size='10px')
                        if 停止态=='armed':
                            界面.label(翻译('kill.confirmAction')).classes('stopLabel')
                    if 停止态=='pending':
                        停钮.props('disabled')
            if 展开 and 可观测:
                视图=观测[键] if isinstance(观测,dict) and 键 in 观测 else None
                if isinstance(视图,dict):
                    with 界面.element('div').classes('panel'):
                        if 视图.get('gapBefore'):
                            界面.label(翻译('output.gap')).classes('notice')
                        if 'error' in 视图 and 视图['error'] is not None:
                            错误文=去掉敏感(视图['error'])
                            界面.label(翻译('output.error',{'error':错误文})).classes('notice noticeError')
                        终端块({
                            'command':标签,
                            'output':视图['text'] if 'text' in 视图 and 视图['text'] is not None else '',
                            'running':进行,
                            'copyText':标签,
                            'maxLines':10**9,
                            'labels':终端文案(翻译),
                        }).渲染()

    def 重画(自身):
        '按当前名册重画触发器。没有可见作业时留空。'
        壳=getattr(自身,'_壳',None)
        if 壳 is None:
            return
        翻译=自身.属性['t']
        作业表=自身.当前行()
        行表=排序作业(作业表)
        进行行=[作业 for 作业 in 行表 if 是否进行中(作业)]
        已结束行=[作业 for 作业 in 行表 if not 是否进行中(作业) and str(作业['id']) not in 自身.已清空]
        if 自身.已结束展开 is None:
            已结束展开=len(进行行)==0
        else:
            已结束展开=自身.已结束展开
        可见数=len(进行行)+len(已结束行)
        自身.同步观测(行表)
        自身.确保时钟(自身.打开 and len(进行行)>0)
        壳.clear()
        if 可见数==0:
            自身.打开=False
            壳.style('display:none')
            return
        壳.style('display:inline-flex')
        if len(进行行)>0:
            if len(进行行)==1:
                计数键='count.live.one'
            else:
                计数键='count.live.other'
            计数数目=len(进行行)
        elif 可见数==1:
            计数键='count.idle.one'
            计数数目=可见数
        else:
            计数键='count.idle.other'
            计数数目=可见数
        计数=翻译(计数键,{'count':计数数目})
        观测=自身.观测视图()
        def 切换已结束():
            '展开或收起已结束'
            自身.切换已结束(not 已结束展开)
            自身.重画()
        def 清空():
            '客户端隐藏已结束行'
            自身.清空已结束()
        with 壳:
            def 开关列表():
                '打开时先采样时钟'
                自身.现在=当前毫秒()
                自身.打开=not 自身.打开
                自身.重画()
            触发=界面.element('button').classes('trigger')
            触发.props(
                'type=button aria-expanded='
                +('true' if 自身.打开 else 'false')
                +' aria-label="'+引号(计数)+'"'
            )
            触发.on('click',开关列表)
            def 按键(事件):
                'Escape 收起列表'
                键=getattr(事件,'key',None)
                参数=getattr(事件,'args',None)
                if 键 is None and isinstance(参数,dict):
                    键=参数.get('key')
                if 键=='Escape' and 自身.打开:
                    自身.打开=False
                    自身.重画()
            触发.on('keydown',按键)
            with 触发:
                if len(进行行)>0:
                    状态点({'state':'ongoing','size':8,'className':'triggerDot'}).渲染()
                界面.label(计数).classes('count')
                箭头类='triggerOpen' if 自身.打开 else ''
                界面.icon('expand_more',size='12px').classes(箭头类)
            if 自身.打开:
                菜单=界面.element('div').classes('menu')
                菜单.props('aria-label="'+引号(翻译('list.aria'))+'"')
                with 菜单:
                    if len(进行行)>0:
                        界面.label(翻译('section.live')).classes('sectionHeader')
                        for 作业 in 进行行:
                            自身.画作业(作业,翻译,观测)
                    if len(已结束行)>0:
                        with 界面.element('div').classes('sectionHeader'):
                            节钮=界面.element('button').classes('sectionToggle')
                            节钮.props('type=button aria-expanded='+('true' if 已结束展开 else 'false'))
                            节钮.on('click',切换已结束)
                            with 节钮:
                                节箭头='sectionChevron sectionChevronOpen' if 已结束展开 else 'sectionChevron'
                                界面.icon('expand_more',size='12px').classes(节箭头)
                                界面.label(翻译('section.settledCount',{'count':len(已结束行)}))
                            清钮=界面.element('button').classes('sectionClear')
                            清钮.props('type=button')
                            清钮.on('click',清空)
                            with 清钮:
                                界面.label(翻译('section.clear'))
                        if 已结束展开:
                            for 作业 in 已结束行:
                                自身.画作业(作业,翻译,观测)

    def 渲染(自身):
        '触发器常在名册上。没有可见作业时内容为空，名册流仍然保持。'
        自身._绘制中=True
        try:
            自身.确保监视()
            自身.确保订阅()
            if getattr(自身,'_计时槽',None) is None:
                自身._计时槽=界面.row().style('display:none')
            if getattr(自身,'_壳',None) is None:
                自身._壳=界面.element('div').classes('任务列表 root')
            自身.重画()
        finally:
            自身._绘制中=False
        if 自身._待重画:
            自身._待重画=False
            自身.重画()

    def 切换展开(自身,键):
        '展开或收起一行'
        if 自身.展开键==键:
            自身.展开键=None
        else:
            自身.展开键=键

    def 切换已结束(自身,打开):
        '已结束分组折叠'
        自身.已结束展开=打开

    def 清空已结束(自身):
        '客户端隐藏已结束行。登记表里的记录仍在。'
        作业表=排序作业(自身.当前行())
        for 作业 in 作业表:
            if not 是否进行中(作业):
                自身.已清空.add(str(作业['id']))
        已结束键={str(作业['id']) for 作业 in 作业表 if not 是否进行中(作业)}
        if 自身.展开键 is not None and 自身.展开键 in 已结束键:
            自身.展开键=None
        自身.重画()

    def 按停止(自身,作业):
        '两击停止。失败只留文案键，不把异常原文画出来。'
        键=str(作业['id'])
        阶段=自身.停止阶段
        if 阶段 is None or 阶段['key']!=键 or 阶段['state']!='armed':
            自身.停止阶段={'key':键,'state':'armed'}
            自身.排停止计时(武装毫秒)
            自身.重画()
            return
        自身.停止阶段={'key':键,'state':'pending'}
        def 收下(成功):
            '未接纳才短暂显示失败'
            当前=自身.停止阶段
            if 当前 is not None and 当前['key']==键 and 成功 is not True:
                自身.停止阶段={'key':键,'state':'failed'}
                自身.排停止计时(失败毫秒)
            自身.重画()
        try:
            结果=自身.属性['killJob'](自身.属性['sessionId'],键)
        except Exception as 原因:
            页面失败文案(原因)
            收下(False)
            return
        if hasattr(结果,'then') and callable(结果.then):
            结果.then(lambda 值:收下(值 is True),lambda _错误:收下(False))
            自身.重画()
            return
        收下(结果 is True)

    def __call__(自身,属性=None):
        '对齐组件调用'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()
