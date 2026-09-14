import math#取整
import time#纪元毫秒
from datetime import datetime#时刻
from zoneinfo import ZoneInfo#时区
from .文案 import 命名空间#命名空间

__all__=[#仅中文公开名
    '单位文案','格式化日程频率','格式化日程本地时间','格式化日程相对',
    '排序日程记录','日程目录动作','空记录','秒毫秒','单位秒表','解析日程时刻',
]#公开面结束

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
协调世界时=ZoneInfo('UTC')#UTC

def 解析日程时刻(原文):
    """把线协议 UTC 时刻翻成纪元毫秒。"""
    时刻=datetime.strptime(原文,日程时刻格式).replace(tzinfo=协调世界时)#写死格式
    return int(时刻.timestamp()*1000)#纪元毫秒

def 缺省翻译(键,_插值=None):
    """无翻译函数时回传键。"""
    return 键#键即文案

def 单位文案(单位,值,翻译):
    """一个整数量级的本地化单位词。"""
    键对={#单复数键对
        'day':('unit.day.one','unit.day.other'),#天
        'hour':('unit.hour.one','unit.hour.other'),#小时
        'minute':('unit.minute.one','unit.minute.other'),#分钟
        'second':('unit.second.one','unit.second.other'),#秒
    }#冻结
    对=键对[单位]#取对
    return 翻译(对[0] if 值==1 else 对[1],{'count':值})#单复数键

def 格式化日程频率(记录,翻译):
    """选取最大可整除完整单位，不舍入持久间隔。记录为线协议 dict。"""
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
    """按当地时区格式化持久 UTC 目标。"""
    时刻=datetime.strptime(计划于,日程时刻格式).replace(tzinfo=协调世界时)#写死格式
    本地=时刻.astimezone()#当地时区
    return 本地.strftime('%Y-%m-%d %H:%M')#中等日期+短时间近似

def 格式化日程相对(计划于,现在,翻译):
    """用最大自然时钟单位表达人类相对目标。"""
    目标=解析日程时刻(计划于)#目标毫秒
    差=目标-现在#差值毫秒
    if 差==0:
        return 翻译('relative.now')#恰到期
    绝对秒=abs(差)/秒毫秒#绝对秒
    选中=秒单位#默认秒
    for 候选 in 单位秒表:
        if 绝对秒>=候选['seconds']:
            选中=候选#选中
            break#停
    if 差>0:
        值=max(1,math.ceil(绝对秒/选中['seconds']))#向上取整
    else:
        值=max(1,math.floor(绝对秒/选中['seconds']))#向下取整
    单位=单位文案(选中['unit'],值,翻译)#单位词
    return 翻译('relative.future' if 差>0 else 'relative.overdue',{'value':值,'unit':单位})#相对句

def 排序日程记录(记录列表,现在):
    """逾期在前，再按目标时间升序。完全并列保持稳定。"""
    def 解析或零(记录):
        """解析 scheduledAt；非法则 0。"""
        try:
            return 解析日程时刻(记录['scheduledAt'])#毫秒
        except ValueError:
            return 0#非法时刻
    带索引=[{'record':记录,'index':索引} for 索引,记录 in enumerate(记录列表)]#带原索引
    def 排序键(项):
        """逾期优先，再时间，再稳定索引。"""
        时=解析或零(项['record'])#目标
        return (时>现在,时,项['index'])#逾期在前
    带索引.sort(key=排序键)#逾期优先
    return [项['record'] for 项 in 带索引]#剥掉索引

class 日程目录动作:#页眉动作
    """只读的当前 Session 活动提醒目录。"""
    def __init__(自身,属性=None):
        """记下 props 与本地状态。"""
        自身.属性={} if 属性 is None else 属性#合成
        自身.打开=False#弹层开合
        自身.现在=int(time.time()*1000)#纪元毫秒

    def 更新(自身,属性):
        """刷新 props。"""
        自身.属性={} if 属性 is None else 属性#新

    def 切换目录(自身):
        """刷新时钟并切换开合。"""
        自身.现在=int(time.time()*1000)#刷新时钟
        自身.打开=not 自身.打开#切换开合

    def 关闭目录(自身):
        """Escape 关。"""
        自身.打开=False#关

    def 渲染(自身):
        """不可见则空；可见时触发+弹层。"""
        属性=自身.属性#props
        用会话=属性['useSession'] if 'useSession' in 属性 else None#会话钩
        用投影=属性['useProjection'] if 'useProjection' in 属性 else None#投影钩
        翻译=属性['t'] if 't' in 属性 else 缺省翻译#文案
        打开态=用会话(自身.选打开态) if 用会话 is not None else None#会话打开态
        投影=用投影('schedule') if 用投影 is not None else None#完整 schedule 投影
        记录列表=投影 if 投影 is not None else 空记录#无投影用空表
        可见=打开态=='open' and len(记录列表)>0#仅打开且有记录时显示
        if not 可见:
            自身.打开=False#强制关
            return None#不渲染
        行列表=排序日程记录(记录列表,自身.现在)#排序行
        计数键='trigger.one' if len(记录列表)==1 else 'trigger.other'#单复数键
        计数标签=翻译(计数键,{'count':len(记录列表)})#触发标签
        菜单行=[]#弹层行
        for 记录 in 行列表:
            原文=记录['scheduledAt']#目标
            try:
                目标=解析日程时刻(原文)#毫秒
            except ValueError:
                目标=自身.现在#非法则当现在
            逾期=目标<=自身.现在#是否逾期
            菜单行.append({#提醒行
                'id':记录['id'],#稳定键
                'overdue':逾期,#逾期
                'status':翻译('status.overdue' if 逾期 else 'status.scheduled'),#状态文案
                'prompt':记录['prompt'],#提示正文
                'frequency':格式化日程频率(记录,翻译),#频率
                'localTime':格式化日程本地时间(原文),#本地时间
                'relative':格式化日程相对(原文,自身.现在,翻译),#相对文案
            })#行结束
        return {#根座位
            'type':'schedule-catalog-action',#类型
            'open':自身.打开,#开合
            'countLabel':计数标签,#计数
            'listAria':翻译('list.aria'),#无障碍
            'rows':菜单行 if 自身.打开 else None,#弹层行
            'onToggle':自身.切换目录,#切换
            'onEscape':自身.关闭目录,#Escape 关
            'cssModule':'日程目录动作.module.css',#样式
            'localeNS':命名空间,#命名空间
        }#视图结束

    def 选打开态(自身,快照):
        """从会话快照取 openState。快照为跨包 dict。"""
        return 快照['openState'] if 'openState' in 快照 else None#打开态

    def __call__(自身,属性=None):
        """对齐 React。"""
        if 属性 is not None:
            自身.更新(属性)#刷
        return 自身.渲染()#渲
