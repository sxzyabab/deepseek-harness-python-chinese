import math

__all__=['轨迹记录身份','格式化毫秒时长','格式化已用秒数']

def 轨迹记录身份(格):
    '解析前置更旧投影记录后仍稳定的身份'
    if 格.get('recordId') is not None:#投影自带身份
        return 格['recordId']
    if 格.get('callId') is not None:#工具调用
        return 格['kind']+'\u0000call\u0000'+str(格['callId'])
    if 格.get('sourceSeq') is not None:#源事件序号
        return 格['kind']+'\u0000seq\u0000'+str(格['sourceSeq'])
    return 格['kind']+'\u0000index\u0000'+str(格['index'])#夹具回退

def 格式化毫秒时长(毫秒):
    '把毫秒时长格式化成千分位分隔的标签；未知时为破折号'
    if 毫秒 is None or isinstance(毫秒,bool) or not isinstance(毫秒,(int,float)) or not math.isfinite(毫秒):
        return '—'#未知
    整数=str(round(毫秒))#四舍五入
    符号=''#正数无号
    数字=整数
    if 整数.startswith('-'):
        符号='-'#负号
        数字=整数[1:]
    分组=[]#从右每三位
    while len(数字)>3:
        分组.append(数字[-3:])
        数字=数字[:-3]
    分组.append(数字)
    分组.reverse()
    return 符号+','.join(分组)+' 毫秒'#中文单位

def 格式化已用秒数(秒):
    '把以秒给出的经过时长格式化成毫秒标签'
    if 秒 is None:
        return 格式化毫秒时长(None)#未知
    return 格式化毫秒时长(秒*1000)#秒转毫秒
