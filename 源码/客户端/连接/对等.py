'本宿主应答的一个操作方。连接寿命持有，每次远程调用作为 invocation.peer'
import uuid#第 4 版标识
from ...内核.作用域 import 创建作用域#作用域纤程
from .异常 import 连接错误#拆除原因
from .rpc import 中止控制器,同步等待#寿命信号与拆除期约


class 对等:
    '操作方自己的作用域。实例就是作用域键'
    def __init__(自身,拥有,选项):
        '作用域纤程挂在拥有者下面。不写 interactions 时为 answer'
        自身.principal=选项['principal']#固定身份
        if 'interactions' in 选项 and 选项['interactions'] is not None:#写了参与方式
            自身.interactions=选项['interactions']#answer 或 none
        else:#没写
            自身.interactions='answer'#默认可应答
        自身.id=str(uuid.uuid4())#对等标识
        作用域对象=创建作用域(拥有,自身)#铸造作用域
        自身._作用域=作用域对象#拆除时用
        自身.ctx=作用域对象.上下文#作用域上下文
        控制器=中止控制器()#寿命
        自身.signal=控制器.signal#中止信号

        def 寿命():
            '作用域结束时中止，无论是 dispose 还是拥有者卸载'
            def 清理():
                '中止这条对等寿命'
                控制器.abort(连接错误('Peer '+自身.id+' was disposed'))#原因带上标识
            return 清理#拆除器

        自身.ctx.副作用(寿命,'client-connection: Peer lifetime')#随作用域拆除

    def dispose(自身):
        '拆除连接寿命内的全部登记。竞态调用共用一次完成'
        return 同步等待(自身._作用域.拆除())#等到作用域静止
