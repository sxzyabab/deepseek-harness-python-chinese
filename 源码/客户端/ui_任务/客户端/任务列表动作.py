import time#纪元毫秒

__all__=['任务列表动作','样式表']

视口边距=12#弹出层与视口边距
武装毫秒=3_000#武装后等待确认
失败毫秒=4_000#失败提示时长
空作业=()#无作业时稳定空序列

样式表=''#由同名 module.css 承载

def 是否进行中(作业):
    """运行中或停止中。"""
    状况=作业['status'] if 'status' in 作业 else None
    return 状况=='running' or 状况=='stopping'

def 是否可观测(作业):
    """进行中或已留输出。"""
    if 是否进行中(作业):
        return True
    输出=作业['output'] if 'output' in 作业 else {}
    总量=输出['total'] if isinstance(输出,dict) and 'total' in 输出 else 0
    return 总量>0

def 作业细节(作业):
    """进行中用 progress，结束后用 detail。"""
    if 'progress' in 作业 and 作业['progress'] is not None:
        return 作业['progress']
    return 作业['detail'] if 'detail' in 作业 else None

def 点状态(状况):
    """状况点语义。"""
    if 状况=='running':
        return 'ongoing'
    if 状况=='stopping' or 状况=='killed':
        return 'warning'
    if 状况=='completed':
        return 'done'
    if 状况=='failed':
        return 'error'
    raise 作业列表错误('unhandled job status: '+repr(状况))

def 状况文案(状况,翻译):
    """状况标签。"""
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
    raise 作业列表错误('unhandled job status: '+repr(状况))

def 格式化时长(经过毫秒,翻译):
    """最多相邻两档；最宽到小时。"""
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
    """内嵌终端面板文案。"""
    def 信号(值):
        """信号文案。"""
        return 翻译('terminal.signal',{'signal':值})
    def 退出码(码):
        """退出码文案。"""
        return 翻译('terminal.exitCode',{'code':码})
    def 展开无障碍(隐藏):
        """展开无障碍。"""
        return 翻译('terminal.expandAria',{'n':隐藏})
    def 展开(隐藏):
        """展开文案。"""
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
    """进行中按开始升序，已结束按完结降序。"""
    def 键(作业):
        """进行中在前。"""
        进行=是否进行中(作业)
        开始=作业['startedAt'] if 'startedAt' in 作业 else 0
        完结=作业['finishedAt'] if 'finishedAt' in 作业 and 作业['finishedAt'] is not None else 开始
        return (0 if 进行 else 1,开始 if 进行 else -完结,开始)
    return sorted(作业表,key=键)

class 作业列表错误(Exception):
    """作业列表呈现失败。"""

class 任务列表动作:
    """会话头部后台作业列表。"""
    def __init__(自身,属性):
        """记下槽注入面。"""
        自身.属性=属性
        自身.打开=False
        自身.展开键=None
        自身.现在=int(time.time()*1000)
        自身.已结束展开=None
        自身.已清空=set()
        自身.停止阶段=None

    def 更新(自身,属性):
        """刷新合成 props。"""
        自身.属性=属性

    def 当前行(自身):
        """本会话作业行。"""
        用作业=自身.属性['useJobs']
        会话标识=自身.属性['sessionId']
        def 选行(快照):
            """rows[sessionId]。"""
            表=快照['rows'] if 'rows' in 快照 else {}
            return 表[会话标识] if 会话标识 in 表 else 空作业
        行=用作业(选行)
        return 行 if 行 is not None else 空作业

    def 观测视图(自身):
        """观测快照。"""
        用作业=自身.属性['useJobs']
        def 选观测(快照):
            """observed。"""
            return 快照['observed'] if 'observed' in 快照 else {}
        return 用作业(选观测)

    def 渲染(自身):
        """与上游 JSX 同构。"""
        翻译=自身.属性['t']
        会话标识=自身.属性['sessionId']
        作业表=自身.当前行()
        行表=排序作业(作业表)
        进行行=[作业 for 作业 in 行表 if 是否进行中(作业)]
        已结束行=[作业 for 作业 in 行表 if not 是否进行中(作业) and str(作业['id']) not in 自身.已清空]
        已结束展开=自身.已结束展开 if 自身.已结束展开 is not None else len(进行行)==0
        可见数=len(进行行)+len(已结束行)
        if 可见数==0:
            return None
        计数键='count.live.one' if len(进行行)==1 else 'count.live.other' if len(进行行)>0 else ('count.idle.one' if 可见数==1 else 'count.idle.other')
        计数=翻译(计数键,{'count':len(进行行) if len(进行行)>0 else 可见数})
        观测=自身.观测视图()
        def 项(作业):
            """一行。"""
            键=str(作业['id'])
            可观测=是否可观测(作业)
            视图=观测[键] if 可观测 and 键 in 观测 else None
            阶段=自身.停止阶段
            停止=None
            if 作业['status']=='running':
                停止={'state':阶段['state'] if 阶段 is not None and 阶段['key']==键 else 'idle','onPress':lambda 当前=作业:自身.按停止(当前)}
            return {
                'type':'job-item',
                'key':键,
                'job':作业,
                'view':视图,
                'expanded':自身.展开键==键,
                'now':自身.现在,
                'onToggle':lambda 当前=键:自身.切换展开(当前),
                'kill':停止,
                'live':是否进行中(作业),
                'statusLabel':状况文案(作业['status'],翻译),
                'detail':作业细节(作业),
                'dot':点状态(作业['status']),
                'duration':格式化时长((自身.现在-作业['startedAt']) if 是否进行中(作业) else ((作业['finishedAt'] if 'finishedAt' in 作业 and 作业['finishedAt'] is not None else 作业['startedAt'])-作业['startedAt']),翻译),
                'labels':终端文案(翻译),
            }
        return {
            'type':'job-list-action',
            'open':自身.打开,
            'countLabel':计数,
            'liveCount':len(进行行),
            'settledExpanded':已结束展开,
            'listAria':翻译('list.aria'),
            'sectionLive':翻译('section.live'),
            'sectionSettled':翻译('section.settledCount',{'count':len(已结束行)}),
            'sectionClear':翻译('section.clear'),
            'liveRows':[项(作业) for 作业 in 进行行],
            'settledRows':[项(作业) for 作业 in 已结束行] if 已结束展开 else [],
            'onToggleOpen':自身.切换打开,
            'onToggleSettled':lambda:自身.切换已结束(not 已结束展开),
            'onClearSettled':自身.清空已结束,
            'watch':lambda:自身.属性['watchRows'](会话标识),
            'observe':自身.属性['observe'],
            'sessionId':会话标识,
            'menuShift':0,
            'viewportMargin':视口边距,
            'armMs':武装毫秒,
            'failedMs':失败毫秒,
        }

    def 切换打开(自身):
        """开关弹出层。"""
        自身.现在=int(time.time()*1000)
        自身.打开=not 自身.打开

    def 切换展开(自身,键):
        """展开或收起一行。"""
        自身.展开键=None if 自身.展开键==键 else 键

    def 切换已结束(自身,打开):
        """已结束分组折叠。"""
        自身.已结束展开=打开

    def 清空已结束(自身):
        """客户端隐藏已结束行。"""
        作业表=排序作业(自身.当前行())
        for 作业 in 作业表:
            if not 是否进行中(作业):
                自身.已清空.add(str(作业['id']))
        if 自身.展开键 is not None:
            自身.展开键=None

    def 按停止(自身,作业):
        """两击停止。"""
        键=str(作业['id'])
        阶段=自身.停止阶段
        if 阶段 is None or 阶段['key']!=键 or 阶段['state']!='armed':
            自身.停止阶段={'key':键,'state':'armed'}
            return
        自身.停止阶段={'key':键,'state':'pending'}
        成功=自身.属性['killJob'](自身.属性['sessionId'],键)
        当前=自身.停止阶段
        if 当前 is not None and 当前['key']==键 and not 成功:
            自身.停止阶段={'key':键,'state':'failed'}

    def __call__(自身,属性=None):
        """对齐组件调用。"""
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()
