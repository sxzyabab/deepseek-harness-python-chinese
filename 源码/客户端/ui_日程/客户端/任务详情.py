'一条任务的规则、运行记录、删除和原会话'
from ...模块.客户端.通告 import 取握手窗口
import json
import os
import re
from ...ui_对话.异常 import 注入模块样式文件,标样式模块
from ...ui_基础界面组件.按钮 import 处理按钮
from ...ui_基础界面组件.模态 import 处理模态
from ...ui_基础界面组件.胶囊 import 处理胶囊
from ...ui_基础界面组件.icons import (
    图标下chevron14,图标右chevron14,图标关闭16,图标省略16,图标垃圾桶16,
)
from ...ui_基础界面组件.引用图标 import 引用图标常规
from .管理文案 import 管理中文
from .文案 import 套用
from .目录反馈 import 目录反馈
from .日历图标 import 日历图标节点
from .日期选择 import 日期选择
from .时钟选择 import 时钟选择
from .投递历史 import 投递历史
from .任务菜单 import 任务菜单
from .任务时刻 import 时刻快照,草稿时区,时刻草稿,斜杠日期,秒精度,时刻错误,分区墙钟
from .相对时钟 import 现在毫秒,安装相对时钟
from .日程格式 import 下次运行两段,格式化日程频率,记录时区,时区标签,时区名,时区选项
from .任务定时 import 解析定时表达式,定时预览
from .会话链接 import 会话链接状态,会话标签
from .任务管理图标 import 画时钟

__all__=['任务详情','任务详情控制器']

样式模块='task-manager-page'
重复选项=('weekly','weekdays','daily','every-hour','every-minute','every-second','once','cron')
重复文案={
    'weekly':'rule.weekly','weekdays':'rule.weekdays','daily':'rule.daily',
    'every-hour':'rule.everyHours','every-minute':'rule.everyMinutes','every-second':'rule.everySeconds',
    'once':'rule.once','cron':'rule.cron',
}
间隔秒={'second':1,'minute':60,'hour':3600}
工作日=(1,2,3,4,5)
全部星期=(1,2,3,4,5,6,7)
星期文案={1:'frequency.weekday.1',2:'frequency.weekday.2',3:'frequency.weekday.3',4:'frequency.weekday.4',5:'frequency.weekday.5',6:'frequency.weekday.6',7:'frequency.weekday.7'}
标题上限=120
本地失败=('rule.invalidTitle','rule.invalidPrompt','timing.invalidInterval','rule.cronInvalid','timing.invalid')
规则覆盖={'timing.conflict':'rule.error.conflict','timing.notFound':'rule.error.notFound','timing.error':'rule.error.unknown'}
会话提示={'loading':'detail.sessionLoading','archived':'detail.sessionArchived','unavailable':'detail.sessionUnavailable'}

def 确保样式(文档):
    '详情用任务管理页样式'
    注入模块样式文件(文档,'日程任务管理页样式',os.path.join(os.path.dirname(__file__),'任务管理页.module.css'),样式模块)

def 标(节点):
    '挂上样式模块'
    if 节点 is not None:
        标样式模块(节点,样式模块)
    return 节点

def 是工作日规则(星期):
    '正好周一到周五'
    if len(星期)!=len(工作日):
        return False
    for 日 in 工作日:
        if 日 not in 星期:
            return False
    return True

def 规则种类(记录):
    '每周且正好工作日时显示周一至周五'
    if 记录.get('kind')=='weekly' and 是工作日规则(记录.get('weekdays') or []):
        return 'weekdays'
    表={'at':'once','after':'once','every':'every','daily':'daily','weekly':'weekly','cron':'cron'}
    return 表[记录['kind']]

def 规则值(记录):
    '从存下的记录种出可编辑值'
    return {
        'title':记录.get('title') or '',
        'prompt':记录.get('prompt') or '',
        'kind':规则种类(记录),
        'draft':时刻草稿(记录),
        'weekdays':list(记录.get('weekdays') or []),
    }

def 比较键(显示):
    '名字和指令按去掉空白后比较'
    草稿=显示['draft']
    return json.dumps([
        显示['title'].strip(),显示['prompt'].strip(),显示['kind'],
        草稿['date'],草稿['time'],草稿['timeZone'],草稿['seconds'],草稿['expression'],显示['weekdays'],
    ],ensure_ascii=False,separators=(',',':'))

def 草稿错误(显示):
    '本地先挡住不合规则的草稿'
    标题=显示['title'].strip()
    if len(标题)==0 or len(标题)>标题上限:
        return 'rule.invalidTitle'
    if len(显示['prompt'].strip())==0:
        return 'rule.invalidPrompt'
    if 显示['kind']=='every':
        秒=显示['draft']['seconds']
        if isinstance(秒,str) and 秒.isdigit() and int(秒)>=60:
            return None
        return 'timing.invalidInterval'
    if 显示['kind']=='cron':
        if 解析定时表达式(显示['draft']['expression']) is None:
            return 'rule.cronInvalid'
        return None
    日期=显示['draft']['date']
    if 显示['kind']=='once' and not re.match(r'^\d{4}-\d{2}-\d{2}$',日期 or ''):
        return 'timing.invalid'
    if not re.match(r'^\d{2}:\d{2}(:\d{2}(\.\d{1,3})?)?$',显示['draft']['time'] or ''):
        return 'timing.invalid'
    return None

def 补秒(时间):
    '只填了时分就补上秒'
    if isinstance(时间,str) and len(时间)==5:
        return 时间+':00'
    return 时间

def 规则变更(草稿,种类,星期):
    '按当前选择拼出要提交的时刻'
    if 种类=='once':
        return {'kind':'at','at':{'date':草稿['date'],'time':补秒(草稿['time']),'time_zone':草稿['timeZone'].strip()}}
    if 种类=='every':
        return {'kind':'every','every_seconds':int(草稿['seconds'])}
    if 种类=='daily':
        return {'kind':'daily','daily':{'time':补秒(草稿['time']),'time_zone':草稿['timeZone'].strip()}}
    if 种类=='cron':
        return {'kind':'cron','cron':{'expression':草稿['expression'].strip(),'time_zone':草稿['timeZone'].strip()}}
    日=list(工作日) if 种类=='weekdays' else list(星期)
    return {'kind':'weekly','weekly':{'time':补秒(草稿['time']),'time_zone':草稿['timeZone'].strip(),'weekdays':日}}

class 任务详情控制器:
    '列表页和任务页共用的草稿、页签和删除确认'
    def __init__(自身):
        '一开始没有选中的任务'
        自身.草稿=None
        自身.页签='rule'
        自身.确认标识=None
        自身.上次=None
        自身.元素标识='dsh-schedule-detail-0'
        自身.序号=0

    def 设确认(自身,标识):
        '打开或关掉删除确认'
        自身.确认标识=标识

    def 设页(自身,页签):
        '规则或运行记录'
        自身.页签=页签

    def 设草稿(自身,任务):
        '保存进行中时留下这一条，避免目录刷新把它卸掉'
        自身.草稿=任务

    def 快照(自身,注入,目录,任务标识):
        '换任务就清草稿。记录没了但草稿还在就继续显示'
        if 任务标识!=自身.上次:
            自身.草稿=None
            自身.页签='rule'
            自身.确认标识=None
            自身.上次=任务标识
            自身.序号=自身.序号+1
            自身.元素标识='dsh-schedule-detail-'+str(自身.序号)
        记录=None
        if 任务标识 is not None:
            for 项 in 目录.get('records') or []:
                if 项.get('id')==任务标识:
                    记录=项
                    break
        任务=记录
        if 任务 is None and isinstance(自身.草稿,dict) and 自身.草稿.get('id')==任务标识:
            任务=自身.草稿
        属性=dict(注入)
        属性['status']=目录.get('status')
        属性['deleting']=目录.get('deleting') or []
        属性['id']=自身.元素标识
        属性['onEditState']=自身.设草稿
        属性['tab']=自身.页签
        属性['onTabChange']=自身.设页
        属性['confirmId']=自身.确认标识
        属性['onConfirm']=自身.设确认
        return {'record':记录,'task':任务,'id':自身.元素标识,'confirmId':自身.确认标识,'setConfirmId':自身.设确认,'setTab':自身.设页,'props':属性}

class 任务详情:
    '规则页可改名字、内容和时刻。删除要先确认'
    def __init__(自身,属性):
        '种出第一份草稿'
        自身.属性=属性
        自身.根=None
        自身.编辑=None
        自身.身份=None
        自身.失败=None
        自身.待定=False
        自身.已确认删除=False
        自身.菜单开=False
        自身.重复开=False
        自身.时区开=False
        自身.时区查询=''
        自身.日期开=False
        自身.时间开=False
        自身.菜单=None
        自身.重复菜单=None
        自身.时区菜单=None
        自身.日期器=None
        自身.时钟器=None
        自身.历史=None
        自身.现在=现在毫秒()
        自身.停时钟=None
        自身.已订=False

    def 渲染(自身,属性=None):
        '目录或草稿变了就重画'
        if 属性 is not None:
            自身.属性=属性
        属性=自身.属性
        窗口=属性.get('window') or 取握手窗口()
        属性['window']=窗口
        文档=窗口.document
        确保样式(文档)
        任务=属性['task']
        身份=str(任务.get('sessionId'))+'\0'+str(任务.get('id'))
        if 自身.身份!=身份 or 自身.编辑 is None:
            值=规则值(任务)
            自身.编辑={'stored':值,'shown':值}
            自身.身份=身份
            自身.失败=None
            自身.待定=False
            自身.已确认删除=False
        if 自身.停时钟 is None:
            def 重画():
                '相对时间走动'
                自身.现在=现在毫秒()
                自身.渲染()
            自身.停时钟=安装相对时钟(重画)
        if not 自身.已订:
            for 名 in ('useSessions','useWorkspaces'):
                钩=属性.get(名)
                if callable(钩) and hasattr(钩,'_subscribe'):
                    def 变更(钩名=名):
                        '会话或工作区变了就重画链接'
                        自身.渲染()
                    钩._subscribe(变更)
            自身.已订=True
        显示=自身.编辑['shown']
        已存=自身.编辑['stored']
        脏=比较键(显示)!=比较键(已存)
        权威=属性.get('authoritative') is True
        已删=自身.已确认删除 and not 权威
        if 已删 and callable(属性.get('onDeleted')):
            属性['onDeleted']()
        忙=任务.get('id') in (属性.get('deleting') or []) or 属性.get('status')=='loading'
        if 自身.根 is None:
            自身.根=文档.createElement('div')
        根=自身.根
        while 根.firstChild is not None:
            根.removeChild(根.firstChild)
        侧=文档.createElement('aside')
        侧.className='detail'
        标(侧)
        侧.id=属性.get('id') or ''
        侧.tabIndex=-1
        侧.setAttribute('aria-label',管理中文['detail.label'])
        自身.画条(侧,文档,窗口,任务,显示,忙)
        滚=文档.createElement('div')
        滚.className='detailScroll'
        标(滚)
        反馈=目录反馈({'window':窗口,'status':属性.get('status'),'populated':True,'onRetry':属性.get('onRetry')})
        if 反馈 is not None:
            滚.appendChild(反馈)
        if 属性.get('tab')=='rule' and not 已删:
            自身.画规则(滚,文档,窗口,任务,显示,忙)
        if 属性.get('tab')=='records' and not 已删:
            自身.画记录(滚,窗口,任务)
        侧.appendChild(滚)
        if 脏 and not 已删 and 任务.get('status')!='inactive':
            脚=文档.createElement('footer')
            脚.className='saveFooter'
            标(脚)
            注=文档.createElement('span')
            注.className='saveNotice'
            标(注)
            注.textContent=管理中文['rule.unsaved']
            脚.appendChild(注)
            脚.appendChild(处理按钮(窗口,{'disabled':自身.待定,'children':管理中文['rule.cancel'],'onClick':自身.取消,'window':窗口}))
            存文=管理中文['rule.saving'] if 自身.待定 else 管理中文['rule.save']
            脚.appendChild(处理按钮(窗口,{'variant':'primary','disabled':自身.待定 or not 脏,'children':存文,'onClick':自身.保存,'window':窗口}))
            侧.appendChild(脚)
        根.appendChild(侧)
        确认=权威 and 属性.get('confirmId')==任务.get('id')
        模态=处理模态(窗口,{
            'open':确认,
            'title':管理中文['delete.title'],
            'description':管理中文['delete.description'],
            'closeLabel':管理中文['delete.close'],
            'onClose':自身.关确认,
            'className':'confirmDialog',
            'children':任务.get('title') or '',
            'footer':处理按钮(窗口,{'className':'deleteButton','disabled':忙,'children':管理中文['delete.confirm'],'onClick':自身.确认删除,'window':窗口}) if 确认 else None,
            'window':窗口,
        })
        if 模态 is not None:
            标(模态)
            根.appendChild(模态)
        if callable(属性.get('onEditState')):
            属性['onEditState'](任务 if 自身.待定 or 自身.失败 or 自身.已确认删除 else None)
        return 根

    def 画条(自身,侧,文档,窗口,任务,显示,忙):
        '页签、原会话、更多和关闭'
        条=文档.createElement('div')
        条.className='detailTabsBar'
        标(条)
        页签=文档.createElement('div')
        页签.className='detailTabs'
        标(页签)
        页签.setAttribute('role','tablist')
        页签.setAttribute('aria-label',管理中文['detail.tabs'])
        for 值,文案键 in (('rule','detail.rule'),('records','detail.records')):
            钮=文档.createElement('button')
            钮.type='button'
            钮.className='detailTab'
            标(钮)
            钮.setAttribute('role','tab')
            钮.setAttribute('data-detail-tab',值)
            钮.setAttribute('aria-selected','true' if 自身.属性.get('tab')==值 else 'false')
            钮.textContent=管理中文[文案键]
            def 点页(事件,值=值):
                '切换规则或记录'
                自身.属性['onTabChange'](值)
                自身.渲染()
            钮.addEventListener('click',点页)
            页签.appendChild(钮)
        条.appendChild(页签)
        动作=文档.createElement('div')
        动作.className='detailActions'
        标(动作)
        自身.画会话(动作,文档,窗口,任务)
        更多=处理按钮(窗口,{
            'size':'sm','className':'detailIconButton','window':窗口,
            'children':图标省略16({'window':窗口}),
        })
        标(更多)
        更多.setAttribute('aria-label',管理中文['detail.more'])
        更多.setAttribute('title',管理中文['detail.more'])
        def 点更多(事件):
            '打开删除菜单'
            自身.菜单开=not 自身.菜单开
            自身.渲染()
        更多.addEventListener('click',点更多)
        if 自身.菜单 is None:
            自身.菜单=任务菜单({'window':窗口})
        图标=图标垃圾桶16({'window':窗口})
        菜单根=自身.菜单.渲染({
            'window':窗口,
            'open':自身.菜单开,
            'anchor':更多,
            'align':'end',
            'portal':True,
            'onClose':自身.关菜单,
            'onSelect':自身.点删除,
            'items':[{
                'id':'delete',
                'label':管理中文['delete.pending'] if 忙 else 管理中文['delete.action'],
                'danger':True,
                'disabled':忙 or 自身.属性.get('authoritative') is not True,
                'icon':图标,
            }],
        })
        动作.appendChild(菜单根)
        if callable(自身.属性.get('onClose')):
            关=处理按钮(窗口,{'size':'sm','className':'detailIconButton','children':图标关闭16({'window':窗口}),'onClick':自身.属性['onClose'],'window':窗口})
            标(关)
            关.setAttribute('aria-label',管理中文['detail.close'])
            动作.appendChild(关)
        条.appendChild(动作)
        侧.appendChild(条)

    def 画会话(自身,动作,文档,窗口,任务):
        '不在这条会话里面才显示原会话'
        if 自身.属性.get('tab')!='rule':
            return
        if 自身.属性.get('withinSession')==任务.get('sessionId'):
            return
        def 取(快照):
            '原样'
            return 快照
        会话=自身.属性['useSessions'](取) if callable(自身.属性.get('useSessions')) else {}
        工作区=自身.属性['useWorkspaces'](取) if callable(自身.属性.get('useWorkspaces')) else {}
        状态=会话链接状态(任务.get('sessionId'),会话 or {},工作区 or {})
        标签=会话标签(任务.get('sessionId'),会话 or {})
        钮=文档.createElement('button')
        钮.type='button'
        钮.className='linkedSession'
        标(钮)
        钮.disabled=状态!='available'
        名=管理中文['detail.openSessionTitle'] if 标签['titled'] else 管理中文['detail.openSession']
        if 标签['titled']:
            钮.setAttribute('aria-label',套用(名,{'title':标签['text']}))
        else:
            钮.setAttribute('aria-label',名)
        字=文档.createElement('span')
        字.className='linkedSessionLabel'
        标(字)
        字.textContent=管理中文['detail.session']
        钮.appendChild(字)
        def 打开(事件):
            '打开原会话'
            自身.属性['onOpenSession'](任务['sessionId'])
        钮.addEventListener('click',打开)
        图=引用图标常规({'window':窗口,'kind':'session'})
        if 图 is not None:
            钮.appendChild(图)
        右=图标右chevron14({'window':窗口})
        if 右 is not None:
            钮.appendChild(右)
        动作.appendChild(钮)
        if 状态!='available':
            注=文档.createElement('p')
            注.className='detailNotice'
            标(注)
            注.setAttribute('role','status')
            注.textContent=管理中文[会话提示[状态]]
            动作.appendChild(注)

    def 画规则(自身,滚,文档,窗口,任务,显示,忙):
        '名字、下次运行、内容和运行时间'
        头=文档.createElement('header')
        头.className='detailHeader'
        标(头)
        if 任务.get('status')=='inactive':
            题=文档.createElement('h2')
            题.className='readonlyName'
            标(题)
            题.textContent=显示['title']
            头.appendChild(题)
        else:
            名=文档.createElement('input')
            名.className='editName'
            标(名)
            名.setAttribute('aria-label',管理中文['detail.name'])
            名.disabled=忙 or 自身.待定
            名.value=显示['title']
            def 改名(事件):
                '改标题草稿'
                自身.改内容({'title':事件.target.value})
            名.addEventListener('input',改名)
            头.appendChild(名)
        滚.appendChild(头)
        下次=文档.createElement('div')
        下次.className='nextRun'
        标(下次)
        段=文档.createElement('p')
        if 任务.get('status')=='active':
            两段=下次运行两段(任务.get('scheduledAt') or '',管理中文['time.locale'],自身.现在,管理中文)
            段.appendChild(文档.createTextNode(管理中文['detail.nextRun']+' '))
            时=文档.createElement('time')
            时.setAttribute('dateTime',任务.get('scheduledAt') or '')
            时.textContent=两段['absolute']
            段.appendChild(时)
            段.appendChild(文档.createTextNode(' '))
            相对=文档.createElement('span')
            相对.className='nextRunRelative'
            标(相对)
            相对.textContent=两段['relative']
            段.appendChild(相对)
        else:
            段.textContent=管理中文['status.inactive']
        下次.appendChild(段)
        滚.appendChild(下次)
        if 任务.get('status')=='inactive':
            指令=文档.createElement('p')
            指令.className='readonlyPrompt'
            标(指令)
            指令.textContent=显示['prompt']
            滚.appendChild(指令)
        else:
            框=文档.createElement('textarea')
            框.className='instruction'
            标(框)
            框.setAttribute('aria-label',管理中文['detail.instruction'])
            框.disabled=忙 or 自身.待定
            框.value=显示['prompt']
            def 改指令(事件):
                '改指令草稿'
                自身.改内容({'prompt':事件.target.value})
            框.addEventListener('input',改指令)
            滚.appendChild(框)
        卡=文档.createElement('section')
        卡.className='ruleCard'
        标(卡)
        卡.setAttribute('aria-label',管理中文['rule.title'])
        题=文档.createElement('h3')
        题.textContent=管理中文['rule.title']
        卡.appendChild(题)
        自身.画重复(卡,文档,窗口,任务,显示,忙)
        滚.appendChild(卡)
        错=自身.失败
        if 错 in 本地失败:
            错=草稿错误(显示)
        if 错 is not None and 显示['kind']!='every':
            提=文档.createElement('p')
            提.className='ruleHint ruleHintError'
            标(提)
            提.setAttribute('role','alert')
            提.textContent=管理中文.get(错,错)
            卡.appendChild(提)

    def 画重复(自身,卡,文档,窗口,任务,显示,忙):
        '重复菜单，以及按种类出现的日期、时间和时区'
        禁用=忙 or 自身.待定 or 任务.get('status')=='inactive'
        锚=文档.createElement('button')
        锚.type='button'
        锚.className='ruleValue'
        标(锚)
        锚.disabled=禁用
        左=文档.createElement('span')
        左.className='ruleLabel'
        标(左)
        左.textContent=管理中文['rule.repeat']
        锚.appendChild(左)
        右=文档.createElement('span')
        右.className='ruleCurrent'
        标(右)
        种类=显示['kind']
        if 种类=='every':
            右.textContent=管理中文['rule.everyHours']
        elif 种类=='cron' or 规则种类(任务)!=种类:
            右.textContent=管理中文[重复文案.get(种类,重复文案['once'])]
        else:
            系统=窗口.Intl.DateTimeFormat().resolvedOptions().timeZone
            def 标时区(区,系统=系统):
                '频率行上的时区名'
                return 时区标签(区,管理中文)
            右.textContent=格式化日程频率(任务,管理中文,{'system':系统,'label':标时区})
        锚.appendChild(右)
        下=图标下chevron14({'window':窗口})
        if 下 is not None:
            锚.appendChild(下)
        def 点重复(事件):
            '展开重复菜单'
            自身.重复开=not 自身.重复开
            自身.渲染()
        锚.addEventListener('click',点重复)
        项列=[]
        for 值 in 重复选项:
            项列.append({'id':值,'label':管理中文[重复文案[值]],'disabled':禁用})
        if 自身.重复菜单 is None:
            自身.重复菜单=任务菜单({'window':窗口})
        卡.appendChild(自身.重复菜单.渲染({
            'window':窗口,'open':自身.重复开,'anchor':锚,'align':'end','portal':True,
            'items':项列,'selectedId':种类,'onClose':自身.关重复,'onSelect':自身.选重复,
        }))
        if 种类=='every':
            行=文档.createElement('div')
            行.className='ruleRow'
            标(行)
            标字=文档.createElement('label')
            标字.className='ruleLabel'
            标(标字)
            标字.textContent=管理中文['timing.interval']
            行.appendChild(标字)
            框=文档.createElement('input')
            框.className='ruleInput'
            标(框)
            框.type='number'
            框.min='1'
            秒=显示['draft']['seconds']
            框.value='' if 秒=='' else str(int(秒)/3600 if str(秒).isdigit() else '')
            def 改间隔(事件):
                '按小时写回秒'
                文=事件.target.value
                if 文=='':
                    自身.改草稿({'seconds':''})
                else:
                    自身.改草稿({'seconds':str(int(round(float(文)*3600)))})
            框.addEventListener('input',改间隔)
            行.appendChild(框)
            单位=文档.createElement('span')
            单位.className='ruleIntervalUnit'
            标(单位)
            单位.textContent=管理中文['timing.unit.hour']
            行.appendChild(单位)
            卡.appendChild(行)
        if 种类=='once':
            自身.画日期(卡,文档,窗口,显示,禁用)
        if 种类!='cron' and 种类!='every':
            自身.画时间(卡,文档,窗口,显示,禁用)
        if 种类=='weekly' or 种类=='weekdays':
            自身.画星期(卡,文档,窗口,显示,禁用)
        if 种类=='cron':
            框=文档.createElement('input')
            框.className='ruleInput'
            标(框)
            框.value=显示['draft']['expression']
            def 改表达式(事件):
                '改 cron 原文'
                自身.改草稿({'expression':事件.target.value})
            框.addEventListener('input',改表达式)
            卡.appendChild(框)
            解析=解析定时表达式(显示['draft']['expression'])
            提=文档.createElement('p')
            提.className='ruleHint'
            标(提)
            提.textContent=管理中文['rule.cronInvalid'] if 解析 is None else 定时预览(解析,管理中文,管理中文['time.locale'])
            卡.appendChild(提)
        if 种类!='every':
            自身.画时区(卡,文档,窗口,显示,禁用)

    def 画日期(自身,卡,文档,窗口,显示,禁用):
        '日期按钮和月历'
        钮=文档.createElement('button')
        钮.type='button'
        钮.className='ruleInput pickerTrigger'
        标(钮)
        钮.disabled=禁用
        钮.setAttribute('aria-label',管理中文['timing.date'])
        字=文档.createElement('span')
        字.textContent=斜杠日期(显示['draft']['date'])
        钮.appendChild(字)
        图=日历图标节点(窗口.document,'pickerIcon')
        if 图 is not None:
            图.setAttribute('data-dsh-css',样式模块)
            钮.appendChild(图)
        def 点(事件):
            '打开月历'
            自身.日期开=not 自身.日期开
            自身.渲染()
        钮.addEventListener('click',点)
        卡.appendChild(钮)
        if 自身.日期器 is None:
            自身.日期器=日期选择({'window':窗口,'open':False,'anchor':钮,'value':显示['draft']['date'],'onPick':自身.选日期,'onClose':自身.关日期})
        if 自身.日期开:
            自身.日期器.同步({'window':窗口,'open':True,'anchor':钮,'value':显示['draft']['date'],'onPick':自身.选日期,'onClose':自身.关日期})

    def 画时间(自身,卡,文档,窗口,显示,禁用):
        '时间按钮和时钟'
        钮=文档.createElement('button')
        钮.type='button'
        钮.className='ruleInput pickerTrigger'
        标(钮)
        钮.disabled=禁用
        钮.setAttribute('aria-label',管理中文['timing.time'])
        字=文档.createElement('span')
        字.textContent=秒精度(显示['draft']['time'])
        钮.appendChild(字)
        钮.appendChild(画时钟(窗口.document,14,'pickerIcon'))
        def 点(事件):
            '打开时钟'
            自身.时间开=not 自身.时间开
            自身.渲染()
        钮.addEventListener('click',点)
        卡.appendChild(钮)
        if 自身.时钟器 is None:
            自身.时钟器=时钟选择({'window':窗口,'open':False,'anchor':钮,'value':显示['draft']['time'],'onPick':自身.选时间,'onClose':自身.关时间})
        if 自身.时间开:
            自身.时钟器.同步({'window':窗口,'open':True,'anchor':钮,'value':显示['draft']['time'],'onPick':自身.选时间,'onClose':自身.关时间,'seconds':显示['kind']!='cron'})

    def 画星期(自身,卡,文档,窗口,显示,禁用):
        '周一到周日的胶囊'
        行=文档.createElement('div')
        行.className='ruleWeekdays'
        标(行)
        for 日 in 全部星期:
            选中=日 in 显示['weekdays']
            def 点(事件,日=日):
                '至少留一天'
                当前=list(自身.编辑['shown']['weekdays'])
                if 日 in 当前 and len(当前)==1:
                    return
                if 日 in 当前:
                    当前=[项 for 项 in 当前 if 项!=日]
                else:
                    当前=sorted(当前+[日])
                自身.改星期(当前)
            胶囊=处理胶囊(窗口,{'active':选中,'disabled':禁用,'children':管理中文[星期文案[日]],'onClick':点,'window':窗口})
            if 胶囊 is not None:
                胶囊.setAttribute('aria-pressed','true' if 选中 else 'false')
                行.appendChild(胶囊)
        卡.appendChild(行)

    def 画时区(自身,卡,文档,窗口,显示,禁用):
        '时区菜单。本机时区排第一'
        系统=窗口.Intl.DateTimeFormat().resolvedOptions().timeZone or 'UTC'
        锚=文档.createElement('button')
        锚.type='button'
        锚.className='ruleValue'
        标(锚)
        锚.disabled=禁用
        左=文档.createElement('span')
        左.className='ruleLabel'
        标(左)
        左.textContent=管理中文['timing.zone']
        锚.appendChild(左)
        右=文档.createElement('span')
        右.className='ruleCurrent'
        标(右)
        右.textContent=时区名(显示['draft']['timeZone'] or 系统,系统,管理中文)
        锚.appendChild(右)
        def 点(事件):
            '展开时区'
            自身.时区开=not 自身.时区开
            自身.渲染()
        锚.addEventListener('click',点)
        项列=[]
        if 自身.时区开:
            for 区 in 时区选项(显示['draft']['timeZone'] or 系统,系统):
                名=时区名(区,系统,管理中文)
                if 自身.时区查询 and 自身.时区查询.lower() not in (区+' '+名).lower():
                    continue
                项列.append({'id':区,'label':名,'disabled':禁用})
            if len(项列)==0:
                项列.append({'id':'__empty','label':管理中文['timing.zoneNoResults'],'disabled':True})
        搜索=文档.createElement('input')
        搜索.className='zoneSearch'
        标(搜索)
        搜索.setAttribute('data-menu-field','')
        搜索.setAttribute('aria-label',管理中文['timing.zoneSearch'])
        搜索.setAttribute('placeholder',管理中文['timing.zoneSearch'])
        搜索.value=自身.时区查询
        def 改查(事件):
            '按偏移、标识或城市过滤'
            自身.时区查询=事件.target.value
            自身.渲染()
        搜索.addEventListener('input',改查)
        if 自身.时区菜单 is None:
            自身.时区菜单=任务菜单({'window':窗口})
        卡.appendChild(自身.时区菜单.渲染({
            'window':窗口,'open':自身.时区开,'anchor':锚,'align':'end','portal':True,
            'listClassName':'zoneMenu','header':搜索,'items':项列,
            'selectedId':显示['draft']['timeZone'],'onClose':自身.关时区,'onSelect':自身.选时区,
        }))

    def 画记录(自身,滚,窗口,任务):
        '运行记录'
        if 自身.历史 is None:
            自身.历史=投递历史({'window':窗口})
        节点=自身.历史({
            'window':窗口,
            'id':任务.get('id'),
            'sessionId':任务.get('sessionId'),
            'latestMessageId':(任务.get('lastDelivery') or {}).get('messageId') if isinstance(任务.get('lastDelivery'),dict) else None,
            'timeZone':记录时区(任务),
            'loadHistory':自身.属性.get('loadHistory'),
        })
        if 节点 is not None:
            滚.appendChild(节点)

    def 改内容(自身,补丁):
        '改名字或指令。不整页重画，避免输入框丢焦点'
        显示=dict(自身.编辑['shown'])
        显示.update(补丁)
        自身.编辑={**自身.编辑,'shown':显示}
        自身.刷新保存条()

    def 改草稿(自身,补丁):
        '改时刻字段。不整页重画，避免输入框丢焦点'
        显示=dict(自身.编辑['shown'])
        草稿=dict(显示['draft'])
        草稿.update(补丁)
        显示['draft']=草稿
        自身.编辑={**自身.编辑,'shown':显示}
        自身.刷新保存条()

    def 刷新保存条(自身):
        '草稿脏了才补上保存条'
        if 自身.根 is None:
            return
        侧=自身.根.querySelector('aside')
        if 侧 is None:
            return
        已有=侧.querySelector('.saveFooter')
        显示=自身.编辑['shown']
        脏=比较键(显示)!=比较键(自身.编辑['stored'])
        if not 脏:
            if 已有 is not None:
                已有.remove()
            return
        if 已有 is not None:
            return
        自身.渲染()

    def 改星期(自身,星期):
        '改每周的日子'
        显示=dict(自身.编辑['shown'])
        显示['weekdays']=星期
        自身.编辑={**自身.编辑,'shown':显示}
        自身.渲染()

    def 选重复(自身,标识):
        '换成另一种重复'
        自身.重复开=False
        表={'every-hour':'every','every-minute':'every','every-second':'every'}
        种类=表.get(标识,标识)
        显示=dict(自身.编辑['shown'])
        显示['kind']=种类
        if 种类=='weekdays':
            显示['weekdays']=list(工作日)
        if 种类=='every':
            草稿=dict(显示['draft'])
            草稿['seconds']='3600'
            显示['draft']=草稿
        自身.编辑={**自身.编辑,'shown':显示}
        自身.渲染()

    def 选日期(自身,日期):
        '月历写回 ISO 日期'
        自身.改草稿({'date':日期})
        自身.渲染()

    def 选时间(自身,时间):
        '时钟写回时刻'
        自身.改草稿({'time':时间})
        自身.渲染()

    def 选时区(自身,时区):
        '换时区'
        自身.时区开=False
        自身.时区查询=''
        if 时区=='__empty':
            自身.渲染()
            return
        自身.改草稿({'timeZone':时区})

    def 关菜单(自身):
        '关掉更多菜单'
        自身.菜单开=False
        自身.渲染()

    def 关重复(自身):
        '关掉重复菜单'
        自身.重复开=False
        自身.渲染()

    def 关时区(自身):
        '关掉时区菜单'
        自身.时区开=False
        自身.时区查询=''
        自身.渲染()

    def 关日期(自身):
        '关掉月历'
        自身.日期开=False
        自身.渲染()

    def 关时间(自身):
        '关掉时钟'
        自身.时间开=False
        自身.渲染()

    def 点删除(自身,标识):
        '打开删除确认'
        自身.菜单开=False
        自身.属性['onConfirm'](自身.属性['task']['id'])
        自身.渲染()

    def 关确认(自身):
        '关掉删除确认'
        自身.属性['onConfirm'](None)
        自身.渲染()

    def 确认删除(自身):
        '先留下这条，再等目录刷新确认删掉'
        自身.已确认删除=True
        自身.属性['onConfirm'](None)
        自身.属性['onDelete'](自身.属性['task']['id'])
        自身.渲染()

    def 取消(自身):
        '回到存下的值'
        自身.编辑={**自身.编辑,'shown':自身.编辑['stored']}
        自身.失败=None
        自身.渲染()

    def 保存(自身):
        '本地检查过后提交。失败把中文留在提示里'
        显示=自身.编辑['shown']
        无效=草稿错误(显示)
        if 无效 is not None:
            自身.失败=无效
            自身.渲染()
            return
        任务=自身.属性['task']
        已存=自身.编辑['stored']
        请求={'sessionId':任务['sessionId'],'id':任务['id'],'expected':时刻快照(任务)}
        if 显示['title'].strip()!=已存['title']:
            请求['title']=显示['title'].strip()
        if 显示['prompt'].strip()!=已存['prompt']:
            请求['prompt']=显示['prompt'].strip()
        时刻键=json.dumps([显示['kind'],显示['draft'],显示['weekdays']],ensure_ascii=False)
        已存键=json.dumps([已存['kind'],已存['draft'],已存['weekdays']],ensure_ascii=False)
        if 时刻键!=已存键:
            请求['change']=规则变更(显示['draft'],显示['kind'],显示['weekdays'])
        自身.待定=True
        自身.失败=None
        try:
            结果=自身.属性['onUpdateTiming'](请求)
        except Exception:
            自身.待定=False
            自身.失败='rule.error.unknown'
            自身.渲染()
            return
        自身.待定=False
        if not isinstance(结果,dict) or not 结果.get('ok'):
            自身.失败='rule.error.unknown'
        elif isinstance(结果.get('value'),dict) and 'code' in 结果['value']:
            键=时刻错误(结果['value']['code'])
            自身.失败=规则覆盖.get(键,键)
        else:
            记录=结果['value'].get('record') if isinstance(结果.get('value'),dict) else None
            if isinstance(记录,dict):
                值=规则值(记录)
                自身.编辑={'stored':值,'shown':值}
        自身.渲染()

    def 拆除(自身):
        '卸下相对时钟和还开着的历史请求'
        if callable(自身.停时钟):
            自身.停时钟()
            自身.停时钟=None
        if 自身.历史 is not None:
            自身.历史.拆除()

    def __call__(自身,属性=None):
        '再画'
        return 自身.渲染(属性)
