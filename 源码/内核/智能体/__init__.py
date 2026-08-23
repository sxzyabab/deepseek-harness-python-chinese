"""Agent 服务：在线注册表、工厂委托，以及进程本地发起方作用域。

对齐上游 `agent/src/index.ts`。公开面仅中文名；ctx 服务槽 `agents`、事件名与诊断英文字面量保持上游。
具体创建与驱动归循环。
"""
import threading#线程本地存储与后台观察
from typing import NotRequired,TypedDict#结构类型
from ...依赖 import cordis#外部依赖胶水
服务=cordis.服务#服务基类
光纤状态=cordis.纤程状态#光纤/纤程状态
取可追踪=cordis.工具.取可追踪#可追踪
符号=cordis.工具.符号#符号
是否thenable=cordis.工具.是否thenable#可等待
承诺=cordis.工具.承诺#承诺
取符号=cordis.工具.取符号#取符号
可追踪包装=cordis.工具.可追踪包装#可追踪包装
from ..作用域 import 作用域目标#作用域载体构造
from .运行时类型 import *#再导出运行时类型（含智能体取消原因）
from .类型 import *#再导出可持久化类型
from .收件箱 import 收件箱,收件箱通知口#再导出收件箱
from .已消费工作 import 折叠已消费工作,交代领取,已消费工作账本#再导出已消费工作
from .模型选择 import 安装模型选择,模型选择,模型选择引用#再导出模型选择
from .派发 import (
    智能体事件派发,#派发器协议
    智能体载体,#作用域载体
    智能体事件,#融合派发器
    为组装构建上下文,#组装上下文
    发出智能体事件,#一次性发出
)

__all__=(#仅中文公开名；无英文别名
    '无工厂诊断','无发起方诊断','发起方已拆除诊断',
    '智能体设置提交','创建智能体选项','恢复智能体选项','已发表句柄','智能体工厂',
    '调用栈存储','智能体条目','发起运行','后台观察拒绝','智能体注册表','默认',
    '收件箱','收件箱通知口','折叠已消费工作','交代领取','已消费工作账本',
    '安装模型选择','模型选择','模型选择引用',
    '智能体事件派发','智能体载体','智能体事件','为组装构建上下文','发出智能体事件',
    '下一轮','下一步','收件箱目标','收件箱拼接字段',
    '智能体取消原因',
    '空闲','运行中','智能体状态','启动','恢复','清空','压缩','会话开始来源',
    '拒绝','进入','重试','智能体选项','取消选项','预步骤拒绝','预步骤进入','请求错误重试',
    '智能体句柄协议',
)#公开面结束

无工厂诊断='no agent factory registered (load an agent-loop plugin)'#无工厂诊断
无发起方诊断='no initiating agent is active'#无发起方诊断
发起方已拆除诊断='agent initiator scope is disposed'#发起方已拆除诊断

class 智能体设置提交:#尚未发表的设置在发表直前的同步收尾
    """设置在发表直前校验并提交已准备贡献。抛错则工厂回滚。"""
    def 提交(自身):#发表直前提交
        """在发表直前校验并提交已准备的设置。"""
        raise NotImplementedError('智能体设置提交.提交')#由设置回调返回

class 创建智能体选项(TypedDict):#经注册表工厂程序化创建的选项
    sessionId:object#在线 Agent/会话身份
    meta:NotRequired[object]#会话创建元数据（cwd／血统／种子边界等）
    seed:NotRequired[list]#初始回放/分叉历史
    agentOptions:NotRequired[object]#每 Agent 选项（模型……）
    signal:NotRequired[object]#仅创建取消信号
    setup:NotRequired[object]#尚未发表的作用域组合回调

class 恢复智能体选项(TypedDict):#在已持久化会话上恢复的选项
    resumeSessionId:object#要加载的已持久化会话 id
    agentOptions:NotRequired[object]#每 Agent 选项
    signal:NotRequired[object]#仅创建取消信号
    setup:NotRequired[object]#恢复时组合全新作用域的回调

class 已发表句柄:#被拥有的 Agent 外加其拆除器
    """create／resume 返回的被拥有句柄：主体 + 拆除能力。"""
    智能体=None#在线 Agent
    def 拆除(自身):#拆除本句柄
        """停止循环、注销、移除会话并解开作用域。"""
        raise NotImplementedError('已发表句柄.拆除')#由工厂实现

class 智能体工厂:#循环经设工厂提供的创建工厂
    """实现创建智能体／恢复；留在本包接口上，使消费方不依赖具体循环包。"""
    def 创建智能体(自身,所有者上下文,选项):#创建并发表
        """在调用方提供的会话 id 上创建新 Agent。"""
        raise NotImplementedError('智能体工厂.创建智能体')#由循环实现
    def 恢复(自身,所有者上下文,选项):#加载并恢复
        """准备已持久化会话并在其上恢复 Agent。"""
        raise NotImplementedError('智能体工厂.恢复')#由循环实现

class 调用栈存储:#对应 Node AsyncLocalStorage
    """按线程继承的存储，对应 Node AsyncLocalStorage 的同步压栈。"""
    def __init__(自身):#建立每线程栈
        """建立每线程空栈。"""
        自身._本地=threading.local()#每线程私有栈
        自身._已停用=False#是否已停用
    def _取栈(自身):#本线程栈
        """本线程栈，没有则建。"""
        栈=getattr(自身._本地,'栈',None)#本线程栈
        if 栈 is None:#首次使用
            栈=[]#空栈
            自身._本地.栈=栈#挂到线程本地
        return 栈#本线程栈
    def 取(自身):#读当前栈顶
        """读当前栈顶。"""
        if 自身._已停用:#已停用
            return None#停用后恒为无
        栈=getattr(自身._本地,'栈',None)#本线程栈
        if 栈 is None or len(栈)==0:#空栈
            return None#停用或空栈
        return 栈[-1]#栈顶
    def 跑(自身,值,操作):#压栈后调用
        """压栈后调用操作，返回后弹栈。"""
        栈=自身._取栈()#本线程栈
        栈.append(值)#压入
        try:#调用操作
            return 操作()#调用操作
        finally:#返回后弹栈
            栈.pop()#弹出
    def 停用(自身):#停用后再读得到 None
        """停用后再读得到 None。"""
        自身._已停用=True#标记停用

class 智能体条目:#一个精确注册表条目
    """一个精确注册表条目的全部可变生命周期状态。"""
    def __init__(自身,身份,智能体,所有者,载体):#记下身份、主体、所有者与载体
        """记下身份、主体、所有者与载体。"""
        自身.身份=身份#会话 id
        自身.智能体=智能体#Agent
        自身.所有者=所有者#运行时所有者
        自身.载体=载体#作用域载体
        自身.已宣布=False#是否已宣布
        自身.正在宣布=False#是否正在宣布
        自身.请求脱离=False#是否请求脱离

class 发起运行:#一个被跟踪的边界
    """一个被跟踪的边界外加其继承嵌套链。"""
    def __init__(自身,父):#记下父运行
        """记下父运行。"""
        自身.活动=True#是否仍活动
        自身.父=父#父运行

def 后台观察拒绝(值,记拒绝):#在后台等到 thenable 落定
    """在后台等到 thenable 落定，拒绝时记日志。"""
    def 观察():#收住拒绝
        """收住拒绝。"""
        try:#等待结算
            if hasattr(值,'等待'):#本库承诺
                值.等待()#等待结算
            else:#普通 thenable
                值.then(None,None)#等待结算
        except Exception as 错误:#拒绝
            记拒绝(错误)#记拒绝
    线程=threading.Thread(target=观察)#后台观察
    线程.daemon=True#不挡住退出
    线程.start()#启动

class 智能体注册表(服务):#Agent 注册表
    """跟踪在线 Agent，并经一条进程本地驱动器链携带发起 Agent。"""
    def __init__(自身,ctx):#登记 agents 服务
        """登记 agents 服务、Typert 查找与发起方生命周期。"""
        super().__init__(ctx,'agents')#注册服务名
        自身.存储={}#在线条目
        自身.工厂=None#工厂槽
        自身.发起方存储=调用栈存储()#发起 Agent
        自身.发起运行存储=调用栈存储()#发起运行
        自身.发起状态='active'#发起方状态
        自身.活动发起运行=0#活动运行数
        自身.发起排空=None#排空闩
        自身.发起拆除=None#拆除承诺
        自身._计数锁=threading.Lock()#运行计数锁
        def 登记类型(类型上下文,配置=None):#等到 typert 后登记
            """等到 typert 后登记查找与宿主上下文。"""
            def 解析智能体(会话身份):#按 id 解析 Agent
                """按 id 解析 Agent。"""
                return 自身.获取(会话身份)#在线 Agent
            def 解析上下文(会话身份):#按 id 解析 Agent 上下文
                """按 id 解析 Agent 上下文。"""
                智能体=自身.获取(会话身份)#在线 Agent
                if 智能体 is None:#没有该 Agent
                    return None#没有该 Agent
                return 智能体.ctx#Agent 作用域
            类型上下文.typert.lookups.register('agent',{
                'parameter':'agent',#参数名
                'wire':'agentId',#线路字段
                'hostTypeSymbol':'@deepseek-ai/dsh-agent#Agent',#宿主类型
                'wireTypeSymbol':'@deepseek-ai/dsh-session/types#SessionId',#线路类型
                'resolve':解析智能体,#按 id 解析
            })#查找结束
            类型上下文.typert.contexts.registerHost('agent',{
                'wire':'agentId',#线路字段
                'wireTypeSymbol':'@deepseek-ai/dsh-session/types#SessionId',#线路类型
                'resolve':解析上下文,#解析 Agent 上下文
            })#宿主结束
        ctx.inject(['typert'],登记类型)#等到 typert
        def 取智能体(目标,接收者,错误):#普通上下文默认没有当前 Agent
            """普通上下文默认没有当前 Agent。"""
            return None#默认 undefined
        ctx.accessor('agent',{'get':取智能体})#默认 None
        def 状态监听(光纤对象,*剩余):#本服务生命周期祖先正在卸载则关闭
            """本服务生命周期祖先正在卸载则关闭新发起边界。"""
            if 光纤对象.state==光纤状态.卸载中 and 自身.有生命周期祖先(光纤对象):#正在卸载
                自身.关闭发起方()#关闭新发起边界
        ctx.on('internal/status',状态监听)#监听光纤状态
        def 发起方生命周期():#先排空再失效
            """先排空再失效，再拒绝新边界。"""
            yield 自身.拆除发起方#先排空再失效
            def 关闭():#再拒绝新边界
                """再拒绝新边界。"""
                自身.关闭发起方()#关闭
            yield 关闭#再拒绝新边界
        ctx.effect(发起方生命周期,'agents.initiatorLifecycle()')#绑定生命周期
    def 当前发起方(自身):#读当前发起方
        """读继承的异步驱动器链所发起的 Agent。"""
        自身.断言发起方可读()#已拆除则抛
        return 自身.发起方存储.取()#取出存储
    def 要求发起方(自身):#要求发起方
        """读发起 Agent，没有活动发起边界时失败。"""
        智能体=自身.当前发起方()#读取
        if 智能体 is None:#没有
            raise Exception(无发起方诊断)#没有则抛
        return 智能体#返回
    def 带发起方(自身,智能体,操作):#带发起方运行
        """以一个精确 Agent 作为其进程本地发起方运行一项操作。"""
        return 自身.带着发起方跑(智能体,操作)#委托
    def 无发起方(自身,操作):#无发起方运行
        """在隐藏任何继承发起 Agent 的边界内运行一项操作。"""
        return 自身.带着发起方跑(None,操作)#清除发起方
    def 设工厂(自身,工厂):#登记工厂
        """登记 Agent 创建工厂；已有工厂则抛错。"""
        def 设工厂体():#挂上 effect 并在拆除时清空槽
            """挂上 effect 并在拆除时清空槽。"""
            if 自身.工厂 is not None:#已有工厂
                raise Exception('an agent factory is already registered')#不得重复
            原始=取符号(工厂,符号.原始)#剥到具体目标
            if 原始 is None and isinstance(工厂,可追踪包装):#可追踪包装
                原始=object.__getattribute__(工厂,'_值')#包装内目标
            目标=工厂 if 原始 is None else 原始#无原始则用传入
            自身.工厂={'target':目标}#写入槽
            def 清空():#拆除时清空
                """拆除时清空。"""
                自身.工厂=None#清空
            return 清空#拆除器
        return 自身.ctx.effect(设工厂体,'agents.setFactory()')#精确拆除器
    def 要求工厂(自身):#返回活动创建工厂
        """返回活动创建工厂。"""
        if 自身.工厂 is None:#未登记
            raise Exception(无工厂诊断)#未登记则抛
        return 自身.工厂#返回槽
    def 创建(自身,选项):#创建
        """经已登记工厂创建并发表新 Agent。"""
        所有者上下文=自身.ctx#调用方上下文
        目标=自身.要求工厂()['target']#取出具体工厂
        接收器=取可追踪(所有者上下文,目标)#调用方追踪接收器
        方法=目标.创建智能体#工厂创建方法
        函数=getattr(方法,'__func__',方法)#未绑定函数
        return 函数(接收器,所有者上下文,选项)#委托创建
    def 恢复(自身,选项):#恢复
        """经已登记工厂加载已持久化会话并在其上恢复 Agent。"""
        所有者上下文=自身.ctx#调用方上下文
        目标=自身.要求工厂()['target']#取出具体工厂
        接收器=取可追踪(所有者上下文,目标)#调用方追踪接收器
        方法=目标.恢复#工厂恢复方法
        函数=getattr(方法,'__func__',方法)#未绑定函数
        return 函数(接收器,所有者上下文,选项)#委托恢复
    def 登记(自身,智能体):#登记
        """登记一个在线 Agent。同 id 已登记则抛。"""
        def 登记体():#先进入再宣布
            """先进入再宣布。"""
            yield 自身.进入(智能体,自身.ctx.agent)#先进入
            自身.宣布(智能体)#再宣布
        return 自身.ctx.effect(登记体,'agents.register()')#精确拆除器
    def 进入(自身,智能体,所有者):#进入注册表
        """插入已构造 Agent 但不宣布它。"""
        身份=智能体.id#Agent id
        if 身份!=智能体.session.id:#与会话 id 不一致
            raise Exception('agent id "'+str(身份)+'" does not match session id "'+str(智能体.session.id)+'"')#必须同一身份
        载体=作用域目标(智能体,智能体)#以自身为键的载体
        if 身份 in 自身.存储:#已登记
            raise Exception('agent "'+str(身份)+'" is already registered')#不得覆盖
        条目=智能体条目(身份,智能体,所有者,载体)#新条目
        自身.存储[身份]=条目#写入存储
        仍有效=True#脱离是否仍有效
        def 脱离():#幂等脱离
            """幂等脱离。"""
            nonlocal 仍有效#修改外层
            if not 仍有效:#已脱离
                return#已脱离
            仍有效=False#标为失效
            if 条目.正在宣布:#正在宣布
                条目.请求脱离=True#推迟脱离
                return#等宣布结束
            自身.脱离已进入(条目)#立即脱离
        return 脱离#返回脱离器
    def 脱离已进入(自身,条目):#脱离已进入条目
        """移除一个精确已进入 Agent，并在已宣布时发出其配对拆除。"""
        条目.请求脱离=False#清掉推迟标记
        if 自身.存储.get(条目.身份) is not 条目:#不是当前条目
            return#不是当前条目
        del 自身.存储[条目.身份]#从存储删掉
        if not 条目.已宣布:#未宣布
            return#未宣布则无配对拆除
        自身.发出已拆除(条目)#发出拆除
    def 发出已拆除(自身,条目):#发出 agent/disposed
        """经条目的稳定载体发出配对拆除边。"""
        参数=[条目.载体,'agent/disposed',{'agent':条目.智能体}]#载体、事件名、载荷
        for 回调 in 自身.ctx.events.dispatch('emit',参数):#逐个监听器
            try:#收住同步抛错
                返回=回调(*参数)#调用
                if 是否thenable(返回):#返回承诺
                    def 记拒绝(错误,身份=条目.身份):#收住 Promise 拒绝
                        """收住 Promise 拒绝。"""
                        自身.ctx.logger.warn('agent "'+str(身份)+'": agent/disposed listener rejected: '+str(错误))#记拒绝
                    后台观察拒绝(返回,记拒绝)#后台观察
            except Exception as 错误:#同步抛错
                自身.ctx.logger.warn('agent "'+str(条目.身份)+'": agent/disposed listener threw: '+str(错误))#记抛错
    def 宣布(自身,智能体):#宣布
        """宣布先前用进入插入的 Agent。"""
        条目=自身.存储.get(智能体.id)#取条目
        if 条目 is None or 条目.智能体 is not 智能体:#不是在线条目
            raise Exception('agent "'+str(智能体.id)+'" is not live in this registry')#必须是本注册表在线实例
        if 条目.已宣布 or 条目.正在宣布:#已经或正在宣布
            raise Exception('agent "'+str(条目.身份)+'" was already announced')#不得重复宣布
        条目.正在宣布=True#正在宣布
        条目.已宣布=True#已宣布
        参数=[条目.载体,'agent/created',{'agent':条目.智能体}]#载体、事件名、载荷
        try:#派发创建
            for 回调 in 自身.ctx.events.dispatch('emit',参数):#逐个监听器
                返回=回调(*参数)#调用
                if 是否thenable(返回):#返回承诺
                    def 记拒绝(错误,身份=条目.身份):#收住拒绝
                        """收住拒绝。"""
                        自身.ctx.logger.warn('agent "'+str(身份)+'": agent/created listener rejected: '+str(错误))#记拒绝
                    后台观察拒绝(返回,记拒绝)#后台观察
        finally:#无论成败
            条目.正在宣布=False#宣布结束
            if 条目.请求脱离:#有推迟脱离
                自身.脱离已进入(条目)#有推迟脱离则执行
    def 获取(自身,身份):#按 id 查找
        """查找在线 Agent。"""
        条目=自身.存储.get(身份)#取条目
        if 条目 is None:#没有该 id
            return None#没有该 id
        return 条目.智能体#取出 Agent
    def 是否被拥有(自身,身份,所有者):#是否被该所有者拥有
        """测试一个在线 Agent 是否经某个精确父 Agent 的作用域上下文创建。"""
        条目=自身.存储.get(身份)#取条目
        if 条目 is None:#没有该 id
            return False#没有该 id
        return 条目.所有者 is 所有者#比较运行时所有者
    def 列出(自身):#列出全部
        """全部在线 Agent，按登记顺序。"""
        return [条目.智能体 for 条目 in 自身.存储.values()]#按插入序
    def 诸根(自身):#列出根
        """全部在线顶层 Agent，按登记顺序。"""
        return [条目.智能体 for 条目 in 自身.存储.values() if 条目.所有者 is None]#无运行时所有者
    def 关闭发起方(自身):#关闭发起方
        """在继承续跑排空时拒绝新的发起边界。"""
        if 自身.发起状态=='active':#活动
            自身.发起状态='closing'#活动则改为关闭中
    def 拆除发起方(自身):#拆除发起方
        """等待返回承诺边界，然后使保留引用失效。"""
        if 自身.发起拆除 is None:#首次拆除
            任务=承诺()#共享一次拆除
            自身.发起拆除=任务#先挂上
            自身.关闭发起方()#先关闭
            自身.释放重入发起运行()#排除启动本拆除的链
            if 自身.活动发起运行!=0:#还有活动运行
                if 自身.发起排空 is None:#尚无排空闩
                    自身.发起排空=承诺()#建排空闩
                自身.发起排空.等待()#等到归零
            自身.发起状态='disposed'#标为已拆除
            自身.发起方存储.停用()#停用发起存储
            自身.发起运行存储.停用()#停用运行存储
            任务.兑现()#完成本次拆除
        return 自身.发起拆除#共享拆除承诺
    def 带着发起方跑(自身,智能体,操作):#建立一个被跟踪的发起或清除边界
        """建立一个被跟踪的发起或清除边界。"""
        if 自身.发起状态!='active':#非活动
            raise Exception(发起方已拆除诊断)#非活动则拒
        运行=发起运行(自身.发起运行存储.取())#新运行
        自身._计数锁.acquire()#加锁
        自身.活动发起运行+=1#计数加一
        自身._计数锁.release()#解锁
        def 内层():#嵌套发起方存储
            """嵌套发起方存储。"""
            return 自身.发起方存储.跑(智能体,操作)#发起方存储
        try:#调用操作
            结果=自身.发起运行存储.跑(运行,内层)#嵌套两层
        except Exception:#同步抛错
            自身.释放发起运行(运行)#释放运行
            raise#原样抛出
        if isinstance(结果,承诺):#返回承诺
            def 完成后释放():#落定后释放
                """落定后释放。"""
                自身.释放发起运行(运行)#释放
            try:#挂观察者
                def 观察():#落定后释放
                    """落定后释放。"""
                    try:#原语 then
                        结果.then(None,None)#原语 then
                    except Exception:#挂观察者失败
                        完成后释放()#挂观察者失败则立即释放
                        return#结束
                    完成后释放()#落定后释放
                线程=threading.Thread(target=观察)#后台观察
                线程.daemon=True#不挡住退出
                线程.start()#启动
            except Exception:#观察者设置未接上
                自身.释放发起运行(运行)#观察者设置未接上则立即释放
        else:#同步值
            自身.释放发起运行(运行)#立即释放
        return 结果#原样返回
    def 有生命周期祖先(自身,候选):#是否生命周期祖先
        """一个正在卸载的光纤是否拥有本服务的生命周期。"""
        光纤对象=自身.ctx.fiber#从本服务光纤起
        while True:#上溯
            if 光纤对象 is 候选:#命中
                return True#命中
            父=光纤对象.parent.fiber#父光纤
            if 父 is 光纤对象:#已到根
                return False#已到根
            光纤对象=父#继续上溯
    def 断言发起方可读(自身):#断言仍可读
        """已拆除则抛。"""
        if 自身.发起状态=='disposed':#已拆除
            raise Exception(发起方已拆除诊断)#已拆除则抛
    def 释放重入发起运行(自身):#释放重入运行
        """把启动本拆除的边界链从其自身排空中排除。"""
        运行=自身.发起运行存储.取()#当前链
        while 运行 is not None:#沿父释放
            自身.释放发起运行(运行)#释放本层
            运行=运行.父#上一层
    def 释放发起运行(自身,运行):#释放一次运行
        """释放一次运行。"""
        自身._计数锁.acquire()#加锁
        try:#改计数
            if not 运行.活动:#已释放
                return#已释放
            运行.活动=False#标为失效
            自身.活动发起运行-=1#计数减一
            if 自身.活动发起运行!=0:#还有活动
                return#还有活动
            if 自身.发起排空 is not None:#有排空闩
                自身.发起排空.兑现()#唤醒排空
            自身.发起排空=None#清掉闩
        finally:#解锁
            自身._计数锁.release()#解锁

默认=智能体注册表#默认导出注册表类
