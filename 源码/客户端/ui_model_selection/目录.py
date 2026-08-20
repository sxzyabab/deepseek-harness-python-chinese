"""每会话模型目录：两条选定入口共享的唯一状态。

对齐上游 `ui-model-selection/src/client/directory.ts`。公开面仅中文名。
"""
from cordis.工具 import 是否thenable#可等待判定

__all__=['模型目录','空目录状态']#仅中文公开名

def 空目录状态():#冷启动快照
    """无选定、无分组、空闲。"""
    return {'current':None,'routable':None,'groups':[],'failures':[],'status':'idle','error':None}#冷启动

def 解开(值):#承诺则等待
    """承诺则等待，否则原样。"""
    if 是否thenable(值):#可等待
        return 值.等待()#等待
    return 值#同步

class 简易快照仓:#对 uSES 安全的浅仓
    """订阅 + 可变快照。"""
    def __init__(自身,初始):#初始快照
        """记下状态与订阅表。"""
        自身.状态=dict(初始)#可变
        自身.订阅们=[]#监听

    def getSnapshot(自身):#读快照
        """返回浅拷贝。"""
        return dict(自身.状态)#拷贝

    def subscribe(自身,听):#订阅
        """返回拆除器。"""
        自身.订阅们.append(听)#登记
        def 拆():#拆除
            """去掉监听。"""
            if 听 in 自身.订阅们:#仍在
                自身.订阅们.remove(听)#删
        return 拆#拆除器

    def update(自身,改):#改快照
        """改函数就地改状态后广播。"""
        改(自身.状态)#改
        for 听 in list(自身.订阅们):#广播
            听()#回调

class 模型目录:#每会话模型目录控制器
    """两条入口共享同一 store 与 selectModel 提交。"""
    def __init__(自身,会话线,会话标识,可用):#注入
        """记下会话线、身份与可用性。"""
        自身.会话线=会话线#sessions RPC
        自身.会话标识=会话标识#会话 id
        自身.可用=可用#可用性工厂
        自身.store=简易快照仓(空目录状态())#共享仓
        自身.世代=0#操作世代
        自身.已拆除=False#拆除标志

    def 断言可用(自身):#本会话必须可用模型 RPC
        """子智能体会话不可用。"""
        if not 自身.可用():#不可用
            raise Exception('model selection is unavailable for addressed subagent sessions')#拒绝

    def load(自身):#刷新目录
        """失败保留上次成功分组与当前选定。"""
        自身.断言可用()#守卫
        自身.世代+=1#世代
        本轮=自身.世代#本轮
        自身.store.update(lambda 态:(态.__setitem__('status','loading'),态.__setitem__('error',None)))#loading
        应答=解开(自身.会话线.models({'sessionId':自身.会话标识}))#拉目录
        结果=应答['result'] if isinstance(应答,dict) and 'result' in 应答 else 应答#结果信封
        if 自身.已拆除 or 本轮!=自身.世代:#过期
            if not 结果.get('ok'):#失败
                错=结果.get('error') or {}#错误
                raise Exception(str(错.get('code'))+': '+str(错.get('message')))#抛
            return 结果.get('value')#值
        if not 结果.get('ok'):#业务失败
            错=结果.get('error') or {}#错误
            文=str(错.get('code'))+': '+str(错.get('message'))#文案
            def 写错(态):#写错误
                """标 error。"""
                态['status']='error'#失败
                态['error']=文#文案
            自身.store.update(写错)#写
            raise Exception('session.models failed: '+文)#抛
        值=结果.get('value') or {}#目录值
        def 写好(态):#写成功
            """写入成功快照。"""
            态['current']=值.get('current')#选定
            态['routable']=值.get('routable')#可路由
            态['groups']=值.get('groups') or []#分组
            态['failures']=值.get('failures') or []#失败
            态['status']='ready'#就绪
            态['error']=None#清错
        自身.store.update(写好)#写
        return 值#目录

    def select(自身,选定):#提交完整选定
        """成功更新共享 current；失败写 store 并抛。"""
        自身.断言可用()#守卫
        自身.世代+=1#世代
        本轮=自身.世代#本轮
        自身.store.update(lambda 态:(态.__setitem__('status','selecting'),态.__setitem__('error',None)))#selecting
        载荷={'sessionId':自身.会话标识,'provider':选定['provider'],'model':选定['model']}#载荷
        if 选定.get('reasoningEffort') is not None:#有力度
            载荷['reasoningEffort']=选定['reasoningEffort']#带上
        应答=解开(自身.会话线.selectModel(载荷))#提交
        结果=应答['result'] if isinstance(应答,dict) and 'result' in 应答 else 应答#信封
        if 自身.已拆除 or 本轮!=自身.世代:#过期
            if not 结果.get('ok'):#失败
                错=结果.get('error') or {}#错误
                raise Exception(str(错.get('code'))+': '+str(错.get('message')))#抛
            return#结束
        if not 结果.get('ok'):#业务失败
            错=结果.get('error') or {}#错误
            文=str(错.get('code'))+': '+str(错.get('message'))#文案
            def 写错(态):#写错误
                """标 error。"""
                态['status']='error'#失败
                态['error']=文#文案
            自身.store.update(写错)#写
            raise Exception('session.selectModel failed: '+文)#抛
        值=结果.get('value') or {}#接受值
        def 写好(态):#写共享 current
            """落地选定。"""
            态['current']=值.get('selected')#宿主接受
            态['routable']=True#可服务
            态['status']='ready'#就绪
            态['error']=None#清错
        自身.store.update(写好)#写

    def resetConnected(自身):#重连后丢掉投影并重拉
        """先清空以免显示进程本地选定。"""
        if 自身.已拆除:#已拆
            return#结束
        自身.世代+=1#作废
        自身.store.update(lambda 态:态.update(空目录状态()))#冷启动
        if not 自身.可用():#不可用
            return#不拉
        try:#重拉
            自身.load()#加载
        except Exception:#失败吞掉
            pass#下次菜单重试

    def dispose(自身):#拆除
        """迟到结算失去写权限。"""
        自身.已拆除=True#标死
