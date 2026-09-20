"""可重连 Remote 流上的游标、分页与实时尾随协调。"""
import threading#消费线程与页读竞态
from concurrent.futures import Future as 原生结果,wait as 等待完成,FIRST_COMPLETED as 先完成
from .流载体 import 远程流载体错误#载体错误
from .网关 import 已中止#中止查询

__all__=[#仅中文公开名
    '远程日志流','远程流工厂字段',
]#公开面结束

远程流工厂字段=('$stream',)#流工厂面


def _协议违规(消息):
    """Host 侧流协议违规。"""
    错误=RuntimeError(消息)#错误
    错误.name='RemoteError'#名
    错误.code='gateway/internal'#码
    return 错误


class 远程日志流:
    """拥有快照优先开口、有序实时投递、分页与修复。

    子类实现 follow / readPage / repairRequest。
    """

    def __init__(自身,远程,选项):
        """远程须提供 $stream；选项含 name/emptyCursor/entries/hasMore/first/last/compare/follows/publish/failed。"""
        自身._选项=选项#选项
        自身._初始请求=None#开口请求
        自身._恢复游标=None#恢复
        自身._有恢复游标=False#旗
        自身._代际=0#代际
        自身._首游标=None#首
        自身._末游标=None#末
        自身._已启动=False
        自身._已打开=False
        自身._已拆除=False#拆除
        自身._完成=None#消费完成 Event
        自身._挂起下一步=None#单步挂起
        自身._迭代器=None#底层迭代
        开流=getattr(远程,'$stream',None)#工厂
        if 开流 is None:#无
            raise RuntimeError(选项['name']+' requires remote.$stream')#拒绝
        流选项={
            'name':选项['name'],
            'open':lambda 信号:自身.跟随(自身._初始请求,信号),
            'ended':lambda 已接受:远程流载体错误(选项['name']+' ended without a terminal result') if 已接受 else _协议违规(
                ('resumed ' if 自身._有恢复游标 else '')+选项['name']+' ended before its opening cursor'
            ),
        }#流选项
        if 'carrierFailed' in 选项 and 选项['carrierFailed'] is not None:#有回调
            流选项['carrierFailed']=选项['carrierFailed']#带上
        自身._流=开流(流选项)#建流

    def 跟随(自身,请求,信号):
        """子类：打开物理代际，产出 opened/entry/notification 帧。"""
        raise NotImplementedError('RemoteJournalStream.follow')#抽象

    def 读页(自身,请求,含末,信号):
        """子类：读一页。"""
        raise NotImplementedError('RemoteJournalStream.readPage')#抽象

    def 修复请求(自身,初始):
        """子类：从初始导出无界尾请求。"""
        raise NotImplementedError('RemoteJournalStream.repairRequest')

    @property
    def signal(自身):
        """共享取消。"""
        return 自身._流.signal

    def open(自身,请求=None):
        """建立跟随并发布首帧开口快照。"""
        if 自身._已启动:#重复
            raise RuntimeError(自身._选项['name']+' already opened')#拒绝
        自身._已启动=True#标记
        自身._初始请求={} if 请求 is None else 请求#请求
        自身._迭代器=iter(自身._流)#迭代
        try:
            首=自身._取得下一步()#首项
            if 首 is None:
                raise _协议违规(自身._选项['name']+' ended before its opening cursor')#违规
            自身._替换代际(首,False)#开口
            自身._已打开=True
            自身._完成=threading.Event()#完成旗
            线=threading.Thread(target=自身._消费,daemon=True,name='dsh-remote-journal')#泵
            线.start()#启
        except BaseException:
            自身._流.dispose()#拆
            raise#抛

    def prepend(自身,请求):
        """前置更旧页。"""
        if not 自身._已打开 or 自身._已拆除:#未开
            raise RuntimeError(自身._选项['name']+' is not open')#拒绝
        页=自身.读页(请求,自身._当前游标(),自身._流.signal)#读
        if 已中止(自身._流.signal):#取消
            raise RuntimeError(自身._选项['name']+' aborted')#中止
        条目=list(自身._选项['entries'](页))#条目
        自身._断言页(条目)#连续
        前=自身._首游标#前界
        if 前 is None:#空窗
            接受=条目#全收
        else:
            接受=[e for e in 条目 if 自身._选项['compare'](自身._选项['first'](e),前)<0]#更旧
        if len(接受)>0 and 前 is not None:#有尾
            尾=接受[-1]#尾
            if not 自身._选项['follows'](自身._选项['last'](尾),前):#不连续
                自身._选项['publish']({'type':'prepend','page':页,'entries':[],'hasMore':False})#空前置
                raise _协议违规(自身._选项['name']+' history page is discontinuous')#违规
        if len(接受)>0:#更新首
            自身._首游标=自身._选项['first'](接受[0])#首
        自身._选项['publish']({
            'type':'prepend',
            'page':页,
            'entries':接受,
            'hasMore':自身._选项['hasMore'](页),
        })#发布

    def restart(自身):
        """替换物理代际。"""
        自身._流.restart()

    def dispose(自身):
        """永久停止。"""
        if 自身._已拆除 and 自身._完成 is not None and 自身._完成.is_set():#已静
            return#空
        自身._已拆除=True#标记
        自身._流.dispose()#拆底层
        if 自身._完成 is not None:#有消费
            自身._完成.wait(timeout=30)

    def _消费(自身):
        """后台消费。"""
        try:
            while True:#循环
                下=自身._取得下一步()#下一项
                if 下 is None:
                    return#停
                if 下.generation!=自身._代际:#换代
                    自身._替换代际(下,True)#恢复替换
                    continue#继续
                帧=下.value#帧
                if 帧['type']=='opened':#重复开口
                    raise _协议违规(自身._选项['name']+' emitted more than one opening cursor')#违规
                if 帧['type']=='notification':#通知
                    自身._发布通知(帧['notification'])#发布
                    continue#下
                自身._接受条目(帧['entry'],下)#条目
        except BaseException as 错误:
            if not 自身._已拆除:#未拆
                自身._选项['failed'](错误)
        finally:
            if 自身._完成 is not None:#有旗
                自身._完成.set()#结算

    def _替换代际(自身,项,已恢复):
        """从开口项替换代际窗口。"""
        开口=自身._开口(项,已恢复)#开口
        自身._从开口替换(开口['page'],开口['cursor'])#发布

    def _开口(自身,项,已恢复):
        """校验并接受开口帧。"""
        帧=项.value#帧
        if 帧['type']!='opened':#非开口
            raise _协议违规(('resumed ' if 已恢复 else '')+自身._选项['name']+' emitted an entry before its opening cursor')#违规
        游标=帧['cursor']#游标
        if 已恢复 and 自身._末游标 is not None:#恢复不得落后
            if 自身._选项['compare'](游标,自身._末游标)<0:#落后
                raise _协议违规(自身._选项['name']+' resumed at a cursor behind the last applied entry')#违规
        自身._代际=项.generation#代际
        项.accept()#接受
        return {'cursor':游标,'page':帧['page']}#开口

    def _从开口替换(自身,页,游标):
        """发布开口页。"""
        自身._断言页截止(页,游标)#截止
        条目=list(自身._选项['entries'](页))#条目
        自身._断言页(条目)#连续
        自身._首游标=None if len(条目)==0 else 自身._选项['first'](条目[0])#首
        自身._末游标=游标#末
        自身._设恢复游标(游标)#恢复
        自身._选项['publish']({
            'type':'replace',
            'page':页,
            'entries':条目,
            'hasMore':自身._选项['hasMore'](页),
        })#发布

    def _接受条目(自身,条目,项):
        """接受实时条目或缺口修复。"""
        首=自身._选项['first'](条目)#首
        游标=自身._选项['last'](条目)#末
        末=自身._末游标#当前末
        if 自身._选项['compare'](游标,末)<=0:#已覆盖
            return#忽略
        if 自身._选项['compare'](首,末)<=0:#部分重叠
            raise _协议违规(自身._选项['name']+' emitted a partially overlapping entry')#违规
        if not 自身._选项['follows'](末,首):#缺口
            请求=自身.修复请求(自身._初始请求)#修复
            取代=自身._经游标替换(请求,游标,项.generation,项.signal,[条目],[])#修复
            if 取代 is not None:#被新代取代
                自身._替换代际(取代,True)#换代
            return
        if 自身._首游标 is None:#空窗首条
            自身._首游标=首#首
        自身._末游标=游标#推进
        自身._设恢复游标(游标)#恢复
        自身._选项['publish']({'type':'append','entry':条目})#追加

    def _经游标替换(自身,请求,所需游标,代际,信号,排队,通知列表):
        """缺口修复：跟随中读页（与流项竞态）并合并排队条目。"""
        读=自身._跟随中读页(请求,所需游标,代际,信号,排队,通知列表)#竞态读页
        if 读['type']=='superseded':#被新代取代
            return 读['item']
        页=读['page']#页
        自身._断言页截止(页,所需游标)#截止
        条目=自身._合并替换(页,排队)#合并
        目标=自身._最大游标(所需游标,排队)#目标
        if 条目 is None or 自身._选项['compare'](自身._尾游标(条目),目标)<0:#不够
            读=自身._跟随中读页(自身.修复请求(自身._初始请求),目标,代际,信号,排队,通知列表)#再竞态读
            if 读['type']=='superseded':#被新代取代
                return 读['item']
            页=读['page']#页
            自身._断言页截止(页,目标)#截止
            条目=自身._合并替换(页,排队)#合并
            目标=自身._最大游标(所需游标,排队)#目标
        if 条目 is None or 自身._选项['compare'](自身._尾游标(条目),目标)<0:#仍不够
            raise _协议违规(自身._选项['name']+' page did not reach its opening cursor')#违规
        自身._首游标=None if len(条目)==0 else 自身._选项['first'](条目[0])#首
        自身._末游标=自身._尾游标(条目)#末
        自身._设恢复游标(自身._末游标)#恢复
        自身._选项['publish']({
            'type':'replace',
            'page':页,
            'entries':条目,
            'hasMore':自身._选项['hasMore'](页),
        })#发布
        for 通知 in 通知列表:#补通知
            自身._发布通知(通知)#发布
        return None#成功

    def _跟随中读页(自身,请求,含末,代际,信号,排队,通知列表):
        """读页与流下一步竞态：同代条目入队，换代则 superseded。"""
        页未来=原生结果()
        def 读页线程():
            """后台读页。"""
            try:
                页未来.set_result(('page',自身.读页(请求,含末,信号)))#成功
            except BaseException as 错误:
                页未来.set_result(('page-error',错误))#失败装箱，供竞态分类
        threading.Thread(target=读页线程,daemon=True,name='dsh-journal-page').start()#启页读
        while True:#直至页到或换代
            下未来=自身._下一步结果()#挂起或新建下一步
            完成,_=等待完成((页未来,下未来),return_when=先完成)
            if 页未来 in 完成:#页先到（并列时优先页）
                种类,载荷=页未来.result()#取页结果
                if 种类=='page':#成功页
                    if 已中止(信号):#页后取消
                        raise RuntimeError(自身._选项['name']+' aborted while reading page')#中止
                    return {'type':'page','page':载荷}#页
                # page-error：若仅页请求取消且流仍活，改等换代
                if (not 已中止(信号)) or 已中止(自身._流.signal):#真失败
                    raise 载荷#抛页错
                return 自身._等待替换代际(代际,下未来)#等新代
            自身._释放下一步()#下一步赢：释放挂起槽
            try:
                种类,载荷=下未来.result()#取流项
            except BaseException:
                raise#流错
            if 种类=='done':#流结束
                if 已中止(信号):#取消优先
                    raise RuntimeError(自身._选项['name']+' aborted while reading page')#中止
                raise _协议违规(自身._选项['name']+' ended while reading its replacement page')#违规
            项=载荷#流项
            if 项.generation!=代际:#换代
                return {'type':'superseded','item':项}#被取代
            帧=项.value#帧
            if 帧['type']=='opened':#重复开口
                raise _协议违规(自身._选项['name']+' emitted more than one opening cursor')#违规
            if 帧['type']=='notification':#通知入队
                通知列表.append(帧['notification'])#排队通知
                continue#再竞态
            排队.append(帧['entry'])#同代条目入队

    def _等待替换代际(自身,代际,初始未来):
        """页因取消失败后，排空当前代直至见到新代项。"""
        挂起=初始未来#当前下一步
        while True:#直至换代
            try:
                种类,载荷=挂起.result()#等一步
            finally:
                自身._释放下一步()#释放槽
            if 种类=='done':#流结束
                if 已中止(自身._流.signal):#流取消
                    raise RuntimeError(自身._选项['name']+' aborted while replacing an aborted page generation')#中止
                raise _协议违规(自身._选项['name']+' ended while replacing an aborted page generation')#违规
            项=载荷#流项
            if 项.generation!=代际:#换代
                return {'type':'superseded','item':项}#被取代
            if 项.value['type']=='opened':#重复开口
                raise _协议违规(自身._选项['name']+' emitted more than one opening cursor')#违规
            挂起=自身._下一步结果()#再取下一步

    def _合并替换(自身,页,排队):
        """合并页与排队实时条目。"""
        条目=list(自身._选项['entries'](页))#页条目
        自身._断言页(条目)#连续
        for 条目项 in 排队:#校验范围
            自身._条目范围(条目项)#范围
        排序=sorted(排队,key=lambda e:自身._选项['first'](e))#按首排
        尾=自身._尾游标(条目)#尾
        for 条目项 in 排序:#合并
            首=自身._选项['first'](条目项)#首
            末=自身._选项['last'](条目项)#末
            if 自身._选项['compare'](末,尾)<=0:#已覆盖
                continue#跳
            if 自身._选项['compare'](首,尾)<=0:#部分重叠
                raise _协议违规(自身._选项['name']+' replacement contains a partially overlapping entry')#违规
            if not 自身._选项['follows'](尾,首):#缺口
                return None
            条目.append(条目项)#追加
            尾=末#推进
        return 条目#合并结果

    def _最大游标(自身,游标,条目列表):
        """取最大末游标。"""
        结果=游标#初
        for 条目 in 条目列表:#扫
            候选=自身._选项['last'](条目)#末
            if 自身._选项['compare'](候选,结果)>0:#更大
                结果=候选#更新
        return 结果#最大

    def _下一步结果(自身):
        """确保至多一个挂起的流下一步。"""
        if 自身._挂起下一步 is not None:#已有挂起
            return 自身._挂起下一步#复用
        未来=原生结果()
        def 取下线程():
            """阻塞取迭代器下一项。"""
            try:
                try:
                    未来.set_result(('item',next(自身._迭代器)))#下一项
                except StopIteration:
                    未来.set_result(('done',None))
            except BaseException as 错误:
                if not 未来.done():#尚未结算
                    未来.set_exception(错误)#流错
        threading.Thread(target=取下线程,daemon=True,name='dsh-journal-next').start()#启
        自身._挂起下一步=未来#挂起
        return 未来

    def _释放下一步(自身):
        """释放挂起下一步槽，使下次可再取。"""
        自身._挂起下一步=None#清空

    def _取得下一步(自身):
        """阻塞取下一项；结束返回 None。页读竞态未消费的挂起项在此复用。"""
        未来=自身._下一步结果()#挂起或新建
        try:
            种类,载荷=未来.result()
        finally:
            自身._释放下一步()#释放槽
        if 种类=='done':
            return None#无
        return 载荷#流项

    def _发布通知(自身,通知):
        """发布无游标通知。"""
        自身._选项['publish']({'type':'notification','notification':通知})#发布

    def _设恢复游标(自身,游标):
        """记下恢复游标。"""
        自身._恢复游标=游标#游标
        自身._有恢复游标=True#旗

    def _当前游标(自身):
        """当前恢复游标。"""
        return 自身._恢复游标#游标

    def _尾游标(自身,条目列表):
        """页尾游标。"""
        if len(条目列表)==0:#空
            return 自身._选项['emptyCursor']#空游标
        return 自身._选项['last'](条目列表[-1])#末

    def _断言页(自身,条目列表):
        """断言页内连续。"""
        if len(条目列表)==0:#空
            return#过
        前=自身._条目范围(条目列表[0])#首范围
        for 条目 in 条目列表[1:]:#后续
            现=自身._条目范围(条目)#范围
            if not 自身._选项['follows'](前['last'],现['first']):#不连续
                raise _协议违规(自身._选项['name']+' page contains discontinuous entries')#违规
            前=现#推进

    def _条目范围(自身,条目):
        """条目游标范围。"""
        首=自身._选项['first'](条目)#首
        末=自身._选项['last'](条目)#末
        if 自身._选项['compare'](首,末)>0:#倒置
            raise _协议违规(自身._选项['name']+' entry has an inverted cursor range')#违规
        return {'first':首,'last':末}#范围

    def _断言页截止(自身,页,含末):
        """页尾须等于请求游标。"""
        尾=自身._尾游标(自身._选项['entries'](页))#尾
        if 自身._选项['compare'](尾,含末)!=0:#不符
            raise _协议违规(自身._选项['name']+' page did not end at its requested cursor')#违规
