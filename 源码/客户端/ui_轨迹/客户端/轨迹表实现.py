import importlib.resources as 包资源
import json
import math
import pywebbridge
from ...ui_基础界面组件.状态点 import 状态点#加载中的点
from ...ui_基础界面组件.Json树 import Json树#选项和来源
from ...ui_基础界面组件.markdown.Markdown文本 import Markdown文本#预览
from ...ui_基础界面组件.提示泡 import 提示泡#种类名
from .轨迹记录 import 格式化已用秒数,轨迹记录身份#身份和时长
from .轨迹预览 import 轨迹预览文本#单行预览
from .代码程序 import 代码程序,编程工具调用名#PTC
from .复制代码 import 压缩中断错误#压缩打断标记
from .虚拟行 import 编组轨迹虚拟行,轨迹虚拟记录键#开窗

样式文本=包资源.files(__package__).joinpath('轨迹表.module.css').read_text(encoding='utf-8')

底部跟随阈值=2
更早加载阈值=48
虚拟化阈值=100
详情最小宽=320
详情最大宽=720
表最小宽=280
详情缩放步长=16
工具请求占比=0.58
工具请求最小宽=180
工具请求最大宽=480
默认工具请求占比=0.36
默认工具请求偏移=56
种类名={
    'system':'系统','user':'用户','context':'上下文','compacted':'已压缩',
    'message':'助手','tool':'工具','subtool':'子工具',
}
种类类={
    'system':'systemNeutral','user':'user','context':'contextGreen','compacted':'compacted',
    'message':'assistantVioletBright','tool':'toolAmber','subtool':'subtoolAmber',
}
系统提示标签=({'id':'system-prompt','label':'系统提示词'},{'id':'tools','label':'工具'})
系统更新标签=({'id':'diff','label':'差异'},)+系统提示标签
请求标签=({'id':'overview','label':'概述'},{'id':'options','label':'选项'},{'id':'usage','label':'用量'},{'id':'timing','label':'计时'})
树标签={
    'copyValue':'复制值','copyJson':'复制 JSON','copyPath':'复制属性路径',
    'copyPrettyJson':'复制格式化 JSON','copyCompactJson':'复制紧凑 JSON',
    'copied':'复制成功','copyFailed':'复制失败','collapseNode':'收起','expandNode':'展开',
    'copyButtonTitle':lambda 动作:str(动作)+'；右键点击可选择复制方式',
}
文标签={'code':{'copyLabel':'复制','copiedLabel':'复制成功'},'footnotes':'脚注'}

def 请求键(回合,组名):
    '轮次和组名合成键'
    return str(回合)+'\u0000'+str(组名)

def 请求身份(请求):
    '压缩用序号，助手用回合和步'
    if 请求.get('purpose')=='compaction':
        return 'compaction\u0000'+str(请求.get('seq'))
    return 'assistant\u0000'+str(请求.get('turn'))+'\u0000'+str(请求.get('step'))

def 展平记录(轮次列表):
    '按展示顺序展平轮次组'
    记录=[]
    for 段,轮次 in enumerate(轮次列表 or []):
        段内第一=True
        本段=[]
        for 组 in 轮次.get('groups') or []:
            for 位,格 in enumerate(组.get('cells') or []):
                轮次开始=段内第一 and 格.get('requestOnly') is not True and 格.get('kind')!='system' and (格.get('kind')!='compacted' or 轮次.get('turn') is None)
                if 轮次开始:
                    段内第一=False
                本段.append({
                    'turn':轮次.get('turn'),
                    'section':段,
                    'group':组.get('title'),
                    'groupStart':位==0,
                    'turnStart':轮次开始,
                    'cell':格,
                    'turnEnd':False,
                })
        if len(本段)>0:
            本段[-1]['turnEnd']=True
        记录.extend(本段)
    return 记录

def 过滤记录(记录列表,命中):
    '只保留匹配下标，并重算组、轮边界'
    留下=[]
    for 记录 in 记录列表:
        if 记录['cell'].get('requestOnly') is True or 记录['cell'].get('index') not in 命中:
            continue
        拷贝=dict(记录)
        拷贝['groupStart']=False
        拷贝['turnStart']=False
        拷贝['turnEnd']=False
        留下.append(拷贝)
    已开始=set()
    for 位,记录 in enumerate(留下):
        上一=留下[位-1] if 位>0 else None
        下一=留下[位+1] if 位+1<len(留下) else None
        记录['groupStart']=上一 is None or 上一['section']!=记录['section'] or 上一['group']!=记录['group']
        记录['turnStart']=记录['section'] not in 已开始 and 记录['cell'].get('kind')!='system' and (记录['cell'].get('kind')!='compacted' or 记录['turn'] is None)
        if 记录['turnStart']:
            已开始.add(记录['section'])
        记录['turnEnd']=下一 is None or 下一['section']!=记录['section']
    return 留下

def 段落标签(回合):
    '轮次或轮间'
    if 回合 is None:
        return '轮次之间'
    return '第 '+str(回合)+' 轮'

def 索引请求边界(记录列表,请求组):
    '每个请求组第一条可见边界'
    边界={}
    for 记录 in 记录列表:
        键=请求键(记录['turn'],记录['group'])
        if 键 not in 请求组 or 键 in 边界:
            continue
        if 记录['cell'].get('kind') in ('user','context'):
            continue
        边界[键]=记录['cell'].get('index')
    return 边界

def 索引请求编号(会话编号):
    '组键到编号'
    编号={}
    for 请求 in 会话编号 or []:
        编号[请求键(请求.get('turn'),请求.get('group'))]=请求.get('number')
    return 编号

def 索引边界游程(记录列表,请求组):
    '连续请求分隔符的偏移'
    偏移={}
    游程=0
    for 记录 in 记录列表:
        if 记录['cell'].get('requestOnly') is True:
            偏移[记录['cell'].get('index')]=游程
            游程+=1
            continue
        if 游程>0 and 记录.get('groupStart') and 请求键(记录['turn'],记录['group']) in 请求组:
            偏移[记录['cell'].get('index')]=游程
        游程=0
    return 偏移

def 摘要轮次(记录列表,请求组):
    '步数和工具调用'
    步=set()
    for 记录 in 记录列表:
        键=请求键(记录['turn'],记录['group'])
        if 键 in 请求组:
            步.add(键)
    调用=sum(1 for 记录 in 记录列表 if 记录['cell'].get('kind') in ('tool','subtool'))
    return str(len(步))+' 个步骤 · '+str(调用)+' 个工具调用'

def 折叠轮次记录(记录列表,收起轮次,请求组):
    '折叠轮次内容为摘要行'
    按轮={}
    for 记录 in 记录列表:
        if 记录['turn'] is None:
            continue
        按轮.setdefault(记录['turn'],[]).append(记录)
    输出=[]
    for 记录 in 记录列表:
        if 记录['turn'] is None or 记录['turn'] not in 收起轮次:
            输出.append(记录)
            continue
        本轮=按轮.get(记录['turn']) or [记录]
        if 记录['cell'].get('requestOnly') is True or 记录['cell'].get('kind')=='system':
            输出.append(记录)
            continue
        内容=[项 for 项 in 本轮 if 项['cell'].get('requestOnly') is not True and 项['cell'].get('kind')!='system']
        if len(内容)<=1 or 记录['cell'].get('index')!=内容[0]['cell'].get('index'):
            if len(内容)<=1:
                输出.append(记录)
            continue
        头=dict(记录)
        头['turnEnd']=False
        摘要=dict(记录)
        摘要['groupStart']=False
        摘要['turnStart']=False
        摘要['turnEnd']=True
        摘要['collapsedSummary']=摘要轮次(内容[1:],请求组)
        摘要['collapsedSummaryKind']='turn'
        输出.append(头)
        输出.append(摘要)
    return 输出

def 摘要助手工具(记录列表):
    '工具调用数和名字'
    名称=[]
    for 记录 in 记录列表:
        文本=记录['cell'].get('text') or ''
        位=文本.find(' · ')
        名=文本 if 位==-1 else 文本[:位]
        if 名!='' and 名 not in 名称:
            名称.append(名)
    摘要=str(len(记录列表))+' 个工具调用'
    if len(名称)>0:
        return 摘要+' · '+', '.join(名称)
    return 摘要

def 折叠助手记录(记录列表,收起助手):
    '折叠助手下的工具调用'
    输出=[]
    位=0
    while 位<len(记录列表):
        记录=记录列表[位]
        输出.append(记录)
        if 记录['cell'].get('kind')!='message' or 轨迹记录身份(记录['cell']) not in 收起助手:
            位+=1
            continue
        调用=[]
        下=位+1
        while 下<len(记录列表):
            候选=记录列表[下]
            if 候选.get('collapsedSummary') is not None or 候选['cell'].get('kind') not in ('tool','subtool'):
                break
            调用.append(候选)
            下+=1
        if len(调用)==0:
            位+=1
            continue
        输出[-1]=dict(记录)
        输出[-1]['turnEnd']=False
        摘要=dict(记录)
        摘要['groupStart']=False
        摘要['turnStart']=False
        摘要['turnEnd']=调用[-1].get('turnEnd') or False
        摘要['collapsedSummary']=摘要助手工具(调用)
        摘要['collapsedSummaryKind']='assistant'
        输出.append(摘要)
        位=下
    return 输出

def 记录状态(记录):
    '记录运行态'
    格=记录['cell']
    if 格.get('isError') is True:
        return 'error'
    if 格.get('kind')=='compacted' and 格.get('timeSeconds') is None:
        return 'running'
    指标=格.get('assistantMetrics')
    if isinstance(指标,dict) and 指标.get('completedTime') is None and 'completedTime' in 指标:
        return 'running'
    if 格.get('kind') in ('tool','subtool') and 格.get('outputDetail') is None:
        return 'running'
    return 'complete'

def 状态标签(状态):
    '状态的中文'
    if 状态=='error':
        return '失败'
    if 状态=='running':
        return '等待中'
    return '已完成'

def 请求错误文案(请求):
    '认证失败和压缩打断换成中文，其余用记录原文'
    if 请求.get('errorCode')=='AUTH':
        return 'API 密钥无效'
    if 请求.get('error')==压缩中断错误:
        return '上下文压缩在完成前被中断。'
    return 请求.get('error')

def 仅工具调用(格):
    '助手只有工具调用占位'
    return 格.get('kind')=='message' and not 格.get('outputDetail') and not 格.get('thinkingDetail') and 格.get('text')=='仅工具调用'

def 记录展示文案(格):
    '列表主文案'
    if 仅工具调用(格):
        return ''
    程序=代码程序(格)
    if 程序 is not None:
        return 编程工具调用名+' · '+(' '.join(程序['description'].split()))
    if 格.get('previewMarkdown') is not None:
        预览=轨迹预览文本(格['previewMarkdown'])
        if 格.get('text')=='':
            return 预览
        if 预览=='':
            return 格.get('text') or ''
        return (格.get('text') or '')+' · '+预览
    if 格.get('text'):
        return 格['text']
    if 格.get('kind') in ('user','context'):
        原文=格.get('inputDetail')
    elif 格.get('kind')=='message':
        原文=格.get('outputDetail') if 格.get('outputDetail') is not None else 格.get('thinkingDetail')
    else:
        原文=None
    if 原文 is None:
        return ''
    return 轨迹预览文本(原文)

def 记录结果文案(格):
    '结果预览'
    if 格.get('resultPreviewMarkdown') is None:
        return 格.get('result')
    return 轨迹预览文本(格['resultPreviewMarkdown'])

def 工具文案部件(格,文本):
    '拆工具名和参数'
    if 格.get('kind') not in ('tool','subtool'):
        return None
    位=文本.find(' · ')
    部件={'program':格.get('toolName')==编程工具调用名,'name':文本 if 位==-1 else 文本[:位]}
    if 位!=-1:
        部件['args']=文本[位+3:]
    return 部件

def 详情标签(记录):
    '按记录种类给出标签页'
    格=记录['cell']
    if 格.get('kind')=='system':
        if 格.get('promptDetail') is None and 格.get('systemPromptDetail') is not None:
            return [项 for 项 in 系统提示标签 if 项['id']=='system-prompt']
        if 格.get('previousPromptDetail') is None:
            return list(系统提示标签)
        return list(系统更新标签)
    if 格.get('kind')=='compacted':
        return [{'id':'overview','label':'概述'},{'id':'raw','label':'原始输出'}]
    if 格.get('kind') in ('user','context','message'):
        标签=[{'id':'overview','label':'概述'},{'id':'rendered','label':'预览'},{'id':'raw','label':'原始内容'}]
        if 格.get('messageSource') is not None:
            标签.append({'id':'source','label':'来源'})
        return 标签
    标签=[{'id':'overview','label':'概述'}]
    if 格.get('inputDetail'):
        标签.append({'id':'input','label':'代码' if 代码程序(格) is not None else '参数'})
    if 格.get('outputDetail') or 代码程序(格) is not None:
        标签.append({'id':'output','label':'结果'})
    标签.append({'id':'schema','label':'Schema'})
    标签.append({'id':'timing','label':'计时'})
    return 标签

def 钳制详情宽(宽度,分栏宽):
    '把详情宽钳在分栏可用区间'
    最大=max(详情最小宽,min(详情最大宽,分栏宽-表最小宽))
    return round(min(max(宽度,详情最小宽),最大))

def 默认工具请求宽(分栏宽):
    '按默认占比推导工具请求栏宽'
    return min(max(分栏宽*默认工具请求占比-默认工具请求偏移,工具请求最小宽),工具请求最大宽)

def 格式化时长毫秒(毫秒):
    '不足一秒用毫秒，否则用秒'
    if 毫秒<1000:
        return str(round(毫秒))+' 毫秒'
    小数=2 if 毫秒<10000 else 1
    return format(毫秒/1000,'.'+str(小数)+'f')+' 秒'

class 轨迹表:
    '分栏账本和可选的事件详情'
    def __init__(自身,属性):
        '记下属性与检查器状态'
        自身.属性=属性 or {}
        自身.选中身份=None
        自身.选中请求=None
        自身.活动标签='overview'
        自身.打开时折行=False
        自身.思考展开=None
        自身.详情宽=None
        自身.工具请求偏移=None
        自身.标签历史=['overview']
        自身.跟随表尾=False
        自身.表滚动就绪=False
        自身.更早加载中=False
        自身.待滚身份=None
        自身.已应用选择=None
        自身.已应用焦点=None
        自身.拖动=None
        自身.根=None
        自身.表板=None
        自身.渲染()

    def __call__(自身,属性=None):
        '属性变了就重画'
        if 属性 is not None:
            自身.属性=属性
        return 自身.渲染()

    def 渲染(自身):
        '画出账本和详情'
        属性=自身.属性
        窗口=属性['window']
        文档=窗口.document
        if 文档.getElementById('轨迹表样式') is None:
            样式=文档.createElement('style')
            样式.id='轨迹表样式'
            样式.textContent=样式文本
            文档.head.appendChild(样式)
        全部=展平记录(属性.get('turns') or [])
        流式表={}
        for 格 in 属性.get('streamingCells') or []:
            流式表[格.get('index')]=格
        def 当前(记录):
            '用流式格替换同下标的结构格'
            格=流式表.get(记录['cell'].get('index'))
            if 格 is None:
                return 记录
            拷贝=dict(记录)
            拷贝['cell']=格
            return 拷贝
        选择=属性.get('recordSelection')
        if isinstance(选择,dict) and 选择 is not 自身.已应用选择:
            自身.已应用选择=选择
            自身._选中(全部,选择.get('index'),属性)
            for 记录 in 全部:
                if 记录['cell'].get('index')==选择.get('index'):
                    自身.待滚身份=轨迹记录身份(记录['cell'])
                    break
        焦点=属性.get('recordFocus')
        if isinstance(焦点,dict) and 焦点 is not 自身.已应用焦点:
            自身.已应用焦点=焦点
            for 记录 in 全部:
                if 记录['cell'].get('index')==焦点.get('index'):
                    自身.待滚身份=轨迹记录身份(记录['cell'])
                    break
        巡检=属性.get('inspectCallId')
        if 巡检 is not None:
            for 记录 in 全部:
                if 记录['cell'].get('callId')==巡检:
                    自身._打开摘要(全部,记录,属性)
                    自身.待滚身份=轨迹记录身份(记录['cell'])
                    if callable(属性.get('onInspectApplied')):
                        属性['onInspectApplied']()
                    break
        请求组=set(请求键(项.get('turn'),项.get('group')) for 项 in 属性.get('requestNumbers') or [])
        边界=索引请求边界(全部,请求组)
        编号=索引请求编号(属性.get('requestNumbers'))
        命中=属性.get('searchMatchIndexes')
        if 命中 is not None:
            记录列表=过滤记录(全部,命中)
        else:
            收起轮=属性.get('collapsedTurns') or set()
            记录列表=全部 if len(收起轮)==0 else 折叠轮次记录(全部,收起轮,请求组)
            收起助=属性.get('collapsedAssistants') or set()
            if len(收起助)>0:
                记录列表=折叠助手记录(记录列表,收起助)
        虚拟=编组轨迹虚拟行(记录列表)
        开窗=属性.get('hasOlderRecords') is True or len(记录列表)>虚拟化阈值
        画出=记录列表
        if 开窗 and len(记录列表)>虚拟化阈值:
            画出=记录列表[:虚拟化阈值]
        选中=None
        for 记录 in 全部:
            if 自身.选中身份 is not None and 轨迹记录身份(记录['cell'])==自身.选中身份:
                选中=当前(记录)
                break
        选中请求信息=None
        if 自身.选中请求 is not None:
            for 请求 in 属性.get('requestNumbers') or []:
                if 请求身份(请求)==自身.选中请求.get('identity'):
                    选中请求信息=请求
                    break
        旧=自身.根
        父=None if 旧 is None else 旧.parentNode
        if 旧 is not None:
            旧.remove()
        根=文档.createElement('div')
        根.className='split'
        if 自身.工具请求偏移 is not None:
            根.style.setProperty('--trajectory-tool-request-width','calc(58cqw - '+str(自身.工具请求偏移)+'px)')
        板=文档.createElement('div')
        板.className='tablePane'
        板.setAttribute('data-trajectory-scroll','')
        def 滚动(事件):
            '靠近底部就跟随；靠近顶部就加载更早'
            面=事件.currentTarget
            高=面.scrollHeight or 0
            视=面.clientHeight or 0
            顶=面.scrollTop or 0
            自身.跟随表尾=高-视-顶<=底部跟随阈值
            if 属性.get('hasOlderRecords') is True and not 自身.更早加载中 and not 属性.get('olderHistoryLoading') and 顶<=更早加载阈值:
                自身._要更早(属性)
        板.addEventListener('scroll',滚动)
        if 属性.get('historyLoading') is True or not 自身.表滚动就绪:
            加载=文档.createElement('div')
            加载.className='historyLoading'
            加载.setAttribute('role','status')
            加载.setAttribute('aria-live','polite')
            条=文档.createElement('span')
            条.className='historyLoadingBar'
            状态点({'window':窗口,'state':'ongoing','parent':条}).渲染()
            条.appendChild(文档.createTextNode('正在加载轨迹…'))
            加载.appendChild(条)
            板.appendChild(加载)
            自身.表滚动就绪=not 属性.get('historyLoading')
        表=文档.createElement('table')
        表.className='table'
        if 自身.表滚动就绪:
            表.setAttribute('data-scroll-ready','true')
        体=文档.createElement('tbody')
        if 属性.get('hasOlderRecords') is True:
            行=文档.createElement('tr')
            行.className='historyLoadRow'
            行.setAttribute('data-history-load','')
            格元=文档.createElement('td')
            格元.colSpan=2
            忙=属性.get('olderHistoryLoading') is True or 自身.更早加载中
            钮=文档.createElement('button')
            钮.setAttribute('type','button')
            钮.className='historyLoadButton'
            钮.disabled=忙 or not callable(属性.get('onLoadOlder'))
            钮.setAttribute('aria-label','正在加载更早的历史…' if 忙 else '加载更早的历史')
            if 忙:
                状态点({'window':窗口,'state':'ongoing','parent':钮}).渲染()
            字=文档.createElement('span')
            字.setAttribute('aria-hidden','true')
            字.textContent='正在加载更早的历史…' if 忙 else '加载更早的历史'
            钮.appendChild(字)
            def 点更早(_事件):
                '按钮加载更早，不要求已经滚到顶'
                自身._要更早(属性)
            钮.addEventListener('click',点更早)
            格元.appendChild(钮)
            行.appendChild(格元)
            体.appendChild(行)
        游程=索引边界游程(记录列表,请求组)
        for 位,记录 in enumerate(画出):
            记录=当前(记录)
            体.appendChild(自身._行(文档,窗口,记录,位,全部,边界,编号,游程,属性,选中))
        表.appendChild(体)
        板.appendChild(表)
        根.appendChild(板)
        if 选中 is not None or 选中请求信息 is not None:
            根.appendChild(自身._详情(文档,窗口,选中,选中请求信息,全部,属性))
        自身.根=根
        自身.表板=板
        if 父 is None and 属性.get('parent') is not None:
            父=属性['parent']
        if 父 is not None and 根.parentNode is not 父:
            父.appendChild(根)
        if 自身.待滚身份 is not None and 自身.表滚动就绪:
            目标行=根.querySelector('tr[data-record-id="'+自身.待滚身份.replace('"','')+'"]') if hasattr(根,'querySelector') else None
            if 目标行 is not None and hasattr(目标行,'scrollIntoView'):
                目标行.scrollIntoView({'behavior':'smooth','block':'center'})
                自身.待滚身份=None
                自身.跟随表尾=False
        elif 自身.跟随表尾 and hasattr(板,'scrollTop'):
            板.scrollTop=板.scrollHeight or 0
        return 根

    def _要更早(自身,属性):
        '向宿主再要一页。调用是同步的'
        if 自身.更早加载中 or not callable(属性.get('onLoadOlder')):
            return
        自身.更早加载中=True
        try:
            属性['onLoadOlder']()
        finally:
            自身.更早加载中=False

    def _选中(自身,全部,下标,属性):
        '选中账本记录并挑最近用过的标签'
        if callable(属性.get('onRecordSelect')):
            属性['onRecordSelect'](下标)
        自身.选中请求=None
        记录=None
        for 项 in 全部:
            if 项['cell'].get('index')==下标:
                记录=项
                break
        自身.选中身份=None if 记录 is None else 轨迹记录身份(记录['cell'])
        if 记录 is None:
            return
        标签=详情标签(记录)
        可用=set(项['id'] for 项 in 标签)
        最近=None
        for 名 in reversed(自身.标签历史):
            if 名 in 可用:
                最近=名
                break
        自身.活动标签=最近 or (标签[0]['id'] if len(标签)>0 else 'overview')

    def _打开摘要(自身,全部,目标,属性):
        '必要时展开轮次和助手，再打开概述'
        if 目标.get('turn') is not None and 目标['turn'] in (属性.get('collapsedTurns') or set()):
            if callable(属性.get('onToggleTurn')):
                属性['onToggleTurn'](目标['turn'])
        if 目标['cell'].get('kind') in ('tool','subtool'):
            for 项 in reversed(全部):
                if 项['cell'].get('index')>=目标['cell'].get('index'):
                    continue
                if 项.get('turn')!=目标.get('turn'):
                    break
                if 项['cell'].get('kind')=='message':
                    标识=轨迹记录身份(项['cell'])
                    if 标识 in (属性.get('collapsedAssistants') or set()) and callable(属性.get('onToggleAssistant')):
                        属性['onToggleAssistant'](标识)
                    break
        自身.选中请求=None
        自身.选中身份=轨迹记录身份(目标['cell'])
        自身.活动标签='overview'

    def _行(自身,文档,窗口,记录,位,全部,边界,编号,游程,属性,选中):
        '一条账本行'
        格=记录['cell']
        收起=记录.get('collapsedSummary') is not None
        仅请求=格.get('requestOnly') is True
        键=请求键(记录['turn'],记录['group'])
        请求号=None
        if 边界.get(键)==格.get('index') and not 收起 and (记录['turn'] is None or 记录['turn'] not in (属性.get('collapsedTurns') or set())):
            请求号=编号.get(键)
        展示=记录展示文案(格)
        结果=记录结果文案(格)
        部件=工具文案部件(格,展示)
        if 仅工具调用(格):
            列表文案='（仅工具调用）'
        elif 部件 is None:
            列表文案=展示
        else:
            列表文案=' '.join(项 for 项 in (部件.get('name'),部件.get('args')) if 项)
        行=文档.createElement('tr')
        行.setAttribute('data-kind',格.get('kind') or '')
        行.setAttribute('data-trajectory-row-key',轨迹虚拟记录键(记录))
        if not 收起 and not 仅请求:
            行.setAttribute('data-record-index',str(格.get('index')))
            行.setAttribute('data-record-id',轨迹记录身份(格))
        if 仅请求:
            行.setAttribute('data-request-only','true')
        if 记录.get('groupStart'):
            行.setAttribute('data-group-start','true')
        if 记录.get('turnStart'):
            行.setAttribute('data-turn-start','true')
        if 格.get('isError') is True:
            行.setAttribute('data-error','true')
        if 记录状态(记录)=='running':
            行.setAttribute('data-running','true')
        if 记录.get('turnEnd'):
            行.setAttribute('data-turn-end','true')
        if 记录.get('collapsedSummaryKind') is not None:
            行.setAttribute('data-collapsed-summary',记录['collapsedSummaryKind'])
        if not 收起 and 选中 is not None and 选中['cell'].get('index')==格.get('index'):
            行.setAttribute('data-selected','true')
            行.setAttribute('aria-selected','true')
        焦点=属性.get('timelineFocusIndexes')
        if not 收起 and 焦点 is not None:
            行.setAttribute('data-timeline-focus','inside' if 格.get('index') in 焦点 else 'outside')
        if 收起:
            种类字='轮次' if 记录.get('collapsedSummaryKind')=='turn' else '助手'
            行.setAttribute('aria-label','已收起的'+种类字+'概述，'+(记录.get('collapsedSummary') or ''))
        elif 仅请求:
            行.setAttribute('aria-label','请求 '+str(请求号 or '')+'，压缩')
        else:
            前缀='' if 请求号 is None else '请求 '+str(请求号)+'，'
            行.setAttribute('aria-label',前缀+种类名.get(格.get('kind'),'')+'，'+(列表文案 or '无内容'))
        单个工具=格.get('kind')=='context' and isinstance(格.get('sourceBlocks'),list) and len(格['sourceBlocks'])==1 and 格['sourceBlocks'][0].get('type') in ('tool-addition','tool-removal')
        if not 仅请求 and not 单个工具:
            行.tabIndex=0
        def 点击(_事件,记录=记录,收起=收起):
            '选中记录，或展开收起的摘要'
            if 收起:
                if 记录.get('collapsedSummaryKind')=='turn' and 记录.get('turn') is not None and callable(属性.get('onToggleTurn')):
                    属性['onToggleTurn'](记录['turn'])
                elif callable(属性.get('onToggleAssistant')):
                    属性['onToggleAssistant'](轨迹记录身份(记录['cell']))
                return
            自身._选中(全部,记录['cell'].get('index'),属性)
            自身.渲染()
        if not 仅请求 and not 单个工具:
            行.addEventListener('click',点击)
        事件格=文档.createElement('td')
        事件格.className='event'
        if 请求号 is not None:
            钮=文档.createElement('button')
            钮.setAttribute('type','button')
            钮.className='requestBoundaryControl'
            标签='请求 #'+str(请求号)+(' · 压缩' if any(项.get('number')==请求号 and 项.get('purpose')=='compaction' for 项 in 属性.get('requestNumbers') or []) else '')
            钮.setAttribute('aria-label',标签)
            钮.setAttribute('data-label',标签)
            钮.style.setProperty('--request-boundary-offset',str((游程.get(格.get('index')) or 0)*8)+'px')
            def 开请求(事件,号=请求号):
                '打开请求检查器'
                事件.stopPropagation()
                for 项 in 属性.get('requestNumbers') or []:
                    if 项.get('number')==号:
                        自身.选中身份=None
                        自身.选中请求={'identity':请求身份(项)}
                        自身.活动标签='overview'
                        自身.渲染()
                        return
            钮.addEventListener('click',开请求)
            事件格.appendChild(钮)
        if not 收起 and not 仅请求:
            槽=文档.createElement('span')
            槽.className='kindSlot'
            标=文档.createElement('span')
            标.className='kindTag '+种类类.get(格.get('kind'),格.get('kind') or '')
            标.setAttribute('data-role-kind',格.get('kind') or '')
            图标=文档.createElement('span')
            图标.className='kindTagIcon'
            图标.setAttribute('aria-hidden','true')
            字=文档.createElement('span')
            字.className='kindTagLabel'
            字.textContent=种类名.get(格.get('kind'),'')
            标.appendChild(图标)
            标.appendChild(字)
            提示泡({'window':窗口,'label':种类名.get(格.get('kind'),''),'side':'right','children':图标,'parent':标}).渲染()
            槽.appendChild(标)
            内=文档.createElement('div')
            内.className='eventInner'
            内.appendChild(槽)
            事件格.appendChild(内)
        内容格=文档.createElement('td')
        内容格.className='content'
        if not 仅请求:
            if 收起:
                盒=文档.createElement('span')
                盒.className='collapsedTurnContent'
                盒.setAttribute('title',记录.get('collapsedSummary') or '')
                点=文档.createElement('span')
                点.className='collapsedTurnEllipsis'
                点.textContent='…'
                文=文档.createElement('span')
                文.className='collapsedTurnText'
                文.textContent=记录.get('collapsedSummary') or ''
                盒.appendChild(点)
                盒.appendChild(文)
                内容格.appendChild(盒)
            else:
                盒=文档.createElement('span')
                盒.className='contentText' if 结果 is None else 'resultPreview'
                盒.setAttribute('title',列表文案 if 结果 is None else 列表文案+' → '+结果)
                主=文档.createElement('span')
                if 结果 is not None:
                    主.className='resultRequest'
                主.textContent=列表文案
                盒.appendChild(主)
                if 结果 is not None:
                    果=文档.createElement('span')
                    果.className='inlineResult error' if 格.get('isError') is True else 'inlineResult'
                    箭=文档.createElement('span')
                    箭.className='arrow'
                    箭.textContent='→'
                    果文=文档.createElement('span')
                    果文.className='inlineResultText noOutputText' if 结果=='无输出' else 'inlineResultText'
                    果文.textContent=结果
                    果.appendChild(箭)
                    果.appendChild(果文)
                    盒.appendChild(果)
                内容格.appendChild(盒)
        行.appendChild(事件格)
        行.appendChild(内容格)
        return 行

    def _详情(自身,文档,窗口,选中,请求,全部,属性):
        '事件详情侧栏'
        侧=文档.createElement('aside')
        侧.className='details'
        侧.setAttribute('aria-label','事件详情')
        if 自身.详情宽 is not None:
            侧.style.width=str(自身.详情宽)+'px'
        头=文档.createElement('div')
        头.className='detailsHeader'
        题=文档.createElement('div')
        题.className='detailsTitle'
        if 请求 is not None:
            名=文档.createElement('span')
            名.className='requestDetailsName'
            名.textContent='请求 #'+str(请求.get('number') or '—')
            处=文档.createElement('span')
            处.className='detailsLocation'
            if 请求.get('purpose')=='compaction':
                处.textContent='压缩 · '+段落标签(请求.get('turn'))
            else:
                处.textContent=段落标签(请求.get('turn'))
            题.appendChild(名)
            题.appendChild(处)
        elif 选中 is not None:
            标=文档.createElement('span')
            标.className='kindTag '+种类类.get(选中['cell'].get('kind'),'')
            标.textContent=种类名.get(选中['cell'].get('kind'),'')
            处=文档.createElement('span')
            处.className='detailsLocation'
            if 选中['cell'].get('kind')=='compacted':
                处.textContent=段落标签(选中.get('turn'))
            else:
                处.textContent=段落标签(选中.get('turn'))+' · '+(选中.get('group') or '')
            题.appendChild(标)
            题.appendChild(处)
        关=文档.createElement('button')
        关.setAttribute('type','button')
        关.className='close'
        关.setAttribute('aria-label','关闭详情')
        关.textContent='×'
        def 关闭(_事件):
            '清掉检查器选中'
            自身.选中身份=None
            自身.选中请求=None
            if callable(属性.get('onClearSelection')):
                属性['onClearSelection']()
            自身.渲染()
        关.addEventListener('click',关闭)
        头.appendChild(题)
        头.appendChild(关)
        侧.appendChild(头)
        标签=请求标签 if 请求 is not None else (详情标签(选中) if 选中 is not None else [])
        if 请求 is not None and 请求.get('requestConfig') is None:
            标签=[项 for 项 in 标签 if 项['id']!='options']
        页=文档.createElement('div')
        页.className='detailTabs'
        页.setAttribute('role','tablist')
        页.setAttribute('aria-label','事件详情')
        for 项 in 标签:
            钮=文档.createElement('button')
            钮.setAttribute('type','button')
            钮.setAttribute('role','tab')
            钮.className='detailTab detailTabActive' if 自身.活动标签==项['id'] else 'detailTab'
            钮.setAttribute('aria-selected','true' if 自身.活动标签==项['id'] else 'false')
            钮.textContent=项['label']
            def 激活(_事件,标识=项['id'],折行=属性.get('stringWrapping')):
                '切换详情标签'
                if callable(折行) is False and isinstance(折行,dict) and callable(折行.get('getDefault')):
                    自身.打开时折行=折行['getDefault']() is True
                if 标识 in 自身.标签历史:
                    自身.标签历史.remove(标识)
                自身.标签历史.append(标识)
                自身.活动标签=标识
                自身.渲染()
            钮.addEventListener('click',激活)
            页.appendChild(钮)
        侧.appendChild(页)
        体=文档.createElement('div')
        体.className='detailBody'
        体.setAttribute('role','tabpanel')
        体.id='trajectory-detail-panel'
        if 请求 is not None and 自身.活动标签=='overview':
            表=文档.createElement('dl')
            表.className='overview'
            自身._项(文档,表,'状态',状态标签(请求.get('status') or 'complete'),请求.get('status')=='error')
            if 请求.get('purpose')=='compaction':
                自身._项(文档,表,'用途','压缩',False)
            if 请求.get('provider') is not None:
                自身._项(文档,表,'提供方',str(请求.get('provider')),False)
            if 请求.get('model') is not None:
                自身._项(文档,表,'模型',str(请求.get('model')),False)
            if 请求.get('error') is not None:
                题='上次尝试错误' if 请求.get('status')!='error' and 请求.get('retry') is not None else '错误'
                自身._项(文档,表,题,请求错误文案(请求) or '',请求.get('status')=='error')
            if 请求.get('retry') is not None:
                if 请求.get('maxRetries') is None:
                    重试文=str(请求.get('retry'))
                else:
                    重试文=str(请求.get('retry'))+'/'+str(请求.get('maxRetries'))
                自身._项(文档,表,'重试',重试文,False)
            if 请求.get('retryDelayMs') is not None:
                自身._项(文档,表,'重试延迟',格式化时长毫秒(请求['retryDelayMs']),False)
            体.appendChild(表)
        elif 选中 is not None and 自身.活动标签=='overview':
            表=文档.createElement('dl')
            表.className='overview'
            自身._项(文档,表,'状态',状态标签(记录状态(选中)),选中['cell'].get('isError') is True)
            if 选中['cell'].get('kind')=='message':
                自身._项(文档,表,'Token', '—' if 选中['cell'].get('output') is None else str(选中['cell'].get('output'))+' tok',False)
            if 选中['cell'].get('kind') in ('user','context','compacted','tool','subtool'):
                自身._项(文档,表,'时长',格式化已用秒数(选中['cell'].get('timeSeconds')),False)
            体.appendChild(表)
            原文=选中['cell'].get('outputDetail') or 选中['cell'].get('inputDetail') or 选中['cell'].get('text') or ''
            if 原文:
                Markdown文本({'window':窗口,'text':原文,'labels':文标签,'parent':体}).渲染()
        elif 选中 is not None and 自身.活动标签 in ('rendered','raw','system-prompt'):
            原文=选中['cell'].get('systemPromptDetail') or 选中['cell'].get('outputDetail') or 选中['cell'].get('inputDetail') or ''
            if 自身.活动标签=='raw':
                预=文档.createElement('pre')
                预.className='markdownPayload'
                预.textContent=原文
                体.appendChild(预)
            elif 原文=='' and 自身.活动标签=='system-prompt':
                空=文档.createElement('p')
                空.className='noPayload'
                空.textContent='本次请求没有系统提示词'
                体.appendChild(空)
            else:
                Markdown文本({'window':窗口,'text':原文,'labels':文标签,'parent':体}).渲染()
        elif 请求 is not None and 自身.活动标签=='options':
            if 请求.get('requestConfig') is None:
                空=文档.createElement('p')
                空.className='noPayload'
                空.textContent='未记录选项'
                体.appendChild(空)
            else:
                Json树({'window':窗口,'data':请求['requestConfig'],'stringWrapping':属性.get('stringWrapping'),'collapsedStringLines':12,'label':'请求选项 JSON','labels':树标签,'className':'jsonPayload','parent':体}).渲染()
        elif 选中 is not None and 自身.活动标签=='source':
            来源=选中['cell'].get('messageSource')
            if 来源 is None:
                空=文档.createElement('p')
                空.className='noPayload'
                空.textContent='未记录来源'
                体.appendChild(空)
            else:
                Json树({'window':窗口,'data':来源 if isinstance(来源,dict) else {'value':来源},'stringWrapping':属性.get('stringWrapping'),'collapsedStringLines':12,'label':'消息来源 JSON','labels':树标签,'className':'jsonPayload','parent':体}).渲染()
        elif 选中 is not None and 自身.活动标签 in ('input','output','schema'):
            if 自身.活动标签=='schema':
                原文=选中['cell'].get('schemaDetail')
                题='Schema 不可用' if not 原文 else None
            elif 自身.活动标签=='input':
                程序=代码程序(选中['cell'])
                原文=None if 程序 is None else 程序.get('source')
                if 原文 is None:
                    原文=选中['cell'].get('inputDetail')
                题=None if 原文 else '未捕获参数'
            else:
                原文=选中['cell'].get('outputDetail')
                题=None if 原文 else '未捕获结果'
            if 题 is not None:
                空=文档.createElement('p')
                空.className='noPayload'
                空.textContent=题
                体.appendChild(空)
            else:
                预=文档.createElement('pre')
                预.className='jsonPayload'
                预.textContent=原文
                体.appendChild(预)
        elif 选中 is not None and 自身.活动标签=='timing':
            表=文档.createElement('dl')
            表.className='overview'
            自身._项(文档,表,'时长',格式化已用秒数(选中['cell'].get('timeSeconds')),False)
            指标=选中['cell'].get('assistantMetrics')
            if isinstance(指标,dict):
                if 指标.get('timingRecorded') is not True:
                    总='未记录'
                elif 指标.get('stepStartTime') is None:
                    总='步骤开始时间不可用'
                elif 指标.get('completedTime') is None:
                    总='等待中'
                else:
                    总=格式化时长毫秒(max(0,指标['completedTime']-指标['stepStartTime']))
                自身._项(文档,表,'总时长',总,False)
            体.appendChild(表)
        侧.appendChild(体)
        return 侧

    def _项(自身,文档,表,名,值,错误):
        '概述里的一行'
        行=文档.createElement('div')
        题=文档.createElement('dt')
        题.textContent=名
        答=文档.createElement('dd')
        if 错误:
            答.className='error'
        答.textContent='' if 值 is None else str(值)
        行.appendChild(题)
        行.appendChild(答)
        表.appendChild(行)
