from ...基础设施.js特性 import PromiseEX as 期约#期约封装
from ...类型化远程调用.协议 import 远程服务,远程#Remote 面
from ...类型化远程调用.协议.异常 import 远程错误#远程失败
from ...工具.时间 import 规范化客户端时区#浏览器时区
from ...内核.作用域 import 作用域目标#导入作用域载体解析
from ...内核.工具 import 断言对象json模式#导入对象JSON模式断言
from .类型 import (
    子智能体运行标识,#跑 id 品牌构造
    子智能体跑信息,#subagent/start 载荷
    子智能体跑结束信息,#subagent/end 载荷
    子智能体能力,#提供方启动时能力广告
    子智能体启动请求,#一次性启动请求
    已解析子智能体启动请求,#挂上描述符后的一次性请求
    可续跑创建请求,#prepareContinuable 入参
    可续跑创建规格,#提供方分离创建数据
    子智能体停止原因映射,#可合并扩展的停止原因表
    子智能体停止原因,#停止原因联合
    子智能体结果,#一次性跑终态结果
    子智能体跑,#一次性跑句柄协议
    子智能体提供方,#具名传输提供方协议
)
from .异常 import 子智能体错误,子智能体深度错误,子智能体描述符错误#缝内带码失败
from .深度 import 断言子智能体最大深度,委托深度于#共享深度词汇
from .生命周期 import 创建生命周期发出,创建激活观察者#start/end 发布与 Activation 观察
from .管理器 import 子智能体管理器#激活编排
from .描述符播种 import 创建智能体消息,附可续跑返回指引,创建结算消息#相邻消息与结算通知
from .内部 import 投递子智能体提示键#宿主投递符号槽
from .结构化 import 结构化输出工具#结构化输出工具名
from .列举子体 import (
    列举子体,列举后代,#直接子体与后代树枚举
    子智能体列举条目,#listChildren 一条
    子智能体后代列举条目,#listDescendants 一条
)
from .描述符 import (
    折叠子智能体描述符,快照子智能体描述符,子智能体描述符版本,#描述符 API
    一次性子智能体描述符,#one-shot 载荷
    可续跑子智能体描述符数据,#continuable 载荷
    子智能体描述符数据,#载荷联合
    一次性子智能体描述符输入,#one-shot 输入
    可续跑子智能体描述符输入,#continuable 输入
    子智能体描述符输入,#输入联合
)
from .助手输出 import 助手输出折叠,最终助手输出#最终助手输出选取
from .子体 import (
    追加委托策略覆盖,应用子体组合,捕获委托策略覆盖,子会话元数据,
    解析子智能体选项,解析子深度,子智能体委托上下文,父委托智能体选项,
    子体组合,#persona / toolFilter
    委托策略覆盖,#sandbox / approval 快照
)
from .投影 import 子智能体计时投影定义,子智能体身份投影定义#sessionProjections 单元
from .目录 import 子智能体目录投影定义,建立目录子体#父拥有目录
from .进程外 import (
    无启动能力,断言正有限,断言可用工作目录,校验已配置工作目录,解析子工作目录,
    结算运行结果,子进程运行句柄,
    跑结果结算,#settleRunResult 零件
    子进程运行句柄零件,#subprocessRunHandle 零件
)
from .客户端 import (
    子智能体身份投影,#模式/标签投影
    子智能体计时投影,#活动回合计时投影
    子智能体目录条目,#直接子发现行
)
from .归档准入 import 安装子智能体归档准入
from .控制 import 校验控制请求,拒绝提示
from . import (
    投影类型,
    控制类型,
    远程,
)
__all__=(
    '子智能体运行时',
    '子智能体运行标识','子智能体跑信息','子智能体跑结束信息','子智能体能力',
    '子智能体启动请求','已解析子智能体启动请求','可续跑创建请求','可续跑创建规格',
    '子智能体停止原因映射','子智能体停止原因','子智能体结果','子智能体跑','子智能体提供方',
    '子智能体错误','断言子智能体最大深度','委托深度于',
    '创建智能体消息','附可续跑返回指引','创建结算消息','父委托智能体选项','结构化输出工具',
    '列举子体','列举后代','子智能体列举条目','子智能体后代列举条目',
    '折叠子智能体描述符','快照子智能体描述符','子智能体描述符版本',
    '一次性子智能体描述符','可续跑子智能体描述符数据','子智能体描述符数据',
    '一次性子智能体描述符输入','可续跑子智能体描述符输入','子智能体描述符输入',
    '助手输出折叠','最终助手输出',
    '追加委托策略覆盖','应用子体组合','捕获委托策略覆盖','子会话元数据',
    '解析子智能体选项','解析子深度','子智能体深度错误','子智能体委托上下文',
    '子体组合','委托策略覆盖',
    '无启动能力','断言正有限','断言可用工作目录','校验已配置工作目录','解析子工作目录',
    '结算运行结果','子进程运行句柄','跑结果结算','子进程运行句柄零件',
    '子智能体身份投影','子智能体计时投影','子智能体目录条目',
    '子智能体目录投影定义','建立目录子体',
)

class 子智能体运行时(远程服务):
    '具名提供方注册表。每次子执行都经激活管理器建立'
    配置模式={'maxDepth':1,'maxActiveSubagents':8}#缺省宿主配置

    def __init__(自身,ctx,配置=None):
        '用 Cordis 上下文安装子智能体服务。配置可含 maxDepth 与 maxActiveSubagents'
        super().__init__(ctx,'subagents')#登记服务名
        配置={} if 配置 is None else dict(配置)#拷贝
        if 'maxDepth' not in 配置:#缺省深度
            配置['maxDepth']=1#缺省
        if 'maxActiveSubagents' not in 配置:#缺省活子
            配置['maxActiveSubagents']=8#缺省
        上限=配置['maxActiveSubagents']#活子上限
        if isinstance(上限,bool) or not isinstance(上限,int) or 上限<1:#必须至少 1
            raise 子智能体错误('maxActiveSubagents must be an integer >= 1','INVALID_CONFIG')#拒绝
        断言子智能体最大深度(配置['maxDepth'])#深度形态
        自身._配置=配置#当前配置
        自身._提供方表={}#提供方注册表
        自身._管理器=None#agents 注入前为空
        def 取委托父载体(父):
            '按委托父解析作用域载体'
            return 作用域目标(自身,父)#载体
        自身._发出生命周期=创建生命周期发出(自身.ctx,取委托父载体)#按委托父载体隔离派发
        def 挂管理器(子上下文):
            'agents 可用时挂激活管理器；纤维拆除只解绑本实例'
            def 启动外部宿主(名,请求):
                '外部提供方启动'
                提供方=自身._期望提供方(名)#解析
                启动=getattr(提供方,'启动',None)#中文入口
                if 启动 is None:#英文槽
                    启动=提供方.start#线协议入口
                return 启动(请求)#委托
            def 准备可续跑宿主(名,请求):
                '本地提供方分离创建'
                return 自身._准备可续跑(名,请求)#委托
            def 观察激活宿主(提供方,子标识,父):
                '驻留纪元观察'
                return 自身._观察激活(提供方,子标识,父)#委托
            def 最大活跃():
                '读活子上限'
                return 自身._配置['maxActiveSubagents']#上限
            管理器=子智能体管理器(子上下文,{
                '启动外部':启动外部宿主,#外部启动
                '准备可续跑':准备可续跑宿主,#本地准备
                '观察激活':观察激活宿主,#生命周期
            },最大活跃)
            自身._管理器=管理器#挂上
            def 解绑工厂():
                '返回仅解绑本实例的 disposer'
                def 解绑():
                    '仍是本实例才清空槽'
                    if 自身._管理器 is 管理器:#仍是本实例
                        自身._管理器=None#解绑
                return 解绑#拆除器
            子上下文.副作用(解绑工厂,'subagents.managerBinding()')#命名副作用
        ctx.依赖启动(['agents'],挂管理器)#agents 注入门
        def 挂投影(投影上下文):
            '登记目录、计时与身份三个投影单元'
            投影上下文.sessionProjections.register(子智能体目录投影定义)#父拥有目录
            投影上下文.sessionProjections.register(子智能体计时投影定义)#活动回合计时
            投影上下文.sessionProjections.register(子智能体身份投影定义)#模式/标签身份
        ctx.依赖启动(['sessionProjections'],挂投影)#投影注入门
        def 挂归档(智能体上下文):
            '归档准入知道哪些活子从一条会话派生'
            安装子智能体归档准入(智能体上下文)#安装
        ctx.依赖启动(['agents'],挂归档)#agents 注入门

    def 解析最大深度(自身,已配置=None):
        '按当前配置解析委托工具的深度策略'
        if 已配置=='provider-managed':#提供方自管
            return None#无数值
        if 已配置 is not None:#显式
            return 已配置#上限
        深度=自身._配置['maxDepth']#配置缺省
        断言子智能体最大深度(深度)#形态
        return 深度#上限

    def 启动激活(自身,规格):
        '建立一次受管理的本地或外部子执行'
        提供方=自身._期望提供方(规格['provider'])#解析提供方
        子标识=规格['childId'] if 'childId' in 规格 else None#预留身份
        if 子标识 is not None and not _有准备可续跑(提供方):#预留 id 只要本地后端
            raise 子智能体错误('reserved child ids require a local backend','UNSUPPORTED_CAPABILITY')#拒绝
        请求=规格['request']#任务
        断言子智能体最大深度(请求['maxDepth'] if 'maxDepth' in 请求 else None)#深度形态
        自身._断言能力(提供方,请求)#校验能力
        管理器=自身._要求管理器()#必须有管理器
        智能体表=自身.ctx.获取服务('agents',False)#智能体表
        父=请求['parent']#父
        if 智能体表 is None or 智能体表.获取(父.id) is not 父:#必须是精确活父
            raise 子智能体错误('subagent creation requires the exact live parent agent','UNAUTHORIZED')#拒绝
        if 'outputSchema' in 请求 and 请求['outputSchema'] is not None:#有输出模式
            断言对象json模式(请求['outputSchema'])#校验
        if _有准备可续跑(提供方):#本地
            return 管理器.启动本地(规格)#本地激活
        return 管理器.启动外部(规格)#外部激活

    def 等待子体(自身,父):
        '加入进行中的后代，不取消它们。没有管理器时为 False'
        if 自身._管理器 is None:#没有管理器
            已定=期约()#空结果
            已定.解决(False)#没有工作
            return 已定#期约
        return 自身._管理器.等待子体(父)#交给管理器

    def 打断(自身,目标会话标识,权威):#打断当前回合
        '在人类父地址或精确活祖先智能体权威下打断一次活可续跑子体的当前回合'
        if 自身._管理器 is not None:#有管理器才有 Activation
            自身._管理器.打断(目标会话标识,权威)#交给管理器

    def 发送消息(自身,发送方,目标标识,内容,选项):
        '把模型撰写的消息转到发送方的直接父或直接可续跑子'
        return 自身._要求管理器().发送消息(发送方,目标标识,内容,选项)

    def 排空子体(自身,父,子标识列表):
        '返回期约：释放一个精确活父之下选中的驻留直接子'
        管理器=自身._管理器
        if 管理器 is None:
            已释放=期约()#无管理器则没有可释放的
            已释放.解决()#已兑现
            return 已释放
        return 管理器.排空子体(父,子标识列表)

    def 投递提示(自身,父,子标识,内容,来源,信号,投递):
        '把一条宿主协议消息投到直接可续跑子'
        if 投递=='steer':
            return 自身._要求管理器().转向提示(父,子标识,内容,来源,信号)
        return 自身._要求管理器().排队提示(父,子标识,内容,来源,信号)

    @远程('prompt')
    def 提示(自身,请求,信号):
        '返回期约：经精确活直接父向可续跑子投递一条浏览器撰写的消息，兑现值是 messageId；失败译成 远程错误 后拒绝（参数校验失败仍同步抛出）'
        父会话标识=请求['parentSessionId']
        子会话标识=请求['childSessionId']
        客户端时区=请求['clientTimeZone'] if 'clientTimeZone' in 请求 else None
        投递=请求['delivery']
        校验控制请求('subagent.prompt',请求)
        规范时区=None if 客户端时区 is None else 规范化客户端时区(客户端时区)
        if 客户端时区 is not None and 规范时区 is None:
            raise 远程错误(
                'subagent/invalid-time-zone',
                'clientTimeZone must be UTC or a valid IANA Area/Location name',
                {'value':客户端时区},
            )
        智能体表=自身.ctx.获取服务('agents',False)
        父=None if 智能体表 is None else 智能体表.获取(父会话标识)
        if 父 is None:
            raise 远程错误(
                'subagent/parent-unavailable',
                'parent session "'+str(父会话标识)+'" is not live',
                {'parentSessionId':父会话标识},
            )
        来源={'kind':'user','rpcId':请求['requestId']}
        if 规范时区 is not None:
            来源['clientTimeZone']=规范时区
        结果=期约()
        def 投递已接受(消息标识):
            '收件箱接受后兑现 messageId'
            结果.解决({'messageId':消息标识})
        def 投递失败(错误):
            '把投递失败译成远程错误并拒绝结果；拒绝提示 始终抛 远程错误'
            try:
                拒绝提示(错误,子会话标识,信号)
            except 远程错误 as 远程失败:
                结果.拒绝(远程失败)
        try:
            内容块=请求['content']
            if all(块['type']=='text' for 块 in 内容块):
                内容=[{'type':'text','text':块['text']} for 块 in 内容块]
            else:
                附件存储=自身.ctx.获取服务('attachments',False)
                if 附件存储 is None:
                    raise 子智能体描述符错误('subagent image prompt requires an attachment store')
                内容=附件存储.准入提示内容(内容块)
            自身.投递提示(父,子会话标识,内容,来源,信号,投递).然后(投递已接受,投递失败)
        except Exception as 错误:
            投递失败(错误)
        return 结果

    @远程('interruptByParent')
    def 按父打断(自身,childSessionId,parentSessionId,mode):
        'Remote 面的打断：只按活 Activation 授权耐久父地址'
        校验控制请求('subagent.interrupt',{
            'childSessionId':childSessionId,
            'parentSessionId':parentSessionId,
            'mode':mode,
        })
        try:
            自身.打断(childSessionId,{'kind':'user','parentSessionId':parentSessionId})
        except Exception as 错误:
            if isinstance(错误,子智能体错误) and 错误.code=='UNAUTHORIZED':
                raise 远程错误(
                    'subagent/unauthorized',
                    'subagent does not belong to this parent',
                    {'childSessionId':childSessionId},
                    错误,
                )
            raise 远程错误('gateway/internal','subagent interrupt failed',{},错误)
        return {'accepted':True}

    def 排空后代(自身,父列表):#排空作用域后代
        '返回期约：关闭精确活父之下的准入，停掉可见后代 Activation，全部拆除后兑现'
        管理器=自身._管理器#可选管理器
        if 管理器 is None:#无管理器则空操作
            已排空=期约()#从未物化过任何东西
            已排空.解决()#已兑现
            return 已排空#空操作
        return 管理器.排空后代(父列表)#交给管理器

    def 列出子体(自身,父会话标识,信号=None):#枚举直接子体
        '枚举父的直接有会话子智能体，不加载或恢复 Agent'
        return 列举子体(自身.ctx,父会话标识,信号)#委托列举实现

    def 列出后代(自身,根会话标识,信号=None):#枚举后代树
        '从一份活优先语料以稳定前序枚举根的完整有会话子智能体树'
        return 列举后代(自身.ctx,根会话标识,信号)#委托列举实现

    def 登记提供方(自身,提供方):#登记提供方
        '按名登记一个提供方。没有 start 也没有 prepareContinuable 的提供方在登记前拒绝'
        名=提供方.名称 if hasattr(提供方,'名称') else 提供方.name#提供方名
        if not _有启动(提供方) and not _有准备可续跑(提供方):#两种执行入口都没有
            raise 子智能体错误(
                'subagent provider "'+str(名)+'" must implement start or prepareContinuable',
                'UNSUPPORTED_CAPABILITY',
            )#拒绝
        def 效果():#效果作用域登记
            '登记并返回拆除器；重复名大声失败'
            if 名 in 自身._提供方表:#名已占用
                raise 子智能体错误('a subagent provider named "'+名+'" is already registered','DUPLICATE_PROVIDER')#拒绝重复
            自身._提供方表[名]=提供方#写入注册表
            def 回滚():#回滚：移除并通知
                '移出注册表并发布 provider-removed'
                自身._提供方表.pop(名,None)#移出注册表
                自身._发出生命周期('subagent/provider-removed',名)#发布移除边
            自身.ctx.广播('subagent/provider-added',提供方)#发布新增
            return 回滚#拆除器
        return 自身.ctx.副作用(效果,'subagents.registerProvider()')#命名副作用

    def 取提供方(自身,名):#按名查找
        '按名查找提供方。缺席时为 None'
        return 自身._提供方表.get(名)#注册表读取

    def 列出(自身):#列出提供方名
        '按插入顺序列出已登记提供方名'
        return list(自身._提供方表.keys())#插入顺序

    def _准备可续跑(自身,名,请求):
        '解析一个提供方的分离可续跑创建贡献'
        提供方=自身._期望提供方(名)#解析提供方
        准备=getattr(提供方,'准备可续跑',None)#中文能力
        if 准备 is None and hasattr(提供方,'prepareContinuable'):#英文槽
            准备=提供方.prepareContinuable#线协议入口
        return 准备(请求)#委托提供方

    def _期望提供方(自身,名):#必须存在的提供方
        '查找供派发用的提供方，否则大声失败'
        if 名 not in 自身._提供方表:#缺席
            raise 子智能体错误('no subagent provider registered for "'+名+'"','NO_PROVIDER')#拒绝
        return 自身._提供方表[名]#已登记提供方

    def _要求管理器(自身):#必须有管理器
        '解析激活管理器，否则大声失败'
        if 自身._管理器 is None:#agents 未注入
            raise 子智能体错误(
                'continuable subagents require the agents service',
                'CONTINUATION_UNAVAILABLE',
            )
        return 自身._管理器#管理器

    def _观察激活(自身,提供方,子标识,父):#建造 Activation 观察者
        '为一次激活的驻留纪元建造生命周期观察者'
        return 创建激活观察者(自身._发出生命周期,提供方,子标识,父)#经本服务发射器

    def _断言能力(自身,提供方,请求):#校验启动能力
        '拒绝提供方缺少的第一个被请求能力'
        能力=提供方.能力 if hasattr(提供方,'能力') else 提供方.capabilities#能力广告
        名=提供方.名称 if hasattr(提供方,'名称') else 提供方.name#提供方名
        需要=[
            ('agentOptions' in 请求 and 请求['agentOptions'] is not None,'agentOptions'),#智能体选项
            ('outputSchema' in 请求 and 请求['outputSchema'] is not None,'outputSchema'),#输出模式
            ('maxDepth' in 请求 and 请求['maxDepth'] is not None,'depthLimit'),#深度上限
            ('toolFilter' in 请求 and 请求['toolFilter'] is not None,'toolFilter'),#工具过滤
            ('persona' in 请求 and 请求['persona'] is not None,'persona'),#人设
        ]
        for 当,帽 in 需要:#逐项检查
            if 当 and (帽 not in 能力 or not 能力[帽]):#请求了但提供方没有
                raise 子智能体错误(
                    'subagent provider "'+名+'" does not support the "'+帽+'" capability',
                    'UNSUPPORTED_CAPABILITY',
                )

def _有启动(提供方):
    '提供方是否实现外部 start'
    return callable(getattr(提供方,'启动',None)) or callable(getattr(提供方,'start',None))

def _有准备可续跑(提供方):
    '提供方是否实现本地 prepareContinuable'
    return callable(getattr(提供方,'准备可续跑',None)) or callable(getattr(提供方,'prepareContinuable',None))

子智能体运行时.inject=['workingDirectory']#框架槽
setattr(子智能体运行时,投递子智能体提示键,子智能体运行时.投递提示)#宿主投递槽，不进 __all__
default=子智能体运行时#框架槽
