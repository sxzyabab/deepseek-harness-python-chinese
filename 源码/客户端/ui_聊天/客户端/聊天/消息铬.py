from datetime import datetime as 日期时间,timedelta as 时间增量
import time as 时间模块

__all__=['本地日起点','距下一本地午夜毫秒','格式化运行时长','格式化延迟秒','格式化每秒令牌','格式化消息时钟','实况时钟间隔毫秒']

def 补两位(数):
    '左侧补零到两位'
    return str(数).zfill(2)

def 本地日起点(毫秒):
    '某瞬间对应的本地午夜毫秒'
    时刻=日期时间.fromtimestamp(毫秒/1000)
    午夜=时刻.replace(hour=0,minute=0,second=0,microsecond=0)
    return int(午夜.timestamp()*1000)

def 距下一本地午夜毫秒(毫秒):
    '至少 1ms，避免 0 定时器'
    时刻=日期时间.fromtimestamp(毫秒/1000)
    次日=(时刻+时间增量(days=1)).replace(hour=0,minute=0,second=0,microsecond=0)
    return max(int(次日.timestamp()*1000)-毫秒,1)

实况时钟间隔毫秒=1000


def 格式化运行时长(毫秒,翻译):
    '数字和单位交替。满 60 秒才写分钟，满 60 分钟才写小时'
    总秒=max(0,毫秒//1000)
    时=总秒//3600
    分=(总秒//60)%60
    秒=总秒%60
    段=[]
    if 时>0:
        段.append({'text':str(时),'numeric':True})
        段.append({'text':翻译('duration.hourUnit'),'numeric':False})
    if 总秒>=60:
        段.append({'text':str(分),'numeric':True})
        段.append({'text':翻译('duration.minuteUnit'),'numeric':False})
    段.append({'text':str(秒),'numeric':True})
    段.append({'text':翻译('duration.secondUnit'),'numeric':False})
    return 段

def 格式化延迟秒(毫秒):#延迟秒显示
    '十秒以下一位小数，以上整秒'
    秒=max(0,毫秒)/1000#钳零转秒
    if 秒<10:#一位小数
        return str(round(秒*10)/10)#一位
    return str(round(秒))#整秒

def 格式化每秒令牌(吞吐):#每秒 token
    '十及以上整，以下一位小数'
    值=max(0,吞吐)#钳零
    if 值>=10:#整
        return str(round(值))#整
    return str(round(值*10)/10)#一位

def 格式化消息时钟(时间,翻译,现在=None):
    '当日 HH:mm；本年 clock.md；跨年 clock.ymd'
    if 现在 is None:
        现在=int(时间模块.time()*1000)
    消息=日期时间.fromtimestamp(时间/1000)
    参照=日期时间.fromtimestamp(现在/1000)
    时钟=f'{补两位(消息.hour)}:{补两位(消息.minute)}'
    if 消息.year==参照.year and 消息.month==参照.month and 消息.day==参照.day:
        return 时钟
    参数={'y':消息.year,'m':消息.month,'d':消息.day}
    日期=翻译('clock.md',参数) if 消息.year==参照.year else 翻译('clock.ymd',参数)
    return f'{日期} {时钟}'
