"""建立在装备客户端之上的高层运行 API。

对齐上游 `sdk/client/src/api.ts`。公开面仅中文名。DeepSeekHarness 跨多个会话拥有一个运行时子进程；HarnessSession.run 发送一条提示，并在整个智能体下次进入空闲时落定。
"""
import os,uuid#工作目录与会话 id
from ...依赖 import cordis#外部依赖胶水
from .客户端 import 装备客户端,是否普通对象,SDK协议错误#底层客户端与协议错误

__all__=['深求装备','装备会话','运行选项','归一化输入','最终回复']#仅中文公开名

def 解开(值):#承诺则等待否则原样
    """承诺则等待，否则原样返回。"""
    if 是否thenable(值):#可等待
        return 值.等待()#等待承诺
    return 值#同步值

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段，缺席为缺省。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

class 深求装备:#高层 SDK 入口，跨会话拥有一个运行时
    """可复用的 SDK：在运行时子进程里跑 DeepSeek Harness 智能体回合。"""
    def __init__(自身,选项):#记下启动与路由
        """运行时启动规格加上会话路由（cwd/provider/model）。"""
        自身.启动=取字段(选项,'launch')#保存启动规格以便换新客户端
        自身.客户端实例=装备客户端(自身.启动)#先建一个底层客户端
        启动cwd=取字段(自身.启动,'cwd')#启动 cwd
        原始cwd=取字段(选项,'cwd')#选项 cwd
        if 原始cwd is not None:#显式 cwd
            自身.cwd=os.path.abspath(原始cwd)#绝对化
        elif 启动cwd is not None:#启动 cwd
            自身.cwd=os.path.abspath(启动cwd)#绝对化
        else:#进程 cwd
            自身.cwd=os.path.abspath(os.getcwd())#绝对化
        自身.provider=取字段(选项,'provider') or 'deepseek-official'#缺省官方提供方
        自身.model=取字段(选项,'model') or 'deepseek-v4-flash'#缺省模型
        自身.maxTokens=取字段(选项,'maxTokens')#可选上限原样保存
        自身.已初始化=None#已记忆的握手
        自身.已关闭=False#是否已终端关闭

    @property#只读
    def 客户端(自身):#当前底层客户端
        """握手失败会回收其运行时并换上新实例。"""
        return 自身.客户端实例#可能已在失败握手后被替换

    def 启动运行时(自身):#惰性握手，失败可换新客户端重试
        """启动子进程并只做一次 initialize 握手。"""
        if 自身.已初始化 is not None:#已记忆
            return 自身.已初始化#共用
        def 跑():#真正握手
            """启动并 initialize。"""
            try:#握手体
                自身.客户端实例.启动()#拉起子进程
                参数={'cwd':自身.cwd,'provider':自身.provider,'model':自身.model}#进程级握手
                if 自身.maxTokens is not None:#有上限才写入
                    参数['maxTokens']=自身.maxTokens#上限
                自身.客户端实例.初始化(参数)#initialize
            except BaseException as 错误:#握手失败则拆掉永久关闭的客户端
                自身.已初始化=None#清掉记忆，允许下次重试
                解开(自身.客户端实例.关闭())#回收失败的运行时
                if not 自身.已关闭:#harness 未终端关闭
                    自身.客户端实例=装备客户端(自身.启动)#换新客户端
                raise 错误#把原错误抛给调用方
        自身.已初始化=已兑现(跑())#立刻跑并记忆
        return 自身.已初始化#后续调用共用

    def 会话(自身,会话号=None):#构造会话句柄
        """打开一个会话句柄（无线上流量）。"""
        号=会话号 if 会话号 is not None else 'session-'+uuid.uuid4().hex#无 id 则造
        return 装备会话(自身,号)#会话句柄

    def 运行(自身,输入,选项=None):#便捷：开会话并 run
        """在一个新的（或具名）会话上跑一条提示。"""
        选项=选项 or {}#缺省空
        return 自身.会话(取字段(选项,'sessionId')).运行(输入,选项)#有 sessionId 则复用

    def 关闭(自身):#终端关闭
        """已关闭的 harness 不再重试失败的握手。"""
        自身.已关闭=True#之后 start 失败不再换新客户端
        return 自身.客户端实例.关闭()#拆除当前底层客户端

class 装备会话:#绑定到一个会话 id 的句柄
    """一个 SDK 会话：稳定 id 加上所拥有的活动区间。"""
    def __init__(自身,装备,标识):#保存所属 harness 与会话 id
        """记下所属与 id。"""
        自身.装备=装备#所属 harness
        自身.id=标识#本句柄所跑的线会话 id

    def 运行(自身,输入,选项=None):#跑一回合直到空闲
        """排队一条提示，然后观察整个会话直到它下次空闲。"""
        选项=选项 or {}#缺省空
        解开(自身.装备.启动运行时())#确保已握手
        客户端=自身.装备.客户端#取当前底层客户端
        内容块们=归一化输入(输入)#字符串变成文本块
        事件们=[]#本会话的 session.event 载荷
        通知们=[]#本树全部通知
        订阅=客户端.订阅会话树(自身.id)#订阅本会话及其后代
        def 收集(通知):#收集一条已确认属于本回合的通知
            """计入本回合。"""
            if (取字段(通知,'method')=='session.event'
                and 取字段(取字段(通知,'params'),'sessionId')==自身.id):#本会话的日志事件
                事件=校验会话事件(取字段(取字段(通知,'params'),'event'))#校验后再收
                通知们.append(通知)#记下原始通知
                观察=取字段(选项,'onNotification')#可选观察者
                if 观察 is not None:#有观察者
                    观察(通知)#回调
                事件们.append(事件)#记下校验后的事件
                return#本会话事件已处理
            通知们.append(通知)#其它树内通知
            观察=取字段(选项,'onNotification')#可选观察者
            if 观察 is not None:#有观察者
                观察(通知)#回调
        try:#提示并观察到空闲
            消息号=客户端.提示(自身.id,内容块们)#排队用户消息
            已收到=False#是否已见到该消息的收件箱回执
            while True:#直到本会话 idle
                通知=订阅.下一条()#下一条树内通知
                if not 已收到:#回执到来之前丢掉无关前缀
                    参数=取字段(通知,'params') or {}#载荷
                    if (取字段(通知,'method')!='session.event'
                        or 取字段(参数,'sessionId')!=自身.id
                        or not 是否收件箱回执(取字段(参数,'event'),消息号)):#尚未回执
                        continue#跳过
                    已收到=True#见到回执
                收集(通知)#计入本回合
                参数=取字段(通知,'params') or {}#再取载荷
                if (取字段(通知,'method')=='session.status'
                    and 取字段(参数,'sessionId')==自身.id
                    and 取字段(参数,'status')=='idle'):#空闲则回合结束
                    break#结束观察循环
        finally:#无论成败都关掉订阅
            订阅.关闭()#丢掉队列并拒绝等待者
        return {#组装活动区间
            'sessionId':自身.id,#本会话
            'finalResponse':最终回复(事件们),#末条助手文本
            'events':事件们,#本会话事件
            'notifications':通知们,#树内全部通知
        }#结束返回值

运行选项=('sessionId','onNotification')#run 的可选参数字段

def 归一化输入(输入):#字符串或块 → 块数组
    """字符串变成一块文本；内容块原样通过。"""
    if isinstance(输入,str):#字符串
        return [{'type':'text','text':输入}]#包成 text 块
    return 输入#原样

def 校验会话事件(值):#线事件 → 会话事件
    """在返回带类型结果之前，校验线 session.event 信封里的字段。"""
    if (not 是否普通对象(值)) or not isinstance(取字段(值,'type'),str):#必须是带 type 字符串的对象
        raise SDK协议错误('session.event carried no event envelope: '+str(值))#缺信封
    if 取字段(值,'type')=='assistant/message':#助手消息需要校验 content
        消息=取字段(取字段(值,'data'),'message') if 是否普通对象(取字段(值,'data')) else None#data.message
        内容=取字段(消息,'content') if 是否普通对象(消息) else None#content
        if (not isinstance(内容,list)
            or not all(是否普通对象(块) and isinstance(取字段(块,'type'),str) for 块 in 内容)):#每块必须有 type
            raise SDK协议错误('assistant/message event carried malformed content: '+str(值))#畸形 content
    return 值#通过校验

def 是否收件箱回执(值,消息号):#是否为该消息的 spliced 回执
    """原始会话事件是否为 messageId 的持久入队回执。"""
    if (not 是否普通对象(值)) or 取字段(值,'type')!='agent/inbox/spliced' or not 是否普通对象(取字段(值,'data')):#类型与 data 不对
        return False#不是
    插入=取字段(取字段(值,'data'),'inserted')#插入的消息列表
    if not isinstance(插入,list):#不是列表
        return False#不是
    for 消息 in 插入:#其中有该 id
        if 是否普通对象(消息) and 取字段(消息,'id')==消息号:#命中
            return True#是回执
    return False#没有

def 最终回复(事件们):#从事件里取末条助手文本
    """抽出末条助手消息拼接后的文本；没有则为空串。"""
    for 索引 in range(len(事件们)-1,-1,-1):#从后往前找
        事件=事件们[索引]#当前事件
        if 取字段(事件,'type')!='assistant/message':#跳过非助手消息
            continue#下一条
        内容=取字段(取字段(取字段(事件,'data'),'message'),'content') or []#内容块
        文本们=[]#文本片段
        for 块 in 内容:#逐块
            if 取字段(块,'type')=='text':#文本块
                文本们.append(取字段(块,'text') or '')#抽出 text
        return ''.join(文本们)#拼接
    return ''#没有任何助手消息
