'会话持久化失败'
__all__=[#仅中文公开名
    '持久化错误','中止错误','会话持久化损坏错误','会话格式不支持错误',
    '会话持久化未找到错误','会话已存在错误','会话已有写主错误','会话只读错误',
    '会话所有权丢失错误','会话句柄已关闭错误',
]#公开面结束

class 持久化错误(Exception):
    '会话持久化包的异常基类'

class 中止错误(持久化错误):
    '取消通道已中止'
    def __init__(自身,消息='aborted',种类=None):
        '用消息与可选控制流种类构造'
        super().__init__(消息)#错误消息原样英文
        if 种类 is not None:#有控制流种类
            自身.种类=种类#按结构识别，不做类型嗅探

class 会话持久化损坏错误(持久化错误):#持久化损坏错误
    '后端读取成功后，耐久会话内容未通过校验'
    def __init__(自身,消息,原因=None):#构造损坏错误
        '记下稳定损坏上下文与原始校验失败'
        if 原因 is not None:#有cause
            super().__init__(消息)#消息
            自身.__cause__=原因#挂cause
        else:#无cause
            super().__init__(消息)#消息
        自身.name='SessionPersistenceCorruptionError'#固定错误名

class 会话格式不支持错误(持久化错误):#格式不支持错误
    '已存日志完好，但本运行时无法忠实解释'
    def __init__(自身,消息,位置=None):#构造拒绝错误
        '记下无法解释原因与可选产物位置'
        super().__init__(消息)#消息
        自身.name='SessionFormatUnsupportedError'#固定错误名
        自身.位置=位置#产物位置

class 会话持久化未找到错误(持久化错误):#未找到
    '请求的已存会话不存在'
    def __init__(自身,标识):#构造
        '记下缺失身份'
        自身.id=标识#会话 id
        super().__init__('session "'+str(标识)+'" not found')#文案
        自身.name='SessionPersistenceNotFoundError'#固定错误名

class 会话已存在错误(持久化错误):#已存在
    '创建时会话 id 已存在'
    def __init__(自身,标识):#构造
        '记下冲突身份'
        自身.id=标识#会话 id
        super().__init__('session "'+str(标识)+'" already exists')#文案
        自身.name='SessionAlreadyExistsError'#固定错误名

class 会话已有写主错误(持久化错误):#已有写主
    '写打开时所有权已被占用'
    def __init__(自身,标识):#构造
        '记下被争用的会话身份'
        自身.id=标识#会话 id
        super().__init__('session "'+str(标识)+'" is already owned by another writer')#文案
        自身.name='SessionAlreadyOwnedError'#固定错误名

class 会话只读错误(持久化错误):#只读
    '读句柄上拒绝变更操作'
    def __init__(自身,标识,操作):#构造
        '记下会话与被拒操作'
        自身.id=标识#会话 id
        自身.操作=操作#操作名
        super().__init__('session "'+str(标识)+'" handle is read-only; cannot '+str(操作))#文案
        自身.name='SessionReadOnlyError'#固定错误名

class 会话所有权丢失错误(持久化错误):#所有权丢失
    '写所有权在句柄生命周期内丢失'
    def __init__(自身,标识):#构造
        '记下丢失所有权的会话'
        自身.id=标识#会话 id
        super().__init__('session "'+str(标识)+'" write ownership was lost')#文案
        自身.name='SessionOwnershipLostError'#固定错误名

class 会话句柄已关闭错误(持久化错误):#已关闭
    '已关闭句柄上的操作'
    def __init__(自身,标识,操作):#构造
        '记下会话与被拒操作'
        自身.id=标识#会话 id
        自身.操作=操作#操作名
        super().__init__('session "'+str(标识)+'" handle is closed; cannot '+str(操作))#文案
        自身.name='SessionHandleClosedError'#固定错误名
