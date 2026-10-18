class 工作区活动会话错误(Exception):
    '会话还有运行中的工作，不能归档'
    def __init__(自身,活动):
        '记下还在跑的活动'
        super().__init__('cannot archive session: activity is still running')
        自身.activity=活动

class 工作区已归档会话钉住错误(Exception):
    '已归档会话不能钉住'
    def __init__(自身,会话号):
        '记下被拒绝的会话'
        super().__init__('cannot pin an archived session')
        自身.sessionId=会话号

class 工作区错误(Exception):
    '工作区包的一般错误'

class 工作区移动无效错误(Exception):
    'insertSessionBefore 点名了未入账的会话或锚'
    def __init__(自身,消息):
        '记下非法移动诊断'
        super().__init__(消息)

class 工作区未知会话错误(Exception):
    '归档点名了活会话与持久化都不认识的会话'
    def __init__(自身,会话号):
        '记下未知会话 id'
        super().__init__("cannot archive session: live sessions and session persistence hold no such session")
        自身.sessionId=会话号

class 工作区顺序无效错误(Exception):
    '重排点名了未登记的工作区'
    def __init__(自身,工作区号):
        '记下未知工作区 id'
        super().__init__("cannot reorder unknown workspace")
        自身.workspaceId=工作区号
