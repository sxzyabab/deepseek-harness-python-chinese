from .节点工厂 import 聊天错误,聊天节点#聊天节点工厂
from .事件面 import 展示失败文案#面辅助

__all__=['回合错定义','登记回合错会话节点']#仅中文公开名

def 末步(上下文):#该回合最后一步号
    """非回合/步骤位置则 0。"""
    起点=上下文['start'] if 'start' in 上下文 else None#起点
    匹配列表=上下文['matches'] if 'matches' in 上下文 and 上下文['matches'] is not None else []#匹配
    if 起点 is not None and 'location' in 起点:#有起点
        位置=起点['location']#位置
    elif len(匹配列表)>0 and 'location' in 匹配列表[0]:#首匹配
        位置=匹配列表[0]['location']#位置
    else:#无
        位置=None#无
    if 位置 is None or 'kind' not in 位置 or 位置['kind'] not in ('turn','step'):#非
        return 0#零
    回合=位置['turn'] if 'turn' in 位置 else None#回合
    步列表=回合['steps'] if 回合 is not None and 'steps' in 回合 and 回合['steps'] is not None else []#步列表
    if len(步列表)==0:#空
        return 0#零
    末=步列表[-1]#末步
    return 末['step'] if 'step' in 末 else 0#末步

def 重试回合(事件):#事件是否属于某回合的重试
    """llm/retry 或 llm/retry-started。"""
    种=事件['type']#种
    if 种 in ('llm/retry','llm/retry-started'):#重试
        数据=事件['data'] if 'data' in 事件 else {}#载荷
        return 数据['turn'] if 'turn' in 数据 else None#回合号
    return None#非

def 自匹配抽失败(匹配项):#从匹配抽出失败快照
    """仅 turn/end 且 reason.kind==error。"""
    事件=匹配项['event']#事件
    if 事件['type']!='turn/end':#非
        return None#无
    数据=事件['data'] if 'data' in 事件 else {}#载荷
    原因=数据['reason'] if 'reason' in 数据 and 数据['reason'] is not None else {}#原因
    if 'kind' not in 原因 or 原因['kind']!='error':#非错误
        return None#无
    失败=原因['error'] if 'error' in 原因 and 原因['error'] is not None else {}#错误对象
    出={'seq':事件['seq'],'time':事件['time'] if 'time' in 事件 else None,'message':展示失败文案(失败)}#快照
    if 'code' in 失败 and 失败['code'] is not None:#有码
        出['code']=失败['code']#带上
    return 出#失败快照

def 回放回合错(上下文):#从匹配回退拼状态
    """有重试链则 hidden。"""
    匹配列表=上下文['matches'] if 'matches' in 上下文 and 上下文['matches'] is not None else []#匹配
    结束=None#带失败
    for 候 in 匹配列表:#扫
        if 自匹配抽失败(候) is not None:#命中
            结束=候#记下
            break#停
    if 结束 is None or 结束['event']['type']!='turn/end':#无
        return None#放弃
    失败=自匹配抽失败(结束)#快照
    if 失败 is None:#无
        return None#放弃
    数据=结束['event']['data'] if 'data' in 结束['event'] else {}#载荷
    回合=数据['turn'] if 'turn' in 数据 else None#回合号
    隐藏=False#默认
    for 候 in 匹配列表:#扫重试
        if 重试回合(候['event'])==回合:#同回合
            隐藏=True#隐藏
            break#停
    return {'turn':回合,'hidden':隐藏,'failure':失败}#回退态

def 回合错匹配(事件):#按事件认领或更新本节点
    """turn/start 开；错误收尾与重试更新。"""
    种=事件['type']#种
    数据=事件['data'] if 'data' in 事件 else {}#载荷
    if 种=='turn/start':#回合开始
        return {'id':str(数据['turn']),'role':'start'}#开
    原因=数据['reason'] if 'reason' in 数据 else None#原因
    if 种=='turn/end' and 原因 is not None and 'kind' in 原因 and 原因['kind']=='error':#错误收尾
        return {'id':str(数据['turn']),'role':'update'}#更新
    回合=重试回合(事件)#重试回合
    return None if 回合 is None else {'id':str(回合),'role':'update'}#有则更新

def 回合错开始(_上下文,匹配项):#从 turn/start 建初始状态
    """必须是 turn/start。"""
    事件=匹配项['event']#事件
    if 事件['type']!='turn/start':#非
        raise 聊天错误('turn-error start requires turn/start')#硬失败
    数据=事件['data'] if 'data' in 事件 else {}#载荷
    return {'turn':数据['turn'] if 'turn' in 数据 else None,'hidden':False}#初态

def 回合错更新(上下文,匹配项):#写入失败或因重试隐藏
    """失败快照或 hidden。"""
    态=上下文['state']#态
    失败=自匹配抽失败(匹配项)#失败
    if 失败 is not None:#有
        return {**态,'failure':失败}#记下
    if 重试回合(匹配项['event'])==(态['turn'] if 'turn' in 态 else None):#本回合重试
        return {**态,'hidden':True}#隐藏
    return 态#无关

def 回合错建视图(上下文):#拼最终聊天节点
    """无失败则不渲染；隐藏仍可占位。"""
    态=上下文['state'] if 'state' in 上下文 else None#态
    if 态 is None:#无
        态=回放回合错(上下文)#回放
    if 态 is None or 'failure' not in 态 or 态['failure'] is None:#无失败
        return None#不建
    失败=态['failure']#快照
    节点={'kind':'turn-error','seq':失败['seq'],'time':失败['time'],'turn':态['turn'],'step':末步(上下文),'message':失败['message']}#载荷
    if 'code' in 失败 and 失败['code'] is not None:#有码
        节点['code']=失败['code']#带上
    if 'hidden' not in 态 or not 态['hidden']:#未隐藏
        return 聊天节点(上下文,'turn-error',节点['seq'],节点)#可见
    当前=None#已有
    取=上下文['current'] if 'current' in 上下文 else None#current
    if 取 is not None and 'chat' in 取:#有
        当前=取['chat']#聊天
    if 当前 is None:#尚空
        return None#不占位
    return 聊天节点(上下文,'turn-error',节点['seq'],节点,{'visibility':'hidden'})#隐藏占位

回合错定义={#终局回合失败节点
    'kind':'turn-error','target':'chat',#kind/目标
    'match':回合错匹配,'start':回合错开始,'update':回合错更新,'buildViewNode':回合错建视图,#生命周期
}#结束

def 登记回合错会话节点(上下文):#注册终局回合错误贡献
    """挂到 uiConversation.events。"""
    上下文.uiConversation.events.register(回合错定义)#登记
