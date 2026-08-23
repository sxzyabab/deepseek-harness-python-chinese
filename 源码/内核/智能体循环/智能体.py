"""默认 Agent 驱动器：处理排队轮次与步骤边界输入。每次请求都从会话日志派生。"""
import threading
from ..智能体 import 收件箱,智能体事件,为组装构建上下文,下一轮,下一步
from ..llm import (
    块组装器,
    语言模型错误,
    创建助手消息,
    深冻结,
    错误链,
    标记循环请求,
    结构化克隆,
)
from ..作用域 import 创建作用域
from ..会话 import 归一请求头,请求头是否相等
from ..系统提示词 import 拼接上下文章节,渲染上下文章节,渲染提示词
from .运行时上下文 import 运行时上下文投影
from .工具调用 import 执行工具调用
from .辅助 import 取,解开,已中止,中止原因,中止控制器,已兑现,抛若中止
from ...依赖 import cordis#外部依赖胶水
承诺=cordis.工具.承诺#承诺

def 请求提议(头):
    """在插件提议下一次请求配置前去掉适配器派生值。"""
    if 取(头,'adapterDefaults') is None:
        return 取(头,'config')#无适配器默认则原样
    提议=dict(取(头,'config'))#拷贝配置
    默认=取(头,'adapterDefaults')#适配器默认
    if 取(默认,'reasoningEffort') is True:
        提议.pop('reasoningEffort',None)#去掉适配器力度
    if 取(默认,'maxTokens') is True:
        提议.pop('maxTokens',None)#去掉适配器 token 上限
    return 提议#返回提议

class 循环智能体:
    """驱动一个会话穿过轮次与步骤边界。"""
    def __init__(自身,循环上下文,标识,选项,会话):
        """构造驱动器。"""
        自身.循环上下文=循环上下文#循环上下文
        自身.id=标识#会话 id
        自身.options=选项 if 选项 is not None else {}#Agent 选项
        自身.session=会话#会话
        自身.派发=智能体事件(循环上下文,自身)#建融合派发器
        def 已插入(消息):
            """插入通知。"""
            自身.派发['发出']('agent/inbox/inserted',{'message':消息})#插入通知
        def 已丢弃(消息):
            """丢弃通知。"""
            自身.派发['发出']('agent/inbox/discarded',{'message':消息})#丢弃通知
        def 已领取(消息,轮次):
            """领取通知。"""
            自身.派发['发出']('agent/inbox/claimed',{'message':消息,'turn':轮次})#领取通知
        class 通知口:
            """收件箱在线通知口。"""
            已插入=staticmethod(已插入)#插入
            已丢弃=staticmethod(已丢弃)#丢弃
            已领取=staticmethod(已领取)#领取
        自身.inbox=收件箱(会话,通知口)#从日志建收件箱
        上次轮次=0#日志里最近轮次
        for 事件 in reversed(会话.events):
            if 取(事件,'type')=='turn/start':
                上次轮次=取(取(事件,'data'),'turn') or 0#最近轮次
                break#已找到
        自身.阶段={'kind':'idle','lastTurn':上次轮次}#从空闲开始
        自身.活动落定=已兑现()#当前活动落定
        自身.作用域=创建作用域(循环上下文,自身)#铸造作用域
        自身.ctx=自身.作用域.上下文.extend({'agent':自身})#挂上 Agent 关联
        自身.请求头已记=False#是否已记请求头
        自身.运行时上下文=运行时上下文投影(自身.ctx,会话)#恢复运行时上下文

    @property
    def 状态(自身):
        """公开状态。"""
        种类=自身.阶段['kind']#当前阶段
        return 'idle' if 种类=='idle' or 种类=='maintenance' else 'running'#维护也算空闲

    def 设阶段(自身,下一):
        """提交一个阶段并发表其对外可见的状态变迁。"""
        先前=自身.状态#先前公开状态
        自身.阶段=下一#写入阶段
        状态=自身.状态#新公开状态
        if 状态!=先前:
            自身.派发['发出']('agent/status',{'status':状态})#发出状态

    def 投递(自身,消息,目标,唤醒):
        """投递消息。"""
        阶段=自身.阶段#当前阶段
        中止后唤醒=唤醒 and 阶段['kind']!='idle' and 已中止(阶段['abort'].信号)#中止后唤醒
        实际目标=下一轮 if 中止后唤醒 else 目标#中止后改走下一轮
        自身.inbox.拼接(实际目标,float('inf'),0,[消息])#追加消息
        if 唤醒:
            自身.叫醒驱动器(中止后唤醒)#需要唤醒则叫醒

    def 后续(自身,输入):
        """后续提示。"""
        自身.投递(输入,下一轮,True)#下一轮并唤醒

    def 转向(自身,输入):
        """转向。"""
        自身.投递(输入,下一步,True)#下一步并唤醒

    def 注入(自身,输入):
        """注入上下文。"""
        自身.投递(输入,下一步,False)#下一步不唤醒

    def 取消(自身,原因,选项=None):
        """取消。"""
        if 选项 is None:
            选项={}#默认选项
        if not 取(选项,'keepInbox'):
            自身.inbox.清空()#清空
            if 自身.阶段['kind']!='idle':
                自身.阶段['wakeRequested']=False#清掉唤醒闩
        if 自身.阶段['kind']!='idle':
            自身.阶段['abort'].中止(原因)#中止活动

    def 跑维护(自身,任务):
        """跑维护。"""
        if 自身.阶段['kind']!='idle':
            raise Exception('agent "'+str(自身.id)+'" already has active work')#已有活动
        落定=承诺()#维护落定
        维护={
            'kind':'maintenance',#种类
            'abort':中止控制器(),#取消控制器
            'lastTurn':自身.阶段['lastTurn'],#保留上次轮次
            'wakeRequested':False,#尚无唤醒闩
        }#维护阶段
        自身.设阶段(维护)#进入维护
        自身.活动落定=落定#跟踪活动
        结果=承诺()#任务结果
        def 跑():
            """执行维护并收尾。"""
            try:
                结果.兑现(解开(任务(维护['abort'].信号)))#交给任务
            except BaseException as 错误:
                结果.拒绝(错误)#拒绝
            finally:
                自身.设阶段({'kind':'idle','lastTurn':维护['lastTurn']})#回到空闲
                if 维护['wakeRequested'] and 自身.inbox.有待处理:
                    自身.叫醒驱动器()#有闩且有工作则叫醒
                落定.兑现()#活动落定
        工作=threading.Thread(target=跑)#工作线程
        工作.daemon=True#不挡住退出
        工作.start()#启动
        return 结果#任务承诺

    def 叫醒驱动器(自身,中止后唤醒=False):
        """启动一个驱动器，或把它的唤醒闩在维护或已中止活动后面。"""
        if 自身.阶段['kind']!='idle':
            原因=中止原因(自身.阶段['abort'].信号)#取消原因
            原因种=取(原因,'kind') if 原因 is not None else None#取消种类
            if 原因种!='disposed' and (自身.阶段['kind']=='maintenance' or 中止后唤醒):
                自身.阶段['wakeRequested']=True#闩住
            return#不新开驱动器
        驱动器=承诺()#驱动器落定
        自身.活动落定=驱动器#跟踪活动
        自身.设阶段({
            'kind':'running',#种类
            'abort':中止控制器(),#取消控制器
            'turn':自身.阶段['lastTurn'],#从上次轮次继续
            'step':0,#步骤尚未开始
            'wakeRequested':False,#新控制器无闩
        })#进入运行
        循环上下文=自身.循环上下文#循环上下文
        def 跑驱动():
            """带发起者跑驱动器。"""
            try:
                解开(循环上下文.agents.带发起方(自身,自身.踢))#带发起者跑
                驱动器.兑现()#落定
            except BaseException as 错误:
                驱动器.拒绝(错误)#拒绝
        工作=threading.Thread(target=跑驱动)#驱动线程
        工作.daemon=True#不挡住退出
        工作.start()#启动

    def 等到空闲(自身):
        """等到空闲。"""
        while True:
            活动=自身.活动落定#当前活动
            解开(活动)#等待当前
            if 活动 is 自身.活动落定:
                return#没有被替换

    def 抛错误(自身,错误):
        """在在线边界报告一次失败，再保留它供驱动器收住。"""
        阶段=自身.阶段#当前阶段
        轮次=阶段['turn'] if 阶段['kind']=='running' else 阶段['lastTurn']#当前或上次轮次
        步骤=阶段['step'] if 阶段['kind']=='running' else 0#当前步骤
        自身.派发['发出']('agent/error',{'turn':轮次,'step':步骤,'error':错误})#发出错误
        raise 错误#再抛出

    def 踢(自身):
        """驱动循环。"""
        try:
            while 自身.轮次():
                pass#还有后续则继续
        except BaseException:
            pass#已报告的失败与取消在驱动器边界收住
        finally:
            if 自身.阶段['kind']=='running':
                轮次=自身.阶段['turn']#取出轮次
                有闩=自身.阶段['wakeRequested']#取出闩
                自身.设阶段({'kind':'idle','lastTurn':轮次})#回到空闲
                if 有闩 and 自身.inbox.有待处理:
                    自身.叫醒驱动器()#有闩且有工作则再叫醒

    def 预步骤(自身,目标,位置):
        """预步骤。"""
        if 自身.阶段['kind']!='running':
            raise Exception('agent "'+str(自身.id)+'": pre-step outside running phase')#必须在运行
        信号=自身.阶段['abort'].信号#轮次信号
        已领=自身.inbox.领取(目标,位置['turn'])#领取批次
        组装=解开(自身.循环上下文.systemPrompt.组装(为组装构建上下文(自身,信号)))#组装提示词
        抛若中止(信号)#组装后检查取消
        段落们=渲染上下文章节(组装)#渲染上下文段落
        快照=自身.运行时上下文.投影(拼接上下文章节(段落们),段落们)#投影快照
        def 默认进入(*位置参数):
            """瀑布内建进入。"""
            消息们=已领 if 快照 is None else list(已领)+[快照]#带上快照
            return {'kind':'enter','messages':消息们}#进入决定
        决定=解开(自身.派发['瀑布']('agent/pre-step',{
            'messages':已领,#已领消息
            'turn':位置['turn'],#轮次
            'step':位置['step'],#步骤
            'signal':信号,#信号
        },默认进入))#瀑布决定进入或拒绝
        抛若中止(信号)#瀑布后检查取消
        if 取(决定,'kind')=='reject':
            return 决定#拒绝
        带组装=dict(决定)#拷贝决定
        带组装['assembly']=组装#带上组装
        return 带组装#进入

    def 轮次(自身):
        """跑一轮。"""
        if 自身.阶段['kind']!='running':
            自身.抛错误(Exception('agent "'+str(自身.id)+'": turn without driver reservation'))#没有驱动器预留
        阶段=自身.阶段#运行阶段
        信号=阶段['abort'].信号#取消信号
        抛若中止(信号)#进入前检查
        轮次号=阶段['turn']+1#下一轮次号
        try:
            自身.session.追加('turn/start',{'turn':轮次号})#打开轮次
        except BaseException as 错误:
            自身.抛错误(错误)#报告并抛
        阶段['turn']=轮次号#记下打开轮次
        轮次结束=None#轮次结束原因
        目标=下一轮#首步吃下一轮
        try:
            while True:
                抛若中止(信号)#每步前检查
                步骤号=阶段['step']+1#下一步号
                决定=自身.预步骤(目标,{'turn':轮次号,'step':步骤号})#预步骤
                if 取(决定,'kind')=='reject':
                    轮次结束={'kind':'blocked'}#预步骤拒绝
                    return False#关闭且不再续
                消息们=取(决定,'messages') or []#进入消息
                if 轮次结束 is not None and len(消息们)==0:
                    break#已有结束且无消息则停
                if 阶段['step']==0 and len(消息们)==0:
                    轮次结束={'kind':'completed'}#当作完成
                    return False#关闭且不再续
                抛若中止(信号)#步骤开始前检查
                自身.session.追加('step/start',{'turn':轮次号,'step':步骤号})#打开步骤
                阶段['step']=步骤号#记下打开步骤
                try:
                    for 消息 in 消息们:
                        自身.session.追加('user/message',消息,{'surfaceOp':'append'})#追加到表面
                    步骤结束=自身.一步(取(决定,'assembly'))#跑一步
                    if 轮次结束 is None or 取(轮次结束,'kind')!='max-tokens':
                        轮次结束=步骤结束#更新结束原因
                finally:
                    自身.session.追加('step/end',{'turn':轮次号,'step':步骤号})#关闭步骤
                抛若中止(信号)#步骤后检查
                if 轮次结束 is not None and len(自身.inbox.下一步队列)==0:
                    解开(自身.派发['串行']('agent/turn-stopping',{'turn':轮次号,'signal':信号}))#征求停止边界
                    抛若中止(信号)#征求后检查
                if 轮次结束 is not None and len(自身.inbox.下一步队列)==0:
                    break#仍无下一步则关轮
                目标=下一步#后续步骤吃下一步
        except BaseException as 错误:
            if 已中止(信号):
                轮次结束={'kind':'aborted','reason':中止原因(信号)}#中止原因
                raise 错误#再抛出
            if isinstance(错误,语言模型错误):
                失败=错误.failure#保留其事实
            else:
                失败={'message':错误链(错误),'code':'UNKNOWN'}#压扁
            轮次结束={'kind':'error','error':失败}#出错
            自身.抛错误(错误)#报告并抛
        finally:
            try:
                自身.session.追加('turn/end',{'turn':轮次号,'reason':轮次结束})#关闭轮次
            except BaseException as 错误:
                自身.抛错误(错误)#报告并抛
        if not 自身.inbox.有待处理:
            return False#没有后续工作
        阶段['abort']=中止控制器()#新控制器
        阶段['wakeRequested']=False#清闩
        阶段['step']=0#步骤重置
        return True#再跑一轮

    def 一步(自身,组装):
        """跑一步。"""
        if 自身.阶段['kind']!='running':
            raise Exception('agent "'+str(自身.id)+'": step outside running phase')#必须在运行
        阶段=自身.阶段#运行阶段
        轮次号=阶段['turn']#轮次
        步骤号=阶段['step']#步骤
        信号=阶段['abort'].信号#信号
        抛若中止(信号)#进入前检查
        系统=渲染提示词(组装)#渲染系统提示
        while True:
            构建=自身.构建请求(轮次号,步骤号,取(组装,'tools'),系统,自身.session.派生消息(),信号)#构建冻结请求
            请求=构建['request']#冻结请求
            已准备调用=取(构建,'preparedCall')#已准备调用
            组装器=块组装器()#块组装器
            块序号们=[]#块序号
            if 已准备调用 is not None:
                流=已准备调用['stream'](请求)#绑定流
            else:
                流=自身.循环上下文.llm.流式(请求)#注册表流
            流=解开(流)#瀑布可能返回承诺
            抛若中止(信号)#流前检查
            for 块 in 流:
                抛若中止(信号)#每块检查
                块序号们.append(取(自身.session.追加('assistant/chunk',{'turn':轮次号,'step':步骤号,'chunk':块}),'seq'))#记下块
                组装器.push(块)#组装块
            抛若中止(信号)#流后检查
            结束=组装器.finish#结束原因
            结束种=取(结束,'kind')#结束种类
            if 结束种=='error' or 结束种=='aborted':
                def 默认动作(*位置参数):
                    """默认不恢复。"""
                    return None#终态
                动作=解开(自身.派发['瀑布']('agent/request-error',{
                    'turn':轮次号,#轮次
                    'step':步骤号,#步骤
                    'provider':取(请求,'provider'),#提供方
                    'failure':取(结束,'failure'),#失败事实
                    'retryPolicy':取(已准备调用,'retryPolicy') if 已准备调用 is not None else None,#重试策略
                    'signal':信号,#信号
                },默认动作))#征求恢复
                抛若中止(信号)#瀑布后检查
                if 取(动作,'kind')!='retry':
                    失败=取(结束,'failure')#失败事实
                    raise 语言模型错误(取(失败,'message'),取(失败,'code'),失败)#抛出失败
                continue#再请求
            来源={'provider':取(请求,'provider'),'model':取(请求,'model')}#来源
            if 组装器.replayState is not None:
                来源['replayState']=组装器.replayState#有回放状态则带
            消息=创建助手消息({
                'content':组装器.blocks(),#内容块
                'source':来源,#来源
            })#助手消息
            载荷={
                'turn':轮次号,#轮次
                'step':步骤号,#步骤
                'message':消息,#消息
            }#助手载荷
            if 组装器.usage is not None:
                载荷['usage']=组装器.usage#有用量则带
            自身.session.追加('assistant/message',载荷,{'surfaceOp':'append','sourceEventSeqs':块序号们})#追加助手消息
            if 结束种=='max-tokens':
                return {'kind':'max-tokens'}#碰到上限
            工具调用们=[块 for 块 in 取(消息,'content') if 取(块,'type')=='tool-call']#取出工具调用
            if len(工具调用们)==0:
                return {'kind':'completed'}#无调用则完成
            def 接受上下文(上下文块):
                """把结果上下文接到下一步收件箱。"""
                自身.inbox.拼接(下一步,len(自身.inbox.下一步队列),0,[上下文块])#追加上下文
            调度=解开(执行工具调用(自身.循环上下文,轮次号,步骤号,工具调用们,信号,接受上下文))#调度工具调用
            return {'kind':'completed'} if 取(调度,'concluded') else None#结束轮次或继续

    def 构建请求(自身,轮次号,步骤号,工具们,系统,边界消息,信号):
        """组装一次冻结请求，并把它绑到解析了其精确模型默认的适配器注册。"""
        会话=自身.session#取出会话
        已存头=会话.请求头()#已折叠请求头
        已存配置=取(已存头,'config') if 已存头 is not None else None#已存配置
        路由={'provider':取(自身.options,'provider') or '','model':取(自身.options,'model') or ''}#声明路由
        适配器默认=取(已存头,'adapterDefaults') if 已存头 is not None else None#适配器默认
        if (取(已存配置,'provider')==路由['provider']
            and 取(已存配置,'model')==路由['model']
            and 取(适配器默认,'reasoningEffort') is not True):
            推理力度=取(已存配置,'reasoningEffort')#同路由且非适配器默认才恢复力度
        else:
            推理力度=None#不恢复
        最大令牌=取(自身.options,'maxTokens')#选项里的 token 上限
        if 自身.请求头已记:
            种子=请求提议(已存头)#已记下则用提议
        else:
            种子=dict(路由)#声明路由
            if 推理力度 is not None:
                种子['reasoningEffort']=推理力度#有力度则带
            if 最大令牌 is not None:
                种子['maxTokens']=最大令牌#有上限则带
        种子配置=深冻结(结构化克隆(种子))#种子配置
        def 默认配置(*位置参数):
            """瀑布内建配置。"""
            return 种子配置#种子
        提议配置=解开(自身.派发['瀑布']('agent/request',{
            'turn':轮次号,#轮次
            'step':步骤号,#步骤
            'signal':信号,#信号
        },默认配置))#插件可替换配置
        抛若中止(信号)#瀑布后检查
        if (not 取(提议配置,'provider')) or (not 取(提议配置,'model')):
            raise Exception('agent "'+str(自身.id)+'" has no provider/model: set AgentOptions.provider and AgentOptions.model or supply both via the agent/request waterfall')#必须有提供方与模型
        已准备调用=None#已准备调用
        try:
            已准备调用=解开(自身.循环上下文.llm.准备调用(提议配置,信号))#准备调用
            配置=已准备调用['config']#取出配置
        except BaseException as 错误:
            if (not isinstance(错误,语言模型错误)) or 错误.code!='NO_ADAPTER':
                raise 错误#非缺适配器则抛
            配置=提议配置#缺适配器则用提议
        抛若中止(信号)#准备后检查
        头输入={'config':配置}#规范请求头输入
        if 已准备调用 is not None:
            头输入['adapterDefaults']=已准备调用['adapterDefaults']#有适配器默认则带
        if 系统:
            头输入['system']=系统#有系统提示则带
        if 工具们 is not None and len(工具们)>0:
            头输入['tools']=工具们#有工具则带
        头=归一请求头(头输入)#规范请求头
        基线=自身.session.请求头()#先前折叠头
        if not 自身.请求头已记:
            原因='initial' if 基线 is None else 'resume'#初始或恢复
            自身.session.追加('request/header',{'header':头,'reason':原因})#记下锚点
            自身.请求头已记=True#已记锚点
        elif 基线 is None or not 请求头是否相等(基线,头):
            自身.session.追加('request/header',{'header':头,'reason':'change'})#记下变更
        上下文窗口=None#上下文窗口
        if 已准备调用 is not None:
            上下文=取(已准备调用,'context')#已准备上下文
            上下文窗口=取(上下文,'contextWindow') if 上下文 is not None else None#窗口
        请求上下文={'provider':取(配置,'provider'),'model':取(配置,'model')}#路由元数据
        if 上下文窗口 is not None:
            请求上下文['contextWindow']=上下文窗口#有窗口则带
        先前上下文=会话.请求上下文()#先前路由元数据
        if (取(先前上下文,'provider')!=请求上下文['provider']
            or 取(先前上下文,'model')!=请求上下文['model']
            or 取(先前上下文,'contextWindow')!=取(请求上下文,'contextWindow')):
            会话.追加('request/context',请求上下文)#记下变更
        抛若中止(信号)#记下后检查
        请求=dict(取(头,'config'))#调用配置
        请求['messages']=边界消息#派生消息
        if 取(头,'system') is not None:
            请求['system']=取(头,'system')#有系统提示则带
        if 取(头,'tools') is not None:
            请求['tools']=取(头,'tools')#有工具则带
        请求['sessionId']=自身.session.id#会话 id
        请求['signal']=信号#信号
        请求=标记循环请求(深冻结(请求))#冻结并标记循环请求
        结果={'request':请求}#返回请求
        if 已准备调用 is not None:
            结果['preparedCall']=已准备调用#可选已准备调用
        return 结果#构建结果
