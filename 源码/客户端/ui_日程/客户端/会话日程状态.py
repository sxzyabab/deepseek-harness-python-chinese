'把共享目录投影成某一个会话的活动任务'
from .目录源 import 创建目录源

__all__=['创建会话日程源','选取会话日程事实','会话悬停上限']

会话悬停上限=2
空记录=()

def 创建会话日程源(上下文,会话标识):
    '这一会话的活动提醒；读取不激活会话'
    def 列出():
        'schedule/list'
        return 上下文.remote.schedule.list({'sessionId':会话标识})
    def 移除(标识):
        'schedule/delete'
        return 上下文.remote.schedule.delete({'sessionId':会话标识,'id':标识})
    def 订变更(监听):
        'schedule/changed'
        远程=上下文.remote
        订=getattr(远程,'$on',None)
        if not callable(订):
            订=getattr(远程,'on',None)
        if not callable(订):
            raise RuntimeError('schedule change subscription is unavailable')
        return 订('schedule/changed',监听)
    def 订重置(监听):
        'connection/reset'
        return 上下文.on('connection/reset',监听)
    return 创建目录源({'list':列出,'remove':移除,'subscribeChanged':订变更,'subscribeReset':订重置})

def 选取会话日程事实(快照,会话标识):
    '未结算的读取不算有活动任务'
    if not isinstance(快照,dict) or 'settled' not in 快照 or 快照['settled'] is not True:
        return {'hasActive':False,'records':空记录}
    记录=快照['records'] if 'records' in 快照 and isinstance(快照['records'],list) else []
    活动=[项 for 项 in 记录 if isinstance(项,dict) and 项.get('sessionId')==会话标识 and 项.get('status')=='active']
    return {'hasActive':len(活动)>0,'records':活动}
