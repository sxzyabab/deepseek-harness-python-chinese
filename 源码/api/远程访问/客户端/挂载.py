'挂载 remoteAccess，跟随访问快照，并发布全局资源钩子'
from ....基础设施.通用工具 import 获取内部数据#读远程上的流工厂
from ....依赖.cordis.服务 import 服务#客户端服务基类
from ...网关.客户端.快照流 import 远程快照流#基线加增量
from ...网关.异常 import 远程流载体错误#流协议失败
from .状态 import 客户端访问状态#快照所有者

class 客户端远程访问服务(服务):
    '调用方对等端的访问答案。它自己不发请求'
    def __init__(自身,上下文,状态):
        '在客户端上下文上以 remoteAccess 登记'
        super().__init__(上下文,'remoteAccess')#服务键
        自身.状态=状态#快照所有者

    def 来源(自身,种类,标识,动作):
        '按资源种类、标识与动作读取是否允许'
        return 自身.状态.资源许可(种类,标识,动作)#稳定源

def 挂载访问(上下文,贡献,初始=None):
    '挂载命名空间并开始跟随。返回拆除器'
    状态=客户端访问状态(初始)#从注入基线起步
    客户端远程访问服务(上下文,状态)#提供服务
    if hasattr(上下文.slots,'provideRoot'):#有根钩才发布
        上下文.slots.provideRoot({'keyedHooks':{'remoteAccess':lambda 动作:状态.全局许可(动作)}})#全局动作
    远程=上下文.remote#远程面
    卸下=None#没有贡献就不挂命名空间
    if 贡献 is not None:#有生成贡献
        卸下=getattr(远程,'$mount')(贡献)#挂上命名空间
    def 跟随(远程上下文):
        '远程命名空间就绪后开始快照流'
        控制=创建访问流(远程上下文.remote,状态,远程上下文.日志)#监督流
        控制.start()#启动
        def 登记拆除():
            '离开时拆掉流'
            def 拆除():
                '等待消费者静默'
                控制.dispose()#拆
            return 拆除#拆除器
        return 远程上下文.副作用(登记拆除,'remote-access.client.follow')#登记
    跟随拆除=上下文.依赖启动(['remote.remoteAccess'],跟随)#等命名空间
    def 拆除器():
        '先停跟随，再卸命名空间'
        if callable(跟随拆除):#有拆除器
            跟随拆除()#停流
        if callable(卸下):#有卸下
            卸下()#卸命名空间
    return 拆除器#交给插件

def 创建访问流(远程,状态,日志):
    '可重连的访问快照流。载体丢失保留上一份，终态失败按所有者与否处理'
    开流=获取内部数据(远程,'stream')#逻辑流工厂
    访问=getattr(远程,'remoteAccess')#已挂上的命名空间
    流=开流({
        'name':'Remote access stream',#诊断名
        'open':lambda 信号:访问.follow(信号),#打开代际
        'ended':lambda 已接受:远程流载体错误('Remote access stream ended without a terminal result') if 已接受 else RuntimeError('Remote access stream ended before its opening snapshot'),#缺终态
    })
    def 失败(错误):
        '终态失败。所有者答案不变'
        if 状态.是所有者:#所有者
            日志.错误('access snapshot stream failed; owner access answers are unaffected',错误)#不影响
        else:#非所有者
            日志.错误('access snapshot stream failed; reload the page to reconnect',错误)#需要重载
        状态.标记不可用()#非所有者改为不允许
    return 远程快照流(流,{
        'name':'Remote access stream',#诊断名
        'isSnapshot':lambda 帧:帧['type']=='baseline',#开口帧
        'replace':状态.替换基线,#换基线
        'update':状态.更新帧,#增量
        'failed':失败,#终态
    })
