import os,uuid#工作目录与会话 id
from .客户端 import 装备客户端,是否普通对象,SDK协议错误#底层客户端与协议错误

__all__=['深求装备','装备会话','运行选项','归一化输入','最终回复']#仅中文公开名

def 通知参数(通知):
    """取出通知 params 对象；缺席或非对象则为空 dict。"""
    原始=通知['params'] if 'params' in 通知 else None#载荷
    if isinstance(原始,dict):#普通对象
        return 原始#原样
    return {}#非对象则空对象

class 深求装备:
    """可复用的 SDK：在运行时子进程里跑 DeepSeek Harness 智能体回合。"""
    def __init__(自身,选项):
        """运行时启动规格加上会话路由（cwd/provider/model）。选项为 dict。"""
        自身.启动=选项['launch'] if 'launch' in 选项 else None#保存启动规格以便换新客户端
        自身.客户端实例=装备客户端(自身.启动)#先建一个底层客户端
        启动cwd=自身.启动['cwd'] if isinstance(自身.启动,dict) and 'cwd' in 自身.启动 else None#启动 cwd
        原始cwd=选项['cwd'] if 'cwd' in 选项 else None#选项 cwd
        if 原始cwd is not None:#显式 cwd
            自身.cwd=os.path.abspath(原始cwd)#绝对化
        elif 启动cwd is not None:#启动 cwd
            自身.cwd=os.path.abspath(启动cwd)#绝对化
        else:#进程 cwd
            自身.cwd=os.path.abspath(os.getcwd())#绝对化
        提供方=选项['provider'] if 'provider' in 选项 else None#提供方
        自身.provider=提供方 if 提供方 is not None and 提供方!='' else 'deepseek-official'#缺省官方提供方
        模型=选项['model'] if 'model' in 选项 else None#模型
        自身.model=模型 if 模型 is not None and 模型!='' else 'deepseek-v4-flash'#缺省模型
        自身.maxTokens=选项['maxTokens'] if 'maxTokens' in 选项 else None#可选上限原样保存
        自身.已初始化=None#已记忆的握手
        自身.已关闭=False#是否已终端关闭

    @property
    def 客户端(自身):
        """握手失败会回收其运行时并换上新实例。"""
        return 自身.客户端实例#可能已在失败握手后被替换

    def 启动运行时(自身):
        """启动子进程并只做一次 initialize 握手。"""
        if 自身.已初始化 is not None:#已记忆
            return 自身.已初始化#共用
        try:
            自身.客户端实例.启动()#拉起子进程
            参数={'cwd':自身.cwd,'provider':自身.provider,'model':自身.model}#进程级握手
            if 自身.maxTokens is not None:#有上限才写入
                参数['maxTokens']=自身.maxTokens#上限
            自身.客户端实例.初始化(参数)#initialize
        except BaseException:
            自身.已初始化=None#清掉记忆，允许下次重试
            自身.客户端实例.关闭()#回收失败的运行时
            if not 自身.已关闭:#harness 未终端关闭
                自身.客户端实例=装备客户端(自身.启动)#换新客户端
            raise#把原错误抛给调用方
        自身.已初始化=True#立刻记忆
        return 自身.已初始化#后续调用共用

    def 会话(自身,会话号=None):
        """打开一个会话句柄（无线上流量）。"""
        号=会话号 if 会话号 is not None else 'session-'+uuid.uuid4().hex#无 id 则造
        return 装备会话(自身,号)#会话句柄

    def 运行(自身,输入,选项=None):
        """在一个新的（或具名）会话上跑一条提示。选项为 dict。"""
        if 选项 is None:#缺省
            选项={}#空
        会话号=选项['sessionId'] if 'sessionId' in 选项 else None#可选会话
        return 自身.会话(会话号).运行(输入,选项)#有 sessionId 则复用

    def 关闭(自身):
        """已关闭的 harness 不再重试失败的握手。"""
        自身.已关闭=True#之后 start 失败不再换新客户端
        自身.客户端实例.关闭()#拆除当前底层客户端

class 装备会话:
    """一个 SDK 会话：稳定 id 加上所拥有的活动区间。"""
    def __init__(自身,装备,标识):
        """记下所属与 id。"""
        自身.装备=装备#所属 harness
        自身.id=标识#本句柄所跑的线会话 id

    def 运行(自身,输入,选项=None):
        """排队一条提示，然后观察整个会话直到它下次空闲。选项与通知为 dict。"""
        if 选项 is None:#缺省
            选项={}#空
        自身.装备.启动运行时()#确保已握手
        客户端=自身.装备.客户端#取当前底层客户端
        内容块列表=归一化输入(输入)#字符串变成文本块
        事件列表=[]#本会话的 session.event 载荷
        通知列表=[]#本树全部通知
        订阅=客户端.订阅会话树(自身.id)#订阅本会话及其后代
        def 收集(通知):
            """计入本回合。"""
            参数=通知参数(通知)#载荷
            方法=通知['method'] if 'method' in 通知 else None#方法名
            观察=选项['onNotification'] if 'onNotification' in 选项 else None#可选观察者
            本会话事件=方法=='session.event' and 'sessionId' in 参数 and 参数['sessionId']==自身.id#本会话的日志事件
            if 本会话事件:#本会话的日志事件
                事件=校验会话事件(参数['event'] if 'event' in 参数 else None)#校验后再收
                通知列表.append(通知)#记下原始通知
                if 观察 is not None:#有观察者
                    观察(通知)#回调
                事件列表.append(事件)#记下校验后的事件
                return#本会话事件已处理
            通知列表.append(通知)#其它树内通知
            if 观察 is not None:#有观察者
                观察(通知)#回调
        try:
            消息号=客户端.提示(自身.id,内容块列表)#排队用户消息
            已收到=False#是否已见到该消息的收件箱回执
            while True:#直到本会话 idle
                通知=订阅.下一条()#下一条树内通知
                if not 已收到:#回执到来之前丢掉无关前缀
                    参数=通知参数(通知)#载荷
                    方法=通知['method'] if 'method' in 通知 else None#方法名
                    事件=参数['event'] if 'event' in 参数 else None#事件
                    会话号=参数['sessionId'] if 'sessionId' in 参数 else None#会话
                    if 方法!='session.event' or 会话号!=自身.id or not 是否收件箱回执(事件,消息号):#尚未回执
                        continue#跳过
                    已收到=True#见到回执
                收集(通知)#计入本回合
                参数=通知参数(通知)#再取载荷
                方法=通知['method'] if 'method' in 通知 else None#方法名
                会话号=参数['sessionId'] if 'sessionId' in 参数 else None#会话
                状态=参数['status'] if 'status' in 参数 else None#状态
                if 方法=='session.status' and 会话号==自身.id and 状态=='idle':#空闲则回合结束
                    break#结束观察循环
        finally:
            订阅.关闭()#丢掉队列并拒绝等待者
        return {#组装活动区间
            'sessionId':自身.id,#本会话
            'finalResponse':最终回复(事件列表),#末条助手文本
            'events':事件列表,#本会话事件
            'notifications':通知列表,#树内全部通知
        }#结束返回值

运行选项=('sessionId','onNotification')#run 的可选参数字段

def 归一化输入(输入):
    """字符串变成一块文本；内容块原样通过。"""
    if isinstance(输入,str):#字符串
        return [{'type':'text','text':输入}]#包成 text 块
    return 输入#原样

def 校验会话事件(值):
    """在返回带类型结果之前，校验线 session.event 信封里的字段。"""
    if (not 是否普通对象(值)) or 'type' not in 值 or not isinstance(值['type'],str):#必须是带 type 字符串的对象
        raise SDK协议错误('session.event 没有事件信封：'+str(值))#缺信封
    if 值['type']=='assistant/message':#助手消息需要校验 content
        数据=值['data'] if 'data' in 值 else None#data
        消息=数据['message'] if 是否普通对象(数据) and 'message' in 数据 else None#data.message
        内容=消息['content'] if 是否普通对象(消息) and 'content' in 消息 else None#content
        if not isinstance(内容,list):#不是列表
            raise SDK协议错误('assistant/message 事件的 content 畸形：'+str(值))#畸形 content
        for 块 in 内容:#每块必须有 type
            if (not 是否普通对象(块)) or 'type' not in 块 or not isinstance(块['type'],str):#缺 type
                raise SDK协议错误('assistant/message 事件的 content 畸形：'+str(值))#畸形 content
    return 值#通过校验

def 是否收件箱回执(值,消息号):
    """原始会话事件是否为 messageId 的持久入队回执。"""
    if (not 是否普通对象(值)) or 'type' not in 值 or 值['type']!='agent/inbox/spliced':#类型不对
        return False#不是
    if 'data' not in 值 or not 是否普通对象(值['data']):#data 不对
        return False#不是
    插入=值['data']['inserted'] if 'inserted' in 值['data'] else None#插入的消息列表
    if not isinstance(插入,list):#不是列表
        return False#不是
    for 消息 in 插入:#其中有该 id
        if 是否普通对象(消息) and 'id' in 消息 and 消息['id']==消息号:#命中
            return True#是回执
    return False#没有

def 最终回复(事件列表):
    """抽出末条助手消息拼接后的文本；没有则为空串。"""
    for 索引 in range(len(事件列表)-1,-1,-1):#从后往前找
        事件=事件列表[索引]#当前事件
        if (not 是否普通对象(事件)) or 'type' not in 事件 or 事件['type']!='assistant/message':#跳过非助手消息
            continue#下一条
        数据=事件['data'] if 'data' in 事件 else None#data
        消息=数据['message'] if 是否普通对象(数据) and 'message' in 数据 else None#message
        原始内容=消息['content'] if 是否普通对象(消息) and 'content' in 消息 else None#内容块
        内容=原始内容 if isinstance(原始内容,list) else []#非列表则空
        文本列表=[]#文本片段
        for 块 in 内容:#逐块
            if 是否普通对象(块) and 'type' in 块 and 块['type']=='text':#文本块
                文本=块['text'] if 'text' in 块 else None#抽出 text
                文本列表.append(文本 if isinstance(文本,str) else '')#空则空串
        return ''.join(文本列表)#拼接
    return ''#没有任何助手消息
