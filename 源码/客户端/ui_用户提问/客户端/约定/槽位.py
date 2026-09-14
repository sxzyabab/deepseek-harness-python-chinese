__all__=[#仅中文公开名
    '计划审阅于',
    '待答提问',
    '提问错误',
]#公开面结束

def 计划审阅于(问题列表):#把请求收窄为可渲染的计划审阅
    """把请求收窄为可渲染的计划审阅，或返回 None 交给通用提问流。

    卡片是对一份计划的一次决策，只有当它能发出该请求允许的每一种答案时才认领——
    意图改的是布局，从不改哪些答案可达。因此批次必须是单条问题：声明该意图、
    把计划放在 detail、提供意图点名的批准标签，且是二元单选：批准之外至多一个选项，
    且不是多选。第三选项或多选批次有两个按钮表达不了的答案，因此留给通用流。
    """
    if 问题列表 is None or len(问题列表)!=1:#必须恰好一条问题
        return None#交给通用流
    题目=问题列表[0]#唯一那条问题
    if 'intent' not in 题目:#无展示意图
        return None#交给通用流
    意图=题目['intent']#展示意图
    if 意图 is None or 意图['kind']!='plan-review' or 'detail' not in 题目 or 题目['detail'] is None:#非计划审阅或无 detail
        return None#交给通用流
    if 'multiSelect' in 题目 and 题目['multiSelect'] is True:#多选无法用两按钮表达
        return None#交给通用流
    选项列表=题目['options'] if 'options' in 题目 and 题目['options'] is not None else []#选项列表
    if len(选项列表)>2:#超过两个选项留给通用流
        return None#交给通用流
    批准标签=意图['approve'] if 'approve' in 意图 else None#意图点名的批准标签
    批准=None#批准选项
    拒绝=None#拒绝选项
    for 选项 in 选项列表:#按标签找批准与拒绝
        if 选项['label']==批准标签:#命中批准
            批准=选项#记下批准选项
        else:#批准之外
            拒绝=选项#记下拒绝选项（若有）
    if 批准 is None:#没有批准选项则不认领
        return None#交给通用流
    审阅={#组装计划审阅
        'id':题目['id'],#问题 id
        'question':题目['question'],#问题文本
        'plan':题目['detail'],#计划 markdown
        'approve':批准,#批准选项
    }#审阅字段结束
    if 拒绝 is not None:#有拒绝选项才带上
        审阅['decline']=拒绝#拒绝选项
    return 审阅#收窄后的审阅

class 提问错误(Exception):
    """提问回执被拒绝。"""
    def __init__(自身,消息,原因=None):
        """记下英文消息与可选结构原因。"""
        super().__init__(消息)#消息原样英文
        自身.reason=原因#结构原因

class 待答提问:#载体上的提问域面
    """载体上的提问域面：渲染身份与问题列表透明转发；answer/cancel 拥有线路编码。载体为跨包 dict。"""
    def __init__(自身,等待):#持有提问载体
        """记下一次待答提问请求的运行时载体。"""
        自身.等待=等待#提问载体

    @property#只读属性
    def key(自身):#渲染身份
        """不透明渲染身份（草稿重挂轴），从载体转发。"""
        return 自身.等待['key']#转发载体 key

    @property#只读属性
    def questions(自身):#问题列表
        """该请求的问题列表，从载体载荷转发。"""
        return 自身.等待['payload']['questions']#转发载体载荷上的问题

    def answer(自身,答案):#投递整批答案
        """投递整批答案；被拒绝的载体回执会抛出。respond 返回任务。"""
        回执=自身.等待.respond({#投递成功应答
            'ok':True,#成功侧
            'value':{#应答值
                'sessionId':自身.等待['sessionId'],#会话 id
                'answer':答案,#整批答案
            },#value 结束
        }).等待()#respond 结束
        if 回执['accepted'] is not True:#回执未接受
            原因=回执['reason'] if 'reason' in 回执 else None#拒绝原因
            raise 提问错误('question response rejected: '+str(原因),原因=原因)#抛出拒绝原因

    def cancel(自身):#取消等待
        """拒绝整次等待（宿主把工具调用结算为已取消）；被拒绝的回执会抛出。respond 返回任务。"""
        回执=自身.等待.respond({#投递取消应答
            'ok':False,#失败侧
            'error':{#取消错误编码
                'code':'cancelled',#取消码
                'message':'the user closed this question request',#取消说明（字面量不译）
                'details':{},#无额外细节
            },#error 结束
        }).等待()#respond 结束
        if 回执['accepted'] is not True:#回执未接受
            原因=回执['reason'] if 'reason' in 回执 else None#拒绝原因
            raise 提问错误('question cancellation rejected: '+str(原因),原因=原因)#抛出拒绝原因
