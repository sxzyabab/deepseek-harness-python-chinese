"""仅用于自动化的 Agent Client Protocol 服务器，经 JSON-RPC stdio 承载。

对齐上游 `@deepseek-ai/dsh-acp`。公开面仅中文名。本桥接向受信任的程序化客户端暴露新铸造的 harness 会话。保持具名插件导出且无默认导出。
"""
import os,sys,threading,uuid#绝对路径、stdio、后台线程与会话 id
from concurrent.futures import Future as _原生Future#单次操作结果
from ...依赖 import cordis#外部依赖胶水
聚合错误=cordis.聚合错误#多失败聚合
from ...依赖 import schemastery#配置字段
字符串字段=schemastery.字符串字段#配置字段
from ...模型后端.llm import 创建用户消息,错误链#铸造用户消息与错误链文本
from ...内核.会话 import 会话标识#会话 id 品牌
from .编解码 import ACP提示转文本,提示含不受支持内容,回合结束到停止原因#提示展平与停止原因映射
from .线路 import 协议版本,请求错误,创建NDJSON流,智能体侧连接#ACP 线路面

__all__=['名称','注入','配置','应用']#仅中文公开名

名称='acp'#Cordis插件名（字面量）
注入=['agents']#依赖 agents 服务

配置={#插件配置模式
    'provider':字符串字段(),#可选提供方
    'model':字符串字段(),#可选模型
}#配置结束

class 操作任务:#单次异步结果
    def __init__(自身):#构造未决任务
        自身._future=_原生Future()#底层 Future
    def 兑现(自身,值=None):#成功结算
        if not 自身._future.done():#尚未结算
            自身._future.set_result(值)#写入结果
        return 值#返回兑现值
    def 拒绝(自身,错误):#失败结算
        if not 自身._future.done():#尚未结算
            if isinstance(错误,BaseException):#已是异常
                自身._future.set_exception(错误)#原样拒绝
            else:#非异常
                自身._future.set_exception(Exception(错误))#包装拒绝
    def wait(自身,超时=None):#阻塞等待
        return 自身._future.result(timeout=超时)#取结果或抛错
    def 等待(自身,超时=None):#兼容外来调用
        return 自身.wait(超时)#转发

def _是否thenable(值):#判定可等待对象
    if 值 is None:#空不是
        return False#不是
    if callable(getattr(值,'wait',None)):#Future 风格
        return True#可等待
    return callable(getattr(值,'等待',None))#外来 thenable

def _等待(值):#统一阻塞到结算
    if callable(getattr(值,'wait',None)):#Future 风格
        return 值.wait()#等待
    return 值.等待()#外来 thenable

def 已兑现(值=None):#立刻兑现的操作任务
    任务=操作任务()#新任务
    任务.兑现(值)#立刻成功
    return 任务#已完成

def 解开(值):#可等待则等待否则原样
    """可等待则等待，否则原样返回。"""
    if _是否thenable(值):#可等待
        return _等待(值)#等待
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

def 非法参数(细节):#铸造 invalid-params 错误
    """把非法参数细节保留在 SDK 线路错误消息里。"""
    return 请求错误.非法参数(None,细节)#无数据载荷

def 内部错误(细节):#铸造 internal 错误
    """把失败回合细节保留为内部错误。"""
    return 请求错误.内部错误(None,细节)#无数据载荷

def 智能体选项(配置值):#从插件配置构造每智能体选项
    """不写入缺席的可选字段。"""
    选项={}#稀疏选项
    if 取字段(配置值,'provider') is not None:#有提供方
        选项['provider']=取字段(配置值,'provider')#写入
    if 取字段(配置值,'model') is not None:#有模型
        选项['model']=取字段(配置值,'model')#写入
    return 选项#仅已配置字段

def 校验会话参数(参数):#校验 newSession 参数
    """拒绝自动化约定之外的会话特性。"""
    cwd=取字段(参数,'cwd')#工作目录
    if not os.path.isabs(cwd):#必须绝对路径
        raise 非法参数('cwd must be an absolute path: '+str(cwd))#拒绝
    额外=取字段(参数,'additionalDirectories')#额外目录
    if 额外 is not None and len(额外)>0:#额外目录非空
        raise 非法参数('additionalDirectories is not supported')#不支持
    mcp=取字段(参数,'mcpServers') or []#MCP 服务器
    if len(mcp)>0:#非空
        raise 非法参数('mcpServers is not supported')#不支持

class 智能体代理:#把字典处理器暴露为属性
    """供线路 getattr 取方法。"""
    def __init__(自身,表):#保存表
        """记下方法表。"""
        自身._表=表#方法表
    def __getattr__(自身,名):#按名取
        """缺席则 AttributeError。"""
        if 名 in 自身._表:#有
            return 自身._表[名]#方法
        raise AttributeError(名)#缺席

def 应用(上下文,配置值):#安装 ACP 桥接插件
    """挂载仅自动化 ACP 服务器。"""
    智能体们=上下文.agents#智能体工厂
    日志器=上下文.logger#本插件日志器
    会话表={}#会话 id 到桥接记录
    已关闭标志={'v':False}#拆除后为真（用盒避免 nonlocal 杂糅）
    连接盒={'conn':None}#智能体侧 ACP 连接
    静止盒={'task':None}#进行中的静止承诺

    def 拥有记录(智能体):#按身份取拥有记录
        """同 id 冒充者一律拒绝。"""
        记录=会话表.get(智能体.session.id)#按会话 id 查找
        if 记录 is not None and 记录['agent'] is 智能体:#必须是同一智能体实例
            return 记录#拥有
        return None#非拥有

    def 断言开放():#拆除后拒绝新工作
        """已拆除则内部错误。"""
        if 已关闭标志['v']:#已拆除
            raise 内部错误('the ACP bridge has been disposed')#内部错误

    def 要求会话(会话号):#取已知会话或报非法参数
        """未知会话抛非法参数。"""
        记录=会话表.get(会话号)#按 id 查找
        if 记录 is None:#未知
            raise 非法参数('unknown session: '+str(会话号))#未知会话
        return 记录#已拥有的记录

    def 通知(通知载荷):#尽力推送会话更新
        """不让已断开的客户端把智能体回合打失败。"""
        try:#推送
            解开(连接盒['conn'].会话更新(通知载荷))#写更新
        except BaseException as 错误:#写失败只记日志
            日志器.warn('acp: session/update failed: '+str(错误))#传输写失败

    def 结算提示(记录,原因):#以停止原因决议进行中提示
        """无进行中提示则忽略。"""
        飞行=记录.get('inflight')#取出进行中槽
        if 飞行 is None:#无槽
            return#忽略
        记录['inflight']=None#先清槽
        飞行['resolve'](原因)#决议 prompt

    def 因错误拒绝(飞行,原因):#把回合错误变成 prompt 拒绝
        """细节进内部错误。"""
        错=取字段(原因,'error')#错误对象
        飞行['reject'](内部错误('turn failed: '+str(取字段(错,'message') if 错 is not None else 错)))#拒绝

    def 会话事件(会话,事件):#订阅会话事件
        """只发出已提交的助手文本。"""
        记录=会话表.get(会话.header.id)#按会话头 id 查找记录
        if 记录 is None or 记录['agent'].session is not 会话:#非本桥接拥有或冒充者
            return#忽略
        try:#先推送助手文本
            if 取字段(事件,'type')=='assistant/message':#已提交助手消息
                for 块 in 取字段(取字段(取字段(事件,'data'),'message'),'content') or []:#逐块
                    if 取字段(块,'type')=='text' and len(取字段(块,'text') or '')>0:#非空文本
                        通知({#推送智能体消息分块
                            'sessionId':记录['agent'].session.id,#本会话 id
                            'update':{#更新载荷
                                'sessionUpdate':'agent_message_chunk',#助手消息分块
                                'content':{'type':'text','text':取字段(块,'text')},#原文文本
                            },#update 结束
                        })#notify 结束
                    elif 取字段(块,'type')=='image':#图像块改写成文本引用
                        附件=取字段(块,'attachment')#附件
                        通知({#推送图像占位文本
                            'sessionId':记录['agent'].session.id,#本会话 id
                            'update':{#更新载荷
                                'sessionUpdate':'agent_message_chunk',#助手消息分块
                                'content':{#文本内容
                                    'type':'text',#仍走文本通道
                                    'text':'[image attachment '+str(取字段(附件,'attachmentId'))+']',#附件 id 引用
                                },#content 结束
                            },#update 结束
                        })#notify 结束
        finally:#无论推送成败都尝试结算回合
            飞行=记录.get('inflight')#取出进行中槽
            if (飞行 is not None
                and 取字段(事件,'type')=='turn/end'
                and 飞行.get('turn')==取字段(取字段(事件,'data'),'turn')):#关联回合已结束
                原因=取字段(取字段(事件,'data'),'reason')#结束原因
                if 取字段(原因,'kind')=='error':#模型失败立刻变成 prompt 错误
                    记录['inflight']=None#先清槽
                    因错误拒绝(飞行,原因)#拒绝 prompt
                else:#非错误结束
                    飞行['endReason']=原因#记下结束原因，待空闲结算

    上下文.on('session/event',会话事件)#挂监听

    def 收件箱认领(载荷):#收件箱认领，绑定回合号
        """同一消息则记下回合。"""
        记录=拥有记录(取字段(载荷,'agent'))#必须是桥接拥有的智能体
        飞行=取字段(记录,'inflight') if 记录 is not None else None#进行中提示
        if 飞行 is not None and 飞行.get('messageId')==取字段(取字段(载荷,'message'),'id'):#同一消息
            飞行['turn']=取字段(载荷,'turn')#记下回合

    上下文.on('agent/inbox/claimed',收件箱认领)#挂监听

    def 智能体错误(载荷):#智能体错误，可能与进行中提示相关
        """其他回合的错误仍拒绝 prompt。"""
        记录=拥有记录(取字段(载荷,'agent'))#必须是桥接拥有的智能体
        飞行=取字段(记录,'inflight') if 记录 is not None else None#进行中提示
        if 记录 is None or 飞行 is None or 飞行.get('turn')==取字段(载荷,'turn'):#非拥有、无槽、或正是关联回合
            return#交给 turn/end
        记录['inflight']=None#清槽
        飞行['reject'](内部错误('turn failed: '+错误链(取字段(载荷,'error'))))#拒绝

    上下文.on('agent/error',智能体错误)#挂监听

    def 审批请求(请求,下一步):#拦截本桥接智能体的审批请求
        """只提供一次性选项。"""
        记录=拥有记录(取字段(请求,'agent'))#必须是桥接拥有的智能体
        if 记录 is None or 取字段(请求,'callId') is None:#非本桥接或无 callId
            return 下一步()#委托下游
        结果=解开(连接盒['conn'].请求许可({#向 ACP 客户端要一次性许可
            'sessionId':记录['agent'].session.id,#本会话 id
            'toolCall':{'toolCallId':取字段(请求,'callId')},#工具调用 id
            'options':[#仅一次性允许/拒绝
                {'optionId':'allow-once','name':'Allow once','kind':'allow_once'},#允许一次
                {'optionId':'reject-once','name':'Reject','kind':'reject_once'},#拒绝一次
            ],#选项结束
        }))#请求结束
        结局=取字段(结果,'outcome')#客户端结果
        if 取字段(结局,'outcome')=='cancelled':#客户端取消
            return 'cancelled'#取消
        return 'allowed-once' if 取字段(结局,'optionId')=='allow-once' else 'rejected'#允许一次或拒绝

    上下文.on('approval/request',审批请求)#挂监听

    def 铸造方法表(连接):#铸造 ACP 智能体处理器表
        """记下连接，供 notify 与权限请求使用。"""
        连接盒['conn']=连接#记下连接
        def 初始化(_参数):#握手
            """单版本智能体。"""
            return {#初始化响应
                'protocolVersion':协议版本,#本服务器协议版本
                'agentInfo':{'name':'deepseek-harness-acp','version':'0.0.1'},#智能体名与版本
                'agentCapabilities':{#能力声明
                    'promptCapabilities':{'image':False,'audio':False,'embeddedContext':False},#基线
                },#能力结束
                'authMethods':[],#无认证方法
            }#响应结束
        def 认证(_参数):#认证入口
            """空操作成功。"""
            return None#成功
        def 新建会话(参数):#新建 harness 会话
            """以绝对路径作为主 cwd 创建新 agent。"""
            断言开放()#已拆除则拒绝
            校验会话参数(参数)#拒绝自动化约定外的会话特性
            会话号=会话标识(str(uuid.uuid4()))#铸造新会话 id
            句柄=解开(智能体们.创建({#创建桥接拥有的智能体
                'sessionId':会话号,#使用刚铸造的会话 id
                'meta':{'cwd':取字段(参数,'cwd')},#工作目录写入会话元数据
                'agentOptions':智能体选项(配置值),#仅填入已配置的提供方/模型
            }))#create 结束
            if 已关闭标志['v']:#创建期间连接已关
                解开(句柄.拆除())#丢掉刚创建的智能体
                raise 内部错误('connection closed during session/new')#报告创建期间关闭
            def 拆本会话():#精确拥有拆除
                """拆除本句柄。"""
                return 句柄.拆除()#委托
            会话表[会话号]={#登记桥接记录
                'agent':句柄.智能体,#拥有的智能体
                'dispose':拆本会话,#精确拥有拆除
                'inflight':None,#尚无进行中提示
            }#记录结束
            return {'sessionId':会话号}#把会话 id 交给客户端
        def 提示(参数):#投递提示并等待停止原因
            """每个会话只允许一个正在处理的请求。"""
            断言开放()#已拆除则拒绝
            记录=要求会话(会话标识(取字段(参数,'sessionId')))#取本桥接会话
            if 记录.get('inflight') is not None:#已有进行中提示
                raise 非法参数('a prompt is already in flight for this session')#同时只允许一条
            提示块=取字段(参数,'prompt') or []#提示块
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
            try:#后续可能同步抛
                记录['agent'].后续(消息)#投递到智能体收件箱
            except BaseException as 错误:#同步投递失败
                记录['inflight']=None#释放槽位
                raise 内部错误('prompt was not queued: '+str(错误))#报告未能入队
            def 空闲结算():#空闲后结算本槽
                """关联的 turn/end 武装 endReason；无回合的槽保持 cancelled。"""
                try:#等待空闲
                    解开(记录['agent'].等到空闲())#整智能体空闲
                except BaseException:#空闲等待失败仍尝试结算
                    pass#继续结算
                if 记录.get('inflight') is not 飞行:#已被错误路径或取消结算
                    return#忽略
                记录['inflight']=None#清槽
                结束=飞行.get('endReason')#关联回合结束原因
                if 结束 is None:#从未记下结束（提示被丢弃）
                    飞行['resolve']('cancelled')#报告已取消
                elif 取字段(结束,'kind')=='max-tokens':#max-tokens 仍报 end_turn
                    飞行['resolve']('end_turn')#end_turn
                else:#其它
                    飞行['resolve'](回合结束到停止原因(结束))#映射
            threading.Thread(target=空闲结算,daemon=True).start()#后台等空闲
            return {'stopReason':解开(等待)}#ACP 提示响应
        def 取消(参数):#客户端取消
            """未知 id 为空操作。"""
            记录=会话表.get(会话标识(取字段(参数,'sessionId')))#按 id 查找
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

    def 铸造包装(连接):#铸造并包成属性对象
        """记下连接后返回代理。"""
        return 智能体代理(铸造方法表(连接))#代理

    流覆盖=取字段(配置值,'stream')#可选测试传输
    if 流覆盖 is None:#生产 stdio
        流=创建NDJSON流(sys.stdout,sys.stdin)#stdout 出、stdin 入
    else:#测试覆盖
        流=流覆盖#注入流
    连接=智能体侧连接(铸造包装,流)#打开智能体侧连接
    连接盒['conn']=连接#确保已赋值

    def 静止():#关闭桥接并拆除全部会话
        """客户端断开与 Cordis 释放共用同一个记忆化清理流程。"""
        if 静止盒['task'] is not None:#已在静止
            return 静止盒['task']#复用
        已关闭标志['v']=True#拒绝新会话与提示
        记录们=list(会话表.values())#快照全部记录
        会话表.clear()#先清空表
        for 记录 in 记录们:#取消每个会话
            记录['agent'].取消({'kind':'user'})#用户取消
            结算提示(记录,'cancelled')#进行中提示报告 cancelled
        def 跑静止():#拆除：先后代再顶层
            """子先序抽干可续跑后代，再拆除顶层。"""
            子智能体=上下文.get('subagents')#可选子智能体服务
            if 子智能体 is not None and hasattr(子智能体,'drainContinuableDescendants'):#存在则可抽干
                try:#拆除失败只记日志
                    解开(子智能体.drainContinuableDescendants([记录['agent'] for 记录 in 记录们]))#子先序抽干
                except BaseException as 错误:#后代拆除失败
                    日志器.warn('acp: continuable subagent teardown failed: '+str(错误))#不阻断顶层拆除
            失败们=[]#收集拆除失败
            for 记录 in 记录们:#逐条拆除顶层
                try:#dispose
                    解开(记录['dispose']())#精确拥有拆除
                except BaseException as 错误:#记下
                    失败们.append(错误)#原因
            if len(失败们)>0:#有会话拆除失败
                细节='; '.join(错误链(失败) for 失败 in 失败们)#拼错误链
                raise 聚合错误(失败们,'ACP agent teardown failed for '+str(len(失败们))+' session(s): '+细节)#聚合
        静止盒['task']=已兑现(跑静止())#立即启动
        return 静止盒['task']#把同一承诺交给调用方

    def 连接关闭后():#连接关闭后静止
        """无论成败都拆除会话。"""
        try:#等待关闭
            解开(连接.已关闭承诺)#关闭边沿
        except BaseException as 错误:#传输带错关闭
            日志器.warn('acp: connection closed with an error: '+str(错误))#记日志后仍静止
        try:#静止
            解开(静止())#拆除会话
        except BaseException as 错误:#拆除本身失败
            日志器.warn('acp: connection-close teardown failed: '+str(错误))#记日志
    threading.Thread(target=连接关闭后,daemon=True).start()#后台盯关闭

    def 生命周期():#插件拆除时静止连接
        """返回拆除函数。"""
        def 拆除():#静止
            """记忆化清理。"""
            解开(静止())#静止
        return 拆除#拆除器
    上下文.effect(生命周期,'acp.connection')#effect 名
