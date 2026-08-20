"""用户/助手 IconActions 行共用的时间标签辅助。

对齐上游 `ui-conversation/src/client/chat/message-chrome.ts`。公开面仅中文名。
"""

__all__=['本地日起点','距下一本地午夜毫秒','格式化运行时长','格式化延迟秒','格式化每秒令牌','格式化消息时钟']#仅中文公开名

def 补两位(数):#补成两位
    """左侧补零到两位。"""
    return str(数).zfill(2)#两位

def 本地日起点(毫秒):#本地日历日午夜
    """某瞬间对应的本地午夜毫秒。"""
    from datetime import datetime#本地日历
    时刻=datetime.fromtimestamp(毫秒/1000)#该瞬间
    午夜=时刻.replace(hour=0,minute=0,second=0,microsecond=0)#拨到午夜
    return int(午夜.timestamp()*1000)#午夜毫秒

def 距下一本地午夜毫秒(毫秒):#距下一本地午夜
    """至少 1ms，避免 0 定时器。"""
    from datetime import datetime,timedelta#日历
    时刻=datetime.fromtimestamp(毫秒/1000)#该瞬间
    次日=(时刻+timedelta(days=1)).replace(hour=0,minute=0,second=0,microsecond=0)#次日午夜
    return max(int(次日.timestamp()*1000)-毫秒,1)#差值至少 1

def 格式化运行时长(毫秒,翻译):#经过时长标签
    """满一分钟走分钟模板，否则只报秒。"""
    总秒=max(0,毫秒//1000)#钳零整秒
    分=总秒//60#整分钟
    秒=总秒%60#余秒
    if 分>0:#分钟模板
        return 翻译('duration.minutes',{'minutes':分,'seconds':补两位(秒)})#分+秒
    return 翻译('duration.seconds',{'seconds':秒})#仅秒

def 格式化延迟秒(毫秒):#延迟秒显示
    """十秒以下一位小数，以上整秒。"""
    秒=max(0,毫秒)/1000#钳零转秒
    if 秒<10:#一位小数
        return str(round(秒*10)/10)#一位
    return str(round(秒))#整秒

def 格式化每秒令牌(吞吐):#每秒 token
    """十及以上整，以下一位小数。"""
    值=max(0,吞吐)#钳零
    if 值>=10:#整
        return str(round(值))#整
    return str(round(值*10)/10)#一位

def 格式化消息时钟(时间,翻译,现在=None):#消息行紧凑时钟
    """当日 HH:mm；本年 clock.md；跨年 clock.ymd。"""
    from datetime import datetime#日历
    import time as 时间模块#墙钟
    if 现在 is None:#缺省墙钟
        现在=int(时间模块.time()*1000)#当前毫秒
    消息=datetime.fromtimestamp(时间/1000)#消息瞬间
    参照=datetime.fromtimestamp(现在/1000)#参照
    时钟=f'{补两位(消息.hour)}:{补两位(消息.minute)}'#HH:mm
    if 消息.year==参照.year and 消息.month==参照.month and 消息.day==参照.day:#当日
        return 时钟#仅时钟
    参数={'y':消息.year,'m':消息.month,'d':消息.day}#模板参数
    日期=翻译('clock.md',参数) if 消息.year==参照.year else 翻译('clock.ymd',参数)#日期模板
    return f'{日期} {时钟}'#日期+时钟
