'共享入口上的已接受值，以及按顺序写回宿主。'
import copy
from ....依赖.cordis.服务 import 服务
from ...存储 import 创建快照存储
from ..开发者工具设置 import 开发者工具命名空间
from .开发者工具 import 开发者工具偏好
from .配置表单类型 import 加载中,就绪,不可用

class 配置表单控制器:
    '一个命名空间在共享描述镜像上的派生视图，以及这个命名空间的有序写入'
    def __init__(自身,上下文,规格,镜像,模式):
        '订阅镜像并立刻派生。写入带着已知修订，拆掉时不再派生'
        自身.上下文=上下文
        自身.规格=规格
        自身.镜像=镜像
        自身.模式=模式
        自身.仓=创建快照存储({
            'status':加载中,
            'value':None,
            'base':None,
            'user':None,
            'revision':None,
            'writable':False,
        })
        自身.写世代=0
        自身.已拆除=False
        自身.待修订=None
        自身.退订=镜像.subscribe(自身.派生)
        自身.派生()

    def getSnapshot(自身):
        '当前同步快照。引用保持到下一次变更'
        return 自身.仓.getSnapshot()

    def subscribe(自身,监听):
        '观察快照替换，返回退订'
        return 自身.仓.subscribe(监听)

    def set(自身,字段,值):
        '排队写一个标量字段'
        return 自身.mutate([{'op':'set','path':[字段],'value':值}])

    def unset(自身,字段):
        '排队清一个字段，让它重新继承组合层'
        return 自身.mutate([{'op':'unset','path':[字段]}])

    def mutate(自身,操作表,期望修订=None):
        '一次原子改写。拒绝后，仍是最新的那次负责重读宿主'
        if 自身.已拆除:
            return False
        自有=copy.deepcopy(list(操作表))
        自身.写世代+=1
        世代=自身.写世代
        if 期望修订 is not None:
            修订=期望修订
        elif 自身.待修订 is not None:
            修订=自身.待修订
        else:
            修订=自身.getSnapshot().get('revision')
        应答=自身.上下文.remote.settings.mutate(自身.规格['namespace'],自有,修订)
        if 应答['ok'] is not True:
            if 自身.已拆除 or 世代!=自身.写世代:
                return False
            自身.待修订=None
            自身.镜像.加载()
            return False
        if 自身.已拆除:
            return True
        if 世代==自身.写世代:
            自身.待修订=None
            自身.镜像.接纳视图(应答['value'])
        else:
            自身.待修订=应答['value']['revision']
        return True

    def 派生(自身):
        '从镜像折出本命名空间的快照'
        if 自身.已拆除:
            return
        镜像快照=自身.镜像.getSnapshot()
        if 镜像快照.get('view') is None:
            return
        可写=镜像快照['view']['writable']
        视图=None
        for 候选 in 镜像快照['view']['namespaces']:
            if 候选['ns']==自身.规格['namespace']:
                视图=候选
                break
        if 视图 is None:
            def 标不可用(草稿):
                '命名空间不在镜像里'
                草稿['status']=不可用
                草稿['writable']=可写
            自身.仓.update(标不可用)
            return
        解码器=自身.规格.get('decode')
        if 解码器 is not None:
            解码=解码器(视图.get('value'))
        else:
            解码=None
            值=视图.get('value')
            if isinstance(值,dict):
                try:
                    失败=自身.模式.校验(自身.模式.再水合(视图['schema']),值)
                except Exception as 坏信封:
                    解码=None#坏信封无法再水合，这一节不当作已接受
                else:
                    if 失败 is None:
                        解码=值

        def 写入(草稿):
            '修订和两层总是更新。解码失败则不改状态和值'
            草稿['revision']=视图.get('revision')
            草稿['base']=视图.get('base')
            草稿['user']=视图.get('user')
            草稿['writable']=可写
            if 解码 is None:
                return
            草稿['status']=就绪
            草稿['value']=解码

        自身.仓.update(写入)

class 配置表单集(服务):
    '设置域的基础服务。偏好通过这份服务读写，不跨插件导入值'
    def __init__(自身,上下文,配置):
        '登记 configForms，并持有提供方上下文'
        super().__init__(上下文,'configForms')
        自身.镜像=配置['镜像']
        自身.模式=配置['模式']
        自身.拥有方=上下文
        自身.表单表={}
        自身.developerTools=开发者工具偏好(自身.get(开发者工具命名空间))

        def 寿命():
            '拆除时停掉全部分表单的派生'
            def 拆():
                '标记拆除、退订，然后清空表'
                for 表单 in list(自身.表单表.values()):
                    表单.已拆除=True
                    表单.写世代+=1
                    表单.退订()
                自身.表单表.clear()
            return 拆

        上下文.副作用(寿命,'ui-settings: configuration forms')

    def describe(自身):
        '跨命名空间的读和折叠。和 get 看的是同一份快照'
        return 自身.镜像

    def get(自身,入口标识):
        '取一个宿主插件入口的共享表单。没有就建，并确保镜像已读'
        已有=自身.表单表.get(入口标识)
        if 已有 is not None:
            return 已有
        表单=配置表单控制器(
            自身.拥有方,
            {'namespace':入口标识},
            自身.镜像,
            自身.模式,
        )
        自身.表单表[入口标识]=表单
        自身.镜像.确保()
        return 表单

    def 在已提供期间(自身,命名空间表,登记):
        '任一命名空间出现在镜像里才登记。全没有，或调用方拆除时，拆掉登记'
        拆除器=[None]

        def 同步():
            '按当前镜像挂上或拆掉'
            视图=自身.镜像.getSnapshot().get('view')
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
            elif 盯着 is False and 拆除器[0] is not None:
                拆除器[0]()
                拆除器[0]=None

        退订=自身.镜像.subscribe(同步)
        自身.镜像.确保()
        同步()

        def 停():
            '停止监视，并拆掉还活着的登记'
            退订()
            if 拆除器[0] is not None:
                拆除器[0]()
                拆除器[0]=None

        return 停
