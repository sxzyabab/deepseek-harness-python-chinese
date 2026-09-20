"""面向模型的 get_goal、create_goal 和 update_goal 工具，叠在同会话持久目标域之上。"""
import json,math#紧凑 JSON 渲染与入口整数判定
from ...依赖 import cordis#外部依赖胶水
from ...依赖.schemastery import 整数字段#配置字段
from ..目标 import 目标标识#目标 id 品牌
from ...模型后端.llm import 装备错误,截上下文摘要,创建用户消息#策略错误、摘要与收尾消息
from ...内核.工具 import 定义工具#定义面向模型的工具
from .权限 import 目标工具执行,要求直接人类,完成权限#执行时权限
from .收尾 import 渲染收尾上下文#终态收尾指令

名称='tool-goal'#Cordis插件名
依赖=['agents','goals','tools','systemPrompt','sessionProjections']#依赖智能体、目标、工具、系统提示与会话投影
更新动作=('edit','pause','resume','complete','blocked')#update_goal 的 action 枚举
创建描述=(#create_goal 面向模型的说明
    'Create one persisted same-session completion goal when the current direct human request '#从人类请求推断长任务
    +'is a long-running objective that should continue across autonomous goal rounds. You may '#可跨自动轮次继续
    +'infer that intent without requiring the user to say "create a goal". Do not use this for '#不必用户亲口说创建
    +'trivial single-turn work. Execution rejects non-human and subagent authority.'#拒绝非人类与子智能体
)#创建描述结束
读取描述=(#get_goal 面向模型的说明
    'Read the current same-session goal, including its exact id/revision, objective, phase, completed '#读精确身份与阶段
    +'continuation rounds, round limit, blocker reason when present, and whether another continuation is armed. '#轮次、阻塞与武装
    +'Call this before updating a goal.'#更新前先读
)#读取描述结束
更新描述=(#update_goal 面向模型的说明
    'Update the exact current goal revision. edit, pause, and resume require a direct '#更新精确修订
    +'top-level human request. During an automatic continuation of the current goal, complete '#完成/阻塞也允许在当前轮
    +'and blocked are also allowed. blocked is rejected before the configured minimum round count; the model remains '#阻塞有轮次下限
    +'responsible for judging that the same condition persisted across those rounds and must explain it in blocked_reason.'#须解释具体条件
)#更新描述结束
目标值模式={#输出 JSON Schema
    'oneOf':[#空或有目标
        {#空目标
            'type':'object',#对象
            'additionalProperties':False,#不许多余键
            'properties':{#仅 goal: null
                'goal':{'type':'null','required':True},#空
            },#结束 properties
        },#结束空分支
        {#有目标
            'type':'object',#对象
            'additionalProperties':False,#不许多余键
            'properties':{#goal 加 activation
                'goal':{#快照对象
                    'type':'object',#对象
                    'additionalProperties':False,#不许多余键
                    'required':True,#必须有
                    'properties':{#快照字段
                        'id':{'type':'string','required':True},#id
                        'revision':{'type':'integer','required':True},#修订
                        'objective':{'type':'string','required':True},#陈述
                        'phase':{'type':'string','required':True,'enum':['active','paused','blocked','complete']},#阶段枚举
                        'roundsStarted':{'type':'integer','required':True},#已接纳轮次
                        'maxGoalRounds':{'type':'integer','required':True},#上限
                        'blockedReason':{#可选阻塞
                            'type':'object',#对象
                            'additionalProperties':False,#不许多余键
                            'properties':{#码与说明
                                'code':{'type':'string','required':True},#分类码
                                'message':{'type':'string','required':True},#说明
                            },#结束 properties
                        },#结束 blockedReason
                    },#结束 goal.properties
                },#结束 goal
                'activation':{'type':'string','required':True,'enum':['armed','disarmed']},#武装枚举
            },#结束 properties
        },#结束有目标分支
    ],#结束 oneOf
}#结束目标值模式
配置={#目标工具策略配置
    'blockedAfterConsecutiveRounds':整数字段(最小=1,默认值=3),#默认 3 轮
}#配置模式结束

安全整数上界=9007199254740991#JSON 入口安全整数上界

def 是正安全整数(值):
    """数据入口：正安全整数，排除布尔。"""
    if isinstance(值,bool):#布尔不是数字
        return False#否
    if isinstance(值,int):#整数
        return 值>=1 and 值<=安全整数上界#正且安全
    if isinstance(值,float) and 值.is_integer() and math.isfinite(值):#整值浮点
        return 值>=1 and 值<=安全整数上界#正且安全
    return False#其它

def 策略指导(阻塞轮次):
    """用部署选定的阻塞阈值渲染策略指导。"""
    return (#系统提示段落
        'Use goal tools for one long-running completion objective in the current session. '#只用于长任务
        +'create_goal may infer goal intent from a direct human request in any language; do not '#可从任意语言推断
        +'create a goal for routine single-turn work. Call get_goal before update_goal and copy its '#更新前先读
        +'exact goal_id and revision. After session resume or fork, an active goal is disarmed: when '#恢复后须再武装
        +'a human asks to continue or resume in any wording or language, use update_goal action '#人类要求继续则 resume
        +'resume to rearm it. Mark complete only when the objective is actually achieved. Mark '#完成须真正达成
        +'blocked only after the same blocking condition persists for at least '+str(阻塞轮次)+' '#阻塞有轮次下限
        +'consecutive goal rounds, and report that concrete condition in blocked_reason; difficulty, uncertainty, '#须写具体条件
        +'or useful remaining work is not blocked.'#困难不等于阻塞
    )#指导结束

def 解析配置(配置值):
    """解析阻塞阈值；非法则加载时失败。配置值是 dict。"""
    阻塞轮次=配置值['blockedAfterConsecutiveRounds'] if 'blockedAfterConsecutiveRounds' in 配置值 else 3#读配置
    if not 是正安全整数(阻塞轮次):#非正安全整数
        raise TypeError('blockedAfterConsecutiveRounds must be a positive safe integer')#加载时失败
    return {'blockedAfterConsecutiveRounds':int(阻塞轮次)}#已解析

def 有文本(值):
    """可选文本是否有意义，而不是严格模式的空填充。"""
    return 值 is not None and 值!=''#缺席或空串都不算

def 有轮次上限(值):
    """可选轮次上限是否有意义，而不是严格模式的零填充。"""
    return 值 is not None and 值!=0#缺席或 0 都不算

def 目标引用(标识,修订):
    """从模型参数构造精确比较交换引用。"""
    if len(标识)==0 or 标识!=标识.strip():#id 必须非空且已规范化
        raise 装备错误(#参数非法
            'goal_id must be non-empty and revision must be a positive safe integer',#人类可读
            'GOAL_TOOL_INVALID_UPDATE',#更新参数错误
        )#结束抛错
    if not 是正安全整数(修订):#修订必须是正安全整数
        raise 装备错误(#参数非法
            'goal_id must be non-empty and revision must be a positive safe integer',#人类可读
            'GOAL_TOOL_INVALID_UPDATE',#更新参数错误
        )#结束抛错
    return {'id':目标标识(标识),'revision':int(修订)}#打成品牌

def 目标工具值(目标):
    """稳定紧凑的模型结果；武装是观察值，不是回放状态。目标是 dict 快照或 None。"""
    if 目标 is None:#没有当前目标
        return {'goal':None}#空
    快照={#快照出站
        'id':目标['id'],#id 以字符串出
        'revision':目标['revision'],#修订
        'objective':目标['objective'],#陈述
        'phase':目标['phase'],#阶段
        'roundsStarted':目标['roundsStarted'],#已接纳轮次
        'maxGoalRounds':目标['maxGoalRounds'],#上限
    }#快照字段结束
    if 'blockedReason' in 目标 and 目标['blockedReason'] is not None:#仅阻塞带原因
        阻塞原因=目标['blockedReason']#原因 dict
        快照['blockedReason']={#码与说明
            'code':阻塞原因['code'],#分类码
            'message':阻塞原因['message'],#说明
        }#原因结束
    return {#有当前目标
        'goal':快照,#快照
        'activation':目标['activation'],#进程内武装
    }#有目标结束

def 渲染目标值(_参数,值):
    """把结构化结果渲染成紧凑 JSON 文本。"""
    return [{'type':'text','text':json.dumps(值,ensure_ascii=False,separators=(',',':'),allow_nan=False)}]#紧凑 JSON

目标输出={#三个目标控件共用的规范输出声明
    'schema':目标值模式,#JSON Schema
    'render':渲染目标值,#紧凑 JSON 文本
}#输出结束

def 呈现(标题,种类,原文=None):
    """目标工具共用的、只依赖 args 的挂起呈现。"""
    视图={'card':'generic','title':标题,'kind':种类}#通用卡片
    if 原文 is not None:#有原文
        视图['rawInput']=原文#可选原文
    return 视图#卡片结束

def 应用(上下文,配置值):
    """注册三个目标控件与共用策略段落。"""
    已解析=解析配置(配置值)#解析阈值
    阻塞阈值=已解析['blockedAfterConsecutiveRounds']#正数阈值
    上下文.systemPrompt.section({#策略段落
        'name':'tool:goal',#段落名
        'order':114,#排序
        'text':策略指导(阻塞阈值),#带阈值的指导
    })#结束段落
    def 执行读取(_参数,执行元数据):
        """认证调用方后返回当前视图或 null。"""
        执行=目标工具执行(上下文,执行元数据)#认证调用方
        return 目标工具值(上下文.goals.get(执行['agent']))#当前视图或 null
    def 呈现读取():
        """调用时读卡片。"""
        return 呈现('Read current goal','read')#读卡片
    上下文.tools.register(定义工具({#get_goal
        'name':'get_goal',#工具名
        'description':读取描述,#面向模型说明
        'parameters':{},#无参数
        'output':目标输出,#规范输出
        'execute':执行读取,#读当前目标
        'presentCall':呈现读取,#读卡片
    }))#结束 get_goal
    def 执行创建(参数,执行元数据):
        """必须是根智能体人类回合；走域创建后返回视图。参数是 dict。"""
        执行=目标工具执行(上下文,执行元数据)#认证调用方
        要求直接人类(上下文,执行)#必须是根智能体人类回合
        请求={'objective':参数['objective']}#陈述
        if 'max_goal_rounds' in 参数 and 参数['max_goal_rounds'] is not None:#有上限
            请求['maxGoalRounds']=参数['max_goal_rounds']#可选上限
        目标=上下文.goals.create(执行['agent'],请求)#走域创建
        return 目标工具值(目标)#创建后视图
    def 呈现创建(参数):
        """调用时创建卡片。参数是 dict。"""
        return 呈现('Create goal','other',参数['objective'] if 'objective' in 参数 else None)#用陈述作原文
    上下文.tools.register(定义工具({#create_goal
        'name':'create_goal',#工具名
        'description':创建描述,#面向模型说明
        'parameters':{#创建参数
            'objective':{#目标陈述
                'type':'string',#字符串
                'required':True,#必填
                'description':'The concrete completion objective inferred from the direct human request.',#从人类请求推断
            },#结束 objective
            'max_goal_rounds':{#可选上限
                'type':'number',#数字
                'description':'Optional positive safe-integer limit on automatic continuation rounds.',#自动轮次上限
            },#结束 max_goal_rounds
        },#结束 parameters
        'output':目标输出,#规范输出
        'execute':执行创建,#创建
        'presentCall':呈现创建,#用陈述作原文
    }))#结束 create_goal
    def 执行更新(参数,执行元数据):
        """按 action 分发 edit/pause/resume/complete/blocked。参数与执行元数据是 dict。"""
        执行=目标工具执行(上下文,执行元数据)#认证调用方
        引用=目标引用(参数['goal_id'],参数['revision'])#比较交换引用
        替换={}#edit 替换字段
        陈述=参数['objective'] if 'objective' in 参数 else None#可选陈述
        if 有文本(陈述):#非空陈述
            替换['objective']=陈述#写入替换
        上限=参数['max_goal_rounds'] if 'max_goal_rounds' in 参数 else None#可选上限
        if 有轮次上限(上限):#非零上限
            替换['maxGoalRounds']=上限#写入替换
        动作=参数['action']#动词
        阻塞原因文本=参数['blocked_reason'] if 'blocked_reason' in 参数 else None#可选阻塞原因
        if 动作=='edit':#编辑
            要求直接人类(上下文,执行)#必须人类回合
            if 有文本(阻塞原因文本):#编辑不得带阻塞原因
                raise 装备错误('blocked_reason is valid only with action blocked','GOAL_TOOL_INVALID_UPDATE')#字段用错
            目标=上下文.goals.edit(执行['agent'],引用,替换)#走域编辑
            return 目标工具值(目标)#编辑后视图
        if 动作=='pause' or 动作=='resume':#暂停或恢复
            要求直接人类(上下文,执行)#必须人类回合
            if 有文本(陈述) or 有轮次上限(上限) or 有文本(阻塞原因文本):#不得带 edit/blocked 字段
                raise 装备错误(#字段用错
                    'objective and max_goal_rounds are valid only with action edit; blocked_reason is valid only with action blocked',#指出合法 action
                    'GOAL_TOOL_INVALID_UPDATE',#更新参数错误
                )#结束抛错
            当前=上下文.goals.get(执行['agent'])#当前目标视图
            if (动作=='resume' and 当前 is not None
                and 当前.get('id')==引用['id'] and 当前.get('revision')==引用['revision']
                and 当前.get('phase')=='paused'):#模型不得自行恢复已暂停目标
                raise 装备错误(#须由用户恢复
                    'the model cannot resume a paused goal; the user must resume it',#人类可读
                    'GOAL_TOOL_RESUME_PAUSED',#暂停恢复拒绝
                )#结束抛错
            if 动作=='pause':#暂停
                目标=上下文.goals.pause(执行['agent'],引用)#暂停
            else:#恢复
                目标=上下文.goals.resume(执行['agent'],引用)#恢复
            return 目标工具值(目标)#变更后视图
        权限=完成权限(上下文,执行)#完成/阻塞权限
        if 有文本(陈述) or 有轮次上限(上限):#完成/阻塞不得改定义
            raise 装备错误(#字段用错
                'objective and max_goal_rounds are valid only with action edit',#仅 edit
                'GOAL_TOOL_INVALID_UPDATE',#更新参数错误
            )#结束抛错
        if 动作=='complete' and 有文本(阻塞原因文本):#完成不得带阻塞原因
            raise 装备错误('blocked_reason is valid only with action blocked','GOAL_TOOL_INVALID_UPDATE')#字段用错
        if 动作=='blocked' and (阻塞原因文本 is None or len(阻塞原因文本.strip())==0):#阻塞必须有原因
            raise 装备错误('blocked_reason is required with action blocked','GOAL_TOOL_INVALID_UPDATE')#缺原因
        if 动作=='blocked' and 权限['kind']=='goal-round':#自动轮次自我报告阻塞
            权限目标=权限['goal']#轮次权限上的目标
            if 权限目标['roundsStarted']<阻塞阈值:#未达阈值
                raise 装备错误(#硬下限
                    'blocked requires at least '+str(阻塞阈值)+' consecutive goal rounds; '#阈值
                    +'current round is '+str(权限目标['roundsStarted']),#当前轮次
                    'GOAL_TOOL_BLOCK_THRESHOLD',#未达阻塞阈值
                )#结束抛错
        if 动作=='complete':#完成
            目标=上下文.goals.complete(执行['agent'],引用)#完成
        else:#阻塞
            目标=上下文.goals.block(执行['agent'],引用,{#阻塞
                'code':'model-reported',#模型自报
                'message':阻塞原因文本,#上面已要求非空
            })#结束 block
        if 权限['kind']=='goal-round':#自动轮次终态要注入收尾
            if 动作=='complete':#完成收尾
                收尾内容=渲染收尾上下文(目标['objective'])#完成收尾
            else:#阻塞收尾
                收尾内容=渲染收尾上下文(目标['objective'],阻塞原因文本)#阻塞收尾
            执行元数据['deferContext'](创建用户消息({#延迟上下文，让模型还能说一次
                'content':收尾内容,#收尾指令块
                'source':{#插件通知来源
                    'kind':'plugin',#插件
                    'plugin':'tool-goal',#本包
                    'form':'notice',#通知
                    'summary':截上下文摘要(动作+': '+目标['objective']),#摘要
                },#结束 source
            }))#结束 deferContext
        return 目标工具值(目标)#终态视图
    def 呈现更新(参数):
        """调用时变更卡片。参数是 dict。"""
        动作=参数['action'] if 'action' in 参数 else ''#动词
        if 动作=='blocked':#阻塞用 Mark
            标题='Mark goal'#Mark goal
        elif len(动作)>0:#其它动作首字母大写
            标题=动作[0].upper()+动作[1:]+' goal'#Pause/Resume/... goal
        else:#缺动作
            标题='Update goal'#回落
        阻塞原因文本=参数['blocked_reason'] if 'blocked_reason' in 参数 else None#可选阻塞原因
        陈述=参数['objective'] if 'objective' in 参数 else None#可选陈述
        上限=参数['max_goal_rounds'] if 'max_goal_rounds' in 参数 else None#可选上限
        if 有文本(阻塞原因文本):#优先展示阻塞原因
            原文=阻塞原因文本#原因原文
        elif 有文本(陈述):#其次陈述
            原文=陈述#陈述原文
        elif 有轮次上限(上限):#否则上限
            原文=上限#上限原文
        else:#否则 id
            原文=参数['goal_id'] if 'goal_id' in 参数 else None#id 原文
        return 呈现(标题,'other',原文)#变更卡片
    上下文.tools.register(定义工具({#update_goal
        'name':'update_goal',#工具名
        'description':更新描述,#面向模型说明
        'parameters':{#更新参数
            'goal_id':{'type':'string','required':True,'description':'Exact id returned by get_goal.'},#精确 id
            'revision':{'type':'number','required':True,'description':'Exact positive revision returned by get_goal.'},#精确修订
            'action':{#动词
                'type':'string',#字符串
                'required':True,#必填
                'enum':list(更新动作),#五个 action
                'description':'edit | pause | resume | complete | blocked',#枚举说明
            },#结束 action
            'objective':{'type':'string','description':'Replacement objective; valid only with action edit.'},#仅 edit
            'max_goal_rounds':{'type':'number','description':'Replacement cap; valid only with action edit.'},#仅 edit
            'blocked_reason':{#仅 blocked
                'type':'string',#字符串
                'description':'Concrete blocking condition; required only with action blocked.',#具体阻塞条件
            },#结束 blocked_reason
        },#结束 parameters
        'output':目标输出,#规范输出
        'execute':执行更新,#按 action 分发
        'presentCall':呈现更新,#按 action 选标题与原文
    }))#结束 update_goal

name=名称#Cordis插件名
inject=依赖#Cordis依赖声明
Config=配置#Cordis配置模式
apply=应用#Cordis插件入口
default=应用#默认导出
默认=应用#中文默认导出

__all__=['名称','依赖','应用','默认']#公开面
