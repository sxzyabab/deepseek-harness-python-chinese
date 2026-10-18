'规则快照、可编辑时刻和宿主失败码。时区解释在宿主'
from ...模块.客户端.通告 import 取握手窗口
import re
from ....工具.值 import 断言永不

__all__=['时刻快照','草稿时区','分区墙钟','时刻草稿','斜杠日期','秒精度','时刻错误']

回退时区='UTC'

def 时刻快照(记录):
    '只留持久规则字段，给比较并更新做期望记录'
    公共={
        'id':记录['id'],
        'title':记录['title'],
        'prompt':记录['prompt'],
        'scheduledAt':记录['scheduledAt'],
    }
    种类=记录['kind']
    if 种类=='at':
        return {**公共,'kind':种类}
    if 种类=='after':
        return {**公共,'kind':种类,'afterSeconds':记录['afterSeconds']}
    if 种类=='every':
        return {**公共,'kind':种类,'everySeconds':记录['everySeconds']}
    if 种类=='daily':
        return {**公共,'kind':种类,'time':记录['time'],'timeZone':记录['timeZone']}
    if 种类=='weekly':
        return {**公共,'kind':种类,'time':记录['time'],'timeZone':记录['timeZone'],'weekdays':list(记录['weekdays'])}
    if 种类=='cron':
        return {**公共,'kind':种类,'expression':记录['expression'],'timeZone':记录['timeZone']}
    return 断言永不(记录)

def 草稿时区(记录):
    '有存时区就用存的。单次和间隔从设备时区起'
    已存=记录['timeZone'] if 'timeZone' in 记录 else None
    if 已存 is None:
        区=取握手窗口().Intl.DateTimeFormat().resolvedOptions().timeZone
        if 区 is None or 区=='':
            区=回退时区
        return {'zone':区,'stored':False}
    return {'zone':已存,'stored':True}

def 分区墙钟(瞬间,时区):
    '瞬间在该时区的 YYYY-MM-DDTHH:MM:SS.mmm。解析不了就空串'
    窗口=取握手窗口()
    时刻=窗口.Date(瞬间)
    if 时刻.getTime()!=时刻.getTime():
        return ''
    try:
        部分=窗口.Intl.DateTimeFormat('en-US',{
            'timeZone':时区,
            'year':'numeric','month':'2-digit','day':'2-digit',
            'hour':'2-digit','minute':'2-digit','second':'2-digit',
            'fractionalSecondDigits':3,
            'hourCycle':'h23',
        }).formatToParts(时刻)
        字段={}
        for 项 in 部分:
            字段[项['type']]=项['value']
        日期=str(字段.get('year'))+'-'+str(字段.get('month'))+'-'+str(字段.get('day'))
        钟=str(字段.get('hour'))+':'+str(字段.get('minute'))+':'+str(字段.get('second'))+'.'+str(字段.get('fractionalSecond'))
        return 日期+'T'+钟
    except Exception:
        return ''

def 时刻草稿(记录):
    '按规则种类填原生输入。不舍入秒和毫秒'
    草稿={'date':'','time':'','timeZone':'','seconds':'','expression':''}
    种类=记录['kind']
    if 种类=='at' or 种类=='after':
        时区=草稿时区(记录)['zone']
        墙钟=分区墙钟(记录['scheduledAt'],时区)
        return {**草稿,'date':墙钟[0:10],'time':墙钟[11:23],'timeZone':时区}
    if 种类=='every':
        return {**草稿,'seconds':str(记录['everySeconds'])}
    if 种类=='daily' or 种类=='weekly':
        return {**草稿,'time':记录['time'],'timeZone':记录['timeZone']}
    if 种类=='cron':
        return {**草稿,'expression':记录['expression'],'timeZone':记录['timeZone']}
    return 断言永不(记录)

def 斜杠日期(日期):
    '给行上看的斜杠日期。草稿本身仍是 ISO'
    return 日期.replace('-','/')

def 秒精度(时间):
    '显示到整秒。对不上时钟就原样返回'
    匹配=re.match(r'^(\d{2}):(\d{2})(?::(\d{2}))?',时间)
    if 匹配 is None:
        return 时间
    秒=匹配.group(3) if 匹配.group(3) is not None else '00'
    return 匹配.group(1)+':'+匹配.group(2)+':'+秒

def 时刻错误(代码):
    '宿主失败码对应的中文表键。调用处再用管理中文取出句子'
    if 代码=='schedule_conflict':
        return 'timing.conflict'
    if 代码=='schedule_ended':
        return 'timing.inactive'
    if 代码=='schedule_not_found':
        return 'timing.notFound'
    if 代码=='subagent_session':
        return 'timing.subagentSession'
    if 代码=='invalid_time_zone':
        return 'timing.invalidZone'
    if 代码=='not_future':
        return 'timing.notFuture'
    if 代码=='frequency_too_high':
        return 'timing.invalidInterval'
    if 代码 in ('invalid_prompt','invalid_selector','invalid_rule','time_out_of_range'):
        return 'timing.invalid'
    if 代码=='internal_error':
        return 'timing.error'
    return 断言永不(代码)
