from .代际目录 import 代际目录#共享 Host 代际目录

__all__=['模型目录','空目录状态','模型选择错误','选定投影']#仅中文公开名

class 模型选择错误(Exception):
    """模型目录或选定失败。"""
    def __init__(自身,消息):
        """记下英文消息。"""
        super().__init__(消息)#消息原样英文

def 空目录状态():#冷启动快照
    """无选定、无分组、空闲。"""
    return {'current':None,'routable':None,'groups':[],'failures':[],'status':'idle','error':None}#冷启动

def 选定投影(值):#未知值 → 选定投影
    """undefined 原样，其余当作投影。"""
    return None if 值 is None else 值#None 原样

class 简易快照存储:#对 uSES 安全的浅存储
    """订阅 + 可变快照。"""
    def __init__(自身,初始):#初始快照
        """记下状态与订阅表。"""
        自身.状态=dict(初始)#可变
        自身.订阅列表=[]#监听

    def getSnapshot(自身):#读快照
        """返回浅拷贝。"""
        return dict(自身.状态)#拷贝

    def subscribe(自身,监听器):#订阅
        """返回拆除器。"""
        自身.订阅列表.append(监听器)#登记
        def 拆除订阅():#拆除
            """去掉监听。"""
            if 监听器 in 自身.订阅列表:#仍在
                自身.订阅列表.remove(监听器)#删
        return 拆除订阅#拆除器

    def update(自身,改):#改快照
        """改函数就地改状态后广播。"""
        改(自身.状态)#改
        for 监听器 in list(自身.订阅列表):#广播
            监听器()#回调

    def set(自身,下一快照):#整表替换
        """写快照并广播。"""
        自身.状态=dict(下一快照)#替换
        for 监听器 in list(自身.订阅列表):#广播
            监听器()#回调

class 模型目录:#每会话模型目录控制器
    """两条入口共享 Host 代际目录与持久选定投影，经同一次 selectModel 提交。"""
    def __init__(自身,会话线,会话标识,可用,目录账本,投影源):#注入
        """记下会话线、身份、可用性、共享目录与投影。"""
        自身.会话线=会话线#仅 selectModel
        自身.会话标识=会话标识#会话 id
        自身.可用=可用#可用性工厂
        自身.目录账本=目录账本#共享 Host 代际目录
        自身.投影源=投影源#可观察投影
        自身.存储=简易快照存储(空目录状态())#共享存储
        自身.世代=0#操作世代
        自身.已拆除=False#拆除标志
        自身.已解析=False#是否已解析过投影与目录
        自身.卸目录=目录账本.存储.subscribe(自身._同步输入)#目录变更则同步
        自身.卸投影=投影源.subscribe(自身._同步输入)#投影变更则同步
        自身._同步输入()#立刻同步一次

    def 断言可用(自身):#本会话必须可用模型 RPC
        """子智能体会话不可用。"""
        if not 自身.可用():#不可用
            raise 模型选择错误('model selection is unavailable for addressed subagent sessions')#拒绝

    def load(自身):#确保共享目录已加载
        """按新目录重算快照并交出。"""
        自身.断言可用()#守卫
        自身.目录账本.load()#拉共享目录
        自身._同步输入()#按新目录重算
        return 自身.存储.getSnapshot()#当前快照

    def select(自身,选定):#提交完整选定
        """成功则就绪；失败写 store 并返回 RemoteResult 形 dict。"""
        自身.断言可用()#守卫
        自身.世代+=1#世代
        本轮=自身.世代#本轮
        def 标选定(态):#selecting
            """标 selecting。"""
            态['status']='selecting'#选定中
            态['error']=None#清错
        自身.存储.update(标选定)#selecting
        载荷={'sessionId':自身.会话标识,'provider':选定['provider'],'model':选定['model']}#载荷
        if 'reasoningEffort' in 选定 and 选定['reasoningEffort'] is not None:#有力度
            载荷['reasoningEffort']=选定['reasoningEffort']#带上
        应答=自身.会话线.selectModel(载荷).等待()#提交
        结果=应答['result'] if 'result' in 应答 else 应答#信封
        if 自身.已拆除 or 本轮!=自身.世代:#过期
            return {'ok':True,'value':None} if 'ok' in 结果 and 结果['ok'] else 结果#过期仍交回
        if not 结果['ok']:#业务失败
            错=结果['error'] if 'error' in 结果 and 结果['error'] is not None else {}#错误
            文=str(错['code'] if 'code' in 错 else None)+': '+str(错['message'] if 'message' in 错 else None)#文案
            def 写错(态):#写错误
                """标 error。"""
                态['status']='error'#失败
                态['error']=文#文案
            自身.存储.update(写错)#写
            return 结果#交回失败
        def 写好(态):#就绪
            """标就绪并清错。"""
            态['status']='ready'#就绪
            态['error']=None#清错
        自身.存储.update(写好)#写
        自身._同步输入()#按投影与目录重算
        return {'ok':True,'value':None}#成功

    def resetConnected(自身):#重连后作废在飞选定
        """作废在飞并按当前目录与投影重算。"""
        if 自身.已拆除:#已拆
            return#结束
        自身.世代+=1#作废
        def 清选定中(态):#清选定中状态
            """选定中回空闲。"""
            if 态['status']=='selecting':#选定中
                态['status']='idle'#回空闲
            态['error']=None#清错
        自身.存储.update(清选定中)#清
        自身._同步输入()#重算

    def dispose(自身):#拆除
        """迟到结算失去写权限。"""
        自身.已拆除=True#标死
        自身.卸投影()#卸投影订阅
        自身.卸目录()#卸目录订阅

    def _同步输入(自身):#按目录与投影重算共享快照
        """输入未齐则 loading/error；齐则就绪。"""
        if 自身.已拆除:#已拆
            return#不再写
        目录态=自身.目录账本.存储.getSnapshot()#共享目录快照
        投影=选定投影(自身.投影源.getSnapshot())#持久选定投影
        if 目录态['status']!='ready' or 目录态['value'] is None or 投影 is None:#输入尚未齐
            if 自身.已解析:#曾经解析过
                if 目录态['status']=='error':#目录失败则映到本 store
                    def 映错(态):#映错误
                        """标 error。"""
                        态['status']='error'#错误态
                        态['error']=目录态['error']#共享错误文案
                    自身.存储.update(映错)#写
                return#已解析过则保留上次成功快照
            自身.存储.set({#冷启动/加载中快照
                'current':None,#尚无选定
                'routable':None,#未加载
                'groups':[],#空分组
                'failures':[],#空失败
                'status':'error' if 目录态['status']=='error' else 'loading',#目录错则 error
                'error':目录态['error'],#共享错误文案
            })#结束 set
            return#输入未齐结束
        目录值=目录态['value']#目录值
        当前=投影['next'] if 'next' in 投影 and 投影['next'] is not None else 目录值['default']#投影下一请求，否则 Host 默认
        自身.已解析=True#标记已解析
        可路由表=目录值['routableProviders'] if 'routableProviders' in 目录值 and 目录值['routableProviders'] is not None else []#可路由提供方
        现态=自身.存储.getSnapshot()#当前本 store
        自身.存储.set({#写入就绪快照
            'current':当前,#有效选定
            'routable':当前['provider'] in 可路由表 if 当前 is not None and 'provider' in 当前 else False,#该提供方是否可路由
            'groups':目录值['groups'] if 'groups' in 目录值 and 目录值['groups'] is not None else [],#提供方分组
            'failures':目录值['failures'] if 'failures' in 目录值 and 目录值['failures'] is not None else [],#提供方失败
            'status':'selecting' if 现态['status']=='selecting' else 'ready',#选定飞行中则保持
            'error':None,#清错误
        })#结束 set
