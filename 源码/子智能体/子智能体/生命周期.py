"""两种子智能体形态的生命周期边发布：带隔离的发射器、一次性跑观察者、可续跑 Activation 观察者。公开载荷约定与缝的其余面向消费方类型一起放在类型模块；本模块只拥有实现，以及续跑管理器消费的包私有 ActivationObserver。"""
import uuid#随机uuid
from cordis.工具 import 是否thenable#可等待判定
from agent import 折叠已消费工作#导入已消费工作折叠
from .助手输出 import 最终助手输出#导入最终助手输出选取
from .类型 import 子智能体跑标识#导入跑id品牌构造

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

def 渲染抛值(值):#渲染抛出值
    """渲染任何监听器抛出的值，不让强制转换逃出隔离。"""
    try:#隔离强制转换失败
        if isinstance(值,Exception):#错误
            return 值.__class__.__name__+': '+str(值)#名与文案
        return str(值)#普通值
    except Exception:#强制转换自己抛
        return '<unrenderable thrown value>'#不可渲染哨兵

def 创建生命周期发射器(上下文对象,载体):#建造带隔离发射器
    """建造本缝每条边都经其发布的带隔离生命周期发射器。每个监听器独立隔离：同步抛出或返回的承诺拒绝会被记录，而不饿死对等监听器。"""
    def 发射(名称,信息,父=None):#发布一条边
        """发布一条生命周期边。"""
        if 父 is None:#无作用域派发
            派发参数=[名称,信息]#无作用域
        else:#带作用域载体
            派发参数=[载体(父),名称,信息]#带作用域
        for 回调 in 上下文对象.events.dispatch('emit',派发参数):#逐监听器
            try:#隔离同步抛出
                返回=回调(信息)#调用监听器
                if 是否thenable(返回):#返回承诺
                    def 记拒绝(错误,_名=名称):#隔离返回的拒绝
                        """记录拒绝。"""
                        上下文对象.logger.warn('subagent: '+_名+' listener rejected: '+渲染抛值(错误))#记录拒绝
                    try:#挂 catch
                        返回.catch(记拒绝)#隔离拒绝
                    except Exception:#无catch则旁路
                        pass#忽略
            except Exception as 错误:#同步抛出
                上下文对象.logger.warn('subagent: '+名称+' listener threw: '+渲染抛值(错误))#记录抛出
    return 发射#生命周期发射器

def 观察跑(发射,提供方,父,跑):#观察一次性跑
    """为一次被接受的一次性跑发出 start/end 生命周期对。返回同一跑，未改动。"""
    身份={#共享身份
        'runId':子智能体跑标识(str(uuid.uuid4())),#铸造跑id
        'provider':提供方,#提供方名
        'id':取字段(跑,'id'),#子会话id
        'local':取字段(跑,'localAgent') is not None,#是否进程内
    }#identity结束
    # 在派发 start 之前挂上终态观察者。Promise 反应仍在这次同步 start 发射之后跑，保持 start → end。
    结果=取字段(跑,'result')#结果承诺
    def 成功(结果值):#成功决议
        """成功决议后发 end。"""
        载荷=dict(身份)#共享身份
        载荷['stopReason']=取字段(结果值,'stopReason')#停止原因
        输出=取字段(结果值,'output') or []#最终输出
        if len(输出)>0:#有输出才带上
            载荷['lastAssistantMessage']=输出#带上
        发射('subagent/end',载荷,父)#终态边
    def 失败(_错误=None):#基础设施拒绝
        """基础设施拒绝后发 error 终态。"""
        载荷=dict(身份)#共享身份
        载荷['stopReason']='error'#错误终态
        发射('subagent/end',载荷,父)#终态边
    if 是否thenable(结果):#承诺
        结果.then(成功,失败)#挂观察
    else:#已决议值
        try:#同步结果
            成功(结果)#当成功
        except Exception:#同步失败
            失败()#当失败
    发射('subagent/start',身份,父)#发布start
    return 跑#原跑

def 纪元停止原因(事件们):#从后缀推导停止原因
    """本子体纪元为何结束，供终态生命周期边与管理器自己的父投递使用。子体自己的日志是权威。"""
    折叠=折叠已消费工作(事件们)#折叠已消费工作
    结束=取字段(折叠,'end')#记账回合结束
    丢弃未跑=取字段(折叠,'droppedUnrun')#已接受但未跑的取消
    种类=None#回合结束种类
    if 结束 is not None:#有结束事件
        种类=取字段(取字段(取字段(结束,'data'),'reason'),'kind')#结束种类
    if 种类=='max-tokens':#token上限
        return 'max-tokens'#映射max-tokens
    if 种类 in ('aborted','interrupted'):#已中止或打断
        return 'aborted'#映射aborted
    if 种类=='error':#错误
        return 'error'#映射error
    # 步骤前拒绝——钩子拒绝、策略插件——丢弃了本纪元已认领的输入：工作被谢绝，不是做完。
    if 种类=='blocked':#被拦截
        return 'refusal'#映射refusal
    # 干净结束与完全没有记账回合共享一条规则：纪元做完了交给它的东西，除非取消队列另有说明。
    if 种类 is None or 种类=='completed':#没有记账回合或干净完成
        return 'aborted' if 丢弃未跑 else 'completed'#有未跑取消则aborted
    # 可合并扩展的原因：未知变体不当成成功
    return 'error'#不当成成功

def 创建激活观察者(发射,提供方,子标识,父):#建造Activation观察者
    """为一次可续跑 Activation 的驻留纪元建造观察者。观察者看到与一次性跑相同的词汇。驻留前的创建失败不发生命周期边。"""
    身份={'runId':子智能体跑标识(str(uuid.uuid4())),'provider':提供方,'id':子标识,'local':True}#共享身份，进程内
    # 冷恢复会回放更早回合，因此本纪元遥测必须来自它实际产出的后缀——绝不是整份会话。
    边界=[0]#纪元后缀起点（用列表可变）
    捕获=[{'stopReason':'completed'}]#捕获的终态
    def 终态(失败):#解析终态
        """解析 settle 将发布的终态事实，但不发布它们。"""
        if 失败 is None:#成功
            return 捕获[0]#成功用捕获事实
        return {'stopReason':'error'}#失败覆盖为error
    def 开始(子):#驻留后发start
        """纪元驻留后发布开始边。"""
        边界[0]=len(取字段(取字段(子,'session'),'events') or [])#记下后缀起点
        发射('subagent/start',身份,父)#发布start
    def 快照(子):#拆除前快照
        """在子体仍登记时快照依赖子体的终态事实。"""
        事件们=取字段(取字段(子,'session'),'events') or []#整份事件
        自身后缀=事件们[边界[0]:]#本纪元后缀
        输出=最终助手输出(自身后缀)#选取最终输出
        记={'stopReason':纪元停止原因(自身后缀)}#记下终态
        if 输出 is not None:#有输出才带上
            记['output']=输出#带上
        捕获[0]=记#保存
    def 结算(失败):#发布end
        """在拆除结局已知后恰好发布一次终态边。"""
        解析=终态(失败)#解析终态
        载荷=dict(身份)#共享身份
        载荷['stopReason']=取字段(解析,'stopReason')#停止原因
        输出=取字段(解析,'output')#可选输出
        if 输出 is not None:#有输出才带上
            载荷['lastAssistantMessage']=输出#带上
        发射('subagent/end',载荷,父)#终态边
    return {'start':开始,'capture':快照,'terminal':终态,'settle':结算}#观察者实现
