'跨会话的任务列表和详情'
from nicegui import ui as 界面
from ....基础设施.通用工具 import 当前毫秒
from ..异常 import 页面失败文案
from .日历图标 import 日历图标
from .目录反馈 import 目录反馈
from .任务详情 import 任务详情
from .日程格式 import 格式化日程频率,下次运行片段,任务名

__all__=['任务管理页']

过滤项=('all','active','inactive')

class 任务管理页:
    '槽位只调用构造。搜索、状态过滤、行和详情'
    def __init__(自身,属性=None):
        '记下搜索和选中。槽位只调用构造，键齐了就画。'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.搜索=''
        自身.过滤='all'
        自身.选中=None
        自身.现在=当前毫秒()
        if 'useCatalog' in 自身.属性:
            自身.渲染()

    def 更新(自身,属性):
        '刷新'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 确保订阅(自身):
        '目录变化时重画'
        if getattr(自身,'_已订',False):
            return
        用=自身.属性['useCatalog'] if 'useCatalog' in 自身.属性 else None
        订=getattr(用,'_subscribe',None)
        if not callable(订):
            return
        自身._已订=True
        def 变(*_参数):
            '重画列表'
            if getattr(自身,'_壳',None) is not None:
                自身.重画()
        订(变)

    def 渲染(自身):
        '列表壳和每秒相对时间'
        自身.确保订阅()
        if getattr(自身,'_壳',None) is None:
            自身._壳=界面.row().classes('schedule-manager').style('width:100%;align-items:flex-start;gap:16px')
            def 滴答():
                '刷新下次运行的距离'
                自身.现在=当前毫秒()
                if getattr(自身,'_壳',None) is not None:
                    自身.重画()
            界面.timer(30.0,滴答)
        自身.重画()

    def _目录(自身):
        '读目录快照'
        用=自身.属性['useCatalog'] if 'useCatalog' in 自身.属性 else None
        if not callable(用):
            return {'records':[],'status':'loading','deleting':[]}
        try:
            值=用(lambda 当前:当前)
        except Exception:
            return {'records':[],'status':'error','deleting':[]}
        return 值 if isinstance(值,dict) else {'records':[],'status':'error','deleting':[]}

    def 重画(自身):
        '过滤后的行，选中时在旁边放详情'
        壳=自身._壳
        壳.clear()
        属性=自身.属性
        翻译=属性['t'] if 't' in 属性 and callable(属性['t']) else (lambda 键,_参数=None:键)
        目录=自身._目录()
        记录=目录['records'] if 'records' in 目录 and isinstance(目录['records'],list) else []
        状态=目录['status'] if 'status' in 目录 else 'loading'
        查询=自身.搜索.strip().lower()
        行=[]
        for 项 in 记录:
            if not isinstance(项,dict):
                continue
            if 自身.过滤!='all' and 项.get('status')!=自身.过滤:
                continue
            if 查询!='':
                名=任务名(项).lower()
                提示=项['prompt'].lower() if isinstance(项.get('prompt'),str) else ''
                会话=str(项['sessionId']).lower() if 'sessionId' in 项 else ''
                if 查询 not in 名 and 查询 not in 提示 and 查询 not in 会话:
                    continue
            行.append(项)
        行.sort(key=lambda 项:项['scheduledAt'] if 'scheduledAt' in 项 and isinstance(项['scheduledAt'],str) else '')
        if 自身.选中 is not None and not any(项.get('id')==自身.选中 for 项 in 记录):
            自身.选中=None
        选中=next((项 for 项 in 记录 if 项.get('id')==自身.选中),None)
        def 改搜索(事件):
            '过滤标题、指令和会话'
            自身.搜索=事件.value if hasattr(事件,'value') and isinstance(事件.value,str) else ''
            自身.重画()
        def 新建():
            '到会话里创建，本页没有创建表单'
            回调=属性['onNewTask'] if 'onNewTask' in 属性 else None
            if callable(回调):
                回调()
        with 壳:
            with 界面.column().style('flex:1;min-width:280px'):
                with 界面.row().style('align-items:center;justify-content:space-between;width:100%'):
                    界面.label(翻译('title'))
                    界面.button(翻译('new.action'), on_click=新建).props('icon=add')
                with 界面.row():
                    for 项 in 过滤项:
                        文=翻译('statusFilter.all' if 项=='all' else 'status.'+项)
                        def 选过滤(当前=项):
                            '切换状态过滤'
                            自身.过滤=当前
                            自身.重画()
                        界面.button(文, on_click=选过滤).props('flat'+(' color=primary' if 自身.过滤==项 else ''))
                界面.input(翻译('search.label'), value=自身.搜索, placeholder=翻译('search.placeholder'), on_change=改搜索).props('icon=search')
                if 自身.搜索!='':
                    def 清空():
                        '清搜索'
                        自身.搜索=''
                        自身.重画()
                    界面.button(翻译('search.clear'), on_click=清空).props('flat')
                if 选中 is None:
                    目录反馈({'status':状态,'populated':len(行)>0,'onRetry':属性['onRetry'] if 'onRetry' in 属性 else (lambda *_参数:None),'t':翻译}).渲染()
                if 状态=='ready' and len(行)==0:
                    日历图标({'size':24}).渲染()
                    空键='list.emptyInactive' if 自身.过滤=='inactive' and 自身.搜索.strip()=='' else ('list.empty' if len(记录)==0 else 'list.noMatches')
                    界面.label(翻译(空键))
                    界面.button(翻译('empty.action'), on_click=新建).props('outline')
                for 项 in 行:
                    片段=下次运行片段(项['scheduledAt'] if 'scheduledAt' in 项 else '',翻译('time.locale'),自身.现在,翻译)
                    def 打开(当前=项['id'] if 'id' in 项 else None):
                        '选中这一条'
                        自身.选中=当前
                        自身.重画()
                    with 界面.column().style('width:100%'):
                        界面.button(任务名(项), on_click=打开).props('flat no-caps align=left')
                        界面.label(格式化日程频率(项,翻译))
                        if 项.get('status')=='active':
                            界面.label(翻译('list.nextPrefix')+片段['absolute']+' '+片段['relative'])
                        elif 项.get('status')=='inactive':
                            界面.label(翻译('status.inactive'))
            if 选中 is not None:
                任务详情({
                    **属性,
                    'task':选中,
                    'status':状态,
                    'deleting':目录['deleting'] if 'deleting' in 目录 and isinstance(目录['deleting'],list) else [],
                    'onDeleted':lambda:自身._关掉(),
                    'onClose':lambda:自身._关掉(),
                }).渲染()

    def _关掉(自身):
        '收起详情'
        自身.选中=None
        自身.重画()

    def __call__(自身,属性=None):
        '更新后渲染'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()
