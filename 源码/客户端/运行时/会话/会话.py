"""拥有一个会话的事件窗口、派生会话状态和可观察快照。

对齐上游 `runtime/src/client/sessions/session.ts`。公开面仅中文名。
会话创建后常驻，以便在后台继续消费 mux 帧。
React 绑定留在本数据层之外。

依赖未迁: conversation-assembler.ts → 会话组装器.py（会话节点组装器）
"""
import asyncio#打开与缺口修复任务
import base64 as 基64#附件 base64 解码
import sys#错误打印到 stderr
from .挂起 import 挂起等待#挂起交互等待
from .通知器 import 通知器#脏标记通知器
from .投影仓库 import 投影值仓库#投影值存储
from .队列镜像 import 会话队列镜像#队列镜像
from .会话快照 import 空聊天快照#空聊天切片
from .会话组装器 import 会话节点组装器#节点组装器（依赖未迁）
from ..时区 import 解析客户端时区#客户端时区

__all__=['页消息数','会话']#仅中文公开名

页消息数=50#每页历史请求的消息数

def 取字段(对象,键,缺省=None):#读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

def 折叠传输错误(错误):#载体抛错 → 业务错误支
    """对齐 apiproxy transportError：internal + 空 details。"""
    if isinstance(错误,BaseException):#异常
        消息=str(错误)#取 message
    else:#其它
        消息=str(错误)#String()
    return {'ok':False,'error':{'code':'internal','message':消息,'details':{}}}#失败支

def 会话输入(条目):#历史行 → 组装输入
    """把一行线历史转成组装器的传输中立输入。"""
    return {'event':取字段(条目,'event'),'view':取字段(条目,'view')}#事件 + 视图

def 有可见会话内容(聊天):#是否有可见会话内容
    """单独一行通用命令仍是控制面内容；任何其他可见 Chat 节点都会激活会话。"""
    顺序=取字段(聊天,'order') or ()#渲染顺序
    节点仓=取字段(聊天,'nodes')#节点仓库
    for 键 in 顺序:#逐键
        节点=节点仓.get(键) if 节点仓 is not None else None#按键读
        if 取字段(节点,'kind')!='command':#非 command 即可见业务
            return True#有内容
    return False#全是命令或空

def 推导阶段(有内容,已尝试提示):#推导作曲阶段
    """composerPhase 判断 — 唯一计算该条件的地点。

    失败的首次提示停留在 engaging，直到权威的已接受回合、running 或挂起信号到达。
    @param 有内容 - 超出挂起首次提示的权威非空白活动。
    @param 已尝试提示 - 本会话对象上已发起过提示。
    @returns 派生阶段。
    """
    if 有内容:#已有内容则活跃
        return 'active'#活跃
    return 'engaging' if 已尝试提示 else 'blank'#仅尝试过则 engaging，否则空白

def 剥信封载荷(帧):#剥 type/sessionId
    """从请求帧剥掉信封字段，留下领域载荷。"""
    if isinstance(帧,dict):#映射帧
        return {键:值 for 键,值 in 帧.items() if 键 not in ('type','sessionId')}#领域字段
    载荷={}#属性帧
    for 键 in dir(帧):#枚举
        if 键.startswith('_') or 键 in ('type','sessionId'):#跳过私有与信封
            continue#下一项
        值=getattr(帧,键,None)#取值
        if callable(值):#方法不算载荷
            continue#跳过
        载荷[键]=值#记下
    return 载荷#领域字段

def 挂任务(协程):#fire-and-forget
    """有事件环则挂 Task；无环则调用方稍后驱动。"""
    try:#有环
        return asyncio.get_running_loop().create_task(协程)#挂任务
    except RuntimeError:#无环
        return 协程#裸协程

class _空事件名册:#空事件定义面
    """未传入注册表时的空事件名册。"""

    def 条目们(自身):#普通定义
        """登记顺序的普通定义。"""
        return []#空

    def 回退条目(自身):#回退定义
        """已登记时的未匹配事件回退。"""
        return None#无回退

class _空视图名册:#空视图定义面
    """未传入注册表时的空视图名册。"""

    def 条目们(自身):#视图定义
        """登记顺序的视图构建器工厂。"""
        return []#空

class 会话:#会话对象层
    """拥有一个会话的事件窗口、派生会话状态和可观察快照。

    功能代码只看见会话面切片；其余公开成员是管理器/运行时入口。
    """

    def __init__(自身,会话标识,接口,远程,选项=None):#会话对象
        """构造会话对象层。

        @param 会话标识 - 宿主会话身份（客户端会话一律由宿主诞生）。
        @param 接口 - 共享线客户端。
        @param 远程 - 本会话调用的生成 Remote 命名空间。
        @param 选项 - 可选的管理器持有状态观察者。
        """
        选项=选项 or {}#缺省空选项
        自身.会话标识=会话标识#宿主会话身份
        自身._接口=接口#共享线客户端
        自身._远程=远程#本会话 Remote 面
        自身._选项=选项#可选管理器观察者
        自身._事件们=[]#当前窗口原始事件
        自身._视图们=[]#与事件对齐的工具视图
        自身._基序号=0#窗口第一条事件的 seq
        自身._还有更多=False#更早页是否还有
        自身._打开态='cold'#打开生命周期
        自身._打开错误=None#打开失败错误
        自身._打开承诺=None#飞行中的 open
        自身._打开代际=0#打开代际
        自身._加载更早中=False#是否正在上翻更早页
        自身._挂起={}#挂起交互
        自身._挂起修订=0#挂起映射修订号
        自身._挂起缓存=None#按修订缓存的挂起数组
        自身._队列镜像=会话队列镜像()#队列镜像
        投影=取字段(选项,'投影们')#可选共享投影存储（对齐 options.projections）
        自身.投影=投影 if 投影 is not None else 投影值仓库()#采纳共享或自建
        自身._地址=取字段(选项,'地址')#可选子智能体地址
        父可用=取字段(选项,'父可用')#可选父可用性
        自身._父可用=False if 父可用 is None else 父可用#记下父可用性
        会话运行时=取字段(选项,'会话运行时')#可选会话注册表（对齐 options.conversation）
        if 会话运行时 is None:#未传入注册表
            自身._对话=会话节点组装器(_空事件名册(),_空视图名册())#空组装器
        else:#用传入注册表
            自身._对话=会话节点组装器(取字段(会话运行时,'事件'),取字段(会话运行时,'视图'))#传入注册表
        自身._运行中=False#当前是否在跑一轮
        自身._已尝试提示=False#是否已尝试发送
        自身._首次提示待回合=False#首次提示尚待回合
        自身._空白位=True#是否空白
        自身._已移除=False#宿主是否已移除
        自身._提示错误=None#发送/停止错误
        自身._最近智能体错误=None#最近一次无回合位置的智能体错误
        自身._直播缓冲=[]#直播缓冲
        自身._缝合中=False#是否正在缝合缺口
        自身._订阅末序号=None#订阅基线 seq
        自身._作用域=None#可选作用域上下文
        自身._通知器=通知器(自身._重建快照缓存)#脏时刷新组装器并重建快照
        自身._快照缓存=自身._建快照()#编出初始快照

    def _重建快照缓存(自身):#通知器回调
        """脏时冲掉待发布节点并重建缓存快照。"""
        自身._对话.冲刷()#冲掉待发布节点
        自身._快照缓存=自身._建快照()#重建缓存快照

    def 绑定作用域(自身,作用域):#绑定作用域
        """绑定 SessionRuntime 铸造的 Agent 作用域上下文（只写一次）。

        @param 作用域 - 智能体的作用域上下文。
        """
        if 自身._作用域 is not None:#重复绑定
            raise Exception('session '+str(自身.会话标识)+' already has a bound scope')#接线错误
        自身._作用域=作用域#记下作用域

    def 解绑作用域(自身):#解绑作用域
        """拆除时释放已绑定作用域。"""
        自身._作用域=None#清掉派发点

    async def 发提示(自身,内容,模式):#发送提示
        """发送（queue/steer 1:1 透传）；失败落入快照的 promptError。

        @param 内容 - 文本加上浏览器持有的临时图片上传。
        @param 模式 - queue 追加到当前回合之后；steer 打断当前回合。
        @returns 提示结果（失败时也镜像进 promptError）。
        """
        自身._提示错误=None#清上次发送错误
        自身._最近智能体错误=None#清上次智能体错误
        自身._已尝试提示=True#粘性发送标记
        if 自身._空白位:#空白上首次发送
            自身._首次提示待回合=True#尚待回合
        自身._通知器.标脏()#立刻刷新作曲阶段
        try:#按地址选传输
            if 自身._地址 is None:#普通会话
                响应=await 自身._接口.sessions.prompt({#走会话 prompt
                    'sessionId':自身.会话标识,#本会话
                    'mode':模式,#queue 或 steer
                    'content':内容,#提示内容
                    'clientTimeZone':解析客户端时区(),#客户端时区
                })#结束请求
                结果=取字段(响应,'result',响应)#取出结果
            elif 取字段(自身._地址,'mode')=='one-shot':#一次性子智能体只读
                结果={#合成拒绝
                    'ok':False,#失败
                    'error':{#子智能体不可续跑
                        'code':'subagent-not-resumable',#错误码
                        'message':'one-shot subagent conversations are read-only',#只读说明
                        'details':{'childSessionId':取字段(自身._地址,'childSessionId')},#子会话 id
                    },#结束 error
                }#结束一次性拒绝
            else:#可续跑子智能体
                if any(取字段(块,'type')=='image' for 块 in 内容):#续跑不支持图片
                    结果={#合成附件错误
                        'ok':False,#失败
                        'error':{#图片不可用
                            'code':'attachment-error',#错误码
                            'message':'Image input is unavailable for subagent continuations.',#图片不可用说明
                            'details':{'reason':'SUBAGENT_IMAGE_UNSUPPORTED'},#原因
                        },#结束 error
                    }#结束图片拒绝
                else:#纯文本续跑
                    文本块们=[{'type':'text','text':取字段(块,'text')} for 块 in 内容 if 取字段(块,'type')=='text']#只保留文本
                    载荷=dict(自身._地址) if isinstance(自身._地址,dict) else {#父/子地址
                        'parentSessionId':取字段(自身._地址,'parentSessionId'),#父
                        'childSessionId':取字段(自身._地址,'childSessionId'),#子
                        'mode':取字段(自身._地址,'mode'),#模式
                    }#结束地址展开
                    载荷['content']=文本块们#文本部分
                    载荷['clientTimeZone']=解析客户端时区()#客户端时区
                    响应=await 自身._接口.subagents.prompt(载荷)#走子智能体 prompt
                    路由=取字段(响应,'result',响应)#取出路由结果
                    if 取字段(路由,'ok'):#成功则归一成 accepted
                        结果={'ok':True,'value':{'accepted':True}}#接受
                    else:#失败原样
                        结果=路由#路由失败
        except Exception as 错误:#传输失败
            结果=折叠传输错误(错误)#折成 RPC 错误
        if not 取字段(结果,'ok'):#宿主拒绝或传输失败
            自身._提示错误={'op':'send','error':取字段(结果,'error')}#写入发送错误槽
            自身._通知器.标脏()#刷新错误条
            return 结果#原样返回失败
        if 自身._空白位:#仍空白且本次已接受
            自身._空白位=False#降下空白位
            回调=取字段(自身._选项,'首次浮出')#管理器浮出回调（对齐 options.onEngaged）
            if 回调 is not None:#有回调
                回调(自身)#通知管理器浮出列表行
            自身._通知器.标脏()#刷新快照
        return 结果#返回接受结果

    async def 读附件(自身,附件标识):#读附件字节
        """把本会话引用的一张图解析成可消费的字节。

        @param 附件标识 - 折叠会话日志里的不透明 id。
        @returns 已认证引用与解码字节。
        """
        try:#拉取并解码
            响应=await 自身._接口.sessions.attachment({#请求附件
                'sessionId':自身.会话标识,#本会话
                'attachmentId':附件标识,#附件 id
            })#结束请求
            结果=取字段(响应,'result',响应)#取出结果
            if not 取字段(结果,'ok'):#业务失败
                return 结果#原样返回
            值=取字段(结果,'value') or {}#成功值
            数据=基64.b64decode(取字段(值,'data') or '')#base64 → 字节
            return {'ok':True,'value':{'attachment':取字段(值,'attachment'),'data':数据}}#引用 + 字节
        except Exception as 错误:#传输失败
            return 折叠传输错误(错误)#折成 RPC 错误

    async def 更新队列(自身,项标识,动作):#改队列项
        """对仍挂起的队列出现施加一次操作。"""
        try:#调用宿主
            响应=await 自身._接口.sessions.updateQueue({#更新队列
                'sessionId':自身.会话标识,#本会话
                'itemId':项标识,#队列项
                'action':动作,#动作
            })#结束请求
            return 取字段(响应,'result',响应)#原样返回
        except Exception as 错误:#传输失败
            return 折叠传输错误(错误)#折成 RPC 错误

    async def 取消(自身):#停止当前回合
        """停止活动回合，同时宿主保留挂起收件箱工作；失败落入 promptError。"""
        地址=自身._地址#当前子智能体地址
        if 地址 is not None and 取字段(地址,'mode')=='one-shot':#一次性不可取消
            结果={#合成拒绝
                'ok':False,#失败
                'error':{#激活取消不可用
                    'code':'subagent-delivery-unavailable',#错误码
                    'message':'subagent activation cancellation is unavailable',#取消不可用说明
                    'details':{'childSessionId':取字段(地址,'childSessionId')},#子会话 id
                },#结束 error
            }#结束一次性拒绝
            自身._提示错误={'op':'stop','error':取字段(结果,'error')}#写入停止错误槽
            自身._通知器.标脏()#刷新错误条
            return 结果#返回拒绝
        try:#按地址选中断路径
            if 地址 is not None:#有子智能体地址
                响应=await 自身._接口.subagents.interrupt(地址)#走子智能体中断
            else:#普通会话
                响应=await 自身._接口.sessions.cancel({'sessionId':自身.会话标识})#走会话取消
            结果=取字段(响应,'result',响应)#取出结果
        except Exception as 错误:#传输失败
            结果=折叠传输错误(错误)#折成 RPC 错误
        if not 取字段(结果,'ok'):#宿主拒绝或传输失败
            自身._提示错误={'op':'stop','error':取字段(结果,'error')}#写入停止错误槽
            自身._通知器.标脏()#刷新错误条
        return 结果#返回取消结果

    async def 重命名(自身,标题):#重命名会话
        """重命名：契约 session.rename 1:1。

        成功时用响应的 {title, seq} 按更高 seq 胜出规则结算 title 投影格。
        @param 标题 - 原始标题文本（宿主规范化接受）。
        @returns 重命名结果。
        """
        try:#调用宿主
            响应=await 自身._接口.sessions.rename({'sessionId':自身.会话标识,'title':标题})#请求重命名
            结果=取字段(响应,'result',响应)#取出结果
            if 取字段(结果,'ok'):#成功
                值=取字段(结果,'value') or {}#标题与 seq
                自身.投影.应用('title',取字段(值,'title'),取字段(值,'seq'))#立刻写入标题格
            return 结果#原样返回
        except Exception as 错误:#传输失败
            return 折叠传输错误(错误)#折成 RPC 错误

    async def 命令(自身,行):#执行斜杠命令
        """对本会话的智能体执行一行斜杠命令 — 纯准入语义。

        @param 行 - 完整命令行，含前导斜杠。
        @returns 准入结果，或传输失败时的错误分支。
        """
        结果=await 自身._远程.commands.execute(自身.会话标识,行)#交给命令 Remote
        if not 取字段(结果,'ok'):#失败
            return 结果#原样返回
        return {'ok':True,'value':{'matched':取字段(结果,'value') is not None}}#有值即匹配

    def 打开(自身):#打开窗口
        """首次打开：拉取尾页（幂等 — 飞行中/已打开返回已有 promise）。"""
        if 自身._打开态=='open':#已打开
            async def _已开():#已完成
                return#无事
            return _已开()#已解析
        if 自身._打开承诺 is not None:#飞行中
            return 自身._打开承诺#复用
        代际=自身._打开代际#启动代际
        async def _包装():#打开并清指针
            try:#执行打开
                await 自身._执行打开(代际)#真正打开
            finally:#收尾
                if 自身._打开承诺 is 承诺:#仍是自己才清
                    自身._打开承诺=None#清指针
        承诺=挂任务(_包装())#启动
        自身._打开承诺=承诺#记下飞行中的
        return 承诺#交给调用方

    async def 加载更早(自身):#加载更早历史
        """上翻：用窗口第一条 seq 作 beforeSeq 拉更早一页并前置。"""
        if 自身._打开态!='open' or not 自身._还有更多 or 自身._加载更早中:#未打开、没更多或已在加载
            return#无事
        自身._加载更早中=True#标记加载中
        自身._通知器.标脏()#刷新加载指示
        try:#拉更早页
            响应=await 自身._历史({'beforeSeq':自身._基序号,'maxMessages':页消息数})#按窗口头分页
            结果=取字段(响应,'result',响应)#取出结果
            if not 取字段(结果,'ok'):#保持窗口原样
                return#不覆盖 openError
            值=取字段(结果,'value') or {}#成功值
            更早=取字段(值,'events') or []#更早页事件
            if len(更早)==0:#空页
                自身._还有更多=取字段(值,'hasMore')#采纳宿主 hasMore
                自身._对话.前置([],自身._还有更多)#空前置仍更新 hasMore
                return#没有事件可拼
            尾=更早[-1]#更早页最后一条
            尾事件=取字段(尾,'event')#尾事件
            尾序号=取字段(尾事件,'seq')#尾 seq
            if 尾事件 is None or 尾序号 is None or 尾序号+1!=自身._基序号:#与当前窗口不连续
                print('[web-runtime] history page discontinuous: tail seq '+str(尾序号)+' vs baseSeq '+str(自身._基序号),file=sys.stderr)#记下不连续
                自身._还有更多=False#停止再翻
                自身._对话.前置([],False)#空前置并关掉 hasMore
                return#丢弃本页
            自身._事件们=[取字段(行,'event') for 行 in 更早]+自身._事件们#前置原始事件
            自身._视图们=[取字段(行,'view') for 行 in 更早]+自身._视图们#前置对齐视图
            头=更早[0] if len(更早)>0 else None#更早页第一条
            头序号=取字段(取字段(头,'event'),'seq') if 头 is not None else None#窗口头
            自身._基序号=头序号 if 头序号 is not None else 自身._基序号#窗口头前移
            自身._还有更多=取字段(值,'hasMore')#采纳宿主 hasMore
            自身._对话.前置([会话输入(行) for 行 in 更早],自身._还有更多)#前置组装器输入
        except Exception as 错误:#传输失败
            print('[web-runtime] loadOlder failed:',错误,file=sys.stderr)#记下失败
        finally:#无论成败
            自身._加载更早中=False#清加载标记
            自身._通知器.标脏()#刷新快照

    async def 重同步(自身):#重连重建窗口
        """重连重建：重置窗口并重跑 open；挂起等待基线重放。"""
        if 自身._打开态=='cold':#从未打开
            return#没有窗口可重建
        自身._打开代际+=1#作废飞行中的 doOpen
        自身._打开承诺=None#丢掉旧 promise
        自身._打开态='cold'#回到未打开
        自身._打开错误=None#清打开错误
        自身._事件们=[]#清空窗口事件
        自身._视图们=[]#清空窗口视图
        自身._基序号=0#窗口头归零
        自身._挂起.clear()#丢掉本地挂起等待
        自身._挂起修订+=1#作废挂起缓存
        自身._订阅末序号=None#丢掉订阅基线
        自身._直播缓冲=[]#丢掉直播缓冲
        自身._通知器.标脏()#刷新快照
        await 自身.打开()#按新代际重开

    def 订阅(自身,监听器):#订阅快照变更
        """uSES 订阅入口。

        @param 监听器 - 变更回调。
        @returns 取消订阅函数。
        """
        return 自身._通知器.订阅(监听器)#交给通知器

    def 取快照(自身):#读缓存快照
        """缓存的会话快照（无监听者时脏了才惰性重建）。"""
        自身._通知器.确保新鲜()#脏则先重建
        return 自身._快照缓存#稳定引用

    def 处理复用信封(自身,rpc标识,帧):#处理一条 mux 帧
        """mux 帧到达（分发开关）。

        @param rpc标识 - 帧信封 id（requested 帧的 respond 回填键）。
        @param 帧 - 已路由的帧。
        """
        种类=取字段(帧,'type')#帧类型
        if 种类=='session/event':#直播会话事件
            自身._接纳直播事件(取字段(帧,'event'),取字段(帧,'view'))#纳入窗口或缓冲
            return#已处理
        if 种类=='session/queue':#队列快照
            自身._队列镜像.替换(取字段(帧,'items') or [])#整集替换镜像
            自身._通知器.标脏()#刷新队列
            return#已处理
        if 种类=='session/subscribed':#新 mux 代际基线
            自身._订阅末序号=取字段(帧,'lastSeq')#记下订阅基线
            if 自身._队列镜像.重置():#重置镜像且有变化
                自身._通知器.标脏()#才刷新
            return#已处理
        if 种类=='approval/requested':#审批请求
            载荷=剥信封载荷(帧)#领域字段
            def 应答(消息):#client-response 载体
                return 自身._接口.respond(消息)#回填后交给载体
            自身._铸造(挂起等待('approval',rpc标识,自身.会话标识,载荷,应答))#铸造审批等待
            自身._通知器.标脏()#刷新挂起
            return#已处理
        if 种类=='approval/resolved':#审批已结算
            审批标识=取字段(帧,'approvalId')#审批 id
            for 项 in list(自身._挂起.values()):#每个挂起项
                if 项.种类=='approval' and 取字段(项.载荷,'approvalId')==审批标识:#匹配则结算
                    自身._结算(项)#结算
            自身._通知器.标脏()#刷新挂起
            return#已处理
        if 种类=='question/requested':#提问请求
            载荷=剥信封载荷(帧)#领域字段
            def 应答提问(消息):#client-response 载体
                return 自身._接口.respond(消息)#回填后交给载体
            自身._铸造(挂起等待('question',rpc标识,自身.会话标识,载荷,应答提问))#铸造提问等待
            自身._通知器.标脏()#刷新挂起
            return#已处理
        if 种类=='question/resolved':#提问已结算
            项=自身._挂起.get('q:'+str(取字段(帧,'questionRpcId')))#按提问 rpcId 查找
            if 项 is not None:#找到则结算
                自身._结算(项)#结算
            自身._通知器.标脏()#刷新挂起
            return#已处理
        return#未知帧忽略

    def 处理运行中(自身,运行中):#中继 running 位
        """宿主流上的 running 位中继（列表行与快照保持一致）。"""
        if 运行中 and 自身._空白位:#空白上首次开跑
            自身._空白位=False#降下空白位
            自身._通知器.标脏()#刷新快照
        if 运行中:#开跑则首次提示回合已可见
            自身._首次提示待回合=False#清待转
        if 自身._运行中==运行中:#没有变化
            return#无事
        自身._运行中=运行中#记下新状态
        自身._通知器.标脏()#刷新快照

    def 配置子智能体(自身,地址,父可用=False):#配置子智能体传输
        """安装或清除名册发现的传输地址。地址变化会经新历史路由重建已打开的窗口。"""
        旧=自身._地址#旧地址
        相同=(取字段(旧,'parentSessionId')==取字段(地址,'parentSessionId')#父相同
            and 取字段(旧,'childSessionId')==取字段(地址,'childSessionId')#子相同
            and 取字段(旧,'mode')==取字段(地址,'mode'))#模式相同
        自身._地址=地址#记下新地址
        自身._父可用=父可用#记下父可用性
        if not 相同 and 自身._打开态!='cold':#已打开且地址变则重建窗口
            挂任务(自身.重同步())#异步重建
        else:#否则只刷新快照
            自身._通知器.标脏()#刷新

    def 处理子智能体父可用(自身,可用):#中继父可用性
        """仅从名册刷新更新父可用性提示。"""
        if 自身._父可用==可用:#没有变化
            return#无事
        自身._父可用=可用#记下新提示
        自身._通知器.标脏()#刷新快照

    def 处理空白(自身,空白):#中继空白位
        """来自权威摘要源的 blank 位中继；单调：清过之后陈旧的 true 永不重新空白。"""
        if 空白==自身._空白位:#没有变化
            return#无事
        if 空白 and (自身._已尝试提示 or 自身._运行中):#本地已发送或在跑则拒回升
            return#拒绝
        自身._空白位=空白#采纳摘要位
        自身._通知器.标脏()#刷新快照

    def 处理已移除(自身):#标记已移除
        """host/session-removed 中继：给快照打标（实例存活 — 常驻实例规则）。"""
        自身._已移除=True#记下移除
        自身._通知器.标脏()#刷新快照

    def 处理智能体错误(自身,消息):#记下智能体错误
        """host/agent-error 中继：没有回合位置的直播失败的唯一出口。"""
        自身._最近智能体错误=消息#覆盖最近错误
        自身._通知器.标脏()#刷新快照

    def 销毁(自身):#常驻实例
        """空操作，因为会话实例保持常驻。"""
        return#拆除无操作

    def 重建会话注册表(自身):#重建会话注册表
        """低频 Definition 或视图注册表变更后重建当前窗口。"""
        自身._调度对话(自身._对话.重建注册表())#按发布节奏刷新

    def _铸造(自身,等待):#铸造挂起等待
        """requested 帧到达：等待以自有键进入挂起映射。"""
        自身._挂起[等待.键]=等待#按键放入
        自身._挂起修订+=1#作废挂起缓存

    def _结算(自身,等待):#结算挂起等待
        """权威 resolved 帧结算：标记，然后从挂起映射拿掉。"""
        等待.标已结清()#标记已结算
        自身._挂起.pop(等待.键,None)#从映射拿掉
        自身._挂起修订+=1#作废挂起缓存

    async def _执行打开(自身,代际):#执行一次打开
        """按代际打开；每次 await 后重检，过期趟丢掉所有写入。"""
        自身._打开态='loading'#进入加载
        自身._打开错误=None#清上次错误
        自身._通知器.标脏()#刷新打开态
        try:#拉尾页并安装
            响应=await 自身._历史({'maxMessages':页消息数})#拉尾页
            结果=取字段(响应,'result',响应)#取出结果
            if 代际!=自身._打开代际:#已被 resync 取代
                return#丢掉写入
            if not 取字段(结果,'ok'):#历史失败
                自身._打开态='error'#进入错误
                自身._打开错误=取字段(结果,'error')#记下错误
                return#不安装窗口
            值=取字段(结果,'value') or {}#成功值
            自身._安装窗口(取字段(值,'events') or [],取字段(值,'hasMore'),取字段(值,'projections'))#安装窗口并缝合缓冲
            尾序号=自身._窗口尾序号()#当前窗口尾 seq
            if 自身._订阅末序号 is not None and 尾序号 is not None and 自身._订阅末序号>尾序号:#订阅基线越过窗口尾
                响应=await 自身._历史({'maxMessages':页消息数})#再拉尾页
                结果=取字段(响应,'result',响应)#取出结果
                if 代际!=自身._打开代际:#打开途中被取代
                    return#丢掉
                if 取字段(结果,'ok'):#成功则重装
                    值=取字段(结果,'value') or {}#成功值
                    自身._安装窗口(取字段(值,'events') or [],取字段(值,'hasMore'),取字段(值,'projections'))#重装
            自身._打开态='open'#打开完成
        except Exception as 错误:#传输失败
            if 代际!=自身._打开代际:#已被取代则不写错误
                return#丢掉
            自身._打开态='error'#进入错误
            折叠=折叠传输错误(错误)#折成 RPC 错误
            自身._打开错误=None if 取字段(折叠,'ok') else 取字段(折叠,'error')#记下折叠错误
        finally:#无论成败
            if 代际==自身._打开代际:#仍是本代际才刷新
                自身._通知器.标脏()#刷新

    def _安装窗口(自身,条目们,还有更多,投影基线=None):#安装窗口
        """安装历史窗口并缝合 liveBuffer（seq 是唯一去重键）。"""
        自身._事件们=[取字段(行,'event') for 行 in 条目们]#换成原始事件
        自身._视图们=[取字段(行,'view') for 行 in 条目们]#换成对齐视图
        头=自身._事件们[0] if len(自身._事件们)>0 else None#窗口头
        自身._基序号=取字段(头,'seq') if 头 is not None else 0#窗口头 seq
        自身._还有更多=还有更多#更早页是否还有
        if any(取字段(事件,'type')=='turn/start' for 事件 in 自身._事件们):#已见回合
            自身._首次提示待回合=False#清首次待转
        自身._对话.替换窗口([会话输入(行) for 行 in 条目们],还有更多)#整窗替换组装器
        if 投影基线 is not None:#有基线
            自身.投影.播种(投影基线)#播种投影基线
        缓冲=自身._直播缓冲#取出缓冲
        自身._直播缓冲=[]#先清空，避免缝合再入缓冲
        for 项 in 缓冲:#按 seq 追加直播
            自身._追加直播(取字段(项,'event'),取字段(项,'view'))#追加
        自身._通知器.标脏()#刷新快照

    def _追加直播(自身,事件,视图=None):#追加一条直播事件
        """缝合与打开态直播路径共用的、带 seq 守卫的追加。"""
        尾序号=自身._窗口尾序号()#当前窗口尾
        if 尾序号 is not None and 取字段(事件,'seq')<=尾序号:#重放过叠
            return 'none'#丢弃
        自身._事件们.append(事件)#追加原始事件
        自身._视图们.append(视图)#追加对齐视图
        if 取字段(事件,'type')=='turn/start':#回合开始
            自身._首次提示待回合=False#清首次待转
        队列变了=自身._队列镜像.接纳持久(事件)#持久事件可能退役队列项
        发布=自身._对话.追加({'event':事件,'view':视图})#交给组装器
        return 'immediate' if 队列变了 else 发布#队列变则立刻刷新

    def _接纳直播事件(自身,事件,视图=None):#接纳直播事件
        """落地一条直播 session/event。"""
        if 自身._打开态=='loading' or 自身._缝合中:#打开或缝合中
            自身._直播缓冲.append({'event':事件,'view':视图})#改道进缓冲
            return#稍后缝合
        if 自身._打开态!='open':#cold/error
            return#不做窗口维护
        尾序号=自身._窗口尾序号()#当前窗口尾
        序号=取字段(事件,'seq')#本条 seq
        if 尾序号 is not None and 序号 is not None and 序号>尾序号+1:#seq 缺口
            自身._直播缓冲.append({'event':事件,'view':视图})#先缓冲本条
            挂任务(自身._修复缺口())#启动尾页重拉
            return#不追加出洞
        自身._调度对话(自身._追加直播(事件,视图))#追加并按节奏刷新

    def _调度对话(自身,发布):#按发布节奏刷新
        """把组装器节奏接到 Session 已有的微任务/RAF 通知器。"""
        if 发布=='immediate':#立刻脏
            自身._通知器.标脏()#立刻
        elif 发布=='animation-frame':#等到动画帧
            自身._通知器.标帧脏()#帧脏

    async def _修复缺口(自身):#修复 seq 缺口
        """轻量 resync：再拉尾页，经共享 installWindow 路径缝合 liveBuffer。"""
        if 自身._缝合中:#已在修复
            return#重入守卫
        自身._缝合中=True#标记缝合中
        代际=自身._打开代际#记下启动代际
        try:#再拉尾页
            响应=await 自身._历史({'maxMessages':页消息数})#拉尾页
            结果=取字段(响应,'result',响应)#取出结果
            if 取字段(结果,'ok') and 代际==自身._打开代际 and 自身._打开态=='open':#仍有效且仍打开
                值=取字段(结果,'value') or {}#成功值
                自身._安装窗口(取字段(值,'events') or [],取字段(值,'hasMore'),取字段(值,'projections'))#重装并缝合
        except Exception as 错误:#传输失败
            print('[web-runtime] gap repair failed:',错误,file=sys.stderr)#记下失败
        finally:#无论成败
            自身._缝合中=False#清缝合标记

    def _窗口尾序号(自身):#窗口尾 seq
        """当前窗口最后一条事件的 seq；空窗则 None。"""
        if len(自身._事件们)==0:#空窗
            return None#无尾
        return 取字段(自身._事件们[-1],'seq')#尾 seq

    def _建快照(自身):#编出会话快照
        """装配 ConversationSnapshot 字典（协议键保持英文）。"""
        if 自身._挂起缓存 is None or 取字段(自身._挂起缓存,'rev')!=自身._挂起修订:#挂起缓存过期
            自身._挂起缓存={'rev':自身._挂起修订,'value':list(自身._挂起.values())}#物化挂起数组
        聊天=自身._对话.快照('chat')#聊天切片
        if 聊天 is None:#缺则空
            聊天=空聊天快照#空聊天
        遗留=取字段(聊天,'legacy') or {}#旧节点投影
        挂起们=取字段(自身._挂起缓存,'value') or []#挂起交互
        有内容=(有可见会话内容(聊天)#可见非命令内容
            or ((not 自身._空白位) and (not 自身._首次提示待回合))#已非空白且首次回合可见
            or 自身._运行中#或正在跑
            or len(挂起们)>0)#或有挂起交互
        if 自身._地址 is None:#无子智能体地址
            子智能体=None#普通会话
        else:#带子智能体信息
            子智能体={'address':自身._地址,'parentAvailable':自身._父可用}#子智能体
        return {#会话快照
            'sessionId':自身.会话标识,#会话身份
            'views':自身._对话,#组装器本身作视图源
            'chat':聊天,#聊天切片
            'nodes':取字段(遗留,'nodes'),#旧节点
            'turnTimings':取字段(遗留,'turnTimings'),#回合计时
            'turnEnds':取字段(遗留,'turnEnds'),#回合结束
            'partial':取字段(遗留,'partial'),#部分输出
            'runningCalls':取字段(遗留,'runningCalls'),#进行中的调用
            'pending':挂起们,#挂起交互
            'queue':自身._队列镜像.快照(),#队列快照
            'running':自身._运行中,#是否在跑
            'subagent':子智能体,#子智能体或 None
            'composerPhase':推导阶段(有内容,自身._已尝试提示),#作曲阶段
            'removed':自身._已移除,#是否已移除
            'openState':自身._打开态,#打开态
            'openError':自身._打开错误,#打开错误
            'hasMore':自身._还有更多,#更早页是否还有
            'loadingOlder':自身._加载更早中,#是否正在上翻
            'promptError':自身._提示错误,#发送/停止错误
            'blank':自身._空白位,#是否空白
            'lastAgentError':自身._最近智能体错误,#最近智能体错误
        }#结束返回

    def _历史(自身,载荷):#拉历史
        """按已存浏览器事实选择普通或寻址历史传输。"""
        if 自身._地址 is None:#无子智能体地址
            请求={'sessionId':自身.会话标识}#普通历史
            请求.update(载荷)#分页参数
            return 自身._接口.sessions.history(请求)#普通历史
        请求=dict(自身._地址) if isinstance(自身._地址,dict) else {#寻址历史
            'parentSessionId':取字段(自身._地址,'parentSessionId'),#父
            'childSessionId':取字段(自身._地址,'childSessionId'),#子
            'mode':取字段(自身._地址,'mode'),#模式
        }#结束地址
        请求.update(载荷)#分页参数
        return 自身._接口.subagents.history(请求)#寻址历史
