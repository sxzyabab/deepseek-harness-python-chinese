from ...存储 import 创建快照存储

__all__=['子智能体模型选择命名空间','子智能体模型键','子智能体模型选择卡片控制器']

子智能体模型选择命名空间='subagent-model-selection-settings'

def 子智能体模型键(路由):
    '一条精确路由的不透明查找键。调用方只拿它来查找，不拆开'
    return 路由['provider']+'\0'+路由['model']

def 同路由(左,右):
    '两边路由集合是否相同，不看顺序'
    if len(左)!=len(右):
        return False
    右键=set(子智能体模型键(路由) for 路由 in 右)
    for 路由 in 左:
        if 子智能体模型键(路由) not in 右键:
            return False
    return True

class 子智能体模型选择卡片控制器:
    '把配置表单与活适配器目录接到暂存卡片'
    def __init__(自身,作用域,上下文):
        '订阅作用域。已经开启且目录还闲着时立刻拉目录'
        自身.作用域=作用域
        自身.上下文=上下文
        自身.目录分组=[]
        自身.目录部分失败=False
        自身.目录状态='idle'
        自身.草稿开启=None
        自身.草稿路由=None
        自身.草稿修订=None
        自身.保存中=False
        自身.失败=False
        自身.冲突=False
        自身.已拆除=False
        自身.保存代=0
        自身.目录代=0
        自身.存储=创建快照存储(自身.投影())
        def 作用域变():
            '修订越过草稿：内容没变就清草稿，否则标冲突。已开启且目录闲着就拉'
            if not 自身.保存中 and 自身.草稿路由 is not None and 自身.作用域.getSnapshot()['revision']!=自身.草稿修订:
                if 自身.当前开启()==自身.开启() and 同路由(自身.当前路由(),自身.期望路由()):
                    自身.清草稿()
                else:
                    自身.冲突=True
            if 自身.开启() and 自身.目录状态=='idle':
                自身.加载目录()
            自身.发布()
        自身.退订=作用域.subscribe(作用域变)
        if 自身.开启() and 自身.目录状态=='idle':
            自身.加载目录()

    def 拆除(自身):
        '停止观察，并作废迟到的目录和写入结算'
        自身.已拆除=True
        自身.保存代+=1
        自身.目录代+=1
        自身.退订()

    def 注入(自身):
        '渲染器注入面：快照和暂存动作'
        return {
            'hooks':{'subagentModelSelectionCard':自身.存储},
            'toggleEnabled':自身.切换开启,
            'toggleModel':自身.切换模型,
            'retryCatalog':自身.加载目录,
            'save':自身.保存,
            'discard':自身.丢弃,
        }

    def 当前路由(自身):
        '生效设置里的路由副本。还没有值时是空表'
        值=自身.作用域.getSnapshot()['value']
        if 值 is None:
            return []
        return [{'provider':路由['provider'],'model':路由['model']} for 路由 in 值['allowedModels']]

    def 当前开启(自身):
        '生效设置里的开关。还没有值时视为关闭'
        值=自身.作用域.getSnapshot()['value']
        if 值 is None:
            return False
        开启=值.get('enabled')
        if 开启 is None:
            return False
        return 开启

    def 已选(自身):
        '草稿优先，否则用生效路由的键'
        if 自身.草稿路由 is not None:
            return set(自身.草稿路由.keys())
        return set(子智能体模型键(路由) for 路由 in 自身.当前路由())

    def 开启(自身):
        '草稿开关优先，否则用生效开关'
        if 自身.草稿开启 is not None:
            return 自身.草稿开启
        return 自身.当前开启()

    def 开始草稿(自身):
        '第一次编辑时把当前生效值拷进草稿，并钉住修订'
        if 自身.草稿路由 is None:
            快照=自身.作用域.getSnapshot()
            值=快照['value']
            if 值 is None:
                自身.草稿开启=False
                路由表=[]
            else:
                开启=值.get('enabled')
                自身.草稿开启=False if 开启 is None else 开启
                路由表=值['allowedModels']
            自身.草稿路由={}
            for 路由 in 路由表:
                自身.草稿路由[子智能体模型键(路由)]={'provider':路由['provider'],'model':路由['model']}
            自身.草稿修订=快照['revision']
        return 自身.草稿路由

    def 切换开启(自身):
        '暂存开关。打开且目录还闲着时拉目录'
        快照=自身.作用域.getSnapshot()
        if 自身.已拆除 or 快照['status']!='ready' or not 快照['writable'] or 自身.保存中:
            return
        自身.开始草稿()
        自身.草稿开启=not 自身.草稿开启
        自身.失败=False
        if 自身.草稿开启 and 自身.目录状态=='idle':
            自身.加载目录()
        自身.发布()

    def 切换模型(自身,键):
        '暂存一条精确路由的允许或拒绝'
        if not 自身.开启() or 自身.保存中 or not 自身.作用域.getSnapshot()['writable']:
            return
        命中=None
        for 行 in 自身.候选():
            if 行['key']==键:
                命中=行
                break
        if 命中 is None:
            return
        路由表=自身.开始草稿()
        if 键 in 路由表:
            del 路由表[键]
        else:
            路由表[键]={'provider':命中['provider'],'model':命中['model']}
        自身.失败=False
        自身.发布()

    def 清草稿(自身):
        '丢掉草稿、失败和冲突'
        自身.草稿开启=None
        自身.草稿路由=None
        自身.草稿修订=None
        自身.失败=False
        自身.冲突=False

    def 丢弃(自身):
        '保存进行中时不丢'
        if 自身.保存中:
            return
        自身.清草稿()
        自身.发布()

    def 候选(自身):
        '活目录叠上草稿仍要保留的路由。目录里没有的已存路由标成不可用'
        保留={}
        for 路由 in 自身.当前路由():
            保留[子智能体模型键(路由)]=路由
        if 自身.草稿路由 is not None:
            for 键,路由 in 自身.草稿路由.items():
                保留[键]=路由
        已选=自身.已选()
        按键=dict(保留)
        候选=[]
        for 分组 in 自身.目录分组:
            for 模型 in 分组['models']:
                路由={'provider':分组['id'],'model':模型['id']}
                键=子智能体模型键(路由)
                按键.pop(键,None)
                候选.append({
                    'provider':路由['provider'],
                    'model':路由['model'],
                    'key':键,
                    'providerName':分组['name'],
                    'modelName':模型['name'],
                    'available':True,
                    'selected':键 in 已选,
                })
        for 路由 in list(按键.values()):
            键=子智能体模型键(路由)
            候选.append({
                'provider':路由['provider'],
                'model':路由['model'],
                'key':键,
                'providerName':路由['provider'],
                'modelName':路由['model'],
                'available':False,
                'selected':键 in 已选,
            })
        return 候选

    def 期望路由(自身):
        '草稿或生效路由的副本'
        if 自身.草稿路由 is None:
            源=自身.当前路由()
        else:
            源=list(自身.草稿路由.values())
        return [{'provider':路由['provider'],'model':路由['model']} for 路由 in 源]

    def 保存(自身):
        '一次带修订栅栏的写入。落定后再看宿主是否收下'
        快照=自身.作用域.getSnapshot()
        期望开启=自身.开启()
        期望=自身.期望路由()
        if (
            自身.已拆除 or 快照['status']!='ready' or not 快照['writable'] or 自身.保存中
            or (自身.当前开启()==期望开启 and 同路由(自身.当前路由(),期望))
            or (期望开启 and len(期望)==0)
        ):
            return
        if 自身.草稿路由 is not None and 快照['revision']!=自身.草稿修订:
            自身.冲突=True
            自身.发布()
            return
        代=自身.保存代
        自身.保存中=True
        自身.失败=False
        自身.冲突=False
        自身.发布()
        自身.作用域.mutate([
            {'op':'set','path':['enabled'],'value':期望开启},
            {
                'op':'set',
                'path':['allowedModels'],
                'value':[{'provider':路由['provider'],'model':路由['model']} for 路由 in 期望],
            },
        ],自身.草稿修订).等待()
        if 代!=自身.保存代:
            return
        落地=自身.当前开启()==期望开启 and 同路由(自身.当前路由(),期望)
        自身.保存中=False
        自身.失败=not 落地
        if 落地:
            自身.清草稿()
        自身.发布()

    def 刷新目录(自身):
        '宿主模型输入变了就作废目录。开着就重拉，关着只发布'
        if 自身.已拆除:
            return
        自身.目录代+=1
        自身.目录状态='idle'
        自身.目录部分失败=False
        if 自身.开启():
            自身.加载目录()
        else:
            自身.发布()

    def 重置连接(自身):
        '重连后丢掉草稿和目录，再按当前开关决定是否重拉'
        if 自身.已拆除:
            return
        自身.保存代+=1
        自身.保存中=False
        自身.清草稿()
        自身.目录分组=[]
        自身.刷新目录()

    def 加载目录(自身):
        '读适配器目录。代际变了的应答丢掉'
        if 自身.已拆除 or 自身.目录状态=='loading':
            return
        代=自身.目录代
        自身.目录状态='loading'
        自身.目录部分失败=False
        自身.发布()
        应答=自身.上下文.remote.session.modelCatalog().等待()
        if 代!=自身.目录代:
            return
        结果=应答['result'] if 'result' in 应答 else 应答
        if 结果['ok']:
            自身.目录分组=结果['value']['groups']
            自身.目录部分失败=len(结果['value']['failures'])>0
            自身.目录状态='ready'
        else:
            自身.目录状态='error'
        自身.发布()

    def 投影(自身):
        '卡片渲染态'
        快照=自身.作用域.getSnapshot()
        当前=自身.当前路由()
        期望=自身.期望路由()
        开启=自身.开启()
        return {
            'available':快照['status']=='ready',
            'writable':bool(快照['writable']),
            'dirty':自身.当前开启()!=开启 or not 同路由(当前,期望),
            'invalid':开启 and len(期望)==0,
            'saving':自身.保存中,
            'failed':自身.失败,
            'enabled':开启,
            'candidates':自身.候选(),
            'catalogStatus':自身.目录状态,
            'catalogPartial':自身.目录部分失败,
            'conflicted':自身.冲突,
        }

    def 发布(自身):
        '把投影写进快照存储'
        自身.存储.set(自身.投影())
