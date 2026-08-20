"""子体作用域内的 report 工具及其用法指引，安装进每个可续跑进程内子体的未发布上下文。根、一次性子体、远程提供方、以及无智能体执行永远看不见这次登记。对齐上游 `@deepseek-ai/dsh-tool-subagent-report`（packages/subagent/tool-subagent-report）。"""
from schemastery import 模式#导入配置模式
from tools import 定义工具#定义面向模型的工具
from cordis import 聚合错误#多失败聚合（登记失败回滚与成对拆除）
from cordis.工具 import 已兑现,是否thenable#立刻兑现与可等待判定

名称='tool-subagent-report'#Cordis插件名（字面量不译）
# 贡献只通过 childCtx.tools 与 childCtx.systemPrompt 登记，但声明这两个服务让 Loader 排序在加载时失败，而不是等到下一次子体物化。
注入=['subagents','tools','systemPrompt']#依赖子智能体、工具与系统提示词
name=名称#Cordis插件名槽
inject=注入#Cordis依赖声明槽
报告段落顺序=117#指引顺序：排在可续跑子体可携带的每个按工具段落之后
配置=模式.对象({#已接受的报告如何在父上调度；Loader 与直接 apply 都经此落实默认值
    'reportDelivery':模式.联合([模式.常量('quiet'),模式.常量('wakeup')]).默认('wakeup'),#默认唤醒父；quiet 只注入上下文
})#配置模式结束
Config=配置#Cordis配置模式槽
段落文案=(#模型可见用法（字面量不译）
    'Deliver your result with the report tool before you finish: call it once with a self-contained '
    +'answer. The agent that started you shares your workspace but does not automatically receive your '
    +'transcript, tool output, or reasoning, so a closing remark such as "done" leaves it nothing it can '
    +'use. Report earlier as well whenever a partial finding changes what that agent should do next; '
    +'reporting never ends your turn.'
)#段落文案结束
工具描述=(#工具描述（字面量不译）
    'Report selected content to the agent that started you. Call this once before you finish, with a '
    +'self-contained final result, and earlier for progress or findings that change what that agent does '
    +'next. That agent shares your workspace but does not automatically receive your transcript, tool '
    +'output, or reasoning, so finishing your work is not itself a result. Reporting does not end your '
    +'turn or finish your work, and only your direct parent receives it. A failed call may still have '
    +'arrived, so do not blindly repeat it.'
)#工具描述结束
参数说明='Actionable content for your parent; summarize conclusions and reference relevant shared paths.'#output 参数说明（字面量不译）

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段；缺席时返回缺省。"""
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

def 安装报告工具(子上下文,服务上下文,投递):#安装 report 工具与指引
    """把 report 及其用法指引安装进一个可续跑子体的作用域。两次登记都由该作用域拥有，因此对子体的父与兄弟不可见。返回同时撤销两者的唯一拆除器。"""
    拆除段落=子上下文.systemPrompt.section({#登记用法指引段落
        'name':'tool:report',#段落名（字面量不译）
        'order':报告段落顺序,#排在各工具段落后
        'text':段落文案,#模型可见用法
    })#section 结束
    拆除工具=None#工具拆除；登记成功后赋值，失败路径保持 None
    try:#登记工具；失败则回滚已登记的指引段落
        def 渲染(_参数,值):#渲染接受确认
            """渲染接受确认文本块；正文为模型可见字面量。"""
            return [{'type':'text','text':'report accepted by the agent that started you as message '+取字段(值,'messageId')}]#确认文案（字面量不译）
        def 执行(参数,执行元数据):#执行投递
            """把 output 包成文本块，经 ctx.subagents.自报告 向直接父投递；成功返回父侧 messageId。"""
            内容=[{'type':'text','text':取字段(参数,'output')}]#把 output 包成文本块
            # 作用域内解析保证有 Agent。服务仍在权威边界核对其精确的活 Activation 身份。
            消息标识=解开(服务上下文.subagents.自报告(取字段(执行元数据,'agent'),内容,{#向父投递
                'delivery':投递,#部署调度策略（quiet|wakeup）
                'signal':取字段(执行元数据,'signal'),#取消信号：授权与准入直到接受
            }))#自报告结束
            return 已兑现({'messageId':消息标识})#返回父侧消息 id
        拆除工具=子上下文.tools.register(定义工具({#登记 report 工具
            'name':'report',#工具名（字面量不译）
            'description':工具描述,#工具描述
            'parameters':{#参数模式
                'output':{#父可见内容
                    'type':'string',#字符串
                    'required':True,#必填
                    'description':参数说明,#参数说明
                },#output 结束
            },#parameters 结束
            'output':{#成功返回
                'schema':{#返回模式
                    'type':'object',#对象
                    'additionalProperties':False,#禁止额外字段
                    'properties':{#字段
                        'messageId':{'type':'string','required':True},#父侧消息 id
                    },#properties 结束
                },#schema 结束
                'render':渲染,#渲染接受确认
            },#output 结束
            'execute':执行,#执行投递
        }))#defineTool 与 register 结束
    except Exception as 错误:#工具登记失败
        try:#回滚已登记的指引
            拆除段落()#拆除段落
        except Exception as 回滚错误:#回滚也失败
            raise 聚合错误([错误,回滚错误],'failed to register the report tool and roll back its prompt guidance')#合并两次失败
        raise 错误#抛出原登记错误
    def 成对拆除():#先工具后段落
        """先尝试两次子登记、再报告清理失败的拆除器；任一侧失败都汇总进聚合错误。"""
        失败们=[]#收集拆除失败
        for 拆除 in (拆除工具,拆除段落):#先工具后段落
            try:#单次拆除
                拆除()#调用拆除
            except Exception as 错误:#单次拆除失败
                失败们.append(错误)#记下失败
        if len(失败们)>0:#有拆除失败
            raise 聚合错误(失败们,'failed to revoke report tool and prompt registrations')#合并抛出
    return 成对拆除#成对拆除器

def 应用(上下文,配置值=None):#登记可续跑子体贡献
    """登记可续跑子体贡献：每个可续跑子体安装 report 工具与指引。配置经 schemastery 落实默认投递策略。"""
    if 配置值 is None:#缺省空配置
        配置值={}#空配置
    # Config() 在运行时落实 schema 默认；schemastery 返回类型仍保留输入的可选形态。
    已落实=配置(配置值)#落实 reportDelivery 默认 wakeup
    投递=取字段(已落实,'reportDelivery')#读投递策略
    if 投递 is None:#未给出（防御：模式未物化时）
        投递='wakeup'#默认唤醒
    def 安装到子体(子上下文):#每个可续跑子体安装 report
        """把本部署的投递策略盖到子作用域上。"""
        return 安装报告工具(子上下文,上下文,投递)#安装工具与指引
    上下文.subagents.登记可续跑装配(安装到子体)#每个可续跑子体安装 report

apply=应用#Cordis插件入口槽
default=应用#默认导出槽
默认=应用#中文默认导出
