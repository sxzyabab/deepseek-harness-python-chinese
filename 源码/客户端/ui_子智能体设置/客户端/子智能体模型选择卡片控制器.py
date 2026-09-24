from ...存储 import 创建快照存储

__all__=['子智能体模型选择命名空间','子智能体模型键','子智能体模型候选','子智能体模型选择卡片控制器']

子智能体模型选择命名空间='subagent-model-selection-settings'

def 子智能体模型键(路由):
    """一条精确路由的不透明查找键。"""
    return 路由['provider']+'\0'+路由['model']

def 子智能体模型候选(分组表,已存,已选):
    """把活目录与仍可移除的已存路由合成候选行。"""
    按键=dict((子智能体模型键(路由),路由) for 路由 in 已存)
    候选=[]
    for 分组 in 分组表:
        for 模型 in 分组['models']:
            路由={'provider':分组['id'],'model':模型['id']}
            键=子智能体模型键(路由)
            按键.pop(键,None)
            候选.append({
                **路由,
                'key':键,
                'providerName':分组['name'],
                'modelName':模型['name'],
                'available':True,
                'selected':键 in 已选,
            })
    for 路由 in 按键.values():
        键=子智能体模型键(路由)
        候选.append({
            **路由,
            'key':键,
            'providerName':路由['provider'],
            'modelName':路由['model'],
            'available':False,
            'selected':键 in 已选,
        })
    return 候选

def 同路由(左,右):
    """两边路由集合是否相同。"""
    if len(左)!=len(右):
        return False
    右键=set(子智能体模型键(路由) for 路由 in 右)
    for 路由 in 左:
        if 子智能体模型键(路由) not in 右键:
            return False
    return True

class 子智能体模型选择卡片控制器:
    """把配置表单与活适配器目录接到暂存卡片。"""
    def __init__(自身,作用域,上下文):
        """订阅作用域并在已开启时拉目录。"""
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
            """修订越过草稿则标冲突。"""
            if not 自身.保存中 and 自身.草稿路由 is not None:
                if 自身.作用域.getSnapshot()['revision']!=自身.草稿修订:
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
        """停止观察并作废迟到结算。"""
        自身.已拆除=True
        自身.保存代+=1
        自身.目录代+=1
        自身.退订()

    def 注入(自身):
        """渲染器注入面。"""
        return {
            'hooks':{'subagentModelSelectionCard':自身.存储},
            'toggleEnabled':自身.切换开启,
            'toggleModel':自身.切换模型,
            'retryCatalog':自身.加载目录,
            'save':自身.保存,
            'discard':自身.丢弃,
        }

    def 当前路由(自身):
        """生效设置里的路由副本。"""
        值=自身.作用域.getSnapshot().get('value')
        if 值 is None:
            return []
        表=值.get('allowedModels') or []
        return [{'provider':路由['provider'],'model':路由['model']} for 路由 in 表]

    def 当前开启(自身):
        """生效设置里的开关。"""
        值=自身.作用域.getSnapshot().get('value')
        if 值 is None:
            return False
        return bool(值.get('enabled'))

    def 已选(自身):
        """草稿或生效路由的键集。"""
        if 自身.草稿路由 is not None:
            return set(自身.草稿路由.keys())
        return set(子智能体模型键(路由) for 路由 in 自身.当前路由())

    def 开启(自身):
        """草稿或生效开关。"""
        if 自身.草稿开启 is not None:
            return 自身.草稿开启
        return 自身.当前开启()

    def 开始草稿(自身):
        """把当前生效值拷进草稿。"""
        if 自身.草稿路由 is None:
            快照=自身.作用域.getSnapshot()
            值=快照.get('value')
            自身.草稿开启=False if 值 is None else bool(值.get('enabled'))
            路由表=[] if 值 is None else (值.get('allowedModels') or [])
            自身.草稿路由=dict(
                (子智能体模型键(路由),{'provider':路由['provider'],'model':路由['model']})
                for 路由 in 路由表
            )
            自身.草稿修订=快照['revision']
        return 自身.草稿路由

    def 切换开启(自身):
        """暂存开关；开启时拉目录。"""
        快照=自身.作用域.getSnapshot()
        if 自身.已拆除 or 快照.get('status')!='ready' or not 快照.get('writable') or 自身.保存中:
            return
        自身.开始草稿()
        自身.草稿开启=not 自身.草稿开启
        自身.失败=False
        if 自身.草稿开启 and 自身.目录状态=='idle':
            自身.加载目录()
        自身.发布()

    def 切换模型(自身,键):
        """暂存一条精确路由的允许或拒绝。"""
        if not 自身.开启() or 自身.保存中 or not 自身.作用域.getSnapshot().get('writable'):
            return
        候选=None
        for 行 in 自身.候选():
            if 行['key']==键:
                候选=行
                break
        if 候选 is None:
            return
        路由=自身.开始草稿()
        if 键 in 路由:
            del 路由[键]
        else:
            路由[键]={'provider':候选['provider'],'model':候选['model']}
        自身.失败=False
        自身.发布()

    def 清草稿(自身):
        """丢掉草稿与失败标记。"""
        自身.草稿开启=None
        自身.草稿路由=None
        自身.草稿修订=None
        自身.失败=False
        自身.冲突=False

    def 丢弃(自身):
        """保存中不可丢。"""
        if 自身.保存中:
            return
        自身.清草稿()
        自身.发布()

    def 候选(自身):
        """活目录叠草稿保留的路由。"""
        保留=dict((子智能体模型键(路由),路由) for 路由 in 自身.当前路由())
        if 自身.草稿路由 is not None:
            for 键,路由 in 自身.草稿路由.items():
                保留[键]=路由
        return 子智能体模型候选(自身.目录分组,list(保留.values()),自身.已选())

    def 期望路由(自身):
        """草稿或生效路由副本。"""
        源=自身.当前路由() if 自身.草稿路由 is None else list(自身.草稿路由.values())
        return [{'provider':路由['provider'],'model':路由['model']} for 路由 in 源]

    def 保存(自身):
        """一次带修订栅栏的 mutate。"""
        快照=自身.作用域.getSnapshot()
        期望开启=自身.开启()
        期望=自身.期望路由()
        if (
            自身.已拆除 or 快照.get('status')!='ready' or not 快照.get('writable') or 自身.保存中
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
        """Host 模型输入变了则作废并重拉。"""
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
        """重连后丢掉 Host 相关草稿再拉目录。"""
        if 自身.已拆除:
            return
        自身.保存代+=1
        自身.保存中=False
        自身.清草稿()
        自身.目录分组=[]
        自身.刷新目录()

    def 加载目录(自身):
        """读适配器目录。"""
        if 自身.已拆除 or 自身.目录状态=='loading':
            return
        代=自身.目录代
        自身.目录状态='loading'
        自身.目录部分失败=False
        自身.发布()
        应答=自身.上下文.remote.session.modelCatalog().等待()
        if 代!=自身.目录代:
            return
        if 应答['ok']:
            自身.目录分组=应答['value']['groups']
            自身.目录部分失败=len(应答['value']['failures'])>0
            自身.目录状态='ready'
        else:
            自身.目录状态='error'
        自身.发布()

    def 投影(自身):
        """卡片渲染态。"""
        快照=自身.作用域.getSnapshot()
        当前=自身.当前路由()
        期望=自身.期望路由()
        开启=自身.开启()
        return {
            'available':快照.get('status')=='ready',
            'writable':bool(快照.get('writable')),
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
        """写快照存储。"""
        自身.存储.set(自身.投影())
