"""Chat target 的请求头提示词 Definition。

对齐上游 `ui-chat/src/client/conversation-nodes/request-prompt.ts`。公开面仅中文名。
"""
from .公共 import 聊天节点#节点工厂
from .面辅助 import 取字段#字段

__all__=['请求提示定义','登记请求提示会话节点']#仅中文公开名

def 请求提示锚(匹配项,先前,是初始):#计算提示词锚点
    """把一次请求的 system 字段放在其可见消息序列起点。"""
    位置=取字段(匹配项,'location') or {}#位置
    事件=取字段(匹配项,'event') or {}#事件
    if 取字段(位置,'kind')!='step':#非步骤
        return 取字段(事件,'seq')#事件 seq
    if 先前 is None and not 是初始:#无先前且非初始
        return 取字段(事件,'seq')#事件
    步位=取字段(位置,'step') or {}#步
    回合位=取字段(位置,'turn') or {}#回合
    if 先前 is not None and 先前.get('turn')==取字段(回合位,'turn') and 先前.get('step')==取字段(步位,'step'):#同一步
        return 取字段(事件,'seq')#事件
    if 取字段(步位,'step')==1:#首步
        回合起=取字段(取字段(回合位,'start'),'seq')#回合起
        步起=取字段(取字段(步位,'start'),'seq')#步起
        return 回合起 if 回合起 is not None else (步起 if 步起 is not None else 取字段(事件,'seq'))#优先回合
    步起=取字段(取字段(步位,'start'),'seq')#步起
    return 步起 if 步起 is not None else 取字段(事件,'seq')#步起

def 稳定请求提示锚(上下文,匹配项,先前,是初始):#稳定锚点
    """已渲染的提示词保持其页生命周期呈现锚点。"""
    当前=None#已有
    取=取字段(上下文,'current')#current
    if 取 is not None and hasattr(取,'get'):#有
        当前=取.get('chat')#聊天
    if 取字段(当前,'kind')=='system-prompt':#已有系统提示
        return 取字段(当前,'anchorSeq')#保留
    return 请求提示锚(匹配项,先前,是初始)#重算

def 请求提示定义(检视):#请求提示词定义工厂
    """inspect 由 uiConversation 服务提供。"""
    def 匹配(事件):#认领请求头
        """request/header。"""
        if 取字段(事件,'type')=='request/header':#头
            return {'id':str(取字段(事件,'seq')),'role':'start'}#开
        return None#不匹配
    def 开始(上下文,匹配项,读取器):#起始状态
        """检视提示词并决定是否显示行。"""
        事件=取字段(匹配项,'event')#事件
        if 取字段(事件,'type')!='request/header':#必须
            raise Exception('request-prompt start requires request/header')#硬失败
        上一=读取器.previous('request-prompt') if hasattr(读取器,'previous') else None#先前
        先前=取字段(上一,'state') if 上一 is not None else None#态
        位置=取字段(匹配项,'location') or {}#位置
        坐标={}#坐标
        if 取字段(位置,'kind')=='step':#步骤
            坐标={'turn':取字段(取字段(位置,'turn'),'turn'),'step':取字段(取字段(位置,'step'),'step')}#坐标
        数据=取字段(事件,'data') or {}#载荷
        检视结果=检视(取字段(先前,'prompt') if 先前 else None,事件)#检视
        变更=取字段(取字段(检视结果,'change'),'kind')#变更种
        显示=先前 is None or 取字段(数据,'reason')!='change' or 取字段(数据,'startsSeries') is True or 变更 in ('system','system-and-tools')#是否显示
        return {#状态
            'anchorSeq':稳定请求提示锚(上下文,匹配项,先前,取字段(数据,'reason')=='initial'),#锚
            'showsPrompt':显示,#显示
            **坐标,#坐标
            **(检视结果 if isinstance(检视结果,dict) else {}),#检视
        }#结束
    def 更新(上下文,_匹配项=None):#状态不变
        """原样。"""
        return 取字段(上下文,'state')#态
    def 建视图(上下文):#构造视图节点
        """无显示或空 system 则不渲染。"""
        态=取字段(上下文,'state')#态
        if 态 is None or not 态.get('showsPrompt'):#不显示
            return None#无
        提示=态.get('prompt') or {}#提示
        系统=取字段(提示,'system') or ''#system
        if 系统=='':#空
            return None#无
        return 聊天节点(上下文,'system-prompt',态['anchorSeq'],{'text':系统})#节点
    return {#定义
        'kind':'request-prompt','target':'chat',#kind/目标
        'match':匹配,'start':开始,'update':更新,'buildViewNode':建视图,#生命周期
    }#结束

def 登记请求提示会话节点(上下文):#登记请求提示词
    """委托 uiConversation.inspectRequestPrompt。"""
    会话=取字段(上下文,'uiConversation') or 上下文#面
    def 检视(先前,事件):#检视
        """服务检视。"""
        函=getattr(会话,'inspectRequestPrompt',None)#检视
        return 函(先前,事件) if callable(函) else {'prompt':{'system':''}}#结果
    事件面=getattr(会话,'events',None) or getattr(上下文,'conversationEvents',None)#事件
    if 事件面 is not None:#有
        事件面.register(请求提示定义(检视))#登记
