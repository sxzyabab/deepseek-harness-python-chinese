'一条任务的规则、记录、删除确认和原会话'
from nicegui import ui as 界面
from ....基础设施.通用工具 import 当前毫秒
from ..异常 import 页面失败文案
from .任务菜单 import 任务菜单
from .日期选择 import 日期选择
from .时钟选择 import 时钟选择
from .目录反馈 import 目录反馈
from .投递历史 import 投递历史
from .会话链接 import 会话链接状态,会话标签
from .日程格式 import 下次运行片段,记录时区

__all__=['任务详情','重复选项']

重复选项=('once','everyMinutes','everyHours','daily','weekdays','weekly','cron')
工作日=(1,2,3,4,5)
标题上限=120

def _种到选项(记录):
    '存储种类对应重复菜单'
    种=记录['kind'] if isinstance(记录,dict) and 'kind' in 记录 else 'at'
    if 种=='every':
        秒=记录['everySeconds'] if 'everySeconds' in 记录 else 3600
        if isinstance(秒,(int,float)) and not isinstance(秒,bool) and 秒%3600==0:
            return 'everyHours'
        return 'everyMinutes'
    if 种=='weekly':
        日=记录['weekdays'] if 'weekdays' in 记录 else ()
        if list(日)==list(工作日):
            return 'weekdays'
        return 'weekly'
    if 种=='daily':
        return 'daily'
    if 种=='cron':
        return 'cron'
    return 'once'

def _种子(记录):
    '从记录抄出可编辑草稿'
    选项=_种到选项(记录)
    return {
        'choice':选项,
        'title':记录['title'] if 'title' in 记录 and isinstance(记录['title'],str) else '',
        'prompt':记录['prompt'] if 'prompt' in 记录 and isinstance(记录['prompt'],str) else '',
        'date':'',
        'time':记录['time'] if 'time' in 记录 and isinstance(记录['time'],str) else '09:00',
        'zone':记录['timeZone'] if 'timeZone' in 记录 and isinstance(记录['timeZone'],str) else '',
        'seconds':str(int(记录['everySeconds'])) if 'everySeconds' in 记录 and isinstance(记录['everySeconds'],(int,float)) and not isinstance(记录['everySeconds'],bool) else '3600',
        'expression':记录['expression'] if 'expression' in 记录 and isinstance(记录['expression'],str) else '',
        'weekdays':list(记录['weekdays']) if 'weekdays' in 记录 and isinstance(记录['weekdays'],list) else [1],
    }

class 任务详情:
    '父组件调用渲染。名称、指令、重复、保存和删除都画在这里'
    def __init__(自身,属性=None):
        '只记 props，等父组件渲染'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.页='rule'
        自身.草稿=None
        自身.菜单开=False
        自身.确认=False
        自身.保存中=False
        自身.失败=None
        自身.现在=当前毫秒()

    def 更新(自身,属性):
        '换任务时丢掉上一份草稿'
        新=属性 if isinstance(属性,dict) else {}
        旧=自身.属性.get('task') if isinstance(自身.属性,dict) else None
        新任务=新.get('task')
        旧键=(旧.get('sessionId'),旧.get('id')) if isinstance(旧,dict) else None
        新键=(新任务.get('sessionId'),新任务.get('id')) if isinstance(新任务,dict) else None
        自身.属性=新
        if 新键!=旧键:
            自身.草稿=None
            自身.页='rule'
            自身.确认=False
            自身.失败=None
            自身.保存中=False
            自身.菜单开=False

    def 渲染(自身):
        '壳和正文'
        if getattr(自身,'_壳',None) is None:
            自身._壳=界面.column().classes('schedule-detail')
        自身.重画()

    def _草稿(自身,任务):
        '第一次按记录播种'
        if 自身.草稿 is None:
            自身.草稿=_种子(任务)
        return 自身.草稿

    def _脏(自身,任务):
        '和记录播种值不同即未保存'
        return 自身._草稿(任务)!=_种子(任务)

    def 重画(自身):
        '规则页或记录页'
        壳=自身._壳
        壳.clear()
        属性=自身.属性
        任务=属性['task'] if 'task' in 属性 and isinstance(属性['task'],dict) else None
        if 任务 is None:
            return
        翻译=属性['t'] if 't' in 属性 and callable(属性['t']) else (lambda 键,_参数=None:键)
        草稿=自身._草稿(任务)
        只读=任务.get('status')=='inactive'
        片段=下次运行片段(任务['scheduledAt'] if 'scheduledAt' in 任务 else '',翻译('time.locale'),自身.现在,翻译)
        def 切页(名):
            '规则或记录'
            自身.页=名
            自身.重画()
        def 改(字段):
            '文本字段写进草稿'
            def 收到(事件):
                '写入'
                自身.草稿[字段]=事件.value if hasattr(事件,'value') else ''
                自身._刷保存条()
            return 收到
        with 壳:
            界面.label(翻译('detail.label'))
            with 界面.row():
                界面.button(翻译('detail.rule'), on_click=lambda:切页('rule')).props('flat'+(' color=primary' if 自身.页=='rule' else ''))
                界面.button(翻译('detail.records'), on_click=lambda:切页('records')).props('flat'+(' color=primary' if 自身.页=='records' else ''))
                自身._画会话(任务,翻译)
                def 开关菜单():
                    '更多'
                    自身.菜单开=not 自身.菜单开
                    自身.重画()
                界面.button(on_click=开关菜单).props('icon=more_horiz flat round aria-label="'+翻译('detail.more')+'"')
                任务菜单({
                    'open':自身.菜单开,
                    'items':[{'id':'delete','label':翻译('delete.pending' if 自身._在删(任务) else 'delete.action'),'disabled':自身._在删(任务)}],
                    'onSelect':lambda _标识:自身._要求删除(),
                    'onClose':开关菜单,
                }).渲染()
                if 'onClose' in 属性 and callable(属性['onClose']):
                    界面.button(on_click=属性['onClose']).props('icon=close flat round aria-label="'+翻译('detail.close')+'"')
            目录反馈({
                'status':属性['status'] if 'status' in 属性 else 'ready',
                'populated':True,
                'onRetry':属性['onRetry'] if 'onRetry' in 属性 else (lambda *_参数:None),
                't':翻译,
            }).渲染()
            if 自身.页=='rule':
                if 任务.get('status')=='active':
                    界面.label(翻译('detail.nextRun')+' '+片段['absolute']+' '+片段['relative'])
                else:
                    界面.label(翻译('status.inactive'))
                if 只读:
                    界面.label(草稿['title'])
                    界面.label(草稿['prompt'])
                else:
                    界面.input(翻译('detail.name'), value=草稿['title'], on_change=改('title'))
                    界面.textarea(翻译('detail.instruction'), value=草稿['prompt'], on_change=改('prompt'))
                    界面.label(翻译('rule.repeat'))
                    界面.select({键:翻译('rule.'+键) for 键 in 重复选项}, value=草稿['choice'], on_change=自身._改重复)
                    自身._画规则字段(草稿,翻译,只读)
                if 自身.失败 is not None:
                    界面.label(翻译(自身.失败))
                自身._保存条=界面.row()
                自身._刷保存条()
            else:
                投递历史({
                    'id':任务['id'] if 'id' in 任务 else None,
                    'sessionId':任务['sessionId'] if 'sessionId' in 任务 else None,
                    'latestMessageId':任务['lastDelivery']['messageId'] if isinstance(任务.get('lastDelivery'),dict) and 'messageId' in 任务['lastDelivery'] else None,
                    'timeZone':记录时区(任务),
                    'loadHistory':属性['loadHistory'] if 'loadHistory' in 属性 else None,
                    't':翻译,
                }).渲染()
            if 自身.确认:
                with 界面.card().classes('schedule-confirm'):
                    界面.label(翻译('delete.title'))
                    界面.label(翻译('delete.description'))
                    界面.label(草稿['title'])
                    界面.button(翻译('delete.cancel'), on_click=自身._取消删除).props('outline')
                    界面.button(翻译('delete.confirm'), on_click=自身._确认删除)

    def _画会话(自身,任务,翻译):
        '原会话链接。就在这个会话里打开时不画'
        所在=自身.属性['withinSession'] if 'withinSession' in 自身.属性 else None
        if 所在==任务.get('sessionId'):
            return
        会话=自身._快照('useSessions')
        工作区=自身._快照('useWorkspaces')
        态=会话链接状态(任务.get('sessionId'),会话 if isinstance(会话,dict) else {},工作区 if isinstance(工作区,dict) else {})
        标签=会话标签(任务.get('sessionId'),会话 if isinstance(会话,dict) else {})
        文=翻译('detail.openSessionTitle',{'title':标签['text']}) if 标签['titled'] else 翻译('detail.openSession')
        def 打开():
            '打开原会话'
            回调=自身.属性['onOpenSession'] if 'onOpenSession' in 自身.属性 else None
            if callable(回调):
                回调(任务['sessionId'])
        钮=界面.button(翻译('detail.session')+' '+标签['text'], on_click=打开).props('flat aria-label="'+文+'"')
        if 态!='available':
            钮.disable()
        说明={'loading':'detail.sessionLoading','archived':'detail.sessionArchived','unavailable':'detail.sessionUnavailable'}
        if 态 in 说明:
            界面.label(翻译(说明[态]))

    def _快照(自身,钩名):
        '钩子缺席则空字典'
        用=自身.属性[钩名] if 钩名 in 自身.属性 else None
        if not callable(用):
            return {}
        try:
            值=用(lambda 当前:当前)
        except Exception:
            return {}
        return 值 if isinstance(值,dict) else {}

    def _画规则字段(自身,草稿,翻译,只读):
        '按重复选项画日期、时钟、间隔、星期或 cron'
        选项=草稿['choice']
        if 选项=='once':
            日期选择({'value':草稿['date'],'t':翻译,'onPick':lambda 值:自身._写('date',值)}).渲染()
            时钟选择({'value':草稿['time'],'t':翻译,'seconds':True,'onPick':lambda 值:自身._写('time',值)}).渲染()
        elif 选项=='everyMinutes' or 选项=='everyHours':
            界面.number(翻译('timing.interval'), value=草稿['seconds'], on_change=lambda 事件:自身._写('seconds',事件.value))
        elif 选项=='daily' or 选项=='weekdays' or 选项=='weekly':
            时钟选择({'value':草稿['time'],'t':翻译,'seconds':False,'onPick':lambda 值:自身._写('time',值)}).渲染()
            界面.input(翻译('timing.zone'), value=草稿['zone'], on_change=lambda 事件:自身._写('zone',事件.value))
            if 选项=='weekly' or 选项=='weekdays':
                界面.label(翻译('rule.weekday'))
                for 日 in range(1,8):
                    开=日 in 草稿['weekdays']
                    def 切换(当前=日):
                        '最后一个星期保持选中'
                        表=list(草稿['weekdays'])
                        if 当前 in 表:
                            if len(表)==1:
                                return
                            表.remove(当前)
                        else:
                            表.append(当前)
                            表.sort()
                        自身._写('weekdays',表)
                    界面.button(str(日), on_click=切换).props('flat'+(' color=primary' if 开 else ''))
        elif 选项=='cron':
            界面.input(翻译('rule.cronLabel'), value=草稿['expression'], on_change=lambda 事件:自身._写('expression',事件.value))
            界面.input(翻译('timing.zone'), value=草稿['zone'], on_change=lambda 事件:自身._写('zone',事件.value))
        if 只读:
            return

    def _写(自身,字段,值):
        '写入草稿并刷新保存条'
        if 自身.草稿 is None:
            return
        自身.草稿[字段]=值
        自身._刷保存条()

    def _改重复(自身,事件):
        '换重复选项'
        if 自身.草稿 is None:
            return
        自身.草稿['choice']=事件.value
        if 事件.value=='weekdays':
            自身.草稿['weekdays']=list(工作日)
        自身.重画()

    def _刷保存条(自身):
        '未保存时才出现取消和保存'
        条=getattr(自身,'_保存条',None)
        if 条 is None:
            return
        条.clear()
        任务=自身.属性.get('task')
        if not isinstance(任务,dict) or 任务.get('status')=='inactive':
            return
        if 自身._脏(任务) is False and 自身.保存中 is False:
            return
        翻译=自身.属性['t'] if 't' in 自身.属性 and callable(自身.属性['t']) else (lambda 键,_参数=None:键)
        with 条:
            界面.label(翻译('rule.unsaved'))
            界面.button(翻译('rule.cancel'), on_click=自身._取消).props('flat')
            界面.button(翻译('rule.saving' if 自身.保存中 else 'rule.save'), on_click=自身._保存)

    def _取消(自身):
        '草稿回到记录'
        自身.草稿=None
        自身.失败=None
        自身.重画()

    def _校验(自身,草稿):
        '名称、指令、间隔'
        if not isinstance(草稿['title'],str) or 草稿['title'].strip()=='' or len(草稿['title'])>标题上限:
            return 'rule.invalidTitle'
        if not isinstance(草稿['prompt'],str) or 草稿['prompt'].strip()=='':
            return 'rule.invalidPrompt'
        if 草稿['choice'] in ('everyMinutes','everyHours'):
            try:
                秒=int(float(草稿['seconds']))
            except (TypeError,ValueError):
                return 'timing.invalidInterval'
            if 秒<60:
                return 'timing.invalidInterval'
        if 草稿['choice']=='cron' and (not isinstance(草稿['expression'],str) or len(草稿['expression'].split())<5):
            return 'rule.cronInvalid'
        return None

    def _保存(自身):
        '把草稿交给 onUpdateTiming'
        任务=自身.属性.get('task')
        if not isinstance(任务,dict) or 自身.草稿 is None:
            return
        错=自身._校验(自身.草稿)
        if 错 is not None:
            自身.失败=错
            自身.重画()
            return
        回调=自身.属性['onUpdateTiming'] if 'onUpdateTiming' in 自身.属性 else None
        if not callable(回调):
            return
        自身.保存中=True
        自身.失败=None
        请求={'sessionId':任务.get('sessionId'),'id':任务.get('id'),'expected':任务,'title':自身.草稿['title'],'prompt':自身.草稿['prompt'],'choice':自身.草稿['choice'],'draft':dict(自身.草稿)}
        try:
            结果=回调(请求)
        except Exception:
            自身.保存中=False
            自身.失败='rule.error.unknown'
            自身.重画()
            return
        def 收(值):
            '失败留草稿'
            自身.保存中=False
            if isinstance(值,dict) and 'ok' in 值 and 值['ok'] is False:
                自身.失败='rule.error.unknown'
            elif isinstance(值,dict) and 'value' in 值 and isinstance(值['value'],dict) and 'code' in 值['value']:
                码=值['value']['code']
                自身.失败='rule.error.notFound' if 码=='schedule_not_found' else ('rule.error.conflict' if 码=='schedule_conflict' else 'rule.error.unknown')
            else:
                自身.草稿=None
                自身.失败=None
            自身.重画()
        if hasattr(结果,'then') and callable(结果.then):
            结果.then(收, lambda _错误:收({'ok':False}))
            return
        收(结果 if 结果 is not None else {'ok':True})

    def _在删(自身,任务):
        '目录正在删这条'
        正在=自身.属性['deleting'] if 'deleting' in 自身.属性 and isinstance(自身.属性['deleting'],list) else []
        return 任务.get('id') in 正在

    def _要求删除(自身):
        '先确认'
        自身.菜单开=False
        自身.确认=True
        自身.重画()

    def _取消删除(自身):
        '关掉确认'
        自身.确认=False
        自身.重画()

    def _确认删除(自身):
        '交给 onDelete，再请父组件离开'
        任务=自身.属性.get('task')
        自身.确认=False
        回调=自身.属性['onDelete'] if 'onDelete' in 自身.属性 else None
        if callable(回调) and isinstance(任务,dict):
            回调(任务['id'])
        离开=自身.属性['onDeleted'] if 'onDeleted' in 自身.属性 else None
        if callable(离开):
            离开()
        自身.重画()

    def __call__(自身,属性=None):
        '更新后渲染'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()
