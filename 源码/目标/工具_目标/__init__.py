"""面向模型的 get_goal、create_goal 和 update_goal 工具，叠在同会话持久目标域之上。"""
import json,math#紧凑 JSON 渲染与安全整数判定
from ...依赖 import cordis#外部依赖胶水
from ...依赖.schemastery import 整数字段#配置字段
from ..目标 import 目标标识#目标 id 品牌
from ...模型后端.llm import 装备错误,截上下文摘要,创建用户消息#策略错误、摘要与收尾消息
from ...内核.工具 import 定义工具#定义面向模型的工具
from .权限 import 目标工具执行,要求直接人类,完成权限#执行时权限
from .收尾 import 渲染收尾上下文#终态收尾指令

名称='tool-goal'#Cordis插件名
注入=['agents','goals','tools','systemPrompt']#依赖智能体、目标、工具与系统提示
name=名称#Cordis插件名
inject=注入#Cordis依赖声明
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
Config=配置#Cordis配置模式

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 是否安全整数(值):#对齐 JS Number.isSafeInteger
    """对齐 JS Number.isSafeInteger，排除布尔。"""
    if isinstance(值,bool):#布尔不是数字
        return False#布尔不是安全整数
    if isinstance(值,int):#整数
        return -(2**53)<值<(2**53)#安全整数范围
    if isinstance(值,float):#浮点
        if not 值.is_integer():#非整值
            return False#不是整数
        return math.isfinite(值) and -(2**53)<值<(2**53)#有限且在安全范围
    return False#其它类型

def 策略指导(阻塞轮次):#用部署选定的阻塞阈值渲染策略指导
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

def 落实配置(配置值):#即使在 Loader 规范化之外直接调用 apply 也校验配置
    """落实阻塞阈值；非法则加载时失败。"""
    阻塞轮次=取字段(配置值,'blockedAfterConsecutiveRounds')#读配置
    if 阻塞轮次 is None:#缺省
        阻塞轮次=3#缺省 3
    if (not 是否安全整数(阻塞轮次)) or 阻塞轮次<1:#非正安全整数
        raise TypeError('blockedAfterConsecutiveRounds must be a positive safe integer')#加载时失败
    return {'blockedAfterConsecutiveRounds':阻塞轮次}#已落实

def 有文本(值):#可选文本是否有意义
    """可选文本是否有意义，而不是严格模式的空填充。"""
    return 值 is not None and 值!=''#缺席或空串都不算

def 有轮次上限(值):#可选轮次上限是否有意义
    """可选轮次上限是否有意义，而不是严格模式的零填充。"""
    return 值 is not None and 值!=0#缺席或 0 都不算

def 目标引用(标识,修订):#从模型参数构造精确比较交换引用
    """从模型参数构造精确比较交换引用。"""
    if len(标识)==0 or 标识!=标识.strip():#id 必须非空且已规范化
        raise 装备错误(#参数非法
            'goal_id must be non-empty and revision must be a positive safe integer',#人类可读
            'GOAL_TOOL_INVALID_UPDATE',#更新参数错误
        )#结束抛错
    if (not 是否安全整数(修订)) or 修订<1:#修订必须是正安全整数
        raise 装备错误(#参数非法
            'goal_id must be non-empty and revision must be a positive safe integer',#人类可读
            'GOAL_TOOL_INVALID_UPDATE',#更新参数错误
        )#结束抛错
    return {'id':目标标识(标识),'revision':修订}#打成品牌

def 目标工具值(目标):#视图 → 工具 JSON
    """稳定紧凑的模型结果；武装是观察值，不是回放状态。"""
    if 目标 is None:#没有当前目标
        return {'goal':None}#空
    快照={#快照出站
        'id':取字段(目标,'id'),#id 以字符串出
        'revision':取字段(目标,'revision'),#修订
        'objective':取字段(目标,'objective'),#陈述
        'phase':取字段(目标,'phase'),#阶段
        'roundsStarted':取字段(目标,'roundsStarted'),#已接纳轮次
        'maxGoalRounds':取字段(目标,'maxGoalRounds'),#上限
    }#快照字段结束
    阻塞原因=取字段(目标,'blockedReason')#可选阻塞原因
    if 阻塞原因 is not None:#仅阻塞带原因
        快照['blockedReason']={#码与说明
            'code':取字段(阻塞原因,'code'),#分类码
            'message':取字段(阻塞原因,'message'),#说明
        }#原因结束
    return {#有当前目标
        'goal':快照,#快照
        'activation':取字段(目标,'activation'),#进程内武装
    }#有目标结束

def 渲染目标值(_参数,值):#紧凑 JSON 文本
    """把结构化结果渲染成紧凑 JSON 文本块。"""
    return [{'type':'text','text':json.dumps(值,ensure_ascii=False,separators=(',',':'))}]#紧凑 JSON

目标输出={#三个目标控件共用的规范输出声明
    'schema':目标值模式,#JSON Schema
    'render':渲染目标值,#紧凑 JSON 文本
}#输出结束
def 呈现(标题,种类,原文=None):#通用卡片
    """目标工具共用的、只依赖 args 的挂起展示。"""
    视图={'card':'generic','title':标题,'kind':种类}#通用卡片
    if 原文 is not None:#有原文
        视图['rawInput']=原文#可选原文
    return 视图#卡片结束

def 应用(上下文,配置值):#注册三个 Codex 形目标工具及其共用策略段落
    """注册三个目标控件与共用策略段落。"""
    已落实=落实配置(配置值)#落实阈值
    阻塞阈值=已落实['blockedAfterConsecutiveRounds']#正数阈值
    上下文.systemPrompt.section({#策略段落
        'name':'tool:goal',#段落名
        'order':114,#排序
        'text':策略指导(阻塞阈值),#带阈值的指导
    })#结束段落
    def 执行读取(_参数,执行元数据):#读当前目标
        """认证调用方后返回当前视图或 null。"""
        执行=目标工具执行(上下文,执行元数据)#认证调用方
        return 已兑现(目标工具值(上下文.goals.get(执行['agent'])))#当前视图或 null
    def 呈现读取():#读卡片
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
    def 执行创建(参数,执行元数据):#创建
        """必须是根智能体人类回合；走域创建后返回视图。"""
        执行=目标工具执行(上下文,执行元数据)#认证调用方
        要求直接人类(上下文,执行)#必须是根智能体人类回合
        请求={'objective':取字段(参数,'objective')}#陈述
        上限=取字段(参数,'max_goal_rounds')#可选上限
        if 上限 is not None:#有上限
            请求['maxGoalRounds']=上限#可选上限
        目标=上下文.goals.create(执行['agent'],请求)#走域创建
        return 已兑现(目标工具值(目标))#创建后视图
    def 呈现创建(参数):#用陈述作原文
        """调用时创建卡片。"""
        return 呈现('Create goal','other',取字段(参数,'objective'))#用陈述作原文
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
    def 执行更新(参数,执行元数据):#按 action 分发
        """按 action 分发 edit/pause/resume/complete/blocked。"""
        执行=目标工具执行(上下文,执行元数据)#认证调用方
        引用=目标引用(取字段(参数,'goal_id'),取字段(参数,'revision'))#比较交换引用
        替换={}#edit 替换字段
        陈述=取字段(参数,'objective')#可选陈述
        if 有文本(陈述):#非空陈述
            替换['objective']=陈述#写入替换
        上限=取字段(参数,'max_goal_rounds')#可选上限
        if 有轮次上限(上限):#非零上限
            替换['maxGoalRounds']=上限#写入替换
        动作=取字段(参数,'action')#动词
        阻塞原因文本=取字段(参数,'blocked_reason')#可选阻塞原因
        if 动作=='edit':#编辑
            要求直接人类(上下文,执行)#必须人类回合
            if 有文本(阻塞原因文本):#编辑不得带阻塞原因
                raise 装备错误('blocked_reason is valid only with action blocked','GOAL_TOOL_INVALID_UPDATE')#字段用错
            目标=上下文.goals.edit(执行['agent'],引用,替换)#走域编辑
            return 已兑现(目标工具值(目标))#编辑后视图
        if 动作=='pause' or 动作=='resume':#暂停或恢复
            要求直接人类(上下文,执行)#必须人类回合
            if 有文本(陈述) or 有轮次上限(上限) or 有文本(阻塞原因文本):#不得带 edit/blocked 字段
                raise 装备错误(#字段用错
                    'objective and max_goal_rounds are valid only with action edit; blocked_reason is valid only with action blocked',#指出合法 action
                    'GOAL_TOOL_INVALID_UPDATE',#更新参数错误
                )#结束抛错
            if 动作=='pause':#暂停
                目标=上下文.goals.pause(执行['agent'],引用)#暂停
            else:#恢复
                目标=上下文.goals.resume(执行['agent'],引用)#恢复
            return 已兑现(目标工具值(目标))#变更后视图
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
        if 动作=='blocked' and 取字段(权限,'kind')=='goal-round':#自动轮次自我报告阻塞
            权限目标=取字段(权限,'goal')#轮次权限上的目标
            if 取字段(权限目标,'roundsStarted')<阻塞阈值:#未达阈值
                raise 装备错误(#硬下限
                    'blocked requires at least '+str(阻塞阈值)+' consecutive goal rounds; '#阈值
                    +'current round is '+str(取字段(权限目标,'roundsStarted')),#当前轮次
                    'GOAL_TOOL_BLOCK_THRESHOLD',#未达阻塞阈值
                )#结束抛错
        if 动作=='complete':#完成
            目标=上下文.goals.complete(执行['agent'],引用)#完成
        else:#阻塞
            目标=上下文.goals.block(执行['agent'],引用,{#阻塞
                'code':'model-reported',#模型自报
                'message':阻塞原因文本,#上面已要求非空
            })#结束 block
        if 取字段(权限,'kind')=='goal-round':#自动轮次终态要注入收尾
            if 动作=='complete':#完成收尾
                收尾内容=渲染收尾上下文(取字段(目标,'objective'))#完成收尾
            else:#阻塞收尾
                收尾内容=渲染收尾上下文(取字段(目标,'objective'),阻塞原因文本)#阻塞收尾
            执行元数据.deferContext(创建用户消息({#延迟上下文，让模型还能说一次
                'content':收尾内容,#收尾指令块
                'source':{#插件通知来源
                    'kind':'plugin',#插件
                    'plugin':'tool-goal',#本包
                    'form':'notice',#通知
                    'summary':截上下文摘要(动作+': '+取字段(目标,'objective')),#摘要
                },#结束 source
            }))#结束 deferContext
        return 已兑现(目标工具值(目标))#终态视图
    def 呈现更新(参数):#按 action 选标题与原文
        """调用时变更卡片。"""
        动作=取字段(参数,'action')#动词
        if 动作=='blocked':#阻塞用 Mark
            标题='Mark goal'#Mark goal
        else:#其它动作首字母大写
            标题=动作[0].upper()+动作[1:]+' goal'#Pause/Resume/... goal
        阻塞原因文本=取字段(参数,'blocked_reason')#可选阻塞原因
        陈述=取字段(参数,'objective')#可选陈述
        上限=取字段(参数,'max_goal_rounds')#可选上限
        if 有文本(阻塞原因文本):#优先展示阻塞原因
            原文=阻塞原因文本#原因原文
        elif 有文本(陈述):#其次陈述
            原文=陈述#陈述原文
        elif 有轮次上限(上限):#否则上限
            原文=上限#上限原文
        else:#否则 id
            原文=取字段(参数,'goal_id')#id 原文
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

apply=应用#Cordis插件入口
default=应用#默认导出
默认=应用#中文默认导出

__all__=['名称','注入','应用','name','inject','apply','默认','default']#公开面