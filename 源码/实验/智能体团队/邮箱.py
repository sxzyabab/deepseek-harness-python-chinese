import copy,uuid#克隆与消息 id
from ...基础设施.通用工具.序列化编码 import 紧凑json编码
from threading import Lock as 互斥锁#队尾互斥
from functools import partial as 偏函数
from ...基础设施.js特性 import PromiseEX as 期约#投递与确认的异步结果
from ...模型后端.llm import 创建用户消息#用户消息工厂
from .异常 import 团队错误,错误文案#领域错误
from .持久化 import 读持久会话#持久读取
from .名册 import 解析活跃成员#活跃成员
from .会话消息 import 消息已接受#消息接受
from .类型 import 团队标识,团队消息标识#身份
from .生命周期 import 若已中止则抛出,合成中止#本包原语

__all__=['团队邮箱']#仅中文公开名

def _团队消息谓词(消息标识):#构造接受谓词
    '匹配团队消息身份'
    def 谓词(消息):#谓词
        '来源 kind 与消息 id'
        if 'source' not in 消息:#无来源
            return False#否
        来源=消息['source']#来源
        return 'kind' in 来源 and 来源['kind']=='team-message' and 'messageId' in 来源 and 来源['messageId']==消息标识#匹配
    return 谓词#谓词

class 团队邮箱:#团队邮箱
    '拥有持久 Team 邮箱的每一个进程内状态转换'
    def __init__(自身,上下文,日志,名册,生命周期,每成员待投上限,最大消息字节):#构造
        '记下依赖与部署限制'
        自身.ctx=上下文#上下文
        自身._日志=日志#日志
        自身._名册=名册#成员表
        自身._生命周期=生命周期#生命周期
        自身._每成员待投上限=每成员待投上限#待投上限
        自身._最大消息字节=最大消息字节#消息字节上限
        自身._投递尾={}#按目标串行尾
        自身._飞行中消息=set()#飞行中消息
        自身._飞行中投递=set()#飞行中投递
        自身._尾锁=互斥锁()#队尾锁

    def 发送(自身,调用方,请求):#发消息
        '排队一条持久 peer 消息，再尝试即时投递。返回期约，兑现值是消息 id 与投递状态'
        if 自身._生命周期.已拆除:#已拆除
            raise 团队错误('Agent Teams service is disposing','TEAM_DISPOSED')#已拆除
        合并=dict(请求)#拷贝
        合并['signal']=合成中止(请求['signal'] if 'signal' in 请求 else None,自身._生命周期.信号)#合并取消
        return 自身._跟踪投递(自身._已准入发送(调用方,合并))#跟踪投递

    def 观察会话事件(自身,会话,事件):#观察会话事件
        '观察目标侧持久回执，并 checkpoint 其 Lead 日志确认'
        if 自身._生命周期.已拆除:#已拆除
            return#跳过
        if 'type' not in 事件 or 事件['type']!='user/message':#非用户消息
            return#跳过
        if 'data' not in 事件:#无载荷
            return#跳过
        数据=事件['data']#载荷
        if 'source' not in 数据:#无来源
            return#跳过
        来源=数据['source']#来源
        if 来源 is None or 'kind' not in 来源 or 来源['kind']!='team-message':#非团队消息
            return#跳过
        启动=期约()#确认在登记在途之后才开始
        def 确认(启动值):#确认任务
            '写 delivered 边，返回期约'
            根=自身.ctx.agents.get(来源['teamId'])#取 Lead
            if 根 is not None:#有 Lead
                return 自身._检查点已投递(根,会话,来源['messageId'])#确认
        def 记录确认失败(错误):#确认失败
            '确认失败只写警告，不影响会话事件发布'
            自身.ctx.日志.警告(f"团队消息 \"{来源['messageId']}\" 确认失败：{错误文案(错误)}")#警告
        确认结果=启动.然后(确认).捕获(记录确认失败)#失败被消化，不会拒绝
        自身._跟踪投递(确认结果)#跟踪
        启动.解决(None)#在途已登记，开始确认

    def 恢复(自身,智能体,信号):#恢复投递
        '重试与一个已启动 Team 成员相关的持久待投消息。返回期约，全部尝试完后兑现'
        若已中止则抛出(信号)#取消
        关系=自身._名册.试成员关系(智能体)#试成员
        链=期约()#逐条投递的链起点
        链.解决(None)#已结算，第一条立即开始
        if 关系 is None:#非成员
            return 链#没有可恢复的消息
        状态=自身._日志.状态(关系['root'])#状态
        消息列表=[#待投且相关
            消息 for 消息 in 状态['messages']#扫
            if 消息['id'] not in 状态['delivered']#未投递
            and (关系['role']=='lead' or 消息['targetId']==智能体.id)#相关
        ]#过滤结束
        for 消息 in 消息列表:#逐条
            def 投递一条(前一条结果,待投消息=消息):#前一条尝试完后
                '取消检查后尝试投递一条，按顺序逐条进行'
                若已中止则抛出(信号)#取消
                return 自身._尝试投递(关系['root'],待投消息,信号)#尝试投递
            链=链.然后(投递一条)#排在上一条之后
        return 链#全部尝试完后兑现

    def 列出待投递(自身):#飞行中投递
        '返回为拆除捕获的已准入投递与确认操作'
        return list(自身._飞行中投递)#快照

    def _已准入发送(自身,调用方,请求):#已准入发送
        '排队并投递在拆除截止前已准入的一条邮箱项'
        关系=自身._名册.成员关系(调用方)#成员
        若已中止则抛出(请求['signal'] if 'signal' in 请求 else None)#取消
        根=关系['root']#Lead
        内容=copy.deepcopy(请求['content'])#克隆内容
        def 操作():#事务
            '入队并登记投递'
            若已中止则抛出(请求['signal'] if 'signal' in 请求 else None)#取消
            状态=自身._日志.状态(根)#状态
            目标=解析活跃成员(根,状态,请求['target'])#目标
            if 目标['id']==调用方.id:#禁自消息
                raise 团队错误('a Team member cannot message itself','TEAM_SELF_MESSAGE')#禁自消息
            待投数=len([#待投数
                候选 for 候选 in 状态['messages']#扫
                if 候选['targetId']==目标['id'] and 候选['id'] not in 状态['delivered']#待投
            ])#计数
            if 待投数>=自身._每成员待投上限:#邮箱满
                raise 团队错误(#满
                    'teammate "'+目标['name']+'" has '+str(待投数)+' pending messages',#文案
                    'TEAM_MAILBOX_FULL',#码
                )#抛出
            已入队={#消息快照
                'id':团队消息标识('team-message-'+str(uuid.uuid4())),#新消息 id
                'senderId':调用方.id,#发送方
                'senderName':关系['name'],#发送方名
                'targetId':目标['id'],#目标
                'content':内容,#内容
            }#快照结束
            字节数=len(紧凑json编码(自身._投递内容(已入队)).encode('utf-8'))#字节
            if 字节数>自身._最大消息字节:#过大
                raise 团队错误('team message exceeds '+str(自身._最大消息字节)+' bytes','TEAM_MESSAGE_TOO_LARGE')#过大
            def 登记投递(刷新值):#入队已持久
                '持久化成功后、释放根事务前登记即时投递，让并发发送方按持久顺序进入目标队列'
                return {'message':已入队,'dispatch':自身._尝试投递(根,已入队,请求['signal'] if 'signal' in 请求 else None)}#投递已开始
            return 自身._日志.追加并刷新(根,'team/message/queued',{#入队
                'version':2,#版本
                'teamId':团队标识(根.id),#团队
                'message':已入队,#消息
            }).然后(登记投递)#追加结束
        def 等即时投递(已排队):#入队事务结束
            '等已开始的即时投递，汇报是否已被接受'
            def 汇报(已接受):#即时投递结束
                '按即时投递结果给出观察状态'
                return {'messageId':已排队['message']['id'],'status':'accepted' if 已接受 else 'queued'}#观察
            return 已排队['dispatch'].然后(汇报)#等即时投递
        return 自身._日志.事务(根.id,操作).然后(等即时投递)#串行入队后再等投递

    def _尝试投递(自身,根,消息,信号):#尝试投递
        '本进程内同一时间只尝试一次已排队消息。返回期约，兑现值是是否已投递'
        if 自身._生命周期.已拆除 or 消息['id'] in 自身._飞行中消息:#已拆除或已在飞
            未尝试结果=期约()#不再尝试
            未尝试结果.解决(False)#视为未投递
            return 未尝试结果
        自身._飞行中消息.add(消息['id'])#标记
        def 遗忘(结算值):#本次尝试结算
            '尝试结算后遗忘飞行标记'
            自身._飞行中消息.discard(消息['id'])#遗忘
        尝试=自身._跟踪投递(自身._已准入尝试投递(根,消息,合成中止(信号,自身._生命周期.信号)))#合并取消并跟踪
        尝试.然后(遗忘,遗忘)#无论成败都遗忘
        return 尝试#尝试结果

    def _跟踪投递(自身,操作):#跟踪投递
        '跟踪一次投递事务直到结算；操作是期约，原样返回'
        自身._飞行中投递.add(操作)#登记
        def 摘除(结算值):#操作结算
            '操作结算后不再跟踪'
            自身._飞行中投递.discard(操作)#摘
        操作.然后(摘除,摘除)#无论成败都摘
        return 操作#调用方观察结果

    def _已准入尝试投递(自身,根,消息,信号):#已准入投递
        '尝试在服务生命周期截止前已准入的一条排队消息'
        def 穿过():#串行体
            '投递穿过'
            return 自身._投递穿过(根,消息,信号)#穿过
        return 自身._串行投递(消息,穿过)#串行

    def _串行投递(自身,消息,操作):#串行投递
        '按排队顺序为一个持久目标串行化投递准入。操作无参，返回值或期约；本方法返回期约'
        目标标识=消息['targetId']#目标
        本尾=期约()#本投递结清后兑现，后来的投递排在它后面
        with 自身._尾锁:#交换队尾必须原子
            if 目标标识 in 自身._投递尾:#已有前驱
                前驱=自身._投递尾[目标标识]#排在前驱之后
            else:#没有前驱
                前驱=期约()#空前驱
                前驱.解决(None)#已结算，立即可跑
            自身._投递尾[目标标识]=本尾#更新尾
        def 运行操作(前驱结果):#前驱结算后
            '无论前驱成败都运行本投递'
            return 操作()#操作的返回值或期约
        运行=前驱.然后(运行操作,运行操作)#前驱成功或失败都轮到本投递
        def 结清(运行结果):#本投递结算后
            '清掉仍是自己的队尾并放行后来的投递'
            with 自身._尾锁:#读写队尾表
                if 目标标识 in 自身._投递尾 and 自身._投递尾[目标标识] is 本尾:#仍是自己
                    del 自身._投递尾[目标标识]#清尾
            本尾.解决(None)#放行后来的投递，不传递本投递的成败
        运行.然后(结清,结清)#队尾只跟踪结算，不观察对错
        return 运行#调用方观察本投递结果

    def _投递穿过(自身,根,消息,信号):#投递到目标
        '按持久队列顺序，经 message 投递该目标的每一条待投消息。返回期约，兑现值是是否全部投递成功'
        状态=自身._日志.状态(根)#状态
        待投=[#该目标待投
            候选 for 候选 in 状态['messages']#扫
            if 候选['targetId']==消息['targetId'] and 候选['id'] not in 状态['delivered']#待投
        ]#过滤
        请求位置=-1#请求位置
        for 下标,候选 in enumerate(待投):#找位置
            if 候选['id']==消息['id']:#命中
                请求位置=下标#记下
                break#结束
        链=期约()#逐条投递的链起点，兑现值表示到目前为止是否全部成功
        if 请求位置<0:#已投或不在队列
            链.解决(消息['id'] in 状态['delivered'])#是否已投
            return 链
        链.解决(True)#还没有失败
        def 清自持标记(自持,待投消息):#本条结算后
            '本条结算后清掉自持的飞行标记'
            if 自持:#自持
                自身._飞行中消息.discard(待投消息['id'])#遗忘
        for 候选 in 待投[:请求位置+1]:#到请求为止
            def 投递一条(此前全部成功,待投消息=候选):#前一条投递结束后
                '前面都成功才投递本条；一条失败则其后不再尝试'
                if not 此前全部成功:#前面已失败
                    return False#停
                自持=待投消息['id'] not in 自身._飞行中消息#是否自持飞行标记
                if 自持:#自持
                    自身._飞行中消息.add(待投消息['id'])#标记
                return 自身._单次投递(根,待投消息,信号).最终(偏函数(清自持标记,自持,待投消息))#失败则链上后续跳过
            链=链.然后(投递一条)#排在上一条之后
        return 链#全部成功才为 True

    def _单次投递(自身,根,消息,信号):#单次投递
        '在目标本地排序准入后尝试一次排队投递。返回期约，兑现值是是否已交付；失败只写警告并兑现 False'
        启动=期约()#主体在登记之后才开始
        def 投递(启动值):#开始
            '开始单次投递；同步抛出也转成拒绝'
            return 自身._单次投递体(根,消息,信号)#体
        def 记录保留排队(错误):#投递失败
            '失败时消息保持排队并写警告'
            标识=消息['id']#消息 id
            自身.ctx.日志.警告(f'团队消息 "{标识}" 保持排队：{错误文案(错误)}')#警告
            return False#未交付
        结果=启动.然后(投递).捕获(记录保留排队)#失败被消化为 False
        启动.解决(None)#开始
        return 结果

    def _单次投递体(自身,根,消息,信号):#单次投递体
        '单次投递的主体逻辑。返回期约（或值），兑现值是是否已交付'
        目标=根 if 消息['targetId']==根.id else 自身.ctx.agents.get(消息['targetId'])#目标 agent
        if 目标 is not None and 自身._目标已记录(目标.session,消息['id']):#已记录则确认
            return 自身._检查点已投递(根,目标.session,消息['id'])#确认
        来源={#消息来源
            'kind':'team-message',#种类
            'teamId':团队标识(根.id),#团队
            'messageId':消息['id'],#消息
            'senderId':消息['senderId'],#发送方
            'senderName':消息['senderName'],#发送方名
        }#来源结束
        内容=自身._投递内容(消息)#成帧内容
        if 消息['targetId']==根.id:#Steer Lead
            输入=创建用户消息({'content':内容,'source':来源})#用户消息
            根.steer(输入)#Steer Lead
            return 自身._检查点已投递(根,根.session,消息['id'])#确认
        def 确认交付(跟进值):#跟进完成
            '跟进后确认交付'
            if 目标 is None:#冷恢复路径视为已交
                return True#成功
            return 自身._检查点已投递(根,目标.session,消息['id'])#live 确认
        def 跟进并确认(跟进前值):#交给宿主跟进
            '交给宿主跟进目标；live 目标再 checkpoint 确认，冷恢复路径视为已交'
            return 自身.ctx.subagents.跟进(根,消息['targetId'],内容,{#宿主跟进子
                'source':来源,#来源
                'signal':信号,#取消
            }).然后(确认交付)#跟进结束
        if 目标 is None:#冷路径
            def 已标记(标记值):#标记完成
                '标记完成即视为成功'
                return True#成功
            def 处理冷路径(已记录):#读完持久目标
                '按持久目标是否已记录决定：保持排队、标记已投或跟进'
                if 已记录 is None:#不确定
                    return False#保持排队
                if 已记录:#已有则标记
                    return 自身._标记已投递(根,消息['id'],消息['targetId']).然后(已标记)#标记
                return 跟进并确认(None)#目标尚未记录，跟进
            return 自身._持久目标已记录(消息['targetId'],消息['id'],信号).然后(处理冷路径)#读持久目标
        return 跟进并确认(None)#live 目标

    def _检查点已投递(自身,根,目标,消息标识):#检查点投递
        '在 Lead 记录 delivered 边之前 flush 一次 live 目标回执。返回期约，兑现值是是否已记录并标记'
        def 标记完成(标记值):#标记完成
            '标记完成即视为成功'
            return True#成功
        def 刷新后(刷新值):#flush 完成
            '确认目标已记录后写 delivered 边'
            if not 自身._目标已记录(目标,消息标识):#仍未记录
                return False#失败
            return 自身._标记已投递(根,消息标识,目标.id).然后(标记完成)#写 delivered
        return 自身.ctx.sessions.flush(目标).然后(刷新后)#flush 目标

    def _标记已投递(自身,根,消息标识,目标标识):#标记已投
        '记录投递，除非确认已存在。返回期约'
        def 操作():#事务
            '条件写 delivered'
            状态=自身._日志.状态(根)#状态
            if 消息标识 in 状态['delivered']:#已有
                return#跳过
            已入队=None#查找
            for 消息 in 状态['messages']:#扫
                if 消息['id']==消息标识:#命中
                    已入队=消息#记下
                    break#结束
            if 已入队 is None or 已入队['targetId']!=目标标识:#不一致
                return#跳过
            return 自身._日志.追加并刷新(根,'team/message/delivered',{#写 delivered
                'version':2,#版本
                'teamId':团队标识(根.id),#团队
                'messageId':消息标识,#消息
                'targetId':目标标识,#目标
            })#追加结束
        return 自身._日志.事务(根.id,操作)#串行

    def _目标已记录(自身,会话,消息标识):#目标是否已记录
        '目标 Session 是否已含该持久消息身份'
        后缀=会话.snapshotEvents(会话.inheritedEventCount)#后缀
        return 消息已接受(后缀,_团队消息谓词(消息标识))#是否命中

    def _投递内容(自身,消息):#投递内容
        '为接收模型把 peer 内容成帧为稳定发送方与消息身份'
        return [#成帧
            {'type':'text','text':'Team message '+消息['id']+' from '+消息['senderName']+':'},#前缀
        ]+copy.deepcopy(消息['content'])#原内容

    def _持久目标已记录(自身,目标标识,消息标识,信号):#持久目标是否已记录
        '冷恢复前读 inactive 目标的持久日志；不确定则保持邮箱排队。返回期约，兑现值是 True、False 或 None（不确定）'
        def 判定(已存):#读完持久会话
            '目标持久日志中是否已含该消息'
            后缀=已存['events'][已存['inheritedEventCount']:]#后缀
            return 消息已接受(后缀,_团队消息谓词(消息标识))#是否命中
        def 记录读取失败(错误):#读取失败
            '读取失败时不确定，保持排队并写警告'
            自身.ctx.日志.警告(f'无法读取团队消息目标 "{目标标识}"：{错误文案(错误)}')#警告
            return None#不确定
        return 读持久会话(自身.ctx.sessionPersistence,目标标识,信号).然后(判定).捕获(记录读取失败)#读失败即不确定
