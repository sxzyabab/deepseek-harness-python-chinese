'一份会话的回合/步骤时间线和事件到位置的索引'
from ...异常 import 对话错误

__all__=['会话位置索引']

会话位置={'kind':'session'}
未解析位置={'kind':'unresolved'}

def 安全非负整数(值):
    '非布尔的非负整数'
    return isinstance(值,int) and not isinstance(值,bool) and 值>=0

def 载荷坐标(事件):
    '事件数据里显式的回合和步骤。turn 为 null 表示会话级'
    数据=事件.get('data') if isinstance(事件.get('data'),dict) else {}
    if 数据.get('turn') is None and 'turn' in 数据:
        return {'session':True,'location':None}
    回合=数据.get('turn') if 安全非负整数(数据.get('turn')) else None
    步=数据.get('step') if 安全非负整数(数据.get('step')) else None
    if 回合 is None:
        if 步 is None:
            return {'location':None}
        return {'step':步,'location':None}
    if 步 is None:
        return {'turn':回合,'location':None}
    return {'turn':回合,'step':步,'location':None}

def 同引用(左,右):
    '逐项是同一对象'
    if len(左)!=len(右):
        return False
    下标=0
    while 下标<len(左):
        if 左[下标] is not 右[下标]:
            return False
        下标+=1
    return True

def 同步骤(左,右):
    '起止、状态和数据存储都没变'
    return 左 is not None and 左.get('start') is 右.get('start') and 左.get('end') is 右.get('end') and 左.get('status')==右.get('status') and 左.get('data') is 右.get('data')

def 同回合(左,右):
    '起止、状态、数据存储和步骤列表都没变'
    return 左 is not None and 左.get('start') is 右.get('start') and 左.get('end') is 右.get('end') and 左.get('status')==右.get('status') and 左.get('data') is 右.get('data') and 同引用(左.get('steps') or [],右.get('steps') or [])

def 同位置(左,右):
    '两种位置指向同一回合或同一步'
    if 左 is None or 右 is None or 左.get('kind')!=右.get('kind'):
        return 左 is 右
    if 左['kind'] in ('session','unresolved'):
        return True
    if 右['kind'] in ('session','unresolved'):
        return False
    if 左['kind']=='turn' or 右['kind']=='turn':
        return 左['kind']=='turn' and 右['kind']=='turn' and 左['turn']==右['turn']
    return 左.get('turn')==右.get('turn') and 左.get('step')==右.get('step')

def 步骤数据键(回合,步):
    '步骤数据存储的键'
    return str(回合)+':'+str(步)

def 要求步骤(数据):
    '步骤数据必须带步骤号'
    if 数据.get('kind')=='step' and 数据.get('step') is not None:
        return 数据['step']
    raise 对话错误('conversation Step data "'+str(数据.get('key'))+'" requires a step')

class 可变位置数据存储:
    '一份回合或步骤上、按键存放的位置数据'
    def __init__(自身,标脏):
        '记下把本存储标脏的回调'
        自身.标脏回调=标脏
        自身.条目={}
        自身.源={}
        自身.脏键=set()

    def get(自身,键):
        '读当前值'
        项=自身.条目.get(键)
        if 项 is None:
            return None
        return 项['value']

    def source(自身,键):
        '这个键的可观察源'
        已有=自身.源.get(键)
        if 已有 is not None:
            return 已有
        监听=set()
        源={'published':自身.get(键)}
        def 取快照():
            '读存储里的当前值'
            return 自身.get(键)
        def 订阅(回调):
            '登记并返回退订'
            监听.add(回调)
            def 退订():
                '拿掉这个监听'
                监听.discard(回调)
            return 退订
        def 发布():
            '值变了才通知'
            下一=取快照()
            if 源['published'] is 下一:
                return
            源['published']=下一
            for 回调 in list(监听):
                回调()
        源['getSnapshot']=取快照
        源['subscribe']=订阅
        源['publish']=发布
        自身.源[键]=源
        return 源

    def remove(自身,所有者,键):
        '只有所有者自己能删'
        当前=自身.条目.get(键)
        if 当前 is None or 当前['owner']!=所有者:
            return False
        del 自身.条目[键]
        自身.变更(键)
        return True

    def set(自身,所有者,键,值):
        '值没变不标脏。别人已经占了这个键就失败'
        当前=自身.条目.get(键)
        if 当前 is not None and 当前['owner']!=所有者:
            raise 对话错误('conversation Location data "'+键+'" is already owned by '+当前['owner'])
        if 当前 is not None and 当前['value'] is 值:
            return False
        自身.条目[键]={'owner':所有者,'value':值}
        自身.变更(键)
        return True

    def replace(自身,条目):
        '整表替换。所有者和值都没变就不发布'
        变更键=[]
        键集=set(自身.条目.keys())
        键集.update(条目.keys())
        for 键 in 键集:
            当前=自身.条目.get(键)
            下一=条目.get(键)
            当前所有者=None if 当前 is None else 当前['owner']
            下一所有者=None if 下一 is None else 下一['owner']
            当前值=None if 当前 is None else 当前['value']
            下一值=None if 下一 is None else 下一['value']
            if 当前所有者!=下一所有者 or 当前值 is not 下一值:
                变更键.append(键)
        if len(变更键)==0:
            return False
        自身.条目=dict(条目)
        for 键 in 变更键:
            自身.变更(键)
        return True

    def publish(自身):
        '把已提交的键发给各自的源'
        脏=list(自身.脏键)
        自身.脏键.clear()
        for 键 in 脏:
            源=自身.源.get(键)
            if 源 is not None:
                源['publish']()

    def 变更(自身,键):
        '记下脏键并通知外层'
        自身.脏键.add(键)
        自身.标脏回调(自身)

class 会话位置索引:
    '回合和步骤的时间线，以及事件序号到位置的索引'
    def __init__(自身):
        '空时间线'
        自身.坐标={}
        自身.回合序号={}
        自身.回合步骤={}
        自身.时间线={'turnOrder':[],'turns':{}}
        自身.回合数据={}
        自身.步骤数据={}
        自身.脏数据=set()
        自身.变更回合=set()
        自身.当前回合=None
        自身.当前步骤=None

    def 快照(自身):
        '当前这份稳定时间线'
        return 自身.时间线

    def 取走变更回合(自身):
        '拿走这一轮刷新里变过的回合号'
        回合=list(自身.变更回合)
        自身.变更回合.clear()
        return 回合

    def 替换数据(自身,条目列):
        '整表替换定义拥有的位置值，读者身份保留'
        回合表={}
        步骤表={}
        for 项 in 条目列:
            数据=项['data']
            if 数据['kind']=='turn':
                值表=回合表.get(数据['turn'])
                if 值表 is None:
                    值表={}
                    回合表[数据['turn']]=值表
            else:
                键=步骤数据键(数据['turn'],要求步骤(数据))
                值表=步骤表.get(键)
                if 值表 is None:
                    值表={}
                    步骤表[键]=值表
            当前=值表.get(数据['key'])
            if 当前 is not None and 当前['owner']!=项['owner']:
                raise 对话错误('conversation Location data "'+数据['key']+'" is already owned by '+当前['owner'])
            值表[数据['key']]={'owner':项['owner'],'value':数据['value']}
        变了=False
        回合键=set(自身.回合数据.keys())
        回合键.update(回合表.keys())
        for 回合 in 回合键:
            if 自身.可变回合数据(回合).replace(回合表.get(回合,{})):
                变了=True
        步骤键=set(自身.步骤数据.keys())
        步骤键.update(步骤表.keys())
        for 步 in 步骤键:
            if 自身.可变步骤数据(步).replace(步骤表.get(步,{})):
                变了=True
        return 变了

    def 应用数据(自身,变更列):
        '先删旧的，再写新的'
        变了=False
        for 变更 in 变更列:
            先前=变更['previous']
            if 先前 is None:
                continue
            if 自身.存储于(先前).remove(变更['owner'],先前['key']):
                变了=True
        for 变更 in 变更列:
            下一=变更['next']
            if 下一 is None:
                continue
            if 自身.存储于(下一).set(变更['owner'],下一['key'],下一['value']):
                变了=True
        return 变了

    def 发布数据(自身):
        '把脏存储发布出去'
        脏=list(自身.脏数据)
        自身.脏数据.clear()
        for 存储 in 脏:
            存储.publish()

    def 位置于(自身,事件):
        '已收入索引的事件的当前位置。没有回合就落在会话'
        坐标=自身.坐标.get(事件['seq'])
        if 坐标 is None or 坐标.get('location') is None:
            return 会话位置
        return 坐标['location']

    def 重建(自身,条目列):
        '按整窗重算时间线，返回位置变了的序号'
        先前坐标=自身.坐标
        回合草稿={}
        坐标表={}
        当前回合=None
        当前步骤=None
        def 回合稿(回合,序号):
            '没有就建，有则收紧第一序号'
            稿=回合草稿.get(回合)
            if 稿 is None:
                稿={'turn':回合,'firstSeq':序号,'steps':{},'start':None,'end':None}
                回合草稿[回合]=稿
            elif 序号<稿['firstSeq']:
                稿['firstSeq']=序号
            return 稿
        def 步骤稿(回合,步,序号):
            '挂在所属回合下'
            主人=回合稿(回合,序号)
            稿=主人['steps'].get(步)
            if 稿 is None:
                稿={'turn':回合,'step':步,'firstSeq':序号,'start':None,'end':None}
                主人['steps'][步]=稿
            elif 序号<稿['firstSeq']:
                稿['firstSeq']=序号
            return 稿
        for 条目 in 条目列:
            事件=条目['event']
            显式=载荷坐标(事件)
            if 事件['type']=='turn/start':
                当前回合=事件['data']['turn']
                当前步骤=None
            if 事件['type']=='step/start':
                当前回合=事件['data']['turn']
                当前步骤=事件['data']['step']
            if 显式.get('session') is not True and 显式.get('turn') is not None:
                if 当前回合!=显式['turn']:
                    当前步骤=None
                当前回合=显式['turn']
                if 显式.get('step') is not None:
                    当前步骤=显式['step']
            if 显式.get('session') is True:
                回合=None
            else:
                回合=显式['turn'] if 显式.get('turn') is not None else 当前回合
            if 显式.get('session') is True or 事件['type'] in ('turn/start','turn/end'):
                步=None
            else:
                步=显式['step'] if 显式.get('step') is not None else (当前步骤 if 回合==当前回合 else None)
            坐标={'location':None}
            if 回合 is not None:
                坐标['turn']=回合
            if 回合 is not None and 步 is not None:
                坐标['step']=步
            坐标表[事件['seq']]=坐标
            if 回合 is not None:
                回合稿(回合,事件['seq'])
            if 回合 is not None and 步 is not None:
                步骤稿(回合,步,事件['seq'])
            if 事件['type']=='turn/start':
                回合稿(事件['data']['turn'],事件['seq'])['start']=事件
            elif 事件['type']=='turn/end':
                回合稿(事件['data']['turn'],事件['seq'])['end']=事件
            elif 事件['type']=='step/start':
                步骤稿(事件['data']['turn'],事件['data']['step'],事件['seq'])['start']=事件
            elif 事件['type']=='step/end':
                步骤稿(事件['data']['turn'],事件['data']['step'],事件['seq'])['end']=事件
            if 事件['type']=='step/end' and 当前回合==事件['data']['turn'] and 当前步骤==事件['data']['step']:
                当前步骤=None
            if 事件['type']=='turn/end' and 当前回合==事件['data']['turn']:
                当前回合=None
                当前步骤=None
        先前回合=自身.时间线['turns']
        下一回合={}
        有序=sorted(回合草稿.values(),key=lambda 稿:稿['firstSeq'])
        for 稿 in 有序:
            先前=先前回合.get(稿['turn'])
            先前步骤={}
            if 先前 is not None:
                for 步 in 先前['steps']:
                    先前步骤[步['step']]=步
            步骤=[]
            for 候选 in sorted(稿['steps'].values(),key=lambda 项:项['firstSeq']):
                if 候选['end'] is not None:
                    状态='closed'
                elif 候选['start'] is None:
                    状态='unknown'
                else:
                    状态='open'
                值={
                    'turn':候选['turn'],
                    'step':候选['step'],
                    'start':候选['start'],
                    'end':候选['end'],
                    'status':状态,
                    'data':自身.步骤数据面(候选['turn'],候选['step']),
                }
                旧=先前步骤.get(候选['step'])
                步骤.append(旧 if 同步骤(旧,值) else 值)
            if 稿['end'] is not None:
                状态='closed'
            elif 稿['start'] is None:
                状态='unknown'
            else:
                状态='open'
            值={
                'turn':稿['turn'],
                'start':稿['start'],
                'end':稿['end'],
                'status':状态,
                'steps':步骤,
                'data':自身.回合数据面(稿['turn']),
            }
            旧=先前回合.get(稿['turn'])
            下一回合[稿['turn']]=旧 if 同回合(旧,值) else 值
        下一序=[稿['turn'] for 稿 in 有序]
        if len(自身.时间线['turnOrder'])==len(下一序) and all(自身.时间线['turnOrder'][下标]==下一序[下标] for 下标 in range(len(下一序))):
            回合序=自身.时间线['turnOrder']
        else:
            回合序=下一序
        同表=len(先前回合)==len(下一回合)
        if 同表:
            for 回合,值 in 下一回合.items():
                if 先前回合.get(回合) is not 值:
                    同表=False
                    break
        回合键=set(先前回合.keys())
        回合键.update(下一回合.keys())
        for 回合 in 回合键:
            if 先前回合.get(回合) is not 下一回合.get(回合):
                自身.变更回合.add(回合)
        if 同表 and 回合序 is 自身.时间线['turnOrder']:
            pass
        else:
            自身.时间线={'turnOrder':回合序,'turns':下一回合}
        自身.回合步骤.clear()
        for 号码,回合 in 自身.时间线['turns'].items():
            自身.回合步骤[号码]={步['step']:步 for 步 in 回合['steps']}
        自身.坐标=坐标表
        自身.回合序号={}
        for 条目 in 条目列:
            事件=条目['event']
            坐标=自身.坐标[事件['seq']]
            if 坐标.get('turn') is not None:
                自身.索引回合序号(坐标['turn'],事件['seq'])
            坐标['location']=自身.解析(事件['seq'])
        自身.当前回合=当前回合
        自身.当前步骤=当前步骤
        变更=set()
        for 条目 in 条目列:
            事件=条目['event']
            旧=None if 先前坐标.get(事件['seq']) is None else 先前坐标[事件['seq']].get('location')
            新=自身.坐标[事件['seq']].get('location')
            if not 同位置(旧,新):
                变更.add(事件['seq'])
        return 变更

    def 追加边界(自身,事件):
        '追加一条回合或步骤边界，只重访所属回合'
        if 事件['type'] not in ('turn/start','turn/end','step/start','step/end'):
            raise 对话错误('conversation Location boundary expected, received '+事件['type'])
        显式=载荷坐标(事件)
        if 事件['type']=='turn/start':
            自身.当前回合=事件['data']['turn']
            自身.当前步骤=None
        elif 事件['type']=='step/start':
            自身.当前回合=事件['data']['turn']
            自身.当前步骤=事件['data']['step']
        if 显式.get('turn') is not None:
            if 自身.当前回合!=显式['turn']:
                自身.当前步骤=None
            自身.当前回合=显式['turn']
            if 显式.get('step') is not None:
                自身.当前步骤=显式['step']
        回合号=显式['turn'] if 显式.get('turn') is not None else 自身.当前回合
        if 回合号 is None:
            raise 对话错误('conversation boundary '+事件['type']+' has no turn')
        if 事件['type'] in ('turn/start','turn/end'):
            步骤号=None
        else:
            步骤号=显式['step'] if 显式.get('step') is not None else (自身.当前步骤 if 回合号==自身.当前回合 else None)
        旧坐标=自身.坐标.get(事件['seq'])
        坐标={'turn':回合号,'location':None if 旧坐标 is None else 旧坐标.get('location')}
        if 步骤号 is not None:
            坐标['step']=步骤号
        自身.坐标[事件['seq']]=坐标
        自身.索引回合序号(回合号,事件['seq'])
        先前回合=自身.时间线['turns'].get(回合号)
        步骤=list(先前回合['steps']) if 先前回合 is not None else []
        if 事件['type'] in ('step/start','step/end'):
            号码=事件['data']['step']
            索引步骤=自身.回合步骤.get(回合号)
            if 索引步骤 is None:
                索引步骤={}
            先前步骤=索引步骤.get(号码)
            候选={
                'turn':回合号,
                'step':号码,
                'start':事件 if 事件['type']=='step/start' else (None if 先前步骤 is None else 先前步骤.get('start')),
                'end':事件 if 事件['type']=='step/end' else (None if 先前步骤 is None else 先前步骤.get('end')),
                'status':'closed' if 事件['type']=='step/end' or (先前步骤 is not None and 先前步骤.get('end') is not None) else 'open',
                'data':自身.步骤数据面(回合号,号码),
            }
            下一步=先前步骤 if 同步骤(先前步骤,候选) else 候选
            索引步骤[号码]=下一步
            自身.回合步骤[回合号]=索引步骤
            下标=-1
            游=0
            while 游<len(步骤):
                if 步骤[游]['step']==号码:
                    下标=游
                    break
                游+=1
            if 下标<0:
                步骤=步骤+[下一步]
            else:
                步骤=[下一步 if 处==下标 else 项 for 处,项 in enumerate(步骤)]
        候选={
            'turn':回合号,
            'start':事件 if 事件['type']=='turn/start' else (None if 先前回合 is None else 先前回合.get('start')),
            'end':事件 if 事件['type']=='turn/end' else (None if 先前回合 is None else 先前回合.get('end')),
            'status':'closed' if 事件['type']=='turn/end' or (先前回合 is not None and 先前回合.get('end') is not None) else ('open' if 事件['type']=='turn/start' or (先前回合 is not None and 先前回合.get('start') is not None) else 'unknown'),
            'steps':步骤,
            'data':自身.回合数据面(回合号),
        }
        回合=先前回合 if 同回合(先前回合,候选) else 候选
        回合表=dict(自身.时间线['turns'])
        回合表[回合号]=回合
        if 先前回合 is None:
            回合序=list(自身.时间线['turnOrder'])+[回合号]
        else:
            回合序=自身.时间线['turnOrder']
        自身.时间线={'turnOrder':回合序,'turns':回合表}
        if 回合 is not 先前回合:
            自身.变更回合.add(回合号)
        变更=set()
        for 序号 in 自身.回合序号.get(回合号,set()):
            坐标=自身.坐标[序号]
            先前=坐标.get('location')
            下一=自身.解析(序号)
            坐标['location']=下一
            if not 同位置(先前,下一):
                变更.add(序号)
        if 事件['type']=='step/end' and 自身.当前回合==事件['data']['turn'] and 自身.当前步骤==事件['data']['step']:
            自身.当前步骤=None
        if 事件['type']=='turn/end' and 自身.当前回合==事件['data']['turn']:
            自身.当前回合=None
            自身.当前步骤=None
        return 变更

    def 追加非边界(自身,事件):
        '追加一条非边界尾事件'
        显式=载荷坐标(事件)
        if 显式.get('session') is True:
            自身.坐标[事件['seq']]={'location':会话位置}
            return
        if 显式.get('turn') is not None:
            if 自身.当前回合!=显式['turn']:
                自身.当前步骤=None
            自身.当前回合=显式['turn']
            if 显式.get('step') is not None:
                自身.当前步骤=显式['step']
        回合=显式['turn'] if 显式.get('turn') is not None else 自身.当前回合
        步=显式['step'] if 显式.get('step') is not None else (自身.当前步骤 if 回合==自身.当前回合 else None)
        if 显式.get('turn') is not None and 显式.get('step') is not None:
            坐标=dict(显式)
        else:
            坐标={'location':None}
            if 回合 is not None:
                坐标['turn']=回合
            if 回合 is not None and 步 is not None:
                坐标['step']=步
        自身.坐标[事件['seq']]=坐标
        if 回合 is not None:
            自身.索引回合序号(回合,事件['seq'])
        坐标['location']=自身.解析(事件['seq'])

    def 移除助手瞬时(自身,事件列):
        '去掉瞬时助手事件，不重建时间线'
        for 事件 in 事件列:
            坐标=自身.坐标.get(事件['seq'])
            回合=None if 坐标 is None else 坐标.get('turn')
            if 回合 is not None:
                序号集=自身.回合序号.get(回合)
                if 序号集 is not None:
                    序号集.discard(事件['seq'])
                    if len(序号集)==0:
                        del 自身.回合序号[回合]
            if 事件['seq'] in 自身.坐标:
                del 自身.坐标[事件['seq']]

    def 插入助手结算(自身,事件):
        '把耐久助手结算插到已经可见的尾巴之前'
        坐标={'turn':事件['data']['turn'],'step':事件['data']['step'],'location':None}
        自身.坐标[事件['seq']]=坐标
        自身.索引回合序号(事件['data']['turn'],事件['seq'])
        坐标['location']=自身.解析(事件['seq'])

    def 索引回合序号(自身,回合,序号):
        '这个回合拥有的事件序号'
        当前=自身.回合序号.get(回合)
        if 当前 is None:
            当前=set()
            自身.回合序号[回合]=当前
        当前.add(序号)

    def 回合数据面(自身,回合):
        '回合位置数据存储'
        return 自身.可变回合数据(回合)

    def 步骤数据面(自身,回合,步):
        '步骤位置数据存储'
        return 自身.可变步骤数据(步骤数据键(回合,步))

    def 可变回合数据(自身,回合):
        '没有就建一份回合存储'
        当前=自身.回合数据.get(回合)
        if 当前 is None:
            当前=自身.创建数据存储(回合)
            自身.回合数据[回合]=当前
        return 当前

    def 可变步骤数据(自身,键):
        '没有就建一份步骤存储。标脏用键里的回合号'
        当前=自身.步骤数据.get(键)
        if 当前 is None:
            回合=int(键.split(':',1)[0])
            当前=自身.创建数据存储(回合)
            自身.步骤数据[键]=当前
        return 当前

    def 创建数据存储(自身,回合):
        '存储变脏时记下回合'
        def 标脏(存储,回合=回合):
            '这份存储和这个回合都脏了'
            自身.脏数据.add(存储)
            自身.变更回合.add(回合)
        return 可变位置数据存储(标脏)

    def 存储于(自身,数据):
        '按种类选回合或步骤存储'
        if 数据['kind']=='turn':
            return 自身.可变回合数据(数据['turn'])
        return 自身.可变步骤数据(步骤数据键(数据['turn'],要求步骤(数据)))

    def 解析(自身,序号):
        '序号落到会话、未解析、回合或步骤'
        坐标=自身.坐标.get(序号)
        if 坐标 is None or 坐标.get('turn') is None:
            return 会话位置
        回合=自身.时间线['turns'].get(坐标['turn'])
        if 回合 is None:
            return 未解析位置
        if 坐标.get('step') is None:
            return {'kind':'turn','turn':回合}
        步=自身.回合步骤.get(坐标['turn'],{}).get(坐标['step'])
        if 步 is None:
            return {'kind':'turn','turn':回合}
        return {'kind':'step','turn':回合,'step':步}

    def snapshot(自身):
        '组装器用的快照名'
        return 自身.快照()

    def takeChangedTurns(自身):
        '组装器用的取走名'
        return 自身.取走变更回合()

    def replaceData(自身,条目列):
        '组装器用的替换名'
        return 自身.替换数据(条目列)

    def applyData(自身,变更列):
        '组装器用的应用名'
        return 自身.应用数据(变更列)

    def publishData(自身):
        '组装器用的发布名'
        自身.发布数据()

    def locationOf(自身,事件):
        '组装器用的位置名'
        return 自身.位置于(事件)

    def rebuild(自身,条目列):
        '组装器用的重建名'
        return 自身.重建(条目列)

    def appendBoundary(自身,事件):
        '组装器用的边界名'
        return 自身.追加边界(事件)

    def appendNonBoundary(自身,事件):
        '组装器用的非边界名'
        自身.追加非边界(事件)

    def removeAssistantTransients(自身,事件列):
        '组装器用的移除名'
        自身.移除助手瞬时(事件列)

    def insertAssistantSettlement(自身,事件):
        '组装器用的结算名'
        自身.插入助手结算(事件)
