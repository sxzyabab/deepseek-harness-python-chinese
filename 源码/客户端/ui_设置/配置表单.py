import copy,threading
from ...依赖.cordis.服务 import 服务
from ...存储 import 创建快照存储
from ...配置.配置 import 操作任务,已结算任务
from .配置表单类型 import 空表单快照,就绪,不可用
from .开发者工具 import 开发者工具偏好
from .开发者工具设置 import 开发者工具命名空间

__all__=['配置表单控制器','配置表单集']

class 配置表单控制器:
    """一份命名空间在共享 describe 镜像上的派生视图与有序写入。"""
    def __init__(自身,上下文,规格,镜像,持久化,模式):
        """host 订阅镜像并派生；memory 停在不可用。"""
        自身.上下文=上下文#提供方上下文
        自身.规格=规格#namespace 与可选 decode
        自身.镜像=镜像#共享镜像
        自身.持久化=持久化#host 或 memory
        自身.模式=模式#设置模式服务
        自身.仓=创建快照存储(空表单快照(持久化))#快照仓
        自身.尾=已结算任务(None)#写链尾巴，始终兑现
        自身.写世代=0#写入世代
        自身.已拆除=False#拆除门
        自身.待修订=None#被顶掉的写入答复修订
        自身.退订=None#镜像订阅
        if 持久化=='host':#导线
            自身.退订=镜像.subscribe(自身.派生)#订镜像
            自身.派生()#立刻派生

    def getSnapshot(自身):
        """当前同步快照。"""
        return 自身.仓.getSnapshot()

    def subscribe(自身,监听):
        """观察快照替换。"""
        return 自身.仓.subscribe(监听)

    def set(自身,字段,值):
        """排队写一个标量字段。"""
        return 自身.mutate([{'op':'set','path':[字段],'value':值}])

    def unset(自身,字段):
        """排队清一个字段。"""
        return 自身.mutate([{'op':'unset','path':[字段]}])

    def mutate(自身,操作表,期望修订=None):
        """排队一次原子改写；拒绝后由最新写入负责恢复。"""
        自有=copy.deepcopy(list(操作表))#排队时拷贝
        自身.写世代+=1#新世代
        世代=自身.写世代#钉住
        def 操作():
            """发 mutate 并折视图或恢复。"""
            修订=期望修订
            if 修订 is None:#未钉
                修订=自身.待修订 if 自身.待修订 is not None else 自身.getSnapshot()['revision']
            应答=自身.上下文.remote.settings.mutate(自身.规格['namespace'],自有,修订)
            if hasattr(应答,'等待'):#操作任务
                应答=应答.等待()
            if 应答.get('ok') is not True:#拒绝
                自身.恢复(世代)
                return False
            if 自身.已拆除:#已拆
                return True
            if 世代==自身.写世代:#仍是最新
                自身.待修订=None#清篱笆
                自身.镜像.接纳视图(应答['value'])#折进镜像
            else:#已被顶
                自身.待修订=应答['value']['revision']#后继用此篱笆
            return True
        return 自身.入队(操作)

    def 恢复(自身,世代):
        """仅最新失败写入才重载宿主态。"""
        if 自身.已拆除 or 世代!=自身.写世代:#过期
            return
        自身.待修订=None#清篱笆
        自身.镜像.加载()#重读

    def 拆除(自身):
        """停排队、停派生，并等当前导线结算。"""
        自身.已拆除=True#门
        自身.写世代+=1#作废在途
        if 自身.退订 is not None:#有订
            自身.退订()#退
        自身.尾.等待()#等尾巴

    def 入队(自身,操作):
        """串行写链；失败的订阅者不得饿死后继。"""
        if 自身.持久化=='memory' or 自身.已拆除:#跳过
            return False
        前=自身.尾#前任
        任务=操作任务()#本次
        def 跑():
            """绕过前任后执行。"""
            try:#前任
                前.等待()
            except Exception:
                pass
            if 自身.已拆除:#已拆
                任务.兑现(False)
                return
            try:#本次
                任务.兑现(操作())
            except Exception as 错误:
                任务.拒绝(错误)
        线=threading.Thread(target=跑)
        线.daemon=True
        线.start()
        吞=操作任务()#尾巴始终兑现
        def 收尾():
            """吞掉本次成败。"""
            try:
                任务.等待()
            except Exception:
                pass
            吞.兑现(None)
        尾线=threading.Thread(target=收尾)
        尾线.daemon=True
        尾线.start()
        自身.尾=吞#新尾巴
        return 任务.等待()

    def 派生(自身):
        """从镜像折本命名空间快照。"""
        if 自身.已拆除:#已拆
            return
        镜=自身.镜像.getSnapshot()#镜像快照
        if 镜['view'] is None:#尚无文档
            return
        可写=镜['view']['writable']#文档可写
        视图=None#本 ns
        for 候选 in 镜['view']['namespaces']:#逐行
            if 候选['ns']==自身.规格['namespace']:#命中
                视图=候选
                break
        if 视图 is None:#未暴露
            def 标不可用(草稿):
                """写不可用。"""
                草稿['status']=不可用
                草稿['writable']=可写
            自身.仓.update(标不可用)
            return
        解码=自身.解码(视图)#可选收窄
        def 写入(草稿):
            """折修订与层。"""
            草稿['revision']=视图['revision']
            草稿['base']=视图['base'] if 'base' in 视图 else None
            草稿['user']=视图['user'] if 'user' in 视图 else None
            草稿['writable']=可写
            if 解码 is None:#未接受
                return
            草稿['status']=就绪
            草稿['value']=解码
        自身.仓.update(写入)

    def 解码(自身,视图):
        """规格 decode 优先；否则按模式信封校验节。"""
        if 'decode' in 自身.规格 and 自身.规格['decode'] is not None:
            return 自身.规格['decode'](视图['value'])
        值=视图['value']#节
        if not isinstance(值,dict):#非对象
            return None
        try:#信封
            失败=自身.模式.校验(自身.模式.再水合(视图['schema']),值)
        except Exception:
            return None
        if 失败 is None:#通过
            return 值
        return None

class 配置表单集(服务):
    """设置域的基础服务。偏好经本服务而非跨插件值导入。"""
    def __init__(自身,上下文,配置):
        """登记 configForms，并持有提供方纤程。"""
        super().__init__(上下文,'configForms')
        自身.镜像=配置['镜像']
        自身.模式=配置['模式']
        自身.持久化=配置['持久化']
        自身.拥有方=上下文#提供方上下文
        自身.表单表={}#entryId → 控制器
        自身.developerTools=开发者工具偏好(自身.get(开发者工具命名空间))#共享开发者工具
        def 寿命():
            """拆除全部表单。"""
            def 拆():
                """逐个拆除。"""
                for 表单 in list(自身.表单表.values()):
                    表单.拆除()
                自身.表单表.clear()
            return 拆
        上下文.副作用(寿命,'ui-settings: configuration forms')

    def describe(自身):
        """跨命名空间读/折面，与 get 同源快照。"""
        return 自身.镜像

    def get(自身,入口标识):
        """取一份宿主插件入口的共享表单。"""
        if 入口标识 in 自身.表单表:
            return 自身.表单表[入口标识]
        表单=配置表单控制器(自身.拥有方,{'namespace':入口标识},自身.镜像,自身.持久化,自身.模式)
        自身.表单表[入口标识]=表单
        自身.镜像.确保()
        return 表单

    def 在已提供期间(自身,命名空间表,登记):
        """任一命名空间出现在镜像里才登记；全无则拆除。"""
        拆除器=[None]#活登记
        def 同步():
            """按镜像决定挂上或拆掉。"""
            视图=自身.镜像.getSnapshot()['view']
            已提供=set()
            if 视图 is not None:
                for 行 in 视图['namespaces']:
                    已提供.add(行['ns'])
            盯着=False
            for 名 in 命名空间表:
                if 名 in 已提供:
                    盯着=True
                    break
            if 盯着 and 拆除器[0] is None:
                拆除器[0]=登记(已提供)
            elif (not 盯着) and 拆除器[0] is not None:
                拆除器[0]()
                拆除器[0]=None
        退订=自身.镜像.subscribe(同步)
        自身.镜像.确保()
        同步()
        def 停():
            """停监视并拆活登记。"""
            退订()
            if 拆除器[0] is not None:
                拆除器[0]()
                拆除器[0]=None
        return 停
