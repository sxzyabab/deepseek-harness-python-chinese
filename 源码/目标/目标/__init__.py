"""同会话目标域：事件源状态、比较交换变更，以及进程内续跑武装。"""
import math,re,time,uuid,weakref#安全整数、阻塞码、纪元毫秒、目标 id 与会话弱表
from ...依赖 import cordis#外部依赖胶水
from ...依赖.schemastery import 数字字段#配置字段
服务=cordis.服务#Cordis 服务基类
from ...内核.智能体 import 智能体事件#按智能体作用域派发
from ...typert.协议 import 远程服务,远程 as _远程#Remote 服务基类与装饰器
from .类型 import *#纯类型出口再导出到包根
from .域 import *#宿主侧域词汇再导出到包根
from .折叠 import (
    应用目标事件,#严格折叠步进
    解码目标变更,#严格解码器
    空目标折叠状态,#空累加器
    目标变更引用,#变更 → 引用
    折叠目标,#整日志折叠
)#纯回放折叠
from .运行时 import (
    目标变更版本,#载荷版本
    目标错误,#域边界错误
    目标标识,#目标 id 品牌函数（覆盖类型面的同名别名）
)#运行时构造（须在类型星号导入之后，保住 GoalId 值出口）
from .远程 import TYPERT_REMOTE,远程贡献对象#Host-for-Client Remote 贡献

配置={#插件配置模式
    'defaultMaxGoalRounds':数字字段(默认值=256),#默认 256 轮
}#结束 Config 模式
Config=配置#Cordis 配置模式
阻塞码模式=re.compile(r'^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$')#小写短横线分类码
安全整数上限=9007199254740991#Number.MAX_SAFE_INTEGER

目标投影模式={#`goal` 投影的线上载荷模式（整个当前目标，或创建前/清除后的 null）
    'anyOf':[#有目标或空
        {#有当前目标时的整值
            'type':'object',#对象
            'additionalProperties':False,#不许多余键
            'properties':{#投影字段
                'goal':{#快照字段
                    'type':'object',#对象
                    'additionalProperties':False,#不许多余键
                    'properties':{#快照字段
                        'id':{'type':'string','minLength':1},#非空 id
                        'revision':{'type':'integer','minimum':1},#正数修订
                        'objective':{'type':'string','minLength':1},#非空陈述
                        'phase':{'type':'string','enum':['active','paused','blocked','complete']},#合法阶段
                        'blockedReason':{#可选阻塞原因
                            'type':'object',#对象
                            'additionalProperties':False,#不许多余键
                            'properties':{#码与说明
                                'code':{'type':'string'},#分类码
                                'message':{'type':'string'},#说明
                            },#结束 properties
                        },#结束 blockedReason
                        'maxGoalRounds':{'type':'integer','minimum':1},#正数上限
                    },#结束 goal.properties
                    'required':['id','revision','objective','phase','maxGoalRounds'],#必填快照字段
                },#结束 goal
                'roundsStarted':{'type':'integer','minimum':0},#非负轮次
                'createdAt':{'type':'number'},#创建时间
                'updatedAt':{'type':'number'},#变更时间
            },#结束 properties
            'required':['goal','roundsStarted','createdAt','updatedAt'],#投影必填
        },#结束有目标分支
        {'type':'null'},#创建前或清除后
    ],#结束 anyOf
}#结束目标投影模式
def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 是否安全整数(值):#对齐 Number.isSafeInteger
    """对齐 JS Number.isSafeInteger，排除布尔。"""
    if isinstance(值,bool):#布尔不是数字
        return False#布尔不是安全整数
    if isinstance(值,int):#整数
        return abs(值)<=安全整数上限#在安全范围内
    if isinstance(值,float):#浮点
        if not math.isfinite(值) or not 值.is_integer():#非有限或非整
            return False#不是安全整数
        return abs(值)<=安全整数上限#在安全范围内
    return False#其它类型

def 此刻毫秒():#对齐 Date.now
    """当前纪元毫秒。"""
    return int(time.time()*1000)#纪元毫秒

def 应用目标投影(状态,事件):#投影级折叠
    """`goal` 投影单元的轻量最后一条胜出折叠。与严格回放折叠（折叠.py：迁移校验、畸形变更大声失败、Set 型状态）不同，这次迁移是投影级：状态是纯 JSON（持久化缓存前置条件），任何非目标或畸形事件返回同一引用（注册表的 Object.is 门闩——与 title/todos 同一姿态），已写入变更的正确性是写侧的职责（目标服务在追加前已校验；包不变量在安装处对违规流大声失败）。"""
    if 取字段(事件,'type')!='goal/change':#非本事件保持引用
        return 状态#保持原投影引用
    try:#持久载荷可能畸形
        变更=解码目标变更(取字段(事件,'data'))#严格解码
    except Exception:#解码失败：投影侧吞掉，不改写引用
        return 状态#保持原投影引用，供 Object.is 门闩
    if 变更 is None:#kind 对不上也保持引用
        return 状态#保持原投影引用
    if 变更['operation']=='clear':#墓碑清空投影
        return None#清除后为 null
    return {#整快照覆盖
        'goal':变更['goal'],#当前快照
        'roundsStarted':变更['roundsStarted'],#已接纳轮次
        'createdAt':变更['createdAt'],#创建时间
        'updatedAt':变更['updatedAt'],#变更时间
    }#结束有目标投影

def 落实轮次上限(值):#校验调用方可见的正安全整数轮次上限
    """校验调用方可见的正安全整数轮次上限。"""
    if (not 是否安全整数(值)) or 值<1:#非正安全整数
        raise 目标错误('maxGoalRounds must be a positive safe integer','GOAL_INVALID_MAX_ROUNDS')#上限非法
    return int(值)#已校验上限

def 落实陈述(值):#在域边界校验并规范化目标陈述
    """在域边界校验并规范化目标陈述。"""
    if (not isinstance(值,str)) or len(值.strip())==0:#空或非字符串
        raise 目标错误('goal objective must be a non-empty string','GOAL_INVALID_OBJECTIVE')#陈述非法
    return 值.strip()#去掉首尾空白

def 落实创建目标(请求,默认轮次上限):#落实部署默认值并校验一次创建请求
    """落实部署默认值并校验一次创建请求。"""
    上限=取字段(请求,'maxGoalRounds')#请求可选上限
    if 上限 is None:#省略则用部署默认
        上限=默认轮次上限#部署默认
    return {#已落实规格
        'objective':落实陈述(取字段(请求,'objective')),#规范化陈述
        'maxGoalRounds':落实轮次上限(上限),#已落实上限
    }#结束规格

def 落实阻塞原因(原因):#校验并脱离一份策略拥有的阻塞说明
    """校验并脱离一份策略拥有的阻塞说明。"""
    if isinstance(原因,dict) and not isinstance(原因,list):#记录形
        记录=原因#收成记录
    elif 原因 is not None and (not isinstance(原因,(str,int,float,bool,list))) and hasattr(原因,'__dict__'):#普通对象
        记录=原因#当对象读字段
    else:#否则缺席
        记录=None#缺席
    码=取字段(记录,'code')#分类码
    说明=取字段(记录,'message')#说明
    if (not isinstance(码,str)) or 阻塞码模式.match(码) is None or (not isinstance(说明,str)) or len(说明.strip())==0:#小写短横线加非空说明
        raise 目标错误(#原因非法
            'goal block reason requires a lower-kebab-case code and a non-empty message',#码与说明都要
            'GOAL_INVALID_BLOCK_REASON',#稳定错误码
        )#结束抛错
    return {'code':码,'message':说明.strip()}#规范化说明

class 目标服务(远程服务):#目标域服务（ctx.goals）
    """目标服务（`ctx.goals`），完全由所属会话日志支撑。"""
    inject=['agents']#依赖智能体注册表
    注入=inject#中文别名
    Config=配置#插件配置模式

    def __init__(自身,上下文,配置值=None):#构造并挂投影单元
        """构造并挂投影单元。"""
        if 配置值 is None:#缺省空配置
            配置值={}#空配置
        super().__init__(上下文,'goals')#以 goals 名注册远程服务
        默认上限=取字段(配置值,'defaultMaxGoalRounds')#配置上限
        if 默认上限 is None:#省略则 256
            默认上限=256#部署默认
        自身.已解析={'defaultMaxGoalRounds':落实轮次上限(默认上限)}#落实默认上限
        自身.缓存表=weakref.WeakKeyDictionary()#会话 → 折叠缓存
        def 会话开始(载荷,*其余):#会话开始边解除武装
            """会话开始边解除武装。"""
            智能体=取字段(载荷,'agent')#所属智能体
            自身.缓存(取字段(智能体,'session'))['activation']='disarmed'#不继承上一生命周期的自动权限
        上下文.on('agent/session-start',会话开始)#结束 session-start
        def 投影安装(投影上下文,*其余):#可选投影子插件
            """`goal` 投影单元：goal/change 整值的最后一条胜出折叠。仅当组合了投影注册表时单元子插件才激活。"""
            投影上下文.sessionProjections.register({#登记 goal 键
                'key':'goal',#投影键
                'schema':目标投影模式,#线上模式
                'init':lambda:None,#创建前为 null
                'apply':应用目标投影,#轻量折叠
                'view':lambda 状态:状态,#状态即视图
                'stateVersion':4,#状态版本
            })#结束登记
        上下文.inject(['sessionProjections'],投影安装)#结束 inject

    def 获取(自身,智能体):#读当前目标
        """读取一个精确实时智能体的当前目标；没有当前目标时为 None。"""
        自身.断言实时(智能体)#必须是实时实例
        缓存=自身.缓存(取字段(智能体,'session'))#拿到或播种缓存
        自身.同步(取字段(智能体,'session'),缓存)#追上未观察事件
        return 自身.视图(缓存)#脱离视图

    def 解除武装(自身,智能体):#解除武装
        """去掉进程内续跑权限，不改持久阶段或修订。"""
        自身.断言实时(智能体)#必须是实时实例
        缓存=自身.缓存(取字段(智能体,'session'))#拿到缓存
        自身.同步(取字段(智能体,'session'),缓存)#追上日志
        缓存['activation']='disarmed'#只改进程内字段
        return 自身.视图(缓存)#脱离视图

    def 创建(自身,智能体,请求):#创建目标
        """创建并武装一个目标。已完成目标可以被替换；其它当前阶段必须先清除或恢复。"""
        规格=落实创建目标(请求,自身.已解析['defaultMaxGoalRounds'])#落实默认并校验
        缓存=自身.准备变更(智能体)#实时实例加已同步缓存
        当前=缓存['state']['goal']#当前快照
        if 当前 is not None and 当前['phase']!='complete':#未完成目标还在
            raise 目标错误('goal "'+str(当前['id'])+'" already exists with phase "'+str(当前['phase'])+'"','GOAL_ALREADY_EXISTS')#拒绝覆盖
        现在=此刻毫秒()#创建与变更同一时刻
        快照={#修订一的活跃快照
            'id':目标标识('goal-'+str(uuid.uuid4())),#新品牌 id
            'revision':1,#首修订
            'objective':规格['objective'],#已规范化陈述
            'phase':'active',#创建即为活跃
            'maxGoalRounds':规格['maxGoalRounds'],#已落实上限
        }#结束快照
        return 自身.提交快照(智能体,缓存,'create',快照,0,现在,现在,'armed')#提交并武装

    def 编辑(自身,智能体,引用,请求):#比较交换编辑
        """编辑目标陈述和/或轮次上限，不改阶段。"""
        缓存=自身.准备变更(智能体)#实时加同步
        当前=自身.期望当前(缓存,引用)#引用必须对准当前
        if 取字段(请求,'objective') is None and 取字段(请求,'maxGoalRounds') is None:#两个字段都缺
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
        if 取字段(请求,'objective') is not None:#可选替换陈述
            快照['objective']=落实陈述(取字段(请求,'objective'))#规范化陈述
        if 取字段(请求,'maxGoalRounds') is not None:#可选替换上限
            快照['maxGoalRounds']=落实轮次上限(取字段(请求,'maxGoalRounds'))#已校验上限
        return 自身.提交当前(智能体,缓存,'edit',快照,缓存['activation'])#武装保持不变

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
        缓存=自身.准备变更(智能体)#实时加同步
        当前=自身.期望当前(缓存,引用)#引用必须对准
        可恢复=('active','paused','blocked')#可恢复阶段
        if 当前['phase'] not in 可恢复:#已完成等不可恢复
            raise 自身.迁移错误(当前,'resume',可恢复)#阶段不对
        if 当前['phase']=='active' and 缓存['activation']=='armed':#已经活跃且武装
            raise 目标错误('goal "'+str(当前['id'])+'" is already active and armed','GOAL_INVALID_TRANSITION')#空恢复
        if 缓存['state']['roundsStarted']>=当前['maxGoalRounds']:#预算耗尽
            raise 目标错误(#须先提高上限
                'goal "'+str(当前['id'])+'" exhausted '+str(当前['maxGoalRounds'])+' goal rounds; increase maxGoalRounds before resuming',#轮次用完
                'GOAL_INVALID_TRANSITION',#迁移非法
            )#结束抛错
        return 自身.提交当前(智能体,缓存,'resume',自身.带阶段(当前,'active'),'armed')#回到活跃并武装

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
        缓存=自身.准备变更(智能体)#实时加同步
        当前=自身.期望当前(缓存,引用)#引用必须对准
        if 当前['phase']!='active':#只能从活跃阻塞
            raise 自身.迁移错误(当前,'block',['active'])#阶段不对
        快照=自身.带阶段(当前,'blocked')#阶段迁移快照
        快照['blockedReason']=落实阻塞原因(原因)#阶段加已校验原因
        return 自身.提交当前(#提交阻塞快照
            智能体,#所属智能体
            缓存,#已同步缓存
            'block',#阻塞动词
            快照,#带原因的阻塞快照
            'disarmed',#阻塞后不再续跑
        )#结束提交

    def 清除(自身,智能体,引用):#清除
        """清除当前目标，同时保留持久墓碑与历史。"""
        缓存=自身.准备变更(智能体)#实时加同步
        当前=自身.期望当前(缓存,引用)#引用必须对准
        墓碑={'id':当前['id'],'revision':当前['revision']+1}#墓碑修订 +1
        变更={#清除变更
            'kind':'goal/change',#事件标签
            'version':目标变更版本,#当前版本
            'operation':'clear',#清除
            'cleared':墓碑,#墓碑引用
            'clearedAt':自身.下一变更时间(缓存),#不早于上次变更
        }#结束墓碑载荷
        自身.提交(智能体,缓存,变更,'disarmed')#提交并解除武装
        return dict(墓碑)#脱离副本

    @_远程('clear')
    def clear(自身,智能体,引用):#Remote 导出名 clear
        """Remote 导出名 clear。"""
        return 自身.清除(智能体,引用)#转中文

    def 准备变更(自身,智能体):#变更前置
        """解析并校验一次变更所用的缓存。"""
        自身.断言实时(智能体)#必须是实时实例
        缓存=自身.缓存(取字段(智能体,'session'))#拿到或播种
        自身.同步(取字段(智能体,'session'),缓存)#追上日志
        return 缓存#已同步缓存

    def 期望当前(自身,缓存,引用):#比较交换
        """拒绝过期或缺失的当前状态引用。"""
        当前=缓存['state']['goal']#当前快照
        if 当前 is None:#没有当前目标
            raise 目标错误('no current goal','GOAL_NOT_FOUND')#没有当前目标
        if 取字段(引用,'id')!=当前['id'] or 取字段(引用,'revision')!=当前['revision']:#身份或修订对不上
            raise 目标错误(#过期引用
                'stale goal ref "'+str(取字段(引用,'id'))+'" revision '+str(取字段(引用,'revision'))+'; current is "'+str(当前['id'])+'" revision '+str(当前['revision']),#指出当前修订
                'GOAL_STALE_REVISION',#比较交换失败
            )#结束抛错
        return 当前#对准的当前快照

    def 断言实时(自身,智能体):#实例同一性
        """强制精确的实时智能体身份，而不信任仅 id 匹配。"""
        if 自身.ctx.agents.get(取字段(智能体,'id')) is not 智能体:#不是注册表里那一份
            raise 目标错误('agent "'+str(取字段(智能体,'id'))+'" is not live in this registry','GOAL_AGENT_NOT_LIVE')#已换实例

    def 缓存(自身,会话):#懒播种
        """返回每会话缓存；首次以解除武装折叠一份种子。"""
        缓存=自身.缓存表.get(会话)#已有则用
        if 缓存 is not None:#命中
            return 缓存#已有缓存
        状态=空目标折叠状态()#空累加器
        for 事件 in 会话.events:#回放已有日志
            应用目标事件(状态,事件)#严格步进
        缓存={#新缓存
            'state':状态,#已折叠状态
            'activation':'disarmed',#种子默认解除武装
            'observedSeq':会话.seq,#已观察到当前序号
            'pendingActivation':None,#没有在途武装
        }#结束缓存
        自身.缓存表[会话]=缓存#按会话记住
        return 缓存#新缓存

    def 同步(自身,会话,缓存):#追上未观察事件
        """增量观察持久事件，并调和本地武装意图。"""
        事件们=会话.events#不可变快照
        for 事件 in 事件们[缓存['observedSeq']:]:#只看新事件
            应用目标事件(缓存['state'],事件)#严格步进
            if 取字段(事件,'type')=='goal/change':#本域变更
                待定=缓存['pendingActivation']#追加中待提交的武装
                if 待定 is not None and 待定['seq']==取字段(事件,'seq'):#若是自己刚追加的那条
                    缓存['activation']=待定['activation']#采用意图武装
                else:#外来变更默认解除武装
                    缓存['activation']='disarmed'#外来变更默认解除武装
            缓存['observedSeq']+=1#前进一步

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
        缓存=自身.准备变更(智能体)#实时加同步
        当前=自身.期望当前(缓存,引用)#引用必须对准
        if 当前['phase'] not in 允许:#阶段不对
            raise 自身.迁移错误(当前,操作,允许)#阶段不对
        return 自身.提交当前(智能体,缓存,操作,自身.带阶段(当前,阶段),武装)#提交迁移

    def 迁移错误(自身,当前,操作,允许):#阶段错误
        """渲染稳定的非法迁移错误。"""
        return 目标错误(#人类可读加稳定码
            'cannot '+str(操作)+' goal "'+str(当前['id'])+'" from phase "'+str(当前['phase'])+'"; expected '+' or '.join(允许),#指出期望阶段
            'GOAL_INVALID_TRANSITION',#迁移非法
        )#结束错误

    def 提交当前(自身,智能体,缓存,操作,快照,武装):#非创建快照提交
        """提交一次保留当前目标导出计数/时间的变更。"""
        创建于=缓存['state']['createdAt']#必须已有创建时间
        if 创建于 is None:#缓存坏了
            raise Exception('current goal cache lacks createdAt')#缓存坏了
        return 自身.提交快照(#带上保留的计数时间
            智能体,#所属智能体
            缓存,#已同步缓存
            操作,#动词
            快照,#下一快照
            缓存['state']['roundsStarted'],#轮次不变
            创建于,#创建时间不变
            自身.下一变更时间(缓存),#变更时间不倒退
            武装,#意图武装
        )#结束提交

    def 下一变更时间(自身,缓存):#不早于上次变更
        """在墙钟回拨时夹紧当前目标的下一时间戳。"""
        变更于=缓存['state']['updatedAt']#必须已有变更时间
        if 变更于 is None:#缓存坏了
            raise Exception('current goal cache lacks updatedAt')#缓存坏了
        return max(此刻毫秒(),变更于)#取较晚者

    def 提交快照(自身,智能体,缓存,操作,快照,已接纳轮次,创建于,变更于,武装):#整值提交
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
        自身.提交(智能体,缓存,变更,武装)#追加并通知
        视图=自身.视图(缓存)#读回实时视图
        if 视图 is None:#提交后不应变空
            raise Exception('snapshot commit cleared the goal unexpectedly')#提交后不应变空
        return 视图#已提交视图

    def 提交(自身,智能体,缓存,变更,武装):#追加边界
        """把一次变更提交进目标日志、缓存和实时事件流。"""
        引用=目标变更引用(变更)#本条引用
        会话=取字段(智能体,'session')#所属会话
        缓存['pendingActivation']={'seq':会话.seq,'activation':武装}#同步追加前记下意图
        try:#追加可能抛
            会话.append('goal/change',变更)#写入会话日志
            自身.同步(会话,缓存)#立即观察本条，采用 pending 武装
        finally:#无论成败都清掉意图
            缓存['pendingActivation']=None#避免残留到后续外来事件
        视图=自身.视图(缓存)#提交后视图，清除则为 None
        通知={#实时通知
            'operation':变更['operation'],#本次动词
            'ref':dict(引用),#脱离引用
        }#结束通知
        if 视图 is not None:#有当前目标才带视图
            通知['goal']=视图#带视图
        智能体事件(自身.ctx,智能体)['emit']('goal/changed',{'change':通知})#作用域内派发

    def 视图(自身,缓存):#缓存 → 视图
        """构造一份脱离的当前视图。"""
        目标=缓存['state']['goal']#当前快照
        创建于=缓存['state']['createdAt']#创建时间
        变更于=缓存['state']['updatedAt']#变更时间
        if 目标 is None:#没有当前目标
            return None#没有当前目标
        if 创建于 is None or 变更于 is None:#缺时间戳
            raise Exception('goal "'+str(目标['id'])+'" cache lacks timestamps')#缓存坏了
        结果={#脱离视图
            'id':目标['id'],#稳定身份
            'revision':目标['revision'],#正数修订
            'objective':目标['objective'],#陈述
            'phase':目标['phase'],#阶段
            'maxGoalRounds':目标['maxGoalRounds'],#上限
            'roundsStarted':缓存['state']['roundsStarted'],#已接纳轮次
            'createdAt':创建于,#创建时间
            'updatedAt':变更于,#变更时间
            'activation':缓存['activation'],#进程内武装
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

__all__=['目标服务','默认','default']#公开面
