'提醒频率、下次运行和排序'
import math
from datetime import datetime as 日期时间
from datetime import timezone as 时区

__all__=['任务名','格式化日程频率','下次运行片段','排序日程记录','记录时区','格式化绝对时刻']

秒毫秒=1_000
秒单位={'unit':'second','seconds':1}
单位秒表=(
    {'unit':'day','seconds':86_400},
    {'unit':'hour','seconds':3_600},
    {'unit':'minute','seconds':60},
    秒单位,
)
星期键=('frequency.weekday.1','frequency.weekday.2','frequency.weekday.3','frequency.weekday.4','frequency.weekday.5','frequency.weekday.6','frequency.weekday.7')

def 缺省翻译(键,_参数=None):
    '无翻译函数时回传键'
    return 键

def 任务名(记录):
    '优先用已存标题，否则取指令第一行'
    if not isinstance(记录,dict):
        return ''
    标题=记录['title'] if 'title' in 记录 else ''
    if isinstance(标题,str) and 标题.strip()!='':
        return 标题.strip()
    提示=记录['prompt'] if 'prompt' in 记录 else ''
    if not isinstance(提示,str):
        return ''
    return 提示.split('\n',1)[0].strip()

def 解析时刻(原文):
    'UTC 时刻转纪元毫秒；解析不了则 None'
    if not isinstance(原文,str) or 原文=='':
        return None
    文=原文[:-1]+'+00:00' if 原文.endswith('Z') else 原文
    try:
        时刻=日期时间.fromisoformat(文)
    except ValueError:
        return None
    if 时刻.tzinfo is None:
        时刻=时刻.replace(tzinfo=时区.utc)
    return int(时刻.timestamp()*1000)

def 单位文案(单位,值,翻译):
    '整数量级的单位词'
    键='unit.'+单位+('.'+'one' if 值==1 else '.other')
    return 翻译(键,{'count':值})

def 时钟文(时间):
    '去掉小数秒和末尾的 :00'
    if not isinstance(时间,str):
        return ''
    文=时间.split('.',1)[0]
    if 文.endswith(':00'):
        return 文[:-3]
    return 文

def 时区名(记录,时区上下文,翻译):
    '有宿主时区比较时用其 label，否则用存下的标识'
    区=记录['timeZone'] if 'timeZone' in 记录 and isinstance(记录['timeZone'],str) else ''
    if isinstance(时区上下文,dict) and 'label' in 时区上下文 and callable(时区上下文['label']):
        return 时区上下文['label'](区)
    return 区

def 省略宿主时区(记录,时区上下文):
    '规则时区与宿主相同时不写出时区'
    if not isinstance(时区上下文,dict) or 'system' not in 时区上下文:
        return False
    区=记录['timeZone'] if 'timeZone' in 记录 else None
    return 区==时区上下文['system']

def 格式化星期(星期表,翻译):
    '按序号拼本地化星期名'
    if not isinstance(星期表,(list,tuple)):
        return ''
    名=[]
    for 日 in 星期表:
        if isinstance(日,bool) or not isinstance(日,int) or 日<1 or 日>7:
            continue
        名.append(翻译(星期键[日-1]))
    return 翻译('frequency.weekday.join').join(名)

def 格式化日程频率(记录,翻译=None,时区上下文=None):
    '单次、间隔、每天、每周、cron 原文'
    译=翻译 if callable(翻译) else 缺省翻译
    if not isinstance(记录,dict) or 'kind' not in 记录:
        return ''
    种=记录['kind']
    if 种=='after' or 种=='at':
        return 译('frequency.once')
    if 种=='every':
        间隔=记录['everySeconds'] if 'everySeconds' in 记录 and isinstance(记录['everySeconds'],(int,float)) and not isinstance(记录['everySeconds'],bool) else 1
        选中=秒单位
        for 候选 in 单位秒表:
            if 间隔%候选['seconds']!=0:
                continue
            选中=候选
            break
        值=int(间隔//选中['seconds'])
        return 译('frequency.every',{'value':值,'unit':单位文案(选中['unit'],值,译)})
    if 种=='daily':
        时间=时钟文(记录['time'] if 'time' in 记录 else '')
        if 省略宿主时区(记录,时区上下文):
            return 译('frequency.dailyLocal',{'time':时间})
        return 译('frequency.daily',{'time':时间,'timeZone':时区名(记录,时区上下文,译)})
    if 种=='weekly':
        参数={'weekdays':格式化星期(记录['weekdays'] if 'weekdays' in 记录 else (),译),'time':时钟文(记录['time'] if 'time' in 记录 else '')}
        if 省略宿主时区(记录,时区上下文):
            return 译('frequency.weeklyLocal',参数)
        参数['timeZone']=时区名(记录,时区上下文,译)
        return 译('frequency.weekly',参数)
    if 种=='cron':
        表达式=记录['expression'] if 'expression' in 记录 and isinstance(记录['expression'],str) else ''
        if 省略宿主时区(记录,时区上下文):
            return 译('frequency.cronLocal',{'expression':表达式})
        return 译('frequency.cron',{'expression':表达式,'timeZone':时区名(记录,时区上下文,译)})
    return str(种)

def 格式化绝对时刻(计划于,区域):
    '设备时区里的月日时刻；中文不带年'
    毫秒=解析时刻(计划于)
    if 毫秒 is None:
        return 计划于 if isinstance(计划于,str) else ''
    时刻=日期时间.fromtimestamp(毫秒/1000)
    语言=区域.lower() if isinstance(区域,str) else 'zh'
    if 语言.startswith('zh'):
        return 时刻.strftime('%m月%d日 %H:%M')
    if 时刻.year!=日期时间.now().year:
        return 时刻.strftime('%b %d, %Y, %H:%M')
    return 时刻.strftime('%b %d, %H:%M')

def 格式化相对(计划于,现在,翻译):
    '最大自然单位的相对句'
    译=翻译 if callable(翻译) else 缺省翻译
    毫秒=解析时刻(计划于)
    if 毫秒 is None:
        return ''
    差=毫秒-现在
    if 差==0:
        return 译('relative.now')
    绝对秒=abs(差)/秒毫秒
    选中=秒单位
    for 候选 in 单位秒表:
        if 绝对秒>=候选['seconds']:
            选中=候选
            break
    if 差>0:
        值=max(1,math.ceil(绝对秒/选中['seconds']))
    else:
        值=max(1,绝对秒//选中['seconds'])
    return 译('relative.future' if 差>0 else 'relative.overdue',{'value':int(值),'unit':单位文案(选中['unit'],int(值),译)})

def 下次运行片段(计划于,区域,现在,翻译):
    '绝对时刻和括号里的距离'
    译=翻译 if callable(翻译) else 缺省翻译
    语言=区域 if isinstance(区域,str) and 区域!='' else 译('time.locale')
    return {'absolute':格式化绝对时刻(计划于,语言),'relative':'('+格式化相对(计划于,现在,译)+')'}

def 排序日程记录(记录列表,现在):
    '逾期在前，再按目标升序'
    表=记录列表 if isinstance(记录列表,(list,tuple)) else ()
    def 键(项):
        '逾期优先'
        记录,索引=项
        毫秒=解析时刻(记录['scheduledAt'] if isinstance(记录,dict) and 'scheduledAt' in 记录 else None)
        时=毫秒 if 毫秒 is not None else 0
        return (时>现在,时,索引)
    带索引=[(记录,索引) for 索引,记录 in enumerate(表)]
    带索引.sort(key=键)
    return [记录 for 记录,_索引 in 带索引]

def 记录时区(记录):
    '每天、每周、cron 才有规则时区'
    if not isinstance(记录,dict) or 'kind' not in 记录:
        return None
    if 记录['kind'] in ('daily','weekly','cron') and 'timeZone' in 记录:
        return 记录['timeZone']
    return None
