from ...内核.工具 import 定义工具#导入工具定义
from ...内核.会话 import 会话标识#导入会话id品牌
from ..子智能体.错误 import 子智能体错误#缝内失败

名称='tool-subagent-control'#Cordis插件名
依赖=['tools','subagents']#依赖工具与子智能体服务

__all__=['名称','依赖','应用']#仅中文公开名

def 应用(上下文):
    """登记 `send_message` 与 `interrupt_agent` 工具。"""
    def 渲染投递(参数,_值):
        """渲染投递确认文本块。参数为 dict。"""
        return [{'type':'text','text':'message delivered to agent '+参数['agent_id']}]#确认文案
    def 执行投递(参数,执行元数据):
        """把 message 包成文本块并经相邻投递；返回已接受的 messageId。"""
        if 'agent' not in 执行元数据 or 执行元数据['agent'] is None:#无活调用方
            raise 子智能体错误('send_message requires a calling agent (exec.agent was undefined)','NO_AGENT')#拒绝
        发送方=执行元数据['agent']#调用方智能体
        内容=[{'type':'text','text':参数['message']}]#包成文本块
        选项={}
        if 'signal' in 执行元数据:#有取消信号
            选项['signal']=执行元数据['signal']#写入
        消息标识=上下文.subagents.发送消息(
            发送方,
            会话标识(参数['agent_id']),
            内容,
            选项,
        )
        return {'messageId':消息标识}#返回消息id
    上下文.tools.登记(定义工具({#登记 send_message
        'name':'send_message',#工具名
        'description':(#工具描述
            'Send a message to a direct continuable child by its agent id. If you are a resident continuable child, '
            +'you may also target your direct parent. If the target is still working, the message steers its nearest step; '
            +'if it is inactive, the message starts or resumes a turn. This call returns no answer from the agent — only confirmation '
            +'that the message was delivered. A failure means the message was NOT delivered.'
        ),#描述结束
        'parameters':{#参数模式
            'agent_id':{#目标 id
                'type':'string',#字符串
                'required':True,#必填
                'description':'The agent id of your direct continuable child, or your direct parent when you are a resident continuable child.',#参数说明
            },#agent_id 结束
            'message':{#投递正文
                'type':'string',#字符串
                'required':True,#必填
                'description':'The message to deliver to the agent.',#参数说明
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
inject=依赖#框架槽
apply=应用#框架槽
default=应用#框架槽
