from ....客户端.模块.客户端.通告 import 取握手窗口
import threading#阻塞到页面定时器
import time#纪元毫秒
from ....依赖.cordis.服务 import 服务#服务基类
from ..异常 import 错误#已拆除的等待


__all__=['客户端定时器服务']


def 现在毫秒():
    '页面 Date.now 的毫秒'
    return time.time()*1000


class 客户端定时器服务(服务):
    '浏览器定时服务。公开动词与宿主 TimerService 相同，定时器跟当前纤程一起拆'
    def __init__(自身,上下文):
        '登记 timer，并把生命周期内安全的助手混进上下文'
        服务.__init__(自身,上下文,'timer')#服务名保持 timer
        上下文.混入成员('timer',{#中文方法挂到上游动词
            '超时':'timeout',
            '间隔':'interval',
            '节流':'throttle',
            '防抖':'debounce',
            '设置超时':'setTimeout',
            '设置间隔':'setInterval',
        })

    def 设置超时(自身,回调,延迟):
        '延迟一次。请改用 timeout'
        return 自身.超时(回调,延迟)

    def 设置间隔(自身,回调,延迟):
        '反复执行。请改用 interval'
        return 自身.间隔(回调,延迟)

    def 超时(自身,*位置参数):
        '有回调则延迟一次并返回拆除器；只有延迟则阻塞到触发或纤程拆除'
        窗口=取握手窗口()#页面定时器
        回调=位置参数[0] if len(位置参数)>0 and callable(位置参数[0]) else None#回调形
        延迟=位置参数[1] if 回调 is not None else 位置参数[0]#毫秒
        if 回调 is not None:#回调形
            拆除箱=[]#副作用返回后才能拆
            def 执行体():
                '到点先拆本副作用，再跑回调'
                def 到点():
                    '拆掉登记再跑'
                    拆除箱[0]()#先拆
                    回调()#再跑
                编号=窗口.setTimeout(到点,延迟)#页面定时器
                def 取消():
                    '取消尚未触发的一次'
                    窗口.clearTimeout(编号)#清掉
                return 取消
            拆除箱.append(自身.ctx.副作用(执行体,'ctx.timeout()'))#跟纤程走
            return 拆除箱[0]
        完成=threading.Event()#等待形门闩
        完成箱={'拒绝':False,'已有':False}#谁先到
        def 执行体():
            '到点放行；拆除则拒绝'
            def 到点():
                '定时器先到'
                if 完成箱['已有']:#已经有结果
                    return
                完成箱['已有']=True#放行
                完成.set()#放行等待
            编号=窗口.setTimeout(到点,延迟)#页面定时器
            def 取消():
                '纤程先拆则拒绝这次等待'
                窗口.clearTimeout(编号)#清掉
                if 完成箱['已有']:#已经触发
                    return
                完成箱['已有']=True#结束等待
                完成箱['拒绝']=True#记拒绝
                完成.set()#放行等待
            return 取消
        拆除=自身.ctx.副作用(执行体,'ctx.timeout()')#跟纤程走
        完成.wait()#阻塞到触发或拆除
        拆除()#触发后拆掉副作用
        if 完成箱['拒绝']:#纤程已拆
            raise 错误('Context has been disposed')
        return None

    def 间隔(自身,*位置参数):
        '有回调则反复执行并返回拆除器；只有延迟则返回可阻塞迭代的间隔'
        窗口=取握手窗口()#页面定时器
        回调=位置参数[0] if len(位置参数)>0 and callable(位置参数[0]) else None#回调形
        延迟=位置参数[1] if 回调 is not None else 位置参数[0]#毫秒
        if 回调 is not None:#回调形
            def 执行体():
                '按间隔跑回调，拆除时停掉'
                编号=窗口.setInterval(回调,延迟)#页面间隔
                def 取消():
                    '停掉间隔'
                    窗口.clearInterval(编号)#清掉
                return 取消
            return 自身.ctx.副作用(执行体,'ctx.interval()')#跟纤程走
        return 间隔迭代(自身,延迟)#等待形

    def 安排(自身,标签,触发,已拆=False):
        '延迟包装。等待中的定时器属于调用方纤程'
        窗口=取握手窗口()#页面定时器
        状态={'已拆':bool(已拆),'编号':None}#包装状态
        def 执行体():
            '纤程拆除时取消等待中的定时器'
            def 取消():
                '标记已拆并清定时器'
                状态['已拆']=True#之后不再排
                窗口.clearTimeout(状态['编号'])#清掉
            return 取消
        拆除=自身.ctx.副作用(执行体,标签)#跟纤程走
        def 包装(*位置参数):
            '清掉上一拍，按触发函数重排'
            窗口.clearTimeout(状态['编号'])#清上一拍
            状态['编号']=触发(位置参数,状态['已拆'])#新的一拍，可能是空
        包装.dispose=拆除#上游拆除槽
        return 包装

    def 节流(自身,回调,延迟,无尾随=False):
        '最小间隔。无尾随则不要延迟的那一次'
        def 执行(*位置参数):
            '记时间并跑回调'
            状态['上次']=现在毫秒()#本拍时间
            回调(*位置参数)#跑
        def 触发(位置参数,已拆):
            '到间隔就立刻跑，否则排尾随'
            剩余=延迟-现在毫秒()+状态['上次']#还要等多久
            if 剩余<=0:#间隔已过
                执行(*位置参数)#立刻跑
                return None
            if 已拆:#不要尾随
                return None
            窗口=取握手窗口()#页面定时器
            return 窗口.setTimeout(执行,剩余,*位置参数)#尾随
        状态={'上次':float('-inf')}#还没跑过
        return 自身.安排('ctx.throttle()',触发,无尾随)#包装

    def 防抖(自身,回调,延迟):
        '安静期过了再跑'
        def 触发(位置参数,已拆):
            '没拆就重排一拍'
            if 已拆:#纤程已拆
                return None
            窗口=取握手窗口()#页面定时器
            return 窗口.setTimeout(回调,延迟,*位置参数)#安静期
        return 自身.安排('ctx.debounce()',触发)#包装


class 间隔迭代:
    '只有延迟的 interval。next 阻塞到下一拍，return 与 throw 结束迭代'
    def __init__(自身,服务,延迟):
        '挂上页面间隔。纤程拆除时以错误结束'
        自身._完=None#return 或 throw
        自身._拍=threading.Event()#有一拍还没被 next 取走
        窗口=取握手窗口()#页面定时器
        def 执行体():
            '每一拍放行一个 next；拆除时抛已拆除'
            def 一拍():
                '放行正在等的 next'
                自身._拍.set()#有值
            编号=窗口.setInterval(一拍,延迟)#页面间隔
            def 取消():
                '停间隔。还没结束就记成已拆除'
                窗口.clearInterval(编号)#清掉
                if 自身._完 is None:#还没主动结束
                    自身._完={'种类':'throw','原因':错误('Context has been disposed')}#已拆除
                自身._拍.set()#放行 next
            return 取消
        自身._拆除=服务.ctx.副作用(执行体,'ctx.interval()')#跟纤程走

    def next(自身):
        '下一拍。已经结束则返回或抛出'
        if 自身._完 is None:#还在跑
            自身._拍.wait()#阻塞到一拍或结束
            自身._拍.clear()#这一拍取走
            if 自身._完 is None:#还在跑
                return {'done':False,'value':None}
        if 自身._完['种类']=='return':#主动结束
            return {'done':True,'value':自身._完['值']}
        raise 自身._完['原因']#已拆除或 throw

    def return_(自身,值=None):
        '结束迭代并拆掉间隔'
        if 自身._完 is None:#还没结束
            自身._完={'种类':'return','值':值}#记下
        自身._拆除()#拆纤程登记
        return {'done':True,'value':值}

    def throw(自身,原因=None):
        '以这个原因结束，并拆掉间隔'
        if 自身._完 is None:#还没结束
            自身._完={'种类':'throw','原因':原因}#记下
        自身._拆除()#拆纤程登记
        return {'done':True,'value':None}
