'会话和宿主目录共用的频率、下次运行和排序'
from ...模块.客户端.通告 import 取握手窗口
import re
from ....工具.值 import 断言永不
from .文案 import 套用
from .任务定时 import 定时预览,解析定时表达式

__all__=['任务名','时区标签','时区名','时区选项','记录时区','格式化日程频率','格式化下次运行','下次运行两段','格式化相对','排序日程记录']

秒毫秒=1000
秒单位={'unit':'second','seconds':1}
单位秒表=[
    {'unit':'day','seconds':86400},
    {'unit':'hour','seconds':3600},
    {'unit':'minute','seconds':60},
    秒单位,
]
星期键=['frequency.weekday.1','frequency.weekday.2','frequency.weekday.3','frequency.weekday.4','frequency.weekday.5','frequency.weekday.6','frequency.weekday.7']
回退时区=['UTC']
带年语言=['en']
不带年语言=['zh']

def 单位文案(单位,值,表):
    '整数量级的中文单位'
    键='unit.'+单位+'.'+('one' if 值==1 else 'other')
    return 套用(表[键],{'count':值})

def 任务名(记录):
    '用存下来的标题'
    return 记录['title']

def 时钟文案(时间):
    '去掉小数秒，整分再去掉秒'
    return re.sub(r':00$','',re.sub(r'\.\d+$','',时间))

def 时区偏移分钟(时区,时刻):
    '这一瞬间的 UTC 偏移分钟'
    窗口=取握手窗口()
    try:
        部分=窗口.Intl.DateTimeFormat('en-US',{'timeZone':时区,'timeZoneName':'longOffset'}).formatToParts(时刻)
        值=None
        for 项 in 部分:
            if 项['type']=='timeZoneName':
                值=项['value']
        if 值=='GMT':
            return 0
        匹配=re.match(r'^GMT([+-])(\d{2}):(\d{2})$','' if 值 is None else 值)
        if 匹配 is None:
            return None
        分钟=int(匹配.group(2))*60+int(匹配.group(3))
        if 匹配.group(1)=='-':
            return -分钟
        return 分钟
    except Exception:
        return None

def 时区标签(时区,表,时刻=None):
    'UTC 偏移加本地化时区名'
    窗口=取握手窗口()
    if 时刻 is None:
        时刻=int(窗口.Date.now())
    分钟=时区偏移分钟(时区,时刻)
    偏移=None
    if 分钟 is not None:
        绝对=abs(分钟)
        时=str(绝对//60).zfill(2)
        余=str(绝对%60).zfill(2)
        偏移=表['time.utcPrefix']+('-' if 分钟<0 else '+')+时+':'+余
    try:
        部分=窗口.Intl.DateTimeFormat(表['time.locale'],{'timeZone':时区,'timeZoneName':'longGeneric'}).formatToParts(时刻)
        名=None
        for 项 in 部分:
            if 项['type']=='timeZoneName':
                名=项['value']
        if 偏移 is None:
            return 时区 if 名 is None else 名
        if 名 is None or re.match(r'^GMT(?:[+-]|$)',名):
            return 偏移
        return 偏移+' · '+名
    except Exception:
        if 偏移 is None:
            return 时区
        return 偏移+' · '+时区

def 时区名(时区,系统,表,时刻=None):
    '是本机时区时在后面加上（系统）'
    名=时区标签(时区,表,时刻)
    if 时区==系统:
        return 名+表['rule.zone.system']
    return 名

def 时区选项(已存,系统,时刻=None):
    '菜单顺序：本机时区，再按当前偏移和标识排'
    窗口=取握手窗口()
    if 时刻 is None:
        时刻=int(窗口.Date.now())
    try:
        清单=list(窗口.Intl.supportedValuesOf('timeZone'))
    except Exception:
        清单=None
    if 清单 is None:
        时区列=list(回退时区)
    else:
        时区列=list(回退时区)+清单
    去重=[]
    for 项 in 时区列+[已存]:
        if 项 not in 去重:
            去重.append(项)
    候选=[项 for 项 in 去重 if 项!=系统]
    带偏移=[]
    for 项 in 候选:
        偏移=时区偏移分钟(项,时刻)
        带偏移.append({'zone':项,'offset':float('inf') if 偏移 is None else 偏移})
    def 排序键(项):
        '先按偏移，再按标识'
        return (项['offset'],项['zone'])
    带偏移.sort(key=排序键)
    return [系统]+[项['zone'] for 项 in 带偏移]

def 记录时区(记录):
    '每天、每周、cron 才有规则时区'
    种类=记录['kind']
    if 种类 in ('after','at','every'):
        return None
    if 种类 in ('daily','weekly','cron'):
        return 记录['timeZone']
    return None

def 格式化日程频率(记录,表,时区=None):
    '按存下的规则写频率。时区参数用来省略本机时区'
    种类=记录['kind']
    if 种类=='after' or 种类=='at':
        return 表['frequency.once']
    if 种类=='cron':
        解析=解析定时表达式(记录['expression'])
        if 解析 is not None:
            规则=定时预览(解析,表,表['time.locale'])
            if 时区 is None:
                return 套用(表['frequency.cronRule'],{'rule':规则,'timeZone':时区标签(记录['timeZone'],表)})
            if 时区['system']==记录['timeZone']:
                return 规则
            return 套用(表['frequency.cronRule'],{'rule':规则,'timeZone':时区['label'](记录['timeZone'])})
        if 时区 is None:
            return 套用(表['frequency.cron'],{'expression':记录['expression'],'timeZone':时区标签(记录['timeZone'],表)})
        if 时区['system']==记录['timeZone']:
            return 套用(表['frequency.cronLocal'],{'expression':记录['expression']})
        return 套用(表['frequency.cron'],{'expression':记录['expression'],'timeZone':时区['label'](记录['timeZone'])})
    if 种类=='daily':
        时间=时钟文案(记录['time'])
        if 时区 is None:
            return 套用(表['frequency.daily'],{'time':时间,'timeZone':时区标签(记录['timeZone'],表)})
        if 时区['system']==记录['timeZone']:
            return 套用(表['frequency.dailyLocal'],{'time':时间})
        return 套用(表['frequency.daily'],{'time':时间,'timeZone':时区['label'](记录['timeZone'])})
    if 种类=='weekly':
        星期名=[]
        for 日 in 记录['weekdays']:
            下标=日-1
            键=星期键[下标] if 0<=下标<len(星期键) else 'frequency.weekday.1'
            星期名.append(表[键])
        参数={'weekdays':表['frequency.weekday.join'].join(星期名),'time':时钟文案(记录['time'])}
        if 时区 is None:
            return 套用(表['frequency.weekly'],{**参数,'timeZone':时区标签(记录['timeZone'],表)})
        if 时区['system']==记录['timeZone']:
            return 套用(表['frequency.weeklyLocal'],参数)
        return 套用(表['frequency.weekly'],{**参数,'timeZone':时区['label'](记录['timeZone'])})
    if 种类=='every':
        选中=秒单位
        for 候选 in 单位秒表:
            if 记录['everySeconds']%候选['seconds']!=0:
                continue
            选中=候选
            break
        值=记录['everySeconds']/选中['seconds']
        if 值==int(值):
            值=int(值)
        return 套用(表['frequency.every'],{'value':值,'unit':单位文案(选中['unit'],值,表)})
    return 断言永不(记录)

def 格式化下次运行(计划于,区域,时区=None):
    '月日加时刻。跨年才带年。解析不了就返回原文'
    窗口=取握手窗口()
    时刻=窗口.Date.parse(计划于)
    if 时刻!=时刻:
        return 计划于
    区={} if 时区 is None else {'timeZone':时区}
    年格式=窗口.Intl.DateTimeFormat('en-US',{'year':'numeric',**区})
    选项={'month':'short','day':'numeric','hour':'numeric','minute':'2-digit',**区}
    if 年格式.format(时刻)!=年格式.format(窗口.Date.now()):
        选项['year']='numeric'
    return 窗口.Intl.DateTimeFormat(区域,选项).format(时刻)

def 要写年(区域):
    '中文绝对日期不写年，其余语言写年'
    语言=区域.lower().split('-')[0]
    if 语言 in 带年语言:
        return True
    if 语言 in 不带年语言:
        return False
    return True

def 格式化绝对(计划于,区域):
    '设备时区里的绝对时刻'
    窗口=取握手窗口()
    时刻=窗口.Date.parse(计划于)
    if 时刻!=时刻:
        return 计划于
    选项={'month':'short','day':'numeric','hour':'2-digit','minute':'2-digit','hourCycle':'h23'}
    if 要写年(区域):
        选项['year']='numeric'
    return 窗口.Intl.DateTimeFormat(区域,选项).format(时刻)

def 格式化相对(计划于,现在,表):
    '用最大的自然时钟单位说相对时间'
    窗口=取握手窗口()
    差=窗口.Date.parse(计划于)-现在
    if 差==0:
        return 表['relative.now']
    绝对秒=abs(差)/秒毫秒
    选中=秒单位
    for 候选 in 单位秒表:
        if 绝对秒>=候选['seconds']:
            选中=候选
            break
    if 差>0:
        值=绝对秒/选中['seconds']
        值=int(值) if 值==int(值) else int(值)+1
    else:
        值=int(绝对秒/选中['seconds'])
    if 值<1:
        值=1
    单位=单位文案(选中['unit'],值,表)
    键='relative.future' if 差>0 else 'relative.overdue'
    return 套用(表[键],{'value':值,'unit':单位})

def 下次运行两段(计划于,区域,现在,表):
    '设备时区戳和括号里的距离'
    return {
        'absolute':格式化绝对(计划于,区域),
        'relative':'('+格式化相对(计划于,现在,表)+')',
    }

def 排序日程记录(记录列,现在):
    '逾期在前，其余按目标时间升序。并列保持原顺序'
    窗口=取握手窗口()
    带序=[]
    序=0
    for 记录 in 记录列:
        带序.append({'record':记录,'index':序,'time':窗口.Date.parse(记录['scheduledAt'])})
        序=序+1
    def 键(项):
        '逾期优先，再按时间，再按原下标'
        逾期=1 if 项['time']<=现在 else 0
        return (-逾期,项['time'],项['index'])
    带序.sort(key=键)
    return [项['record'] for 项 in 带序]
