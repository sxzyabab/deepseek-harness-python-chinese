'一份调用方自己的原文协调。失败时不发布半截结果'
from ...异常 import 用户文本变换错误,对话错误

__all__=['用户文本文档']

def 文本节点(文本,起,止):
    '一段未解释的原文'
    return {'id':'text','start':起,'end':止,'data':{'text':文本[起:止]}}

def 校验候选(文本,规则标识,从,节点):
    '范围必须非空，且落在从这里到文末'
    起=节点.get('start')
    止=节点.get('end')
    if not isinstance(起,int) or not isinstance(止,int) or isinstance(起,bool) or isinstance(止,bool):
        raise 对话错误('invalid candidate range')
    if 起<从 or 止<=起 or 止>len(文本):
        raise 对话错误('invalid candidate range ['+str(起)+', '+str(止)+'); expected a nonempty range from '+str(从)+' to '+str(len(文本)))
    if 节点['id']=='text':
        if 节点['data']['text']!=文本[起:止]:
            raise 对话错误('text candidate must preserve its original substring')
    elif 节点['id']!=规则标识:
        raise 对话错误('candidate must use rule ID "'+规则标识+'" or text')

class 用户文本文档:
    '按当前规则把原文收成有序节点'
    def __init__(自身):
        '还没有文本'
        自身.求值中=False

    def 求值(自身,输入,规则列):
        '失败则抛出，不返回半截'
        if 自身.求值中:
            raise 对话错误('user-text document evaluation cannot be reentrant')
        自身.求值中=True
        try:
            return 自身.协调(输入,规则列)
        finally:
            自身.求值中=False

    def 协调(自身,输入,规则列):
        '优先级靠前的规则在同一起点上获胜'
        节点列=[]
        游标=0
        文本=输入['text']
        while True:
            胜者=None
            for 规则 in 规则列:
                已读={}
                开着=True
                def 读(键,已读=已读):
                    '只在匹配期间读事实'
                    nonlocal 开着
                    if not 开着:
                        raise 对话错误('user-text transform context is closed; read is synchronous only')
                    值=输入['facts'].get(键) if isinstance(输入.get('facts'),dict) else None
                    已读[键]=值
                    return 值
                try:
                    候选=规则['match'](文本,游标,{'read':读})
                except Exception as 原因:
                    raise 用户文本变换错误(规则['id'],原因)
                finally:
                    开着=False
                if 候选 is None:
                    continue
                校验候选(文本,规则['id'],游标,候选)
                if 胜者 is None or 候选['start']<胜者['start']:
                    胜者=候选
            if 胜者 is None:
                if 游标<len(文本):
                    节点列.append(文本节点(文本,游标,len(文本)))
                return 节点列
            if 游标<胜者['start']:
                节点列.append(文本节点(文本,游标,胜者['start']))
            节点列.append(胜者)
            游标=胜者['end']

    def evaluate(自身,输入,规则列):
        '与上游方法名相同'
        return 自身.求值(输入,规则列)
