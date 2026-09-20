"""面向 Gateway 拥有的 Remote 流生命周期的 Session 专用适配器。

经 remote.$stream 走 RemoteSnapshotStream / RemoteJournalStream；
无 $stream 时回退直连 follow/control。
"""
import threading#控制流泵线程
from .会话线事件 import 断言会话线事件#线事件验收
from .历史记录 import 历史条目,历史记录首序号,历史记录末序号#历史辅助
from .助手流 import 客户端助手流#帧→live-chunk（直连回退用）
from ...网关.流载体 import 远程流载体错误#载体错误
from ...网关.快照流 import 远程快照流#快照流
from ...网关.日志流 import 远程日志流#日志流

__all__=[#仅中文公开名
    '会话搜索结果上限','会话搜索摘要最大码点',
    '转会话日志变更','创建会话控制流','会话事件流','客户端助手流',
    '历史条目','历史记录首序号','历史记录末序号',
]#公开面结束

会话搜索结果上限=50#搜索条数上限（对齐 types）
会话搜索摘要最大码点=120#摘要码点上限

def 转会话日志变更(变更):
    """远程变更转会话变更。变更为 dict。"""
    类型=变更['type']#类型
    if 类型=='replace' or 类型=='prepend':#整窗
        结果=dict(变更)#拷
        结果['entries']=历史条目(变更['entries'])#收窄
        return 结果#变更
    if 类型=='append':#追加
        return {'type':'append','entry':变更['entry']}#追加
    if 类型=='notification':#通知即助手流
        return {'type':'assistant-stream','frame':变更['notification']}#助手流
    return 变更#原样

def _有流工厂(远程):
    """远程是否暴露 $stream。"""
    return getattr(远程,'$stream',None) is not None#有

def _取流工厂(远程):
    """取 $stream 可调用。"""
    return getattr(远程,'$stream')#属性

def 创建会话控制流(远程,选项):
    """创建 Host 范围会话控制快照流。

    选项：accept / failed / carrierFailed?。
    有 $stream 时返回远程快照流；否则直连 control 迭代器句柄。
    """
    if not _有流工厂(远程):#回退
        return _直连控制流(远程,选项)#直连
    会话面=远程.session#session
    流选项={
        'name':'session control stream',
        'open':lambda 信号:会话面.control(信号),
        'ended':lambda 已接受:远程流载体错误('session control stream ended without a terminal result') if 已接受 else RuntimeError('session control stream ended before its opening snapshot'),
    }#流选项
    if 'carrierFailed' in 选项 and 选项['carrierFailed'] is not None:#有
        流选项['carrierFailed']=选项['carrierFailed']#带上
    底层=_取流工厂(远程)(流选项)#开监督流
    return 远程快照流(底层,{
        'name':'session control stream',
        'isSnapshot':lambda 帧:帧.get('type')=='baseline',
        'replace':选项['accept'],
        'update':选项['accept'],
        'failed':选项['failed'],
    })#快照流

class _直连控制流句柄:
    """无 $stream 时的直连 control 句柄。"""

    def __init__(自身,远程,选项):
        """记下远程与接收端。"""
        自身._远程=远程#远程
        自身._选项=选项#选项
        自身._已关闭=False#状态
        自身.name='session control stream'#名称

    def start(自身,信号=None):
        """打开控制流并投递帧。"""
        if 自身._已关闭:#已拆
            return#空
        try:
            控制=自身._远程.session.control#控制方法
            for 帧 in 控制(信号):#迭代
                if 自身._已关闭:#已拆
                    break#停
                自身._选项['accept'](帧)#接受
        except BaseException as 错误:
            if 自身._已关闭:#拆除中
                return#吞
            自身._选项['failed'](错误)

    def dispose(自身):
        """标记关闭。"""
        自身._已关闭=True

    def restart(自身):
        """直连无监督代际，空操作。"""
        return

def _直连控制流(远程,选项):
    """无 $stream 时的直连 control。"""
    return _直连控制流句柄(远程,选项)#句柄

class 会话事件流(远程日志流):
    """绑定到普通或直连子智能体会话地址的事件日志。"""

    def __init__(自身,远程,地址,选项):
        """保存远程面、地址与接收端。选项含 publish/failed/carrierFailed?。"""
        if not _有流工厂(远程):#无工厂则薄包装直连
            自身._直连=_直连事件流(远程,地址,选项)#直连
            自身._用直连=True#旗
            return#跳过基类
        自身._用直连=False#网关路径
        自身._远程=远程#远程
        自身._地址=地址#地址
        日志选项={
            'name':'session event stream',
            'emptyCursor':-1,
            'entries':lambda 页:页['records'],
            'hasMore':lambda 页:页['hasMore'],
            'first':历史记录首序号,
            'last':历史记录末序号,
            'compare':lambda 左,右:左-右,
            'follows':lambda 左,右:右==左+1,
            'publish':lambda 变更:选项['publish'](转会话日志变更(变更)),
            'failed':选项['failed'],
        }#日志选项
        if 'carrierFailed' in 选项 and 选项['carrierFailed'] is not None:#有
            日志选项['carrierFailed']=选项['carrierFailed']#带上
        super().__init__(远程,日志选项)#基类

    def 跟随(自身,请求,信号):
        """打开 follow，产出 opened/entry/notification。"""
        助手修订=None#助手修订
        会话面=自身._远程.session#session
        跟随请求={'address':自身._地址,'assistantStream':True}#跟随
        if 请求 is not None and 'maxMessages' in 请求 and 请求['maxMessages'] is not None:#上限
            跟随请求['maxMessages']=请求['maxMessages']#带上
        for 帧 in 会话面.follow(跟随请求,信号):#跟随
            if 帧['type']=='snapshot':#开场
                for 记录 in 帧['records']:#验收
                    断言会话线事件(记录['event'])#线事件
                if 'assistantStream' not in 帧 or 帧['assistantStream'] is None:#缺基线
                    错=RuntimeError('session assistant stream omitted its opted-in opening baseline')#内部
                    错.code='gateway/internal'#码
                    raise 错#抛
                助手修订=帧['assistantStream']['revision']#修订
                yield {
                    'type':'opened',
                    'cursor':帧['cursor'] if 'cursor' in 帧 else (帧['records'][-1]['event']['seq'] if len(帧['records'])>0 else -1),
                    'page':{
                        'records':帧['records'],
                        'hasMore':帧['hasMore'],
                        'projections':帧['projections'] if 'projections' in 帧 else None,
                        'assistantStream':帧['assistantStream'],
                    },
                }#开口
                continue#下帧
            if 帧['type']=='assistant-stream':#助手流
                期望=(助手修订 if 助手修订 is not None else 0)+1#期望
                if 帧['frame']['revision']!=期望:#跳修订
                    raise 远程流载体错误('session assistant stream skipped revision '+str(期望))#载体
                助手修订=帧['frame']['revision']#推进
                yield {'type':'notification','notification':帧['frame']}#通知
                continue#下帧
            断言会话线事件(帧['event'])#验收
            yield {'type':'entry','entry':帧}#条目

    def 读页(自身,请求,含末序号,信号=None):
        """读更早页。"""
        会话面=自身._远程.session#session
        页请求={'address':自身._地址,'throughSeq':含末序号}#页
        if 请求 is not None and 'maxMessages' in 请求 and 请求['maxMessages'] is not None:#上限
            页请求['maxMessages']=请求['maxMessages']#带上
        if 请求 is not None and 'beforeSeq' in 请求:#向前
            页请求['beforeSeq']=请求['beforeSeq']#带上
        结果=会话面.page(页请求,信号)#读页
        if isinstance(结果,dict) and 'ok' in 结果:#信封
            if not 结果['ok']:
                raise 结果['error']#抛
            页=结果['value']#页
        else:#直接页
            页=结果#页
        for 记录 in 页['records']:#验收
            断言会话线事件(记录['event'])#线事件
        return 页#页

    def 修复请求(自身,初始):
        """保留 maxMessages。"""
        if 初始 is None or 'maxMessages' not in 初始 or 初始['maxMessages'] is None:#无
            return {}#空
        return {'maxMessages':初始['maxMessages']}#保留

    def open(自身,请求=None):
        """打开；直连路径走折叠泵。"""
        if 自身._用直连:
            自身._直连.start(请求)
            return
        super().open(请求)

    def dispose(自身):
        """拆除。"""
        if 自身._用直连:
            自身._直连.dispose()
            return
        super().dispose()

    def prepend(自身,请求):
        """前置；直连走读更早页。"""
        if 自身._用直连:#直连
            raise RuntimeError('session event stream direct mode does not support prepend via journal')#拒绝
        super().prepend(请求)#网关

    def 读更早页(自身,请求,含末序号,信号=None):
        """兼容旧调用面。"""
        if 自身._用直连:#直连
            return 自身._直连.读更早页(请求,含末序号,信号)#委托
        return 自身.读页(请求,含末序号,信号)#网关


class _直连事件流:
    """无 $stream 时的直连 follow（保留助手流折叠）。"""

    def __init__(自身,远程,地址,选项):
        """保存远程面、地址与接收端。"""
        自身._远程=远程#远程
        自身._地址=地址#地址
        自身._选项=选项#选项
        自身._助手流=客户端助手流()#呈现折叠
        自身._已关闭=False#拆除
        自身._泵=None#泵线程

    def start(自身,请求=None,信号=None):
        """后台泵 follow。"""
        if 请求 is None:#缺省
            请求={}#空
        if 自身._已关闭:#已拆
            return#空
        自身._泵=threading.Thread(target=lambda:自身._执行跟随泵(请求,信号),daemon=True)#泵
        自身._泵.start()#启

    def _执行跟随泵(自身,请求,信号):
        """打开 follow 并把变更交给 publish。"""
        助手修订=None#助手修订
        try:
            会话面=自身._远程.session#session
            跟随请求={'address':自身._地址,'assistantStream':True}#跟随
            if 'maxMessages' in 请求 and 请求['maxMessages'] is not None:#有上限
                跟随请求['maxMessages']=请求['maxMessages']#带上
            for 帧 in 会话面.follow(跟随请求,信号):#跟随
                if 自身._已关闭:#已拆
                    break#停
                if 帧['type']=='snapshot':#开场
                    for 记录 in 帧['records']:#验收
                        断言会话线事件(记录['event'])#线事件
                    if 'assistantStream' not in 帧 or 帧['assistantStream'] is None:#缺基线
                        raise RuntimeError('session assistant stream omitted its opted-in opening baseline')#内部
                    助手修订=帧['assistantStream']['revision']#修订
                    条目=历史条目(帧['records'])#条目
                    可见=自身._助手流.替换(条目,帧['assistantStream'])#替换窗口
                    自身._选项['publish']({
                        'type':'replace',
                        'page':{
                            'records':帧['records'],
                            'hasMore':帧['hasMore'],
                            'projections':帧['projections'] if 'projections' in 帧 else None,
                            'assistantStream':帧['assistantStream'],
                        },
                        'entries':可见,
                        'hasMore':帧['hasMore'],
                    })#发布替换
                    continue#下帧
                if 帧['type']=='assistant-stream':#助手流
                    期望=(助手修订 if 助手修订 is not None else 0)+1#期望
                    if 帧['frame']['revision']!=期望:#跳修订
                        raise RuntimeError('session assistant stream skipped revision '+str(期望))#载体
                    助手修订=帧['frame']['revision']#推进
                    决策=自身._助手流.接受帧(帧['frame'])#折叠
                    自身._应用决策(决策)#发布
                    continue#下帧
                断言会话线事件(帧['event'])#验收
                决策=自身._助手流.接受耐久({'type':'event','event':帧['event']})#耐久
                自身._应用决策(决策)#发布
        except BaseException as 错误:
            if 自身._已关闭:#拆除中
                return#吞
            自身._选项['failed'](错误)

    def 读更早页(自身,请求,含末序号,信号=None):
        """读更早页。"""
        会话面=自身._远程.session#session
        页请求={'address':自身._地址,'throughSeq':含末序号}#页
        if 请求 is not None and 'maxMessages' in 请求 and 请求['maxMessages'] is not None:#上限
            页请求['maxMessages']=请求['maxMessages']#带上
        if 请求 is not None and 'beforeSeq' in 请求:#向前
            页请求['beforeSeq']=请求['beforeSeq']#带上
        结果=会话面.page(页请求,信号)#读页
        if isinstance(结果,dict) and 'ok' in 结果:#信封
            if not 结果['ok']:
                raise 结果['error']#抛
            页=结果['value']#页
        else:#直接页
            页=结果#页
        for 记录 in 页['records']:#验收
            断言会话线事件(记录['event'])#线事件
        return 页#页

    def dispose(自身):
        """标记关闭。"""
        自身._已关闭=True#关

    def _应用决策(自身,决策):
        """把助手流决策变成日志变更。"""
        if 决策 is None:#无可见
            return#空
        类型=决策['type']#类型
        if 类型=='publish' or 类型=='settlement' or 类型=='transient':#发布类
            自身._选项['publish']({'type':'append','entry':决策['entry']})#追加
            return
        if 类型=='rebaseline':#重基线
            自身._选项['failed'](RuntimeError('session assistant stream requires rebaseline'))
            return
        if 类型=='abandonment':#放弃
            return#无可见条目
