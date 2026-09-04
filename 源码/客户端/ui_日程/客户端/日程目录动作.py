"""只读的当前 Session 活动提醒目录。

对齐上游 `ui-schedule/src/client/ScheduleCatalogAction.tsx`。公开面仅中文名。
无真 React：类状态 + 结构树字典。
"""
import math#取整
import time#浏览器时钟
from datetime import datetime#本地时间格式化
from .文案 import NS#命名空间

__all__=[#仅中文公开名
    '单位文案','格式化日程频率','格式化日程本地时间','格式化日程相对',
    '排序日程记录','日程目录动作','空记录','秒毫秒','单位秒表',
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

def 取字段(对象,键,缺省=None):#读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

def 单位文案(单位,值,翻译):#一个整数量级的本地化单位词
    """单复数键对。"""
    键对={#单复数键对
        'day':('unit.day.one','unit.day.other'),#天
        'hour':('unit.hour.one','unit.hour.other'),#小时
        'minute':('unit.minute.one','unit.minute.other'),#分钟
        'second':('unit.second.one','unit.second.other'),#秒
    }#冻结
    对=键对[单位]#取对
    return 翻译(对[0] if 值==1 else 对[1],{'count':值})#单复数键

def 格式化日程频率(记录,翻译):#频率文案
    """选取最大可整除完整单位，不舍入持久间隔。"""
    种类=取字段(记录,'kind')#种类
    if 种类!='every':#单次
        return 翻译('frequency.once')#单次
    选中=秒单位#默认秒
    间隔=取字段(记录,'everySeconds',0)#间隔秒
    for 候选 in 单位秒表:#自大到小
        if 间隔%候选['seconds']!=0:#不可整除
            continue#跳过
        选中=候选#命中
        break#取最大可整除
    值=间隔//选中['seconds']#整数量
    return 翻译('frequency.every',{'value':值,'unit':单位文案(选中['unit'],值,翻译)})#重复文案

def 格式化日程本地时间(计划于,区域=None):#本地时间
    """按浏览器当前 locale 与时区格式化持久 UTC 目标。"""
    try:#解析
        时刻=datetime.fromisoformat(计划于.replace('Z','+00:00'))#解析 ISO
    except Exception:#失败
        时刻=datetime.utcfromtimestamp(0)#回退纪元
    return 时刻.strftime('%Y-%m-%d %H:%M')#中等日期+短时间近似

def 格式化日程相对(计划于,现在,翻译):#相对文案
    """用最大自然时钟单位表达人类相对目标。"""
    try:#解析
        目标=int(datetime.fromisoformat(计划于.replace('Z','+00:00')).timestamp()*1000)#目标毫秒
    except Exception:#失败
        目标=现在#回退
    差=目标-现在#差值毫秒
    if 差==0:#恰到期
        return 翻译('relative.now')#恰到期
    绝对秒=abs(差)/秒毫秒#绝对秒
    选中=秒单位#默认秒
    for 候选 in 单位秒表:#最大未超过的单位
        if 绝对秒>=候选['seconds']:#够大
            选中=候选#选中
            break#停
    if 差>0:#未来
        值=max(1,math.ceil(绝对秒/选中['seconds']))#向上取整
    else:#逾期
        值=max(1,math.floor(绝对秒/选中['seconds']))#向下取整
    单位=单位文案(选中['unit'],值,翻译)#单位词
    return 翻译('relative.future' if 差>0 else 'relative.overdue',{'value':值,'unit':单位})#相对句

def 排序日程记录(记录们,现在):#逾期在前，再按目标时间升序
    """完全并列保持稳定。"""
    def 解析时刻(记录):#目标毫秒
        """解析 scheduledAt。"""
        原文=取字段(记录,'scheduledAt','')#原文
        try:#解析
            return int(datetime.fromisoformat(原文.replace('Z','+00:00')).timestamp()*1000)#毫秒
        except Exception:#失败
            return 0#回退
    带索引=[{'record':记录,'index':索引} for 索引,记录 in enumerate(记录们)]#带原索引
    def 比较(左,右):#比较器
        """逾期优先，再时间，再稳定索引。"""
        左时=解析时刻(左['record'])#左目标
        右时=解析时刻(右['record'])#右目标
        左逾期=左时<=现在#左是否逾期
        右逾期=右时<=现在#右是否逾期
        if 左逾期!=右逾期:#逾期优先
            return int(右逾期)-int(左逾期)#逾期在前
        return (左时-右时) or (左['index']-右['index'])#时间再稳定索引
    带索引.sort(key=lambda 项:(解析时刻(项['record'])>现在,解析时刻(项['record']),项['index']))#逾期优先近似
    return [项['record'] for 项 in 带索引]#剥掉索引

class 日程目录动作:#页眉动作
    """只读的当前 Session 活动提醒目录。"""

    def __init__(自身,属性=None):#构造
        """记下 props 与本地状态。"""
        自身.属性=属性 or {}#合成
        自身.打开=False#弹层开合
        自身.现在=int(time.time()*1000)#浏览器时钟

    def 更新(自身,属性):#刷新
        """刷新 props。"""
        自身.属性=属性 or {}#新

    def 切换目录(自身):#切换开合
        """刷新时钟并切换开合。"""
        自身.现在=int(time.time()*1000)#刷新时钟
        自身.打开=not 自身.打开#切换开合

    def 渲染(自身):#结构树
        """不可见则空；可见时触发+弹层。"""
        属性=自身.属性#props
        用会话=取字段(属性,'useSession')#会话钩
        用投影=取字段(属性,'useProjection')#投影钩
        翻译=取字段(属性,'t',lambda 键,_=None:键)#文案
        打开态=用会话(lambda 快照:取字段(快照,'openState')) if callable(用会话) else None#会话打开态
        投影=用投影('schedule') if callable(用投影) else None#完整 schedule 投影
        记录们=投影 if 投影 is not None else 空记录#无投影用空表
        可见=打开态=='open' and len(记录们)>0#仅打开且有记录时显示
        if not 可见:#不可见
            自身.打开=False#强制关
            return None#不渲染
        行们=排序日程记录(记录们,自身.现在)#排序行
        计数键='trigger.one' if len(记录们)==1 else 'trigger.other'#单复数键
        计数标签=翻译(计数键,{'count':len(记录们)})#触发标签
        菜单行=[]#弹层行
        for 记录 in 行们:#逐行
            原文=取字段(记录,'scheduledAt','')#目标
            try:#解析
                目标=int(datetime.fromisoformat(原文.replace('Z','+00:00')).timestamp()*1000)#毫秒
            except Exception:#失败
                目标=自身.现在#回退
            逾期=目标<=自身.现在#是否逾期
            菜单行.append({#提醒行
                'id':取字段(记录,'id'),#稳定键
                'overdue':逾期,#逾期
                'status':翻译('status.overdue' if 逾期 else 'status.scheduled'),#状态文案
                'prompt':取字段(记录,'prompt'),#提示正文
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
            'onEscape':lambda:(setattr(自身,'打开',False)),#Escape 关
            'cssModule':'日程目录动作.module.css',#样式
            'localeNS':NS,#命名空间
        }#视图结束

    def __call__(自身,属性=None):#调用形
        """对齐 React。"""
        if 属性 is not None:#有
            自身.更新(属性)#刷
        return 自身.渲染()#渲

ScheduleCatalogAction=日程目录动作#上游名
