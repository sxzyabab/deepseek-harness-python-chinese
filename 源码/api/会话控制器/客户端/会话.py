"""客户端会话对象：事件窗口、生命周期与可观察快照。

对齐上游 `session-controller/src/client/sessions/session.ts`。公开面仅中文名。
React 绑定留在本数据层之外。
"""
import base64#附件解码
import threading#帧调度
import time#挂钟
import uuid#请求 id
from ..远程错误与并发 import 远程错误#失败
from .传输 import 会话事件流#事件流
from .约定.事件 import 可变会话事件源#事件源
from .通知器 import 通知器#通知
from .投影存储 import 投影值存储#投影
from .时区 import 解析客户端时区#时区
from .队列镜像 import 会话队列镜像#队列
from .助手流 import 客户端助手流#助手流

__all__=['页消息数','跳转页消息数','会话']#仅中文公开名

页消息数=50#尾页消息数
跳转页消息数=200#跳转页消息数

def _是否远程失败(错误):
    """结构识别远程失败。"""
    if isinstance(错误,远程错误):#本包
        return True#是
    if isinstance(错误,dict) and 'code' in 错误 and 'message' in 错误:#信封
        return True#是
    return getattr(错误,'isDSHRemoteError',False) is True#标记

def _调度帧(回调):
    """下一宏任务运行回调。"""
    定时器=threading.Timer(0,回调)#宏任务
    定时器.daemon=True#守护
    定时器.start()#启

def _内容附件引用(内容):
    """内容块中的附件引用。"""
    if not isinstance(内容,list):#非列表
        return []#空
    引用列表=[]#结果
    for 块 in 内容:#逐块
        if not isinstance(块,dict):#非对象
            continue#跳过
        if 块.get('type') in ('image','file') and isinstance(块.get('attachment'),dict):#附件
            引用列表.append(块['attachment'])#收下
    return 引用列表#引用

def _调用远程(方法,*参数,信号=None):
    """调用可能返回信封或抛错的远程方法，归一为 {ok,value|error}。"""
    try:
        if 信号 is not None:#带信号
            原始=方法(*参数,信号)#调用
        else:#无信号
            try:
                原始=方法(*参数)#尝试位置
            except TypeError:#可能不收信号形参以外
                原始=方法(*参数)#再试
        if isinstance(原始,dict) and 'ok' in 原始:#已是信封
            return 原始#原样
        return {'ok':True,'value':原始}#包装
    except BaseException as 错误:
        if _是否远程失败(错误):#远程失败
            return {'ok':False,'error':错误}#失败
        raise#其它

class 会话:
    """拥有会话的事件窗口、生命周期状态与可观察快照。"""

    def __init__(自身,会话标识,远程,选项=None):
        """构造。选项可含 address／parentAvailable／onEngaged／projections。"""
        if 选项 is None:#缺省
            选项={}#空
        自身.sessionId=会话标识#身份
        自身._远程=远程#远程
        自身._选项=选项#选项
        自身.projections=选项['projections'] if 'projections' in 选项 and 选项['projections'] is not None else 投影值存储()#投影
        自身._地址=选项['address'] if 'address' in 选项 else None#子地址
        自身._父可用=选项['parentAvailable'] if 'parentAvailable' in 选项 else None#父可用性
        自身._基序号=0#窗口首序号
        自身._还有更多=False#还有更早
        自身._打开状态='cold'#打开状态
        自身._打开错误=None#打开错误
        自身._打开承诺=None#飞行中打开
        自身._打开代=0#打开代
        自身._加载更早=False#加载更早
        自身._跳转目标=None#跳转目标
        自身._跳转承诺=None#跳转承诺
        自身._队列镜像=会话队列镜像()#队列
        自身._助手流=客户端助手流()#助手流
        自身._运行中=False#运行
        自身._提示已尝试=False#提示尝试
        自身._等待首轮=False#等待首轮
        自身._空白=True#空白
        自身._已移除=False#移除
        自身._提示错误=None#提示错误
        自身._最近智能体错误=None#智能体错误
        自身._待定提交=()#待定提交
        自身._提交结算={}#requestId → 结算
        自身._事件流=None#事件流
        自身.eventSource=可变会话事件源()#事件源
        自身._作用域上下文=None#actx
        自身._通知器=通知器(自身._重建快照)#通知
        自身._快照=自身._构建快照()#初始

    def 绑定作用域(自身,作用域上下文):
        """绑定 ClientSessions 铸造的 Agent 作用域上下文（单次）。"""
        if 自身._作用域上下文 is not None:#已绑
            raise RuntimeError('session '+str(自身.sessionId)+' already has a bound scope')#错误
        自身._作用域上下文=作用域上下文#写入

    def 解绑作用域(自身):
        """修剪时释放已绑定作用域。"""
        自身._作用域上下文=None#清空

    def beginSubmission(自身,输入):
        """登记本地提交回声。"""
        请求标识=str(uuid.uuid4())#铸造
        if 自身._运行中:#运行中
            放置='steering' if 输入.get('mode')=='steer' else 'queued'#放置
        else:#空闲
            放置='transcript'#转录
        自身._待定提交=自身._待定提交+({
            'requestId':请求标识,
            'placement':放置,
            'time':int(time.time()*1000),
            'text':输入['text'],
            'attachments':list(输入['attachments']) if 'attachments' in 输入 else [],
        },)#追加
        自身._提交结算[请求标识]={'onRetire':输入['onRetire'] if 'onRetire' in 输入 else None,'retiring':False}#结算
        自身._提示已尝试=True#标记
        自身._通知器.标脏()#脏
        return {'requestId':请求标识,'abandon':lambda:自身._失败退役提交(请求标识)}#句柄

    def prompt(自身,内容,模式,信号=None,请求标识=None):
        """发送提示。"""
        自身._提示错误=None#清
        自身._最近智能体错误=None#清
        自身._提示已尝试=True#尝试
        if 自身._空白:#空白
            自身._等待首轮=True#等待
        自身._通知器.标脏()#脏
        会话面=自身._远程.session if hasattr(自身._远程,'session') else 自身._远程['session']#session
        if 自身._地址 is None:#普通
            实际请求标识=请求标识 if 请求标识 is not None else str(uuid.uuid4())#id
            结果=_调用远程(会话面.prompt,{
                'requestId':实际请求标识,
                'sessionId':自身.sessionId,
                'mode':模式,
                'content':内容,
                'clientTimeZone':解析客户端时区(),
            },信号=信号)#提示
        elif any(isinstance(块,dict) and 块.get('type')=='file' for 块 in 内容):#子智能体拒文件
            结果={'ok':False,'error':远程错误('subagent/attachment-invalid','subagent continuation does not accept files',{'reason':'SUBAGENT_FILE_UNSUPPORTED'})}#失败
        else:#子智能体
            子面=自身._远程.subagents if hasattr(自身._远程,'subagents') else 自身._远程['subagents']#subagents
            路由=_调用远程(子面.prompt,{
                'requestId':str(uuid.uuid4()),
                'parentSessionId':自身._地址['parentSessionId'],
                'childSessionId':自身._地址['childSessionId'],
                'mode':'continuable',
                'delivery':模式,
                'content':内容,
                'clientTimeZone':解析客户端时区(),
            },信号=信号)#提示
            结果={'ok':True,'value':{'accepted':True}} if 路由.get('ok') else 路由#归一
        if not 结果.get('ok'):#失败
            if 请求标识 is not None:#有回声
                自身._失败退役提交(请求标识)#退役
            自身._提示错误={'op':'send','error':结果['error']}#错误
            自身._通知器.标脏()#脏
            return 结果#失败
        if 自身._空白:#接受翻转
            自身._空白=False#非空白
            if 'onEngaged' in 自身._选项 and 自身._选项['onEngaged'] is not None:#回调
                自身._选项['onEngaged'](自身)#参与
            自身._通知器.标脏()#脏
        return 结果#成功

    def readAttachment(自身,附件标识):
        """读持久图片为字节。"""
        会话面=自身._远程.session if hasattr(自身._远程,'session') else 自身._远程['session']#session
        结果=_调用远程(会话面.attachment,{'sessionId':自身.sessionId,'attachmentId':附件标识})#读
        if not 结果.get('ok'):#失败
            return 结果#原样
        值=结果['value']#值
        二进制=base64.b64decode(值['data'])#解码
        return {'ok':True,'value':{'attachment':值['attachment'],'data':二进制}}#结果

    def updateQueue(自身,项标识,动作):
        """更新队列。"""
        会话面=自身._远程.session if hasattr(自身._远程,'session') else 自身._远程['session']#session
        return _调用远程(会话面.updateQueue,{'sessionId':自身.sessionId,'itemId':项标识,'action':动作})#更新

    def cancel(自身):
        """取消活跃回合。"""
        if 自身._地址 is not None:#子智能体
            子面=自身._远程.subagents if hasattr(自身._远程,'subagents') else 自身._远程['subagents']#subagents
            结果=_调用远程(子面.interruptByParent,自身._地址['childSessionId'],自身._地址['parentSessionId'],'continuable')#中断
        else:#普通
            会话面=自身._远程.session if hasattr(自身._远程,'session') else 自身._远程['session']#session
            结果=_调用远程(会话面.cancel,{'sessionId':自身.sessionId})#取消
        if not 结果.get('ok'):#失败
            自身._提示错误={'op':'stop','error':结果['error']}#错误
            自身._通知器.标脏()#脏
        return 结果#结果

    def rename(自身,标题):
        """重命名并乐观安装 title 投影。"""
        会话面=自身._远程.session if hasattr(自身._远程,'session') else 自身._远程['session']#session
        结果=_调用远程(会话面.rename,{'sessionId':自身.sessionId,'title':标题})#重命名
        if not 结果.get('ok'):#失败
            return 结果#原样
        值=结果['value']#值
        自身.projections.应用('title',值['title'],值['seq'])#乐观
        return {'ok':True,'value':{'title':值['title'],'seq':值['seq']}}#结果

    def command(自身,行):
        """斜杠命令。"""
        命令面=自身._远程.commands if hasattr(自身._远程,'commands') else 自身._远程['commands']#commands
        结果=_调用远程(命令面.execute,自身.sessionId,行,[])#执行
        if not 结果.get('ok'):#失败
            return 结果#原样
        return {'ok':True,'value':{'matched':结果['value'] is not None}}#匹配

    def open(自身):
        """首次打开：拉尾页（幂等）。"""
        if 自身._打开状态=='open':#已开
            return#空
        if 自身._打开承诺 is not None:#飞行中
            自身._打开承诺.等待()#等
            return#空
        代=自身._打开代#代
        任务=_操作任务()#承诺
        自身._打开承诺=任务#登记
        def 后台打开():
            """执行打开。"""
            try:
                自身._执行打开(代)#打开
                任务.兑现(None)#成功
            except BaseException as 错误:
                任务.拒绝(错误)#失败
            finally:
                if 自身._打开承诺 is 任务:#仍是本承诺
                    自身._打开承诺=None#清空
        threading.Thread(target=后台打开,daemon=True).start()#后台
        任务.等待()#同步等待（对齐阻塞切片）

    def loadOlder(自身):
        """向上翻页。"""
        if 自身._打开状态!='open' or (not 自身._还有更多) or 自身._加载更早:#不可
            return#空
        流=自身._事件流#流
        if 流 is None:#无
            return#空
        自身._加载更早=True#忙
        自身._通知器.标脏()#脏
        try:
            流.prepend({'beforeSeq':自身._基序号,'maxMessages':页消息数})#前置
        except BaseException as 错误:
            if not _是否远程失败(错误):#非远程
                print('[session-controller] loadOlder failed:',错误)#日志
        finally:
            自身._加载更早=False#清
            自身._通知器.标脏()#脏

    def loadThrough(自身,序号):
        """跳转加载至序号。"""
        if 自身._打开状态!='open' or (not 自身._还有更多) or 自身._基序号<=序号:#已覆盖
            return#空
        if 自身._跳转承诺 is not None:#重定向
            自身._跳转目标=min(自身._跳转目标 if 自身._跳转目标 is not None else 序号,序号)#最低
            自身._跳转承诺.等待()#等
            return#空
        if 自身._加载更早:#单页占用
            return#空
        自身._跳转目标=序号#目标
        自身._加载更早=True#忙
        自身._通知器.标脏()#脏
        代=自身._打开代#代
        任务=_操作任务()#承诺
        自身._跳转承诺=任务#登记
        def 后台跳转():
            """跳转循环。"""
            try:
                while 自身._还有更多 and 自身._跳转目标 is not None and 自身._基序号>自身._跳转目标:#未覆盖
                    if 代!=自身._打开代:#陈旧
                        return#停
                    流=自身._事件流#流
                    if 流 is None:#无
                        return#停
                    先前=自身._基序号#前
                    流.prepend({'beforeSeq':自身._基序号,'maxMessages':跳转页消息数})#前置
                    if 自身._基序号>=先前:#无进展
                        return#停
            except BaseException as 错误:
                if not _是否远程失败(错误):#非远程
                    print('[session-controller] loadThrough failed:',错误)#日志
            finally:
                自身._跳转目标=None#清
                自身._跳转承诺=None#清
                自身._加载更早=False#清
                自身._通知器.标脏()#脏
                任务.兑现(None)#完成
        threading.Thread(target=后台跳转,daemon=True).start()#后台
        任务.等待()#等

    def resync(自身):
        """地址替换后重建已打开历史源。"""
        if 自身._打开状态=='cold':#从未打开
            return#空
        自身._打开代+=1#升代
        流=自身._事件流#旧流
        自身._事件流=None#清空
        if 流 is not None:#有
            流.拆除()#拆
        自身._打开承诺=None#清
        自身._打开状态='cold'#冷
        自身._打开错误=None#清
        自身._基序号=0#重置
        自身._通知器.标脏()#脏
        自身.open()#重开

    def 订阅(自身,监听者):
        """uSES 订阅。"""
        return 自身._通知器.订阅(监听者)#取消函数

    def getSnapshot(自身):
        """缓存会话快照。"""
        自身._通知器.确保新鲜()#新鲜
        return 自身._快照#快照

    def replaceControl(自身,队列项):
        """用流基线替换瞬态控制值。"""
        自身._队列镜像.替换(队列项)#替换
        自身._观察提交队列(队列项)#观察
        自身._通知器.标脏()#脏

    def handleControlFrame(自身,帧):
        """应用寻址到本会话的队列替换。"""
        自身._队列镜像.替换(帧['items'])#替换
        自身._观察提交队列(帧['items'])#观察
        自身._通知器.标脏()#脏

    def handleRunning(自身,运行中):
        """运行位中继。"""
        if 运行中 and 自身._空白:#首条落地
            自身._空白=False#非空白
            自身._通知器.标脏()#脏
        if 运行中:#运行
            自身._等待首轮=False#清
        if 自身._运行中==运行中:#无变
            return#空
        自身._运行中=运行中#写入
        自身._通知器.标脏()#脏

    def configureSubagent(自身,地址,父可用=None):
        """安装或清除目录发现的传输地址。"""
        相同=(
            (自身._地址 is None and 地址 is None)
            or (
                isinstance(自身._地址,dict) and isinstance(地址,dict)
                and 自身._地址.get('parentSessionId')==地址.get('parentSessionId')
                and 自身._地址.get('childSessionId')==地址.get('childSessionId')
                and 自身._地址.get('mode')==地址.get('mode')
            )
        )#同址
        自身._地址=地址#写入
        自身._父可用=父可用#写入
        if (not 相同) and 自身._打开状态!='cold':#需重同步
            自身.resync()#重同步
        else:#仅脏
            自身._通知器.标脏()#脏

    def handleSubagentParentAvailable(自身,可用):
        """更新父可用性提示。"""
        if 自身._父可用==可用:#无变
            return#空
        自身._父可用=可用#写入
        自身._通知器.标脏()#脏

    def handleBlank(自身,空白):
        """空白位中继（单调下降）。"""
        if 空白==自身._空白:#无变
            return#空
        if 空白 and (自身._提示已尝试 or 自身._运行中):#不得回升
            return#空
        自身._空白=空白#写入
        自身._通知器.标脏()#脏

    def handleRemoved(自身):
        """标记移除。"""
        自身._已移除=True#标记
        自身._通知器.标脏()#脏

    def handleAgentError(自身,消息):
        """存活失败出口。"""
        自身._最近智能体错误=消息#写入
        自身._通知器.标脏()#脏

    def dispose(自身):
        """停止存活 Remote 源。"""
        for 请求标识 in list(自身._提交结算.keys()):#未结算
            自身._失败退役提交(请求标识)#失败退役
        自身._打开代+=1#升代
        流=自身._事件流#流
        自身._事件流=None#清
        if 流 is not None:#有
            流.拆除()#拆

    def _执行打开(自身,代):
        """执行打开。"""
        自身._打开状态='loading'#加载
        自身._打开错误=None#清
        自身._通知器.标脏()#脏
        箱={'流':None}#闭包箱
        def 发布(变更):
            """接受变更。"""
            if 代!=自身._打开代 or 自身._事件流 is not 箱['流']:#陈旧
                return#忽略
            自身._接受事件变更(变更)#接受
        def 失败(错误):
            """流失败。"""
            自身._事件流失败(箱['流'],代,错误)#失败
        流=会话事件流(自身._远程,自身._会话地址(),{'publish':发布,'failed':失败})#流
        箱['流']=流#写入箱
        自身._事件流=流#登记
        try:
            流.open({'maxMessages':页消息数})#打开
            if 代!=自身._打开代 or 自身._事件流 is not 流:#陈旧
                return#停
            自身._打开状态='open'#开
        except BaseException as 错误:
            if 代!=自身._打开代 or 自身._事件流 is not 流:#陈旧
                return#停
            if not _是否远程失败(错误):#非远程
                raise#抛
            自身._事件流=None#清
            自身._打开状态='error'#错
            自身._打开错误=错误#记下
        finally:
            if 代==自身._打开代:#本代
                自身._通知器.标脏()#脏

    def _接受事件变更(自身,变更):
        """应用连续日志更新。"""
        类型=变更['type']#类型
        if 类型=='replace':#整窗
            投影=变更['page']['projections'] if isinstance(变更.get('page'),dict) and 'projections' in 变更['page'] else None#投影
            助手=变更['page']['assistantStream'] if isinstance(变更.get('page'),dict) and 'assistantStream' in 变更['page'] else None#助手
            自身._安装窗口(变更['entries'],变更['hasMore'],投影,助手)#安装
            return#结束
        if 类型=='prepend':#前置
            自身._前置窗口(变更['entries'],变更['hasMore'])#前置
            return#结束
        if 类型=='append':#追加
            自身._发布助手条目(自身._助手流.接受耐久(变更['entry']))#发布
            return#结束
        if 类型=='assistant-stream':#助手流
            自身._发布助手条目(自身._助手流.接受帧(变更['frame']))#发布

    def _安装窗口(自身,条目列表,还有更多,投影=None,助手流=None):
        """替换完整连续窗口。"""
        可见=自身._助手流.替换(条目列表,助手流)#可见
        自身._基序号=条目列表[0]['event']['seq'] if len(条目列表)>0 else 0#首序号
        自身._还有更多=还有更多#更多
        if any(条目.get('event',{}).get('type')=='turn/start' for 条目 in 可见):#有回合
            自身._等待首轮=False#清
        if 投影 is not None:#播种
            自身.projections.播种(投影)#播种
        自身.eventSource.替换(可见,还有更多)#替换
        for 条目 in 可见:#观察提交
            自身._观察提交事件(条目['event'])#观察
        自身._通知器.标脏()#脏

    def _发布助手条目(自身,决策):
        """发布助手流决策。"""
        if 决策 is None:#无
            return#空
        类型=决策['type']#类型
        if 类型=='rebaseline':#重基线
            流=自身._事件流#流
            def 重启():
                """重启流。"""
                if 流 is not None and 自身._事件流 is 流 and hasattr(流,'restart'):#可重启
                    流.restart()#重启
            _调度帧(重启)#调度
            return#结束
        if 类型=='settlement':#结算
            自身.eventSource.结算助手(决策['attemptId'],决策['entry'] if 'entry' in 决策 else None)#结算
            if 'entry' in 决策:#有条目
                自身._观察提交事件(决策['entry']['event'])#观察
            自身._通知器.标脏()#脏
            return#结束
        if 类型=='abandonment':#放弃
            自身.eventSource.结算助手(决策['attemptId'])#结算
            自身._通知器.标脏()#脏
            return#结束
        if 类型=='publish' and 自身._追加存活(决策['entry']):#发布
            自身._通知器.标脏()#脏
        elif 类型=='transient':#瞬态
            自身.eventSource.追加(决策['entry'])#追加
            自身._通知器.标脏()#脏

    def _前置窗口(自身,条目列表,还有更多):
        """前置历史页。"""
        if len(条目列表)>0:#有
            自身._基序号=条目列表[0]['event']['seq']#首序号
        自身._还有更多=还有更多#更多
        自身.eventSource.前置(条目列表,还有更多)#前置

    def _追加存活(自身,条目):
        """追加存活事件。返回是否需标脏。"""
        事件=条目['event']#事件
        曾等待=自身._等待首轮#曾
        if 事件.get('type')=='turn/start':#回合开始
            自身._等待首轮=False#清
        队列变=自身._队列镜像.接受耐久(事件)#队列
        自身.eventSource.追加(条目)#追加
        自身._观察提交事件(事件)#观察
        return 队列变 or 曾等待!=自身._等待首轮#脏否

    def _观察提交事件(自身,事件):
        """持久 user/message 时退役回声。"""
        if len(自身._提交结算)==0 or 事件.get('type')!='user/message':#无关
            return#空
        数据=事件['data'] if isinstance(事件.get('data'),dict) else None#载荷
        源=数据['source'] if isinstance(数据,dict) and isinstance(数据.get('source'),dict) else None#来源
        if 源 is None or 源.get('kind')!='user' or not isinstance(源.get('rpcId'),str):#非用户 rpc
            return#空
        自身._调度已观察退役(源['rpcId'],_内容附件引用(数据.get('content') if 数据 else None))#调度

    def _观察提交队列(自身,项列表):
        """队列出现时退役回声。"""
        if len(自身._提交结算)==0:#无
            return#空
        for 项 in 项列表:#逐项
            if 'rpcId' in 项 and 项['rpcId'] is not None:#有 rpc
                内容=项['message']['content'] if isinstance(项.get('message'),dict) else None#内容
                自身._调度已观察退役(项['rpcId'],_内容附件引用(内容))#调度

    def _调度已观察退役(自身,请求标识,附件列表):
        """闩住并延后完成。"""
        结算=自身._提交结算[请求标识] if 请求标识 in 自身._提交结算 else None#结算
        if 结算 is None or 结算['retiring']:#无或已闩
            return#空
        结算['retiring']=True#闩
        _调度帧(lambda:自身._完成提交(请求标识,{'reason':'observed','attachments':附件列表}))#帧后

    def _失败退役提交(自身,请求标识):
        """立即失败退役。"""
        结算=自身._提交结算[请求标识] if 请求标识 in 自身._提交结算 else None#结算
        if 结算 is None or 结算['retiring']:#无或已闩
            return#空
        结算['retiring']=True#闩
        自身._完成提交(请求标识,{'reason':'failed'})#完成

    def _完成提交(自身,请求标识,退役):
        """单一移除点。"""
        结算=自身._提交结算.pop(请求标识,None)#取出
        if 结算 is None:#无
            return#空
        自身._待定提交=tuple(回声 for 回声 in 自身._待定提交 if 回声['requestId']!=请求标识)#过滤
        自身._通知器.标脏()#脏
        if 结算['onRetire'] is not None:#回调
            结算['onRetire'](退役)#通知所有者

    def _事件流失败(自身,流,代,错误):
        """终端后台失败。"""
        if 代!=自身._打开代 or 自身._事件流 is not 流:#陈旧
            return#忽略
        if not _是否远程失败(错误):#非远程
            raise 错误#抛
        自身._打开代+=1#升代
        自身._事件流=None#清
        自身._打开承诺=None#清
        自身._打开状态='error'#错
        自身._打开错误=错误#记下
        流.拆除()#拆
        自身._通知器.标脏()#脏

    def _重建快照(自身):
        """通知器重建入口。"""
        自身._快照=自身._构建快照()#重建

    def _构建快照(自身):
        """构造快照 dict。"""
        if 自身._地址 is None:#普通
            子=None#无
        else:#子智能体
            子={'address':自身._地址}#地址
            if 自身._父可用 is not None:#有提示
                子['parentAvailable']=自身._父可用#写入
        return {
            'sessionId':自身.sessionId,
            'queue':自身._队列镜像.快照(),
            'pendingSubmissions':自身._待定提交,
            'running':自身._运行中,
            'subagent':子,
            'removed':自身._已移除,
            'openState':自身._打开状态,
            'openError':自身._打开错误,
            'hasMore':自身._还有更多,
            'loadingOlder':自身._加载更早,
            'promptError':自身._提示错误,
            'blank':自身._空白,
            'lastAgentError':自身._最近智能体错误,
            'promptAttempted':自身._提示已尝试,
            'awaitingFirstTurn':自身._等待首轮,
        }#快照

    def _会话地址(自身):
        """传输地址。"""
        if 自身._地址 is None:#普通
            return {'kind':'session','sessionId':自身.sessionId}#会话
        地址=dict(自身._地址)#拷
        地址['kind']='subagent'#种类
        return 地址#子智能体

class _操作任务:
    """简易同步任务。"""
    def __init__(自身):
        """未决。"""
        自身._事件=threading.Event()#事件
        自身._值=None#值
        自身._错误=None#错误
    def 兑现(自身,值=None):
        """成功。"""
        自身._值=值#值
        自身._事件.set()#唤醒
    def 拒绝(自身,错误):
        """失败。"""
        自身._错误=错误#错误
        自身._事件.set()#唤醒
    def 等待(自身):
        """阻塞。"""
        自身._事件.wait()#等
        if 自身._错误 is not None:#失败
            raise 自身._错误#抛
        return 自身._值#值
