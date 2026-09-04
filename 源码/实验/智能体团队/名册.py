"""Team 成员关系、可延续子代供应，以及 roster 拥有的拆除。

对齐上游 `agent-team/src/roster.ts`。公开面仅中文名。
"""
import re,uuid#名字模式与预留子 id
from ...内核.智能体循环.辅助 import 解开,抛若中止,中止原因,听中止,摘中止,操作任务#取消与等待
from ...工具.超时 import 合成信号#AbortSignal.any
from ...子智能体.子智能体 import 折叠子智能体描述符#描述符折叠
from .错误 import 团队错误,错误文案#领域错误
from .持久化 import 读持久会话#持久读取
from .会话消息 import 消息已接受#消息接受
from .类型 import 团队标识#TeamId
from .校验 import 必填文本#必填文本

__all__=['解析活跃成员','团队名册']#仅中文公开名

成员名模式=re.compile(r'^[a-z0-9]+(?:-[a-z0-9]+)*$')#小写 kebab 名字

def 取字段(对象,键,缺省=None):#读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

def 解析活跃成员(根,状态,原始名):#解析活跃成员
    """按面向模型的名字解析一个活跃 Team 成员，含 Lead 伪行。"""
    名字=原始名.strip()#修剪
    if 名字=='lead':#Lead 伪行
        return {'id':根.id,'name':名字}#Lead
    成员=None#查找
    for 候选 in 状态['members']:#按名找
        if 候选['name']==名字:#命中
            成员=候选#记下
            break#结束
    if 成员 is None or 成员['phase']!='active':#未找到
        raise 团队错误('active teammate "'+名字+'" not found','TEAM_MEMBER_NOT_FOUND')#未找到
    return {'id':成员['id'],'name':名字}#命中

class 团队名册:#成员表
    """拥有 Team 身份与 roster 可延续子代的生命周期。"""
    def __init__(自身,上下文,日志,生命周期,最大成员数):#构造
        """记下上下文、日志、生命周期与成员上限。"""
        自身.ctx=上下文#服务上下文
        自身._日志=日志#日志
        自身._生命周期=生命周期#生命周期
        自身._最大成员数=最大成员数#成员上限
        自身._飞行中创建=set()#飞行中创建

    def 成员关系(自身,智能体):#解析成员
        """解析一个精确 live Agent 的 Team 角色。"""
        关系=自身.试成员关系(智能体)#试解析
        if 关系 is None:#非成员
            raise 团队错误('agent "'+str(智能体.id)+'" is not a member of an active Agent Team','TEAM_NOT_MEMBER')#非成员
        return 关系#命中

    def 试成员关系(自身,智能体):#试解析成员
        """不抛错地解析调用方，供 scoped 安装与生命周期观察者使用。"""
        if 自身.ctx.agents.get(智能体.id) is not 智能体:#非精确 live
            return None#非成员
        try:#探测
            return 自身._试成员关系体(智能体)#体
        except Exception:#探测失败不否决
            return None#失败

    def _试成员关系体(自身,智能体):#试解析体
        """试成员关系的主体逻辑。"""
        父标识=取字段(取字段(智能体.session,'header'),'parentSession')#父 Session
        if 父标识 is not None:#有父
            根=自身.ctx.agents.get(父标识)#取 Lead
            if 根 is not None:#有 Lead
                成员=None#roster 行
                for 候选 in 自身._日志.状态(根)['members']:#扫
                    if 候选['id']==智能体.id:#命中
                        成员=候选#记下
                        break#结束
                if 成员 is not None and 成员['phase'] in ('active','provisioning'):#teammate
                    return {'root':根,'id':团队标识(根.id),'role':'teammate','name':成员['name']}#teammate
                if 自身._子智能体描述符(智能体):#provider 子代
                    return None#非团队
                return {'root':智能体,'id':团队标识(智能体.id),'role':'lead','name':'lead'}#独立根
        if 自身._子智能体描述符(智能体):#无父的 subagent
            return None#非团队
        return {'root':智能体,'id':团队标识(智能体.id),'role':'lead','name':'lead'}#隐式 Lead

    def 列表(自身,成员关系):#列 roster
        """列出一个 Team 成员可见的、经运行时充实的 roster。"""
        根=成员关系['root']#Lead
        状态=自身._日志.状态(根)#状态
        结果=[{#Lead 行
            'id':根.id,#Lead id
            'name':'lead',#伪名
            'role':'lead',#角色
            'status':根.status,#运行时状态
            'diagnostics':[],#无诊断
        }]#Lead 结束
        模型=取字段(取字段(根,'options'),'model')#Lead 模型
        if 模型 is not None:#有模型
            结果[0]['model']=模型#展开
        for 成员 in 状态['members']:#逐 teammate
            结果.append(自身._充实成员行(根,成员))#追加
        return 结果#含 Lead

    def _充实成员行(自身,根,成员):#充实一行
        """从持久快照派生运行时成员行。"""
        活=自身.ctx.agents.get(成员['id'])#live agent
        模型=取字段(取字段(活,'options'),'model') if 活 is not None else None#活模型
        if 模型 is None:#回退 Lead
            模型=取字段(取字段(根,'options'),'model')#Lead 模型
        if 成员['phase']=='failed':#失败
            状态='failed'#失败
        elif 成员['phase']=='provisioning':#供应中
            状态='provisioning'#供应
        else:#派生
            状态=活.status if 活 is not None else 'inactive'#派生状态
        行={#成员行
            'id':成员['id'],#id
            'name':成员['name'],#名
            'role':'teammate',#角色
            'status':状态,#状态
            'description':成员['description'],#描述
            'provider':成员['provider'],#provider
            'context':成员['context'],#上下文
            'diagnostics':[] if 成员.get('error') is None else [成员['error']],#诊断
        }#行骨架
        if 模型 is not None:#有模型
            行['model']=模型#展开
        return 行#行

    def 创建(自身,调用方,请求):#创建 teammate
        """创建一个具名、可延续的 Team Lead 直接子代。"""
        if 自身._生命周期.已处置:#已处置
            raise 团队错误('Agent Teams service is disposing','TEAM_DISPOSED')#已处置
        操作=操作任务()#飞行跟踪用
        自身._飞行中创建.add(操作)#跟踪
        try:#等待
            结果=自身._已准入创建(调用方,请求)#已准入创建
            操作.兑现(结果)#兑现跟踪
            return 结果#返回
        except Exception as 错误:#失败
            操作.拒绝(错误)#拒绝跟踪
            raise#上抛
        finally:#摘跟踪
            自身._飞行中创建.discard(操作)#摘跟踪

    def 待创建们(自身):#飞行中创建
        """返回为有序处置捕获的已准入创建操作。"""
        return list(自身._飞行中创建)#快照

    def 恢复(自身,智能体,信号):#恢复供应
        """当一个 Team 成员 Session 启动时对账供应状态。"""
        抛若中止(信号)#已取消
        关系=自身.试成员关系(智能体)#试成员
        if 关系 is not None and 关系['role']=='lead':#Lead 对账
            自身._对账供应(关系['root'],信号)#对账

    def 中断(自身,调用方,目标名):#中断
        """中断一个 live teammate 轮次，不清理其 pending inbox。"""
        关系=自身.成员关系(调用方)#解析
        if 关系['role']!='lead':#仅 Lead
            raise 团队错误('only the Team Lead can interrupt teammates','TEAM_LEAD_REQUIRED')#仅 Lead
        状态=自身._日志.状态(关系['root'])#状态
        目标=解析活跃成员(关系['root'],状态,目标名)#目标
        if 目标['id']==关系['root'].id:#禁自中断
            raise 团队错误('the Team Lead cannot interrupt itself','TEAM_INVALID_TARGET')#禁自中断
        活=自身.ctx.agents.get(目标['id'])#live
        if 活 is None:#未加载
            return {'previousStatus':'inactive'}#未加载
        先前=活.status#采样
        自身.ctx.subagents.打断(目标['id'],{'kind':'ancestor','agent':调用方})#祖先中断
        return {'previousStatus':先前}#返回

    def 按根分组活子(自身):#按根分组子代
        """按当前 Lead 分组精确 live roster 子代，供运行时拆除。"""
        团队们={}#结果
        for 智能体 in 自身.ctx.agents.list():#扫全部
            根标识=取字段(取字段(智能体.session,'header'),'parentSession')#父
            if 根标识 is None:#无父
                continue#下一
            根=自身.ctx.agents.get(根标识)#Lead
            if 根 is None:#无 Lead
                continue#下一
            if not any(成员['id']==智能体.id for 成员 in 自身._日志.状态(根)['members']):#非 roster
                continue#下一
            子们=团队们.get(根)#桶
            if 子们 is None:#新建
                子们=[]#空
                团队们[根]=子们#挂上
            子们.append(智能体.id)#追加
        return 团队们#分组

    def 停止队友们(自身,根,子标识们):#停 teammate
        """经延续生命周期所有者释放精确 teammate Activation。"""
        自身._生命周期.有界等待(自身.ctx.subagents.排空可续跑后代([根]))#有界 drain

    def _已准入创建(自身,调用方,请求):#已准入创建
        """执行在 Team 运行时处置截止前已准入的一次创建。"""
        关系=自身.成员关系(调用方)#解析
        if 关系['role']!='lead':#仅 Lead
            raise 团队错误('only the Team Lead can create teammates','TEAM_LEAD_REQUIRED')#仅 Lead
        信号=合成信号(取字段(请求,'signal'),自身._生命周期.信号)#合并取消
        抛若中止(信号)#已取消
        根=关系['root']#Lead
        名字=自身._成员名(取字段(请求,'name'))#校验名
        描述=必填文本(取字段(请求,'description'),'description',200)#描述
        子标识=str(uuid.uuid4())#预留子 id
        成员={#供应快照
            'id':子标识,#子 id
            'name':名字,#名
            'description':描述,#描述
            'provider':必填文本(取字段(请求,'provider'),'provider',200),#provider
            'context':取字段(请求,'context'),#上下文
            'phase':'provisioning',#供应中
        }#快照结束
        自身._持久供应(根,名字,成员)#持久供应边
        return 自身._启动并结算(根,名字,成员,请求,信号)#启动结算

    def _持久供应(自身,根,名字,成员):#持久供应边
        """在 Lead 日志写入 provisioning 边。"""
        def 操作():#事务
            """检查名占用与上限后追加。"""
            状态=自身._日志.状态(根)#状态
            if any(候选['name']==名字 for 候选 in 状态['members']):#名占用
                raise 团队错误('teammate name "'+名字+'" was already used in this Team','TEAM_MEMBER_NAME_TAKEN')#占用
            if len(状态['members'])>=自身._最大成员数:#上限
                raise 团队错误('Team member limit '+str(自身._最大成员数)+' reached','TEAM_MEMBER_LIMIT')#上限
            自身._日志.追加并刷新(根,'team/member',{'version':2,'teamId':团队标识(根.id),'member':成员})#持久
        自身._日志.事务(根.id,操作)#串行

    def _启动并结算(自身,根,名字,成员,请求,信号):#启动并结算
        """启动可续跑子代并结算 active/failed。"""
        子标识=成员['id']#子 id
        try:#启动
            已启动=解开(自身.ctx.subagents.启动可续跑({#启动可续跑
                'childId':子标识,#预留 id（上游字段）
                'provider':取字段(请求,'provider'),#provider
                'label':成员['description'],#标签
                'request':{'prompt':取字段(请求,'prompt'),'parent':根},#请求
                'signal':信号,#取消
            }))#启动结束
            实际子标识=取字段(已启动,'childId') or 子标识#实际 id
            if 实际子标识!=子标识:#上游自生成 id
                成员={**成员,'id':实际子标识}#对齐
                子标识=实际子标识#更新
            自身._检查点初始提示(子标识,取字段(已启动,'messageId'),信号)#等初始提示落盘
        except Exception as 错误:#失败路径
            自身._创建失败(根,名字,成员,子标识,错误)#失败结算
            raise#原错误
        活跃={**成员,'phase':'active'}#活跃快照
        已结算阶段=自身._结算供应(根,活跃)#结算 active
        if 已结算阶段=='failed':#对账冲突
            冲突=团队错误(#对账冲突
                'teammate "'+名字+'" was reconciled as failed while creation was in progress',#文案
                'TEAM_PROVISIONING_CONFLICT',#码
            )#冲突
            try:#清理
                自身.停止队友们(根,[子标识])#清理
            except Exception as 清理错误:#清理也败
                from ...依赖.工具 import 聚合错误#聚合错误
                raise 聚合错误([冲突,清理错误],'provisioning conflict cleanup failed')#双失败
            raise 冲突#抛冲突
        return {'member':自身._成员视图(活跃)}#返回视图

    def _创建失败(自身,根,名字,成员,子标识,错误):#创建失败结算
        """创建失败时写 failed 边并清理。"""
        失败={**成员,'phase':'failed','error':错误文案(错误)}#失败快照
        try:#结算
            阶段=自身._结算供应(根,失败)#结算
            自身.停止队友们(根,[子标识])#清理子
            if 阶段=='active':#竞态冲突
                raise 团队错误(#竞态
                    'teammate "'+名字+'" became active while its creator reported failure',#文案
                    'TEAM_PROVISIONING_CONFLICT',#码
                    {'cause':错误},#cause
                )#抛出
        except Exception as 记录错误:#双失败
            if 记录错误 is 错误:#同错
                raise#上抛
            from ...依赖.工具 import 聚合错误#聚合错误
            raise 聚合错误([错误,记录错误],'teammate creation and durable failure recording both failed')#双失败

    def _检查点初始提示(自身,子标识,消息标识,信号):#检查点初始提示
        """在 Lead 可提交 active 之前 flush 已接受的初始 inbox 项。"""
        while True:#轮询直到接受
            抛若中止(信号)#取消
            会话=自身.ctx.sessions.get(子标识)#live 会话
            if 会话 is None:#读持久
                已存=读持久会话(自身.ctx.sessionPersistence,子标识,信号)#读持久
                后缀=已存['events'][已存['inheritedEventCount']:]#自有后缀
                if 消息已接受(后缀,lambda 消息:取字段(消息,'id')==消息标识):#已接受
                    return#完成
                raise 团队错误(#未落盘
                    'teammate "'+str(子标识)+'" initial prompt was not durably accepted',#文案
                    'TEAM_PROVISIONING_CONFLICT',#码
                )#抛出
            自身._等会话推进(会话,子标识,消息标识,信号)#等推进或接受

    def _等会话推进(自身,会话,子标识,消息标识,信号):#等会话推进
        """flush 后检查接受；否则等事件或处置。"""
        进度=操作任务()#进度门
        def 忽略拒绝(错误):#吞未等拒绝
            """标记稍后拒绝已处理。"""
            return None#吞掉
        def 事件推进(候选,*_其余):#事件推进
            """会话事件推进。"""
            if 候选 is 会话:#同会话
                进度.兑现()#推进
        def 处置推进(候选,*_其余):#处置推进
            """会话处置推进。"""
            if 候选 is 会话:#同会话
                进度.兑现()#推进
        def 取消处理(*_位置):#取消
            """取消进度门。"""
            原因=中止原因(信号)#取消原因
            if isinstance(原因,BaseException):#已是异常
                进度.拒绝(原因)#保留
            else:#包装
                进度.拒绝(团队错误('teammate creation aborted: '+错误文案(原因),'TEAM_DISPOSED'))#包装
        停事件=自身.ctx.on('session/event',事件推进)#听事件
        停处置=自身.ctx.on('session/disposed',处置推进)#听处置
        听中止(信号,取消处理)#听取消
        try:#flush 检查
            抛若中止(信号)#取消
            解开(自身.ctx.sessions.flush(会话))#flush
            后缀=会话.snapshotEvents(会话.inheritedEventCount)#后缀
            if 消息已接受(后缀,lambda 消息:取字段(消息,'id')==消息标识):#已接受
                return#完成
            if 自身.ctx.sessions.get(子标识) is not 会话:#会话换了
                return#外层重来
            try:#等推进
                解开(进度)#等
            except Exception:#取消等
                raise#上抛
        finally:#卸监听
            摘中止(信号,取消处理)#卸取消
            停处置()#卸处置
            停事件()#卸事件

    def _对账供应(自身,根,信号):#对账供应
        """从各自独立持久的子 Session 结算仅供应中的成员。"""
        供应中=[成员 for 成员 in 自身._日志.状态(根)['members'] if 成员['phase']=='provisioning']#供应中
        for 成员 in 供应中:#逐成员
            抛若中止(信号)#取消
            if 自身.ctx.agents.get(成员['id']) is not None:#创建中跳过
                continue#下一
            阶段,失败=自身._判定供应终态(根,成员,信号)#判定
            抛若中止(信号)#取消
            自身._写供应终态(根,成员,阶段,失败,信号)#写终态

    def _判定供应终态(自身,根,成员,信号):#判定供应终态
        """读持久子 Session 判定 active/failed。"""
        阶段='failed'#默认失败
        失败='provisioning did not leave a resumable child Session'#默认文案
        try:#读子
            已载=读持久会话(自身.ctx.sessionPersistence,成员['id'],信号)#读子
            后缀=已载['events'][已载['inheritedEventCount']:]#后缀
            描述符=折叠子智能体描述符(后缀)#描述符
            已接受初始=消息已接受(后缀,lambda 消息:取字段(取字段(消息,'source'),'kind')=='user')#初始用户消息
            头父=取字段(已载['header'],'parentSession')#父
            if (头父==根.id and 取字段(描述符,'mode')=='continuable'
                    and 取字段(描述符,'provider')==成员['provider'] and 已接受初始):#匹配
                阶段='active'#活跃
            else:#不匹配
                失败='persisted child Session does not match the provisioned continuation'#不匹配
        except Exception as 错误:#读失败
            失败='child Session recovery failed: '+错误文案(错误)#读失败
        return 阶段,失败#结果

    def _写供应终态(自身,根,成员,阶段,失败,信号):#写供应终态
        """若仍为 provisioning 则写终态边。"""
        def 操作():#事务
            """条件写终态。"""
            抛若中止(信号)#取消
            当前=None#当前行
            for 候选 in 自身._日志.状态(根)['members']:#扫
                if 候选['id']==成员['id']:#命中
                    当前=候选#记下
                    break#结束
            if 当前 is None or 当前['phase']!='provisioning':#已被结算
                return#跳过
            已结算=dict(当前)#拷贝
            已结算['phase']=阶段#阶段
            if 阶段=='failed':#失败文案
                已结算['error']=失败#错误
            自身._日志.追加并刷新(根,'team/member',{#写终态
                'version':2,#版本
                'teamId':团队标识(根.id),#团队
                'member':已结算,#成员
            })#追加结束
        自身._日志.事务(根.id,操作)#串行

    def _成员视图(自身,成员):#成员视图
        """成功创建后构建一条运行时成员行。"""
        活=自身.ctx.agents.get(成员['id'])#live
        行={#视图
            'id':成员['id'],#id
            'name':成员['name'],#名
            'role':'teammate',#角色
            'status':活.status if 活 is not None else 'inactive',#状态
            'description':成员['description'],#描述
            'provider':成员['provider'],#provider
            'context':成员['context'],#上下文
            'diagnostics':[],#无诊断
        }#骨架
        模型=取字段(取字段(活,'options'),'model') if 活 is not None else None#模型
        if 模型 is not None:#有模型
            行['model']=模型#展开
        return 行#视图

    def _成员名(自身,值):#校验名字
        """校验永不复用的、面向模型的 teammate 名。"""
        if 成员名模式.match(值) is None or len(值)>64 or 值=='lead':#非法名
            raise 团队错误(#非法名
                'teammate name must be lower-kebab-case, at most 64 characters, and not "lead"',#文案
                'TEAM_INVALID_MEMBER_NAME',#码
            )#抛出
        return 值#通过

    def _结算供应(自身,根,终态):#结算供应
        """追加一条终态供应边，除非恢复已先结算。"""
        def 操作():#事务
            """条件写终态并返回阶段。"""
            当前=None#当前
            for 成员 in 自身._日志.状态(根)['members']:#扫
                if 成员['id']==终态['id']:#命中
                    当前=成员#记下
                    break#结束
            if 当前 is None:#消失
                raise 团队错误('provisioned teammate "'+终态['id']+'" disappeared','TEAM_PROVISIONING_CONFLICT')#消失
            if 当前['phase']!='provisioning':#已被结算
                return 当前['phase']#返回已有
            自身._日志.追加并刷新(根,'team/member',{#写终态
                'version':2,#版本
                'teamId':团队标识(根.id),#团队
                'member':终态,#终态
            })#追加结束
            return 'active' if 终态['phase']=='active' else 'failed'#阶段
        return 自身._日志.事务(根.id,操作)#串行

    def _子智能体描述符(自身,智能体):#是否 subagent
        """一个 Session 的自有后缀是否标识 provider 拥有的 subagent 子代。"""
        后缀=智能体.session.snapshotEvents(智能体.session.inheritedEventCount)#后缀
        return 折叠子智能体描述符(后缀) is not None#有描述符
