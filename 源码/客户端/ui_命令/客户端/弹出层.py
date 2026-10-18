from ...ui_基础界面组件.按名排序 import 按名排序
from ...存储 import 创建快照存储
from .选项组 import 分组选项

__all__=['过滤选项','等返回','弹出选定控制器']

关闭态={
    'open':False,
    'command':None,
    'status':'pending',
    'options':(),
    'search':'',
    'searchLabels':None,
    'searchMode':'substring',
    'active':0,
    'submitting':False,
    'confirming':None,
    'acknowledged':False,
    'error':None,
}

def 等返回(值):
    '上游 await 的同步等待。对象带等待方法就等它交回结果'
    等待=getattr(值,'等待',None)
    if callable(等待):
        return 等待()
    return 值

def 错误文本(错误):
    '失败条上的一行。异常取消息，其余转成字符串'
    if isinstance(错误,BaseException):
        return str(错误)
    return str(错误)

def 过滤选项(选项表,搜索,模式='substring'):
    '空搜索保留分组顺序。子串匹配标签和说明；fuzzy-label 在每组内按名称排序'
    查询=搜索.strip().lower()
    组表=分组选项(选项表)
    有组=False
    for 组 in 组表:
        if 组['group'] is not None:
            有组=True
            break
    if 有组:
        有序=[]
        for 组 in 组表:
            有序.extend(组['rows'])
    else:
        有序=list(选项表)
    if 查询=='':
        return 有序
    if 模式=='fuzzy-label':
        结果=[]
        for 组 in 组表:
            包装=[]
            for 行 in 组['rows']:
                包装.append({'name':行['label'],'option':行})
            for 行 in 按名排序(包装,查询):
                结果.append(行['option'])
        return 结果
    留下=[]
    for 行 in 有序:
        命中=查询 in 行['label'].lower()
        if 命中 is False and 'detail' in 行 and 行['detail'] is not None:
            命中=查询 in 行['detail'].lower()
        if 命中:
            留下.append(行)
    return 留下

class 中止信号:
    '一次弹出拉取的取消通道。页面回调认 aborted 和 abort 监听'
    def __init__(自身):
        '还没取消'
        自身.aborted=False
        自身.reason=None
        自身._监听=[]

    def addEventListener(自身,类型,回调,选项=None):
        '只听 abort。已经取消就立刻回调'
        if 类型!='abort':
            return
        if 自身.aborted:
            回调()
            return
        自身._监听.append(回调)

    def removeEventListener(自身,类型,回调):
        '摘掉这个 abort 监听'
        if 类型!='abort':
            return
        if 回调 in 自身._监听:
            自身._监听.remove(回调)

    def _触发(自身,原因):
        '标记取消并通知监听'
        if 自身.aborted:
            return
        自身.aborted=True
        if isinstance(原因,BaseException):
            自身.reason=原因
        else:
            自身.reason=Exception('The operation was aborted')
        副本=list(自身._监听)
        自身._监听=[]
        for 回调 in 副本:
            回调()

class 中止控制器:
    '发出取消的控制器'
    def __init__(自身):
        '创建配套信号'
        自身.signal=中止信号()

    def abort(自身):
        '取消配套信号'
        自身.signal._触发(None)

class 弹出选定控制器:
    '一场会话的弹出壳。晚到的拉取和结算对不上当前绑定时什么都不写'
    def __init__(自身,依赖):
        '记下消费令牌和还焦，并播种关闭态'
        自身.依赖=依赖
        自身.state=创建快照存储(dict(关闭态))
        自身.绑定=None

    def open(自身,命令,规格,上下文,片段):
        '打开壳，中止上一次拉取，并按这次规格拉一次选项'
        取文案=规格['searchLabels'] if 'searchLabels' in 规格 else None
        if callable(取文案):
            搜索文案=取文案()
        else:
            搜索文案=None
        if 自身.绑定 is not None:
            自身.绑定['abort'].abort()
        绑定={
            'command':命令,
            'spec':规格,
            'context':上下文,
            'segment':片段,
            'abort':中止控制器(),
        }
        自身.绑定=绑定
        下一=dict(关闭态)
        下一['open']=True
        下一['command']=命令
        下一['searchLabels']=搜索文案
        if 'searchMode' in 规格 and 规格['searchMode'] is not None:
            下一['searchMode']=规格['searchMode']
        自身.state.set(下一)
        自身._装载(绑定)

    def _装载(自身,绑定):
        '同一次打开只拉一次。绑定已经换过就丢掉结果'
        try:
            选项=等返回(绑定['spec']['options'](绑定['context'],绑定['abort'].signal))
        except Exception as 错误:
            if 自身.绑定 is not 绑定:
                return
            print('[ui-commands] popupSelect options failed for /'+str(绑定['command'])+':',错误)
            当前=dict(自身.state.getSnapshot())
            当前['status']='failed'
            当前['options']=[]
            当前['active']=0
            当前['error']=错误文本(错误)
            自身.state.set(当前)
            return
        if 自身.绑定 is not 绑定:
            return
        当前=dict(自身.state.getSnapshot())
        行表=过滤选项(选项,当前['search'],当前['searchMode'])
        下标=0
        活跃=0
        找到=False
        for 行 in 行表:
            if 行.get('active') is True:
                活跃=下标
                找到=True
                break
            下标+=1
        if 找到 is False:
            活跃=0
        当前['status']='ready'
        当前['options']=选项
        当前['active']=活跃
        当前['error']=None
        自身.state.set(当前)

    def retry(自身):
        '失败后再拉一次。搜索文字保留'
        绑定=自身.绑定
        态=自身.state.getSnapshot()
        if 绑定 is None or 态['open'] is not True or 态['status']!='failed':
            return
        下一=dict(态)
        下一['status']='pending'
        下一['error']=None
        自身.state.set(下一)
        自身._装载(绑定)

    def setSearch(自身,搜索):
        '只改本地过滤文字，并把高亮放回过滤结果的第一行'
        态=自身.state.getSnapshot()
        if 态['open'] is not True or 态['submitting'] is True or 态['confirming'] is not None or 搜索==态['search']:
            return
        下一=dict(态)
        下一['search']=搜索
        下一['active']=0
        自身.state.set(下一)

    def move(自身,方向):
        '在过滤后的行之间循环移动高亮'
        态=自身.state.getSnapshot()
        if 态['open'] is not True or 态['status']!='ready' or 态['submitting'] is True or 态['confirming'] is not None:
            return
        行表=过滤选项(态['options'],态['search'],态['searchMode'])
        if len(行表)==0:
            return
        下一=dict(态)
        下一['active']=(态['active']+方向+len(行表))%len(行表)
        自身.state.set(下一)

    def highlight(自身,下标):
        '指针悬停直接指定高亮'
        态=自身.state.getSnapshot()
        if 态['open'] is not True or 态['status']!='ready' or 态['submitting'] is True or 态['confirming'] is not None:
            return
        行数=len(过滤选项(态['options'],态['search'],态['searchMode']))
        if 下标<0 or 下标>=行数 or 下标==态['active']:
            return
        下一=dict(态)
        下一['active']=下标
        自身.state.set(下一)

    def select(自身,下标):
        '有风险确认就先停在确认，否则结算这一行'
        绑定=自身.绑定
        态=自身.state.getSnapshot()
        if 绑定 is None or 态['open'] is not True or 态['status']!='ready' or 态['submitting'] is True or 态['confirming'] is not None:
            return
        行表=过滤选项(态['options'],态['search'],态['searchMode'])
        if 下标<0 or 下标>=len(行表):
            return
        选项=行表[下标]
        if 'confirmation' in 选项 and 选项['confirmation'] is not None:
            下一=dict(态)
            下一['confirming']=选项
            下一['acknowledged']=False
            下一['error']=None
            自身.state.set(下一)
            return
        自身._结算(绑定,选项)

    def acknowledge(自身,已认):
        '记下风险勾选'
        态=自身.state.getSnapshot()
        if 态['open'] is not True or 态['submitting'] is True or 态['confirming'] is None or 态['acknowledged'] is 已认:
            return
        下一=dict(态)
        下一['acknowledged']=已认
        自身.state.set(下一)

    def cancelConfirmation(自身):
        '取消风险门，回到仍开着的选项列表'
        态=自身.state.getSnapshot()
        if 态['open'] is not True or 态['submitting'] is True or 态['confirming'] is None:
            return
        下一=dict(态)
        下一['confirming']=None
        下一['acknowledged']=False
        自身.state.set(下一)

    def confirm(自身):
        '勾选之后才结算被拦住的那一行'
        绑定=自身.绑定
        态=自身.state.getSnapshot()
        if 绑定 is None or 态['open'] is not True or 态['submitting'] is True or 态['confirming'] is None or 态['acknowledged'] is not True:
            return
        自身._结算(绑定,态['confirming'])

    def _结算(自身,绑定,选项):
        '业务选中成功后消费草稿并关闭。失败留在卡片上'
        态=自身.state.getSnapshot()
        if 自身.绑定 is not 绑定 or 态['open'] is not True or 态['submitting'] is True:
            return
        下一=dict(态)
        下一['submitting']=True
        下一['confirming']=None
        下一['acknowledged']=False
        下一['error']=None
        自身.state.set(下一)
        try:
            等返回(绑定['spec']['onSelect'](选项,绑定['context']))
        except Exception as 错误:
            print('[ui-commands] popupSelect onSelect failed for /'+str(绑定['command'])+':',错误)
            if 自身.绑定 is not 绑定:
                return
            当前=dict(自身.state.getSnapshot())
            当前['submitting']=False
            当前['error']=错误文本(错误)
            自身.state.set(当前)
            return
        if 自身.绑定 is not 绑定:
            return
        自身.依赖['consume'](绑定['segment'])
        自身.绑定=None
        自身.state.set(dict(关闭态))
        自身.依赖['focusComposer']()

    def dismiss(自身,选项=None):
        '关掉壳并取消在途拉取。Escape 可以再把焦点还给编写器'
        if 自身.绑定 is None:
            return
        自身.绑定['abort'].abort()
        自身.绑定=None
        自身.state.set(dict(关闭态))
        if isinstance(选项,dict) and 选项.get('focusComposer') is True:
            自身.依赖['focusComposer']()

    def dispose(自身):
        '会话拆除：取消在途工作并清掉状态，不移动焦点'
        if 自身.绑定 is not None:
            自身.绑定['abort'].abort()
        自身.绑定=None
        自身.state.set(dict(关闭态))
