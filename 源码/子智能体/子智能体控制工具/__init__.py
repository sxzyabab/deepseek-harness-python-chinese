"""全局命名的 `send_message` 与 `interrupt_agent` 工具：`ctx.subagents.跟进()` 与 `ctx.subagents.打断()` 上的薄面向模型适配器。它们自己不做生命周期路由——驻留、冷恢复与中断授权属于子智能体服务——并且与绑定提供方的 `@deepseek-ai/dsh-tool-subagent` 实例分开，以便多个委托工具共享一套控制 API。

对齐上游 `tool-subagent-control/src/index.ts`。可单独加载的发现工具见 `.列举智能体`；本包空不变量配套见 `.不变量`。公开面仅中文名。
"""
from tools import 定义工具#导入工具定义
from session import 会话标识#导入会话id品牌
from cordis.工具 import 已兑现,是否thenable#立刻兑现与可等待判定

名称='tool-subagent-control'#Cordis插件名
注入=['tools','subagents']#依赖工具与子智能体服务
name=名称#Cordis插件名（协议槽）
inject=注入#Cordis依赖声明（协议槽）

__all__=['名称','注入','应用','默认','取字段','解开']#仅中文公开名

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段；映射优先于属性。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 解开(值):#承诺则等待否则原样
    """承诺则等待，否则原样返回。"""
    if 是否thenable(值):#可等待
        return 值.等待()#等待承诺
    return 值#同步值

def 应用(上下文):#登记 send_message 与 interrupt_agent
    """登记 `send_message` 与 `interrupt_agent` 工具。"""
    def 渲染投递(参数,_值):#渲染投递确认
        """渲染投递确认文本块。"""
        return [{'type':'text','text':'message queued as the next turn for subagent '+取字段(参数,'subagent_id')}]#确认文案（字面量不译）
    def 执行投递(参数,执行元数据):#执行投递
        """把 message 包成文本块并向子体跟进投递；返回已接受的 messageId。"""
        父=取字段(执行元数据,'agent')#调用方智能体
        if not 父:#无活调用方
            # 父权威要求精确的活调用智能体。
            raise Exception('send_message requires a calling agent (exec.agent was undefined)')#拒绝
        内容=[{'type':'text','text':取字段(参数,'message')}]#包成文本块
        消息标识=解开(上下文.subagents.跟进(#投递后续消息
            父,#父权威
            会话标识(取字段(参数,'subagent_id')),#目标子id
            内容,#正文
            {#投递选项
                'source':{'kind':'coordinator','form':'relay','senderSessionId':取字段(父,'id')},#协调方中继
                'signal':取字段(执行元数据,'signal'),#取消信号
            },#选项结束
        ))#跟进结束
        return 已兑现({'messageId':消息标识})#返回消息id
    上下文.tools.register(定义工具({#登记 send_message
        'name':'send_message',#工具名（协议字面量不译）
        'description':(#工具描述（字面量不译）
            'Send a message to a background subagent by its subagent id, continuing the same conversation. It '
            +'becomes the subagent\'s next turn: if it is still working, the message waits until its current turn '
            +'finishes, so it cannot redirect work already underway. This call returns no answer from the '
            +'subagent — only confirmation that the message was delivered — so use it to give it more work. A '
            +'failure means the message was NOT delivered.'
        ),#描述结束
        'parameters':{#参数模式
            'subagent_id':{#目标子id
                'type':'string',#字符串
                'required':True,#必填
                'description':'The subagent id returned when the background subagent was started.',#参数说明（字面量不译）
            },#subagent_id 结束
            'message':{#投递正文
                'type':'string',#字符串
                'required':True,#必填
                'description':'The message to deliver to the subagent.',#参数说明（字面量不译）
            },#message 结束
        },#parameters 结束
        'output':{#成功返回
            'schema':{#返回模式
                'type':'object',#对象
                'additionalProperties':False,#禁止额外字段
                'properties':{#字段
                    'messageId':{'type':'string','required':True},#投递消息id
                },#properties 结束
            },#schema 结束
            'render':渲染投递,#渲染投递确认
        },#output 结束
        'execute':执行投递,#执行投递
    }))#send_message 登记结束
    def 渲染打断(参数,_值):#渲染中断确认
        """渲染中断确认文本块。"""
        return [{'type':'text','text':'interrupt requested for agent '+取字段(参数,'agent_id')}]#确认文案（字面量不译）
    def 执行打断(参数,执行元数据):#执行中断
        """在祖先权威下请求打断目标当前回合；立即返回 accepted。"""
        调用方=取字段(执行元数据,'agent')#调用方智能体
        if not 调用方:#无活调用方
            # 祖先权威要求精确的活调用智能体。
            raise Exception('interrupt_agent requires a calling agent (exec.agent was undefined)')#拒绝
        # 服务用目标记下的谱系授权精确的活调用方；工具自己不加权威。
        上下文.subagents.打断(会话标识(取字段(参数,'agent_id')),{'kind':'ancestor','agent':调用方})#请求中断
        return 已兑现({'accepted':True})#立即接受
    上下文.tools.register(定义工具({#登记 interrupt_agent
        'name':'interrupt_agent',#工具名（协议字面量不译）
        'description':(#工具描述（字面量不译）
            'Request cancellation of a background agent\'s current turn by its agent id. The target may be your '
            +'direct child or a deeper agent created under you. Only the current turn stops: messages already '
            +'queued for the agent stay parked until a later send_message, agents it started keep running, and '
            +'the agent itself stays available for follow-ups. This call returns as soon as the stop request is '
            +'accepted, so the target may keep running briefly; interrupting an agent that already finished is '
            +'an accepted no-op.'
        ),#描述结束
        'parameters':{#参数模式
            'agent_id':{#目标智能体id
                'type':'string',#字符串
                'required':True,#必填
                'description':'The agent id of the running agent to interrupt.',#参数说明（字面量不译）
            },#agent_id 结束
        },#parameters 结束
        'output':{#成功返回
            'schema':{#返回模式
                'type':'object',#对象
                'additionalProperties':False,#禁止额外字段
                'properties':{#字段
                    'accepted':{'type':'boolean','required':True},#是否已接受
                },#properties 结束
            },#schema 结束
            'render':渲染打断,#渲染中断确认
        },#output 结束
        'execute':执行打断,#执行中断
    }))#interrupt_agent 登记结束

apply=应用#Cordis插件入口（协议槽）
默认=应用#中文默认导出
default=应用#Cordis默认导出（协议槽）
