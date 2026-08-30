"""子智能体能力缝（ctx.subagents）的 Service Definition：具名提供方注册表，外加按能力校验的异步 start API。提供方在返回跑之前建立子体，因此兑现是唯一的发布与所有权转移边界。"""
from ...依赖 import cordis#外部依赖胶水
服务=cordis.服务#导入服务基类
from ...内核.作用域 import 作用域目标#导入作用域载体解析
from ...内核.工具 import 断言对象json模式#导入对象JSON模式断言
from .类型 import (
    子智能体跑标识,#跑 id 品牌构造
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
from .错误 import 子智能体错误#缝内带码失败
from .深度 import 断言子智能体最大深度,委托深度于#共享深度词汇
from .生命周期 import 创建生命周期发射器,观察跑,创建激活观察者#start/end 发布与 Activation 观察
from .续跑 import (
    子智能体续跑管理器,#可续跑编排（agents 注入后挂上）
    协调者消息来源,#父跟进归属
    子智能体报告消息来源,#子自报告归属
    子智能体结算消息来源,#运行时结算通知归属
    子智能体报告投递,#quiet / wakeup
    子智能体报告选项,#自报告选项
    可续跑启动规格,#startContinuable 入参
    可续跑启动,#已接受初始提示后的身份
    子智能体打断权威,#interrupt 权威联合
    子智能体跟进选项,#followup 选项
)
from .激活装配注册表 import (
    子智能体激活装配注册表,#可续跑未发布窗口的部署贡献表
    可续跑装配贡献,#(子上下文)->拆除器
)
from .列举子体 import (
    列举子体,列举后代,#直接子体与后代树枚举
    子智能体列举条目,#listChildren 一条
    子智能体后代列举条目,#listDescendants 一条
)
from .描述符 import (
    折叠子智能体描述符,快照子智能体描述符,子智能体描述符版本,#描述符 API
    一次性子智能体描述符数据,#one-shot 载荷
    可续跑子智能体描述符数据,#continuable 载荷
    子智能体描述符数据,#载荷联合
    一次性子智能体描述符输入,#one-shot 输入
    可续跑子智能体描述符输入,#continuable 输入
    子智能体描述符输入,#输入联合
)
from .描述符播种 import 播种描述符回合#创建种子末尾追加隐藏描述符
from .运行结算 import 结算运行#一次性后台 Task 结局
from .助手输出 import 助手输出折叠,最终助手输出#最终助手输出选取
from .子体 import (
    追加委托策略覆盖,应用子体组合,捕获委托策略覆盖,子会话元数据,
    解析子智能体选项,解析子深度,子智能体深度错误,子智能体委托上下文,
    子体组合,#persona / toolFilter
    委托策略覆盖,#sandbox / approval 快照
)
from .投影 import 子智能体计时投影定义,子智能体身份投影定义#sessionProjections 单元
from .进程外 import (
    无启动能力,断言正有限,断言可用工作目录,校验已配置工作目录,解析子工作目录,
    结算跑结果,子进程跑句柄,
    跑结果结算,#settleRunResult 零件
    子进程跑句柄零件,#subprocessRunHandle 零件
)
from .客户端 import (
    子智能体身份投影,#模式/标签投影
    子智能体计时投影,#活动回合计时投影
)
__all__=(
    '子智能体运行时',
    '子智能体跑标识','子智能体跑信息','子智能体跑结束信息','子智能体能力',
    '子智能体启动请求','已解析子智能体启动请求','可续跑创建请求','可续跑创建规格',
    '子智能体停止原因映射','子智能体停止原因','子智能体结果','子智能体跑','子智能体提供方',
    '子智能体错误','断言子智能体最大深度','委托深度于',
    '协调者消息来源','子智能体报告消息来源','子智能体结算消息来源','子智能体报告投递',
    '子智能体报告选项','可续跑启动规格','可续跑启动','子智能体打断权威','子智能体跟进选项',
    '可续跑装配贡献','列举子体','列举后代','子智能体列举条目','子智能体后代列举条目',
    '折叠子智能体描述符','快照子智能体描述符','子智能体描述符版本',
    '一次性子智能体描述符数据','可续跑子智能体描述符数据','子智能体描述符数据',
    '一次性子智能体描述符输入','可续跑子智能体描述符输入','子智能体描述符输入',
    '播种描述符回合','结算运行','助手输出折叠','最终助手输出',
    '追加委托策略覆盖','应用子体组合','捕获委托策略覆盖','子会话元数据',
    '解析子智能体选项','解析子深度','子智能体深度错误','子智能体委托上下文',
    '子体组合','委托策略覆盖',
    '无启动能力','断言正有限','断言可用工作目录','校验已配置工作目录','解析子工作目录',
    '结算跑结果','子进程跑句柄','跑结果结算','子进程跑句柄零件',
    '子智能体身份投影','子智能体计时投影',
    '默认',
)

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段。"""
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

class 子智能体运行时(服务):#子智能体运行时服务
    """具名提供方注册表，含一次性跑、耐久发现与可续跑子体操作。"""
    def __init__(自身,ctx):#安装服务
        """用 Cordis 上下文安装子智能体服务。"""
        super().__init__(ctx,'subagents')#登记服务名
        自身._提供方们={}#提供方注册表（插入顺序用 dict 保序）
        自身._续跑=None#可选续跑管理器；agents 注入前为空
        自身._装配注册表=子智能体激活装配注册表()#可续跑未发布窗口贡献
        自身._发射生命周期=创建生命周期发射器(自身.ctx,lambda 父: 作用域目标(自身,父))#按委托父载体隔离派发
        def 挂续跑(子上下文):#agents 可用时挂续跑管理器
            """agents 可用时挂续跑管理器；纤维拆除只解绑本实例。"""
            管理器=子智能体续跑管理器(子上下文,{
                'prepareContinuable':lambda 名,请求: 自身._准备可续跑(名,请求),#提供方分离创建
                'observeActivation':lambda 提供方,子标识,父: 自身._观察激活(提供方,子标识,父),#驻留纪元观察
            },自身._装配注册表)
            自身._续跑=管理器#挂上
            def 解绑工厂():#纤维拆除时解绑
                """返回仅解绑本实例的 disposer。"""
                def 解绑():#纤维拆除时解绑
                    """仍是本实例才清空槽，避免后注入的绑定被误清。"""
                    if 自身._续跑 is 管理器:#仍是本实例
                        自身._续跑=None#解绑
                return 解绑#拆除器
            子上下文.effect(解绑工厂,'subagents.continuationBinding()')#命名 effect
        ctx.inject(['agents'],挂续跑)#agents 注入门
        def 挂投影(投影上下文):#投影可用时登记单元
            """登记计时与身份两个投影单元；缺席时列举会大声失败。"""
            投影上下文.sessionProjections.register(子智能体计时投影定义)#活动回合计时
            投影上下文.sessionProjections.register(子智能体身份投影定义)#模式/标签身份
        ctx.inject(['sessionProjections'],挂投影)#投影注入门

    def 启动可续跑(自身,规格):#启动可续跑子体
        """建立一次耐久可续跑子体并投递其初始提示；收件箱接受即决议。"""
        return 自身._要求续跑().启动可续跑(规格)#交给管理器

    def 跟进(自身,父,子标识,内容,选项):#跟进投递
        """把一条后续消息作为可续跑子体的下一 FIFO 回合投递。"""
        return 自身._要求续跑().跟进(父,子标识,内容,选项)#交给管理器

    def 打断(自身,目标会话标识,权威):#打断当前回合
        """在人类父地址或精确活祖先智能体权威下打断一次活可续跑子体的当前回合。"""
        if 自身._续跑 is not None:#有管理器才有 Activation
            自身._续跑.打断(目标会话标识,权威)#交给管理器
        # 无管理器：不可能拥有活 Activation，空操作

    def 自报告(自身,子,内容,选项):#子体向父报告
        """把一份选定内容从一个活可续跑子体投递到其耐久直接父。"""
        return 自身._要求续跑().自报告(子,内容,选项)#交给管理器

    def 登记可续跑装配(自身,贡献):#登记可续跑装配
        """把一项部署能力组进每个可续跑子体在全新创建与冷恢复时的未发布创建上下文。"""
        return 自身.ctx.effect(
            lambda: 自身._装配注册表.登记(贡献),#效果作用域登记
            'subagents.registerContinuableSetup()',#effect 名
        )

    def 排空可续跑后代(自身,父们):#排空作用域后代
        """关闭精确活父智能体之下的可续跑准入，同步只停它们可见的后代 Activation。"""
        管理器=自身._续跑#可选管理器
        # 缺少续跑服务表示从未物化过任何东西。
        if 管理器 is None:#无管理器则空操作
            return#空操作
        return 管理器.排空后代(父们)#交给管理器

    def 列举子体们(自身,父会话标识,信号=None):#枚举直接子体
        """枚举父的直接有会话子智能体，不加载或恢复 Agent。"""
        return 列举子体(自身.ctx,父会话标识,信号)#委托列举实现

    def 列举后代们(自身,根会话标识,信号=None):#枚举后代树
        """从一份活优先语料以稳定前序枚举根的完整有会话子智能体树。"""
        return 列举后代(自身.ctx,根会话标识,信号)#委托列举实现

    def 登记提供方(自身,提供方):#登记提供方
        """按名登记一个提供方。登记是效果作用域且 HMR 安全。"""
        名=取字段(提供方,'name') or 取字段(提供方,'名称')#提供方名（协议字段优先）
        def 效果():#效果作用域登记
            """登记并返回拆除器；重复名大声失败。"""
            if 名 in 自身._提供方们:#名已占用
                raise 子智能体错误('a subagent provider named "'+名+'" is already registered','DUPLICATE_PROVIDER')#拒绝重复
            自身._提供方们[名]=提供方#写入注册表
            def 回滚():#回滚：移除并通知
                """移出注册表并发布 provider-removed。"""
                自身._提供方们.pop(名,None)#移出注册表
                自身._发射生命周期('subagent/provider-removed',名)#发布移除边
            # 抛出的 added 监听器会解开已 yield 的回滚，匹配仓库大声失败的登记语义。
            自身.ctx.emit('subagent/provider-added',提供方)#发布新增
            return 回滚#拆除器
        return 自身.ctx.effect(效果,'subagents.registerProvider()')#命名 effect

    def 取提供方(自身,名):#按名查找
        """按名查找提供方。缺席时为 None。"""
        return 自身._提供方们.get(名)#注册表读取

    def 列出(自身):#列出提供方名
        """按插入顺序列出已登记提供方名。"""
        return list(自身._提供方们.keys())#插入顺序

    def 启动(自身,名,请求):#启动一次性跑
        """在具名提供方上建立已发布子体。能力与语义检查在委托之前跑。"""
        提供方=自身._期望提供方(名)#解析提供方
        自身._断言能力(提供方,请求)#校验能力
        断言子智能体最大深度(取字段(请求,'maxDepth'))#校验深度上限形态
        if 取字段(请求,'outputSchema') is not None:#有输出模式
            断言对象json模式(取字段(请求,'outputSchema'))#校验输出模式
        描述符输入={'mode':'one-shot','provider':名}#快照一次性描述符
        if 取字段(请求,'label') is not None:#有标签才展开
            描述符输入['label']=取字段(请求,'label')#展开
        描述符=快照子智能体描述符(描述符输入)#快照
        if isinstance(请求,dict):#映射请求
            已解析=dict(请求)#浅拷贝
        else:#对象请求
            已解析={
                'label':取字段(请求,'label'),#标签
                'prompt':取字段(请求,'prompt'),#提示
                'parent':取字段(请求,'parent'),#父
                'signal':取字段(请求,'signal'),#信号
                'agentOptions':取字段(请求,'agentOptions'),#选项
                'outputSchema':取字段(请求,'outputSchema'),#输出模式
                'maxDepth':取字段(请求,'maxDepth'),#深度
                'toolFilter':取字段(请求,'toolFilter'),#过滤
                'persona':取字段(请求,'persona'),#人设
            }
        已解析['descriptor']=描述符#挂上描述符
        启动方法=getattr(提供方,'启动',None) or getattr(提供方,'start',None)#中文方法优先
        跑=解开(启动方法(已解析))#等待提供方发布
        return 观察跑(自身._发射生命周期,名,取字段(请求,'parent'),跑)#观察并返回跑

    def _准备可续跑(自身,名,请求):#准备可续跑创建
        """解析一个提供方的分离可续跑创建贡献。"""
        提供方=自身._期望提供方(名)#解析提供方
        准备=getattr(提供方,'准备可续跑',None) or getattr(提供方,'prepareContinuable',None)#中文方法优先
        if 准备 is None:#缺少能力
            raise 子智能体错误(
                'subagent provider "'+取字段(提供方,'name')+'" does not support continuable children '
                +'(no prepareContinuable capability)',
                'UNSUPPORTED_CAPABILITY',
            )
        return 解开(准备(请求))#委托提供方

    def _期望提供方(自身,名):#必须存在的提供方
        """查找供派发用的提供方，否则大声失败。"""
        提供方=自身._提供方们.get(名)#按名查找
        if 提供方 is None:#缺席
            raise 子智能体错误('no subagent provider registered for "'+名+'"','NO_PROVIDER')#拒绝
        return 提供方#已登记提供方

    def _要求续跑(自身):#必须有管理器
        """解析可选的可续跑子智能体管理器，否则大声失败。"""
        if 自身._续跑 is None:#agents 未注入
            raise 子智能体错误(
                'continuable subagents require the agents service',
                'CONTINUATION_UNAVAILABLE',
            )
        return 自身._续跑#管理器

    def _观察激活(自身,提供方,子标识,父):#建造 Activation 观察者
        """为一次可续跑 Activation 的驻留纪元建造生命周期观察者。"""
        return 创建激活观察者(自身._发射生命周期,提供方,子标识,父)#经本服务发射器

    def _断言能力(自身,提供方,请求):#校验启动能力
        """拒绝提供方缺少的第一个被请求能力。"""
        能力=取字段(提供方,'capabilities') or 取字段(提供方,'能力') or {}#能力广告
        需要=[
            (取字段(请求,'outputSchema') is not None,'outputSchema'),#输出模式
            (取字段(请求,'maxDepth') is not None,'depthLimit'),#深度上限
            (取字段(请求,'toolFilter') is not None,'toolFilter'),#工具过滤
            (取字段(请求,'persona') is not None,'persona'),#人设
        ]
        for 当,帽 in 需要:#逐项检查
            if 当 and not 取字段(能力,帽):#请求了但提供方没有
                raise 子智能体错误(
                    'subagent provider "'+(取字段(提供方,'name') or 取字段(提供方,'名称') or '')+'" does not support the "'+帽+'" capability',
                    'UNSUPPORTED_CAPABILITY',
                )

默认=子智能体运行时#默认导出
default=子智能体运行时#Cordis 默认导出槽（不入 __all__）
