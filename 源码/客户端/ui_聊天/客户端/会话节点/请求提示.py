"""Chat target 的请求头提示词 Definition。

对齐上游 `ui-chat/src/client/conversation-nodes/request-prompt.ts`。公开面仅中文名。
"""
from .节点工厂 import 聊天错误,聊天节点#节点工厂

__all__=['请求提示定义','登记请求提示会话节点']#仅中文公开名

def 请求提示锚(匹配项,先前,是初始):#计算提示词锚点
    """把一次请求的 system 字段放在其可见消息序列起点。"""
    位置=匹配项['location'] if 'location' in 匹配项 else {}#位置
    事件=匹配项['event'] if 'event' in 匹配项 else {}#事件
    if 'kind' not in 位置 or 位置['kind']!='step':#非步骤
        return 事件['seq']#事件 seq
    if 先前 is None and not 是初始:#无先前且非初始
        return 事件['seq']#事件
    步位=位置['step'] if 'step' in 位置 else {}#步
    回合位=位置['turn'] if 'turn' in 位置 else {}#回合
    if 先前 is not None and 先前.get('turn')==(回合位['turn'] if 'turn' in 回合位 else None) and 先前.get('step')==(步位['step'] if 'step' in 步位 else None):#同一步
        return 事件['seq']#事件
    if ('step' in 步位) and 步位['step']==1:#首步
        回合起=None#回合起
        if 'start' in 回合位 and 回合位['start'] is not None and 'seq' in 回合位['start']:#有
            回合起=回合位['start']['seq']#回合起
        步起=None#步起
        if 'start' in 步位 and 步位['start'] is not None and 'seq' in 步位['start']:#有
            步起=步位['start']['seq']#步起
        return 回合起 if 回合起 is not None else (步起 if 步起 is not None else 事件['seq'])#优先回合
    步起=None#步起
    if 'start' in 步位 and 步位['start'] is not None and 'seq' in 步位['start']:#有
        步起=步位['start']['seq']#步起
    return 步起 if 步起 is not None else 事件['seq']#步起

def 稳定请求提示锚(上下文,匹配项,先前,是初始):#稳定锚点
    """已渲染的提示词保持其页生命周期呈现锚点。"""
    取=上下文['current'] if 'current' in 上下文 else None#current
    当前=取['chat'] if 取 is not None and 'chat' in 取 else None#聊天
    if 当前 is not None and 'kind' in 当前 and 当前['kind']=='system-prompt':#已有系统提示
        return 当前['anchorSeq']#保留
    return 请求提示锚(匹配项,先前,是初始)#重算

def 请求提示定义(检视):#请求提示词定义工厂
    """inspect 由 uiConversation 服务提供。"""
    def 匹配(事件):#认领请求头
        """request/header。"""
        if 事件['type']=='request/header':#头
            return {'id':str(事件['seq']),'role':'start'}#开
        return None#不匹配
    def 开始(上下文,匹配项,读取器):#起始状态
        """检视提示词并决定是否显示行。"""
        事件=匹配项['event']#事件
        if 事件['type']!='request/header':#必须
            raise 聊天错误('request-prompt start requires request/header')#硬失败
        上一=读取器.previous('request-prompt')#先前
        先前=上一['state'] if 上一 is not None and 'state' in 上一 else None#态
        位置=匹配项['location'] if 'location' in 匹配项 else {}#位置
        坐标={}#坐标
        if 'kind' in 位置 and 位置['kind']=='step':#步骤
            回合位=位置['turn'] if 'turn' in 位置 else {}#回合
            步位=位置['step'] if 'step' in 位置 else {}#步
            坐标={'turn':回合位['turn'] if 'turn' in 回合位 else None,'step':步位['step'] if 'step' in 步位 else None}#坐标
        数据=事件['data'] if 'data' in 事件 else {}#载荷
        先前提示=先前['prompt'] if 先前 is not None and 'prompt' in 先前 else None#先前提示
        检视结果=检视(先前提示,事件)#检视
        变更=None#变更种
        if 'change' in 检视结果 and 检视结果['change'] is not None and 'kind' in 检视结果['change']:#有
            变更=检视结果['change']['kind']#变更种
        原因=数据['reason'] if 'reason' in 数据 else None#原因
        开系列=数据['startsSeries'] if 'startsSeries' in 数据 else None#开系列
        显示=先前 is None or 原因!='change' or 开系列 is True or 变更 in ('system','system-and-tools')#是否显示
        return {#状态
            'anchorSeq':稳定请求提示锚(上下文,匹配项,先前,原因=='initial'),#锚
            'showsPrompt':显示,#显示
            **坐标,#坐标
            **检视结果,#检视
        }#结束
    def 更新(上下文,_匹配项=None):#状态不变
        """原样。"""
        return 上下文['state'] if 'state' in 上下文 else None#态
    def 建视图(上下文):#构造视图节点
        """无显示或空 system 则不渲染。"""
        态=上下文['state'] if 'state' in 上下文 else None#态
        if 态 is None or not 态.get('showsPrompt'):#不显示
            return None#无
        提示=态['prompt'] if 'prompt' in 态 and 态['prompt'] is not None else {}#提示
        系统=提示['system'] if 'system' in 提示 else ''#system
        if 系统=='':#空
            return None#无
        return 聊天节点(上下文,'system-prompt',态['anchorSeq'],{'text':系统})#节点
    return {#定义
        'kind':'request-prompt','target':'chat',#kind/目标
        'match':匹配,'start':开始,'update':更新,'buildViewNode':建视图,#生命周期
    }#结束

def 登记请求提示会话节点(上下文):#登记请求提示词
    """委托 uiConversation.inspectRequestPrompt。"""
    def 检视(先前,事件):#检视
        """服务检视。"""
        return 上下文.uiConversation.inspectRequestPrompt(先前,事件)#结果
    上下文.uiConversation.events.register(请求提示定义(检视))#登记
