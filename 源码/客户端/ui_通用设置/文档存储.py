__all__=['快照存储','设置文档存储','已加载则刷新文档','通用设置错误']#仅中文公开名

class 通用设置错误(Exception):
    """本包设置文档动作失败。"""
    def __init__(自身,消息):
        """记下英文消息。"""
        super().__init__(消息)#消息原样英文

def 错误文案(错误):
    """Error 取其 message。"""
    return str(错误)#文案

class 快照存储:
    """标题栏动作共用的状态源。"""
    def __init__(自身,初值):
        """记下初值。"""
        自身.状态=dict(初值)#状态
        自身.监听者=set()#订阅者

    def getSnapshot(自身):
        """返回当前状态。"""
        return 自身.状态#状态

    def subscribe(自身,回调):
        """登记变更回调。"""
        自身.监听者.add(回调)#加入
        def 退订():
            """取消。"""
            自身.监听者.discard(回调)#删除
        return 退订#退订器

    def update(自身,变换):
        """调用变换(state)。"""
        变换(自身.状态)#变换
        for 回调 in list(自身.监听者):#通知
            回调()#触发

class 设置文档存储:
    """加载本地文档是否可用，并调用无路径的宿主打开操作。describe/openDocument 返回任务。"""
    def __init__(自身,接口):
        """空闲快照。"""
        自身.接口=接口#settings 面
        自身.存储=快照存储({'status':'idle','opening':False,'error':None})#快照
        自身.世代=0#在飞请求世代

    def load(自身):
        """最新请求胜出。"""
        自身.世代+=1#抬世代
        世代=自身.世代#本请求
        def 标加载(态):
            """标 loading。"""
            态['status']='loading'#加载中
            态['error']=None#清错误
        自身.存储.update(标加载)#写入
        try:#describe
            应答=自身.接口.settings.describe({}).等待()#描述
            if 世代!=自身.世代:#过期
                return#丢弃
            结果=应答['result']#业务结果
            if not 结果['ok']:#业务失败
                错误体=结果['error'] if 'error' in 结果 else None#错误
                消息=错误体['message'] if 错误体 is not None and 'message' in 错误体 else None#文案
                def 写成不可用(态):
                    """记下业务错误。"""
                    态['status']='unavailable'#不可用
                    态['error']=消息#错误
                自身.存储.update(写成不可用)#写入
                return
            值=结果['value'] if 'value' in 结果 and 结果['value'] is not None else {}#值
            有文档=bool(值['hasDocument']) if 'hasDocument' in 值 else False#是否有文档
            def 写结果(态):
                """按是否有文档写入。"""
                态['status']='ready' if 有文档 else 'unavailable'#状态
                态['error']=None#清错误
            自身.存储.update(写结果)#写入
        except Exception as 错误:#传输失败；RPC 异常契约未定
            if 世代!=自身.世代:#过期
                return#丢弃
            def 写失败(态):
                """记下失败。"""
                态['status']='unavailable'#不可用
                态['error']=错误文案(错误)#文案
            自身.存储.update(写失败)#写入

    def open(自身):
        """并发手势并入在飞。"""
        当前=自身.存储.getSnapshot()#当前
        if 当前['status']!='ready' or 当前['opening']:#未就绪或已在打开
            return#忽略
        def 标打开(态):
            """标 opening。"""
            态['opening']=True#打开中
            态['error']=None#清错误
        自身.存储.update(标打开)#写入
        try:#openDocument
            应答=自身.接口.settings.openDocument({}).等待()#无路径打开
            结果=应答['result']#业务结果
            if not 结果['ok']:#业务失败
                错误体=结果['error'] if 'error' in 结果 else None#错误
                消息=错误体['message'] if 错误体 is not None and 'message' in 错误体 else None#文案
                raise 通用设置错误(消息)#抛
        except Exception as 错误:#打开失败；RPC 异常契约未定
            def 写失败(态):
                """记下失败文案。"""
                态['error']=错误文案(错误)#文案
            自身.存储.update(写失败)#写入
        finally:#清 opening
            def 清打开(态):
                """打开不再在飞。"""
                态['opening']=False
            自身.存储.update(清打开)#写入

def 已加载则刷新文档(控制器):
    """idle 则跳过。"""
    if 控制器 is None:#无
        return#跳过
    if 控制器.存储.getSnapshot()['status']=='idle':#尚未打开
        return#跳过
    控制器.load()#刷新
