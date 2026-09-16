"""同会话目标域：事件源状态、比较交换变更，以及进程内续跑武装。"""
import re,time,uuid,weakref#阻塞码、纪元毫秒、目标 id 与会话弱表
from ...依赖 import cordis#外部依赖胶水
from ...依赖.schemastery import 数字字段#配置字段
from ...内核.智能体 import 智能体事件#按智能体作用域派发
from ...typert.协议 import 远程服务,远程 as _远程#Remote 服务基类与装饰器
from .类型 import *#纯类型出口再导出到包根
from .域 import *#宿主侧域词汇再导出到包根
from .折叠 import (
    应用目标事件,#严格折叠步进
    解码目标变更,#严格解码器
    目标变更引用,#变更 → 引用
    折叠目标,#整日志折叠
)#纯回放折叠
from .运行时 import (
    目标变更版本,#载荷版本
    目标错误,#域边界错误
    目标标识,#目标 id 品牌函数
)#运行时构造
from .远程 import TYPERT_REMOTE#Host-for-Client Remote 贡献

配置={#插件配置模式
    'defaultMaxGoalRounds':数字字段(默认值=256),#默认 256 轮
}#结束 Config 模式
Config=配置#Cordis 配置模式
安全整数上限=9007199254740991#Number.MAX_SAFE_INTEGER
阻塞码模式=re.compile(r'^[a-z][a-z0-9]*(?:-[a-z0-9]+)*\Z',re.ASCII)#小写短横线分类码

def 此刻毫秒():#对齐 Date.now
    """当前纪元毫秒。"""
    return int(time.time()*1000)#纪元毫秒

def 折叠状态从投影(状态):#检查点 → 严格折叠
    """从一份检查点安全的投影状态构造严格折叠状态。"""
    当前=状态['current']#当前目标
    return {#严格累加器
        'goal':当前['goal'] if 当前 is not None else None,#快照
        'roundsStarted':当前['roundsStarted'] if 当前 is not None else 0,#轮次
        'createdAt':当前['createdAt'] if 当前 is not None else None,#创建
        'updatedAt':当前['updatedAt'] if 当前 is not None else None,#变更
        'lastRef':None,#投影不保留最近引用
        'seenGoalIds':set(状态['seenGoalIds']),#已见身份
    }#结束累加器

def 投影状态从折叠(状态):#严格折叠 → 检查点
    """把严格折叠状态转成检查点安全的投影状态。"""
    当前=None#默认无当前
    if 状态['goal'] is not None:#有快照
        if 状态['createdAt'] is None or 状态['updatedAt'] is None:#缺时间戳
            raise Exception('current goal fold lacks timestamps')#折叠坏了
        当前={#当前投影
            'goal':状态['goal'],#快照
            'roundsStarted':状态['roundsStarted'],#轮次
            'createdAt':状态['createdAt'],#创建
            'updatedAt':状态['updatedAt'],#变更
        }#结束当前
    return {#检查点
        'current':当前,#当前或空
        'seenGoalIds':list(状态['seenGoalIds']),#已见身份
        'failure':None,#合法流
    }#结束检查点

def 应用目标投影(状态,事件):#投影级折叠
    """经严格回放规则折叠持久目标事件，不从投影登记表的事件驱动里抛错。

    第一条非法自有事件留在 failure；宿主目标访问拒绝该状态，客户端视图停在最后合法目标。
    """
    if 状态['failure'] is not None:#已经失败
        return 状态#保持
    类型=事件['type']#事件类型
    if 类型!='goal/change':#非自有变更
        if 类型!='user/message':#也不是用户消息
            return 状态#无关
        数据=事件['data']#载荷
        来源=数据['source'] if 'source' in 数据 else None#来源
        if 来源 is None or 来源['kind']!='goal':#非目标轮次
            return 状态#无关
    折叠=折叠状态从投影(状态)#严格累加器
    try:#严格步进
        应用目标事件(折叠,事件)#应用
        return 投影状态从折叠(折叠)#下一投影
    except Exception as 错误:#严格失败
        消息=str(错误)#诊断
        下一=dict(状态)#拆离
        下一['failure']='goal replay failed at session event '+str(事件['seq'])+': '+消息#记下
        return 下一#失败态

def 投影初态():#创建前
    """创建前的空检查点。"""
    return {'current':None,'seenGoalIds':[],'failure':None}#空

def 投影视图(状态):#线视图
    """客户端只看当前目标。"""
    return 状态['current']#当前或空

目标投影定义={#goal 投影单元
    'key':'goal',#投影键
    'stateSchema':None,#由折叠自检
    'init':投影初态,#空检查点
    'apply':应用目标投影,#严格折叠
    'wire':{'viewSchema':None,'view':投影视图},#当前目标
    'stateVersion':6,#状态版本
}#结束定义

def 解析轮次上限(值):#校验调用方可见的正安全整数轮次上限
    """校验调用方可见的正安全整数轮次上限。"""
    if isinstance(值,bool):#布尔不是数字
        合法=False#非法
    elif isinstance(值,int):#整数
        合法=值>=1 and 值<=安全整数上限#正且在安全范围内
    elif isinstance(值,float) and 值.is_integer():#整值浮点
        合法=值>=1 and 值<=安全整数上限#正且在安全范围内
    else:#其它类型
        合法=False#非法
    if not 合法:#非正安全整数
        raise 目标错误('maxGoalRounds must be a positive safe integer','GOAL_INVALID_MAX_ROUNDS')#上限非法
    return int(值)#已校验上限

def 解析陈述(值):#在域边界校验并规范化目标陈述
    """在域边界校验并规范化目标陈述。"""
    if (not isinstance(值,str)) or len(值.strip())==0:#空或非字符串
        raise 目标错误('goal objective must be a non-empty string','GOAL_INVALID_OBJECTIVE')#陈述非法
    return 值.strip()#去掉首尾空白

def 解析创建目标(请求,默认轮次上限):#解析部署默认值并校验一次创建请求
    """解析部署默认值并校验一次创建请求。"""
    上限=请求['maxGoalRounds'] if 'maxGoalRounds' in 请求 else None#请求可选上限
    if 上限 is None:#省略则用部署默认
        上限=默认轮次上限#部署默认
    return {#已解析规格
        'objective':解析陈述(请求['objective']),#规范化陈述
        'maxGoalRounds':解析轮次上限(上限),#已解析上限
    }#结束规格

def 解析阻塞原因(原因):#校验并脱离一份策略拥有的阻塞说明
    """校验并脱离一份策略拥有的阻塞说明。"""
    记录=原因 if isinstance(原因,dict) else None#原因是 dict
    码=记录['code'] if 记录 is not None and 'code' in 记录 else None#分类码
    说明=记录['message'] if 记录 is not None and 'message' in 记录 else None#说明
    if (not isinstance(码,str)) or 阻塞码模式.match(码) is None or (not isinstance(说明,str)) or len(说明.strip())==0:#小写短横线加非空说明
        raise 目标错误(#原因非法
            'goal block reason requires a lower-kebab-case code and a non-empty message',#码与说明都要
            'GOAL_INVALID_BLOCK_REASON',#稳定错误码
        )#结束抛错
    return {'code':码,'message':说明.strip()}#规范化说明

class 目标服务(远程服务):#目标域服务（ctx.goals）
    """目标服务（`ctx.goals`），完全由所属会话日志支撑。"""
    inject=['agents','sessionProjections']#依赖智能体与投影登记表
    Config=配置#插件配置模式

    def __init__(自身,上下文,配置值=None):#构造并挂投影单元
        """构造并挂投影单元。"""
        if 配置值 is None:#缺省空配置
            配置值={}#空配置
        super().__init__(上下文,'goals')#以 goals 名注册远程服务
        默认上限=配置值['defaultMaxGoalRounds'] if 'defaultMaxGoalRounds' in 配置值 else None#配置上限
        if 默认上限 is None:#省略则 256
            默认上限=256#部署默认
        自身.已解析={'defaultMaxGoalRounds':解析轮次上限(默认上限)}#解析默认上限
        自身.运行时表=weakref.WeakKeyDictionary()#会话 → 进程内武装
        def 智能体已创建(载荷,*位置参数):#新生命周期解除武装
            """新智能体生命周期默认解除武装。"""
            自身.设置武装(载荷['agent'].session,'disarmed')#不继承上一生命周期
        上下文.监听('agent/created',智能体已创建)#创建边
        上下文.sessionProjections.register(目标投影定义)#登记 goal 键
        def 会话事件(会话,事件,*位置参数):#持久变更调和武装
            """自有变更落盘后写入进程内武装。"""
            if 事件['type']!='goal/change':#非自有
                return#放过
            运行时=自身.运行时状态(会话)#进程内
            待定=运行时['pendingActivation']#追加中意图
            if 待定 is not None and 待定['offset']==事件['seq']:#自己刚追加的
                武装=待定['activation']#采用意图
            else:#外来变更
                武装='disarmed'#默认解除
            自身.设置武装(会话,武装)#经发布边写入
        上下文.监听('session/event',会话事件)#日志边

    @_远程('get')
    def get(自身,智能体):#Remote 导出名 get
        """Remote 导出名 get。"""
        return 自身.获取(智能体)#转中文

    def 获取(自身,智能体):#读当前目标
        """读取一个精确实时智能体的当前目标；没有当前目标时为 None。"""
        自身.断言实时(智能体)#必须是实时实例
        return 自身.视图(自身.状态(智能体.session),自身.运行时状态(智能体.session))#脱离视图

    def 解除武装(自身,智能体):#解除武装
        """去掉进程内续跑权限，不改持久阶段或修订。"""
        自身.断言实时(智能体)#必须是实时实例
        自身.设置武装(智能体.session,'disarmed')#经发布边解除
        return 自身.视图(自身.状态(智能体.session),自身.运行时状态(智能体.session))#脱离视图

    def 创建(自身,智能体,请求):#创建目标
        """创建并武装一个目标。已完成目标可以被替换；其它当前阶段必须先清除或恢复。"""
        规格=解析创建目标(请求,自身.已解析['defaultMaxGoalRounds'])#解析默认并校验
        状态,运行时=自身.准备变更(智能体)#实时实例加投影
        当前=状态['goal'] if 状态 is not None else None#当前快照
        if 当前 is not None and 当前['phase']!='complete':#未完成目标还在
            raise 目标错误('goal "'+str(当前['id'])+'" already exists with phase "'+str(当前['phase'])+'"','GOAL_ALREADY_EXISTS')#拒绝覆盖
        现在=此刻毫秒()#创建与变更同一时刻
        快照={#修订一的活跃快照
            'id':目标标识('goal-'+str(uuid.uuid4())),#新品牌 id
            'revision':1,#首修订
            'objective':规格['objective'],#已规范化陈述
            'phase':'active',#创建即为活跃
            'maxGoalRounds':规格['maxGoalRounds'],#已解析上限
        }#结束快照
        return 自身.提交快照(智能体,运行时,'create',快照,0,现在,现在,'armed')#提交并武装

    def 编辑(自身,智能体,引用,请求):#比较交换编辑
        """编辑目标陈述和/或轮次上限，不改阶段。"""
        状态,运行时=自身.准备变更(智能体)#实时加投影
        当前态=自身.期望当前(状态,引用)#引用必须对准当前
        当前=当前态['goal']#快照
        if ('objective' not in 请求 or 请求['objective'] is None) and ('maxGoalRounds' not in 请求 or 请求['maxGoalRounds'] is None):#两个字段都缺
            raise 目标错误('goal edit requires objective and/or maxGoalRounds','GOAL_INVALID_EDIT')#编辑空操作
        快照={#修订 +1，阶段保留
            'id':当前['id'],#同一身份
            'revision':当前['revision']+1,#前进一步
            'objective':当前['objective'],#默认保留陈述
            'phase':当前['phase'],#阶段保留
            'maxGoalRounds':当前['maxGoalRounds'],#默认保留上限
        }#结束下一快照
        if 'blockedReason' in 当前:#保留阻塞原因
            快照['blockedReason']=dict(当前['blockedReason'])#脱离原因
        if 'objective' in 请求 and 请求['objective'] is not None:#可选替换陈述
            快照['objective']=解析陈述(请求['objective'])#规范化陈述
        if 'maxGoalRounds' in 请求 and 请求['maxGoalRounds'] is not None:#可选替换上限
            快照['maxGoalRounds']=解析轮次上限(请求['maxGoalRounds'])#已校验上限
        return 自身.提交当前(智能体,当前态,运行时,'edit',快照,运行时['activation'])#武装保持不变

    @_远程('edit')
    def edit(自身,智能体,引用,请求):#Remote 导出名 edit
        """Remote 导出名 edit。"""
        return 自身.编辑(智能体,引用,请求)#转中文

    def 暂停(自身,智能体,引用):#暂停
        """暂停一个活跃目标并解除自动续跑。"""
        return 自身.迁移(智能体,引用,'pause',['active'],'paused','disarmed')#active→paused 并解除武装

    @_远程('pause')
    def pause(自身,智能体,引用):#Remote 导出名 pause
        """Remote 导出名 pause。"""
        return 自身.暂停(智能体,引用)#转中文

    def 恢复(自身,智能体,引用):#恢复或再武装
        """恢复并武装一个已停止目标，或在会话开始边之后给活跃目标重新武装，前提是轮次预算仍有余量。"""
        状态,运行时=自身.准备变更(智能体)#实时加投影
        当前态=自身.期望当前(状态,引用)#引用必须对准
        当前=当前态['goal']#快照
        可恢复=('active','paused','blocked')#可恢复阶段
        if 当前['phase'] not in 可恢复:#已完成等不可恢复
            raise 自身.迁移错误(当前,'resume',可恢复)#阶段不对
        if 当前['phase']=='active' and 运行时['activation']=='armed':#已经活跃且武装
            raise 目标错误('goal "'+str(当前['id'])+'" is already active and armed','GOAL_INVALID_TRANSITION')#空恢复
        if 当前态['roundsStarted']>=当前['maxGoalRounds']:#预算耗尽
            raise 目标错误(#须先提高上限
                'goal "'+str(当前['id'])+'" exhausted '+str(当前['maxGoalRounds'])+' goal rounds; increase maxGoalRounds before resuming',#轮次用完
                'GOAL_INVALID_TRANSITION',#迁移非法
            )#结束抛错
        return 自身.提交当前(智能体,当前态,运行时,'resume',自身.带阶段(当前,'active'),'armed')#回到活跃并武装

    @_远程('resume')
    def resume(自身,智能体,引用):#Remote 导出名 resume
        """Remote 导出名 resume。"""
        return 自身.恢复(智能体,引用)#转中文

    def 完成(自身,智能体,引用):#完成
        """把当前非完成目标标为完成并解除武装。"""
        return 自身.迁移(#允许的来源阶段
            智能体,#所属智能体
            引用,#比较交换引用
            'complete',#完成动词
            ['active','paused','blocked'],#非完成均可
            'complete',#目标阶段
            'disarmed',#完成后不再续跑
        )#结束迁移

    @_远程('complete')
    def complete(自身,智能体,引用):#Remote 导出名 complete
        """Remote 导出名 complete。"""
        return 自身.完成(智能体,引用)#转中文

    def 阻塞(自身,智能体,引用,原因):#阻塞
        """把一个活跃目标标为阻塞并解除武装。"""
        状态,运行时=自身.准备变更(智能体)#实时加投影
        当前态=自身.期望当前(状态,引用)#引用必须对准
        当前=当前态['goal']#快照
        if 当前['phase']!='active':#只能从活跃阻塞
            raise 自身.迁移错误(当前,'block',['active'])#阶段不对
        快照=自身.带阶段(当前,'blocked')#阶段迁移快照
        快照['blockedReason']=解析阻塞原因(原因)#阶段加已校验原因
        return 自身.提交当前(#提交阻塞快照
            智能体,#所属智能体
            当前态,#当前投影
            运行时,#进程内
            'block',#阻塞动词
            快照,#带原因的阻塞快照
            'disarmed',#阻塞后不再续跑
        )#结束提交

    def 清除(自身,智能体,引用):#清除
        """清除当前目标，同时保留持久墓碑与历史。"""
        状态,运行时=自身.准备变更(智能体)#实时加投影
        当前态=自身.期望当前(状态,引用)#引用必须对准
        当前=当前态['goal']#快照
        墓碑={'id':当前['id'],'revision':当前['revision']+1}#墓碑修订 +1
        变更={#清除变更
            'kind':'goal/change',#事件标签
            'version':目标变更版本,#当前版本
            'operation':'clear',#清除
            'cleared':墓碑,#墓碑引用
            'clearedAt':自身.下一变更时间(当前态),#不早于上次变更
        }#结束墓碑载荷
        自身.提交(智能体,运行时,变更,'disarmed')#提交并解除武装
        return dict(墓碑)#脱离副本

    @_远程('clear')
    def clear(自身,智能体,引用):#Remote 导出名 clear
        """Remote 导出名 clear。"""
        return 自身.清除(智能体,引用)#转中文

    def 准备变更(自身,智能体):#变更前置
        """解析一次变更所用的持久投影与进程内武装。"""
        自身.断言实时(智能体)#必须是实时实例
        return 自身.状态(智能体.session),自身.运行时状态(智能体.session)#投影加武装

    def 期望当前(自身,状态,引用):#比较交换
        """拒绝过期或缺失的当前状态引用。"""
        if 状态 is None:#没有当前目标
            raise 目标错误('no current goal','GOAL_NOT_FOUND')#没有当前目标
        当前=状态['goal']#当前快照
        if 引用['id']!=当前['id'] or 引用['revision']!=当前['revision']:#身份或修订对不上
            raise 目标错误(#过期引用
                'stale goal ref "'+str(引用['id'])+'" revision '+str(引用['revision'])+'; current is "'+str(当前['id'])+'" revision '+str(当前['revision']),#指出当前修订
                'GOAL_STALE_REVISION',#比较交换失败
            )#结束抛错
        return 状态#对准的当前投影

    def 断言实时(自身,智能体):#实例同一性
        """强制精确的实时智能体身份，而不信任仅 id 匹配。"""
        if 自身.ctx.agents.获取(智能体.id) is not 智能体:#不是注册表里那一份
            raise 目标错误('agent "'+str(智能体.id)+'" is not live in this registry','GOAL_AGENT_NOT_LIVE')#已换实例

    def 状态(自身,会话):#读登记表投影
        """读登记表维护的当前持久投影。"""
        投影=自身.ctx.sessionProjections.stateOf(会话,'goal')#检查点
        if 投影 is None:#未登记
            raise Exception('goal projection is not registered')#未登记
        if 投影['failure'] is not None:#回放失败
            raise Exception(投影['failure'])#失败诊断
        return 投影['current']#当前或空

    def 运行时状态(自身,会话):#懒播种武装
        """返回进程内武装状态；首次为解除武装。"""
        运行时=自身.运行时表.get(会话)#已有则用
        if 运行时 is not None:#命中
            return 运行时#已有
        运行时={'activation':'disarmed','pendingActivation':None}#种子
        自身.运行时表[会话]=运行时#按会话记住
        return 运行时#新状态

    def 设置武装(自身,会话,武装):#武装发布
        """仅在实际变化时发布一条进程内武装边。"""
        运行时=自身.运行时状态(会话)#拿到或播种
        if 运行时['activation']==武装:#无变化
            return#结束
        运行时['activation']=武装#写入
        投影=自身.ctx.sessionProjections.stateOf(会话,'goal')#检查点
        if 投影 is None:#静态注入要求登记表先于本服务
            return#结束
        if 投影['failure'] is not None:#失败态不发视图
            return#结束
        视图=自身.视图(投影['current'],运行时)#当前视图
        载荷={'sessionId':会话.id}#会话
        if 视图 is not None:#有目标才带精确武装
            载荷['goal']={#精确身份
                'id':视图['id'],#id
                'revision':视图['revision'],#修订
                'activation':视图['activation'],#武装
            }#结束 goal
        自身.ctx.emit('goal/activation-changed',载荷)#武装变更

    def 带阶段(自身,当前,阶段):#阶段迁移快照
        """用一个替换阶段构造新修订。"""
        return {#修订 +1，去掉阻塞原因
            'id':当前['id'],#同一身份
            'revision':当前['revision']+1,#前进一步
            'objective':当前['objective'],#保留陈述
            'phase':阶段,#新阶段
            'maxGoalRounds':当前['maxGoalRounds'],#保留上限
        }#结束快照

    def 迁移(自身,智能体,引用,操作,允许,阶段,武装):#pause/complete 共用
        """共用的已校验阶段迁移。"""
        状态,运行时=自身.准备变更(智能体)#实时加投影
        当前态=自身.期望当前(状态,引用)#引用必须对准
        当前=当前态['goal']#快照
        if 当前['phase'] not in 允许:#阶段不对
            raise 自身.迁移错误(当前,操作,允许)#阶段不对
        return 自身.提交当前(智能体,当前态,运行时,操作,自身.带阶段(当前,阶段),武装)#提交迁移

    def 迁移错误(自身,当前,操作,允许):#阶段错误
        """渲染稳定的非法迁移错误。"""
        return 目标错误(#人类可读加稳定码
            'cannot '+str(操作)+' goal "'+str(当前['id'])+'" from phase "'+str(当前['phase'])+'"; expected '+' or '.join(允许),#指出期望阶段
            'GOAL_INVALID_TRANSITION',#迁移非法
        )#结束错误

    def 提交当前(自身,智能体,状态,运行时,操作,快照,武装):#非创建快照提交
        """提交一次保留当前目标导出计数/时间的变更。"""
        return 自身.提交快照(#带上保留的计数时间
            智能体,#所属智能体
            运行时,#进程内
            操作,#动词
            快照,#下一快照
            状态['roundsStarted'],#轮次不变
            状态['createdAt'],#创建时间不变
            自身.下一变更时间(状态),#变更时间不倒退
            武装,#意图武装
        )#结束提交

    def 下一变更时间(自身,状态):#不早于上次变更
        """在墙钟回拨时夹紧当前目标的下一时间戳。"""
        return max(此刻毫秒(),状态['updatedAt'])#取较晚者

    def 提交快照(自身,智能体,运行时,操作,快照,已接纳轮次,创建于,变更于,武装):#整值提交
        """构造并提交一次整快照变更。"""
        变更={#整值载荷
            'kind':'goal/change',#事件标签
            'version':目标变更版本,#当前版本
            'operation':操作,#动词
            'goal':快照,#完整快照
            'roundsStarted':已接纳轮次,#轮次
            'createdAt':创建于,#创建时间
            'updatedAt':变更于,#变更时间
        }#结束载荷
        自身.提交(智能体,运行时,变更,武装)#追加并通知
        结果={#已提交视图
            'id':快照['id'],#身份
            'revision':快照['revision'],#修订
            'objective':快照['objective'],#陈述
            'phase':快照['phase'],#阶段
            'maxGoalRounds':快照['maxGoalRounds'],#上限
            'roundsStarted':已接纳轮次,#轮次
            'createdAt':创建于,#创建
            'updatedAt':变更于,#变更
            'activation':运行时['activation'],#武装
        }#结束视图
        if 'blockedReason' in 快照:#阻塞带原因
            结果['blockedReason']=dict(快照['blockedReason'])#脱离原因
        return 结果#已提交视图

    def 提交(自身,智能体,运行时,变更,武装):#追加边界
        """把一次变更提交进目标日志和实时事件流。"""
        引用=目标变更引用(变更)#本条引用
        会话=智能体.session#所属会话
        运行时['pendingActivation']={'offset':会话.seq,'activation':武装}#同步追加前记下意图
        try:#追加可能抛
            事件=会话.append('goal/change',变更)#写入会话日志
            if 运行时['pendingActivation'] is not None and 运行时['pendingActivation']['offset']==事件['seq']:#本条
                运行时['activation']=武装#立即采用
        finally:#无论成败都清掉意图
            运行时['pendingActivation']=None#避免残留到后续外来事件
        视图=自身.视图(自身.状态(会话),运行时)#提交后视图，清除则为 None
        通知={#实时通知
            'operation':变更['operation'],#本次动词
            'ref':dict(引用),#脱离引用
        }#结束通知
        if 视图 is not None:#有当前目标才带视图
            通知['goal']=视图#带视图
        智能体事件(自身.ctx,智能体)['emit']('goal/changed',{'change':通知})#作用域内派发

    def 视图(自身,状态,运行时):#投影 → 视图
        """构造一份脱离的当前视图。"""
        if 状态 is None:#没有当前目标
            return None#没有当前目标
        目标=状态['goal']#当前快照
        结果={#脱离视图
            'id':目标['id'],#稳定身份
            'revision':目标['revision'],#正数修订
            'objective':目标['objective'],#陈述
            'phase':目标['phase'],#阶段
            'maxGoalRounds':目标['maxGoalRounds'],#上限
            'roundsStarted':状态['roundsStarted'],#已接纳轮次
            'createdAt':状态['createdAt'],#创建时间
            'updatedAt':状态['updatedAt'],#变更时间
            'activation':运行时['activation'],#进程内武装
        }#结束视图
        if 'blockedReason' in 目标:#仅阻塞带原因
            结果['blockedReason']=dict(目标['blockedReason'])#脱离原因
        return 结果#脱离视图

    def 远程创建(自身,智能体,请求):#远程创建
        """经远程边界创建一条目标；只回已创建目标的身份。"""
        视图=自身.创建(智能体,请求)#走本地域创建
        return {'ref':{'id':视图['id'],'revision':视图['revision']}}#只回引用

    @_远程('create')
    def create(自身,智能体,请求):#Remote 导出名 create
        """Remote 导出名 create。"""
        return 自身.远程创建(智能体,请求)#转中文

默认=目标服务#中文默认导出
default=目标服务#Cordis 默认导出

__all__=[#仅中文公开名
    '目标服务','默认','配置',
    '应用目标投影','目标投影定义',
    '目标变更版本','目标错误','目标标识',
    '解码目标变更','折叠目标','目标变更引用',
]#公开面结束
