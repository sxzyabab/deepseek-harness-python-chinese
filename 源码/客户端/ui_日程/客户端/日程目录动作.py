import math#向上取整
from nicegui import ui as 界面
from ....基础设施.通用工具 import 当前毫秒
from ..异常 import 页面失败文案
from datetime import datetime as 日期时间
from zoneinfo import ZoneInfo as 时区信息
from .文案 import 命名空间#命名空间
from .日程格式 import 下次运行片段,任务名
from .日程格式 import 格式化日程频率 as 展示频率
from .日程格式 import 排序日程记录 as 按逾期排序

__all__=[#仅中文公开名
    '单位文案','格式化日程频率','格式化日程本地时间','格式化日程相对',
    '排序日程记录','日程目录动作','空记录','秒毫秒','单位秒表','解析日程时刻',
]

空记录=()#无投影时的空表
秒毫秒=1_000#一秒毫秒
秒单位={'unit':'second','seconds':1}#秒单位兜底
单位秒表=(#从大到小的整单位
    {'unit':'day','seconds':86_400},#天
    {'unit':'hour','seconds':3_600},#小时
    {'unit':'minute','seconds':60},#分钟
    秒单位,#秒
)#单位表结束
日程时刻格式='%Y-%m-%dT%H:%M:%S.%fZ'#线协议 scheduledAt
协调世界时=时区信息('UTC')

def 解析日程时刻(原文):
    '把线协议 UTC 时刻翻成纪元毫秒'
    时刻=日期时间.strptime(原文,日程时刻格式).replace(tzinfo=协调世界时)
    return int(时刻.timestamp()*1000)#纪元毫秒

def 缺省翻译(键,_插值=None):
    '无翻译函数时回传键'
    return 键#键即文案

def 单位文案(单位,值,翻译):
    '一个整数量级的本地化单位词'
    键对={#单复数键对
        'day':('unit.day.one','unit.day.other'),#天
        'hour':('unit.hour.one','unit.hour.other'),#小时
        'minute':('unit.minute.one','unit.minute.other'),#分钟
        'second':('unit.second.one','unit.second.other'),#秒
    }#冻结
    对=键对[单位]#取对
    return 翻译(对[0] if 值==1 else 对[1],{'count':值})#单复数键

def 格式化日程频率(记录,翻译):
    '选取最大可整除完整单位，不舍入持久间隔。记录为线协议 dict'
    if 记录['kind']!='every':
        return 翻译('frequency.once')#单次
    选中=秒单位#默认秒
    间隔=记录['everySeconds']#间隔秒
    for 候选 in 单位秒表:
        if 间隔%候选['seconds']!=0:
            continue#跳过
        选中=候选#命中
        break#取最大可整除
    值=间隔//选中['seconds']#整数量
    return 翻译('frequency.every',{'value':值,'unit':单位文案(选中['unit'],值,翻译)})#重复文案

def 格式化日程本地时间(计划于,区域=None):
    '按当地时区格式化持久 UTC 目标'
    时刻=日期时间.strptime(计划于,日程时刻格式).replace(tzinfo=协调世界时)
    本地=时刻.astimezone()#当地时区
    return 本地.strftime('%Y-%m-%d %H:%M')#中等日期+短时间近似

def 格式化日程相对(计划于,现在,翻译):
    '用最大自然时钟单位表达人类相对目标'
    目标=解析日程时刻(计划于)#目标毫秒
    差=目标-现在#差值毫秒
    if 差==0:
        return 翻译('relative.now')#恰到期
    绝对秒=abs(差)/秒毫秒#绝对秒
    选中=秒单位#默认秒
    for 候选 in 单位秒表:
        if 绝对秒>=候选['seconds']:
            选中=候选#选中
            break
    if 差>0:
        值=max(1,math.ceil(绝对秒/选中['seconds']))#向上取整
    else:
        值=max(1,绝对秒//选中['seconds'])#向下取整
    单位=单位文案(选中['unit'],值,翻译)#单位词
    return 翻译('relative.future' if 差>0 else 'relative.overdue',{'value':值,'unit':单位})#相对句

def 排序日程记录(记录列表,现在):
    '逾期在前，再按目标时间升序。完全并列保持稳定'
    def 解析或零(记录):
        '解析 scheduledAt；非法则 0'
        try:
            return 解析日程时刻(记录['scheduledAt'])#毫秒
        except ValueError:
            return 0#非法时刻
    带索引=[{'record':记录,'index':索引} for 索引,记录 in enumerate(记录列表)]#带原索引
    def 排序键(项):
        '逾期优先，再时间，再稳定索引'
        时=解析或零(项['record'])#目标
        return (时>现在,时,项['index'])#逾期在前
    带索引.sort(key=排序键)#逾期优先
    return [项['record'] for 项 in 带索引]#剥掉索引

class 日程目录动作:#页眉动作
    '当前会话的活动提醒：时钟按钮、菜单、打开详情和删除'
    def __init__(自身,属性=None):
        '记下 props 与本地状态'
        自身.属性={} if 属性 is None else 属性#合成
        自身.打开=False#弹层开合
        自身.现在=当前毫秒()#纪元毫秒
        if 'useCatalog' in 自身.属性 and 'useSession' in 自身.属性:
            自身.渲染()#槽位只调用构造，键齐了就画

    def 更新(自身,属性):
        '刷新 props'
        自身.属性={} if 属性 is None else 属性#新

    def 切换目录(自身):
        '刷新时钟并切换开合'
        自身.现在=当前毫秒()#刷新时钟
        自身.打开=not 自身.打开#切换开合
        自身._确保时钟()
        自身.重画()

    def 关闭目录(自身):
        'Escape 关'
        自身.打开=False#关
        自身.重画()

    def 确保订阅(自身):
        '会话或目录变化时重画'
        if getattr(自身,'_已订',False):
            return
        自身._已订=True
        def 变(*_参数):
            '重画触发器'
            if getattr(自身,'_壳',None) is not None:
                自身.重画()
        for 名 in ('useCatalog','useSession'):
            用=自身.属性[名] if 名 in 自身.属性 else None
            订=getattr(用,'_subscribe',None)
            if callable(订):
                订(变)

    def _读(自身,名,选择):
        '钩子缺席则 None'
        用=自身.属性[名] if 名 in 自身.属性 else None
        if not callable(用):
            return None
        try:
            return 用(选择)
        except Exception:
            return None

    def _材料(自身):
        '可见记录、状态和是否显示入口'
        翻译=自身.属性['t'] if 't' in 自身.属性 and callable(自身.属性['t']) else 缺省翻译
        打开态=自身._读('useSession',自身.选打开态)
        目录=自身._读('useCatalog',lambda 值:值)
        if isinstance(目录,dict):
            记录=目录['records'] if 'records' in 目录 and isinstance(目录['records'],list) else []
            状态=目录['status'] if 'status' in 目录 else 'ready'
            正在删=目录['deleting'] if 'deleting' in 目录 and isinstance(目录['deleting'],list) else []
        else:
            投影=None
            用投影=自身.属性['useProjection'] if 'useProjection' in 自身.属性 else None
            if callable(用投影):
                try:
                    投影=用投影('schedule')
                except Exception:
                    投影=None
            记录=list(投影) if isinstance(投影,(list,tuple)) else []
            状态='ready'
            正在删=[]
        可见=打开态=='open' and (len(记录)>0 or 状态=='error')
        return 翻译,记录,状态,正在删,可见

    def _确保时钟(自身):
        '菜单打开时每秒刷新相对时间'
        需要=自身.打开
        钟=getattr(自身,'_钟',None)
        if 需要 and 钟 is None:
            def 滴答():
                '采样并重画'
                自身.现在=当前毫秒()
                if 自身.打开:
                    自身.重画()
            自身._钟=界面.timer(1.0,滴答)
        if 需要 is False and 钟 is not None:
            钟.active=False
            自身._钟=None

    def 渲染(自身):
        '时钟按钮；有多条或正在读时展开菜单'
        自身.确保订阅()
        if getattr(自身,'_壳',None) is None:
            自身._壳=界面.column().classes('schedule-catalog')
        自身.重画()

    def 重画(自身):
        '没有可见提醒时留空'
        壳=getattr(自身,'_壳',None)
        if 壳 is None:
            return
        壳.clear()
        翻译,记录,状态,正在删,可见=自身._材料()
        if 可见 is False:
            自身.打开=False
            自身._确保时钟()
            return
        行列表=按逾期排序(记录,自身.现在)
        已知=len(记录)
        if 已知==0:
            计数=翻译('trigger.label')
        else:
            计数=翻译('trigger.one' if 已知==1 else 'trigger.other',{'count':已知})
        唯一=记录[0] if 状态=='ready' and len(记录)==1 else None
        可展开=唯一 is None or 自身.打开
        def 点击():
            '一条直接打开详情，多条展开菜单'
            自身.现在=当前毫秒()
            if 可展开:
                自身.切换目录()
                return
            自身._打开(唯一['id'])
        def 按键(事件):
            'Escape 收起'
            键=getattr(事件,'key',None)
            参数=getattr(事件,'args',None)
            if 键 is None and isinstance(参数,dict):
                键=参数.get('key')
            if 键=='Escape' and 自身.打开:
                自身.关闭目录()
        with 壳:
            触发=界面.button(on_click=点击).props('flat round icon=schedule aria-label="'+计数+'" aria-expanded='+('true' if 自身.打开 else 'false'))
            触发.on('keydown',按键)
            if 自身.打开:
                with 界面.column().classes('schedule-menu'):
                    if 状态=='loading':
                        界面.label(翻译('list.loading'))
                    if 状态=='error':
                        界面.label(翻译('list.error'))
                        重试=自身.属性['onRetry'] if 'onRetry' in 自身.属性 and callable(自身.属性['onRetry']) else None
                        if 重试 is not None:
                            界面.button(翻译('list.retry'), on_click=lambda:重试())
                    for 记录 in 行列表:
                        名=任务名(记录)
                        片段=下次运行片段(记录['scheduledAt'] if 'scheduledAt' in 记录 else '',翻译('time.locale'),自身.现在,翻译)
                        def 打开(当前=记录['id'] if 'id' in 记录 else None):
                            '打开这条详情'
                            自身._打开(当前)
                        界面.button(名, on_click=打开).props('flat no-caps align=left aria-label="'+翻译('list.open',{'title':名})+'"')
                        界面.label(展示频率(记录,翻译))
                        界面.label(翻译('list.nextRun')+' '+片段['absolute']+' '+片段['relative'])
                        标识=记录['id'] if 'id' in 记录 else None
                        在删=标识 in 正在删
                        def 删除(当前=标识):
                            '删这条提醒'
                            回调=自身.属性['onDelete'] if 'onDelete' in 自身.属性 else None
                            if callable(回调):
                                回调(当前)
                        钮=界面.button(on_click=删除).props('flat round icon=delete aria-label="'+翻译('delete.label',{'title':名})+'"')
                        if 在删:
                            钮.disable()
        自身._确保时钟()

    def _打开(自身,标识):
        '收起菜单并打开详情'
        自身.打开=False
        回调=自身.属性['openTaskDetail'] if 'openTaskDetail' in 自身.属性 else None
        if callable(回调):
            回调(标识)
        自身.重画()

    def 选打开态(自身,快照):
        '从会话快照取 openState。快照为跨包 dict'
        return 快照['openState'] if 'openState' in 快照 else None#打开态

    def __call__(自身,属性=None):
        '组件调用形；有属性则更新后渲染'
        if 属性 is not None:
            自身.更新(属性)#刷
        return 自身.渲染()
