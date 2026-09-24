import uuid,weakref,threading#随机uuid、弱谱系与后台结算线程
from concurrent.futures import Future as 原生结果#单次操作结果
from typing import Literal,NotRequired,TypedDict#字面量、可选字段与结构类型
from ...依赖 import cordis#外部依赖胶水
聚合错误=cordis.聚合错误#多失败聚合
from ...模型后端.llm import 创建用户消息,截上下文摘要,错误链#用户消息、摘要与错误链
from ...内核.会话 import 会话标识#会话id品牌
from .描述符 import 折叠子智能体描述符,快照子智能体描述符#描述符折叠与快照
from .子体 import (#子体组合零件
    追加委托策略覆盖,#追加委托策略覆盖
    应用子体组合,#应用子体组合
    捕获委托策略覆盖,#捕获委托策略覆盖
    子会话元数据,#子会话元数据
    解析子智能体选项,#解析子智能体选项
    解析子深度,#解析子深度
)#子体组合零件结束
from .深度 import 断言子智能体最大深度#导入深度上限断言
from .错误 import 子智能体错误#导入子智能体错误
from .目录 import 建立目录子体#父拥有目录追加

class 子智能体中止错误(子智能体错误):
    """调用方取消。"""

class 操作任务:
    """单次操作的 Future 包装，只留 等待。"""
    def __init__(自身):
        """构造未决任务。"""
        自身._原生结果=原生结果()#底层 Future

    def 兑现(自身,值=None):
        """成功结算。"""
        if not 自身._原生结果.done():#尚未结算
            自身._原生结果.set_result(值)#写入结果
        return 值#返回兑现值

    def 拒绝(自身,错误):
        """失败结算。"""
        if not 自身._原生结果.done():#尚未结算
            if isinstance(错误,BaseException):#已是异常
                自身._原生结果.set_exception(错误)#原样拒绝
            else:#非异常
                自身._原生结果.set_exception(子智能体错误(str(错误)))#包装拒绝

    def 等待(自身,超时=None):
        """阻塞等到结算。"""
        return 自身._原生结果.result(timeout=超时)#取结果或抛错

def 已中止(信号):
    """信号是否已中止。无信号视为未中止。信号为中止通道（Event 形态）。"""
    if 信号 is None:#无信号
        return False#未中止
    return 信号.is_set()#置位即中止

def 若已中止则抛出(信号):
    """已中止则抛出本包中止异常。原因由异常对象承载。"""
    if not 已中止(信号):#未中止
        return#继续
    原因=getattr(信号,'_异常',None)#承载的异常
    if isinstance(原因,BaseException):#已是异常
        raise 原因#原样
    raise 子智能体中止错误('已中止')#默认

class 协调者消息来源(TypedDict):
    """模型协调者对其某个子体跟进的归属。"""
    kind:Literal['coordinator']#协调者种类
    form:Literal['relay']#中继形态
    senderSessionId:str#其工具调用产出该跟进的智能体会话 id

class 子智能体报告消息来源(TypedDict):#可续跑子体显式父报告的耐久归属
    kind:Literal['subagent-report']#报告种类
    form:Literal['relay']#中继形态
    senderSessionId:str#报告子体的会话 id

class 子智能体结算消息来源(TypedDict):#运行时自己对可续跑子体结算的叙述的耐久归属；故意与报告不同种类
    kind:Literal['subagent-settled']#结算种类
    form:Literal['notice']#通知形态
    summary:str#子体如何结束的一行叙述
    senderSessionId:str#结算子体的会话 id

子智能体报告投递=Literal['quiet','wakeup']#安静注入或唤醒

class 子智能体报告选项(TypedDict):#一个可续跑子体向其直接父报告的选项
    delivery:子智能体报告投递#已解析的父调度策略
    signal:object#调用方取消（上游类型为 AbortSignal）

class 可续跑启动规格(TypedDict):#启动可续跑后台子体时调用方要的东西
    provider:str#其可续跑创建能力建立该子体的提供方
    label:str#初始委托的短 description，持久化为创建标签
    request:object#委托请求（去掉由续跑表拥有的 label/signal/outputSchema）
    signal:object#调用方取消（上游类型为 AbortSignal）

class 可续跑启动(TypedDict):#可续跑子体接受其初始提示后返回的身份
    childId:str#耐久子会话 id，跨 Activation 稳定
    messageId:str#已接受初始提示的收件箱消息 id

class 子智能体打断用户权威(TypedDict):#人类客户端出示的耐久直接父地址
    kind:Literal['user']#人类父地址
    parentSessionId:str#耐久直接父会话 id

class 子智能体打断祖先权威(TypedDict):#精确活祖先智能体
    kind:Literal['ancestor']#精确活祖先
    agent:object#祖先 Agent

子智能体打断权威=子智能体打断用户权威|子智能体打断祖先权威#打断权威联合

class 子智能体跟进选项(TypedDict):
    """向一个可续跑子体跟进的选项。"""
    source:object#保留在已投递消息上的耐久归属；它不授予权威
    signal:object#调用方取消
    delivery:NotRequired[Literal['queue','steer']]#排队下一回合或转向最近一步

def 拆除于(激活):
    """读一次 Activation 当前的拆除事务。激活为 dict。"""
    if 'disposal' in 激活:#有拆除事务
        return 激活['disposal']#可变字段
    return None#无

def 结算摘要(子标识,停止原因):#结算摘要
    """一行告诉父某个后台子体做完了以及为何，用父自己的任务词汇。"""
    主语='后台子智能体 '+str(子标识)#主语
    if 停止原因=='completed':#正常完成
        return 主语+' 已完成，除非再发消息，否则不会继续工作。'#完成文案
    if 停止原因=='aborted':#已中止
        return 主语+' 在完成前被停止。'#中止文案
    if 停止原因=='max-tokens':#token上限
        return 主语+' 在完成前用尽了额度。'#上限文案
    # 步骤前拒绝——钩子拒绝、策略插件——丢弃了子体已认领的输入。
    if 停止原因=='refusal':#拒绝
        return 主语+' 拒绝了该任务。'#拒绝文案
    if 停止原因=='error':#错误
        return 主语+' 在完成前失败。'#失败文案
    return 主语+' 在完成前异常结束（'+str(停止原因)+'）。'#异常文案

class 子体锁:#串行化每个耐久子体的投递、释放与拆除
    """串行化每个耐久子体的投递、释放与拆除。"""
    def __init__(自身):#空锁表
        """空锁表。"""
        自身._尾={}#每子体链尾

    def 排队执行(自身,子标识,操作):#排队临界区
        """在 childId 上先前排队的每个操作之后执行 operation。返回该操作自己的结算。"""
        先前=自身._尾.get(子标识)#先前链尾
        结果盒=[None]#操作结果
        错误盒=[None]#操作错误
        门=threading.Event()#本操作完成门
        def 临界():#按序跑
            """等待先前后跑操作。"""
            if 先前 is not None:#有先前
                try:#无论先前成败都跑
                    先前.wait()#等先前
                except Exception:#先前失败
                    pass#吸收
            try:#跑本操作
                结果盒[0]=操作()#临界区
            except Exception as 错误:#操作失败
                错误盒[0]=错误#记下
            finally:#放开后来者
                门.set()#完成
                if 自身._尾.get(子标识) is 门:#仍是当前尾
                    自身._尾.pop(子标识,None)#清掉
        自身._尾[子标识]=门#记下新链尾
        工作=threading.Thread(target=临界)#后台临界
        工作.start()#启动
        门.wait()#等本操作
        if 错误盒[0] is not None:#失败
            raise 错误盒[0]#抛出
        return 结果盒[0]#成功值

class 激活池:#进程内槽位池
    """经不间断可续跑父链路共享的进程内槽位。"""
    def __init__(自身):#空池
        """空池。"""
        自身._槽=set()#已占用槽

    def 预留(自身,容量):#重建前预留
        """重建前预留；返回的释放对未发布回滚也容忍。"""
        if len(自身._槽)>=容量:#已满
            raise 子智能体错误(#拒绝
                'subagent limit reached (active child limit: '+str(容量)+'); wait for an existing child to finish '
                +'or complete this work with the current agents',
                'ACTIVATION_LIMIT_REACHED',
            )#SubagentError结束
        槽=object()#槽标记
        自身._槽.add(槽)#占用
        def 释放():#归还
            """幂等释放。"""
            自身._槽.discard(槽)#归还
        return 释放#释放器

class 子智能体续跑表:#可续跑表
    """ctx.subagents 背后的可续跑子智能体编排服务。工具模式与宿主适配器是本约定的消费方；前台一次性委托继续调用 ctx.subagents.start()，从不进入本生命周期。"""
    def __init__(自身,上下文,宿主,装配注册表,最大活跃子体):#安装续跑表
        """安装续跑表。最大活跃子体为 ()->int。"""
        自身.ctx=上下文#服务上下文
        自身._宿主=宿主#宿主钩子
        自身._装配注册表=装配注册表#装配注册表
        自身._最大活跃子体=最大活跃子体#活子上限
        自身._激活表={}#子会话 id → 其活 Activation
        自身._根池={}#根 Agent id → 激活池（弱：根拆除时靠 disposed 清）
        自身._物化集合=set()#进行中物化 id
        自身._物化表={}#物化 id → 物化记录
        自身._锁=子体锁()#每子体锁
        自身._关闭作用域={}#作用域拆除根到成员（用 id 键，值存 Agent 集合）
        自身._关闭根代理={}#根 id → 精确 Agent 弱引用
        自身._排空中=False#续跑表是否正在排空
        # 普通 Cordis 所有者效果按登记反序拆除，表达不了动态子图。
        def 激活所有者插件(子上下文,配置=None):#私有所有者作用域插件
            """作为支撑 Activation 句柄的共享空操作插件。"""
            return#无注册
        作用域=上下文.启动插件(激活所有者插件)#私有所有者作用域
        自身._所有者上下文=作用域.所属上下文 if 作用域.所属上下文 is not None else 上下文#记下所有者上下文
        def 根离开(载荷):#根离开注册表
            """根离开注册表时关掉其作用域截止。"""
            智能体=载荷['agent']#离开的智能体
            键=id(智能体)#对象身份
            自身._关闭作用域.pop(键,None)#关掉
            自身._关闭根代理.pop(键,None)#摘掉
            自身._根池.pop(键,None)#清根池
        上下文.监听('agent/disposed',根离开)#disposed监听
        def 排空拆除():#先拆除：排空森林
            """结构拆除：先排空。"""
            自身.排空()#排空
        def 作用域拆除():#后拆除：释放作用域
            """结构拆除：释放作用域。"""
            if hasattr(作用域,'dispose'):#有拆除
                作用域.拆除()#释放
        def 效果工厂():#结构拆除顺序
            """先排空森林，再释放作用域。"""
            def 拆除():#反序拆除
                """先排空再释放作用域。"""
                排空拆除()#先拆除：排空森林
                作用域拆除()#后拆除：释放作用域
            return 拆除#拆除器
        上下文.副作用(效果工厂,'subagents.continuations()')#结构拆除顺序

    def 启动可续跑(自身,规格):#启动可续跑
        """启动一个可续跑后台子体：预留其耐久身份，解析提供方的分离创建规格，经私有 activation-owner 作用域创建子 Agent，建立任何可续跑父所有权，并提交初始提示。"""
        请求=规格['request']#委托请求
        父=请求['parent']#委托父
        自身._断言准入(父)#准入必须开着
        自身._要求持久化()#可续跑需要持久化
        断言子智能体最大深度((请求['maxDepth'] if 'maxDepth' in 请求 else None))#校验深度上限形态
        子标识=会话标识(str(uuid.uuid4()))#预留子会话id
        子深度=解析子深度(父,(请求['maxDepth'] if 'maxDepth' in 请求 else None))#解析子深度
        #在任何阻塞等待之前快照：非法描述符 JSON 在子体存在之前拒绝调用。
        请求选项=请求['agentOptions'] if 'agentOptions' in 请求 else None#子选项
        智能体提供方=请求选项['provider'] if isinstance(请求选项,dict) and 'provider' in 请求选项 else None#子提供方
        if 智能体提供方 is None:#无子提供方
            父选项=父.options#父选项
            智能体提供方=父选项['provider'] if isinstance(父选项,dict) and 'provider' in 父选项 else None#父提供方
        智能体模型=请求选项['model'] if isinstance(请求选项,dict) and 'model' in 请求选项 else None#子模型
        if 智能体模型 is None:#无子模型
            父选项=父.options#父选项
            智能体模型=父选项['model'] if isinstance(父选项,dict) and 'model' in 父选项 else None#父模型
        描述符输入={'mode':'continuable','provider':规格['provider'],'label':规格['label']}#可续跑描述符
        if 智能体提供方 is not None:#有子提供方
            描述符输入['agentProvider']=智能体提供方#展开
        if 智能体模型 is not None:#有子模型
            描述符输入['agentModel']=智能体模型#展开
        if 'persona' in 请求 and 请求['persona'] is not None:#有人设
            描述符输入['persona']=请求['persona']#展开
        if 'toolFilter' in 请求 and 请求['toolFilter'] is not None:#有过滤
            描述符输入['toolFilter']=请求['toolFilter']#展开
        描述符=快照子智能体描述符(描述符输入)#快照
        委托策略=捕获委托策略覆盖(父)#捕获委托策略
        准备=自身._宿主['准备可续跑'](规格['provider'],{#解析提供方贡献
            'sessionId':子标识,#已预留id
            'parent':父,#委托父
            'signal':规格['signal'] if 'signal' in 规格 else None,#取消信号
        })#prepare结束
        若已中止则抛出(规格['signal'] if 'signal' in 规格 else None)#准备后取消检查
        自身._断言准入(父)#准备后准入检查
        准备种子=准备['seed'] if isinstance(准备,dict) and 'seed' in 准备 else None#父前缀
        继承计数=len(准备种子) if 准备种子 is not None else 0#精确继承前缀长度
        def 临界():#在子锁内物化并提交
            """物化并提交初始提示。"""
            创建={#创建字段：描述符与策略在未发布装配里追加，不塞进构造种子
                'meta':子会话元数据(父,子深度,准备种子 is not None),#是否 fork 种子
                'inheritedEventCount':继承计数,#继承计数
                'delegatedPolicies':委托策略,#委托策略
                'descriptor':描述符,#描述符
            }#创建结束
            if 准备种子 is not None:#有父前缀
                创建['seed']=准备种子#写入种子
            激活=自身._物化({#物化Activation
                'childId':子标识,#子id
                'provider':规格['provider'],#提供方
                'parent':父,#委托父
                'create':创建,#创建输入
                'agentOptions':解析子智能体选项(父,(请求['agentOptions'] if 'agentOptions' in 请求 else None),子深度),#子选项
                'composition':{'persona':(请求['persona'] if 'persona' in 请求 else None),'toolFilter':(请求['toolFilter'] if 'toolFilter' in 请求 else None)},#组合
                'signal':(规格['signal'] if 'signal' in 规格 else None),#取消
            })#materialize结束
            子头=激活['handle'].智能体.session.header if hasattr(激活['handle'],'智能体') else 激活['handle'].agent.session.header#子头
            if not isinstance(子头,dict):#对象形
                子头={'id':子头.id,'createdAt':子头.createdAt}#收成 dict
            def 提交目录():#接受后追加目录
                """建立目录子体。"""
                建立目录子体(父.session,子头,描述符)#目录
            return 自身._提交已物化(#提交或整份回滚
                激活,#刚发布的Activation
                请求['prompt'],#初始提示
                {'kind':'user'},#用户来源
                父,#授权父
                (规格['signal'] if 'signal' in 规格 else None),#取消
                提交目录,#接受后目录追加
            )#submitMaterialized结束
        消息标识=自身._锁.排队执行(子标识,临界)#在子锁内
        return {'childId':子标识,'messageId':消息标识}#耐久身份

    def 跟进(自身,父,子标识,内容,选项):#跟进投递
        """把一条后续消息作为已知可续跑子体的下一 FIFO 回合投递。"""
        自身._断言准入(父)#准入必须开着
        投递=选项['delivery'] if isinstance(选项,dict) and 'delivery' in 选项 else 'queue'
        while True:#拆除竞态则重试
            def 临界():#在子锁内投递
                """驻留提交或冷恢复。"""
                if 子标识 not in 自身._激活表:#缺席则冷恢复
                    return 自身._冷恢复(父,子标识,内容,选项)#冷恢复
                激活=自身._激活表[子标识]#活Activation
                if 激活.get('disposal') is not None:#拆除已打开
                    激活['disposal'].等待()#等释放后重试
                    return None#重试
                消息标识=自身._同步准入提交(激活,内容,(选项['source'] if 'source' in 选项 else None),父,(选项['signal'] if 'signal' in 选项 else None),投递)#驻留提交
                激活['announced']=True#活跟进也对外宣布
                return 消息标识#消息 id
            活=自身._锁.排队执行(子标识,临界)#在子锁内
            if 活 is not None:#已接受
                return 活#消息id
            自身._断言准入(父)#重试前准入检查
            若已中止则抛出((选项['signal'] if 'signal' in 选项 else None))#重试前取消检查

    def 打断(自身,目标会话标识,权威):#打断当前回合
        """打断一个活可续跑子体的当前回合。准入同步、效果异步。"""
        种类=权威['kind']#权威种类
        if 种类=='ancestor':#祖先权威
            调用方=权威['agent']#出示的祖先
            # 即使目标缺席也拒绝陈旧调用方，使替换的同 id Agent 永远不能探测本续跑表状态。
            if 自身.ctx.agents.获取(调用方.id) is not 调用方:#不是注册表当前项
                raise 子智能体错误(#拒绝陈旧祖先
                    '打断 "'+str(目标会话标识)+'" 需要精确的活祖先智能体',#文案
                    'UNAUTHORIZED',#错误码
                )#SubagentError结束
            if 调用方.id==目标会话标识:#不能打断自己
                raise 子智能体错误(#拒绝自打断
                    '智能体 "'+str(调用方.id)+'" 不能打断自己',#文案
                    'UNAUTHORIZED',#错误码
                )#SubagentError结束
        if 目标会话标识 not in 自身._激活表:#缺席空操作
            return#空操作
        激活=自身._激活表[目标会话标识]#活目标
        if 种类=='user':#人类父地址
            父会话=激活['handle'].智能体.session.header#头
            if (父会话['parentSession'] if isinstance(父会话,dict) and 'parentSession' in 父会话 else None)!=权威['parentSessionId']:#不是直接父
                raise 子智能体错误(#拒绝
                    '子智能体 "'+str(目标会话标识)+'" 属于另一个父会话',#文案
                    'UNAUTHORIZED',#错误码
                )#SubagentError结束
        else:#祖先权威
            if 'ancestry' not in 激活 or 权威['agent'] not in 激活['ancestry']:#祖先不在活谱系
                raise 子智能体错误(#拒绝
                    '子智能体 "'+str(目标会话标识)+'" 不是智能体 "'#文案前
                    +str(权威['agent'].id)+'" 的活后代',#文案后
                    'UNAUTHORIZED',#错误码
                )#SubagentError结束
        # 拆除已经用整份 Activation 拆除停了目标。
        if 激活.get('disposal') is not None:#拆除中空操作
            return#空操作
        智能体=激活['handle'].智能体#目标智能体
        原因={'kind':'user'} if 种类=='user' else {'kind':'parent'}#取消原因
                智能体.取消(原因,{'keepInbox':True})#保留未认领收件箱

    def 发送消息(自身,发送方,目标标识,内容,选项):
        """把模型撰写的消息投到发送方的直接父或直接可续跑子。"""
        if 自身.ctx.agents.获取(发送方.id) is not 发送方:
            raise 子智能体错误('message delivery requires the exact live sender agent','UNAUTHORIZED')
        自身._断言准入(发送方)
        发送方激活=自身._激活表.get(发送方.id)
        信号=选项['signal'] if isinstance(选项,dict) and 'signal' in 选项 else None
        if (发送方激活 is not None
            and 发送方激活['handle'].智能体 is 发送方
            and 发送方激活.get('parentSession')==目标标识):
            若已中止则抛出(信号)
            if 发送方激活.get('disposal') is not None:
                raise 子智能体错误(
                    'subagent "'+str(发送方.id)+'" activation is being disposed; the message was not delivered',
                    'ACTIVATION_CLOSING',
                )
            父=自身.ctx.agents.获取(发送方激活['parentSession'])
            if 父 is None:
                raise 子智能体错误('direct parent is not live; the message was not delivered','PARENT_UNAVAILABLE')
            消息=创建用户消息({
                'content':内容,
                'source':{'kind':'coordinator','form':'relay','senderSessionId':发送方.id},
            })
            try:
                def 按状态发送():
                    """空闲则开回合，忙则转向。"""
                    if 父.status=='idle':
                        父.后续(消息)
                    else:
                        父.转向(消息)
                自身._唤醒发送(父,消息,按状态发送)
            except Exception as 错误:
                raise 子智能体错误(
                    'direct parent is not live; the message was not delivered',
                    'PARENT_UNAVAILABLE',
                    {'cause':错误},
                )
            return 消息.id
        头=发送方.session.header
        父会话=头['parentSession'] if isinstance(头,dict) and 'parentSession' in 头 else None
        if 父会话==目标标识:
            raise 子智能体错误(
                'agent "'+str(发送方.id)+'" is not a resident continuable child and cannot send to parent "'+str(目标标识)+'"',
                'UNAUTHORIZED',
            )
        return 自身.跟进(发送方,目标标识,内容,{
            'source':{'kind':'coordinator','form':'relay','senderSessionId':发送方.id},
            'signal':信号,
            'delivery':'steer',
        })

    def 排队提示(自身,父,子标识,内容,来源,信号):
        """把一条人类提示作为直接子的独立回合排队。"""
        return 自身.跟进(父,子标识,内容,{'source':来源,'signal':信号,'delivery':'queue'})

    def 转向提示(自身,父,子标识,内容,来源,信号):
        """把一条宿主提示转向直接可续跑子的最近一步。"""
        return 自身.跟进(父,子标识,内容,{'source':来源,'signal':信号,'delivery':'steer'})

    def 排空子体(自身,父,子标识列表):
        """释放一个精确活父之下选中的驻留可续跑直接子。"""
        if 自身.ctx.agents.获取(父.id) is not 父:
            raise 子智能体错误(
                'release of selected children requires the exact live parent agent',
                'UNAUTHORIZED',
            )
        目标列表=[]
        for 子标识 in 子标识列表:
            激活=自身._激活表.get(子标识)
            if 激活 is None:
                continue
            if 激活.get('parentSession')!=父.id:
                raise 子智能体错误(
                    'subagent "'+str(子标识)+'" belongs to another parent session',
                    'UNAUTHORIZED',
                )
            目标列表.append(激活)
        for 激活 in 目标列表:
            自身._拆除(激活)
        for 激活 in 目标列表:
            拆除=激活.get('disposal')
            if 拆除 is not None:
                拆除.等待()

    def 自报告(自身,子,内容,选项):#子体向父报告
        """把一个驻留可续跑子体显式选定的内容投递到其耐久直接父。"""
        若已中止则抛出((选项['signal'] if 'signal' in 选项 else None))#接受前取消
        自身._断言准入(子)#准入必须开着
        激活=自身._授权报告者(子)#授权报告者
        父=自身._解析报告父(子)#解析活直接父
        return 自身._投递报告(激活,父,内容,选项['delivery'] if 'delivery' in 选项 else None)#投递报告

    def 排空(自身):#排空全部
        """关闭准入，等待每个已准入物化走到发布或回滚，然后子优先拆除稳定活 Activation 森林。"""
        #第一次阻塞等待之前同步关闭准入。
        自身._排空中=True#关闭准入
        for 物化 in list(自身._物化表.values()):#等物化静止
            物化['settled'].等待()#屏障
        # 关闭准入后快照根：根是没有活 Activation 拥有的 Activation。
        被拥有=set()#被拥有的子id
        for 激活 in 自身._激活表.values():#收集被拥有者
            for 子 in 激活.get('ownedChildren') or set():#记下子
                被拥有.add(子)#记下
        根列表=[激活 for 激活 in 自身._激活表.values() if 激活['childId'] not in 被拥有]#森林根
        自身._拆除根列表(根列表,'Activation')#拆除根

    def 排空后代(自身,父列表):#排空作用域后代
        """只停精确活宿主拥有父的可续跑后代。"""
        根集合=set()#精确活根
        for 父 in 父列表:#过滤精确活
            if 自身.ctx.agents.获取(父.id) is 父:#精确活
                根集合.add(父)#收下
        if len(根集合)==0:#没有活根
            return#空操作
        #第一次阻塞等待之前发布作用域准入截止。
        for 根 in 根集合:#发布截止
            自身._关闭成员(根).add(根)#根自己也是成员
        目标列表=[]#要停的Activation
        for 激活 in list(自身._激活表.values()):#扫描活纪元
            谱系=自身._活谱系(激活['handle'].智能体)#当前可解析谱系
            所有者列表=[根 for 根 in 根集合#在物化谱系里的所有者
                if 激活['handle'].智能体 is not 根#排除自身
                and 根 in (激活.get('ancestry') or [])]#在物化谱系里
            if len(所有者列表)==0:#无关树跳过
                continue#跳过
            目标列表.append(激活)#选中
            for 所有者 in 所有者列表:#把谱系记进关闭成员
                成员=自身._关闭成员(所有者)#该根的成员集
                成员.add(激活['handle'].智能体)#子体自己
                for 智能体 in 谱系:#其祖先
                    成员.add(智能体)#记下
        物化列表=[]#作用域内物化
        for 物化 in list(自身._物化表.values()):#过滤
            所有者列表=[根 for 根 in 根集合 if 根 in (物化.get('lineage') or [])]#物化谱系含根
            for 所有者 in 所有者列表:#把物化谱系记进关闭成员
                成员=自身._关闭成员(所有者)#该根的成员集
                for 智能体 in 物化.get('lineage') or []:#谱系成员
                    成员.add(智能体)#记下
            if len(所有者列表)>0:#属于某个根
                物化列表.append(物化)#收下
        被拥有目标=set()#目标中被拥有的
        for 激活 in 目标列表:#收集被拥有者
            for 子 in 激活.get('ownedChildren') or set():#记下子
                被拥有目标.add(子)#记下
        目标根列表=[激活 for 激活 in 目标列表 if 激活['childId'] not in 被拥有目标]#作用域根
        # 在物化屏障之前打开每个选中事务。
        for 激活 in 目标列表:#打开拆除
            自身._拆除(激活)#打开记忆化事务，稍后等待
        for 物化 in 物化列表:#等作用域物化
            物化['settled'].等待()#屏障
        自身._拆除根列表(目标根列表,'作用域 Activation')#拆除作用域根

    def _授权报告者(自身,子):#授权报告者
        """只授权一个驻留 Activation 的精确 Agent。"""
        激活=自身._激活表.get(子.id)#按id查找
        if 激活 is None or 激活['handle'].智能体 is not 子:#不是精确活可续跑子体
            raise 子智能体错误(#拒绝
                '智能体 "'+str(子.id)+'" 不是活的可续跑子智能体，无法报告',#文案
                'UNAUTHORIZED',#错误码
            )#SubagentError结束
        if 激活.get('disposal') is not None:#拆除已打开
            raise 子智能体错误(#拒绝
                '子智能体 "'+str(子.id)+'" 的 Activation 正在拆除；报告未投递',#文案
                'ACTIVATION_CLOSING',#错误码
            )#SubagentError结束
        return 激活#已授权Activation

    def _解析报告父(自身,子):#解析报告父
        """从耐久谱系解析报告子体的活直接父。"""
        头=子.session.header#会话头
        父标识=头['parentSession'] if isinstance(头,dict) and 'parentSession' in 头 else None#耐久直接父id
        父=自身.ctx.agents.获取(父标识) if 父标识 is not None else None#活父
        if 父 is None:#父不活
            raise 子智能体错误(#拒绝
                '直接父不存活；报告未投递',#文案
                'PARENT_UNAVAILABLE',#错误码
            )#SubagentError结束
        return 父#活直接父

    def _投递报告(自身,激活,父,内容,投递):#投递报告
        """经选定的父调度预设投递一份成帧报告。"""
        前缀={'type':'text','text':'后台子智能体 '+str(激活['childId'])+' 报告：'}#前缀
        消息=创建用户消息({#成帧报告消息
            'content':[前缀]+list(内容),#前缀加选定内容
            'source':{#报告归属
                'kind':'subagent-report',#报告种类
                'form':'relay',#中继形态
                'senderSessionId':激活['childId'],#发送方
            },#source结束
        })#createUserMessage结束
        if 投递=='wakeup':#唤醒父
            自身._唤醒发送(父,消息,lambda: 自身._发送报告(父,消息,投递))#记账后发送
        else:#安静注入
            自身._发送报告(父,消息,投递)#直接注入
        return 消息.id#消息id

    def _唤醒发送(自身,父,消息,发送):#唤醒发送并记账
        """对父执行一次唤醒发送，若该父自己有 Activation 则记到它头上。"""
        父激活=自身._激活表.get(父.id)#父是否可续跑管理
        if 父激活 is not None and 父激活['handle'].智能体 is 父:#精确活父Activation
            自身._准入唤醒(父激活,消息.id,发送)#经父记账窗口发送
        else:#非可续跑父
            发送()#直接发送

    def _发送报告(自身,父,消息,投递):#发送报告
        """发送一份报告，只翻译父自己的拒绝。"""
        try:#隔离父拒绝
            if 投递=='wakeup':#唤醒入队
                父.后续(消息)#唤醒入队
            else:#安静注入
                父.注入(消息)#安静注入
        except Exception as 错误:#父不接受
            raise 子智能体错误(#翻译为父不可用
                '直接父不存活；报告未投递',#文案
                'PARENT_UNAVAILABLE',#错误码
                {'cause':错误},#原因
            )#SubagentError结束

    def _拆除根列表(自身,根列表,失败主语):#拆除根并聚合失败
        """拆除独立根并在全部结算后报告每个分支失败。"""
        失败列表=[]#失败原因
        for 激活 in 根列表:#并行拆除（串行等待）
            try:#隔离分支失败
                自身._拆除(激活)#拆除一根
            except Exception as 错误:#分支失败
                失败列表.append(错误)#记下
        if len(失败列表)>0:#有失败
            raise 子智能体错误(#聚合拒绝
                '可续跑子智能体拆除失败，涉及 '+str(len(失败列表))+' 个'+失败主语+'：'#文案前
                +'; '.join([错误链(原因) for 原因 in 失败列表]),#文案后
                'ACTIVATION_TEARDOWN_FAILED',#错误码
            )#SubagentError结束

    def _关闭成员(自身,根):#根的关闭成员
        """返回一个精确作用域拆除根的保留成员集。"""
        键=id(根)#对象身份
        已有=自身._关闭作用域.get(键)#已有集
        if 已有 is not None:#复用
            return 已有#成员集
        成员=set()#新建空集
        自身._关闭作用域[键]=成员#登记
        自身._关闭根代理[键]=根#记下精确根
        return 成员#成员集

    def _活谱系(自身,智能体):#向上走活谱系
        """返回从 agent 向上当前可解析的精确谱系。第一个元素永远是所供身份。"""
        谱系=[智能体]#从自身开始
        已见=set([智能体.id])#防环
        头=智能体.session.header#会话头
        父会话=头['parentSession'] if isinstance(头,dict) and 'parentSession' in 头 else None#直接父id
        while 父会话 is not None:#沿头向上
            父=自身.ctx.agents.获取(父会话)#当前活父
            if 父 is None or 父.id in 已见:#缺席或环
                break#停止
            谱系.append(父)#记下
            已见.add(父.id)#防环
            父头=父.session.header#父头
            父会话=父头['parentSession'] if isinstance(父头,dict) and 'parentSession' in 父头 else None#再上一层
        return 谱系#自身加祖先

    def _关闭拆除于(自身,智能体):#查关闭拆除
        """为该智能体谱系关闭了可续跑准入的拆除。"""
        if 自身._排空中:#整份排空
            return 'manager'#整份
        谱系=自身._活谱系(智能体)#当前谱系
        for 键,成员 in list(自身._关闭作用域.items()):#逐作用域根
            根=自身._关闭根代理.get(键)#精确根
            if 智能体 in 成员 or (根 is not None and 根 in 谱系):#命中该根
                return 根#该根
        return None#准入开着

    def _断言准入(自身,智能体):#断言仍在准入
        """一旦续跑表或本精确父树开始排空就拒绝新准入。"""
        关闭=自身._关闭拆除于(智能体)#关闭拆除
        if 关闭 is None:#仍开着
            return#通过
        if 关闭=='manager':#整份
            raise 子智能体错误(#拒绝新操作
                '可续跑子智能体正在排空；操作未被准入',#文案
                'DRAINING',#错误码
            )#SubagentError结束
        raise 子智能体错误(#作用域拒绝
            '父 "'+str(关闭.id)+'" 之下的可续跑子智能体正在排空；操作未被准入',#文案
            'DRAINING',#错误码
        )#SubagentError结束

    def _状态于(自身,激活):#推导驻留状态
        """从 Agent 静止与已拥有子体集合推导驻留。"""
        智能体=激活['handle'].智能体#子智能体
        状态=智能体.status#Agent.status
        if 状态=='running' or len(激活.get('accepted') or set())>0:#忙或待承认唤醒
            return 'running'#忙
        if len(激活.get('ownedChildren') or set())>0:#等后代
            return 'waiting'#等
        return 'settled'#可拆除

    def _冷恢复(自身,父,子标识,内容,选项):#冷恢复并提交
        """冷恢复一个持久子体并提交等待中的回合。"""
        持久化=自身._要求持久化()#必须有持久化
        try:#读持久会话
            已载=持久化.检查(子标识,选项['signal'] if 'signal' in 选项 else None)#检查头与事件
        except Exception as 错误:#检查失败
            若已中止则抛出((选项['signal'] if 'signal' in 选项 else None))#取消则改抛Abort
            raise 子智能体错误('子智能体 "'+str(子标识)+'" 不可用','NOT_RESUMABLE',{'cause':错误})#不可恢复
        若已中止则抛出((选项['signal'] if 'signal' in 选项 else None))#检查后取消
        自身._断言准入(父)#检查后准入
        # 折叠之前授权持久头：只有耐久子体的精确活直接父可以续它。
        元=已载['meta'] if isinstance(已载,dict) and 'meta' in 已载 else None#持久头
        自身._授权谱系(父,子标识,元['parentSession'] if isinstance(元,dict) and 'parentSession' in 元 else None)#授权谱系
        继承计数=已载['inheritedEventCount'] if isinstance(已载,dict) and 'inheritedEventCount' in 已载 and 已载['inheritedEventCount'] is not None else 0#继承切口
        原始事件=已载['events'] if isinstance(已载,dict) and 'events' in 已载 else None#事件
        事件列表=list(原始事件 if 原始事件 is not None else [])[继承计数:]#自身后缀
        描述符=折叠子智能体描述符(事件列表)#自身后缀描述符
        if 描述符 is None or 描述符.get('mode')!='continuable':#无法续跑
            raise 子智能体错误(#拒绝
                '子智能体 "'+str(子标识)+'" 没有可支持的续跑状态，无法恢复；'#文案前
                +'请勿用此 id 重试 send_message',#文案后
                'NOT_RESUMABLE',#错误码
            )#SubagentError结束
        try:#重建Activation
            智能体选项={}#从描述符重建选项
            if 描述符.get('agentProvider') is not None:#有子提供方
                智能体选项['provider']=描述符['agentProvider']#展开
            if 描述符.get('agentModel') is not None:#有子模型
                智能体选项['model']=描述符['agentModel']#展开
            激活=自身._物化({#物化
                'childId':子标识,#子id
                'provider':描述符['provider'],#描述符提供方
                'parent':父,#授权父
                'agentOptions':智能体选项,#子选项
                'composition':{'persona':描述符.get('persona'),'toolFilter':描述符.get('toolFilter')},#组合
                'signal':(选项['signal'] if 'signal' in 选项 else None),#取消
            })#materialize结束
        except Exception as 错误:#物化失败
            若已中止则抛出((选项['signal'] if 'signal' in 选项 else None))#取消则改抛Abort
            if isinstance(错误,子智能体错误):#已是缝错误则原样
                raise 错误#原样
            raise 子智能体错误('子智能体 "'+str(子标识)+'" 不可用','NOT_RESUMABLE',{'cause':错误})#包装为不可恢复
        return 自身._提交已物化(激活,内容,(选项['source'] if 'source' in 选项 else None),父,(选项['signal'] if 'signal' in 选项 else None),None,选项['delivery'] if 'delivery' in 选项 else 'queue')#提交或回滚

    def _提交已物化(自身,激活,内容,来源,父,信号,提交=None,投递='queue'):#提交或回滚
        """向刚物化的 Activation 提交，或整份回滚；接受后可选目录提交。"""
        try:#尝试提交
            消息标识=自身._同步准入提交(激活,内容,来源,父,信号,投递)#同步准入提交
            if 提交 is not None:#有提交钩子
                提交()#目录追加等
            激活['announced']=True#已向调用方公布
            return 消息标识#消息 id
        except Exception as 错误:#接受前失败
            try:#回滚拆除
                自身._拆除(激活)#回滚
            except Exception as 清理错误:#回滚失败不得掩盖原失败
                try:#记警告
                    自身.ctx.logger.warn('子智能体续跑：准入或目录追加失败后的拆除也失败了：'+str(清理错误))#警告
                except Exception:#无 logger
                    pass#吞掉
            raise 错误#保留原失败

    def _根池于(自身,父):#解析根池
        """根的池解析一次；后代直接继承其驻留父的池。"""
        父激活=自身._激活表.get(父.id)#驻留父
        if 父激活 is not None and 父激活.get('pool') is not None:#继承父池
            return 父激活['pool']#池
        键=id(父)#根身份
        if 键 not in 自身._根池:#新建
            自身._根池[键]=激活池()#池
        池=自身._根池[键]#已有
        return 池#池

    def _物化(自身,输入):#跟踪物化
        """经私有 activation-owner 作用域创建或恢复子 Agent。"""
        自身._断言准入(输入['parent'])#准入必须开着
        若已中止则抛出((输入['signal'] if 'signal' in 输入 else None))#取消检查
        屏障=操作任务()#发布或回滚屏障
        谱系=自身._活谱系(输入['parent'])#同步准入边界谱系
        池=自身._根池于(输入['parent'])#池
        释放槽=池.预留(自身._最大活跃子体())#预留槽
        物化标识=object()#物化身份
        物化={'lineage':谱系,'settled':屏障}#已准入物化
        自身._物化表[物化标识]=物化#登记屏障
        自身._物化集合.add(物化标识)#登记
        try:#实际创建或恢复
            return 自身._跟踪物化(输入,谱系,池,释放槽)#驻留Activation
        except Exception:#失败归还槽
            释放槽()#归还
            raise#原样
        finally:#无论成败摘屏障
            自身._物化表.pop(物化标识,None)#移出集合
            自身._物化集合.discard(物化标识)#移出
            屏障.兑现()#放开排空等待

    def _跟踪物化(自身,输入,父谱系,池,释放槽):#实际创建或恢复
        """执行一次被跟踪的物化。"""
        子标识=输入['childId']#子id
        提供方=输入['provider']#提供方
        父=输入['parent']#委托父
        创建=(输入['create'] if 'create' in 输入 else None)#可选创建输入
        若已中止则抛出((输入['signal'] if 'signal' in 输入 else None))#创建前取消
        def 装配(子上下文,子=None):#未发布装配
            """未发布装配。子为工厂传入的智能体；缺席时取自子上下文。"""
            智能体=子 if 子 is not None else 子上下文.agent#优先用工厂传入的子体
            if 创建 is not None:#全新创建
                智能体.session.追加('subagent/descriptor',创建['descriptor'])#追加描述符
                追加委托策略覆盖(智能体.session,创建['delegatedPolicies'] if 'delegatedPolicies' in 创建 else None)#追加策略事件
            应用子体组合(子上下文,父,(输入['composition'] if 'composition' in 输入 else None))#应用人设与工具过滤
            return 自身._装配注册表.应用(子上下文)#部署贡献
        观察者=自身._宿主['观察激活'](提供方,子标识,父)#本纪元观察者
        所有者智能体=自身._所有者上下文.agents#所有者注册表
        if 创建 is None:#冷恢复
            句柄=所有者智能体.恢复({#恢复持久会话
                'resumeSessionId':子标识,#要恢复的id
                'parentAgent':父,#委托父
                'agentOptions':(输入['agentOptions'] if 'agentOptions' in 输入 else None),#子选项
                'signal':(输入['signal'] if 'signal' in 输入 else None),#取消
                'setup':装配,#未发布装配
            })#resume结束
        else:#全新创建
            创建选项={#创建选项
                'sessionId':子标识,#已预留id
                'parentAgent':父,#委托父
                'meta':创建['meta'] if 'meta' in 创建 else None,#会话元数据
                'agentOptions':(输入['agentOptions'] if 'agentOptions' in 输入 else None),#子选项
                'signal':(输入['signal'] if 'signal' in 输入 else None),#取消
                'setup':装配,#未发布装配
            }#选项结束
            if 'seed' in 创建 and 创建['seed'] is not None:#有种子
                创建选项['seed']=创建['seed']#写入
            if 'inheritedEventCount' in 创建:#有继承计数
                创建选项['inheritedEventCount']=创建['inheritedEventCount']#写入
            句柄=所有者智能体.创建(创建选项)#create结束
        谱系弱=weakref.WeakSet()#子体加父谱系
        谱系弱.add(句柄.智能体)#子体
        for 祖先 in 父谱系:#父谱系
            try:#弱引用可能失败于内置类型
                谱系弱.add(祖先)#记下
            except TypeError:#不可弱引用
                pass#跳过
        激活={#驻留纪元
            'pool':池,#激活池
            'releaseSlot':释放槽,#释放槽
            'childId':子标识,#子id
            'parentSession':父.id,#父会话id
            'provider':提供方,#提供方名
            'handle':句柄,#已发布句柄
            'ancestry':谱系弱,#子体加父谱系
            'ownedChildren':set(),#尚无后代
            'observer':观察者,#生命周期观察者
            'disposal':None,#尚未拆除
            'accepted':set(),#尚无已接受唤醒
            'announced':False,#尚未向调用方公布
            'poke':操作任务(),#结算唤醒
        }#activation结束
        # 转移之后，任何失败都必须拆除已创建句柄、移除 Activation，并在拒绝之前回滚父所有权。
        自身._激活表[子标识]=激活#装进活表
        try:#发布后装配
            若已中止则抛出((输入['signal'] if 'signal' in 输入 else None))#转移后取消
            自身._断言准入(父)#转移后准入
            自身._获取所有权(父,子标识)#在子能跑之前登记父所有权
            智能体=句柄.智能体#子智能体
            def 出队(载荷):#出队
                """已接受 id 离开收件箱。"""
                消息=载荷['message']#消息
                if 消息.id in 激活['accepted']:#本续跑表准入的
                    激活['accepted'].discard(消息.id)#清掉
                    自身._唤醒(激活)#重观察
            def 丢弃(载荷):#丢弃
                """已接受 id 被丢弃。"""
                消息=载荷['message']#消息
                if 消息.id in 激活['accepted']:#本续跑表准入的
                    激活['accepted'].discard(消息.id)#清掉
                    自身._唤醒(激活)#重观察
            智能体.ctx.监听('agent/inbox/claimed',出队)#出队
            智能体.ctx.监听('agent/inbox/discarded',丢弃)#丢弃
            # 在任何回合能跑之前发布 start 边。
            观察者['start'](智能体)#发布start
        except Exception as 错误:#发布后失败
            try:#未发布回滚
                自身._未发布回滚(激活)#回滚
            except Exception:#回滚失败不得掩盖准入失败
                pass#吞掉
            raise 错误#保留原失败
        自身._观察结算(激活)#开始结算观察
        return 激活#驻留纪元

    def _未发布回滚(自身,激活):#未发布回滚
        """释放尚未发布 start 边的 Activation。"""
        if 激活.get('disposal') is not None:#已有事务
            return 激活['disposal']#复用
        任务=操作任务()#拆除操作任务
        激活['disposal']=任务#记忆化
        def 后台拆除句柄():#拆除句柄
            """拆除句柄并回滚所有权。"""
            try:#拆除句柄
                激活['handle'].拆除()#释放Agent
            finally:#无论成败
                自身._激活表.pop(激活['childId'],None)#移出活表
                释放=激活.get('releaseSlot')#槽释放
                if 释放 is not None:#有
                    释放()#归还槽
                自身._释放所有权(激活['childId'])#回滚父所有权
                任务.兑现()#放开
        threading.Thread(target=后台拆除句柄).start()#后台
        return 任务#拆除事务

    def _获取所有权(自身,父,子标识):#登记父所有权
        """在子体能跑之前把它登记进可续跑管理父的已拥有集合。"""
        if 父.id not in 自身._激活表:#非续跑父
            return#跳过
        父激活=自身._激活表[父.id]#父是否可续跑管理
        if 父激活.get('disposal') is not None:#父正在拆
            raise 子智能体错误(#拒绝建立子体
                '子智能体父 "'+str(父.id)+'" 正在拆除；子体未建立',#文案
                'ACTIVATION_CLOSING',#错误码
            )#SubagentError结束
        父激活['ownedChildren'].add(子标识)#记下子

    def _释放所有权(自身,子标识):#释放所有权
        """从活所有者集合移除一个子体，并让该所有者重新检查结算。"""
        for 候选 in list(自身._激活表.values()):#找拥有者
            if 子标识 in (候选.get('ownedChildren') or set()):#拥有
                候选['ownedChildren'].discard(子标识)#删掉
                自身._唤醒(候选)#唤醒

    def _唤醒(自身,激活):#唤醒结算观察者
        """让结算观察者在所有权或收件箱变化后重新观察静止。"""
        激活['poke'].兑现()#放开当前等待
        激活['poke']=操作任务()#续订下一轮

    def _提交(自身,激活,内容,来源,父,投递='queue'):#提交已成帧消息
        """把一条消息作为子体的下一 FIFO 回合提交，并返回其已接受收件箱 id。"""
        # 源自父的投递通过所有权保持父活着。
        自身._获取所有权(父,激活['childId'])#登记父所有权
        消息=创建用户消息({'content':内容,'source':来源})#建造用户消息
        def 发送跟进():
            """记账窗口内入队下一回合或转向最近一步。"""
            if 投递=='steer':
                激活['handle'].智能体.转向(消息)
            else:
                激活['handle'].智能体.后续(消息)#入队下一回合
        已接受=自身._准入唤醒(激活,消息.id,发送跟进)#admitWaking结束
        # announced 由 _提交已物化 在目录提交后置位；此处只返回已接受 id。
        return 已接受#消息id

    def _准入唤醒(自身,激活,消息标识,发送):#记账唤醒发送
        """跨驻留 Activation 的结算窗口记账一次唤醒发送。"""
        # Agent.followup() 同步发布收件箱事件，因此观察者必须在调用开始前看见本 Activation 为忙。
        激活['accepted'].add(消息标识)#先记账
        try:#发送可能拒绝
            发送()#同步入队
        except Exception as 错误:#发送失败
            激活['accepted'].discard(消息标识)#回滚记账
            raise 错误#原样抛出
        # 已接受唤醒工作保持本 Activation 活到 whenIdle() 观察到完整唤醒后缀。
        自身._唤醒(激活)#重观察静止
        return 消息标识#消息id

    def _同步准入提交(自身,激活,内容,来源,父,信号,投递='queue'):#同步准入提交
        """越过最终准入截止并提交，不让出。"""
        若已中止则抛出(信号)#截止前取消
        自身._断言准入(父)#截止前准入
        if 拆除于(激活) is not None:#拆除已打开
            raise 子智能体错误(#拒绝
                '子智能体 "'+str(激活['childId'])+'" 的 Activation 正在拆除；消息未被接受',#文案
                'ACTIVATION_CLOSING',#错误码
            )#SubagentError结束
        子头=激活['handle'].智能体.session.header#子会话头
        自身._授权谱系(父,激活['childId'],子头['parentSession'] if isinstance(子头,dict) and 'parentSession' in 子头 else None)#授权直接父
        return 自身._提交(激活,内容,来源,父,投递)#提交

    def _授权谱系(自身,父,子标识,父会话):#授权直接父
        """对照耐久直接父谱系授权一次操作。"""
        if 自身.ctx.agents.获取(父.id) is not 父:#不是注册表当前项
            raise 子智能体错误(#拒绝陈旧父
                '向子智能体 "'+str(子标识)+'" 投递需要精确的活父智能体',#文案
                'UNAUTHORIZED',#错误码
            )#SubagentError结束
        if 父会话!=父.id:#不是直接父
            raise 子智能体错误('子智能体 "'+str(子标识)+'" 属于另一个父会话','UNAUTHORIZED')#拒绝

    def _观察结算(自身,激活):#后台结算观察
        """跟随一次 Activation 到结算。"""
        def 循环():#不阻塞调用方
            """驻留结算循环。"""
            while 拆除于(激活) is None:#驻留循环
                戳=激活['poke']#本轮唤醒
                智能体=激活['handle'].智能体#子智能体
                空闲时=智能体.等到空闲#空闲等待
                try:#静止或被戳
                    if 空闲时 is not None:#有空闲
                        # 简化：后台线程分别等待戳与空闲（竞速）
                        完成=threading.Event()#竞速门
                        def 等空闲():#等空闲
                            """等 Agent 静止。"""
                            try:#空闲可能抛
                                智能体.等到空闲()#等空闲
                            except Exception:#忽略
                                pass#忽略
                            finally:#放行
                                完成.set()#完成
                        def 等戳():#等戳
                            """等 poke。"""
                            try:#戳可能拒绝
                                戳.等待()#等戳
                            except Exception:#忽略
                                pass#忽略
                            finally:#放行
                                完成.set()#完成
                        threading.Thread(target=等空闲).start()#后台空闲
                        threading.Thread(target=等戳).start()#后台戳
                        完成.wait()#任一完成
                except Exception:#观察失败
                    pass#继续
                if 拆除于(激活) is not None:#拆除已接手
                    return
                def 锁内决定():#锁内决定
                    """重新检查结算并在同一临界区开始拆除。"""
                    if 拆除于(激活) is not None or 自身._状态于(激活)!='settled':#忙或已拆
                        return {'settling':False}#再观察
                    return {'settling':True,'done':自身._拆除(激活)}#打开拆除
                结算中=自身._锁.排队执行(激活['childId'],锁内决定)#锁内决定
                if not 结算中.get('settling'):#尚未拆除
                    if 智能体.status!='running':#等下一次戳
                        try:#等戳
                            戳.等待()#等
                        except Exception:#忽略
                            pass#忽略
                    continue#再循环
                try:#等待拆除
                    结算中['done'].等待()#拆除事务
                except Exception as 错误:#拆除失败
                    自身.ctx.日志.警告(#记录但不抛给观察循环
                        '子智能体 "'+str(激活['childId'])+'" 的 Activation 拆除失败：'+错误链(错误),#文案
                    )#warn结束
                return#本纪元结束
        threading.Thread(target=循环,daemon=True).start()#立即启动

    def _拆除(自身,激活):#打开拆除事务
        """立即停一次 Activation，然后子优先释放它。记忆化事务在取消或递归回调之前安装。"""
        已有=激活.get('disposal')#已有事务
        if 已有 is not None:#幂等
            return 已有#同一事务
        完成=操作任务()#对外任务
        # 存在即准入截止。
        激活['disposal']=完成#安装截止
        def 后台完成拆除():#后台完成拆除
            """完成拆除后兑现或拒绝。"""
            try:#完成拆除
                自身._完成拆除(激活)#完成
                完成.兑现()#成功
            except Exception as 错误:#失败
                完成.拒绝(错误)#拒绝
        threading.Thread(target=后台完成拆除).start()#后台
        return 完成#同一事务

    def _完成拆除(自身,激活):#完成拆除
        """同步传播停止，然后完成子优先释放。"""
        自身._唤醒(激活)#放开结算观察者
        子标识=激活['childId']#子id
        #第一次阻塞等待之前自上而下停止。
        智能体=激活['handle'].智能体#子智能体
        智能体.取消({'kind':'parent'})#取消当前回合
        子拆除列表=[]#子拆除
        for 子 in list(激活.get('ownedChildren') or set()):#已拥有子id
            子激活=自身._激活表.get(子)#活Activation
            if 子激活 is not None:#仍驻留
                子拆除列表.append(自身._拆除(子激活))#递归打开子拆除
        失败列表=[]#本边界失败
        try:#子优先释放
            for 拆除 in 子拆除列表:#等子拆除
                try:#隔离子失败
                    拆除.等待()#子事务
                except Exception as 错误:#子失败
                    失败列表.append(子智能体错误(#记下聚合
                        '子智能体 "'+str(子标识)+'" 的子体拆除失败：'+错误链(错误),#文案
                        'ACTIVATION_TEARDOWN_FAILED',#错误码
                    ))#push结束
            智能体.等到空闲()#等本Agent静止
            自身._刷新最终态(激活)#尽力最终刷新
            # 在子体仍活时捕获依赖子体的边数据。
            激活['observer']['capture'](智能体)#快照终态
        except Exception as 错误:#释放路径失败
            失败列表.append(子智能体错误(#记下
                '子智能体 "'+str(子标识)+'" 的 Activation 拆除失败：'+错误链(错误),#文案
                'ACTIVATION_TEARDOWN_FAILED',#错误码
                {'cause':错误},#原因
            ))#push结束
        try:#拆除句柄
            激活['handle'].拆除()#释放Agent
        except Exception as 错误:#句柄拆除失败
            失败列表.append(子智能体错误(#记下
                '子智能体 "'+str(子标识)+'" 的 Activation 句柄拆除失败：'+错误链(错误),#文案
                'ACTIVATION_TEARDOWN_FAILED',#错误码
                {'cause':错误},#原因
            ))#push结束
        失败=None#聚合失败
        if len(失败列表)==1:#单边界
            失败=失败列表[0]#原样
        elif len(失败列表)>1:#多边界
            失败=子智能体错误(#聚合
                '子智能体 "'+str(子标识)+'" 的 Activation 拆除在 '+str(len(失败列表))+' 个边界失败：'#文案前
                +'; '.join([错误链(项) for 项 in 失败列表]),#文案后
                'ACTIVATION_TEARDOWN_FAILED',#错误码
                {'cause':聚合错误(失败列表)},#原因
            )#SubagentError结束
        # 只到现在 Activation 才消失。
        自身._激活表.pop(子标识,None)#移出活表
        释放=激活.get('releaseSlot')#槽释放
        if 释放 is not None:#有
            释放()#归还槽
        # 在释放所有权之前，父仍把本子体算进去因此不能被判为已结算。
        自身._通知结算(激活,激活['observer']['terminal'](失败))#向父投递结算
        # 即使失败也释放所有权。
        自身._释放所有权(子标识)#释放父所有权
        # 拆除结局已知后才发射。
        激活['observer']['settle'](失败)#发布end
        if 失败 is not None:#有失败
            raise 失败#向外抛聚合失败

    def _通知结算(自身,激活,终态):#向父投递结算通知
        """告诉耐久直接父本子体已经产出了它将产出的一切。"""
        if not 激活.get('announced'):#未公布则沉默
            return#沉默
        try:#隔离投递失败
            父=自身.ctx.agents.获取(激活['parentSession'])#活直接父
            if 父 is None:#父不活则丢掉
                return#丢掉
            摘要=结算摘要(激活['childId'],终态['stopReason'] if 'stopReason' in 终态 else None)#开场行
            输出=终态['output'] if 'output' in 终态 else None#可选最终输出
            if 输出 is None:#无收尾
                内容=[{'type':'text','text':摘要},{'type':'text','text':'没有收尾消息。'}]#无收尾
            else:#带收尾
                内容=[{'type':'text','text':摘要},{'type':'text','text':'收尾消息：'}]+list(输出)#带收尾
            消息=创建用户消息({#结算通知
                'content':内容,#摘要加可选收尾
                'source':{#结算归属
                    'kind':'subagent-settled',#结算种类
                    'form':'notice',#通知形态
                    'summary':截上下文摘要(摘要),#上下文摘要
                    'senderSessionId':激活['childId'],#发送方
                },#source结束
            })#createUserMessage结束
            # 自身拆除已开始的父不得被唤醒。
            if 自身._关闭拆除于(父) is not None:#父谱系正在关
                父.注入(消息)#安静注入
                return#不唤醒
            def 按状态发送():#记账后按状态发送
                """空闲则开回合，忙则转向。"""
                if 父.status=='idle':#空闲
                    父.后续(消息)#开回合
                else:#忙
                    父.转向(消息)#转向
            自身._唤醒发送(父,消息,按状态发送)#记账后按状态发送
        except Exception as 错误:#投递失败
            自身.ctx.日志.警告(#记录并丢掉
                '子智能体 "'+str(激活['childId'])+'" 的结算通知未投递到其父：'#文案前
                +错误链(错误),#文案后
            )#warn结束

    def _刷新最终态(自身,激活):#尽力最终刷新
        """子体静止后请求一次尽力最终会话刷新。"""
        子=激活['handle'].智能体#子智能体
        try:#刷新可能拒绝
            子.ctx.sessions.flush(子.session)#刷新会话
        except Exception as 错误:#刷新失败
            自身.ctx.日志.警告(#记录后继续拆除
                '子智能体 "'+str(激活['childId'])+'" 尽力最终会话刷新失败；'#文案前
                +'持久化状态在恢复时可能不可用或过期：'+错误链(错误),#文案后
            )#warn结束

    def _要求持久化(自身):#必须有持久化
        """解析可续跑子体需要的持久化服务，否则大声失败。"""
        持久化=自身.ctx.获取服务('sessionPersistence')#可选持久化
        if 持久化 is None:#未挂载
            raise 子智能体错误(#拒绝
                '可续跑子智能体需要会话持久化（请加载 dsh-session-persistence 后端）',#文案
                'PERSISTENCE_UNAVAILABLE',#错误码
            )#SubagentError结束
        return 持久化#持久化服务

