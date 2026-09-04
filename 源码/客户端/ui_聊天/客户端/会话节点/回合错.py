"""终局回合失败会话节点。

对齐上游 `ui-chat/src/client/conversation-nodes/turn-error.ts`。公开面仅中文名。
"""
from .公共 import 聊天节点#聊天节点工厂
from .面辅助 import 取字段,展示失败文案#面辅助

__all__=['回合错定义','登记回合错会话节点']#仅中文公开名

def 末步(上下文):#该回合最后一步号
    """非回合/步骤位置则 0。"""
    起点=取字段(上下文,'start')#起点
    匹配们=取字段(上下文,'matches') or []#匹配
    位置=取字段(起点,'location') if 起点 is not None else (取字段(匹配们[0],'location') if 匹配们 else None)#位置
    if 取字段(位置,'kind') not in ('turn','step'):#非
        return 0#零
    步们=取字段(取字段(位置,'turn'),'steps') or []#步列表
    return 取字段(步们[-1],'step',0) if 步们 else 0#末步

def 重试回合(事件):#事件是否属于某回合的重试
    """llm/retry 或 llm/retry-started。"""
    种=取字段(事件,'type')#种
    if 种 in ('llm/retry','llm/retry-started'):#重试
        return 取字段(取字段(事件,'data'),'turn')#回合号
    return None#非

def 自匹配抽失败(匹配项):#从匹配抽出失败快照
    """仅 turn/end 且 reason.kind==error。"""
    事件=取字段(匹配项,'event')#事件
    if 取字段(事件,'type')!='turn/end':#非
        return None#无
    原因=取字段(取字段(事件,'data'),'reason') or {}#原因
    if 取字段(原因,'kind')!='error':#非错误
        return None#无
    失败=取字段(原因,'error') or {}#错误对象
    出={'seq':取字段(事件,'seq'),'time':取字段(事件,'time'),'message':展示失败文案(失败)}#快照
    if 取字段(失败,'code') is not None:#有码
        出['code']=取字段(失败,'code')#带上
    return 出#失败快照

def 回放回合错(上下文):#从匹配回退拼状态
    """有重试链则 hidden。"""
    匹配们=取字段(上下文,'matches') or []#匹配
    结束=next((候 for 候 in 匹配们 if 自匹配抽失败(候) is not None),None)#带失败
    if 结束 is None or 取字段(取字段(结束,'event'),'type')!='turn/end':#无
        return None#放弃
    失败=自匹配抽失败(结束)#快照
    if 失败 is None:#无
        return None#放弃
    数据=取字段(取字段(结束,'event'),'data') or {}#载荷
    回合=取字段(数据,'turn')#回合号
    隐藏=any(重试回合(取字段(候,'event'))==回合 for 候 in 匹配们)#同回合有重试
    return {'turn':回合,'hidden':隐藏,'failure':失败}#回退态

def 回合错匹配(事件):#按事件认领或更新本节点
    """turn/start 开；错误收尾与重试更新。"""
    种=取字段(事件,'type')#种
    数据=取字段(事件,'data') or {}#载荷
    if 种=='turn/start':#回合开始
        return {'id':str(取字段(数据,'turn')),'role':'start'}#开
    if 种=='turn/end' and 取字段(取字段(数据,'reason'),'kind')=='error':#错误收尾
        return {'id':str(取字段(数据,'turn')),'role':'update'}#更新
    回合=重试回合(事件)#重试回合
    return None if 回合 is None else {'id':str(回合),'role':'update'}#有则更新

def 回合错开始(_上下文,匹配项):#从 turn/start 建初始状态
    """必须是 turn/start。"""
    事件=取字段(匹配项,'event')#事件
    if 取字段(事件,'type')!='turn/start':#非
        raise Exception('turn-error start requires turn/start')#硬失败
    return {'turn':取字段(取字段(事件,'data'),'turn'),'hidden':False}#初态

def 回合错更新(上下文,匹配项):#写入失败或因重试隐藏
    """失败快照或 hidden。"""
    态=取字段(上下文,'state')#态
    失败=自匹配抽失败(匹配项)#失败
    if 失败 is not None:#有
        return {**态,'failure':失败}#记下
    if 重试回合(取字段(匹配项,'event'))==态.get('turn'):#本回合重试
        return {**态,'hidden':True}#隐藏
    return 态#无关

def 回合错建视图(上下文):#拼最终聊天节点
    """无失败则不渲染；隐藏仍可占位。"""
    态=取字段(上下文,'state') or 回放回合错(上下文)#态
    if 态 is None or 态.get('failure') is None:#无失败
        return None#不建
    失败=态['failure']#快照
    节点={'kind':'turn-error','seq':失败['seq'],'time':失败['time'],'turn':态['turn'],'step':末步(上下文),'message':失败['message']}#载荷
    if 失败.get('code') is not None:#有码
        节点['code']=失败['code']#带上
    if not 态.get('hidden'):#未隐藏
        return 聊天节点(上下文,'turn-error',节点['seq'],节点)#可见
    当前=None#已有
    取=取字段(上下文,'current')#current
    if 取 is not None and hasattr(取,'get'):#有
        当前=取.get('chat')#聊天
    if 当前 is None:#尚空
        return None#不占位
    return 聊天节点(上下文,'turn-error',节点['seq'],节点,{'visibility':'hidden'})#隐藏占位

回合错定义={#终局回合失败节点
    'kind':'turn-error','target':'chat',#kind/目标
    'match':回合错匹配,'start':回合错开始,'update':回合错更新,'buildViewNode':回合错建视图,#生命周期
}#结束

def 登记回合错会话节点(上下文):#注册终局回合错误贡献
    """挂到 conversationEvents。"""
    上下文.conversationEvents.register(回合错定义)#登记
