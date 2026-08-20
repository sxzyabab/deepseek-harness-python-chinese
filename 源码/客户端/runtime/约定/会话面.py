"""对外的会话行为面、投影面与完整面。

对齐上游 `runtime/src/client/contract/session.ts`。公开面仅中文名。
功能包从不看见具体 Session 类：组件经 `useSession`（可观察快照那一半）
读会话状态，编排代码调用下面的行为动词 — 别无其它。
加宽本面就是显式加宽功能对一条会话能做什么（以及每个测试夹具必须桩掉什么）；
运行时内部入口（历史暂存、线帧派发）留在类上，外面看不见。

依赖未迁：附件品牌 id / 图像引用（dsh-attachment）、完整 RpcResult / RemoteResult 图、
ConversationSnapshot（会话快照叶）；本叶以鸭式 object / dict 表达上述类型能承载的入参与返回。
存储叶尚未导出 ObservableSnapshot Protocol；本叶在完整面上钉交叉，不另造冲突名。
"""
from typing import Protocol,Literal#协议与字面量

__all__=[#仅中文公开名
    '投影面方法',
    '会话面方法',
    '会话完整面方法',
    '投影面',
    '会话行为面',
    '会话完整面',
]#公开面结束

#------------------------------ 方法名表（稳定动词清单） ------------------------------

投影面方法=(#ProjectionsFace
    'faceOf',#按键取面
)#投影方法结束

会话面方法=(#ISession 行为动词
    'sessionId',#会话 id
    'projections',#投影面
    'prompt',#发提示
    'readAttachment',#读附件
    'updateQueue',#更新队列
    'cancel',#取消回合
    'rename',#重命名
    'loadOlder',#加载更旧
    'command',#执行命令
)#会话方法结束

会话完整面方法=会话面方法+(#SessionFace = ISession & ObservableSnapshot
    'getSnapshot',#读会话快照
    'subscribe',#订阅快照替换
)#完整面方法结束

#------------------------------ Protocol（对齐接口体） ------------------------------

class 投影面(Protocol):#ProjectionsFace
    """按键寻址的投影读面（useProjection 解析路径；见 ProjectionValueStore）。"""

    def faceOf(自身,键):#按键取面
        """一个投影键的身份稳定裸可观察源。

        缺席是 `undefined` 快照，从不是缺失的面。

        @param 键 - 投影键。
        @returns 该键的值面（可观察快照）。
        """
        ...#协议槽

class 会话行为面(Protocol):#ISession
    """身份加上功能可以对一条会话调用的行为动词。"""

    @property
    def sessionId(自身):#会话宿主身份
        """会话的宿主身份（智能体 id — 同一轴）。"""
        ...#协议槽

    @property
    def projections(自身):#投影读面
        """宿主按键算出的投影值（useProjection 座位）。"""
        ...#协议槽

    async def prompt(自身,内容,模式):#发提示
        """向会话发送一条提示。

        @param 内容 - 文本加上浏览器拥有的临时图像上传（PromptContentPart 序列）。
        @param 模式 - 'queue' 追加一个回合；'steer' 打断正在跑的那个。
        @returns 接受，或业务错误（也会镜像进 snapshot.promptError）。
        """
        ...#协议槽

    async def readAttachment(自身,附件id):#读附件
        """解析本会话引用的一张持久化图像。

        @param 附件id - 折叠后的会话日志里的不透明 id。
        @returns 已认证引用与解码后的字节。
        """
        ...#协议槽

    async def updateQueue(自身,项id,动作):#更新队列
        """对仍挂起的队列出现项做一次编辑、删除或严格转向。

        @param 项id - 智能体拥有的收件箱出现项身份。
        @param 动作 - 请求的队列操作。
        @returns 接受，或业务/传输错误。
        """
        ...#协议槽

    async def cancel(自身):#取消回合
        """取消正在跑的回合。

        挂起的排队工作仍在，宿主到达取消静止后按 FIFO 恢复。
        @returns 接受，或业务错误。
        """
        ...#协议槽

    async def rename(自身,标题):#重命名
        """重命名本会话（显式用户标题；钉住它不再自动再生成）。

        @param 标题 - 原始标题文本（宿主归一接受）。
        @returns 归一后接受的标题及其事件 seq，或业务错误。
        """
        ...#协议槽

    async def loadOlder(自身):#加载更旧
        """把历史窗口向后延伸（更旧消息分页）。

        @returns 完成；失败落在 snapshot.openState/loadingOlder。
        """
        ...#协议槽

    async def command(自身,行):#执行命令
        """对本会话的智能体执行一条斜杠命令行 — 纯准入语义。

        宿主执行器持久化记录生命周期。
        @param 行 - 完整命令行，含前导斜杠。
        @returns 准入结果，或 Remote 面的错误分支。
        """
        ...#协议槽

class 会话完整面(会话行为面,Protocol):#SessionFace = ISession & ObservableSnapshot<ConversationSnapshot>
    """完整对外面：行为动词加上会话读取侧（`useSession` 钩源）。

    这是 `SessionBinding.session` 和 provide 通道携带的类型。
    Python 以 Protocol 继承行为面并显式钉 getSnapshot/subscribe，表达上游 `& ObservableSnapshot` 交叉。
    """

    def getSnapshot(自身):#ObservableSnapshot.getSnapshot
        """当前会话快照（ConversationSnapshot；下次变更前引用稳定）。

        @returns 会话快照。
        """
        ...#协议槽

    def subscribe(自身,监听器):#ObservableSnapshot.subscribe
        """观察快照替换。

        @param 监听器 - 每次快照变更后调用。
        @returns 去掉本监听器的 disposer。
        """
        ...#协议槽

# 提示模式字面量（prompt 第二参）
提示模式=Literal['queue','steer']#queue 追加；steer 打断
