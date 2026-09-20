"""仅用于自动化的 Agent Client Protocol 服务器，经 JSON-RPC stdio 承载。

本桥接向受信任的程序化客户端暴露新铸造的 harness 会话。保持具名插件导出且无默认导出。
"""
import os,sys,threading,uuid#绝对路径、stdio、后台线程与会话 id
from ...依赖 import cordis#外部依赖胶水
聚合错误=cordis.聚合错误#多失败聚合
from ...依赖.schemastery import 字符串字段
from ...模型后端.llm import 创建用户消息,错误链#铸造用户消息与错误链文本
from ...内核.会话 import 会话标识#会话 id 品牌
from .编解码 import ACP提示转文本,提示含不受支持内容,回合结束到停止原因#提示展平与停止原因映射
from .线路 import 协议版本,请求错误,创建NDJSON流,智能体侧连接,操作任务#ACP 线路面

__all__=['包名','名称','依赖','应用','默认','配置']

包名='@deepseek-ai/dsh-acp'
名称='acp'
依赖=['agents']

配置={#插件配置模式
    'provider':字符串字段(),#可选提供方
    'model':字符串字段(),#可选模型
}

def 非法参数(细节):
    """把非法参数细节保留在 SDK 线路错误消息里。"""
    return 请求错误.非法参数(None,细节)#无数据载荷

def 内部错误(细节):
    """把失败回合细节保留为内部错误。"""
    return 请求错误.内部错误(None,细节)#无数据载荷

def 智能体选项(配置值):
    """不写入缺席的可选字段。配置为 dict。"""
    选项={}#稀疏选项
    if 'provider' in 配置值 and 配置值['provider'] is not None:#有提供方
        选项['provider']=配置值['provider']#写入
    if 'model' in 配置值 and 配置值['model'] is not None:#有模型
        选项['model']=配置值['model']#写入
    return 选项#仅已配置字段

def 校验会话参数(参数):
    """拒绝自动化约定之外的会话特性。参数为 dict。"""
    cwd=参数['cwd'] if 'cwd' in 参数 else None#工作目录
    if not os.path.isabs(cwd):#必须绝对路径
        raise 非法参数('cwd must be an absolute path: '+str(cwd))#拒绝
    额外=参数['additionalDirectories'] if 'additionalDirectories' in 参数 else None#额外目录
    if 额外 is not None and len(额外)>0:#额外目录非空
        raise 非法参数('additionalDirectories is not supported')#不支持
    if 'mcpServers' in 参数 and 参数['mcpServers'] is not None:#有 MCP 列表
        mcp=参数['mcpServers']#MCP 服务器
    else:#缺席
        mcp=[]#空列表
    if not isinstance(mcp,list):#非列表
        mcp=[]#当空
    if len(mcp)>0:#非空
        raise 非法参数('mcpServers is not supported')#不支持

class 智能体代理:
    """把字典处理器暴露为属性。"""
    def __init__(自身,表):
        """记下方法表。"""
        自身._表=表#方法表

    def __getattr__(自身,名):
        """缺席则 AttributeError。"""
        if 名 in 自身._表:#有
            return 自身._表[名]#方法
        raise AttributeError(名)#缺席

def 应用(上下文,配置值):
    """挂载仅自动化 ACP 服务器。配置为 dict。"""
    智能体服务=上下文.agents#智能体工厂
    日志器=上下文.日志#本插件日志器
    会话表={}#会话 id 到桥接记录
    已关闭标志={'v':False}#拆除后为真（用盒避免 nonlocal 杂糅）
    连接盒={'conn':None}#智能体侧 ACP 连接
    静止盒={'task':None}#进行中的静止任务

    def 拥有记录(智能体):
        """同 id 冒充者一律拒绝。"""
        记录=会话表[智能体.session.id] if 智能体.session.id in 会话表 else None#按会话 id 查找
        if 记录 is not None and 记录['agent'] is 智能体:#必须是同一智能体实例
            return 记录#拥有
        return None#非拥有

    def 断言开放():
        """已拆除则内部错误。"""
        if 已关闭标志['v']:#已拆除
            raise 内部错误('the ACP bridge has been disposed')#内部错误

    def 要求会话(会话号):
        """未知会话抛非法参数。"""
        记录=会话表[会话号] if 会话号 in 会话表 else None#按 id 查找
        if 记录 is None:#未知
            raise 非法参数('unknown session: '+str(会话号))#未知会话
        return 记录#已拥有的记录

    def 通知(通知载荷):
        """不让已断开的客户端把智能体回合打失败。"""
        try:
            连接盒['conn'].会话更新(通知载荷)#写更新
        except BaseException as 错误:
            日志器.警告('acp: session/update failed: '+str(错误))#传输写失败

    def 结算提示(记录,原因):
        """无进行中提示则忽略。"""
        飞行=记录['inflight'] if 'inflight' in 记录 else None#取出进行中槽
        if 飞行 is None:#无槽
            return#忽略
        记录['inflight']=None#先清槽
        飞行['resolve'](原因)#决议 prompt

    def 因错误拒绝(飞行,原因):
        """细节进内部错误。原因为 dict。"""
        错=原因['error'] if isinstance(原因,dict) and 'error' in 原因 else None#错误对象
        if isinstance(错,dict) and 'message' in 错:#有消息字段
            文案=str(错['message'])#消息
        else:#无结构化消息
            文案=str(错)#字符串化
        飞行['reject'](内部错误('turn failed: '+文案))#拒绝

    def 会话事件(会话,事件):
        """只发出已提交的助手文本。会话为对象，事件为 dict。"""
        头=会话.header#会话头
        头标识=头['id'] if isinstance(头,dict) and 'id' in 头 else 会话.id#按会话头 id
        记录=会话表[头标识] if 头标识 in 会话表 else None#查找记录
        if 记录 is None or 记录['agent'].session is not 会话:#非本桥接拥有或冒充者
            return#忽略
        try:
            if 'type' in 事件 and 事件['type']=='assistant/message':#已提交助手消息
                数据=事件['data'] if 'data' in 事件 else None#data
                消息=数据['message'] if isinstance(数据,dict) and 'message' in 数据 else None#message
                原始内容=消息['content'] if isinstance(消息,dict) and 'content' in 消息 else None#content
                内容=原始内容 if isinstance(原始内容,list) else []#非列表则空
                for 块 in 内容:#逐块
                    if not isinstance(块,dict):#非对象
                        continue#跳过
                    块类型=块['type'] if 'type' in 块 else None#块类型
                    if 块类型=='text':#文本块
                        文本=块['text'] if 'text' in 块 else None#原文
                        if isinstance(文本,str) and len(文本)>0:#非空文本
                            通知({#推送智能体消息分块
                                'sessionId':记录['agent'].session.id,#本会话 id
                                'update':{#更新载荷
                                    'sessionUpdate':'agent_message_chunk',#助手消息分块
                                    'content':{'type':'text','text':文本},#原文文本
                                },#update 结束
                            })#notify 结束
                    elif 块类型=='image':#图像块改写成文本引用
                        附件=块['attachment'] if 'attachment' in 块 else None#附件
                        附件号=附件['attachmentId'] if isinstance(附件,dict) and 'attachmentId' in 附件 else None#附件 id
                        通知({#推送图像占位文本
                            'sessionId':记录['agent'].session.id,#本会话 id
                            'update':{#更新载荷
                                'sessionUpdate':'agent_message_chunk',#助手消息分块
                                'content':{#文本内容
                                    'type':'text',#仍走文本通道
                                    'text':'[image attachment '+str(附件号)+']',#附件 id 引用
                                },#content 结束
                            },#update 结束
                        })#notify 结束
        finally:
            飞行=记录['inflight'] if 'inflight' in 记录 else None#取出进行中槽
            数据=事件['data'] if 'data' in 事件 else None#data
            回合=数据['turn'] if isinstance(数据,dict) and 'turn' in 数据 else None#回合
            if (飞行 is not None
                and 'type' in 事件 and 事件['type']=='turn/end'
                and 飞行['turn']==回合):#关联回合已结束
                原因=数据['reason'] if isinstance(数据,dict) and 'reason' in 数据 else None#结束原因
                种类=原因['kind'] if isinstance(原因,dict) and 'kind' in 原因 else None#结束种类
                if 种类=='error':#模型失败立刻变成 prompt 错误
                    记录['inflight']=None#先清槽
                    因错误拒绝(飞行,原因)#拒绝 prompt
                else:#非错误结束
                    飞行['endReason']=原因#记下结束原因，待空闲结算

    上下文.监听('session/event',会话事件)#挂监听

    def 收件箱认领(载荷):
        """同一消息则记下回合。载荷为 dict。"""
        记录=拥有记录(载荷['agent'] if 'agent' in 载荷 else None)#必须是桥接拥有的智能体
        飞行=记录['inflight'] if 记录 is not None and 'inflight' in 记录 else None#进行中提示
        消息=载荷['message'] if 'message' in 载荷 else None#消息
        消息号=消息.id if 消息 is not None else None#消息 id
        if 飞行 is not None and 飞行['messageId']==消息号:#同一消息
            飞行['turn']=载荷['turn'] if 'turn' in 载荷 else None#记下回合

    上下文.监听('agent/inbox/claimed',收件箱认领)#挂监听

    def 智能体错误(载荷):
        """其他回合的错误仍拒绝 prompt。载荷为 dict。"""
        记录=拥有记录(载荷['agent'] if 'agent' in 载荷 else None)#必须是桥接拥有的智能体
        飞行=记录['inflight'] if 记录 is not None and 'inflight' in 记录 else None#进行中提示
        回合=载荷['turn'] if 'turn' in 载荷 else None#回合
        if 记录 is None or 飞行 is None or 飞行['turn']==回合:#非拥有、无槽、或正是关联回合
            return#交给 turn/end
        记录['inflight']=None#清槽
        飞行['reject'](内部错误('turn failed: '+错误链(载荷['error'] if 'error' in 载荷 else None)))#拒绝

    上下文.监听('agent/error',智能体错误)#挂监听

    def 审批请求(请求,下一步):
        """只提供一次性选项。请求为 dict。"""
        记录=拥有记录(请求['agent'] if 'agent' in 请求 else None)#必须是桥接拥有的智能体
        if 记录 is None or 'callId' not in 请求 or 请求['callId'] is None:#非本桥接或无 callId
            return 下一步()#委托下游
        结果=连接盒['conn'].请求许可({#向 ACP 客户端要一次性许可
            'sessionId':记录['agent'].session.id,#本会话 id
            'toolCall':{'toolCallId':请求['callId']},#工具调用 id
            'options':[#仅一次性允许/拒绝
                {'optionId':'allow-once','name':'Allow once','kind':'allow_once'},#允许一次
                {'optionId':'reject-once','name':'Reject','kind':'reject_once'},#拒绝一次
            ],#选项结束
        })#请求结束
        结局=结果['outcome'] if isinstance(结果,dict) and 'outcome' in 结果 else None#客户端结果
        结局种类=结局['outcome'] if isinstance(结局,dict) and 'outcome' in 结局 else None#结果种类
        if 结局种类=='cancelled':#客户端取消
            return 'cancelled'#取消
        选项号=结局['optionId'] if isinstance(结局,dict) and 'optionId' in 结局 else None#选项
        return 'allowed-once' if 选项号=='allow-once' else 'rejected'#允许一次或拒绝

    上下文.监听('approval/request',审批请求)#挂监听

    def 铸造方法表(连接):
        """记下连接，供 notify 与权限请求使用。"""
        连接盒['conn']=连接#记下连接
        def 初始化(_参数):
            """单版本智能体。"""
            return {#初始化响应
                'protocolVersion':协议版本,#本服务器协议版本
                'agentInfo':{'name':'deepseek-harness-acp','version':'0.0.1'},#智能体名与版本
                'agentCapabilities':{#能力声明
                    'promptCapabilities':{'image':False,'audio':False,'embeddedContext':False},#基线
                },#能力结束
                'authMethods':[],#无认证方法
            }#响应结束
        def 认证(_参数):
            """空操作成功。"""
            return None#成功
        def 新建会话(参数):
            """以绝对路径作为主 cwd 创建新 agent。参数为 dict。"""
            断言开放()#已拆除则拒绝
            校验会话参数(参数)#拒绝自动化约定外的会话特性
            会话号=会话标识(str(uuid.uuid4()))#铸造新会话 id
            句柄=智能体服务.创建({#创建桥接拥有的智能体
                'sessionId':会话号,#使用刚铸造的会话 id
                'meta':{'cwd':参数['cwd'] if 'cwd' in 参数 else None},#工作目录写入会话元数据
                'agentOptions':智能体选项(配置值),#仅填入已配置的提供方/模型
            })#create 结束
            if 已关闭标志['v']:#创建期间连接已关
                句柄.拆除()#丢掉刚创建的智能体
                raise 内部错误('connection closed during session/new')#报告创建期间关闭
            def 拆本会话():
                """拆除本句柄。"""
                return 句柄.拆除()#委托
            会话表[会话号]={#登记桥接记录
                'agent':句柄.智能体,#拥有的智能体
                'dispose':拆本会话,#精确拥有拆除
                'inflight':None,#尚无进行中提示
            }#记录结束
            return {'sessionId':会话号}#把会话 id 交给客户端
        def 提示(参数):
            """每个会话只允许一个正在处理的请求。参数为 dict。"""
            断言开放()#已拆除则拒绝
            记录=要求会话(会话标识(参数['sessionId'] if 'sessionId' in 参数 else None))#取本桥接会话
            if 记录['inflight'] is not None:#已有进行中提示
                raise 非法参数('a prompt is already in flight for this session')#同时只允许一条
            原始提示=参数['prompt'] if 'prompt' in 参数 else None#提示块
            提示块=原始提示 if isinstance(原始提示,list) else []#非列表则空
            if 提示含不受支持内容(提示块):#含基线外内容
                raise 非法参数('only text and resource_link prompt content is supported')#拒绝
            文本=ACP提示转文本(提示块)#展平为文本
            if len(文本.strip())==0:#空白提示
                raise 非法参数('empty prompt')#非法
            if 上下文.agents.获取(记录['agent'].id) is not 记录['agent']:#注册表里已不是同一实例
                raise 内部错误('prompt was not queued: the agent was disposed outside the bridge')#桥接外拆除
            消息=创建用户消息({'content':[{'type':'text','text':文本}],'source':{'kind':'user'}})#铸造用户消息
            等待=操作任务()#等到结算才决议
            飞行={#新的进行中槽
                'resolve':等待.兑现,#决议器
                'reject':等待.拒绝,#拒绝器
                'messageId':消息.id,#消息 id
                'turn':None,#尚未认领回合
                'endReason':None,#尚未结束
            }#飞行结束
            记录['inflight']=飞行#先武装再发送
            try:
                记录['agent'].后续(消息)#投递到智能体收件箱
            except BaseException as 错误:
                记录['inflight']=None#释放槽位
                raise 内部错误('prompt was not queued: '+str(错误))#报告未能入队
            def 空闲结算():
                """关联的 turn/end 武装 endReason；无回合的槽保持 cancelled。"""
                try:
                    记录['agent'].等到空闲()#整智能体空闲
                except BaseException:
                    pass#继续结算
                if 记录['inflight'] is not 飞行:#已被错误路径或取消结算
                    return#忽略
                记录['inflight']=None#清槽
                结束=飞行['endReason']#关联回合结束原因
                if 结束 is None:#从未记下结束（提示被丢弃）
                    飞行['resolve']('cancelled')#报告已取消
                elif isinstance(结束,dict) and 'kind' in 结束 and 结束['kind']=='max-tokens':#max-tokens 仍报 end_turn
                    飞行['resolve']('end_turn')#end_turn
                else:#其它
                    飞行['resolve'](回合结束到停止原因(结束))#映射
            threading.Thread(target=空闲结算,daemon=True).start()#后台等空闲
            return {'stopReason':等待.等待()}#ACP 提示响应
        def 取消(参数):
            """未知 id 为空操作。参数为 dict。"""
            会话号=会话标识(参数['sessionId'] if 'sessionId' in 参数 else None)#会话
            记录=会话表[会话号] if 会话号 in 会话表 else None#按 id 查找
            if 记录 is None:#未知会话
                return None#当成功
            记录['agent'].取消({'kind':'user'})#用户取消智能体
            结算提示(记录,'cancelled')#进行中提示报告 cancelled
            return None#通知无响应体
        return {#ACP Agent 实现
            'initialize':初始化,#握手
            'authenticate':认证,#认证
            'newSession':新建会话,#新建会话
            'prompt':提示,#提示
            'cancel':取消,#取消
        }#表结束

    def 铸造包装(连接):
        """记下连接后返回代理。"""
        return 智能体代理(铸造方法表(连接))#代理

    流覆盖=配置值['stream'] if 'stream' in 配置值 else None#可选测试传输
    if 流覆盖 is None:#生产 stdio
        流=创建NDJSON流(sys.stdout,sys.stdin)#stdout 出、stdin 入
    else:#测试覆盖
        流=流覆盖#注入流
    连接=智能体侧连接(铸造包装,流)#打开智能体侧连接
    连接盒['conn']=连接#确保已赋值

    def 静止():
        """客户端断开与 Cordis 释放共用同一个记忆化清理流程。"""
        if 静止盒['task'] is not None:#已在静止
            return 静止盒['task'].等待()#复用
        任务=操作任务()#本轮静止
        静止盒['task']=任务#先登记防重入
        已关闭标志['v']=True#拒绝新会话与提示
        记录列表=list(会话表.values())#快照全部记录
        会话表.clear()#先清空表
        for 记录 in 记录列表:#取消每个会话
            记录['agent'].取消({'kind':'user'})#用户取消
            结算提示(记录,'cancelled')#进行中提示报告 cancelled
        try:
            子智能体=上下文.获取服务('subagents')#可选子智能体服务
            if 子智能体 is not None:#存在则可抽干
                try:
                    子智能体.排空可续跑后代([记录['agent'] for 记录 in 记录列表])#子先序抽干
                except BaseException as 错误:
                    日志器.警告('acp: continuable subagent teardown failed: '+str(错误))#不阻断顶层拆除
            失败列表=[]#收集拆除失败
            for 记录 in 记录列表:#逐条拆除顶层
                try:
                    记录['dispose']()#精确拥有拆除
                except BaseException as 错误:
                    失败列表.append(错误)#原因
            if len(失败列表)>0:#有会话拆除失败
                细节='; '.join(错误链(失败) for 失败 in 失败列表)#拼错误链
                raise 聚合错误(失败列表,'ACP agent teardown failed for '+str(len(失败列表))+' session(s): '+细节)#聚合
            任务.兑现(None)#成功
        except BaseException as 错误:
            任务.拒绝(错误)
        return 任务.等待()#把同一结果交给调用方

    def 连接关闭后():
        """无论成败都拆除会话。"""
        try:
            连接.已关闭.等待()#关闭边沿
        except BaseException as 错误:
            日志器.警告('acp: connection closed with an error: '+str(错误))#记日志后仍静止
        try:
            静止()#拆除会话
        except BaseException as 错误:
            日志器.警告('acp: connection-close teardown failed: '+str(错误))#记日志
    threading.Thread(target=连接关闭后,daemon=True).start()#后台盯关闭

    def 生命周期():
        """返回拆除函数。"""
        def 拆除():
            """记忆化清理。"""
            静止()#静止
        return 拆除#拆除器
    上下文.副作用(生命周期,'acp.connection')#副作用名

默认=应用
name=名称#框架槽
inject=依赖#框架槽
apply=应用#框架槽
Config=配置#框架槽
default=默认#框架槽
