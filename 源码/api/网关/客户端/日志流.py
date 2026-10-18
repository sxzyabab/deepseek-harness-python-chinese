'可重连 Remote 流上的游标、分页与实时尾随'
import threading#页读取和流下一步赛跑
from ..异常 import 协议违规,远程流载体错误#协议违规与载体结束
from ..流协议 import 已中止#取消
from .远程流 import 远程流#可重连流

class 远程日志流:
    '快照优先的开口、有序实时投递、分页和缺口修复'
    def __init__(自身,远程,选项):
        '远程提供 $stream。选项含游标运算和 publish、failed'
        自身._选项=选项#领域操作
        自身._初始请求=None#打开时记下，供修复
        自身._恢复游标=None#上次发布的游标
        自身._有恢复游标=False#是否有过
        自身._代际=0#当前物理代际
        自身._首游标=None#窗口头
        自身._末游标=None#窗口尾
        自身._已启动=False#open 只一次
        自身._已打开=False#开口已发布
        自身._已拆除=False#拆除后不再报失败
        自身._完成=None#后台消费结束
        自身._关闭=None#dispose 结束
        自身._挂起下一步=None#至多一个未取的 next
        def 打开代际(信号):
            '打开时才读初始请求'
            return 自身.跟随(自身._初始请求,信号)#子类
        def 代际结束(已接受):
            '接受过开口则是载体结束，否则是协议违规'
            if 已接受:#开口已接受
                return 远程流载体错误(选项['name']+' ended without a terminal result')#可重试
            前缀='resumed ' if 自身._有恢复游标 else ''#是否恢复
            return 协议违规(前缀+选项['name']+' ended before its opening cursor')#违规
        流选项={'name':选项['name'],'open':打开代际,'ended':代际结束}#流选项
        if 'carrierFailed' in 选项:#领域要观察载体失败
            流选项['carrierFailed']=选项['carrierFailed']#原样
        自身._流=getattr(远程,'$stream')(流选项)#可重连流

    def 跟随(自身,请求,信号):
        '子类打开物理代际，产出 opened、entry、notification'
        raise NotImplementedError(自身._选项['name']+' follow')#子类

    def 读取页(自身,请求,含末,信号):
        '子类读一页。页尾等于含末，除非领域请求的是更旧的条目'
        raise NotImplementedError(自身._选项['name']+' readPage')#子类

    def 修复请求(自身,初始):
        '子类从初始请求导出无界尾请求'
        raise NotImplementedError(自身._选项['name']+' repairRequest')#子类

    @property
    def signal(自身):
        '跟随和读页共享的取消'
        return 自身._流.signal#信号

    def open(自身,请求):
        '建立跟随并发布第一帧开口'
        if 自身._已启动:#第二次
            raise Exception(自身._选项['name']+' already opened')#拒绝
        自身._已启动=True#占住
        自身._初始请求=请求#修复要用
        迭代=iter(自身._流)#消费者
        try:#开口失败则拆掉流
            第一=自身._取得下一步(迭代)#第一帧
            if 第一 is None:#空
                raise 协议违规(自身._选项['name']+' ended before its opening cursor')#违规
            自身._替换代际(第一,False)#发布开口
            自身._已打开=True#已开
            完成=threading.Event()#后台结束
            def 跑():
                '继续消费'
                try:#消费
                    自身._消费流(迭代)#循环
                finally:#放开
                    完成.set()#结束
            threading.Thread(target=跑,daemon=True).start()#后台
            自身._完成=完成#等
        except Exception:#开口失败
            自身._流.dispose()#拆
            raise#交给调用方

    def prepend(自身,请求):
        '前置更旧的一页'
        if not 自身._已打开 or 自身._已拆除:#没开
            raise Exception(自身._选项['name']+' is not open')#拒绝
        页=自身.读取页(请求,自身._当前游标(),自身._流.signal)#读页
        if 已中止流(自身._流.signal):#取消
            raise Exception('The operation was aborted.')#取消
        条目=自身._选项['entries'](页)#条目
        自身._断言页(条目)#连续
        之前=自身._首游标#当前头
        if 之前 is None:#还没有头
            接受=list(条目)#整页
        else:#只要比头更旧的
            接受=[项 for 项 in 条目 if 自身._选项['compare'](自身._选项['first'](项),之前)<0]#更旧
        尾=接受[-1] if len(接受)>0 else None#接受段的尾
        if 尾 is not None and 之前 is not None and not 自身._选项['follows'](自身._选项['last'](尾),之前):#接不上
            自身._选项['publish']({'type':'prepend','page':页,'entries':[],'hasMore':False})#空发布
            raise 协议违规(自身._选项['name']+' history page is discontinuous')#违规
        if len(接受)>0:#有条目
            自身._首游标=自身._选项['first'](接受[0])#新的头
        自身._选项['publish']({#发布
            'type':'prepend',
            'page':页,
            'entries':接受,
            'hasMore':自身._选项['hasMore'](页),
        })#发布结束

    def restart(自身):
        '替换物理代际，已发布的窗口留着'
        自身._流.restart()#换代

    def dispose(自身):
        '永久停止跟随、读页和后台消费'
        if 自身._关闭 is not None:#已经在关
            自身._关闭.wait()#等
            return#完
        自身._已拆除=True#不再报失败
        自身._关闭=threading.Event()#这一次
        自身._流.dispose()#停流
        if 自身._完成 is not None:#后台已启动
            自身._完成.wait()#等
        自身._关闭.set()#完成

    def _消费流(自身,迭代):
        '开口之后的实时条目'
        try:#失败交给领域
            while True:#直到流结束
                下一项=自身._取得下一步(迭代)#下一项
                if 下一项 is None:#结束
                    return#停
                if 下一项.generation!=自身._代际:#新代际
                    自身._替换代际(下一项,True)#替换窗口
                    continue#下一
                if 下一项.value['type']=='opened':#第二张开口
                    raise 协议违规(自身._选项['name']+' emitted more than one opening cursor')#违规
                if 下一项.value['type']=='notification':#无游标通知
                    自身._发布通知(下一项.value['notification'])#发布
                    continue#下一
                自身._接受条目(下一项.value['entry'],下一项,迭代)#实时条目
        except Exception as 错误:#终端
            if not 自身._已拆除:#不是拆除
                自身._选项['failed'](错误)#交给领域

    def _替换代际(自身,初始,已恢复):
        '从开口项替换代际窗口'
        开口=自身._接受开口帧(初始,已恢复)#校验
        自身._从开口替换(开口['page'],开口['cursor'])#发布

    def _接受开口帧(自身,项,已恢复):
        '开口帧必须是 opened，恢复游标不能倒退'
        if 项.value['type']!='opened':#不是开口
            前缀='resumed ' if 已恢复 else ''#恢复前缀
            raise 协议违规(前缀+自身._选项['name']+' emitted an entry before its opening cursor')#违规
        游标=项.value['cursor']#游标
        if 已恢复 and 自身._末游标 is not None and 自身._选项['compare'](游标,自身._末游标)<0:#倒退
            raise 协议违规(自身._选项['name']+' resumed at a cursor behind the last applied entry')#违规
        自身._代际=项.generation#换代
        项.accept()#接受
        return {'cursor':游标,'page':项.value['page']}#开口

    def _从开口替换(自身,页,游标):
        '发布开口页，不再另打一次远程调用'
        自身._断言页截止(页,游标)#页尾必须是这个游标
        条目=list(自身._选项['entries'](页))#条目
        自身._断言页(条目)#连续
        自身._首游标=自身._选项['first'](条目[0]) if len(条目)>0 else None#头
        自身._末游标=游标#尾
        自身._设恢复游标(游标)#恢复点
        自身._选项['publish']({#替换
            'type':'replace',
            'page':页,
            'entries':条目,
            'hasMore':自身._选项['hasMore'](页),
        })#发布结束

    def _接受条目(自身,条目,项,迭代):
        '接受实时条目。缺口则读页修复'
        范围=自身._条目范围(条目)#这条的游标
        首=范围['first']#头
        游标=范围['last']#尾
        末=自身._末游标#当前尾
        if 自身._选项['compare'](游标,末)<=0:#不比当前尾新
            return#丢掉
        if 自身._选项['compare'](首,末)<=0:#部分重叠
            raise 协议违规(自身._选项['name']+' emitted a partially overlapping entry')#违规
        if not 自身._选项['follows'](末,首):#中间有缺口
            被取代=自身._经游标替换(自身._修复页请求(),游标,项.generation,项.signal,迭代,[条目],[])#修复
            if 被取代 is not None:#读页期间换代了
                自身._替换代际(被取代,True)#用新代际
            return#修复完
        if 自身._首游标 is None:#窗口还没有头
            自身._首游标=首#记下
        自身._末游标=游标#推进
        自身._设恢复游标(游标)#恢复点
        自身._选项['publish']({'type':'append','entry':条目})#追加

    def _经游标替换(自身,请求,所需游标,代际,信号,迭代,排队,通知列表):
        '缺口修复。页和流项赛跑，换代则把新项交回去'
        读到=自身._跟随中读取页(请求,所需游标,代际,信号,迭代,排队,通知列表)#读
        if 读到['type']=='superseded':#换代
            return 读到['item']#交给调用方
        页=读到['page']#页
        自身._断言页截止(页,所需游标)#页尾
        条目=自身._合并替换(页,排队)#合并
        目标=自身._最大游标(所需游标,排队)#要到达的游标
        if 条目 is None or 自身._选项['compare'](自身._尾游标(条目),目标)<0:#没盖住
            读到=自身._跟随中读取页(自身._修复页请求(),目标,代际,信号,迭代,排队,通知列表)#再读无界尾
            if 读到['type']=='superseded':#换代
                return 读到['item']#交回
            页=读到['page']#新页
            自身._断言页截止(页,目标)#页尾
            条目=自身._合并替换(页,排队)#再合并
            目标=自身._最大游标(所需游标,排队)#目标可能没变
        if 条目 is None or 自身._选项['compare'](自身._尾游标(条目),目标)<0:#仍不够
            raise 协议违规(自身._选项['name']+' page did not reach its opening cursor')#违规
        自身._首游标=自身._选项['first'](条目[0]) if len(条目)>0 else None#头
        自身._末游标=自身._尾游标(条目)#尾
        自身._设恢复游标(自身._末游标)#恢复点
        自身._选项['publish']({#替换
            'type':'replace',
            'page':页,
            'entries':条目,
            'hasMore':自身._选项['hasMore'](页),
        })#发布结束
        for 通知 in 通知列表:#修缺口时攒下的通知
            自身._发布通知(通知)#现在发
        return None#没有被换代

    def _跟随中读取页(自身,请求,含末,代际,信号,迭代,排队,通知列表):
        '读页和流下一步赛跑。同代条目入队，换代则 superseded'
        页盒={'完成':threading.Event()}#页
        def 读():
            '后台读页'
            try:#读
                页盒['页']=自身.读取页(请求,含末,信号)#页
                页盒['种类']='page'#成功
            except Exception as 错误:#失败
                页盒['种类']='page-error'#失败
                页盒['错误']=错误#原因
            页盒['完成'].set()#放开
        threading.Thread(target=读,daemon=True).start()#赛跑
        while True:#谁先完成
            下一步=自身._下一步结果(迭代)#至多一个挂起
            if 页盒['完成'].wait(0.05) or 下一步['完成'].is_set():#有一边好了
                if 页盒['完成'].is_set() and 页盒.get('种类')=='page':#页先到
                    if 已中止流(信号):#取消
                        raise Exception('The operation was aborted.')#取消
                    return {'type':'page','page':页盒['页']}#页
                if 页盒['完成'].is_set() and 页盒.get('种类')=='page-error':#页失败
                    if not 已中止流(信号) or 已中止流(自身._流.signal):#不是这一代被取消
                        raise 页盒['错误']#原样
                    return 自身._等待替换代际(代际,迭代,下一步)#等新代际
                if 下一步['完成'].is_set():#流项先到
                    自身._释放下一步()#这一项被取走
                    if '错误' in 下一步:#流抛了
                        raise 下一步['错误']#抛
                    if 下一步.get('结束'):#流结束
                        if 已中止流(信号):#取消
                            raise Exception('The operation was aborted.')#取消
                        raise 协议违规(自身._选项['name']+' ended while reading its replacement page')#违规
                    项=下一步['值']#项
                    if 项.generation!=代际:#换代
                        return {'type':'superseded','item':项}#交回
                    if 项.value['type']=='opened':#第二张开口
                        raise 协议违规(自身._选项['name']+' emitted more than one opening cursor')#违规
                    if 项.value['type']=='notification':#通知先攒着
                        通知列表.append(项.value['notification'])#攒
                        continue#继续等页
                    排队.append(项.value['entry'])#同代条目
                    continue#继续等页

    def _等待替换代际(自身,代际,迭代,初始):
        '页因取消失败后，排空当前代直到见到新代项'
        挂起=初始#已经在飞的下一步
        while True:#直到新代际
            try:#取
                挂起['完成'].wait()#等
                if '错误' in 挂起:#流错误
                    raise 挂起['错误']#抛
                if 挂起.get('结束'):#结束
                    下一项=None#没有
                else:#有项
                    下一项=挂起['值']#项
            finally:#槽释放
                自身._释放下一步()#释放
            if 下一项 is None:#结束
                if 已中止流(自身._流.signal):#整条取消
                    raise Exception('The operation was aborted.')#取消
                raise 协议违规(自身._选项['name']+' ended while replacing an aborted page generation')#违规
            if 下一项.generation!=代际:#新代际
                return {'type':'superseded','item':下一项}#交回
            if 下一项.value['type']=='opened':#不该再来开口
                raise 协议违规(自身._选项['name']+' emitted more than one opening cursor')#违规
            挂起=自身._下一步结果(迭代)#再取

    def _合并替换(自身,页,排队):
        '合并页和排队的实时条目。接不上则 None'
        条目=list(自身._选项['entries'](页))#页内
        自身._断言页(条目)#连续
        for 项 in 排队:#排队的也要范围合法
            自身._条目范围(项)#校验
        手排=list(排队)#拷贝
        for 步 in range(len(手排)):#插入排序，用 compare
            当前=手排[步]#这一项
            位置=步#插入点
            while 位置>0 and 自身._选项['compare'](自身._选项['first'](手排[位置-1]),自身._选项['first'](当前))>0:#更大
                手排[位置]=手排[位置-1]#后移
                位置-=1#左
            手排[位置]=当前#插入
        尾=自身._尾游标(条目)#页尾
        for 项 in 手排:#按顺序接上
            首=自身._选项['first'](项)#头
            末=自身._选项['last'](项)#尾
            if 自身._选项['compare'](末,尾)<=0:#已覆盖
                continue#丢
            if 自身._选项['compare'](首,尾)<=0:#部分重叠
                raise 协议违规(自身._选项['name']+' replacement contains a partially overlapping entry')#违规
            if not 自身._选项['follows'](尾,首):#接不上
                return None#让调用方再读
            条目.append(项)#接上
            尾=末#推进
        return 条目#合并结果

    def _最大游标(自身,游标,条目列表):
        '取最大末游标'
        结果=游标#起点
        for 项 in 条目列表:#逐个
            候选=自身._选项['last'](项)#末
            if 自身._选项['compare'](候选,结果)>0:#更大
                结果=候选#更新
        return 结果#最大

    def _下一步结果(自身,迭代):
        '确保至多一个挂起的流下一步'
        if 自身._挂起下一步 is not None:#已经有
            return 自身._挂起下一步#复用
        盒={'完成':threading.Event()}#结果
        def 跑():
            '阻塞取下一项'
            try:#取
                盒['值']=next(迭代)#项
            except StopIteration:#结束
                盒['结束']=True#结束
            except Exception as 错误:#失败
                盒['错误']=错误#原因
            盒['完成'].set()#放开
        threading.Thread(target=跑,daemon=True).start()#不堵页读取
        自身._挂起下一步=盒#占住
        return 盒#盒

    def _释放下一步(自身):
        '释放挂起槽，使下次可以再取'
        自身._挂起下一步=None#空

    def _取得下一步(自身,迭代):
        '阻塞取下一项。结束返回 None'
        挂起=自身._下一步结果(迭代)#挂起
        try:#等
            挂起['完成'].wait()#阻塞
            if '错误' in 挂起:#失败
                raise 挂起['错误']#抛
            if 挂起.get('结束'):#结束
                return None#没有
            return 挂起['值']#项
        finally:#释放槽
            自身._释放下一步()#释放

    def _发布通知(自身,通知):
        '发布无游标通知'
        自身._选项['publish']({'type':'notification','notification':通知})#发布

    def _修复页请求(自身):
        '从初始请求导出修复请求'
        return 自身.修复请求(自身._初始请求)#子类

    def _设恢复游标(自身,游标):
        '记下恢复游标'
        自身._恢复游标=游标#游标
        自身._有恢复游标=True#有了

    def _当前游标(自身):
        '当前恢复游标'
        return 自身._恢复游标#游标

    def _尾游标(自身,条目列表):
        '页尾游标。空页用空游标'
        if len(条目列表)==0:#空
            return 自身._选项['emptyCursor']#空游标
        return 自身._选项['last'](条目列表[-1])#最后一条的尾

    def _断言页(自身,条目列表):
        '页内条目必须首尾相接'
        if len(条目列表)==0:#空页
            return#通过
        上一=自身._条目范围(条目列表[0])#第一条
        for 项 in 条目列表[1:]:#其余
            范围=自身._条目范围(项)#这一条
            if not 自身._选项['follows'](上一['last'],范围['first']):#断开
                raise 协议违规(自身._选项['name']+' page contains discontinuous entries')#违规
            上一=范围#推进

    def _条目范围(自身,条目):
        '条目的首尾游标。首不能大于尾'
        首=自身._选项['first'](条目)#首
        尾=自身._选项['last'](条目)#尾
        if 自身._选项['compare'](首,尾)>0:#倒了
            raise 协议违规(自身._选项['name']+' entry has an inverted cursor range')#违规
        return {'first':首,'last':尾}#范围

    def _断言页截止(自身,页,含末):
        '页尾必须等于请求游标'
        尾=自身._尾游标(自身._选项['entries'](页))#页尾
        if 自身._选项['compare'](尾,含末)!=0:#不是
            raise 协议违规(自身._选项['name']+' page did not end at its requested cursor')#违规

def 已中止流(信号):
    '信号已中止'
    return 已中止(信号)#是否

__all__=['远程日志流']#公开名
