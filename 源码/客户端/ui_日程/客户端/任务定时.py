'五字段 cron 的解析、中文句子和构建器形状'
from ...模块.客户端.通告 import 取握手窗口
import re
from ....工具.值 import 断言永不
from ..异常 import 定时不变式错误
from .文案 import 套用

__all__=['解析定时表达式','定时预览','识别定时形状','定时形状表达式']

字段规格=[
    {'min':0,'max':59,'count':60},
    {'min':0,'max':23,'count':24},
    {'min':1,'max':31,'count':31},
    {'min':1,'max':12,'count':12},
    {'min':0,'max':7,'count':7,'foldMax':7},
]
步进表达式=re.compile(r'^\*/(?P<step>\d+)$')
元素表达式=re.compile(r'^(?P<start>\d+)(?:-(?P<end>\d+))?(?:/(?P<step>\d+))?$')
星期键=['frequency.weekday.1','frequency.weekday.2','frequency.weekday.3','frequency.weekday.4','frequency.weekday.5','frequency.weekday.6','frequency.weekday.7']
时刻列举上限=6

def 升序范围(起,止,步):
    '含端点的等差数列'
    值列=[]
    值=起
    while 值<=止:
        值列.append(值)
        值=值+步
    return 值列

def 字段值(文本,规格):
    '读一个落在字段范围内的整数'
    if not 文本.isdigit():
        return None
    值=int(文本)
    if 值<规格['min'] or 值>规格['max']:
        return None
    return 值

def 字段步(文本):
    '读一个正整数步长'
    if not 文本.isdigit():
        return None
    值=int(文本)
    if 值<1:
        return None
    return 值

def 元素值(元素,规格):
    '把一个逗号段展开成命中的值'
    if len(元素)==0:
        return None
    if 元素=='*':
        return 升序范围(规格['min'],规格['max'],1)
    if 元素.startswith('*'):
        匹配=步进表达式.match(元素)
        if 匹配 is None:
            return None
        步=字段步(匹配.group('step'))
        if 步 is None:
            return None
        return 升序范围(规格['min'],规格['max'],步)
    匹配=元素表达式.match(元素)
    if 匹配 is None:
        return None
    起=字段值(匹配.group('start'),规格)
    if 起 is None:
        return None
    止文=匹配.group('end')
    if 止文 is None:
        if 匹配.group('step') is not None:
            return None
        return [起]
    止=字段值(止文,规格)
    if 止 is None or 起>止:
        return None
    步文=匹配.group('step')
    步=1 if 步文 is None else 字段步(步文)
    if 步 is None:
        return None
    return 升序范围(起,止,步)

def 定时下标(值列,下标):
    '调用方已经保证下标在长度内'
    if 下标<0 or 下标>=len(值列):
        raise 定时不变式错误('cron description read an index outside its array')
    return 值列[下标]

def 解析定时表达式(表达式):
    '解析宿主接受的五字段表达式。不合格返回 None'
    if len(表达式)==0 or 表达式.strip()!=表达式:
        return None
    字段=re.split(r'\s+',表达式)
    if len(字段)!=5:
        return None
    解析=[]
    序=0
    while 序<5:
        规格=定时下标(字段规格,序)
        原文=字段[序]
        命中=set()
        坏=False
        for 元素 in 原文.split(','):
            值列=元素值(元素,规格)
            if 值列 is None:
                坏=True
                break
            折叠=规格.get('foldMax')
            for 值 in 值列:
                命中.add(规格['min'] if 值==折叠 else 值)
        if 坏:
            解析.append(None)
        else:
            值列=sorted(命中)
            星号=原文.startswith('*')
            全满=len(值列)==规格['count']
            解析.append({'values':值列,'starred':星号,'full':全满,'unrestricted':星号 and 全满})
        序=序+1
    if None in 解析:
        return None
    return {
        'minutes':解析[0],
        'hours':解析[1],
        'daysOfMonth':解析[2],
        'months':解析[3],
        'daysOfWeek':解析[4],
    }

def 两位(值):
    '至少两位'
    文=str(值)
    if len(文)<2:
        return '0'+文
    return 文

def 连续段(值列):
    '把升序值切成连续段'
    段列=[]
    for 值 in 值列:
        if len(段列)>0 and 定时下标(段列[-1],len(段列[-1])-1)+1==值:
            段列[-1].append(值)
        else:
            段列.append([值])
    return 段列

def 数字列表(值列,表):
    '用中文表的分隔符接数字'
    return 表['cron.list.join'].join([str(值) for 值 in 值列])

def 全范围步(值列,最小,最大):
    '覆盖整段且等步长时返回步长'
    if len(值列)<2:
        return None
    首=定时下标(值列,0)
    if 首!=最小:
        return None
    步=定时下标(值列,1)-首
    序=1
    while 序<len(值列):
        if 定时下标(值列,序)-定时下标(值列,序-1)!=步:
            return None
        序=序+1
    if 定时下标(值列,len(值列)-1)+步>最大:
        return 步
    return None

def 星期文本(值列,表):
    '星期名。连续三天以上收成范围'
    连接=表['cron.list.join']
    def 名称(日):
        '周几'
        return 套用(表['cron.weekday.name'],{'weekday':表[定时下标(星期键,日-1)]})
    国际=[7 if 值==0 else 值 for 值 in 值列]
    国际.sort()
    段文=[]
    for 段 in 连续段(国际):
        if len(段)>=3:
            段文.append(套用(表['cron.weekday.range'],{'from':名称(定时下标(段,0)),'to':名称(定时下标(段,len(段)-1))}))
        else:
            段文.append(连接.join([名称(日) for 日 in 段]))
    return 连接.join(段文)

def 月份后缀(值列,区域,表):
    '不是十二个月才加月份后缀'
    if len(值列)==12:
        return ''
    窗口=取握手窗口()
    格式=窗口.Intl.DateTimeFormat(区域,{'month':'long','timeZone':'UTC'})
    月份=[]
    for 月 in 值列:
        月份.append(格式.format(窗口.Date.UTC(2026,月-1,1)))
    return 套用(表['cron.months'],{'months':表['cron.list.join'].join(月份)})

def 日文本(解析,区域,表):
    '这一条规则命中哪些天'
    月份=月份后缀(解析['months']['values'],区域,表)
    星期=星期文本(解析['daysOfWeek']['values'],表)
    日=数字列表(解析['daysOfMonth']['values'],表)
    参数={'days':日,'weekdays':星期,'months':月份}
    月日=解析['daysOfMonth']
    周=解析['daysOfWeek']
    if 月日['starred'] or 周['starred']:
        if 月日['full'] and 周['full']:
            return {'everyDay':月份=='','text':套用(表['cron.day.every'],{'months':月份})}
        if 月日['full']:
            return {'everyDay':False,'text':套用(表['cron.day.weekdays'],参数)}
        if 周['full']:
            return {'everyDay':False,'text':套用(表['cron.day.monthDays'],参数)}
        return {'everyDay':False,'text':套用(表['cron.day.bothStarred'],参数)}
    if 月日['full'] or 周['full']:
        return {'everyDay':月份=='','text':套用(表['cron.day.every'],{'months':月份})}
    return {'everyDay':False,'text':套用(表['cron.day.both'],参数)}

def 小时文本(值列,表):
    '连续小时写成范围，否则列举'
    小时=[两位(值) for 值 in 值列]
    连续=len(小时)>=2 and 定时下标(值列,len(值列)-1)-定时下标(值列,0)==len(值列)-1
    if 连续:
        return 套用(表['cron.hours.range'],{'from':定时下标(小时,0),'to':定时下标(小时,len(小时)-1)})
    return 套用(表['cron.hours.list'],{'hours':表['cron.list.join'].join(小时)})

def 时刻文本(解析,表):
    '一天里的时刻。interval 表示这句话自己就是重复'
    步=None if 解析['minutes']['unrestricted'] else 全范围步(解析['minutes']['values'],0,59)
    if 解析['hours']['unrestricted']:
        if 解析['minutes']['unrestricted']:
            return {'interval':True,'text':表['cron.time.everyMinute'],'joined':表['cron.time.joinedEveryMinute']}
        if 步 is not None and 步>=2:
            return {
                'interval':True,
                'text':套用(表['cron.time.everyMinutes'],{'step':步}),
                'joined':套用(表['cron.time.joinedEveryMinutes'],{'step':步}),
            }
        if len(解析['minutes']['values'])==1 and 定时下标(解析['minutes']['values'],0)==0:
            return {'interval':True,'text':表['cron.time.everyHour'],'joined':表['cron.time.joinedEveryHour']}
        分钟=数字列表(解析['minutes']['values'],表)
        return {
            'interval':False,
            'text':套用(表['cron.time.hourlyAt'],{'minutes':分钟}),
            'joined':套用(表['cron.time.joinedHourlyAt'],{'minutes':分钟}),
        }
    小时=小时文本(解析['hours']['values'],表)
    if 解析['minutes']['unrestricted']:
        文=套用(表['cron.time.hoursEveryMinute'],{'hours':小时})
        return {'interval':False,'text':文,'joined':文}
    if 步 is not None and 步>=2:
        文=套用(表['cron.time.hoursEveryMinutes'],{'hours':小时,'step':步})
        return {'interval':False,'text':文,'joined':文}
    小时步=全范围步(解析['hours']['values'],0,23)
    if len(解析['minutes']['values'])==1 and 定时下标(解析['minutes']['values'],0)==0 and 小时步 is not None and 小时步>=2:
        return {
            'interval':True,
            'text':套用(表['cron.time.everyNHours'],{'count':小时步}),
            'joined':套用(表['cron.time.joinedEveryNHours'],{'count':小时步}),
        }
    时刻=[]
    for 时 in 解析['hours']['values']:
        for 分 in 解析['minutes']['values']:
            时刻.append(两位(时)+':'+两位(分))
    if len(时刻)<=时刻列举上限:
        文=套用(表['cron.time.at'],{'times':表['cron.list.join'].join(时刻)})
    else:
        文=套用(表['cron.time.hoursAt'],{'hours':小时,'minutes':数字列表(解析['minutes']['values'],表)})
    return {'interval':False,'text':文,'joined':文}

def 定时预览(解析,表,区域):
    '把解析结果说成一句中文'
    日=日文本(解析,区域,表)
    时=时刻文本(解析,表)
    if 日['everyDay'] and 时['interval']:
        return 时['text']
    return 表['cron.part.join'].join([日['text'],时['joined']])

def 识别定时形状(解析):
    '能被构建器编辑的形状。月份必须全满'
    if not 解析['months']['full']:
        return None
    分步=1 if 解析['minutes']['unrestricted'] else 全范围步(解析['minutes']['values'],0,59)
    时步=1 if 解析['hours']['unrestricted'] else 全范围步(解析['hours']['values'],0,23)
    分=定时下标(解析['minutes']['values'],0) if len(解析['minutes']['values'])==1 else None
    时=定时下标(解析['hours']['values'],0) if len(解析['hours']['values'])==1 else None
    if 解析['daysOfWeek']['unrestricted']:
        if 解析['daysOfMonth']['unrestricted']:
            if 分步 is not None and 解析['hours']['full']:
                return {'kind':'minutely','step':分步}
            if 分 is not None and 时步 is not None:
                return {'kind':'hourly','step':时步,'minute':分}
            if 分 is not None and 时 is not None:
                return {'kind':'daily','hour':时,'minute':分}
            return None
        if 分 is None or 时 is None:
            return None
        return {'kind':'monthly','days':解析['daysOfMonth']['values'],'hour':时,'minute':分}
    if (not 解析['daysOfMonth']['unrestricted']) or 分 is None or 时 is None:
        return None
    星期=[7 if 值==0 else 值 for 值 in 解析['daysOfWeek']['values']]
    星期.sort()
    return {'kind':'weekly','weekdays':星期,'hour':时,'minute':分}

def 段字段(值列):
    '连续三段以上收成 a-b'
    段文=[]
    for 段 in 连续段(值列):
        if len(段)>=3:
            段文.append(str(定时下标(段,0))+'-'+str(定时下标(段,len(段)-1)))
        else:
            段文.append(','.join([str(值) for 值 in 段]))
    return ','.join(段文)

def 定时形状表达式(状态):
    '构建器形状写成五字段表达式'
    种类=状态['kind']
    if 种类=='minutely':
        if 状态['step']==1:
            return '* * * * *'
        return '*/'+str(状态['step'])+' * * * *'
    if 种类=='hourly':
        if 状态['step']==1:
            return str(状态['minute'])+' * * * *'
        return str(状态['minute'])+' */'+str(状态['step'])+' * * *'
    if 种类=='daily':
        return str(状态['minute'])+' '+str(状态['hour'])+' * * *'
    if 种类=='weekly':
        星期=sorted(set([日%7 for 日 in 状态['weekdays']]))
        return str(状态['minute'])+' '+str(状态['hour'])+' * * '+段字段(星期)
    if 种类=='monthly':
        日=sorted(set(状态['days']))
        return str(状态['minute'])+' '+str(状态['hour'])+' '+段字段(日)+' * *'
    return 断言永不(状态)
