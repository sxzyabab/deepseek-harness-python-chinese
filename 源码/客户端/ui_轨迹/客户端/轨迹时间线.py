import importlib.resources as 包资源
import math
from datetime import datetime
import pywebbridge
from ...ui_基础界面组件.提示泡 import 提示泡#悬停说明
from .时间线 import 派生轨迹时间线,格式化时间线偏移#投影

样式文本=包资源.files(__package__).joinpath('轨迹时间线.module.css').read_text(encoding='utf-8')

最小拖动像素=3
最小缩放操作数=4
边平移区比例=0.08
边平移步进比例=0.025
最大边平移像素=32
时间线提示延迟毫秒=500
种类名={
    'system':'系统','user':'用户','context':'上下文','compacted':'已压缩',
    'message':'助手','tool':'工具','subtool':'子工具',
}

def 钳制比例(值):
    '把比例钳到单位区间'
    return min(1,max(0,值))

def 有序区间(左,右):
    '保证 start<=end'
    if 左<=右:
        return {'start':左,'end':右}
    return {'start':右,'end':左}

def 居中区间(中心,宽度,最小,最大):
    '以中心铺开宽度，钳在最小和最大之间'
    钳宽=min(最大-最小,max(0,宽度))
    起点=min(max(中心-钳宽/2,最小),最大-钳宽)
    return {'start':起点,'end':起点+钳宽}

def 区间比例(区间,起点,时长,最小,最大):
    '把投影选区换成相对当前域的比例区间'
    界=有序区间(min(最大,max(最小,区间['start'])),min(最大,max(最小,区间['end'])))
    return {'start':(界['start']-起点)/时长,'end':(界['end']-起点)/时长}

def 格式化记录时刻(时间戳):
    '把毫秒时间戳格式成本地时刻'
    时刻=datetime.fromtimestamp(时间戳/1000)
    return 时刻.strftime('%H:%M:%S')+'.'+str(时刻.microsecond//1000).zfill(3)

def 助手计时明细(指标):
    '有完整计时则返回首 token 和解码毫秒'
    if not isinstance(指标,dict) or 指标.get('timingRecorded') is not True:
        return {}
    开始=指标.get('stepStartTime')
    首=指标.get('firstTokenTime')
    完成=指标.get('completedTime')
    if not all(isinstance(项,(int,float)) and not isinstance(项,bool) and math.isfinite(项) for 项 in (开始,首,完成)):
        return {}
    if 首<开始 or 完成<首:
        return {}
    return {'ttftMs':首-开始,'decodingMs':完成-首}

def 时间线记录明细(格):
    '从格子合成提示用明细'
    明细={}
    if isinstance(格.get('timeSeconds'),(int,float)) and not isinstance(格.get('timeSeconds'),bool) and math.isfinite(格['timeSeconds']):
        明细['durationMs']=max(0,格['timeSeconds']*1000)
    if isinstance(格.get('startedAt'),(int,float)) and not isinstance(格.get('startedAt'),bool) and math.isfinite(格['startedAt']):
        明细['startedAt']=格['startedAt']
    明细.update(助手计时明细(格.get('assistantMetrics')))
    return 明细

def 时间线提示文案(种类,明细):
    '种类标题、起止时刻和首 token、解码'
    标题=种类名.get(种类,种类)
    if 明细 is None:
        return 标题
    段=[]
    if 明细.get('durationMs') is not None:
        段.append('总计 '+格式化时间线偏移(明细['durationMs']))
    if 明细.get('startedAt') is not None:
        if 明细.get('durationMs') is None:
            范围='开始于 '+格式化记录时刻(明细['startedAt'])
        else:
            范围=格式化记录时刻(明细['startedAt'])+' → '+格式化记录时刻(明细['startedAt']+明细['durationMs'])
    else:
        范围=None
    if 明细.get('ttftMs') is not None and 明细.get('decodingMs') is not None:
        计时='首 token '+格式化时间线偏移(明细['ttftMs'])+' · 解码 '+格式化时间线偏移(明细['decodingMs'])
    else:
        计时=None
    时间=' · '.join(项 for 项 in (None if 明细.get('durationMs') is None else '总计 '+格式化时间线偏移(明细['durationMs']),计时) if 项)
    return '\n'.join(项 for 项 in (标题,范围,时间) if 项 not in (None,''))

class 车道标签:
    '输入、模型、工具三道的名字'
    def __init__(自身,属性):
        '画出三道标签'
        自身.属性=属性
        自身.渲染()

    def 渲染(自身):
        '三道标签不进无障碍树'
        文档=自身.属性['window'].document
        根=文档.createElement('div')
        根.className='labels'
        根.setAttribute('aria-hidden','true')
        for 文案 in ('输入','模型','工具'):
            字=文档.createElement('span')
            字.textContent=文案
            根.appendChild(字)
        if 自身.属性.get('parent') is not None:
            自身.属性['parent'].appendChild(根)
        自身.根=根
        return 根

class 更早历史边界:
    '加载更早历史的省略按钮'
    def __init__(自身,属性):
        '画出省略按钮'
        自身.属性=属性
        自身.渲染()

    def 渲染(自身):
        '加载中和可点的文案不同'
        属性=自身.属性
        文档=属性['window'].document
        加载中=属性.get('loading') is True
        钮=文档.createElement('button')
        钮.setAttribute('type','button')
        钮.className='earlierHistory'
        钮.setAttribute('data-earlier-history','')
        if 加载中:
            钮.setAttribute('data-loading','true')
        钮.setAttribute('aria-label','正在加载更早的历史…' if 加载中 else '加载更早的历史')
        if 加载中 or not callable(属性.get('onLoad')):
            钮.setAttribute('aria-disabled','true')
        钮.textContent='…'
        def 进入(事件):
            '悬停时清掉轨道上的十字线'
            事件.stopPropagation()
            if callable(属性.get('onHover')):
                属性['onHover']()
        def 挡住(事件):
            '不把指针交给轨道'
            事件.stopPropagation()
        def 点击(_事件):
            '再加载一页更早历史'
            if callable(属性.get('onLoad')):
                属性['onLoad']()
        钮.addEventListener('pointerenter',进入)
        钮.addEventListener('pointermove',挡住)
        钮.addEventListener('pointerdown',挡住)
        钮.addEventListener('click',点击)
        提示泡({
            'window':属性['window'],
            'label':'正在加载更早的历史…' if 加载中 else '点击加载更早的历史',
            'side':'right',
            'delayMs':时间线提示延迟毫秒,
            'children':钮,
            'parent':属性.get('parent'),
        }).渲染()
        自身.根=钮
        return 钮

class 轨迹时间线:
    '拖选区间、点击聚焦、滚轮缩放、右键平移、Escape 清空'
    def __init__(自身,属性):
        '记下属性与手势'
        自身.属性=属性 or {}
        自身.草稿=None
        自身.悬停=None
        自身.加载更早中=False
        自身.平移中=False
        自身.视口=None
        自身.动画视口=False
        自身.拖动=None
        自身.平移=None
        自身.根=None
        自身.轨道=None
        自身.渲染()

    def __call__(自身,属性=None):
        '属性变了就重画，手势状态留着'
        if 属性 is not None:
            自身.属性=属性
        return 自身.渲染()

    def 渲染(自身):
        '按当前模型和视口画出总览'
        属性=自身.属性
        窗口=属性['window']
        文档=窗口.document
        if 文档.getElementById('轨迹时间线样式') is None:
            样式=文档.createElement('style')
            样式.id='轨迹时间线样式'
            样式.textContent=样式文本
            文档.head.appendChild(样式)
        轮次=属性.get('turns') or []
        模式=属性.get('mode') or 'sequence'
        选区=属性.get('range')
        模型=派生轨迹时间线(轮次,模式)
        if 模型 is not None and 选区 is not None and (选区['end']<模型['start'] or 选区['start']>模型['end']):
            if callable(属性.get('onRangeChange')):
                属性['onRangeChange'](None)
            选区=None
        if 模型 is not None and 自身.视口 is not None and (自身.视口['end']<模型['start'] or 自身.视口['start']>模型['end']):
            自身.视口=None
        全长=max(1,(0 if 模型 is None else 模型['end'])-(0 if 模型 is None else 模型['start']))
        视口长=全长 if 自身.视口 is None else min(全长,max(1,自身.视口['end']-自身.视口['start']))
        if 模型 is None or 自身.视口 is None:
            视口起=0 if 模型 is None else 模型['start']
        else:
            视口起=min(max(自身.视口['start'],模型['start']),模型['end']-视口长)
        域长=全长 if 自身.视口 is None else 视口长
        域起=0 if 模型 is None else (模型['start'] if 自身.视口 is None else 视口起)
        显示更早=属性.get('hasEarlierRecords') is True and 模型 is not None and 域起==模型['start']
        旧=自身.根
        父=None if 旧 is None else 旧.parentNode
        if 旧 is not None:
            旧.remove()
        根=文档.createElement('section')
        根.className='root'
        根.setAttribute('aria-label','轨迹时间线')
        图=文档.createElement('div')
        图.className='plot'
        车道标签({'window':窗口,'parent':图})
        轨=文档.createElement('div')
        轨.className='track'
        if 模型 is None:
            空=文档.createElement('span')
            空.className='empty'
            空.textContent='无计时数据'
            轨.appendChild(空)
            if 属性.get('hasEarlierRecords') is True:
                更早历史边界({
                    'window':窗口,
                    'parent':轨,
                    'loading':自身.加载更早中,
                    'onHover':lambda:自身._清悬停(),
                    'onLoad':自身._加载更早(),
                })
        else:
            if 自身.平移中:
                轨.setAttribute('data-panning','true')
            轨.setAttribute('aria-label','时间线概览；水平拖动可聚焦事件')
            轨.tabIndex=0
            最小选区=min(域长,全长/max(1,len(模型['spans'])))
            域样式={
                '--trajectory-domain-left':str(-(域起-模型['start'])/域长*100)+'%',
                '--trajectory-domain-width':str(全长/域长*100)+'%',
            }
            if 显示更早:
                更早历史边界({
                    'window':窗口,
                    'parent':轨,
                    'loading':自身.加载更早中,
                    'onHover':lambda:自身._清悬停(),
                    'onLoad':自身._加载更早(),
                })
            if 自身.悬停 is not None and 自身.悬停.get('recordIndex') is None and 自身.草稿 is None:
                线=文档.createElement('div')
                线.className='hoverLine'
                线.setAttribute('data-timeline-hover-line','')
                线.setAttribute('aria-hidden','true')
                线.style.setProperty('--trajectory-hover-left',str(自身.悬停['fraction']*100)+'%')
                轨.appendChild(线)
            可见=None
            if 自身.草稿 is not None:
                可见=区间比例(自身.草稿,域起,域长,模型['start'],模型['end'])
            elif 选区 is not None:
                可见=区间比例(选区,域起,域长,模型['start'],模型['end'])
            if 可见 is not None:
                for 类 in ('selection','selectionEdges'):
                    盒=文档.createElement('div')
                    盒.className=类
                    盒.setAttribute('aria-hidden','true')
                    if 自身.草稿 is not None:
                        盒.setAttribute('data-dragging','true')
                    盒.style.setProperty('--trajectory-selection-left',str(可见['start']*100)+'%')
                    盒.style.setProperty('--trajectory-selection-width',str((可见['end']-可见['start'])*100)+'%')
                    轨.appendChild(盒)
            边界盒=文档.createElement('div')
            边界盒.className='turnBoundaries'
            边界盒.setAttribute('aria-hidden','true')
            if 自身.动画视口:
                边界盒.setAttribute('data-animate-viewport','true')
            for 键,值 in 域样式.items():
                边界盒.style.setProperty(键,值)
            for 界 in 模型['turnBoundaries']:
                if 界['time']<=模型['start'] or 界['time']<域起 or 界['time']>域起+域长:
                    continue
                标=文档.createElement('span')
                标.className='turnBoundary'
                标.setAttribute('data-turn',str(界['turn']))
                标.style.setProperty('--trajectory-turn-left',str((界['time']-模型['start'])/全长*100)+'%')
                边界盒.appendChild(标)
            轨.appendChild(边界盒)
            道=文档.createElement('div')
            道.className='lanes'
            道.setAttribute('data-timeline-domain','')
            if 自身.动画视口:
                道.setAttribute('data-animate-viewport','true')
            for 键,值 in 域样式.items():
                道.style.setProperty(键,值)
            明细表={}
            for 轮 in 轮次:
                for 组 in 轮.get('groups') or []:
                    for 格 in 组.get('cells') or []:
                        明细表[格['index']]=时间线记录明细(格)
            活动=自身.草稿 if 自身.草稿 is not None else 选区
            选中=属性.get('selectedIndex')
            搜索=属性.get('searchMatchIndexes')
            for 跨度 in 模型['spans']:
                if 跨度['index']!=选中 and not (跨度['end']>=域起 and 跨度['start']<=域起+域长):
                    continue
                左=(跨度['start']-模型['start'])/全长
                宽=(跨度['end']-跨度['start'])/全长
                明细=明细表.get(跨度['index']) or {}
                首比=None
                if 明细.get('ttftMs') is not None and 明细.get('decodingMs') is not None and 明细['ttftMs']+明细['decodingMs']>0:
                    首比=明细['ttftMs']/(明细['ttftMs']+明细['decodingMs'])
                条=文档.createElement('span')
                条.setAttribute('aria-hidden','true')
                条.className='span'
                条.setAttribute('data-timeline-span',跨度['kind'])
                条.setAttribute('data-timeline-record-index',str(跨度['index']))
                if 首比 is not None:
                    条.setAttribute('data-assistant-timing','true')
                if 跨度.get('isError'):
                    条.setAttribute('data-error','true')
                if 模式=='time':
                    条.setAttribute('data-equal-duration','true')
                if 跨度['index']==选中:
                    条.setAttribute('data-current','true')
                if 自身.悬停 is not None and 自身.悬停.get('recordIndex')==跨度['index']:
                    条.setAttribute('data-hovered','true')
                if 搜索 is not None:
                    条.setAttribute('data-search-match','true' if 跨度['index'] in 搜索 else 'false')
                if 活动 is not None:
                    条.setAttribute('data-selected','true' if 跨度['start']<=活动['end'] and 跨度['end']>=活动['start'] else 'false')
                条.style.setProperty('--trajectory-span-left',str(左*100)+'%')
                条.style.setProperty('--trajectory-span-width',str(宽*100)+'%')
                条.style.setProperty('--trajectory-span-gap','min('+str(宽*100*0.08)+'%, 1px)')
                条.style.setProperty('--trajectory-span-lane',str(跨度['lane']))
                if 首比 is not None:
                    条.style.setProperty('--trajectory-assistant-ttft',str(首比*100)+'%')
                def 文案(种类=跨度['kind'],明细=明细):
                    '悬停时才拼提示'
                    return 时间线提示文案(种类,明细)
                提示泡({
                    'window':窗口,
                    'label':文案,
                    'side':'bottom',
                    'delayMs':时间线提示延迟毫秒,
                    'children':条,
                    'parent':道,
                }).渲染()
            轨.appendChild(道)
            def 比例于(事件):
                '指针在轨道上的位置'
                矩形=事件.currentTarget.getBoundingClientRect()
                宽=矩形.width if 矩形.width else 1
                return 钳制比例((事件.clientX-矩形.left)/max(1,宽))
            def 记录于(事件):
                '点中的记录下标'
                目标=事件.target
                最近=目标.closest('[data-timeline-record-index]') if 目标 is not None and hasattr(目标,'closest') else None
                if 最近 is None:
                    return None
                值=最近.dataset.timelineRecordIndex if hasattr(最近,'dataset') else 最近.getAttribute('data-timeline-record-index')
                try:
                    数=float(值)
                except (TypeError,ValueError):
                    return None
                if not math.isfinite(数):
                    return None
                return 数
            def 按下(事件):
                '左键拖选，右键平移'
                if 事件.button==2:
                    自身.平移={
                        'anchorClientX':事件.clientX,
                        'anchorStart':域起,
                        'moved':False,
                        'pannable':自身.视口 is not None,
                        'pointerId':事件.pointerId,
                    }
                    if 自身.视口 is not None:
                        自身.动画视口=False
                    自身.平移中=True
                    if hasattr(事件.currentTarget,'setPointerCapture'):
                        事件.currentTarget.setPointerCapture(事件.pointerId)
                    自身.渲染()
                    return
                if 事件.button!=0:
                    return
                比例=比例于(事件)
                锚时=域起+比例*域长
                自身.悬停={'fraction':比例,'recordIndex':记录于(事件)}
                自身.拖动={
                    'pointerId':事件.pointerId,
                    'anchorTime':锚时,
                    'anchorClientX':事件.clientX,
                    'recordIndex':自身.悬停['recordIndex'],
                }
                if hasattr(事件.currentTarget,'setPointerCapture'):
                    事件.currentTarget.setPointerCapture(事件.pointerId)
                自身.草稿={'start':锚时,'end':锚时}
                自身.渲染()
            def 移动(事件):
                '拖选或平移视口'
                比例=比例于(事件)
                自身.悬停={'fraction':比例,'recordIndex':记录于(事件)}
                平移=自身.平移
                if 平移 is not None and 平移.get('pointerId')==事件.pointerId:
                    if abs(事件.clientX-平移['anchorClientX'])>=最小拖动像素:
                        平移['moved']=True
                    if not 平移['pannable']:
                        自身.渲染()
                        return
                    矩形=事件.currentTarget.getBoundingClientRect()
                    差=(事件.clientX-平移['anchorClientX'])/max(1,矩形.width or 1)
                    下一=min(max(平移['anchorStart']-差*域长,模型['start']),模型['end']-域长)
                    自身.视口={'start':下一,'end':下一+域长}
                    自身.渲染()
                    return
                拖=自身.拖动
                if 拖 is None or 拖.get('pointerId')!=事件.pointerId:
                    自身.渲染()
                    return
                自身.草稿=有序区间(拖['anchorTime'],域起+比例*域长)
                自身.渲染()
            def 抬起(事件):
                '松手后提交选区、点选记录或聚焦最近记录'
                平移=自身.平移
                if 平移 is not None and 平移.get('pointerId')==事件.pointerId:
                    动过=平移['moved'] or abs(事件.clientX-平移['anchorClientX'])>=最小拖动像素
                    自身.平移=None
                    自身.平移中=False
                    if not 动过 and callable(属性.get('onRangeChange')):
                        属性['onRangeChange'](None)
                    自身.渲染()
                    return
                拖=自身.拖动
                if 拖 is None or 拖.get('pointerId')!=事件.pointerId:
                    return
                比例=比例于(事件)
                点时=域起+比例*域长
                选定=有序区间(拖['anchorTime'],点时)
                自身.悬停={'fraction':比例,'recordIndex':记录于(事件)}
                自身.拖动=None
                自身.草稿=None
                是点击=abs(事件.clientX-拖['anchorClientX'])<最小拖动像素
                点中=None
                if 是点击 and 拖.get('recordIndex') is not None:
                    for 跨度 in 模型['spans']:
                        if 跨度['index']==拖['recordIndex']:
                            点中=跨度
                            break
                if 点中 is not None:
                    if callable(属性.get('onRangeChange')):
                        属性['onRangeChange'](None)
                    if callable(属性.get('onRecordSelect')):
                        属性['onRecordSelect'](点中['index'])
                    自身.渲染()
                    return
                if 选定['end']-选定['start']<最小选区:
                    中心=选定['start'] if 是点击 else (选定['start']+选定['end'])/2
                    提交=居中区间(中心,最小选区,模型['start'],模型['end'])
                else:
                    提交=选定
                if callable(属性.get('onRangeChange')):
                    属性['onRangeChange'](提交)
                if 是点击 and len(模型['spans'])>0:
                    最近=模型['spans'][0]
                    最近距=0 if 最近['start']<=选定['start']<=最近['end'] else min(abs(选定['start']-最近['start']),abs(选定['start']-最近['end']))
                    for 跨度 in 模型['spans']:
                        if 跨度['start']<=选定['start']<=跨度['end']:
                            距=0
                        elif 选定['start']<跨度['start']:
                            距=跨度['start']-选定['start']
                        else:
                            距=选定['start']-跨度['end']
                        if 距<最近距:
                            最近=跨度
                            最近距=距
                    if callable(属性.get('onRecordFocus')):
                        属性['onRecordFocus'](最近['index'])
                自身.渲染()
            def 按键(事件):
                'Escape 清掉选区'
                if 事件.key!='Escape' or 属性.get('range') is None:
                    return
                事件.preventDefault()
                if callable(属性.get('onRangeChange')):
                    属性['onRangeChange'](None)
            def 取消(_事件=None):
                '指针取消时丢掉草稿'
                自身.拖动=None
                自身.平移=None
                自身.草稿=None
                自身.悬停=None
                自身.平移中=False
                自身.渲染()
            def 离开(_事件):
                '没有手势时清掉悬停'
                if 自身.拖动 is None and 自身.平移 is None:
                    自身.悬停=None
                    自身.渲染()
            def 双击(事件):
                '双击清掉选区'
                事件.preventDefault()
                if callable(属性.get('onRangeChange')):
                    属性['onRangeChange'](None)
            def 右键(事件):
                '右键留给平移，不弹菜单'
                事件.preventDefault()
            def 滚轮(事件):
                '以指针为锚缩放视口'
                事件.preventDefault()
                矩形=轨.getBoundingClientRect()
                比例=钳制比例((事件.clientX-矩形.left)/max(1,矩形.width or 1))
                自身.动画视口=False
                下限=min(最小缩放操作数 if 模式=='sequence' else 20,全长)
                下一长=min(全长,max(下限,域长*math.exp(事件.deltaY*0.0015)))
                if 下一长>=全长*0.999:
                    自身.视口=None
                else:
                    锚时=域起+比例*域长
                    下一=min(max(锚时-比例*下一长,模型['start']),模型['end']-下一长)
                    自身.视口={'start':下一,'end':下一+下一长}
                自身.渲染()
            轨.addEventListener('pointerdown',按下)
            轨.addEventListener('pointermove',移动)
            轨.addEventListener('pointerup',抬起)
            轨.addEventListener('pointercancel',取消)
            轨.addEventListener('pointerleave',离开)
            轨.addEventListener('dblclick',双击)
            轨.addEventListener('contextmenu',右键)
            轨.addEventListener('keydown',按键)
            根.addEventListener('wheel',滚轮)
        图.appendChild(轨)
        根.appendChild(图)
        自身.根=根
        自身.轨道=轨
        if 父 is None and 属性.get('parent') is not None:
            父=属性['parent']
        if 父 is not None and 根.parentNode is not 父:
            父.appendChild(根)
        return 根

    def _清悬停(自身):
        '边界按钮悬停时不画十字线'
        自身.悬停=None
        自身.渲染()

    def _加载更早(自身):
        '再要一页更早历史。调用是同步的'
        回调=自身.属性.get('onLoadEarlier')
        if not callable(回调) or 自身.加载更早中:
            return None
        自身.加载更早中=True
        自身.渲染()
        try:
            return 回调()
        finally:
            自身.加载更早中=False
            自身.渲染()
