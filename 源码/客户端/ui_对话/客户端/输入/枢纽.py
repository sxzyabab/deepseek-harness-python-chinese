"""输入枢纽：按会话解析的输入门面注册表。

对齐上游 `ui-conversation/src/client/input/hub.ts`。公开面仅中文名。
每个会话一个会话输入壳，在 sessions provide 物化时创建，由作用域 disposer 拆除。
"""
from ..队列.仓库 import 队列读面自会话#队列只读面
from .外壳 import 会话输入壳#会话输入壳

__all__=['输入枢纽']#仅中文公开名

def 取字段(对象,键,缺省=None):#读字段
    """映射或对象。"""
    if 对象 is None:#空
        return 缺省#缺
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

def 解开(值):#承诺则等待
    """有等待方法则调用。"""
    if hasattr(值,'等待') and callable(值.等待):#中文承诺
        return 值.等待()#等待
    then=getattr(值,'then',None)#Promise
    if callable(then):#异步面——同步宿主半不挂回调，原样返回
        return 值#原样
    return 值#同步

class 输入枢纽:#会话输入门面注册表
    """SessionInputResolver 面；发布为 ctx.conversation.input。"""
    def __init__(自身,根上下文,翻译):#记下根上下文与翻译
        """翻译 thunk 随 locale 变。"""
        自身.根上下文=根上下文#根
        自身.翻译=翻译#conversation 命名空间
        自身.外壳们={}#会话 id → 壳

    def for_(自身,作用域上下文):#按会话作用域 ctx 解析门面
        """非会话作用域则抛。上游方法名 for。"""
        标识=自身.会话们().scopeOf(作用域上下文)#读会话 id
        if 标识 is None:#非会话
            raise Exception('conversation.input.for requires a session scope')#抛
        return 自身.shell(标识)#壳

    def shellFor(自身,绑定):#按会话绑定取驻留壳
        """provide 通道入口；把监听与拆除接到作用域。"""
        标识=取字段(绑定,'sessionId')#会话 id
        已有=自身.外壳们.get(标识)#复用
        if 已有 is not None:#已物化
            return 已有#复用
        会话=取字段(绑定,'session')#会话面
        作用域=取字段(绑定,'ctx')#作用域 ctx
        壳容器={'shell':None}#闭包可变
        def 默认汇(文本,图片标识们,模式):#默认下沉
            """发提示。"""
            自身.下沉(会话,文本,图片标识们,模式)#下沉
        def 转向队列():#整队转向
            """并入当前回合。"""
            自身.转向队列(会话,壳容器['shell'])#转向
        壳=会话输入壳({#本会话壳
            'actx':作用域,#作用域
            'inputTriggers':lambda:自身.控制器(作用域),#斜杠控制器
            'popup':lambda:自身.弹层(作用域),#弹层
            'queue':队列读面自会话(会话),#队列读面
            'defaultSink':默认汇,#下沉
            'steerQueue':转向队列,#转向
        })#壳结束
        壳容器['shell']=壳#供闭包
        自身.外壳们[标识]=壳#登记
        def 挂监听():#作用域 fiber
            """四条 slash 监听；拆除时丢壳。"""
            退订们=[#四条监听
                作用域.on('slash/input-begin-command',lambda 求:True if 壳.beginCommand(取字段(求,'claim'),取字段(求,'span')) else None),#开始命令
                作用域.on('slash/input-insert-reference',lambda 求:True if 壳.insertReference(取字段(求,'reference'),取字段(求,'span')) else None),#插入引用
                作用域.on('slash/input-consume-token',lambda 求:True if 壳.consumeToken(取字段(求,'guard')) else None),#消费令牌
                作用域.on('slash/input-insert-text',lambda 求:True if 壳.insertText(取字段(求,'text'),取字段(求,'span')) else None),#插入文本
            ]#结束
            def 拆除():#作用域拆除
                """卸监听、丢壳、释放草稿图。"""
                for 退 in 退订们:#逐个
                    退()#退订
                草稿=取字段(壳.snapshot,'imageIds') or []#草稿图
                壳.dispose()#拆壳
                自身.外壳们.pop(标识,None)#删表
                会话面=自身.根上下文.get('conversation')#附件面
                if 会话面 is not None:#有
                    for 图标识 in 草稿:#逐张
                        会话面.releaseDraftImage(图标识)#释放
                return None#无额外
            return 拆除#退订器
        作用域.effect(挂监听,'conversation.input: session shell')#挂
        return 壳#交给调用方

    def shell(自身,标识):#按会话 id 取驻留壳
        """服务面路径；没有绑定则硬失败。"""
        已有=自身.外壳们.get(标识)#复用
        if 已有 is not None:#已有
            return 已有#复用
        绑定=自身.会话们().binding(标识)#绑定
        if 绑定 is None:#无
            raise Exception('conversation.input: session "'+str(标识)+'" resolved no binding')#抛
        return 自身.shellFor(绑定)#创建

    def keyboard(自身,标识):#InputBar 键盘面
        """壳即键盘面。"""
        return 自身.shell(标识)#壳

    def inputTriggers(自身,标识):#可选 slash 控制器
        """未装 ui-input-trigger 则为 None。"""
        作用域=自身.会话们().scope(标识)#作用域
        return None if 作用域 is None else 自身.控制器(作用域)#控制器

    def 下沉(自身,会话,文本,图片标识们,模式):#乐观清空后发提示
        """空正文且无图则不发。"""
        if 文本=='' and len(图片标识们)==0:#空
            return#停
        标识=取字段(会话,'sessionId')#会话 id
        壳=自身.外壳们.get(标识)#壳
        if 壳 is not None:#有
            壳.commitSend(图片标识们)#提交发送
        def 失败(_=None):#发送失败
            """恢复草稿或释放图。"""
            if 自身.外壳们.get(标识) is 壳 and 壳 is not None:#同实例
                壳.restoreImages(图片标识们)#恢复图
                if 取字段(壳.snapshot,'draft')=='':#草稿仍空
                    壳.setDraft(文本)#还原正文
                return#停
            会话面=自身.根上下文.get('conversation')#附件面
            if 会话面 is not None:#有
                for 图标识 in 图片标识们:#逐张
                    会话面.releaseDraftImage(图标识)#释放
        try:#发送
            结果=自身.会话附件().sendSession(会话,文本,图片标识们,模式)#发
            then=getattr(结果,'then',None)#Promise
            if callable(then):#异步
                then(lambda *_:None,失败)#挂失败
            等待=getattr(结果,'等待',None)#中文承诺
            if callable(等待):#可等待——同步宿主半当即等
                try:#等
                    等待()#等
                except Exception:#失败
                    失败()#恢复
        except Exception:#同步失败
            失败()#恢复

    def 转向队列(自身,会话,壳):#FIFO 严格 steer
        """窗口关闭或行已认领则静默收敛。"""
        if 壳 is None:#无壳
            return#停
        快照=会话.getSnapshot()#快照
        排队=[项 for 项 in (取字段(快照,'queue') or []) if 取字段(项,'placement')=='queued']#排队
        if len(排队)==0:#空
            return#停
        for 项 in 排队:#逐条
            结果=解开(会话.updateQueue(取字段(项,'id'),{'kind':'steer'}))#steer
            if 取字段(结果,'ok') is True:#成功
                continue#下一条
            错误=取字段(结果,'error') or {}#错误
            码=取字段(错误,'code')#码
            if 码 in ('steer-unavailable','queue-item-not-found'):#可收敛
                return#停
            壳.notify('error',自身.翻译('queue.steerFailed'))#通知
            return#停

    def 控制器(自身,作用域):#按作用域取 slash 控制器
        """根上 inputTriggers 可能未装。"""
        触发=自身.根上下文.get('inputTriggers')#服务
        if 触发 is None:#未装
            return None#无
        取=getattr(触发,'sessionOf',None)#sessionOf
        return 取(作用域) if callable(取) else None#控制器

    def 弹层(自身,作用域):#按作用域取弹层关闭面
        """commandUi 可能未装。"""
        命令=自身.根上下文.get('commandUi')#命令 UI
        if 命令 is None:#未装
            return None#无
        取=getattr(命令,'popupFor',None)#popupFor
        return 取(作用域) if callable(取) else None#弹层

    def 会话们(自身):#取会话表
        """未装则硬失败。"""
        会话们=自身.根上下文.get('sessions')#sessions
        if 会话们 is None:#未装
            raise Exception('conversation.input: sessions service unavailable')#抛
        return 会话们#面

    def 会话附件(自身):#取附件发送面
        """未装则硬失败。"""
        会话=自身.根上下文.get('conversation')#conversation
        if 会话 is None:#未装
            raise Exception('conversation.input: conversation service unavailable')#抛
        return 会话#面

输入枢纽.for=输入枢纽.for_#上游方法名 for（关键字，属性别名）
