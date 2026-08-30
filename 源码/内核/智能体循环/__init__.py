"""具体 agent-loop 插件：铸造带作用域的循环智能体，经 agent/session 注册表发表它们，并拥有其有序拆除。"""
import uuid,threading#随机身份与工作线程
from ...依赖 import cordis#外部依赖胶水
from ...依赖 import schemastery#配置字段
字符串字段=schemastery.字符串字段#配置字段
整数字段=schemastery.整数字段#配置字段
列表字段=schemastery.列表字段#配置字段
服务=cordis.服务#服务基类
光纤状态=cordis.纤程状态#光纤/纤程状态
from ..智能体 import 发出智能体事件#按作用域发出 Agent 事件
from ...模型后端.llm import 错误链#把未知错误链成日志串
from ...配置.配置 import 设置命名空间#设置段安装与命名空间
from ..会话 import 会话标识,会话准备#会话 id 与准备句柄
from .智能体 import 循环智能体#具体循环驱动
from .常量 import 默认最大并行工具调用,安全整数上限#默认并行上限与安全整数
from .辅助 import (
    取,#读字段
    解开,#等待操作任务
    _是否thenable as 是否thenable,#可等待判定
    是否整数,#对齐 Number.isInteger
    是否安全整数,#对齐 Number.isSafeInteger
    已中止,#信号是否已中止
    中止原因,#取出中止原因
    听中止,#登记 abort 回调
    摘中止,#去掉 abort 回调
    中止控制器,#发出中止
    中止信号,#可监听取消通道
    与中止赛跑,#等待或中止
    与中止赛跑调用,#启动并与中止赛跑
    释放准备,#释放会话准备
    包中止错误,#包装创建中止
    全部并发,#并发等全部
    赛跑,#最先结算胜出
    操作任务,#单次异步结果
)

__all__=(#仅中文公开名；Cordis 槽英文别名不入表
    '工厂所有权','穿透配置','已发表句柄','已准备智能体',
    '解析并行上限','断言智能体选项','叠启动器身份','校验配置智能体','解开作用域',
    '智能体循环设置命名空间','智能体循环设置模式',
    '智能体循环','默认',
)#公开面结束

生成UUID=uuid.uuid4#随机 UUID
不活动状态=frozenset((光纤状态.卸载中,光纤状态.已释放,光纤状态.失败))#不能拥有或服务新生命周期的光纤状态
配置智能体身份键='configuredAgentIdentities'#启动器身份表键
智能体循环设置命名空间=设置命名空间('agent-loop')#agent-loop 设置命名空间
智能体循环设置模式={
    'maxParallelToolCalls':整数字段(最小=1,默认值=默认最大并行工具调用),#正整数，默认常量
}#用户设置模式

class 工厂所有权:
    """工厂级所有权：在线 Agent 拆除，外加配置启动工作。"""
    def __init__(自身,光纤):
        """记下所属光纤。"""
        自身.光纤=光纤#所属光纤
        自身.接受中=True#是否仍接受新工作
        自身.拆除控制器=中止控制器()#工厂拆除信号
        自身.失活=操作任务()#拆除开始时兑现
        自身.在线智能体=set()#在线 Agent 拆除器
        自身.启动任务=set()#配置启动任务

    @property
    def 信号(自身):
        """工厂拆除开始时中止。"""
        return 自身.拆除控制器.信号#AbortController 的信号

    def 是否活动(自身):
        """工厂是否仍可服务。"""
        return 自身.接受中 and 自身.光纤.state not in 不活动状态#仍接受且光纤活动

    def 跟踪(自身,拆除):
        """跟踪一个在线 Agent 的共享拆除，直到它跑完。"""
        自身.在线智能体.add(拆除)#加入集合
        def 忘掉():
            """从工厂集合忘掉。"""
            自身.在线智能体.discard(拆除)#删除
        return 忘掉#返回忘记闭包

    def 跟踪启动(自身,任务):
        """加入在 Agent 存在之前就开始的配置启动工作。"""
        自身.启动任务.add(任务)#加入集合
        def 忘掉():
            """结算后忘记。"""
            自身.启动任务.discard(任务)#删掉
        def 收尾():
            """成败都忘掉。"""
            try:
                解开(任务)#等待
            except BaseException:
                pass#失败也忘掉
            忘掉()#从集合删掉
        工作=threading.Thread(target=收尾)#收尾线程
        工作.daemon=True#不挡住退出
        工作.start()#启动

    def 跟踪续体(自身,任务):
        """加入一次公开 create/resume 续体；工厂 dispose 等待它落定。"""
        吞=操作任务()#吞结果只等落定
        def 收():
            """吞掉成败。"""
            try:
                解开(任务)#等待
            except BaseException:
                pass#吞失败
            吞.兑现()#落定
        工作=threading.Thread(target=收)#收尾线程
        工作.daemon=True#不挡住退出
        工作.start()#启动
        自身.跟踪启动(吞)#登记启动任务

    def 活动期内等待(自身,任务):
        """等待任务兑现，或在工厂拆除开始时停止等待。"""
        赛跑([任务,自身.失活])#任务或拆除，先到先停

    def 拆除(自身):
        """拆除工厂。"""
        自身.接受中=False#不再接受新工作
        自身.拆除控制器.中止(Exception('agent loop is not active'))#中止进行中的等待
        自身.失活.兑现()#放开活动期内等待
        任务们=[]#并行排空
        for 拆除器 in list(自身.在线智能体):
            任务们.append(拆除器())#每个在线 Agent
        for 启动 in list(自身.启动任务):
            任务们.append(启动)#每个启动任务
        全部并发(任务们)#并行排空

class 穿透配置:
    """已解析配置，并行上限每次从设置源读取。"""
    def __init__(自身,原始,条目们,读上限):
        """记下原始字段、叠后条目与上限读取。"""
        自身._原始=dict(原始) if isinstance(原始,dict) else {}#原始配置
        自身.智能体们=条目们#叠后条目
        自身._读上限=读上限#设置源读取

    @property
    def 最大并行工具调用(自身):
        """穿透读并行上限。"""
        return 自身._读上限()#当前设置源

    def __getattr__(自身,名):
        """其余字段从原始配置读。"""
        if 名 in 自身._原始:
            return 自身._原始[名]#原始字段
        raise AttributeError(名)#没有该字段

class 已发表句柄:
    """已进入注册表的 Agent 与其记忆化拆除。"""
    def __init__(自身,智能体,拆除):
        """记下主体与拆除。"""
        自身.智能体=智能体#循环驱动
        自身.拆除=拆除#记忆化拆除

class 已准备智能体:
    """已准备、尚未发表的 Agent 资源。"""
    def __init__(自身,智能体,信号,发表,拆除):
        """记下驱动、融合信号、发表与拆除。"""
        自身.智能体=智能体#循环驱动
        自身.信号=信号#融合中止信号
        自身.发表=发表#发表
        自身.拆除=拆除#记忆化拆除

def 解析并行上限(值):
    """在所属配置边界解析部署级调度上限。"""
    上限=默认最大并行工具调用 if 值 is None else 值#缺省用默认
    if (not 是否整数(上限)) or 上限<1:
        raise Exception('maxParallelToolCalls must be a positive integer')#非法上限
    return 上限#已校验上限

def 断言智能体选项(选项):
    """拒绝无法在请求线上精确表示的输出 token 上限。"""
    最大令牌=取(选项,'maxTokens')#可选上限
    if 最大令牌 is not None and ((not 是否安全整数(最大令牌)) or 最大令牌<=0):
        raise TypeError('agent maxTokens must be a positive safe integer')#非法 maxTokens

def 叠启动器身份(条目们,身份表):
    """把启动器拥有的身份叠到配置 Agent 上。"""
    if 身份表 is None:
        return 条目们#无启动器表则原样
    结果=[]#叠后条目
    for 条目 in 条目们:
        配置id=取(条目,'id')#配置标签
        身份=取(身份表,配置id)#该配置 id 的启动器身份
        if 身份 is None:
            结果.append(条目)#未点名则保留
            continue#下一条
        其余={}#剥掉两个身份键
        if isinstance(条目,dict):
            for 键 in 条目:
                if 键!='sessionId' and 键!='resumeSessionId':
                    其余[键]=条目[键]#保留其余
        else:
            其余=dict(条目.__dict__)#对象字段
            其余.pop('sessionId',None)#剥掉精确 id
            其余.pop('resumeSessionId',None)#剥掉恢复 id
        if 取(身份,'resume'):
            其余['resumeSessionId']=取(身份,'id')#只留 resumeSessionId
        else:
            其余['sessionId']=取(身份,'id')#只留 sessionId
        结果.append(其余)#叠后条目
    return 结果#已应用启动器身份

def 校验配置智能体(条目们):
    """在任何配置 Agent 启动之前拒绝自洽的身份冲突。"""
    精确身份={}#精确身份 → 先到的配置 id
    for 条目 in 条目们:
        配置id=取(条目,'id')#配置标签
        会话号=取(条目,'sessionId')#精确会话 id
        恢复号=取(条目,'resumeSessionId')#恢复会话 id
        有恢复=恢复号 is not None and 恢复号!=''#给了非空 resume
        if 会话号 is not None and 有恢复:
            raise Exception('agent "'+str(配置id)+'": sessionId and resumeSessionId are mutually exclusive')#互斥
        精确=恢复号 if 有恢复 else 会话号#取精确身份
        if 精确 is None:
            continue#无精确身份则跳过
        先到=精确身份.get(精确)#是否已被占用
        if 先到 is not None:
            raise Exception('agents "'+str(先到)+'" and "'+str(配置id)+'" use duplicate exact session identity "'+str(精确)+'"')#重复
        精确身份[精确]=配置id#记下先到者

def 解开作用域(作用域对象):
    """解开 Agent 作用域。"""
    解开(作用域对象.拆除())#等待静止拆除

class 智能体循环(服务):
    """具体 Agent 工厂与驱动服务。"""
    注入=['agents','sessions','llm','tools','systemPrompt']#依赖注册表、会话、LLM、工具、提示词
    inject=注入#Cordis 依赖声明槽
    配置={
        'maxParallelToolCalls':整数字段(最小=1,默认值=默认最大并行工具调用),#并行上限
        'agents':列表字段(({
            'id':字符串字段(可空=False),#配置标签
            'sessionId':字符串字段(最小长度=1),#可选精确会话 id
            'provider':字符串字段(),#模型提供方
            'model':字符串字段(),#模型名
            'maxTokens':整数字段(最小=1,最大=安全整数上限),#输出 token 上限
            'cwd':字符串字段(),#工作目录
            'resumeSessionId':字符串字段(),#可选恢复会话 id
        }),默认值=[]),#默认无条目
    }#插件配置模式
    Config=配置#Cordis Config 槽

    def __init__(自身,ctx,配置):
        """构造工厂。"""
        super().__init__(ctx,'agentLoop')#注册为 agentLoop
        if 配置 is None:
            配置={}#缺省空配置
        入口={'maxParallelToolCalls':解析并行上限(取(配置,'maxParallelToolCalls'))}#设置段初值
        源=lambda:入口#当前设置源
        def 读上限():
            """穿透读并行上限。"""
            return 取(源(),'maxParallelToolCalls')#当前设置源
        def 校验(值):
            """校验新上限。"""
            解析并行上限(取(值,'maxParallelToolCalls'))#拒绝非法上限
        def 设源(当前):
            """切换设置源。"""
            nonlocal 源#修改外层
            源=当前#之后的 getter 读这里
        def 变更():
            """上限没有派生物。"""
            return#无派生，空操作
        条目们=叠启动器身份(取(配置,'agents') or [],ctx.get(配置智能体身份键))#叠启动器身份
        自身.配置=穿透配置(配置,条目们,读上限)#已解析配置
        安装设置段落(ctx,智能体循环设置命名空间,智能体循环设置模式,入口,{
            'validate':校验,#校验新上限
            'setSource':设源,#切换设置源
            'onChange':变更,#无派生
        })#安装用户设置段
        校验配置智能体(自身.配置.智能体们)#加载时拒绝身份冲突
        自身.所有权=工厂所有权(ctx.fiber)#铸造所有权账本
        自身.运行时={'ctx':ctx}#保住未追踪上下文
        def 拆除工厂():
            """fiber 拆除时排空所有权。"""
            def 释放():
                """排空所有权。"""
                自身.所有权.拆除()#拆除工厂
            return 释放#拆除器
        ctx.effect(拆除工厂,'agentLoop.transactions()')#fiber 拆除时排空所有权
        def 登记工厂():
            """登记为本工厂。"""
            return ctx.agents.设工厂(自身)#登记
        ctx.effect(登记工厂,'agentLoop.setFactory()')#登记为本工厂
        def 提供方变量(上下文):
            """提示词变量：提供方。"""
            智能体=取(上下文,'agent')#当前 Agent
            if 智能体 is None:
                return None#无 Agent
            return 取(取(智能体,'options'),'provider')#提供方
        def 模型变量(上下文):
            """提示词变量：模型。"""
            智能体=取(上下文,'agent')#当前 Agent
            if 智能体 is None:
                return None#无 Agent
            return 取(取(智能体,'options'),'model')#模型
        def 工作目录变量(上下文):
            """提示词变量：工作目录。"""
            智能体=取(上下文,'agent')#当前 Agent
            if 智能体 is None:
                return None#无 Agent
            return 取(取(智能体.session,'header'),'cwd')#工作目录
        ctx.systemPrompt.变量('provider',提供方变量)#提示词变量：提供方
        ctx.systemPrompt.变量('model',模型变量)#提示词变量：模型
        ctx.systemPrompt.变量('cwd',工作目录变量)#提示词变量：工作目录
        for 条目 in 自身.配置.智能体们:
            配置id=取(条目,'id')#配置标签
            会话号=取(条目,'sessionId')#精确会话 id
            工作目录=取(条目,'cwd')#工作目录
            恢复号=取(条目,'resumeSessionId')#恢复会话 id
            选项={}#循环选项
            if isinstance(条目,dict):
                for 键 in 条目:
                    if 键 not in ('id','sessionId','cwd','resumeSessionId'):
                        选项[键]=条目[键]#其余为循环选项
            元={} if 工作目录 is None else {'cwd':工作目录}#可选工作区
            if 恢复号 is None or 恢复号=='':
                配置标识=会话号 if 会话号 is not None else 会话标识(str(配置id)+'-session-'+str(生成UUID()))#精确 id 或新鲜组合 id
                持久化=None if 会话号 is None else ctx.get('sessionPersistence')#有精确 id 才找持久化
                if 持久化 is None:
                    自身.创建(配置标识,选项,元)#新鲜创建
                else:
                    启动=操作任务()#启动任务
                    def 跑启动(持久化句柄=持久化,标识=配置标识,循环选项=选项,元数据=元,标签=配置id):
                        """再挂载恢复或首次创建。"""
                        try:
                            自身.恢复或首次创建(ctx,持久化句柄,标识,循环选项,元数据)#启动
                            启动.兑现()#成功
                        except BaseException as 错误:
                            自身.报告配置启动失败(标签,'restore',标识,错误)#报告 restore 失败
                            启动.兑现()#catch 后仍落定
                    工作=threading.Thread(target=跑启动)#启动线程
                    工作.daemon=True#不挡住退出
                    工作.start()#启动
                    自身.所有权.跟踪启动(启动)#登记启动任务
                continue#下一条
            def 恢复副作用(标签=配置id,恢复会话号=恢复号,循环选项=选项):
                """恢复路径：等 sessionPersistence 再注入。"""
                def 子回调(子上下文,*位置参数):
                    """经显式句柄恢复。"""
                    def 跑恢复():
                        """恢复并收住失败。"""
                        try:
                            解开(自身.经持久化恢复(ctx,子上下文.sessionPersistence,{
                                'resumeSessionId':恢复会话号,#要恢复的会话
                                'agentOptions':循环选项,#循环选项
                            }))#经显式句柄恢复
                        except BaseException as 错误:
                            自身.报告配置启动失败(标签,'resume',恢复会话号,错误)#报告 resume 失败
                    恢复线程=threading.Thread(target=跑恢复)#恢复线程
                    恢复线程.daemon=True#不挡住退出
                    恢复线程.start()#启动
                光纤=ctx.inject(['sessionPersistence'],子回调)#注入持久化
                return 光纤.dispose#effect 拆除即卸注入
            ctx.effect(恢复副作用,'agentLoop.resume('+str(配置id)+')')#effect 名

    def 报告配置启动失败(自身,配置id,动作,会话号,错误):
        """向身份绑定的消费方报告一次被收住的声明式启动失败。"""
        if not 自身.所有权.是否活动():
            return#工厂已拆除则抑制
        自身.ctx.logger.warn('agent "'+str(配置id)+'": config-driven '+动作+' of "'+str(会话号)+'" failed: '+错误链(错误))#记警告
        参数=['agent-loop/config-start-failed',{'sessionId':会话号,'error':错误}]#事件名与载荷
        for 回调 in 自身.ctx.events.dispatch('emit',参数):
            try:
                返回=回调(*参数)#调用
                if 是否thenable(返回):
                    def 观察(返回值=返回,标签=配置id):
                        """收住 Promise 拒绝。"""
                        try:
                            解开(返回值)#等待
                        except BaseException as 监听错误:
                            自身.ctx.logger.warn('agent "'+str(标签)+'": config-start-failed listener rejected: '+错误链(监听错误))#记拒绝
                    观察线程=threading.Thread(target=观察)#后台观察
                    观察线程.daemon=True#不挡住退出
                    观察线程.start()#启动
            except BaseException as 监听错误:
                自身.ctx.logger.warn('agent "'+str(配置id)+'": config-start-failed listener threw: '+错误链(监听错误))#记抛错

    def 恢复或首次创建(自身,所有者上下文,持久化,会话号,智能体选项,元):
        """再挂载时恢复已物化的精确配置身份，或在首次使用时创建它。"""
        自身.等待同身份腾出(所有者上下文,会话号)#等同 id 排空
        if not 自身.所有权.是否活动():
            return#拆除则停
        try:
            解开(自身.经持久化恢复(所有者上下文,持久化,{
                'resumeSessionId':会话号,#按精确 id 恢复
                'agentOptions':智能体选项,#循环选项
            }))#按精确 id 恢复
            return#恢复成功
        except BaseException as 错误:
            if not 自身.所有权.是否活动():
                return#拆除则停
            存在=False#产物是否仍在
            for 头 in 解开(持久化.list()):
                if 取(头,'id')==会话号:
                    存在=True#仍在
                    break#已找到
            if 存在:
                raise 错误#在则原错上抛
        自身.创建(会话号,智能体选项,元)#缺席则首次创建

    def 等待同身份腾出(自身,所有者上下文,会话号):
        """等待一个正在排空的同 id 生命周期完成注册表拆除。"""
        if 所有者上下文.agents.获取(会话号) is None and 所有者上下文.sessions.获取(会话号) is None:
            return#两边都空则无需等
        已腾出=操作任务()#腾出时兑现
        def 检查(*位置参数):
            """检查是否已腾出。"""
            if 所有者上下文.agents.获取(会话号) is None and 所有者上下文.sessions.获取(会话号) is None:
                已腾出.兑现()#兑现
        卸智能体=所有者上下文.on('agent/disposed',检查)#Agent 拆除时再查
        卸会话=所有者上下文.on('session/disposed',检查)#会话拆除时再查
        try:
            检查()#可能已经空了
            自身.所有权.活动期内等待(已腾出)#活动期内等腾出
        finally:
            卸智能体()#摘掉 Agent 监听
            卸会话()#摘掉会话监听

    def 准备(自身,所有者上下文,标识,选项,会话,调用方信号=None):
        """为一个新 Agent 构造驱动、作用域和一次记忆化反向拆除。"""
        断言智能体选项(选项)#校验选项
        所有者上下文.fiber.assertActive()#所有者光纤必须活动
        if not 自身.所有权.是否活动():
            raise Exception('agent loop is not active')#工厂必须活动
        if 已中止(调用方信号):
            raise 包中止错误(标识,中止原因(调用方信号))#调用方已取消
        循环上下文=自身.运行时['ctx']#未追踪运行时上下文
        融合=中止控制器()#融合中止
        def 调用方中止(*位置参数):
            """调用方取消。"""
            融合.中止(包中止错误(标识,中止原因(调用方信号)))#包装原因
        def 工厂拆除(*位置参数):
            """工厂拆除。"""
            融合.中止(中止原因(自身.所有权.信号))#工厂原因
        听中止(调用方信号,调用方中止)#听调用方
        听中止(自身.所有权.信号,工厂拆除)#听工厂
        机器=[None]#循环驱动，铸造前为空
        脱离会话=[None]#会话脱离器
        脱离智能体=[None]#Agent 脱离器
        拆除中=[None]#记忆化拆除
        驱动就绪=操作任务()#驱动已赋值或失败时兑现
        取消跟随所有者=[None]#所有者 effect 拆除器
        忘掉=[None]#从工厂集合忘掉
        def 拆除(所有者触发=False):
            """反向拆除，记忆化。"""
            if 拆除中[0] is not None:
                return 拆除中[0]#已有一次拆除
            任务=操作任务()#本次拆除
            拆除中[0]=任务#先挂上供竞态等待
            def 跑拆除():
                """停状态机、离开注册表、解开作用域。"""
                try:
                    融合.中止(Exception('agent "'+str(标识)+'" lifecycle disposed'))#结束设置等待
                    摘中止(调用方信号,调用方中止)#摘掉调用方监听
                    摘中止(自身.所有权.信号,工厂拆除)#摘掉工厂监听
                    try:
                        if 机器[0] is None:
                            解开(驱动就绪)#等铸造完成或失败
                        驱动=机器[0]#已铸造驱动
                        if 驱动 is not None:
                            驱动.取消({'kind':'disposed'})#按拆除取消
                            解开(驱动.等到空闲())#等到空闲
                            解开作用域(驱动.作用域)#解开作用域
                    finally:
                        try:
                            if 脱离智能体[0] is not None:
                                脱离智能体[0]()#离开 Agent 注册表
                            if 脱离会话[0] is not None:
                                脱离会话[0]()#离开会话存储
                        finally:
                            if 忘掉[0] is not None:
                                忘掉[0]()#从工厂集合忘掉
                            if (not 所有者触发) and 取消跟随所有者[0] is not None:
                                解开(取消跟随所有者[0]())#非所有者触发则卸所有者 effect
                    任务.兑现()#拆除完成
                except BaseException as 错误:
                    任务.拒绝(错误)#拆除失败
            拆除线程=threading.Thread(target=跑拆除)#拆除线程
            拆除线程.daemon=True#不挡住退出
            拆除线程.start()#启动
            return 任务#记忆化拆除
        忘掉[0]=自身.所有权.跟踪(拆除)#发表前就向工厂登记拆除
        try:
            def 所有者生命周期():
                """所有者拆除拥有同一静默边界。"""
                def 释放():
                    """所有者拆除。"""
                    if 拆除中[0] is not None:
                        return#已在拆除则不再重入
                    融合.中止(Exception('agent "'+str(标识)+'" setup aborted: owner disposed during setup'))#设置中所有者没了
                    return 拆除(True)#所有者触发的拆除
                return 释放#拆除器
            取消跟随所有者[0]=所有者上下文.effect(所有者生命周期,'agentLoop.lifecycle('+str(标识)+')')#effect 名
        except BaseException as 错误:
            忘掉[0]()#忘掉工厂登记
            摘中止(调用方信号,调用方中止)#摘掉调用方监听
            摘中止(自身.所有权.信号,工厂拆除)#摘掉工厂监听
            raise 错误#原错上抛
        def 断言仍活():
            """断言融合信号尚未中止。"""
            if not 已中止(融合.信号):
                return#仍活着
            原因=中止原因(融合.信号)#中止原因
            if isinstance(原因,BaseException):
                raise 原因#抛原因
            raise Exception(str(原因))#非异常则包装
        try:
            驱动=循环智能体(循环上下文,标识,选项,会话)#铸造驱动
            机器[0]=驱动#记下驱动
            驱动就绪.兑现()#铸造完成
            断言仍活()#铸造后仍须活着
            def 发表(来源):
                """进入注册表、宣布、通知 session-start。"""
                断言仍活()#进入前须活着
                脱离会话[0]=驱动.ctx.sessions.进入(会话)#进入会话存储
                脱离智能体[0]=循环上下文.agents.进入(驱动,所有者上下文.agent)#进入 Agent 注册表
                驱动.ctx.sessions.宣布(会话)#宣布会话
                断言仍活()#宣布会话后须活着
                循环上下文.agents.宣布(驱动)#宣布 Agent
                断言仍活()#宣布 Agent 后须活着
                发出智能体事件(循环上下文,驱动,'agent/session-start',{'source':来源})#发出 session-start
                断言仍活()#发出后仍须活着
                return 已发表句柄(驱动,拆除)#已发表句柄
            return 已准备智能体(驱动,融合.信号,发表,拆除)#已准备面
        except BaseException as 错误:
            驱动就绪.兑现()#放开拆除里对铸造的等待
            拆除()#回滚
            raise 错误#原错上抛

    def 创建(自身,标识,选项=None,元=None):
        """在调用方供给的单一身份下创建 Agent 与会话，由访问光纤拥有。"""
        if 选项 is None:
            选项={}#默认选项
        if 元 is None:
            元={}#默认元数据
        准备=会话准备.创建(自身.运行时['ctx'].sessions.准备(标识,{'meta':元}))#准备会话
        try:
            已准备=自身.准备(自身.ctx,标识,选项,准备.会话)#准备 Agent
            try:
                return 已准备.发表('startup').智能体#启动来源
            except BaseException as 错误:
                已准备.拆除()#回滚
                raise 错误#原错上抛
        finally:
            准备.拆除()#释放准备

    def 创建智能体(自身,所有者上下文,选项):
        """在调用方供给的会话 id 上创建被拥有的 Agent。"""
        准备选项={}#准备选项
        种子=取(选项,'seed')#可选种子
        if 种子 is not None:
            准备选项['seed']=种子#可选种子
        元=取(选项,'meta')#可选元数据
        if 元 is not None:
            准备选项['meta']=元#可选元数据
        准备=会话准备.创建(自身.运行时['ctx'].sessions.准备(取(选项,'sessionId'),准备选项))#准备会话
        已发表=自身.设置并发表(
            所有者上下文,#所有者
            取(选项,'sessionId'),#共享身份
            准备,#已准备会话
            取(选项,'agentOptions') or {},#循环选项
            取(选项,'setup'),#可选设置
            取(选项,'signal'),#可选取消
            'startup',#启动来源
        )#设置并发表
        自身.所有权.跟踪续体(已发表)#工厂拆除等待本续体
        return 已发表#已发表句柄

    def 设置并发表(自身,所有者上下文,标识,准备,智能体选项,设置,信号,来源):
        """在已获取的 Session 周围准备一个 Agent，跑设置，再发表它。"""
        任务=操作任务()#本续体
        def 跑():
            """设置并发表。"""
            try:
                会话=准备.会话#已构造会话
                已准备=自身.准备(所有者上下文,标识,智能体选项,会话,信号)#准备 Agent
                try:
                    if 设置 is not None:
                        设置提交=与中止赛跑(设置(已准备.智能体.ctx),已准备.信号,标识)#等待设置
                    else:
                        设置提交=None#无设置
                    if 设置提交 is not None:
                        提交=取(设置提交,'commit')#可选提交
                        if 提交 is not None:
                            提交()#发表直前同步提交
                    任务.兑现(已准备.发表(来源))#进入注册表并宣布
                except BaseException as 错误:
                    解开(已准备.拆除())#回滚
                    raise 错误#原错上抛
            except BaseException as 错误:
                任务.拒绝(错误)#失败
            finally:
                释放准备(准备)#作用域结束时释放准备
        工作=threading.Thread(target=跑)#工作线程
        工作.daemon=True#不挡住退出
        工作.start()#启动
        return 任务#已发表句柄承诺

    def 恢复(自身,所有者上下文,选项):
        """从已配置的持久化服务恢复一个被拥有的 Agent。"""
        持久化=自身.运行时['ctx'].get('sessionPersistence')#取持久化服务
        if 持久化 is None:
            raise Exception('cannot resume: session persistence is not configured (load a dsh-session-persistence backend)')#无法恢复
        return 自身.经持久化恢复(所有者上下文,持久化,选项)#经显式句柄恢复

    def 经持久化恢复(自身,所有者上下文,持久化,选项):
        """经延迟配置路径使用的显式持久化句柄恢复。"""
        标识=取(选项,'resumeSessionId')#要加载的会话 id
        已发表=操作任务()#加载、设置、发表
        def 跑():
            """加载、设置、发表。"""
            准备=None#加载得到的准备
            所有者中止=中止控制器()#所有者卸载信号
            def 加载期所有者():
                """所有者拆除。"""
                def 释放():
                    """设置中所有者没了。"""
                    所有者中止.中止(Exception('agent "'+str(标识)+'" setup aborted: owner disposed during setup'))#设置中所有者没了
                return 释放#拆除器
            取消跟随=所有者上下文.effect(加载期所有者,'agentLoop.resume-load('+str(标识)+')')#effect 名
            信号们=[]#融合三路中止
            调用方信号=取(选项,'signal')#可选调用方信号
            if 调用方信号 is not None:
                信号们.append(调用方信号)#可选调用方信号
            信号们.append(所有者中止.信号)#所有者卸载
            信号们.append(自身.所有权.信号)#工厂拆除
            融合=中止信号.任一(信号们)#融合三路中止
            try:
                try:
                    准备=与中止赛跑调用(
                        lambda:持久化.prepare(标识,融合),#后端 prepare
                        融合,#融合信号
                        标识,#身份
                        释放准备,#取消后仍兑现则释放
                    )#可中止加载
                finally:
                    解开(取消跟随())#卸加载期所有者 effect
                所有者上下文.fiber.assertActive()#加载后所有者仍须活动
                if not 自身.所有权.是否活动():
                    raise Exception('agent loop is not active')#工厂仍须活动
                句柄=解开(自身.设置并发表(
                    所有者上下文,#所有者
                    标识,#身份
                    准备,#已加载会话
                    取(选项,'agentOptions') or {},#循环选项
                    取(选项,'setup'),#可选设置
                    取(选项,'signal'),#调用方取消
                    'resume',#恢复来源
                ))#设置并发表
                已发表.兑现(句柄)#已发表句柄
            except BaseException as 错误:
                已发表.拒绝(错误)#失败
            finally:
                释放准备(准备)#setupAndPublish 的 using 已接管则此处为空操作
        工作=threading.Thread(target=跑)#工作线程
        工作.daemon=True#不挡住退出
        工作.start()#启动
        自身.所有权.跟踪续体(已发表)#工厂拆除等待本续体
        return 已发表#已发表句柄

默认=智能体循环#默认导出具体工厂
default=智能体循环#Cordis 默认导出槽（不入 __all__）
