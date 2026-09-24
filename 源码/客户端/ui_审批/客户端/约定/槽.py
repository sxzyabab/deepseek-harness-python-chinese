import threading#中止等待与结算等待

__all__=['待决审批','下一审批键','审批决定','审批错误','已中止','若已中止则抛出']#仅中文公开名

下一审批键=0#渲染身份序号
审批决定=('allowed-once','rejected')#仅本次允许 | 拒绝

class 审批错误(Exception):
    """本包审批结算、中止与委托失败。"""
    def __init__(自身,消息,码=None):
        """记下英文消息与可选结构码。"""
        super().__init__(消息)#消息原样英文
        自身.code=码#结构识别码

def 已中止(信号):
    """threading.Event 是否已置位。"""
    return 信号.is_set()#已置位

def 若已中止则抛出(信号):
    """已置位则抛审批中止。"""
    if 已中止(信号):
        raise 审批错误('approval request was aborted')#中止

class 待决审批:#可作答的待处理 Host waterfall 的 Client 呈现
    """Session 待处理交互消费者使用的域判别。"""
    def __init__(自身,会话标识,请求):
        """记下会话身份与呈现用请求字段。请求为线协议 dict。"""
        global 下一审批键#序号
        下一审批键+=1#递增序号
        自身.kind='approval'#域 kind
        自身.key=f'approval:{下一审批键}'#生成渲染键
        自身.sessionId=会话标识#所属会话
        自身.toolName=请求['toolName']#工具名
        自身.callId=请求['callId'] if 'callId' in 请求 else None#可选调用 id
        自身.reason=请求['reason'] if 'reason' in 请求 else None#可选原因
        自身._信号=请求['signal'] if 'signal' in 请求 else None#可选取消
        自身._已结算=False#是否已结算
        自身._完成=threading.Event()#结算门闩
        自身._结果箱={'value':None,'error':None}#结算箱
        自身._委托=审批错误('pending approval delegated',码='delegated')#本实例委托身份
        自身._onAbort=None#abort 回调
        if 自身._信号 is not None:
            def 中止():
                """传输取消。"""
                自身.abort(审批错误('approval request was aborted'))#传输取消
            自身._onAbort=中止#保存回调
            if 已中止(自身._信号):
                中止()#立即结算
            else:
                def 等中止():
                    """等 Event 置位后结算。"""
                    自身._信号.wait()#阻塞至中止
                    中止()#结算
                threading.Thread(target=等中止,daemon=True).start()#后台等中止

    @property#只读
    def result(自身):
        """阻塞至结算；委托/失败抛。"""
        自身._完成.wait()#等到结算
        if 自身._结果箱['error'] is not None:
            raise 自身._结果箱['error']#抛
        return 自身._结果箱['value']#决定

    def answer(自身,结果):
        """用用户决定解析 Host waterfall。"""
        def 写入():
            """写入决定。"""
            自身._结果箱['value']=结果#成功结算
        try:
            自身._收尾(写入)#一次结算
        except 审批错误 as 错误:
            raise 审批错误('pending approval settlement failed') from 错误

    def delegate(自身):
        """把未作答请求委托给下一个 waterfall 监听器。"""
        if 自身._已结算:
            return#忽略
        def 写入():
            """以委托身份拒绝。"""
            自身._结果箱['error']=自身._委托#委托
        自身._收尾(写入)#一次结算

    def isDelegation(自身,原因):
        """是否由 delegate 产生。"""
        return 原因 is 自身._委托#引用相等

    def abort(自身,原因):
        """在传输、作用域或插件寿命结束时终止未作答呈现。"""
        if 自身._已结算:
            return#忽略
        def 写入():
            """以给定原因拒绝。"""
            自身._结果箱['error']=原因#拒绝
        自身._收尾(写入)#一次结算

    def _收尾(自身,结算):
        """禁止二次结算。"""
        if 自身._已结算:
            raise 审批错误(f'pending approval {自身.key} is already settled')#禁止二次
        自身._已结算=True#标记已结算
        结算()#执行结算回调
        自身._完成.set()#放行 result
