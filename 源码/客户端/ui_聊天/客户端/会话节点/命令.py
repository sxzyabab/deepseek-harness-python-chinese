from .....内核.会话.表面 import 是否替换表面事件
from .....内核.会话.类型 import 安全整数上限
from ...异常 import 聊天错误
from .节点工厂 import 聊天节点

__all__=['压缩来源','压缩摘要','更新压缩状态','命令定义']

压缩种类='compact-checkpoint'


def 是安全非负整数(值):
    'JS 安全整数，且不小于 0。布尔不算'
    if isinstance(值,bool) or not isinstance(值,int):
        return False
    return 值>=0 and 值<=安全整数上限


def 自运行(匹配项):
    'command/run 折成命令节点'
    事件=匹配项['event']
    if 事件.get('type')!='command/run':
        raise 聊天错误('command start requires command/run')
    数据=事件.get('data') if isinstance(事件.get('data'),dict) else {}
    return {
        'kind':'command',
        'seq':事件.get('seq'),
        'time':事件.get('time'),
        'commandId':数据.get('commandId'),
        'name':数据.get('name'),
        'args':数据.get('args') if 数据.get('args') is not None else None,
        'outcome':None,
    }


def 自完成(匹配项,先前=None):
    'command/done 折成命令节点。成功且序号合法才留下 sourceEventSeq'
    事件=匹配项['event']
    if 事件.get('type')!='command/done':
        raise 聊天错误('command update requires command/done')
    数据=事件.get('data') if isinstance(事件.get('data'),dict) else {}
    源序号=数据.get('sourceEventSeq')
    if not (数据.get('kind')=='success' and 是安全非负整数(源序号)):
        源序号=None
    结果={
        'kind':数据.get('kind'),
    }
    if 'text' in 数据:
        结果['text']=数据['text']
    if 源序号 is not None:
        结果['sourceEventSeq']=源序号
    return {
        'kind':'command',
        'seq':先前.get('seq') if isinstance(先前,dict) and 'seq' in 先前 else 事件.get('seq'),
        'time':先前.get('time') if isinstance(先前,dict) and 'time' in 先前 else 事件.get('time'),
        'commandId':数据.get('commandId'),
        'name':先前.get('name') if isinstance(先前,dict) and 先前.get('name') is not None else None,
        'args':先前.get('args') if isinstance(先前,dict) and 'args' in 先前 else None,
        'outcome':结果,
    }


def 压缩来源(事件):
    '替换检查点上的压缩身份和可选命令身份'
    if 事件.get('type')!='user/message' or not 是否替换表面事件(事件):
        return None
    数据=事件.get('data') if isinstance(事件.get('data'),dict) else {}
    来源=数据.get('source') if isinstance(数据.get('source'),dict) else {}
    if 来源.get('kind')!=压缩种类 or not isinstance(来源.get('compactionId'),str):
        return None
    结果={'compactionId':来源['compactionId']}
    if 'sourceCommandId' in 来源:
        结果['sourceCommandId']=来源['sourceCommandId']
    return 结果


def 压缩摘要(匹配项,检查点):
    '有摘要事件就读文本和被挡住的条数、token。没有就只留检查点位置'
    摘要=None
    挡住条数=None
    挡住令牌=None
    if isinstance(匹配项,dict) and isinstance(匹配项.get('event'),dict) and 匹配项['event'].get('type')=='compaction/summary':
        数据=匹配项['event'].get('data') if isinstance(匹配项['event'].get('data'),dict) else {}
        if isinstance(数据.get('summary'),list):
            文本=''.join(块.get('text') if isinstance(块,dict) and 块.get('type')=='text' else '' for 块 in 数据['summary'])
            摘要=None if 文本.strip()=='' else 文本
        序号表=数据.get('shadowedSeqs')
        if isinstance(序号表,list) and all(是安全非负整数(序号) for 序号 in 序号表):
            挡住条数=len(序号表)
        if 是安全非负整数(数据.get('shadowedTokenCount')):
            挡住令牌=数据['shadowedTokenCount']
    检查点事件=检查点['event']
    return {
        'kind':'compaction',
        'seq':检查点事件.get('seq'),
        'time':检查点事件.get('time'),
        'summary':摘要,
        'summaryEventSeq':匹配项['event'].get('seq') if isinstance(匹配项,dict) and isinstance(匹配项.get('event'),dict) else None,
        'shadowedItemCount':挡住条数,
        'shadowedTokenCount':挡住令牌,
    }


def 更新压缩状态(状态,匹配项):
    '把共享的压缩证据折进定义自己的状态。没有新证据就保持原引用'
    事件=匹配项.get('event') if isinstance(匹配项,dict) else None
    if isinstance(事件,dict) and 事件.get('type')=='compaction/summary':
        下一=dict(状态)
        下一['summary']=匹配项
        return 下一
    if isinstance(事件,dict) and 压缩来源(事件) is not None:
        下一=dict(状态)
        下一['checkpoint']=匹配项
        return 下一
    return 状态


def 命令匹配(事件):
    '命令运行、完成，以及挂在命令上的压缩事件'
    if 事件.get('type')=='command/run':
        return {'id':str(事件['data']['commandId']),'role':'start'}
    if 事件.get('type')=='command/done':
        return {'id':str(事件['data']['commandId']),'role':'update'}
    检查点=压缩来源(事件)
    if isinstance(检查点,dict) and 检查点.get('sourceCommandId') is not None:
        return {'id':str(检查点['sourceCommandId']),'role':'update'}
    if 事件.get('type') in ('compaction/start','compaction/summary','compaction/end'):
        数据=事件.get('data') if isinstance(事件.get('data'),dict) else {}
        if 数据.get('sourceCommandId') is not None:
            return {'id':str(数据['sourceCommandId']),'role':'update'}
    return None


def 命令开始(上下文,匹配项):
    '从 command/run 建立状态'
    return {'command':自运行(匹配项)}


def 命令更新(上下文,匹配项):
    '完成事件改命令。其余压缩事件并进同一状态'
    事件=匹配项.get('event') if isinstance(匹配项,dict) else None
    状态=上下文.get('state') if isinstance(上下文,dict) else {}
    if isinstance(事件,dict) and 事件.get('type')=='command/done':
        下一=dict(状态)
        下一['command']=自完成(匹配项,状态.get('command') if isinstance(状态,dict) else None)
        return 下一
    return 更新压缩状态(状态 if isinstance(状态,dict) else {},匹配项)


def 命令回退状态(上下文):
    '没有状态时从已加载匹配里补命令和压缩证据'
    匹配=上下文.get('matches') if isinstance(上下文.get('matches'),list) else []
    完成=None
    检查点=None
    摘要=None
    for 项 in 匹配:
        事件=项.get('event') if isinstance(项,dict) else None
        if not isinstance(事件,dict):
            continue
        if 完成 is None and 事件.get('type')=='command/done':
            完成=项
        if 检查点 is None and 压缩来源(事件) is not None:
            检查点=项
        if 摘要 is None and 事件.get('type')=='compaction/summary':
            摘要=项
    if 检查点 is None:
        if 完成 is None:
            return None
        return {'command':自完成(完成)}
    来源=压缩来源(检查点['event'])
    if not isinstance(来源,dict) or 来源.get('sourceCommandId') is None:
        if 完成 is None:
            return None
        return {'command':自完成(完成)}
    if 完成 is None:
        事件=检查点['event']
        命令={
            'kind':'command',
            'seq':事件.get('seq'),
            'time':事件.get('time'),
            'commandId':来源['sourceCommandId'],
            'name':'compact',
            'args':None,
            'outcome':None,
        }
    else:
        命令=自完成(完成)
        命令['name']='compact'
    状态={'command':命令,'checkpoint':检查点}
    if 摘要 is not None:
        状态['summary']=摘要
    return 状态


def 命令建视图(上下文):
    '普通命令直接成行。compact 再带上压缩摘要'
    状态=上下文.get('state')
    if 状态 is None:
        状态=命令回退状态(上下文)
    if not isinstance(状态,dict):
        return None
    命令=状态.get('command') if isinstance(状态.get('command'),dict) else {}
    if 命令.get('name')!='compact':
        return 聊天节点(上下文,'command',命令.get('seq'),命令)
    压缩=None
    if 状态.get('checkpoint') is not None:
        压缩=压缩摘要(状态.get('summary'),状态['checkpoint'])
    数据={'command':命令,'compaction':压缩}
    锚=压缩.get('seq') if isinstance(压缩,dict) else 命令.get('seq')
    return 聊天节点(上下文,'manual-compaction',锚,数据)


命令定义={
    'kind':'command',
    'target':'chat',
    'match':命令匹配,
    'start':命令开始,
    'update':命令更新,
    'buildViewNode':命令建视图,
}
