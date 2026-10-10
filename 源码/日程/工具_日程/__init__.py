'面向模型的 schedule_create、schedule_list、schedule_update 和 schedule_delete，叠在宿主 schedule 服务上'
from ...依赖 import cordis#外部依赖胶水
from ...基础设施.通用工具 import 是否整值数,是否正安全整数,最大安全整数,紧凑json编码,当前毫秒
from ...内核.工具 import 定义工具#定义面向模型的工具
from ...子智能体.子智能体.深度 import 委托深度于#委托深度
from ..日程 import 最短固定间隔秒,日程标识,日程输入错误,日程视图#域里已有的常量、品牌、输入错误与视图

名称='tool-schedule'#Cordis插件名
依赖=['tools']#工具注册表；schedule 服务在应用里再等
最长标题长度=120#域未导出标题上限，与上游 MAX_TITLE_LENGTH 相同
必填标题消息='title is required and must be non-empty after trimming.'#域未导出该句，模型可见诊断保持原文
共有视图属性={#六种视图共用的字段
    'id':{'type':'string','required':True},#日程 id
    'title':{'type':'string','required':True},#任务名
    'prompt':{'type':'string','required':True},#提醒正文
    'scheduledAt':{'type':'string','required':True},#计划时刻
    'state':{'type':'string','required':True,'enum':['scheduled','overdue']},#计划中或已过期
    'deliveryMode':{'type':'string','required':True,'const':'host'},#宿主投递
}#结束共有
延迟视图模式={#延迟视图
    'type':'object',#对象
    'additionalProperties':False,#禁止额外键
    'properties':{**共有视图属性,'kind':{'type':'string','required':True,'const':'after'},'afterSeconds':{'type':'integer','required':True}},#字段
}#结束延迟
绝对视图模式={#绝对视图
    'type':'object',#对象
    'additionalProperties':False,#禁止额外键
    'properties':{**共有视图属性,'kind':{'type':'string','required':True,'const':'at'}},#字段
}#结束绝对
固定频率视图模式={#固定频率视图
    'type':'object',#对象
    'additionalProperties':False,#禁止额外键
    'properties':{**共有视图属性,'kind':{'type':'string','required':True,'const':'every'},'everySeconds':{'type':'integer','required':True}},#字段
}#结束固定频率
每日视图模式={#每日视图
    'type':'object',#对象
    'additionalProperties':False,#禁止额外键
    'properties':{**共有视图属性,'kind':{'type':'string','required':True,'const':'daily'},'time':{'type':'string','required':True},'timeZone':{'type':'string','required':True}},#字段
}#结束每日
每周视图模式={#每周视图
    'type':'object',#对象
    'additionalProperties':False,#禁止额外键
    'properties':{#字段
        **共有视图属性,#共有
        'kind':{'type':'string','required':True,'const':'weekly'},#每周
        'time':{'type':'string','required':True},#本地时刻
        'timeZone':{'type':'string','required':True},#时区
        'weekdays':{'type':'array','required':True,'items':{'type':'integer'}},#ISO 星期
    },#结束 properties
}#结束每周
定时视图模式={#cron 视图
    'type':'object',#对象
    'additionalProperties':False,#禁止额外键
    'properties':{**共有视图属性,'kind':{'type':'string','required':True,'const':'cron'},'expression':{'type':'string','required':True},'timeZone':{'type':'string','required':True}},#字段
}#结束 cron
视图模式={'oneOf':[延迟视图模式,绝对视图模式,固定频率视图模式,每日视图模式,每周视图模式,定时视图模式]}#视图联合

def 基本错误模式(码):
    '构造恰好两字段的错误模式，并保留其字面 code'
    return {#模式对象
        'type':'object',#对象
        'additionalProperties':False,#禁止额外键
        'properties':{#字段
            'code':{'type':'string','required':True,'const':码},#字面错误码
            'message':{'type':'string','required':True},#错误消息
        },#结束 properties
    }#结束模式

错误模式列表=[#封闭错误模式
    基本错误模式('invalid_prompt'),#非法正文或标题
    基本错误模式('invalid_selector'),#非法选择器
    基本错误模式('invalid_rule'),#非法规则
    基本错误模式('invalid_time_zone'),#非法时区
    基本错误模式('not_future'),#非未来
    基本错误模式('time_out_of_range'),#时间越界
    基本错误模式('frequency_too_high'),#频率过高
    基本错误模式('subagent_session'),#子体会话
    基本错误模式('internal_error'),#内部错误
]#结束错误模式
创建输出模式={'oneOf':[视图模式]+错误模式列表}#创建输出
列出输出模式={'oneOf':[{'type':'array','items':视图模式}]+错误模式列表}#列出输出
删除输出模式={'oneOf':[#已删除、未找到或错误
    {'type':'object','additionalProperties':False,'properties':{'id':{'type':'string','required':True},'deleted':{'type':'boolean','required':True,'const':True}}},#已删除
    {'type':'object','additionalProperties':False,'properties':{'id':{'type':'string','required':True},'deleted':{'type':'boolean','required':True,'const':False},'code':{'type':'string','required':True,'const':'schedule_not_found'}}},#未找到
]+错误模式列表}#结束删除
更新输出模式={'oneOf':[#视图、未改成或错误
    视图模式,#成功视图
    {#未更新
        'type':'object',#对象
        'additionalProperties':False,#禁止额外键
        'properties':{#字段
            'id':{'type':'string','required':True},#日程 id
            'updated':{'type':'boolean','required':True,'const':False},#未更新
            'code':{'type':'string','required':True,'enum':['schedule_not_found','schedule_ended','schedule_conflict']},#未找到、已结束或冲突
        },#结束 properties
    },#结束未更新
]+错误模式列表}#结束更新
创建说明=('Create a reminder in the current session that delivers prompt when it becomes due. '#到期投递正文
    +'Supply exactly one timing parameter: after_seconds, at, every_seconds, daily, weekly, or cron. '#恰好一个时机
    +'Local times that do not exist in the zone are skipped; repeated local times fire once, at the earlier instant. '#缺口跳过，重叠取较早
    +'After downtime, a recurring reminder delivers only its latest missed occurrence. Delivery can repeat after a crash.')#宕机后只补最近一次
列出说明='List the active reminders in the current session.'#列出当前会话的活动提醒
删除说明=('Delete a reminder in the current session, active or inactive. '#活动与已结束都可删
    +'Deletion does not retract a reminder message that is already queued.')#不撤回已入队消息
更新说明=('Change a reminder in place, keeping its id. Supply a new title, prompt, or at most one timing parameter; '#原地修改并保持 id
    +'omitted fields keep their stored values. To change a relative delay, create a new reminder.')#相对延迟须新建
选择器参数={#创建与更新共用的时机参数，顺序与工具目录一致
    'every_seconds':{#固定频率
        'type':'number',#数字
        'description':'Fixed-rate interval in whole seconds, at least '+str(最短固定间隔秒)+', aligned to the creation time; changing it with schedule_update re-aligns it to the save time.',#下限与对齐
    },#结束 every_seconds
    'daily':{#每日
        'type':'object',#对象
        'additionalProperties':False,#禁止额外键
        'description':'Every day at a local time.',#每天一次
        'properties':{#字段
            'time':{'type':'string','required':True,'description':'HH:mm:ss with optional 1-3 fractional digits, for example 23:00:00.'},#本地时刻
            'time_zone':{'type':'string','required':True,'description':'UTC or IANA Area/Location, for example Asia/Shanghai.'},#时区
        },#结束 properties
    },#结束 daily
    'weekly':{#每周
        'type':'object',#对象
        'additionalProperties':False,#禁止额外键
        'description':'On the given weekdays at a local time.',#指定星期
        'properties':{#字段
            'time':{'type':'string','required':True,'description':'HH:mm:ss with optional 1-3 fractional digits, for example 09:00:00.'},#本地时刻
            'time_zone':{'type':'string','required':True,'description':'UTC or IANA Area/Location, for example Asia/Shanghai.'},#时区
            'weekdays':{#ISO 星期
                'type':'array',#数组
                'required':True,#必填
                'description':'ISO weekdays, Monday 1 through Sunday 7, without repetitions.',#周一到周日，不重复
                'items':{'type':'integer'},#整数
            },#结束 weekdays
        },#结束 properties
    },#结束 weekly
    'cron':{#五段 cron
        'type':'object',#对象
        'additionalProperties':False,#禁止额外键
        'description':'Five-field Vixie cron expression in a time zone.',#五段表达式
        'properties':{#字段
            'expression':{#表达式
                'type':'string',#字符串
                'required':True,#必填
                'description':'minute hour day-of-month month day-of-week, for example "*/15 9-17 * * 1-5". When both day fields are restricted, a date matches if either one matches.',#日与星期同时限制时任一命中即可
            },#结束 expression
            'time_zone':{'type':'string','required':True,'description':'UTC or IANA Area/Location, for example Asia/Shanghai.'},#时区
        },#结束 properties
    },#结束 cron
    'at':{#绝对时刻
        'description':'Absolute target: an RFC 3339 date-time with offset, or a local date, time, and IANA time_zone.',#带偏移或本地日历
        'oneOf':[#字符串或对象
            {'type':'string'},#显式偏移
            {'type':'object','additionalProperties':False,'properties':{'date':{'type':'string','required':True},'time':{'type':'string','required':True},'time_zone':{'type':'string','required':True}}},#本地日历
        ],#结束 oneOf
    },#结束 at
}#结束选择器参数

def 已中止(信号):
    '信号是 threading.Event；未给出或未置位都算未中止'
    if 信号 is None:#无信号
        return False#未中止
    return 信号.is_set()#已置位

def 渲染取值(_参数,值):
    '每个规范日程取值的确定性模型正文'
    return [{'type':'text','text':紧凑json编码(值)}]#单文本块

def 呈现(标题,种类,原始输入=None):
    '纯 generic 待处理卡片'
    卡片={'card':'generic','title':标题,'kind':种类}#generic 卡片
    if 原始输入 is not None:#有原始输入
        卡片['rawInput']=原始输入#带上
    return 卡片#卡片

def 内部错误():
    '不宜对外披露的失败所用的稳定错误'
    return {'code':'internal_error','message':'The schedule operation failed.'}#固定文案

def 操作错误(错误):
    '输入失败公开码与消息；存储失败收成内部错误'
    if isinstance(错误,日程输入错误):#稳定输入失败
        return {'code':错误.code,'message':str(错误)}#公开码与诊断
    return 内部错误()#不披露内部异常

def 子智能体拒绝(智能体):
    '委托子体不能使用提醒；顶层调用方返回 None'
    if 智能体 is None or 委托深度于(智能体)==0:#没有调用方或顶层
        return None#放行
    return {'code':'subagent_session','message':'A delegated subagent cannot use reminders.'}#子体拒绝

def 是安全整数(值):
    '整值且绝对值不超过最大安全整数，排除布尔'
    if not 是否整值数(值):#布尔与非整值都不是
        return False#不是安全整数
    return abs(值)<=最大安全整数#落在安全范围

def 非法间隔(间隔秒):
    '给出的固定频率须是不低于域下限的安全整数；未给出则返回 None'
    if 间隔秒 is None:#未给出
        return None#不用查
    if not 是安全整数(间隔秒):#须是安全整数
        return {'code':'invalid_rule','message':'every_seconds must be a safe integer.'}#非法间隔
    if 间隔秒<最短固定间隔秒:#不低于域下限
        return {'code':'frequency_too_high','message':'every_seconds must be at least '+str(最短固定间隔秒)+'.'}#频率过高
    return None#间隔合法

def 派生日程视图(记录,现在):
    '执行局部管理视图。域函数仍把投递写成 session-local，新工具模式要求 host'
    视图=日程视图(记录,现在)#复制记录并派生状态
    视图['deliveryMode']='host'#改成宿主投递
    return 视图#完整视图

def 校验创建参数(参数):
    '校验开放参数根无法表达的选择器、标题、正文与延迟'
    允许=('prompt','title','after_seconds','at','every_seconds','daily','weekly','cron')#允许的键
    选择数=0#已给出的时机数
    for 键 in ('after_seconds','at','every_seconds','daily','weekly','cron'):#六个时机
        if 键 in 参数:#给出了
            选择数+=1#计数
    有多余键=False#是否有选择器之外的键
    for 键 in 参数:#实际键
        if 键 not in 允许:#非法键
            有多余键=True#记下
    if 有多余键 or 选择数!=1:#必须恰好一个时机
        return {'code':'invalid_selector','message':'schedule_create accepts exactly one of after_seconds, at, every_seconds, daily, weekly, or cron.'}#非法选择器
    if 参数['prompt'].strip()=='':#裁切后须非空
        return {'code':'invalid_prompt','message':'prompt must be non-empty after trimming.'}#非法正文
    标题=参数['title']#任务名
    if 标题.strip()=='':#裁切后须非空
        return {'code':'invalid_prompt','message':必填标题消息}#缺标题
    if len(标题.strip())>最长标题长度:#不超过上限
        return {'code':'invalid_prompt','message':'title must be at most '+str(最长标题长度)+' characters.'}#标题过长
    if 'after_seconds' in 参数 and not 是否正安全整数(参数['after_seconds']):#延迟须是正安全整数
        return {'code':'invalid_rule','message':'after_seconds must be a positive safe integer.'}#非法延迟
    间隔=参数['every_seconds'] if 'every_seconds' in 参数 else None#固定频率
    return 非法间隔(间隔)#间隔约束

def 校验更新参数(参数):
    '校验原地更新的选择器个数、id，以及给出的标题、正文或间隔'
    允许=('id','title','prompt','at','every_seconds','daily','weekly','cron')#允许的键
    选择数=0#已给出的时机数
    for 键 in ('at','every_seconds','daily','weekly','cron'):#更新不接受相对延迟
        if 键 in 参数:#给出了
            选择数+=1#计数
    有多余键=False#是否有允许集之外的键
    for 键 in 参数:#实际键
        if 键 not in 允许:#非法键
            有多余键=True#记下
    if 有多余键 or 选择数>1:#至多一个时机
        return {'code':'invalid_selector','message':'schedule_update accepts at most one of at, every_seconds, daily, weekly, or cron.'}#非法选择器
    标识=参数['id']#日程 id
    if len(标识)==0 or 标识.strip()!=标识:#须非空且无两侧空白
        return {'code':'invalid_rule','message':'schedule_update id must be non-empty without surrounding whitespace.'}#非法 id
    if 选择数==0 and 'title' not in 参数 and 'prompt' not in 参数:#至少改一处
        return {'code':'invalid_selector','message':'schedule_update needs a new title, prompt, or one of at, every_seconds, daily, weekly, or cron.'}#空更新
    if 'title' in 参数 and 参数['title'].strip()=='':#给出的标题裁切后须非空
        return {'code':'invalid_prompt','message':必填标题消息}#缺标题
    if 'title' in 参数 and len(参数['title'].strip())>最长标题长度:#给出的标题不超过上限
        return {'code':'invalid_prompt','message':'title must be at most '+str(最长标题长度)+' characters.'}#标题过长
    if 'prompt' in 参数 and 参数['prompt'].strip()=='':#给出的正文裁切后须非空
        return {'code':'invalid_prompt','message':'prompt must be non-empty after trimming.'}#非法正文
    间隔=参数['every_seconds'] if 'every_seconds' in 参数 else None#固定频率
    return 非法间隔(间隔)#间隔约束

def 时机变更(参数):
    '更新携带的那一个时机替换；未带时机则返回 None，保留已提交目标'
    if 'at' in 参数:#绝对
        return {'kind':'at','at':参数['at']}#绝对替换
    if 'every_seconds' in 参数:#固定频率
        return {'kind':'every','every_seconds':参数['every_seconds']}#固定频率替换
    if 'daily' in 参数:#每日
        return {'kind':'daily','daily':参数['daily']}#每日替换
    if 'weekly' in 参数:#每周
        return {'kind':'weekly','weekly':参数['weekly']}#每周替换
    if 'cron' in 参数:#cron
        return {'kind':'cron','cron':参数['cron']}#cron 替换
    return None#保持原目标

def 调用方智能体(执行):
    '取出调用方智能体；没有则是 None'
    if 'agent' not in 执行:#非智能体调用
        return None#没有
    return 执行['agent']#调用方

def 执行信号(执行):
    '取出取消信号；没有则是 None'
    if 'signal' not in 执行:#没有信号
        return None#没有
    return 执行['signal']#取消信号

def 登记日程工具(日程上下文):
    '在解析出 schedule 服务的作用域登记四个提醒工具'
    def 执行创建(参数,执行):
        '校验后在调用方会话创建提醒'
        智能体=调用方智能体(执行)#调用方
        if 智能体 is None:#没有调用方
            return 内部错误()#内部
        拒绝=子智能体拒绝(智能体)#子体
        if 拒绝 is not None:#拒绝
            return 拒绝#稳定拒绝
        非法=校验创建参数(参数)#选择器约束
        if 非法 is not None:#非法
            return 非法#稳定错误
        信号=执行信号(执行)#取消信号
        if 已中止(信号):#已取消
            return 内部错误()#停正文
        try:#交给宿主服务
            记录=日程上下文.schedule.create(智能体.session.id,参数,信号)#创建
            return 派生日程视图(记录,当前毫秒())#返回视图
        except Exception as 错误:#输入失败或存储失败
            return 操作错误(错误)#稳定取值
    def 呈现创建(参数):
        '创建待处理卡片'
        return 呈现('Create reminder','other',参数['prompt'] if 'prompt' in 参数 else None)#用正文作原文
    日程上下文.tools.register(定义工具({#注册 schedule_create
        'name':'schedule_create',#创建工具名
        'description':创建说明,#创建说明
        'parameters':{#开放参数根
            'prompt':{'type':'string','required':True,'description':'Reminder content to present when the target becomes due.'},#提醒正文
            'title':{'type':'string','required':True,'description':'Task name of at most '+str(最长标题长度)+' characters, shown on the task card and in task lists.'},#任务名
            'after_seconds':{'type':'number','description':'Delay in whole seconds.'},#相对延迟
            **选择器参数,#其余时机
        },#结束 parameters
        'output':{'schema':创建输出模式,'render':渲染取值},#创建输出
        'execute':执行创建,#执行
        'presentCall':呈现创建,#卡片
    }))#结束 schedule_create
    def 执行列出(_参数,执行):
        '列出调用方会话的活动提醒'
        智能体=调用方智能体(执行)#调用方
        if 智能体 is None:#没有调用方
            return 内部错误()#内部
        拒绝=子智能体拒绝(智能体)#子体
        if 拒绝 is not None:#拒绝
            return 拒绝#稳定拒绝
        if 已中止(执行信号(执行)):#已取消
            return 内部错误()#停正文
        try:#交给宿主服务
            记录列表=日程上下文.schedule.list({'sessionId':智能体.session.id})#活动提醒
            return [派生日程视图(记录,当前毫秒()) for 记录 in 记录列表]#逐条视图
        except Exception as 错误:#输入失败或存储失败
            return 操作错误(错误)#稳定取值
    def 呈现列出(_参数):
        '列出只读卡片'
        return 呈现('List reminders','read')#只读卡片
    日程上下文.tools.register(定义工具({#注册 schedule_list
        'name':'schedule_list',#列出工具名
        'description':列出说明,#列出说明
        'parameters':{},#无参数
        'output':{'schema':列出输出模式,'render':渲染取值},#列出输出
        'execute':执行列出,#执行
        'presentCall':呈现列出,#卡片
    }))#结束 schedule_list
    def 执行删除(参数,执行):
        '按精确 id 删除调用方会话里的提醒'
        if len(参数['id'])==0 or 参数['id'].strip()!=参数['id']:#须非空且无两侧空白
            return {'code':'invalid_rule','message':'schedule_delete id must be non-empty without surrounding whitespace.'}#非法 id
        标识=日程标识(参数['id'])#打品牌
        智能体=调用方智能体(执行)#调用方
        if 智能体 is None:#没有调用方
            return 内部错误()#内部
        拒绝=子智能体拒绝(智能体)#子体
        if 拒绝 is not None:#拒绝
            return 拒绝#稳定拒绝
        信号=执行信号(执行)#取消信号
        if 已中止(信号):#已取消
            return 内部错误()#停正文
        try:#交给宿主服务
            return 日程上下文.schedule.delete({'sessionId':智能体.session.id,'id':标识},信号)#删除
        except Exception as 错误:#输入失败或存储失败
            return 操作错误(错误)#稳定取值
    def 呈现删除(参数):
        '删除待处理卡片'
        return 呈现('Delete reminder','other',参数['id'] if 'id' in 参数 else None)#用 id 作原文
    日程上下文.tools.register(定义工具({#注册 schedule_delete
        'name':'schedule_delete',#删除工具名
        'description':删除说明,#删除说明
        'parameters':{'id':{'type':'string','required':True,'description':'Exact schedule id.'}},#精确 id
        'output':{'schema':删除输出模式,'render':渲染取值},#删除输出
        'execute':执行删除,#执行
        'presentCall':呈现删除,#卡片
    }))#结束 schedule_delete
    def 执行更新(参数,执行):
        '按观察记录原地更新标题、正文或一个时机'
        智能体=调用方智能体(执行)#调用方
        if 智能体 is None:#没有调用方
            return 内部错误()#内部
        拒绝=子智能体拒绝(智能体)#子体
        if 拒绝 is not None:#拒绝
            return 拒绝#稳定拒绝
        非法=校验更新参数(参数)#选择器约束
        if 非法 is not None:#非法
            return 非法#稳定错误
        信号=执行信号(执行)#取消信号
        if 已中止(信号):#已取消
            return 内部错误()#停正文
        标识=日程标识(参数['id'])#打品牌
        try:#先读活动集，缺席时再查目录
            会话标识=智能体.session.id#原会话
            期望=None#观察到的活动记录
            for 记录 in 日程上下文.schedule.list({'sessionId':会话标识}):#活动提醒
                if 记录['id']==标识:#命中
                    期望=记录#记下
                    break#停
            if 期望 is None:#不在活动集
                已结束=False#目录里是否有同一条
                for 条目 in 日程上下文.schedule.catalog():#活动与已结束
                    if 条目['sessionId']==会话标识 and 条目['id']==标识:#同一会话同一 id
                        已结束=True#已结束而非从未存在
                        break#停
                if 已结束:#目录里有
                    return {'id':标识,'updated':False,'code':'schedule_ended'}#已结束
                return {'id':标识,'updated':False,'code':'schedule_not_found'}#未找到
            变更=时机变更(参数)#时机替换
            请求={'sessionId':会话标识,'id':标识,'expected':期望}#比较交换
            if 变更 is not None:#有时机
                请求['change']=变更#带上
            if 'title' in 参数:#有新标题
                请求['title']=参数['title']#带上
            if 'prompt' in 参数:#有新正文
                请求['prompt']=参数['prompt']#带上
            结果=日程上下文.schedule.update(请求,信号)#更新
            if 'record' in 结果:#提交了记录
                return 派生日程视图(结果['record'],当前毫秒())#返回视图
            return 结果#未找到、已结束、冲突或服务拒绝
        except Exception as 错误:#输入失败或存储失败
            return 操作错误(错误)#稳定取值
    def 呈现更新(参数):
        '更新待处理卡片'
        return 呈现('Update reminder','other',参数['id'] if 'id' in 参数 else None)#用 id 作原文
    日程上下文.tools.register(定义工具({#注册 schedule_update
        'name':'schedule_update',#更新工具名
        'description':更新说明,#更新说明
        'parameters':{#开放参数根
            'id':{'type':'string','required':True,'description':'Schedule id returned by schedule_list.'},#精确 id
            'title':{'type':'string','description':'New task name of at most '+str(最长标题长度)+' characters.'},#新任务名
            'prompt':{'type':'string','description':'New reminder content.'},#新正文
            **选择器参数,#时机
        },#结束 parameters
        'output':{'schema':更新输出模式,'render':渲染取值},#更新输出
        'execute':执行更新,#执行
        'presentCall':呈现更新,#卡片
    }))#结束 schedule_update

def 应用(上下文):
    '挂载作用域登记四个日程工具；每次调用作用在调用方智能体的会话上'
    def 等到日程(日程上下文,*其余):
        'schedule 服务解析后再登记'
        登记日程工具(日程上下文)#四个工具
    上下文.依赖启动(['schedule'],等到日程)#等到宿主服务

name=名称#Cordis插件名
inject=依赖#Cordis依赖声明
apply=应用#Cordis插件入口
default=应用#默认导出
默认=应用#中文默认导出

__all__=['名称','依赖','应用','默认']#公开面
