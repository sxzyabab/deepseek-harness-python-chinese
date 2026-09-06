"""全局命名的 `send_message` 与 `interrupt_agent` 工具：`ctx.subagents.跟进()` 与 `ctx.subagents.打断()` 上的薄面向模型适配器。它们自己不做生命周期路由——驻留、冷恢复与中断授权属于子智能体服务——并且与绑定提供方的 `@deepseek-ai/dsh-tool-subagent` 实例分开，以便多个委托工具共享一套控制 API。

对齐上游 `tool-subagent-control/src/index.ts`。可单独加载的发现工具见 `.列举智能体`；本包空不变量配套见 `.不变量`。公开面仅中文名。
"""
from ...内核.工具 import 定义工具#导入工具定义
from ...内核.会话 import 会话标识#导入会话id品牌
from ..子智能体.错误 import 子智能体错误#缝内失败

名称='tool-subagent-control'#Cordis插件名
注入=['tools','subagents']#依赖工具与子智能体服务

__all__=['名称','注入','应用']#仅中文公开名

def 应用(上下文):
    """登记 `send_message` 与 `interrupt_agent` 工具。"""
    def 渲染投递(参数,_值):
        """渲染投递确认文本块。参数为 dict。"""
        return [{'type':'text','text':'message queued as the next turn for subagent '+参数['subagent_id']}]#确认文案
    def 执行投递(参数,执行元数据):
        """把 message 包成文本块并向子体跟进投递；返回已接受的 messageId。参数与执行为 dict；父为智能体对象。"""
        if 'agent' not in 执行元数据 or 执行元数据['agent'] is None:#无活调用方
            raise 子智能体错误('send_message requires a calling agent (exec.agent was undefined)','NO_AGENT')#拒绝
        父=执行元数据['agent']#调用方智能体
        内容=[{'type':'text','text':参数['message']}]#包成文本块
        选项={'source':{'kind':'coordinator','form':'relay','senderSessionId':父.id}}#投递选项
        if 'signal' in 执行元数据:#有取消信号
            选项['signal']=执行元数据['signal']#写入
        消息标识=上下文.subagents.跟进(#投递后续消息
            父,#父权威
            会话标识(参数['subagent_id']),#目标子id
            内容,#正文
            选项,#选项
        )#跟进结束
        return {'messageId':消息标识}#返回消息id
    上下文.tools.登记(定义工具({#登记 send_message
        'name':'send_message',#工具名
        'description':(#工具描述
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
                'description':'The subagent id returned when the background subagent was started.',#参数说明
            },#subagent_id 结束
            'message':{#投递正文
                'type':'string',#字符串
                'required':True,#必填
                'description':'The message to deliver to the subagent.',#参数说明
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
    def 渲染打断(参数,_值):
        """渲染中断确认文本块。参数为 dict。"""
        return [{'type':'text','text':'interrupt requested for agent '+参数['agent_id']}]#确认文案
    def 执行打断(参数,执行元数据):
        """在祖先权威下请求打断目标当前回合；立即返回 accepted。参数与执行为 dict；调用方为智能体对象。"""
        if 'agent' not in 执行元数据 or 执行元数据['agent'] is None:#无活调用方
            raise 子智能体错误('interrupt_agent requires a calling agent (exec.agent was undefined)','NO_AGENT')#拒绝
        调用方=执行元数据['agent']#调用方智能体
        上下文.subagents.打断(会话标识(参数['agent_id']),{'kind':'ancestor','agent':调用方})#请求中断
        return {'accepted':True}#立即接受
    上下文.tools.登记(定义工具({#登记 interrupt_agent
        'name':'interrupt_agent',#工具名
        'description':(#工具描述
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
                'description':'The agent id of the running agent to interrupt.',#参数说明
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

name=名称#框架槽
inject=注入#框架槽
apply=应用#框架槽
default=应用#框架槽
