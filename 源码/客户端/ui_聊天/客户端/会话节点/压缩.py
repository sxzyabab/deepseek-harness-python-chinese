from .命令 import 压缩来源,压缩摘要,更新压缩状态
from .节点工厂 import 聊天节点

__all__=['压缩定义']


def 压缩匹配(事件):
    '自动压缩。已经挂在命令上的检查点不认'
    检查点=压缩来源(事件)
    if isinstance(检查点,dict) and 检查点.get('sourceCommandId') is None:
        return {'id':检查点['compactionId'],'role':'update'}
    if 事件.get('type') in ('compaction/start','compaction/summary','compaction/end'):
        数据=事件.get('data') if isinstance(事件.get('data'),dict) else {}
        if 数据.get('sourceCommandId') is not None:
            return None
        标识=数据.get('compactionId')
        if not isinstance(标识,str) or 标识=='':
            return None
        return {'id':标识,'role':'start' if 事件.get('type')=='compaction/start' else 'update'}
    return None


def 压缩开始(上下文=None,匹配项=None):
    '自动压缩从空状态开始'
    return {}


def 压缩更新(上下文,匹配项):
    '后续摘要和检查点并进同一状态'
    状态=上下文.get('state') if isinstance(上下文,dict) else {}
    return 更新压缩状态(状态 if isinstance(状态,dict) else {},匹配项)


def 压缩回退(上下文):
    '没有状态时从已加载匹配里找摘要和检查点'
    匹配=上下文.get('matches') if isinstance(上下文.get('matches'),list) else []
    摘要=None
    检查点=None
    for 项 in 匹配:
        事件=项.get('event') if isinstance(项,dict) else None
        if not isinstance(事件,dict):
            continue
        if 摘要 is None and 事件.get('type')=='compaction/summary':
            摘要=项
        if 检查点 is None and 压缩来源(事件) is not None:
            检查点=项
    状态={}
    if 摘要 is not None:
        状态['summary']=摘要
    if 检查点 is not None:
        状态['checkpoint']=检查点
    return 状态


def 压缩建视图(上下文):
    '检查点落地才画出压缩标记'
    状态=上下文.get('state')
    if not isinstance(状态,dict):
        状态=压缩回退(上下文)
    if 状态.get('checkpoint') is None:
        return None
    标记=压缩摘要(状态.get('summary'),状态['checkpoint'])
    return 聊天节点(上下文,'compaction',标记.get('seq'),标记)


压缩定义={
    'kind':'compaction',
    'target':'chat',
    'match':压缩匹配,
    'start':压缩开始,
    'update':压缩更新,
    'buildViewNode':压缩建视图,
}
