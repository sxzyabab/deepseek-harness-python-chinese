'完整程序化工具调用的取消与结算，含嵌套工具'
import threading#调用完成与取消
from ..智能体循环.中止与并发 import 中止控制器,已中止,合成信号#调用自己的取消

class 代码调用:
    '策略变了之后，新调用要等被取消的前一次落定'
    def __init__(自身,上下文):
        '监听沙箱模式变化，拆除时取消并等全部调用'
        自身.调用表={}#会话到进行中的调用
        自身.已拆除=False#登记表已拆
        def 会话事件(会话,事件):
            '模式变了就取消还停在旧模式上的调用'
            if 事件['type']!='sandbox/mode':#不是模式变化
                return#忽略
            for 调用 in 自身.调用表.get(会话.id,()):#这一会话
                if 调用['mode']!=事件['data']['mode']:#还是旧模式
                    调用['控制器'].中止(RuntimeError('sandbox mode changed'))#取消
        上下文.监听('session/event',会话事件,{'global':True})#全局
        def 登记拆除():
            '拆除时取消并等待全部调用'
            def 拆除():
                '先取消，再等它们的完成'
                自身.已拆除=True#不再接纳
                全部=[]#摊平
                for 集合 in 自身.调用表.values():#每个会话
                    全部.extend(集合)#收进来
                for 调用 in 全部:#逐个取消
                    调用['控制器'].中止(RuntimeError('PTC tool registry disposed'))#登记表已拆
                for 调用 in 全部:#再等
                    调用['完成'].wait()#落定
            return 拆除#交给纤程
        上下文.副作用(登记拆除,'PTC calls')#生命周期

    def 运行(自身,会话标识,信号,取模式,执行):
        '先等已取消的前一次，再按当前模式接纳这次调用'
        while True:#等前一次清理完
            待等=[调用 for 调用 in 自身.调用表.get(会话标识,()) if 已中止(调用['控制器'].信号)]#已取消还没走完
            if len(待等)==0:#没有
                break#可以接纳
            for 调用 in 待等:#等它们
                调用['完成'].wait()#落定
        if 已中止(信号):#调用方已取消
            raise RuntimeError('aborted')#不再开始
        if 自身.已拆除:#登记表没了
            raise RuntimeError('PTC tool registry disposed')#拒绝
        控制器=中止控制器()#这次调用
        完成=threading.Event()#结算
        调用={'mode':取模式(),'控制器':控制器,'完成':完成}#记录
        集合=自身.调用表.get(会话标识)#这一会话
        if 集合 is None:#还没有
            集合=set()#新建
            自身.调用表[会话标识]=集合#记下
        集合.add(调用)#纳入
        try:#无论成败都摘掉
            return 执行(合成信号(信号,控制器.信号))#含嵌套清理
        finally:#摘掉并标完成
            集合.discard(调用)#离开
            if len(集合)==0:#空了
                自身.调用表.pop(会话标识,None)#去掉会话
            完成.set()#前一次可以继续
