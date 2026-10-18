'一场会话的反馈对话框和轻提示。同一张表服务会话备注和单条消息'
from ...存储 import 创建快照存储

__all__=['反馈对话框控制器']

def 空草稿(轻提示,目标=None):
    '关掉的对话框。轻提示序号单独带上'
    return {
        'target':目标,
        'category':None,
        'text':'',
        'submitting':False,
        'failure':None,
        'toast':轻提示,
    }

class 反馈对话框控制器:
    '一场会话一份对话框。覆盖层和每条消息的入口都用它'
    def __init__(自身,提交):
        '提交按目标把草稿记下去，返回动作结果'
        自身._提交=提交
        自身.状态=创建快照存储(空草稿(0))
        自身.代数=0
        自身.轻提示序号=0

    def 打开(自身,目标):
        '用空草稿打开，换掉当前已经打开的草稿。屏幕上的轻提示留着'
        自身.代数+=1
        自身.状态.set(空草稿(自身.状态.getSnapshot()['toast'],目标))

    def 关闭(自身):
        '关掉对话框并丢掉草稿。屏幕上的轻提示留着'
        自身.代数+=1
        自身.状态.set(空草稿(自身.状态.getSnapshot()['toast']))

    def 编辑(自身,草稿):
        '可编辑时替换分类或正文。提交途中和关掉之后忽略'
        当前=自身.状态.getSnapshot()
        if 当前['target'] is None or 当前['submitting']:
            return
        下一=dict(当前)
        下一.update(草稿)
        自身.状态.set(下一)

    def 提交草稿(自身):
        '空草稿也允许提交。成功就关掉并拉起轻提示，失败留下失败码'
        当前=自身.状态.getSnapshot()
        if 当前['target'] is None or 当前['submitting']:
            return
        代数=自身.代数
        下一=dict(当前)
        下一['submitting']=True
        下一['failure']=None
        自身.状态.set(下一)
        正文=当前['text'].strip()
        条目={}
        if len(正文)>0:
            条目['text']=正文
        if 当前['category'] is not None:
            条目['category']=当前['category']
        结果=自身._提交(当前['target'],条目)
        if 结果['ok']:
            if 代数==自身.代数:
                自身.关闭()
            自身.轻提示序号+=1
            快照=dict(自身.状态.getSnapshot())
            快照['toast']=自身.轻提示序号
            自身.状态.set(快照)
            return
        if 代数!=自身.代数:
            return
        失败后=dict(自身.状态.getSnapshot())
        失败后['submitting']=False
        失败后['failure']=结果['error']['code']
        失败后['toast']=0
        自身.状态.set(失败后)

    def 关掉失败(自身):
        '清掉当前失败轻提示，不关掉草稿'
        当前=自身.状态.getSnapshot()
        下一=dict(当前)
        下一['failure']=None
        自身.状态.set(下一)

    def 退役轻提示(自身,序号):
        '淡出的是这一条才清掉。更新的轻提示留着'
        当前=自身.状态.getSnapshot()
        if 当前['toast']==序号:
            下一=dict(当前)
            下一['toast']=0
            自身.状态.set(下一)

    def 拆除(自身):
        '丢掉草稿和轻提示。还在飞的提交回来时会对不上代数'
        自身.代数+=1
        自身.状态.set(空草稿(0))
