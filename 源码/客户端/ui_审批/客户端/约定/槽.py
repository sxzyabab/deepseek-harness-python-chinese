"""审批 composer 与可选关联详情约定。

对齐上游 `ui-approval/src/client/contract/slots.ts`。公开面仅中文名。
TypeScript 声明合并面以注释保留；可执行域面为 `待决审批`。
"""
__all__=['结算待处理撰写','待决审批','下一审批键','审批决定']#仅中文公开名

下一审批键=0#渲染身份序号
审批决定=('allowed-once','rejected')#仅本次允许 | 拒绝
委托哨兵=object()#委托哨兵

def 结算待处理撰写(结算,失败文案):#把同步结算包成结果
    """成功返回 None；失败抛。"""
    try:#尝试同步结算
        结算()#执行结算
        return None#成功
    except Exception as 错误:#结算抛错
        if isinstance(错误,Exception):#已是 Error
            raise#原样
        raise Exception(失败文案) from 错误#非 Error 包一层

class 待决审批:#可作答的待处理 Host waterfall 的 Client 呈现
    """Session 待处理交互消费者使用的域判别。"""

    def __init__(自身,会话标识,请求):#构造待处理面
        """记下会话身份与呈现用请求字段。"""
        global 下一审批键#序号
        下一审批键+=1#递增序号
        自身.kind='approval'#域 kind
        自身.key=f'approval:{下一审批键}'#生成渲染键
        自身.sessionId=会话标识#所属会话
        自身.toolName=请求.get('toolName') if isinstance(请求,dict) else getattr(请求,'toolName',None)#工具名
        自身.callId=请求.get('callId') if isinstance(请求,dict) else getattr(请求,'callId',None)#可选调用 id
        自身.reason=请求.get('reason') if isinstance(请求,dict) else getattr(请求,'reason',None)#可选原因
        自身._信号=请求.get('signal') if isinstance(请求,dict) else getattr(请求,'signal',None)#可选取消
        自身._已结算=False#是否已结算
        自身._结果箱={'value':None,'error':None,'done':False}#结算箱
        自身._委托哨兵=委托哨兵#委托哨兵
        自身._onAbort=None#abort 监听
        if 自身._信号 is not None:#有取消信号
            def 中止():#abort 回调
                """传输取消。"""
                原因=getattr(自身._信号,'reason',None) or Exception('approval request was aborted')#取消原因
                自身.abort(原因)#传输取消
            自身._onAbort=中止#保存监听引用
            加=getattr(自身._信号,'addEventListener',None)#挂监听
            if callable(加):#有 API
                加('abort',中止,{'once':True})#挂一次性 abort
            if getattr(自身._信号,'aborted',False):#已中止
                中止()#立即结算

    @property#只读
    def result(自身):#Remote Event 监听器返回给 Host waterfall 的结果
        """阻塞至结算；委托/失败抛。"""
        if not 自身._结果箱['done']:#未结算
            return 自身._结果箱#未完成箱（宿主可轮询）
        if 自身._结果箱['error'] is not None:#失败
            raise 自身._结果箱['error']#抛
        return 自身._结果箱['value']#决定

    def answer(自身,结果):#用户作答
        """用用户决定解析 Host waterfall。"""
        def 结算():#成功结算
            """写入决定。"""
            自身._收尾(lambda:自身._结果箱.update({'value':结果,'done':True}))#成功结算
        return 结算待处理撰写(结算,'pending approval settlement failed')#失败文案

    def delegate(自身):#插件拆卸委托
        """把未作答请求委托给下一个 waterfall 监听器。"""
        if 自身._已结算:#已结算
            return#忽略
        自身._收尾(lambda:自身._结果箱.update({'error':自身._委托哨兵,'done':True}))#以委托哨兵拒绝

    def isDelegation(自身,原因):#识别委托哨兵
        """是否由 delegate 产生。"""
        return 原因 is 自身._委托哨兵#比较哨兵

    def abort(自身,原因):#强制结束
        """在传输、作用域或插件寿命结束时终止未作答呈现。"""
        if 自身._已结算:#已结算
            return#忽略
        自身._收尾(lambda:自身._结果箱.update({'error':原因,'done':True}))#以给定原因拒绝

    def _收尾(自身,结算):#一次性结算门闩
        """禁止二次结算。"""
        if 自身._已结算:#已结算
            raise Exception(f'pending approval {自身.key} is already settled')#禁止二次
        自身._已结算=True#标记已结算
        if 自身._信号 is not None and 自身._onAbort is not None:#有 abort 监听
            卸=getattr(自身._信号,'removeEventListener',None)#卸监听
            if callable(卸):#有 API
                卸('abort',自身._onAbort)#卸下 abort 监听
        结算()#执行结算回调

PendingApproval=待决审批#上游名
