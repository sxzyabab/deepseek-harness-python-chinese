'把共享宿主目录投成某一会话的活动任务'

__all__=['用会话日程事实']

空记录=()

def 用会话日程事实(用目录,会话标识):
    '未落定不算有活动任务。刷新中的 loading 仍用上次成功的记录'
    def 选择(快照):
        '只留这一会话、状态为 active 的记录'
        if not 快照.get('settled'):
            return {'hasActive':False,'records':空记录}
        记录=[项 for 项 in 快照['records'] if 项.get('sessionId')==会话标识 and 项.get('status')=='active']
        return {'hasActive':len(记录)>0,'records':记录}
    return 用目录(选择)
