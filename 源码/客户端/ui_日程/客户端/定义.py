'右侧任务标签的种类和参数'

__all__=['任务标识','任务种类','任务标签定义','任务参数']

任务标识='@deepseek-ai/dsh-client-ui-schedule/task'
任务种类='scheduleTask'

def 任务标签定义(翻译):
    '芯片正文由标题组件替换；这里只给种类'
    def 标题():
        '缺省详情名'
        return 翻译('detail.label')
    return {'id':任务标识,'kind':任务种类,'priority':'builtin','title':标题}

def 任务参数(参数):
    '另一类标签的参数返回 None'
    if not isinstance(参数,dict):
        return None
    if 'sessionId' not in 参数 or 'id' not in 参数:
        return None
    return {'sessionId':参数['sessionId'],'id':参数['id']}
