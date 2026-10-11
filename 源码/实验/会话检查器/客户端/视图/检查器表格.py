'会话日志和对话分组共用的虚拟原始数据表'

import math
import time
import datetime
from .表格模型 import 检查器表格层级,行已折叠
from .表格布局 import 检查器表格布局,行高
from .格式 import 检查器预览
from .原始json import 检查器json,未定义
from .类型筛选 import 检查器类型筛选
from .类型筛选器 import 类型筛选器
from .检查器详情 import 检查器详情
from .检查器对象树 import 检查器json树,检查器对象树

__all__=['检查器表格']

def 读(值,键,默认=None):
    '字典或对象上的字段'
    if 值 is None:
        return 默认
    if isinstance(值,dict):
        return 值.get(键,默认)
    return getattr(值,键,默认)

def 矩形字段(矩形,键):
    'DOMRect 或字典上的一个数'
    if isinstance(矩形,dict):
        return 矩形.get(键,0)
    return getattr(矩形,键)

def utc片段(毫秒):
    'UTC 的 HH:MM:SS.mmm'
    时刻=datetime.datetime.fromtimestamp(毫秒/1000,datetime.timezone.utc)
    return 时刻.strftime('%H:%M:%S.')+f'{时刻.microsecond//1000:03d}'

def 现在():
    '与 performance.now 同一量纲的毫秒'
    return time.perf_counter()*1000

def 默认范围提取(范围):
    'overscan 内的连续下标'
    if 范围['count']<=0:
        return []
    开始=max(范围['startIndex']-范围['overscan'],0)
    结束=min(范围['endIndex']+范围['overscan'],范围['count']-1)
    if 开始>结束:
        return []
    return list(range(开始,结束+1))

class 滚动宿主:
    '还没有真实滚动元素时的几何'
    def __init__(自身):
        '初始视口高 600'
        自身.scrollTop=0
        自身.clientHeight=600
        自身.clientTop=0
        自身.scrollHeight=0

    def getBoundingClientRect(自身):
        '与 clientHeight 一致的矩形'
        return {'top':0,'left':0,'width':0,'height':自身.clientHeight,'right':0,'bottom':自身.clientHeight}

class 虚拟器:
    '固定行高的视口窗口，对齐表格用到的 virtualizer 方法'
    def __init__(自身):
        '偏移和视口在第一次配置时按 anchorTo 摆放'
        自身.scrollOffset=0
        自身.scrollRect={'width':0,'height':600}
        自身.选项={}
        自身._已初始化=False

    def 配置(自身,选项):
        '换选项；只有第一次使用 anchorTo'
        自身.选项=选项
        if not 自身._已初始化:
            高度=读(选项.get('initialRect'),'height',600)
            自身.scrollRect={'width':0,'height':高度}
            if 选项.get('anchorTo')=='end':
                自身.scrollToEnd()
            自身._已初始化=True
        宿主=选项['getScrollElement']()
        if 宿主 is None:
            return
        高度=getattr(宿主,'clientHeight',None)
        if isinstance(高度,(int,float)) and not isinstance(高度,bool) and 高度>0:
            自身.scrollRect={'width':0,'height':高度}
        顶=getattr(宿主,'scrollTop',None)
        if isinstance(顶,(int,float)) and not isinstance(顶,bool):
            自身.scrollOffset=顶

    def _项开始(自身,下标):
        '含表头留白的起点'
        return 自身.选项.get('paddingStart',0)+下标*行高

    def getTotalSize(自身):
        '表头、行和底留白的总高'
        选项=自身.选项
        return 选项.get('paddingStart',0)+选项['count']*行高+选项.get('paddingEnd',0)

    def scrollToOffset(自身,偏移):
        '滚到绝对偏移，并写回宿主'
        自身.scrollOffset=max(0,偏移)
        取=自身.选项.get('getScrollElement')
        宿主=None if 取 is None else 取()
        if 宿主 is not None:
            宿主.scrollTop=自身.scrollOffset

    def scrollToEnd(自身):
        '贴到底部'
        自身.scrollToOffset(max(0,自身.getTotalSize()-自身.scrollRect['height']))

    def scrollToIndex(自身,下标,选项=None):
        '按对齐方式滚到一行'
        选项={} if 选项 is None else 选项
        开始=自身._项开始(下标)
        尺寸=自身.选项['estimateSize'](下标)
        视口=自身.scrollRect['height']
        if 选项.get('align')=='center':
            自身.scrollToOffset(开始-(视口-尺寸)/2)
        else:
            自身.scrollToOffset(开始)

    def _基础范围(自身):
        '当前偏移能看见的行下标'
        数量=自身.选项['count']
        起点=自身.选项.get('paddingStart',0)
        视口=自身.scrollRect['height']
        偏移=自身.scrollOffset
        超扫=自身.选项.get('overscan',0)
        if 数量<=0:
            return {'startIndex':0,'endIndex':-1,'overscan':超扫,'count':数量}
        开始=max(0,int((偏移-起点)/行高))
        结束=min(数量-1,math.ceil((偏移+视口-起点)/行高)-1)
        if 结束<开始:
            结束=开始
        return {'startIndex':开始,'endIndex':结束,'overscan':超扫,'count':数量}

    def getVirtualItems(自身):
        '范围提取器给出的虚拟行'
        索引=自身.选项['rangeExtractor'](自身._基础范围())
        项=[]
        for 下标 in 索引:
            始=自身._项开始(下标)
            尺寸=自身.选项['estimateSize'](下标)
            项.append({'key':自身.选项['getItemKey'](下标),'index':下标,'start':始,'end':始+尺寸,'size':尺寸})
        return 项

class 数据行:
    '一行的高亮动画；依赖不变则不重开'
    def __init__(自身):
        '元素和上一次记录都空着'
        自身.元素=None
        自身.先前记录=None
        自身.先前脉冲=0
        自身._见过=False
        自身._效果键=None
        自身.动画=None

    def 见(自身,记录):
        '对齐首次渲染时的 useRef 初值'
        if not 自身._见过:
            自身.先前记录=记录
            自身._见过=True

    def 跑效果(自身,记录,新增,闪,脉冲):
        '记录、新增或定位脉冲变化时闪一下'
        键=(id(记录) if 记录 is not None else None,新增,闪,脉冲)
        if 自身._效果键==键:
            return
        变了=自身.先前记录 is not 记录
        自身.先前记录=记录
        导航了=脉冲>0 and 自身.先前脉冲!=脉冲
        自身.先前脉冲=脉冲
        if 自身.动画 is not None:
            自身.动画.cancel()
            自身.动画=None
        if 自身.元素 is None:
            return
        自身._效果键=键
        if (not 闪 and not 导航了) or (not 变了 and not 新增 and not 导航了):
            return
        if window.matchMedia('(prefers-reduced-motion: reduce)').matches:
            return
        颜色=getComputedStyle(自身.元素).getPropertyValue('--dsw-specific-bubble-highlight')
        自身.动画=自身.元素.animate([{'backgroundColor':颜色},{'backgroundColor':'transparent'}],{'duration':700})

class 检查器表格:
    '分页层级、稳定虚拟行键，以及选中行的实时详情'
    def __init__(自身,属性):
        '默认跟着最新一行，详情高度留给详情面板自己'
        自身.属性=属性
        自身.失败=None
        自身.选中=None
        自身.对象历史=None
        自身.定位=None
        自身._已应用定位=None
        自身._已应用选取=None
        自身.展开={}
        自身.类型查询=''
        自身.滚动区=滚动宿主()
        自身.跟随='tail'
        自身.视口={'offset':0,'height':600}
        自身.展开锚=None
        自身.间距代=0
        自身._已提交=None
        自身._见到={}
        自身._行已初始化=False
        自身._到达={}
        自身._到达键=None
        自身._筛选=None
        自身._筛选查询=None
        自身._过滤=None
        自身._过滤键=None
        自身._层级=None
        自身._层级键=None
        自身._布局=None
        自身._布局键=None
        自身._全部行=()
        自身._行标=''
        自身.虚拟=虚拟器()
        自身.筛选器=None
        自身.详情=None
        自身._数据行={}
        自身._json树=None
        自身._json键=None
        自身._对象树=None
        自身._对象键=None
        自身._待滚动=None

    def 更新(自身,属性):
        '刷新 props；表格状态留在这一次挂载上'
        自身.属性=属性

    def _建议(自身,查询):
        '从全部已加载行取类型候选'
        return 检查器类型筛选(查询).建议(自身._全部行,自身.属性['typeOf'])

    def _定位聊天(自身,目标):
        '有导航时揭示目标；没有目标则揭示空坐标'
        导航=自身.属性.get('navigation')
        if 导航 is None:
            return
        导航['reveal']({} if 目标 is None else 目标)

    def _选择(自身,键):
        '选中一行，清掉对象历史，并揭示它在对话里的位置'
        自身.选中=键
        自身.对象历史=None
        导航=自身.属性.get('navigation')
        目标=None if 导航 is None else 导航['target'](键)
        自身._定位聊天(目标)

    def _定位行(自身,键):
        '必要时清掉筛选，展开祖先，并把这一行滚到中间'
        筛选=自身._筛选
        过滤=自身._过滤
        清筛选=筛选 is not None and 筛选.活动 and not any(行['key']==键 for 行 in 过滤['rows'])
        if 清筛选:
            自身.类型查询=''
            自身._筛选查询=None
        自身.跟随='scroll'
        自身.选中=键
        源=自身._全部行 if 清筛选 else 过滤['rows']
        按键={行['key']:行 for 行 in 源}
        下一=dict(自身.展开)
        父=按键[键].get('parent') if 键 in 按键 else None
        while 父 is not None:
            行=按键.get(父)
            if 行 is None:
                break
            下一[父]={'state':行.get('disclosure'),'collapsed':False}
            父=行.get('parent')
        自身.展开=下一
        脉冲=1 if 自身.定位 is None else 自身.定位['pulse']+1
        自身.定位={'key':键,'pulse':脉冲}

    def _切换(自身,行,元素):
        '手折一行，并用该行顶部当滚动锚'
        宿主=自身.滚动区
        自身.跟随='manual'
        行顶=矩形字段(元素.getBoundingClientRect(),'top')
        宿顶=矩形字段(宿主.getBoundingClientRect(),'top')
        自身.展开锚={'key':行['key'],'top':行顶-宿顶-宿主.clientTop}
        自身.视口['offset']=宿主.scrollTop
        自身.视口['height']=宿主.clientHeight
        下一=dict(自身.展开)
        下一[行['key']]={'state':行.get('disclosure'),'collapsed':not 行已折叠(行,自身.展开)}
        自身.展开=下一

    def _导航(自身,引用):
        '压入对象面包屑；有表格行时同时定位'
        先前=自身.对象历史
        自身.对象历史={
            'rootKey':自身.选中 if 先前 is None else 先前['rootKey'],
            'rootLabel':自身._行标 if 先前 is None else 先前['rootLabel'],
            'references':([] if 先前 is None else list(先前['references']))+[引用],
        }
        自身._定位聊天(引用.get('target'))
        if 引用.get('rowKey') is not None:
            自身._定位行(引用['rowKey'])

    def _回到(自身,下标):
        '退回面包屑的某一级'
        历史=自身.对象历史
        引用=None if 下标==0 else 历史['references'][下标-1]
        键=历史['rootKey'] if 下标==0 else (None if 引用 is None else 引用.get('rowKey'))
        if 下标==0:
            导航=自身.属性.get('navigation')
            目标=None if 导航 is None else 导航['target'](历史['rootKey'])
            自身.对象历史=None
        else:
            目标=None if 引用 is None else 引用.get('target')
            自身.对象历史={**历史,'references':历史['references'][:下标]}
        if 键 is not None:
            自身._定位行(键)
        自身._定位聊天(目标)

    def 应用筛选(自身,查询):
        '确认类型筛选后从顶部按滚动模式看结果'
        自身.跟随='scroll'
        自身.类型查询=检查器类型筛选(查询).查询
        自身._筛选查询=None
        自身.展开={}
        自身.间距代+=1
        自身.选中=None
        自身.对象历史=None
        自身.定位=None
        自身._待滚动=0
        if 自身.虚拟 is not None:
            自身.虚拟.scrollToOffset(0)

    def _最新(自身):
        '回到尾随最新行'
        自身.跟随='tail'
        自身.间距代+=1

    def _更早(自身):
        '加载上一页；失败记到表头下'
        自身.跟随='scroll'
        自身.失败=None
        结果=自身.属性['loadOlder']()
        if hasattr(结果,'捕获'):
            def 记下(错误):
                '把拒绝原因写成字符串'
                自身.失败=str(错误)
                return None
            结果.捕获(记下)

    def _滚动(自身,事件):
        '非手动模式下，离底部 40 像素内算尾随'
        当前=事件['currentTarget'] if isinstance(事件,dict) else 事件.currentTarget
        自身.视口['offset']=当前.scrollTop
        if 自身.跟随!='manual':
            剩余=当前.scrollHeight-当前.clientHeight-当前.scrollTop
            自身.跟随='tail' if 剩余<=40 else 'scroll'

    def _关闭(自身):
        '关掉详情和对象历史'
        自身.选中=None
        自身.对象历史=None

    def _记滚动区(自身,元素):
        '宿主交出真实滚动元素后换掉占位'
        if 元素 is not None:
            自身.滚动区=元素

    def _确保筛选(自身,全部行):
        '查询或行身份变了才重算筛选'
        if 自身._筛选 is None or 自身._筛选查询!=自身.类型查询:
            自身._筛选=检查器类型筛选(自身.类型查询)
            自身._筛选查询=自身.类型查询
            自身._过滤键=None
        键=(id(全部行),自身.属性.get('typeOf'),id(自身._筛选))
        if 自身._过滤键!=键:
            自身._过滤=自身._筛选.应用(全部行,自身.属性['typeOf'])
            自身._过滤键=键

    def _应用选取(自身):
        '新的选取行出现在表里时定位一次'
        选取=自身.属性.get('pickedRow')
        if 选取 is None or 自身._已应用选取 is 选取:
            return
        if not any(行['key']==选取['key'] for 行 in 自身._全部行):
            return
        自身._已应用选取=选取
        自身.对象历史=None
        自身._定位行(选取['key'])

    def _确保层级(自身):
        '可见行或展开选择变了才重建层级和布局'
        过滤行=自身._过滤['rows']
        层键=(id(过滤行),id(自身.展开))
        if 自身._层级键!=层键:
            自身._层级=检查器表格层级(过滤行,自身.展开)
            自身._层级键=层键
            自身._布局键=None
        布局键=(id(自身._层级),id(自身.展开),自身.间距代)
        if 自身._布局键!=布局键:
            提交=自身._已提交
            先前=None
            if 提交 is not None and 提交['disclosures'] is 自身.展开 and 提交['spacingGeneration']==自身.间距代:
                先前=提交['layout']
            自身._布局=检查器表格布局(自身._层级,先前,自身.视口,自身.展开锚)
            自身._布局键=布局键

    def _确保到达(自身,全部行):
        '第一次见到的行不算新增；之后 700 毫秒内算新增'
        if 全部行 is 自身._到达键:
            return
        此刻=现在()
        下一={}
        for 行 in 全部行:
            键=行['key']
            if 键 in 自身._见到:
                下一[键]=自身._见到[键]
            else:
                下一[键]=-math.inf if not 自身._行已初始化 else 此刻
        if len(全部行)>0:
            自身._行已初始化=True
        自身._见到=下一
        自身._到达=下一
        自身._到达键=全部行

    def _配置虚拟(自身,布局,锚偏移):
        '把范围提取器指到这一份布局'
        虚拟=自身.虚拟
        视口高=自身.视口['height']
        def 提取(范围,布局=布局,锚偏移=锚偏移,虚拟=虚拟,视口高=视口高):
            '锚定偏移时先按该偏移算可见行，再并上吸顶行'
            偏移=虚拟.scrollOffset if 锚偏移 is None else 锚偏移
            if 锚偏移 is None:
                可见=范围
            else:
                可见={'startIndex':max(0,math.floor(偏移/行高)-1),'endIndex':min(范围['count']-1,math.ceil((偏移+视口高)/行高)-1),'overscan':范围['overscan'],'count':范围['count']}
            合并=[]
            见过=set()
            for 下标 in list(布局.偏移处吸顶下标(偏移))+默认范围提取(可见):
                if 下标 not in 见过:
                    见过.add(下标)
                    合并.append(下标)
            合并.sort()
            return 合并
        def 键于(下标,布局=布局):
            '布局项的行键'
            return 布局.项[下标]['key']
        def 尺寸于(下标,布局=布局):
            '布局项的行高'
            return 布局.项[下标]['size']
        虚拟.配置({
            'count':len(布局.项),
            'getScrollElement':lambda:自身.滚动区,
            'estimateSize':尺寸于,
            'getItemKey':键于,
            'overscan':12,
            'initialRect':{'width':0,'height':600},
            'anchorTo':'start' if 布局.滚动偏移 is not None or 自身.跟随=='manual' else 'end',
            'scrollEndThreshold':40,
            'paddingStart':行高,
            'scrollPaddingStart':行高,
            'rangeExtractor':提取,
            'paddingEnd':布局.底内边距,
        })

    def _摆放(自身,布局,锚偏移):
        '布局效果：锚点优先，否则尾随且没有底留白时贴底'
        虚拟=自身.虚拟
        if 自身._待滚动 is not None:
            虚拟.scrollToOffset(自身._待滚动)
            自身._待滚动=None
        if 锚偏移 is not None:
            虚拟.scrollToOffset(锚偏移)
        elif 自身.跟随=='tail' and 布局.底内边距==0:
            虚拟.scrollToEnd()
        自身.视口['offset']=getattr(自身.滚动区,'scrollTop',0)
        自身.视口['height']=虚拟.scrollRect.get('height',600)
        自身.展开锚=None
        自身._已提交={'layout':布局,'disclosures':自身.展开,'spacingGeneration':自身.间距代}
        if 自身.定位 is not None and 自身._已应用定位 is not 自身.定位:
            下标=-1
            for 序号,项 in enumerate(布局.项):
                if 项['key']==自身.定位['key']:
                    下标=序号
                    break
            if 下标!=-1:
                虚拟.scrollToIndex(下标,{'align':'center'})
                自身._已应用定位=自身.定位

    def _一行(自身,条目,吸顶级,翻译,闪,显示时间):
        '一行的记录、摘要和点击'
        行=条目['row']
        记录=自身.属性['useRecord'](行['key'])
        折叠=行已折叠(行,自身.展开)
        到达=自身._到达[行['key']]
        新增=现在()-到达<700
        脉冲=自身.定位['pulse'] if 自身.定位 is not None and 自身.定位['key']==行['key'] else 0
        行件=自身._数据行.get(行['key'])
        if 行件 is None:
            行件=数据行()
            自身._数据行[行['key']]=行件
        行件.见(记录)
        if 行件.元素 is not None:
            行件.跑效果(记录,新增,闪,脉冲)
        if 折叠 and 记录 is not None and 记录.get('collapsedSummary') is not None:
            摘要=记录.get('collapsedSummary')
        elif 记录 is not None and 记录.get('summary') is not None:
            摘要=记录.get('summary')
        else:
            摘要=检查器预览(None if 记录 is None else 记录.get('value'))
        上下文行=自身._筛选.活动 and 行['key'] not in 自身._过滤['matches']
        类名=[]
        if 行['key']==自身.选中:
            类名.append('selected')
        if 吸顶级 is not None:
            类名.append('sticky')
        if 上下文行:
            类名.append('contextRow')
        def 记(元素,行件=行件,记录=记录,新增=新增,闪=闪,脉冲=脉冲):
            '元素到达后再跑高亮'
            行件.元素=元素
            if 元素 is not None:
                行件.跑效果(记录,新增,闪,脉冲)
        def 点折(行=行):
            '折起或展开这一行'
            自身._切换(行,行件.元素)
        def 点选(键=行['key']):
            '选中这一行'
            自身._选择(键)
        格=[
            {'type':'td','className':'identity','children':[{'type':'Tooltip','label':'' if 记录 is None else (记录.get('identity') or ''),'side':'right','portal':True,'children':{'type':'span','className':'identityText','tabIndex':0,'text':None if 记录 is None else 记录.get('identity')}}]},
            {'type':'td','style':{'paddingInlineStart':8+行['depth']*20},'children':[
                None if not 自身._层级.是分支(行['key']) else {'type':'button','className':'disclosure','aria-label':翻译('table.expand') if 折叠 else 翻译('table.collapse'),'aria-expanded':not 折叠,'text':'▸' if 折叠 else '▾','onClick':点折},
                {'type':'button','className':'record','text':None if 记录 is None else 记录.get('type'),'onClick':点选},
            ]},
            {'type':'td','text':None if 记录 is None else 记录.get('location')},
        ]
        if 显示时间:
            时刻=None if 记录 is None else 记录.get('time')
            格.append({'type':'td','text':'' if 时刻 is None else utc片段(时刻)})
        格.append({'type':'td','children':[{'type':'button','className':'preview','text':摘要,'onClick':点选}]})
        return {
            'type':'tr',
            'key':行['key'],
            'ref':记,
            'aria-selected':行['key']==自身.选中,
            'data-inspector-context':'' if 上下文行 else None,
            'title':翻译('filter.context') if 上下文行 else None,
            'className':' '.join(类名),
            'style':None if 吸顶级 is None else {'top':(吸顶级+1)*行高,'zIndex':9-吸顶级},
            'cells':格,
        }

    def _详情(自身,记录,翻译):
        '选中行的原文或对象树'
        if 自身.选中 is None:
            if 自身._对象树 is not None:
                自身._对象树.拆除()
                自身._对象树=None
                自身._对象键=None
            自身.详情=None
            return None
        对象表=自身.属性.get('objects')
        if 对象表 is not None:
            详情=检查器json()
        elif 记录 is None or 'value' not in 记录:
            详情=检查器json()
        else:
            详情=检查器json(记录['value'] if 记录['value'] is not 未定义 else 未定义)
        if 记录 is None:
            文本=翻译('table.removed')
        elif 详情['failed']:
            文本=翻译('table.rawError')+'\n'+详情['text']
        else:
            文本=详情['text']
        对象目标=None if 自身.对象历史 is None or len(自身.对象历史['references'])==0 else 自身.对象历史['references'][-1]
        if 对象目标 is not None:
            详情值=对象目标['read']()
        elif 记录 is None or 'value' not in 记录:
            详情值=未定义
        else:
            详情值=记录['value']
        子=None
        if 对象表 is None:
            if 记录 is not None and not 详情['failed']:
                if 自身._json树 is None or 自身._json键!=自身.选中:
                    自身._json树=检查器json树({'text':详情['text'],'t':翻译})
                    自身._json键=自身.选中
                else:
                    自身._json树.更新({'text':详情['text'],'t':翻译})
                子=自身._json树.渲染()
        else:
            屑=[自身.对象历史['rootLabel'] if 自身.对象历史 is not None else 自身._行标]
            if 自身.对象历史 is not None:
                for 引用 in 自身.对象历史['references']:
                    屑.append(f"{翻译('object.'+引用['kind'])} · {引用['identity']}")
            项=[]
            末=len(屑)-1
            for 下标,标签 in enumerate(屑):
                def 点(下标=下标):
                    '退回这一级'
                    自身._回到(下标)
                项.append({'type':'li','key':下标,'children':[
                    None if 下标==0 else {'type':'span','aria-hidden':True,'text':'›'},
                    {'type':'button','title':标签,'text':标签,'disabled':下标==末,'aria-current':'page' if 下标==末 else None,'onClick':点},
                ]})
            树键=自身.选中 if 对象目标 is None or 对象目标.get('id') is None else 对象目标['id']
            树属性={'value':详情值,'objects':对象表,'navigate':自身._导航,'t':翻译}
            if 自身._对象树 is None or 自身._对象键!=树键:
                if 自身._对象树 is not None:
                    自身._对象树.拆除()
                自身._对象树=检查器对象树(树属性)
                自身._对象键=树键
            else:
                自身._对象树.更新(树属性)
            子={'type':'fragment','children':[
                {'type':'nav','className':'objectBreadcrumbs','aria-label':翻译('object.navigation'),'children':[{'type':'ol','children':项}]},
                自身._对象树.渲染(),
            ]}
        详情属性={'text':文本,'failed':详情['failed'],'children':子,'close':自身._关闭,'t':翻译}
        if 自身.详情 is None:
            自身.详情=检查器详情(详情属性)
        else:
            自身.详情.更新(详情属性)
        return 自身.详情.渲染()

    def 渲染(自身):
        '工具条、虚拟表和选中详情'
        属性=自身.属性
        翻译=属性['t']
        全部行=属性['useRows'](lambda 值:值)
        自身._全部行=全部行
        还有=属性['useSession'](lambda 值:读(值,'hasMore'))
        加载中=属性['useSession'](lambda 值:读(值,'loadingOlder'))
        打开错误=属性['useSession'](lambda 值:读(值,'openError'))
        自身._确保到达(全部行)
        自身._确保筛选(全部行)
        自身._应用选取()
        自身._确保筛选(全部行)
        自身._确保层级()
        布局=自身._布局
        锚偏移=None if 自身._已提交 is not None and 自身._已提交['layout'] is 布局 else 布局.滚动偏移
        自身._配置虚拟(布局,锚偏移)
        自身._摆放(布局,锚偏移)
        自身._配置虚拟(布局,None)
        项表=自身.虚拟.getVirtualItems()
        粘下标=布局.偏移处吸顶下标(自身.虚拟.scrollOffset)
        粘={}
        for 级,下标 in enumerate(粘下标):
            粘[下标]=级
        末项=None if len(项表)==0 else 项表[-1]
        底=0 if 末项 is None else max(0,自身.虚拟.getTotalSize()-末项['end'])
        记录=属性['useRecord']('' if 自身.选中 is None else 自身.选中)
        类型='' if 记录 is None or 记录.get('type') is None else 记录.get('type')
        身份=自身.选中 if 记录 is None or 记录.get('identity') is None else 记录.get('identity')
        自身._行标=f'{类型} · {身份}'
        列数=5 if 属性['showTime'] else 4
        闪=属性['flash']
        显示时间=属性['showTime']
        行块=[]
        for 位置,项 in enumerate(项表):
            上端=行高 if 位置==0 else 项表[位置-1]['end']
            间隙=项['start']-上端
            条目=布局.项[项['index']]
            块={'key':项['key']}
            if 间隙>0:
                块['gap']={'type':'tr','aria-hidden':True,'cells':[{'type':'td','colSpan':列数,'style':{'height':间隙,'padding':0}}]}
            块['row']=自身._一行(条目,粘.get(项['index']),翻译,闪,显示时间)
            行块.append(块)
        底行=None
        if 底>0:
            底行={'type':'tr','aria-hidden':True,'data-inspector-fold-space':'' if 布局.底内边距>0 else None,'cells':[{'type':'td','colSpan':列数,'style':{'height':底,'padding':0}}]}
        数量=f"{len(自身._过滤['matches'])} / {len(全部行)}" if 自身._筛选.活动 else str(len(全部行))
        筛选属性={'value':自身.类型查询,'suggest':自身._建议,'apply':自身.应用筛选,'t':翻译}
        if 自身.筛选器 is None:
            自身.筛选器=类型筛选器(筛选属性)
        else:
            自身.筛选器.更新(筛选属性)
        错误文=自身.失败
        if 错误文 is None and 打开错误 is not None:
            错误文=读(打开错误,'message')
        表头=[{'className':'idColumn','text':翻译('table.id')},{'className':'typeColumn','children':[{'type':'span','className':'typeHeader','text':翻译('table.type'),'filter':自身.筛选器.渲染()}]},{'className':'locationColumn','text':翻译('table.location')}]
        if 显示时间:
            表头.append({'className':'timeColumn','text':翻译('table.time')})
        表头.append({'text':翻译('table.data')})
        return {
            'type':'section',
            'className':'root',
            'cssModule':'检查器.module.css',
            'aria-label':属性['title'],
            'toolbar':{
                'className':'toolbar',
                'title':属性.get('modeSelector',属性['title']),
                'count':数量,
                'older':None if not 还有 else {'type':'button','disabled':加载中,'text':翻译('table.loading') if 加载中 else 翻译('table.older'),'onClick':自身._更早},
                'latest':{'type':'button','text':翻译('table.latest'),'onClick':自身._最新},
            },
            'notice':None if 属性.get('notice') is None else {'className':'pickNotice','role':'status','text':属性['notice']},
            'alert':None if 错误文 is None else {'type':'p','role':'alert','text':错误文},
            'scroller':{
                'ref':自身._记滚动区,
                'className':'scroller',
                'onScroll':自身._滚动,
                'table':{
                    'className':'table',
                    'aria-label':属性['title'],
                    'aria-rowcount':len(布局.层级.行)+1,
                    'head':表头,
                    'rows':行块,
                    'bottom':底行,
                },
                'empty':None if len(布局.层级.行)!=0 else {'type':'p','className':'empty','text':翻译('table.empty')},
            },
            'details':自身._详情(记录,翻译),
        }

    def __call__(自身,属性=None):
        '对齐 React 调用'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()
