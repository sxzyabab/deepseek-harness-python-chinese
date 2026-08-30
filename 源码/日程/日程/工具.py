"""智能体作用域的日程管理工具，建立在持久会话折叠上。"""
import json,time#JSON 文本与墙钟
from ...依赖 import cordis#外部依赖胶水
from ...内核.工具 import 定义工具#定义面向模型的工具
from .领域 import (
    分配日程标识,#分配 id
    创建延迟日程记录,#创建延迟记录
    创建绝对日程记录,#创建绝对记录
    创建固定频率日程记录,#创建固定频率记录
    折叠日程事件,#折叠事件流
    最短固定间隔秒,#最短固定间隔
    日程标识,#日程 id
    日程输入错误,#输入错误
    日程日志错误,#日志错误
    日程视图,#面向模型视图
)#domain 导出
from .持久化 import 冲洗日程持久#导入持久屏障
from .事务 import 跑日程事务#导入串行事务

共有视图片段={#视图共有字段
    'id':{'type':'string','required':True},#日程 id
    'prompt':{'type':'string','required':True},#提醒正文
    'scheduledAt':{'type':'string','required':True},#计划时刻
    'state':{'type':'string','required':True,'enum':['scheduled','overdue']},#计划中或已过期
    'deliveryMode':{'type':'string','required':True,'const':'session-local'},#仅会话内投递
}#结束共有
延迟视图模式={#延迟视图模式
    'type':'object',#对象
    'additionalProperties':False,#禁止额外键
    'properties':{**共有视图片段,'kind':{'type':'string','required':True,'const':'after'},'afterSeconds':{'type':'integer','required':True}},#字段
}#结束延迟
绝对视图模式={#绝对视图模式
    'type':'object',#对象
    'additionalProperties':False,#禁止额外键
    'properties':{**共有视图片段,'kind':{'type':'string','required':True,'const':'at'}},#字段
}#结束绝对
固定频率视图模式={#固定频率视图模式
    'type':'object',#对象
    'additionalProperties':False,#禁止额外键
    'properties':{**共有视图片段,'kind':{'type':'string','required':True,'const':'every'},'everySeconds':{'type':'integer','required':True}},#字段
}#结束固定频率
视图模式={'oneOf':[延迟视图模式,绝对视图模式,固定频率视图模式]}#视图联合

def 基本错误模式(码):#构造恰好两字段的错误模式，并保留其字面 code
    """构造恰好两字段的错误模式，并保留其字面 code。"""
    return {#模式对象
        'type':'object',#对象
        'additionalProperties':False,#禁止额外键
        'properties':{#字段
            'code':{'type':'string','required':True,'const':码},#字面错误码
            'message':{'type':'string','required':True},#错误消息
        },#结束 properties
    }#只读模式

基本错误模式们=[#不含持久不确定的错误模式
    基本错误模式('invalid_prompt'),#非法正文
    基本错误模式('invalid_selector'),#非法选择器
    基本错误模式('invalid_rule'),#非法规则
    基本错误模式('invalid_time_zone'),#非法时区
    基本错误模式('not_future'),#非未来
    基本错误模式('time_out_of_range'),#时间越界
    基本错误模式('frequency_too_high'),#频率过高
    基本错误模式('corrupt_schedule_log'),#日志损坏
    基本错误模式('internal_error'),#内部错误
]#结束基本
持久错误模式={#持久不确定模式
    'type':'object',#对象
    'additionalProperties':False,#禁止额外键
    'properties':{#字段
        'code':{'type':'string','required':True,'const':'persistence_uncertain'},#持久不确定码
        'message':{'type':'string','required':True},#错误消息
        'operation':{'type':'string','required':True,'enum':['create','list','delete']},#相关操作
        'id':{'type':'string'},#可选相关 id
    },#结束 properties
}#结束持久
错误模式们=基本错误模式们+[持久错误模式]#全部错误模式
创建输出模式={'oneOf':[视图模式]+错误模式们}#创建输出
列出输出模式={'oneOf':[{'type':'array','items':视图模式}]+错误模式们}#列出输出
删除输出模式={'oneOf':[#成功、未找到或错误
    {'type':'object','additionalProperties':False,'properties':{'id':{'type':'string','required':True},'deleted':{'type':'boolean','required':True,'const':True}}},#已删除
    {'type':'object','additionalProperties':False,'properties':{'id':{'type':'string','required':True},'deleted':{'type':'boolean','required':True,'const':False},'code':{'type':'string','required':True,'const':'schedule_not_found'}}},#未找到
]+错误模式们}#结束删除
创建说明=('Create one reminder in the current session. Supply a non-empty prompt and exactly one selector: '#选择器总述
    +'a positive safe-integer after_seconds delay, at as a strict offset date-time or local '#延迟或绝对
    +'date/time object, or safe-integer every_seconds of at least '+str(最短固定间隔秒)+'. '#固定频率下限
    +'Fixed-rate reminders stay creation-aligned, skip missed occurrences, and batch one latest '#固定频率语义
    +'occurrence per overdue rule. '#每条最新出现
    +'Delivery is session-local: the reminder runs on time only while this session '#会话内投递
    +'is live and otherwise becomes overdue until the session is resumed.')#离线则过期
列出说明=('List every active reminder in the current session in creation order, including its exact id, '#创建序列出
    +'UTC target, scheduled or overdue state, and session-local delivery mode.')#目标、状态与投递
删除说明=('Delete one active reminder in the current session by the exact id returned by schedule_create '#按精确 id 删除
    +'or schedule_list. Unknown or already-finished ids return deleted false.')#未知则 deleted false

def 解开(值):#承诺则等待否则原样
    """承诺则等待，否则原样返回。"""
    if 是否thenable(值):#可等待
        return 值.等待()#等待承诺
    return 值#同步值

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 已中止(信号):#信号是否已中止
    """英文 aborted 或中文 已中止 任一为真则视为已中止。"""
    if 信号 is None:#无信号
        return False#无信号
    if getattr(信号,'aborted',False):#英文旗标
        return True#英文旗标
    if getattr(信号,'已中止',False):#中文旗标
        return True#中文旗标
    return False#未中止

def 是否安全整数(值):#对齐 Number.isSafeInteger
    """对齐 JS Number.isSafeInteger，排除布尔。"""
    if isinstance(值,bool):#布尔不是数字
        return False#布尔不是整数
    if isinstance(值,int):#整数
        return abs(值)<=9007199254740991#在安全范围内
    if isinstance(值,float) and 值.is_integer():#整浮点
        return abs(值)<=9007199254740991#在安全范围内
    return False#其它

def 渲染取值(_参数,值):#每个规范日程取值的确定性模型正文
    """每个规范日程取值的确定性模型正文。"""
    文本=json.dumps(值,ensure_ascii=False)#规范 JSON 文本
    return [{'type':'text','text':文本}]#单文本块

def 呈现(标题,种类,原始输入=None):#纯 generic 待处理卡片
    """纯 generic 待处理卡片。"""
    卡片={'card':'generic','title':标题,'kind':种类}#generic 卡片
    if 原始输入 is not None:#有原始输入
        卡片['rawInput']=原始输入#带上
    return 卡片#卡片

def 内部错误():#不宜对外披露的失败所用的稳定错误
    """不宜对外披露的失败所用的稳定错误。"""
    return {'code':'internal_error','message':'The schedule operation failed.'}#固定文案

def 取消占位(信号):#正文静止后由注册表替换为规范 ABORTED 结果的占位
    """正文静止后由注册表替换为规范 ABORTED 结果的占位。"""
    if 已中止(信号):#已取消
        return 内部错误()#占位
    return None#未取消

def 可取消日程事务(智能体,信号,任务):#串行一次操作；调用方在 FIFO 轮到之前已取消则停正文
    """串行一次操作；调用方在 FIFO 轮到之前已取消则停正文。"""
    def 体():#事务体
        """接到前一事务之后。"""
        取消=取消占位(信号)#轮到时再看取消
        if 取消 is not None:#已取消
            return 取消#停正文
        return 任务()#跑完整操作
    return 跑日程事务(智能体,体)#串行

def 日志损坏错误():#稳定的持久日志失败
    """稳定的持久日志失败。"""
    return {'code':'corrupt_schedule_log','message':'The session schedule log is corrupt.'}#固定文案

def 持久不确定(操作,标识=None):#带已知操作身份的稳定持久不确定
    """带已知操作身份的稳定持久不确定。"""
    错误={'code':'persistence_uncertain','message':'Schedule persistence is uncertain; retry with schedule_list before relying on this result.','operation':操作}#错误对象
    if 标识 is not None:#有 id
        错误['id']=标识#带上
    return 错误#结束

def 输入错误译(错误):#把一条被包含的输入失败译成封闭工具联合
    """把一条被包含的输入失败译成封闭工具联合。"""
    return {'code':错误.code,'message':str(错误)}#公开码与诊断

def 工具折叠(智能体):#仅在预检成功后折叠，损坏映射为稳定取值
    """仅在预检成功后折叠，损坏映射为稳定取值。"""
    try:#折叠当前后缀
        会话=取字段(智能体,'session')#所属会话
        头=取字段(会话,'header')#会话头
        种子=取字段(头,'seedLength',0) or 0#fork 后缀起点
        return 折叠日程事件(取字段(会话,'events'),种子)#按 fork 后缀折叠
    except 日程日志错误:#折叠拒绝为日志损坏
        return 日志损坏错误()#稳定损坏
    except Exception:#其它
        return 内部错误()#内部错误

def 是工具错误(值):#折叠尝试是否产出错误而非回放态
    """折叠尝试是否产出错误而非回放态。"""
    return isinstance(值,dict) and 'code' in 值 and 'active' not in 值#错误带 code

def 预检(根上下文,智能体,操作,标识=None):#要求一次持久检查点，不泄漏后端失败
    """要求一次持久检查点，不泄漏后端失败。"""
    try:#调用共享屏障
        冲洗日程持久(根上下文,取字段(智能体,'session'))#flush 当前前缀
        return None#已确认
    except Exception:#屏障失败不泄漏后端
        return 持久不确定(操作,标识)#稳定的持久不确定

def 校验创建参数(参数):#校验开放参数根无法表达的 v1 选择器约束
    """校验开放参数根无法表达的 v1 选择器约束。"""
    if isinstance(参数,dict):#映射
        键们=list(参数.keys())#实际键
    else:#对象
        键们=[键 for 键 in getattr(参数,'__dict__',{}) if not str(键).startswith('_')]#自有键
    for 键 in 键们:#只允许这些键
        if 键 not in ('prompt','after_seconds','at','every_seconds'):#非法键
            return {'code':'invalid_selector','message':'schedule_create accepts exactly one of after_seconds, at, or every_seconds.'}#非法选择器
    延迟=取字段(参数,'after_seconds')#延迟
    绝对=取字段(参数,'at')#绝对
    间隔=取字段(参数,'every_seconds')#固定频率
    选择数=(0 if 延迟 is None else 1)+(0 if 绝对 is None else 1)+(0 if 间隔 is None else 1)#恰好一个选择器
    if 选择数!=1:#三者择一
        return {'code':'invalid_selector','message':'schedule_create accepts exactly one of after_seconds, at, or every_seconds.'}#非法选择器
    正文=取字段(参数,'prompt')#提醒正文
    if 正文 is None or str(正文).strip()=='':#裁切后须非空
        return {'code':'invalid_prompt','message':'prompt must be non-empty after trimming.'}#非法正文
    if 延迟 is not None and ((not 是否安全整数(延迟)) or 延迟<=0):#有延迟则须正安全整数
        return {'code':'invalid_rule','message':'after_seconds must be a positive safe integer.'}#非法延迟
    if 间隔 is not None and (not 是否安全整数(间隔)):#有间隔则须安全整数
        return {'code':'invalid_rule','message':'every_seconds must be a safe integer.'}#非法间隔
    if 间隔 is not None and 间隔<最短固定间隔秒:#不低于五分钟
        return {'code':'frequency_too_high','message':'every_seconds must be at least '+str(最短固定间隔秒)+'.'}#频率过高
    return None#选择器合法

def 登记日程工具(根上下文,工具上下文,智能体,耐久变更时):#在一个精确智能体作用域注册全部三个日程工具
    """在一个精确智能体作用域注册全部三个日程工具。返回三次注册的幂等聚合 disposer。"""
    拆除们=[]#三次注册的拆除
    def 通知耐久变更():#投影观察者无法撤销已完成的耐久屏障
        """投影观察者无法撤销已完成的耐久屏障。"""
        try:#观察者不得使工具失败
            耐久变更时()#驱使运行时
        except Exception as 错误:#观察者抛错
            消息=错误.message if isinstance(错误,Exception) and hasattr(错误,'message') else str(错误)#诊断
            if hasattr(错误,'args') and len(错误.args)>0 and not hasattr(错误,'message'):#标准异常
                消息=str(错误)#消息
            根上下文.logger.warn('schedule: durable-change observer failed: '+str(错误))#记警告
    try:#注册三个工具
        def 执行创建(参数,执行上下文):#执行创建
            """执行 schedule_create。"""
            if 取字段(执行上下文,'agent') is not 智能体:#必须是本拥有方
                return 内部错误()#内部
            非法=校验创建参数(参数)#选择器约束
            if 非法 is not None:#非法
                return 非法#稳定错误
            信号=取字段(执行上下文,'signal')#取消信号
            def 任务():#串行创建
                """串行创建正文。"""
                不确定=预检(根上下文,智能体,'create')#预检持久
                if 不确定 is not None:#不确定
                    return 不确定#停
                通知耐久变更()#预检成功后驱使
                折叠=工具折叠(智能体)#折叠当前流
                if 是工具错误(折叠):#损坏或内部错误
                    return 折叠#错误
                标识=分配日程标识(折叠)#分配新鲜 id
                try:#按选择器铸造记录
                    if 取字段(参数,'at') is not None:#绝对
                        记录=创建绝对日程记录(标识,取字段(参数,'prompt'),取字段(参数,'at'),int(time.time()*1000))#绝对记录
                    elif 取字段(参数,'after_seconds') is not None:#延迟
                        记录=创建延迟日程记录(标识,取字段(参数,'prompt'),取字段(参数,'after_seconds'),int(time.time()*1000))#延迟记录
                    else:#固定频率
                        记录=创建固定频率日程记录(标识,取字段(参数,'prompt'),取字段(参数,'every_seconds'),int(time.time()*1000))#固定频率记录
                except 日程输入错误 as 错误:#铸造失败为输入
                    return 输入错误译(错误)#输入
                except Exception:#其它
                    return 内部错误()#内部
                追加前取消=取消占位(信号)#追加前再看取消
                if 追加前取消 is not None:#已取消
                    return 追加前取消#不追加
                try:#追加创建变更
                    解开(取字段(智能体,'session').append('schedule/change',{'version':1,'operation':'create','schedule':记录}))#持久创建
                except Exception:#append 抛错不泄漏会话实现
                    return 内部错误()#稳定内部错误
                屏障=预检(根上下文,智能体,'create',标识)#创建后屏障
                if 屏障 is not None:#不确定
                    return 屏障#带 id 报告
                通知耐久变更()#屏障成功后再驱使
                return 日程视图(记录,int(time.time()*1000))#返回视图
            return 可取消日程事务(智能体,信号,任务)#串行
        def 呈现创建(参数):#待处理卡片
            """创建待处理卡片。"""
            return 呈现('Create reminder','other',取字段(参数,'prompt'))#卡片
        拆除们.append(工具上下文.tools.register(定义工具({#注册 schedule_create
            'name':'schedule_create',#创建工具名
            'description':创建说明,#创建说明
            'parameters':{#开放参数根
                'prompt':{'type':'string','required':True,'description':'Reminder content to present when the target becomes due.'},#提醒正文
                'after_seconds':{'type':'number','description':'Positive safe-integer delay in seconds.'},#延迟选择器
                'every_seconds':{'type':'number','description':'Fixed-rate safe-integer interval in seconds, at least '+str(最短固定间隔秒)+'.'},#固定频率
                'at':{#绝对选择器
                    'description':'Absolute target as strict offset RFC 3339 or local date/time with an explicit IANA zone.',#说明
                    'oneOf':[#字符串或对象
                        {'type':'string'},#显式偏移字符串
                        {'type':'object','additionalProperties':False,'properties':{'date':{'type':'string','required':True},'time':{'type':'string','required':True},'time_zone':{'type':'string','required':True}}},#本地日历
                    ],#结束 oneOf
                },#结束 at
            },#结束 parameters
            'output':{'schema':创建输出模式,'render':渲染取值},#创建输出
            'execute':执行创建,#执行
            'presentCall':呈现创建,#卡片
        })))#结束 schedule_create
        def 执行列出(_参数,执行上下文):#执行列出
            """执行 schedule_list。"""
            if 取字段(执行上下文,'agent') is not 智能体:#必须是本拥有方
                return 内部错误()#内部
            信号=取字段(执行上下文,'signal')#取消信号
            def 任务():#串行列出
                """串行列出正文。"""
                不确定=预检(根上下文,智能体,'list')#预检持久
                if 不确定 is not None:#不确定
                    return 不确定#停
                通知耐久变更()#预检成功后驱使
                折叠=工具折叠(智能体)#折叠当前流
                if 是工具错误(折叠):#损坏或内部错误
                    return 折叠#错误
                现在=int(time.time()*1000)#墙钟采样
                return [日程视图(记录,现在) for 记录 in 折叠['active']]#创建序视图
            return 可取消日程事务(智能体,信号,任务)#串行
        def 呈现列出(_参数=None):#只读卡片
            """列出只读卡片。"""
            return 呈现('List reminders','read')#卡片
        拆除们.append(工具上下文.tools.register(定义工具({#注册 schedule_list
            'name':'schedule_list',#列出工具名
            'description':列出说明,#列出说明
            'parameters':{},#无参数
            'output':{'schema':列出输出模式,'render':渲染取值},#列出输出
            'execute':执行列出,#执行
            'presentCall':呈现列出,#卡片
        })))#结束 schedule_list
        def 执行删除(参数,执行上下文):#执行删除
            """执行 schedule_delete。"""
            原始标识=取字段(参数,'id')#原始 id
            if (not isinstance(原始标识,str)) or len(原始标识)==0 or 原始标识.strip()!=原始标识:#须非空且无两侧空白
                return {'code':'invalid_rule','message':'schedule_delete id must be non-empty without surrounding whitespace.'}#非法 id
            标识=日程标识(原始标识)#打品牌
            if 取字段(执行上下文,'agent') is not 智能体:#必须是本拥有方
                return 内部错误()#内部
            信号=取字段(执行上下文,'signal')#取消信号
            def 任务():#串行删除
                """串行删除正文。"""
                不确定=预检(根上下文,智能体,'delete',标识)#预检持久
                if 不确定 is not None:#不确定
                    return 不确定#停
                通知耐久变更()#预检成功后驱使
                折叠=工具折叠(智能体)#折叠当前流
                if 是工具错误(折叠):#损坏或内部错误
                    return 折叠#错误
                if not any(记录['id']==标识 for 记录 in 折叠['active']):#不在活动集
                    return {'id':标识,'deleted':False,'code':'schedule_not_found'}#未找到非变更
                追加前取消=取消占位(信号)#追加前再看取消
                if 追加前取消 is not None:#已取消
                    return 追加前取消#不追加
                try:#追加删除变更
                    解开(取字段(智能体,'session').append('schedule/change',{'version':1,'operation':'delete','id':标识}))#持久删除
                except Exception:#append 抛错不泄漏会话实现
                    return 内部错误()#稳定内部错误
                屏障=预检(根上下文,智能体,'delete',标识)#删除后屏障
                if 屏障 is not None:#不确定
                    return 屏障#带 id 报告
                通知耐久变更()#屏障成功后再驱使
                return {'id':标识,'deleted':True}#已删除
            return 可取消日程事务(智能体,信号,任务)#串行
        def 呈现删除(参数):#待处理卡片
            """删除待处理卡片。"""
            return 呈现('Delete reminder','other',取字段(参数,'id'))#卡片
        拆除们.append(工具上下文.tools.register(定义工具({#注册 schedule_delete
            'name':'schedule_delete',#删除工具名
            'description':删除说明,#删除说明
            'parameters':{'id':{'type':'string','required':True,'description':'Exact session-local schedule id.'}},#删除参数
            'output':{'schema':删除输出模式,'render':渲染取值},#删除输出
            'execute':执行删除,#执行
            'presentCall':呈现删除,#卡片
        })))#结束 schedule_delete
    except Exception as 错误:#任一注册失败则回滚已注册
        for 拆除 in reversed(拆除们):#逆序拆除
            拆除()#拆
        raise 错误#再抛原错
    活跃=[True]#聚合 disposer 只跑一次
    def 聚合拆除():#幂等拆除
        """幂等拆除三个工具。"""
        if not 活跃[0]:#已拆过
            return#停
        活跃[0]=False#标记已拆
        for 拆除 in reversed(拆除们):#逆序卸三个工具
            拆除()#拆
    return 聚合拆除#聚合 disposer
