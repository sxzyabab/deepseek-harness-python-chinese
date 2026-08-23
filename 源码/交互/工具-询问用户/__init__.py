"""`ctx.userQuestions` 能力缝的面向模型消费方。该工具暂停，直到 UI 提供方返回人类答案，再把那份答案作为普通工具结果喂回智能体循环。

对齐上游 `tool-ask-user/src/index.ts`。公开面仅中文名；本包空不变量配套见 `.不变量`。
"""
import json#把结果收成紧凑 JSON 文本
from ..工具 import 定义工具#定义面向模型的工具
from ...依赖 import cordis#外部依赖胶水
已兑现=cordis.工具.已兑现#立刻兑现
是否thenable=cordis.工具.是否thenable#可等待判定

名称='tool-ask-user'#Cordis插件名
注入=['tools','userQuestions']#依赖工具注册表与提问服务
name=名称#Cordis插件名（协议槽）
inject=注入#Cordis依赖声明（协议槽）
描述=('Ask the user a concise question when you need confirmation, a choice, or missing information before proceeding. '#面向模型说明前段（字面量不译）
    +'Send one or more questions, each with a stable id that will be echoed in the answer.')#面向模型说明后段（字面量不译）

__all__=['名称','注入','描述','应用','默认','取字段','解开']#仅中文公开名

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

def 应用(上下文):#登记 ask_user_question 工具
    """向工具注册表登记 `ask_user_question`。"""
    def 渲染(_参数,值):#把结果收成文本块
        """把结构化结果渲染成一条紧凑 JSON 文本块。"""
        return [{'type':'text','text':json.dumps(值,ensure_ascii=False,separators=(',',':'))}]#单个文本块
    def 执行(参数,执行上下文):#暂停直到人类作答
        """把模型参数映射为提问缝请求，等待人类作答，再归一化工具结果。"""
        问题们=[]#缝请求里的问题列表
        for 题目 in 取字段(参数,'questions'):#模型参数逐题映射
            条={'id':取字段(题目,'id'),'question':取字段(题目,'question')}#必填 id 与正文
            标题=取字段(题目,'header')#可选标题
            if 标题 is not None:#有标题
                条['header']=标题#带上标题
            选项=取字段(题目,'options')#可选选项
            if 选项 is not None:#有选项
                条['options']=选项#带上选项
            多选=取字段(题目,'multi_select')#蛇形多选标志
            if 多选 is not None:#有多选标志
                条['multiSelect']=多选#蛇形转驼峰
            问题们.append(条)#收下映射后的题
        请求={'questions':问题们,'signal':取字段(执行上下文,'signal')}#问题与取消信号
        智能体=取字段(执行上下文,'agent')#调用智能体
        if 智能体 is not None:#有所属智能体
            请求['agent']=智能体#带上调用智能体
        结果=解开(上下文.userQuestions.ask(请求))#交给提问能力缝
        答案们=[]#归一化答案
        for 答案 in 取字段(结果,'answers'):#逐条拷贝以免共享可变数组
            项={'id':取字段(答案,'id'),'selected':list(取字段(答案,'selected'))}#id 与选中列表拷贝
            自定义=取字段(答案,'custom')#可选自定义文本
            if 自定义 is not None:#有自定义
                项['custom']=自定义#带上自定义
            答案们.append(项)#收下答案
        return 已兑现({'answers':答案们})#结构化工具结果
    提问工具=定义工具({#面向模型的 ask_user_question
        'name':'ask_user_question',#工具名（协议字面量不译）
        'description':描述,#面向模型说明
        'parameters':{#参数模式
            'questions':{#问题数组
                'type':'array',#数组
                'required':True,#必填
                'description':'Questions to ask the user before continuing.',#问题列表说明（字面量不译）
                'items':{#单题对象
                    'type':'object',#对象
                    'additionalProperties':True,#允许额外字段
                    'properties':{#题目字段
                        'id':{'type':'string','required':True,'description':'Stable id for this question; echoed in the answer.'},#稳定问题 id（字面量不译）
                        'question':{'type':'string','required':True,'description':'The specific question to ask the user.'},#问题正文（字面量不译）
                        'header':{#可选标题
                            'type':'string',#字符串
                            'description':'Optional short heading for the question, such as "Confirm" or "Choose Mode".',#标题说明（字面量不译）
                        },#header 结束
                        'options':{#可选选项
                            'type':'array',#数组
                            'description':'Optional choices to show the user. If you recommend one, put it first and append "(Recommended)" to that label.',#选项说明（字面量不译）
                            'items':{#单个选项
                                'type':'object',#对象
                                'additionalProperties':True,#允许额外字段
                                'properties':{#选项字段
                                    'label':{'type':'string','required':True,'description':'Short user-facing option label.'},#选项标签（字面量不译）
                                    'description':{'type':'string','description':'One sentence explaining the tradeoff or impact.'},#选项说明（字面量不译）
                                },#选项 properties 结束
                            },#选项 items 结束
                        },#options 结束
                        'multi_select':{#是否多选
                            'type':'boolean',#布尔
                            'description':'Whether the user may select more than one option. Defaults to false.',#多选说明（字面量不译）
                        },#multi_select 结束
                    },#题目 properties 结束
                },#题目 items 结束
            },#questions 结束
        },#parameters 结束
        'output':{#输出模式
            'schema':{#结果 JSON 模式
                'type':'object',#对象
                'additionalProperties':False,#禁止额外字段
                'properties':{#结果字段
                    'answers':{#答案数组
                        'type':'array',#数组
                        'required':True,#必填
                        'items':{#单条答案
                            'type':'object',#对象
                            'additionalProperties':False,#禁止额外字段
                            'properties':{#答案字段
                                'id':{'type':'string','required':True},#问题 id
                                'selected':{'type':'array','required':True,'items':{'type':'string'}},#选中标签
                                'custom':{'type':'string'},#可选自定义文本
                            },#答案 properties 结束
                        },#答案 items 结束
                    },#answers 结束
                },#结果 properties 结束
            },#schema 结束
            'render':渲染,#把结果收成文本块
        },#output 结束
        'execute':执行,#暂停直到人类作答
    })#定义结束
    上下文.tools.登记(提问工具)#挂到工具注册表

apply=应用#Cordis插件入口（协议槽）
默认=应用#中文默认导出
default=应用#Cordis默认导出（协议槽）
