from .外壳 import 会话输入壳#会话输入壳
from ..服务 import 对话错误#发送失败

__all__=['输入枢纽']#仅中文公开名

class 即时任务:#已兑现的汇结局
    """Promise.resolve 的同步任务面，只留等待。"""
    def __init__(自身,值):
        """记下值。"""
        自身._值=值#值

    def 等待(自身):
        """立即交回。"""
        return 自身._值#值

class 输入枢纽:#会话输入门面注册表
    """SessionInputResolver 面；发布为 ctx.conversation.input。"""
    def __init__(自身,根上下文,翻译):
        """翻译 thunk 随 locale 变。"""
        自身.根上下文=根上下文#根
        自身.翻译=翻译#conversation 命名空间
        自身.外壳表={}#会话 id → 壳

    def 按作用域取门面(自身,作用域上下文):
        """非会话作用域则抛。对应上游 for。"""
        标识=自身.取会话面().scopeOf(作用域上下文)#读会话 id
        if 标识 is None:
            raise 对话错误('conversation.input.for requires a session scope')#抛
        return 自身.shell(标识)#壳

    def shellFor(自身,绑定):
        """provide 通道入口；把监听与拆除接到作用域。绑定为跨包对象。"""
        标识=绑定.sessionId#会话 id
        if 标识 in 自身.外壳表:
            return 自身.外壳表[标识]#复用
        会话=绑定.session#会话面
        作用域=绑定.ctx#作用域 ctx
        壳容器={'shell':None}#闭包可变
        def 默认汇(文本,附件标识列表,模式,信号):
            """发提示。"""
            return 自身.下沉(会话,文本,附件标识列表,模式,信号)#下沉
        def 转向队列():
            """并入当前回合。"""
            自身.转向队列(会话,壳容器['shell'])#转向
        def 取触发():
            """斜杠控制器。"""
            return 自身.控制器(作用域)#控制器
        def 取弹层():
            """弹层关闭面。"""
            return 自身.弹层(作用域)#弹层
        def 序列化附件(标识列表):
            """解析草稿附件为线载荷。"""
            return 自身.会话附件().serializeDraftAttachments(标识列表)#任务
        def 释放附件(标识列表):
            """提交成功后释放；会话拆除后服务可能已卸。"""
            会话面=自身.根上下文.获取服务('conversation')#附件面
            if 会话面 is None:#已卸
                return#停
            for 附标识 in 标识列表:#各 id
                会话面.releaseDraftAttachment(附标识)#释放
        def 不支持通知(令牌):
            """命令不接受附件。"""
            名=令牌.strip()#修剪
            if 名.startswith('/'):#去斜杠
                名=名[1:]#切
            return 自身.翻译('command.attachmentsUnsupported',{'command':名})#文案
        壳=会话输入壳({#本会话壳
            'actx':作用域,#作用域
            'inputTriggers':取触发,#斜杠控制器
            'popup':取弹层,#弹层
            'inbox':会话.projections.faceOf('inbox'),#收件箱投影
            'defaultSink':默认汇,#下沉
            'steerQueue':转向队列,#转向
            'commandAttachments':{#命令附件
                'serialize':序列化附件,#序列化
                'release':释放附件,#释放
                'unsupportedNotice':不支持通知,#通知
            },#附件结束
        })#壳结束
        壳容器['shell']=壳#供闭包
        自身.外壳表[标识]=壳#登记
        def 挂监听():
            """四条 slash 监听；拆除时丢壳。"""
            def 开始命令(求):
                """开始命令。求为线协议 dict。"""
                return True if 壳.beginCommand(求['claim'],求['span']) else None#开始
            def 插入引用(求):
                """插入引用。"""
                return True if 壳.insertReference(求['reference'],求['span']) else None#插入
            def 消费令牌(求):
                """消费令牌。"""
                return True if 壳.consumeToken(求['guard']) else None#消费
            def 插入文本(求):
                """插入文本。"""
                继续=求['continue'] is True if 'continue' in 求 else False#继续完成
                return True if 壳.insertText(求['text'],求['span'],继续) else None#插入
            退订列表=[#四条监听
                作用域.监听('slash/input-begin-command',开始命令),#开始命令
                作用域.监听('slash/input-insert-reference',插入引用),#插入引用
                作用域.监听('slash/input-consume-token',消费令牌),#消费令牌
                作用域.监听('slash/input-insert-text',插入文本),#插入文本
            ]#结束
            def 拆除():
                """卸监听、丢壳、释放草稿附件。"""
                for 退 in 退订列表:
                    退()#退订
                草稿=壳.dispose()#仍占用的附件
                自身.外壳表.pop(标识,None)#删表
                会话面=自身.根上下文.获取服务('conversation')#附件面
                if 会话面 is not None:
                    for 附标识 in 草稿:
                        会话面.releaseDraftAttachment(附标识)#释放
                return None#无额外
            return 拆除#退订器
        作用域.副作用(挂监听,'conversation.input: session shell')#挂
        return 壳#交给调用方

    def shell(自身,标识):
        """服务面路径；没有绑定则硬失败。"""
        if 标识 in 自身.外壳表:
            return 自身.外壳表[标识]#复用
        绑定=自身.取会话面().binding(标识)#绑定
        if 绑定 is None:
            raise 对话错误('conversation.input: session "'+str(标识)+'" resolved no binding')#抛
        return 自身.shellFor(绑定)#创建

    def keyboard(自身,标识):
        """InputBar 键盘面。"""
        return 自身.shell(标识)#壳

    def inputTriggers(自身,标识):
        """未装 ui-input-trigger 则为 None。"""
        作用域=自身.取会话面().scope(标识)#作用域
        return None if 作用域 is None else 自身.控制器(作用域)#控制器

    def canPickFiles(自身,标识):
        """不创建会话输入，只问已有壳是否接受文件。"""
        if 标识 not in 自身.外壳表:#无壳
            return False#不接受
        return 自身.外壳表[标识].canPickFiles() is True#已绑且可用

    def pickFiles(自身,标识):
        """按壳存活接入策略打开文件对话框；无壳则无操作。"""
        if 标识 not in 自身.外壳表:#无壳
            return#停
        自身.外壳表[标识].pickFiles()#打开

    def 下沉(自身,会话,文本,附件标识列表,模式,信号):
        """乐观清空后发提示。空内容直接成功。"""
        if 文本=='' and len(附件标识列表)==0:
            return 即时任务({'kind':'success'})#空成功
        return 自身.会话附件().sendSession(会话,文本,附件标识列表,模式,信号)#发

    def 转向队列(自身,会话,壳):
        """FIFO 严格 steer。窗口关闭或行已认领则静默收敛。"""
        if 壳 is None:
            return#停
        收件箱=会话.projections.faceOf('inbox').getSnapshot()#收件箱
        排队=收件箱['next-turn'] if 收件箱 is not None and 'next-turn' in 收件箱 else []#排队
        if len(排队)==0:
            return#停
        for 项 in 排队:
            结果=会话.updateQueue(项['id'],{'kind':'steer'}).等待()#steer
            if 结果['ok'] is True:
                continue#下一条
            错误=结果['error'] if 'error' in 结果 else {}#错误
            码=错误['code'] if 'code' in 错误 else None#码
            if 码 in ('session/steer-unavailable','session/queue-item-not-found'):
                return#停
            壳.notify('error',自身.翻译('queue.steerFailed'))#通知
            return#停

    def 控制器(自身,作用域):
        """按作用域取 slash 控制器。未装则为 None。"""
        触发=自身.根上下文.获取服务('inputTriggers')#服务
        if 触发 is None:
            return None#无
        return 触发.sessionOf(作用域)#控制器

    def 弹层(自身,作用域):
        """按作用域取弹层关闭面。commandUi 可能未装。"""
        命令=自身.根上下文.获取服务('commandUi')#命令 UI
        if 命令 is None:
            return None#无
        return 命令.popupFor(作用域)#弹层

    def 取会话面(自身):
        """未装则硬失败。"""
        会话面=自身.根上下文.获取服务('sessions')#sessions
        if 会话面 is None:
            raise 对话错误('conversation.input: sessions service unavailable')#抛
        return 会话面#面

    def 会话附件(自身):
        """未装则硬失败。"""
        会话=自身.根上下文.获取服务('conversation')#conversation
        if 会话 is None:
            raise 对话错误('conversation.input: conversation service unavailable')#抛
        return 会话#面
