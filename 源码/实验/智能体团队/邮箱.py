"""持久 Team 邮箱：准入、目标本地投递、确认与恢复。

对齐上游 `agent-team/src/mailbox.ts`。公开面仅中文名。
"""
import copy,json,threading,uuid#克隆、字节计、串行、消息 id
from ...内核.智能体循环.辅助 import 解开,抛若中止,操作任务#等待与取消
from ...工具.超时 import 合成信号#AbortSignal.any
from ...模型后端.llm import 创建用户消息#用户消息工厂
from .错误 import 团队错误,错误文案#领域错误
from .持久化 import 读持久会话#持久读取
from .名册 import 解析活跃成员#活跃成员
from .会话消息 import 消息已接受#消息接受
from .类型 import 团队标识,团队消息标识#身份

__all__=['团队邮箱']#仅中文公开名

def 取字段(对象,键,缺省=None):#读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

class 团队邮箱:#团队邮箱
    """拥有持久 Team 邮箱的每一个进程内状态转换。"""
    def __init__(自身,上下文,日志,名册,生命周期,每成员待投上限,最大消息字节):#构造
        """记下依赖与部署限制。"""
        自身.ctx=上下文#上下文
        自身._日志=日志#日志
        自身._名册=名册#成员表
        自身._生命周期=生命周期#生命周期
        自身._每成员待投上限=每成员待投上限#待投上限
        自身._最大消息字节=最大消息字节#消息字节上限
        自身._投递尾={}#按目标串行尾
        自身._飞行中消息=set()#飞行中消息
        自身._飞行中投递=set()#飞行中投递
        自身._尾锁=threading.Lock()#队尾锁

    def 发送(自身,调用方,请求):#发消息
        """排队一条持久 peer 消息，再尝试即时投递。"""
        if 自身._生命周期.已处置:#已处置
            raise 团队错误('Agent Teams service is disposing','TEAM_DISPOSED')#已处置
        if isinstance(请求,dict):#映射请求
            合并=dict(请求)#拷贝
        else:#对象请求
            合并={#展开
                'target':取字段(请求,'target'),#目标
                'content':取字段(请求,'content'),#内容
                'signal':取字段(请求,'signal'),#信号
            }#展开结束
        合并['signal']=合成信号(取字段(请求,'signal'),自身._生命周期.信号)#合并取消
        return 自身._跟踪投递(lambda:自身._已准入发送(调用方,合并))#跟踪投递

    def 观察会话事件(自身,会话,事件):#观察会话事件
        """观察目标侧持久回执，并 checkpoint 其 Lead 日志确认。"""
        if 自身._生命周期.已处置:#已处置
            return#跳过
        if 取字段(事件,'type')!='user/message':#非用户消息
            return#跳过
        来源=取字段(取字段(事件,'data'),'source')#来源
        if 取字段(来源,'kind')!='team-message':#非团队消息
            return#跳过
        def 确认():#确认任务
            """写 delivered 边。"""
            try:#试确认
                根=自身.ctx.agents.get(取字段(来源,'teamId'))#取 Lead
                if 根 is not None:#有 Lead
                    自身._检查点已投递(根,会话,取字段(来源,'messageId'))#确认
            except Exception as 错误:#记警告
                自身.ctx.logger.warn('Team message "'+str(取字段(来源,'messageId'))+'" acknowledgement failed: '+错误文案(错误))#警告
        自身._跟踪投递(确认)#跟踪

    def 恢复(自身,智能体,信号):#恢复投递
        """重试与一个已启动 Team 成员相关的持久待投消息。"""
        抛若中止(信号)#取消
        关系=自身._名册.试成员关系(智能体)#试成员
        if 关系 is None:#非成员
            return#返回
        状态=自身._日志.状态(关系['root'])#状态
        消息们=[#待投且相关
            消息 for 消息 in 状态['messages']#扫
            if 消息['id'] not in 状态['delivered']#未投递
            and (关系['role']=='lead' or 消息['targetId']==智能体.id)#相关
        ]#过滤结束
        for 消息 in 消息们:#逐条
            抛若中止(信号)#取消
            自身._尝试投递(关系['root'],消息,信号)#尝试投递

    def 待投递们(自身):#飞行中投递
        """返回为处置捕获的已准入投递与确认操作。"""
        return list(自身._飞行中投递)#快照

    def _已准入发送(自身,调用方,请求):#已准入发送
        """排队并投递在处置截止前已准入的一条邮箱项。"""
        关系=自身._名册.成员关系(调用方)#成员
        抛若中止(取字段(请求,'signal'))#取消
        根=关系['root']#Lead
        内容=copy.deepcopy(取字段(请求,'content'))#克隆内容
        def 操作():#事务
            """入队并登记投递。"""
            抛若中止(取字段(请求,'signal'))#取消
            状态=自身._日志.状态(根)#状态
            目标=解析活跃成员(根,状态,取字段(请求,'target'))#目标
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
            字节数=len(json.dumps(自身._投递内容(已入队),ensure_ascii=False,separators=(',',':')).encode('utf-8'))#字节
            if 字节数>自身._最大消息字节:#过大
                raise 团队错误('team message exceeds '+str(自身._最大消息字节)+' bytes','TEAM_MESSAGE_TOO_LARGE')#过大
            自身._日志.追加并刷新(根,'team/message/queued',{#入队
                'version':2,#版本
                'teamId':团队标识(根.id),#团队
                'message':已入队,#消息
            })#追加结束
            return {'message':已入队,'dispatch':lambda:自身._尝试投递(根,已入队,取字段(请求,'signal'))}#先登记投递
        已排队=自身._日志.事务(根.id,操作)#串行入队
        已接受=已排队['dispatch']()#等即时投递
        return {'messageId':已排队['message']['id'],'status':'accepted' if 已接受 else 'queued'}#观察

    def _尝试投递(自身,根,消息,信号):#尝试投递
        """本进程内同一时间只尝试一次已排队消息。"""
        if 自身._生命周期.已处置:#已处置
            return False#失败
        if 消息['id'] in 自身._飞行中消息:#已在飞
            return False#跳过
        自身._飞行中消息.add(消息['id'])#标记
        try:#投递
            return 自身._跟踪投递(lambda:自身._已准入尝试投递(#已准入
                根,消息,合成信号(信号,自身._生命周期.信号),#合并取消
            ))#跟踪
        finally:#遗忘
            自身._飞行中消息.discard(消息['id'])#遗忘

    def _跟踪投递(自身,操作):#跟踪投递
        """经投递准入或受控失败跟踪一次投递事务。"""
        任务=操作任务()#跟踪句柄
        自身._飞行中投递.add(任务)#登记
        try:#执行
            结果=操作()#跑
            任务.兑现(结果)#成功
            return 结果#返回
        except Exception as 错误:#失败
            任务.拒绝(错误)#失败
            raise#上抛
        finally:#摘
            自身._飞行中投递.discard(任务)#摘

    def _已准入尝试投递(自身,根,消息,信号):#已准入投递
        """尝试在服务生命周期截止前已准入的一条排队消息。"""
        return 自身._串行投递(消息,lambda:自身._投递穿过(根,消息,信号))#串行

    def _串行投递(自身,消息,操作):#串行投递
        """按排队顺序为一个持久目标串行化投递准入。"""
        目标标识=消息['targetId']#目标
        with 自身._尾锁:#取先前尾
            先前=自身._投递尾.get(目标标识)#前尾
            门=threading.Event()#本尾
            自身._投递尾[目标标识]=门#更新尾
        if 先前 is not None:#等先前
            先前.wait()#前后都跑
        try:#跑
            return 操作()#结果
        finally:#清尾
            门.set()#放行
            with 自身._尾锁:#仍是自己则清
                if 自身._投递尾.get(目标标识) is 门:#仍是自己
                    自身._投递尾.pop(目标标识,None)#清尾

    def _投递穿过(自身,根,消息,信号):#投递到目标
        """按持久队列顺序，经 message 投递该目标的每一条待投消息。"""
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
        if 请求位置<0:#已投或不在队列
            return 消息['id'] in 状态['delivered']#是否已投
        for 候选 in 待投[:请求位置+1]:#到请求为止
            自持=候选['id'] not in 自身._飞行中消息#是否自持飞行标记
            if 自持:#自持
                自身._飞行中消息.add(候选['id'])#标记
            try:#单次
                if not 自身._单次投递(根,候选,信号):#失败停
                    return False#失败
            finally:#清自持
                if 自持:#自持
                    自身._飞行中消息.discard(候选['id'])#遗忘
        return True#全部成功

    def _单次投递(自身,根,消息,信号):#单次投递
        """在目标本地排序准入后尝试一次排队投递。"""
        try:#试投递
            return 自身._单次投递体(根,消息,信号)#体
        except Exception as 错误:#保持排队
            自身.ctx.logger.warn('team message "'+消息['id']+'" remains queued: '+错误文案(错误))#警告
            return False#失败

    def _单次投递体(自身,根,消息,信号):#单次投递体
        """单次投递的主体逻辑。"""
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
        if 目标 is None:#冷路径
            已记录=自身._持久目标已记录(消息['targetId'],消息['id'],信号)#读持久目标
            if 已记录 is None:#不确定
                return False#保持排队
            if 已记录:#已有则标记
                自身._标记已投递(根,消息['id'],消息['targetId'])#标记
                return True#成功
        解开(自身.ctx.subagents.跟进(根,消息['targetId'],内容,{#宿主跟进子
            'source':来源,#来源
            'signal':信号,#取消
        }))#跟进结束
        if 目标 is None:#冷恢复路径视为已交
            return True#成功
        return 自身._检查点已投递(根,目标.session,消息['id'])#live 确认

    def _检查点已投递(自身,根,目标,消息标识):#检查点投递
        """在 Lead 记录 delivered 边之前 flush 一次 live 目标回执。"""
        解开(自身.ctx.sessions.flush(目标))#flush 目标
        if not 自身._目标已记录(目标,消息标识):#仍未记录
            return False#失败
        自身._标记已投递(根,消息标识,目标.id)#写 delivered
        return True#成功

    def _标记已投递(自身,根,消息标识,目标标识):#标记已投
        """记录投递，除非确认已存在。"""
        def 操作():#事务
            """条件写 delivered。"""
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
            自身._日志.追加并刷新(根,'team/message/delivered',{#写 delivered
                'version':2,#版本
                'teamId':团队标识(根.id),#团队
                'messageId':消息标识,#消息
                'targetId':目标标识,#目标
            })#追加结束
        自身._日志.事务(根.id,操作)#串行

    def _目标已记录(自身,会话,消息标识):#目标是否已记录
        """目标 Session 是否已含该持久消息身份。"""
        后缀=会话.snapshotEvents(会话.inheritedEventCount)#后缀
        def 谓词(消息):#谓词
            """匹配团队消息身份。"""
            来源=取字段(消息,'source')#来源
            return 取字段(来源,'kind')=='team-message' and 取字段(来源,'messageId')==消息标识#匹配
        return 消息已接受(后缀,谓词)#是否命中

    def _投递内容(自身,消息):#投递内容
        """为接收模型把 peer 内容成帧为稳定发送方与消息身份。"""
        return [#成帧
            {'type':'text','text':'Team message '+消息['id']+' from '+消息['senderName']+':'},#前缀
        ]+copy.deepcopy(消息['content'])#原内容

    def _持久目标已记录(自身,目标标识,消息标识,信号):#持久目标是否已记录
        """冷恢复前读 inactive 目标的持久日志；不确定则保持邮箱排队。"""
        try:#读
            已存=读持久会话(自身.ctx.sessionPersistence,目标标识,信号)#读
            后缀=已存['events'][已存['inheritedEventCount']:]#后缀
            def 谓词(消息):#谓词
                """匹配团队消息身份。"""
                来源=取字段(消息,'source')#来源
                return 取字段(来源,'kind')=='team-message' and 取字段(来源,'messageId')==消息标识#匹配
            return 消息已接受(后缀,谓词)#是否命中
        except Exception as 错误:#不确定
            自身.ctx.logger.warn('cannot read Team message target "'+str(目标标识)+'": '+错误文案(错误))#警告
            return None#不确定
