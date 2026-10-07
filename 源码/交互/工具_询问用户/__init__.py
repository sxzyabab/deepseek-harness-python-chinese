'面向模型的 ask_user_question，停在 ctx.userQuestions 上等人回答'
import json#结果渲染
from ...内核.工具 import 定义工具#定义面向模型的工具
from ..用户提问 import 询问用户问题请求#缝要的请求对象

__all__=['名称','依赖','应用']#仅中文公开名

名称='tool-ask-user'#插件名
依赖=['tools','userQuestions']#工具注册表与提问缝
描述='Ask the user a concise question when you need confirmation, a choice, or missing information before proceeding.'#面向模型的描述，字面量不译

def 应用(上下文,配置值=None):#登记工具
    '把人类答案当作普通工具结果送回循环'
    def 渲染(_参数,值):#模型看到 JSON
        '整份答案编成一条文本'
        return [{'type':'text','text':json.dumps(值,ensure_ascii=False)}]#文本块
    def 执行(参数,执行上下文):#向缝提问
        'header、options、multi_select 缺席就不传'
        问题=[]#缝要的问题
        for 题目 in 参数['questions']:#逐题
            一条={'id':题目['id'],'question':题目['question']}#必填
            if 'header' in 题目 and 题目['header'] is not None:#有标题
                一条['header']=题目['header']#标题
            if 'options' in 题目 and 题目['options'] is not None:#有选项
                一条['options']=题目['options']#选项
            if 'multi_select' in 题目 and 题目['multi_select'] is not None:#有多选
                一条['multiSelect']=题目['multi_select']#缝用驼峰
            问题.append(一条)#收下
        智能体=执行上下文['agent'] if 'agent' in 执行上下文 else None#调用智能体
        信号=执行上下文['signal'] if 'signal' in 执行上下文 else None#中止信号
        结果=上下文.userQuestions.ask(询问用户问题请求(问题,智能体,信号))#等人回答
        答案=[]#回给模型
        for 项 in 结果['answers']:#逐条
            一条={'id':项['id'],'selected':list(项['selected'])}#必填
            if 'custom' in 项 and 项['custom'] is not None:#有自由文本
                一条['custom']=项['custom']#带上
            答案.append(一条)#收下
        return {'answers':答案}#结构化结果
    上下文.tools.登记(定义工具({#面向模型的工具
        'name':'ask_user_question',#工具名
        'description':描述,#描述
        'parameters':{#参数
            'questions':{#问题列表
                'type':'array',#数组
                'required':True,#必填
                'description':'Questions to ask the user before continuing.',#说明
                'items':{#一条
                    'type':'object',#对象
                    'additionalProperties':True,#允许额外字段
                    'properties':{#字段
                        'id':{'type':'string','required':True,'description':'Stable id for this question; echoed in the answer.'},#稳定 id
                        'question':{'type':'string','required':True,'description':'The specific question to ask the user.'},#问题
                        'header':{'type':'string','description':'Optional short heading for the question, such as "Confirm" or "Choose Mode".'},#短标题
                        'options':{#选项
                            'type':'array',#数组
                            'description':'Optional choices to show the user. If you recommend one, put it first and append "(Recommended)" to that label.',#说明
                            'items':{#一条选项
                                'type':'object',#对象
                                'additionalProperties':True,#允许额外字段
                                'properties':{#字段
                                    'label':{'type':'string','required':True,'description':'Short user-facing option label.'},#标签
                                    'description':{'type':'string','description':'One sentence explaining the tradeoff or impact.'},#一句说明
                                },#字段结束
                            },#选项结束
                        },#options 结束
                        'multi_select':{'type':'boolean','description':'Whether the user may select more than one option. Defaults to false.'},#多选
                    },#字段结束
                },#一条结束
            },#questions 结束
        },#参数结束
        'output':{#输出
            'schema':{#模式
                'type':'object',#对象
                'additionalProperties':False,#禁止额外字段
                'properties':{#字段
                    'answers':{#答案
                        'type':'array',#数组
                        'required':True,#必填
                        'items':{#一条
                            'type':'object',#对象
                            'additionalProperties':False,#禁止额外字段
                            'properties':{#字段
                                'id':{'type':'string','required':True},#问题 id
                                'selected':{'type':'array','required':True,'items':{'type':'string'}},#选中标签
                                'custom':{'type':'string'},#自由文本
                            },#字段结束
                        },#一条结束
                    },#answers 结束
                },#字段结束
            },#模式结束
            'render':渲染,#文本
        },#输出结束
        'execute':执行,#提问
    }))#登记结束

name=名称#框架槽
inject=依赖#框架槽
apply=应用#框架槽
