"""提问撰写器槽约定：登记方对会话拥有的 `conversation.composer` 槽的 props 合成，外加运行时载体对象上的提问域面。

载体（PendingWait）只拥有信封运输；提问协议——答案值形状、取消错误编码、回执检查——住在这里，与消费它的包在一起。

对齐上游 `ui-user-questions/src/client/contract/slots.ts`。公开面仅中文名。
"""
from .....依赖 import cordis#外部依赖胶水
__all__=[#仅中文公开名
    '取字段',
    '解开',
    '计划审阅于',
    '待答提问',
]#公开面结束

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段，缺席为缺省。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 解开(值):#承诺则等待否则原样
    """承诺则等待，否则原样返回。"""
    if 是否thenable(值):#可等待
        return 值.等待()#等待承诺
    return 值#同步值

def 计划审阅于(问题们):#把请求收窄为可渲染的计划审阅
    """把请求收窄为可渲染的计划审阅，或返回 None 交给通用提问流。

    卡片是对一份计划的一次决策，只有当它能发出该请求允许的每一种答案时才认领——
    意图改的是布局，从不改哪些答案可达。因此批次必须是单条问题：声明该意图、
    把计划放在 detail、提供意图点名的批准标签，且是二元单选：批准之外至多一个选项，
    且不是多选。第三选项或多选批次有两个按钮表达不了的答案，因此留给通用流。
    """
    if 问题们 is None or len(问题们)!=1:#必须恰好一条问题
        return None#交给通用流
    题目=问题们[0]#唯一那条问题
    意图=取字段(题目,'intent')#展示意图
    if 取字段(意图,'kind')!='plan-review' or 取字段(题目,'detail') is None:#非计划审阅或无 detail
        return None#交给通用流
    if 取字段(题目,'multiSelect') is True:#多选无法用两按钮表达
        return None#交给通用流
    选项们=取字段(题目,'options')#选项列表
    if 选项们 is None:#缺省空
        选项们=[]#空列表
    if len(选项们)>2:#超过两个选项留给通用流
        return None#交给通用流
    批准标签=取字段(意图,'approve')#意图点名的批准标签
    批准=None#批准选项
    拒绝=None#拒绝选项
    for 选项 in 选项们:#按标签找批准与拒绝
        if 取字段(选项,'label')==批准标签:#命中批准
            批准=选项#记下批准选项
        else:#批准之外
            拒绝=选项#记下拒绝选项（若有）
    if 批准 is None:#没有批准选项则不认领
        return None#交给通用流
    审阅={#组装计划审阅
        'id':取字段(题目,'id'),#问题 id
        'question':取字段(题目,'question'),#问题文本
        'plan':取字段(题目,'detail'),#计划 markdown
        'approve':批准,#批准选项
    }#审阅字段结束
    if 拒绝 is not None:#有拒绝选项才带上
        审阅['decline']=拒绝#拒绝选项
    return 审阅#收窄后的审阅

class 待答提问:#载体上的提问域面
    """载体上的提问域面：渲染身份与问题列表透明转发；answer/cancel 拥有线路编码。"""
    def __init__(自身,等待):#持有提问载体
        """记下一次待答提问请求的运行时载体。"""
        自身.等待=等待#提问载体

    @property#只读属性
    def key(自身):#渲染身份
        """不透明渲染身份（草稿重挂轴），从载体转发。"""
        return 取字段(自身.等待,'key')#转发载体 key

    @property#只读属性
    def questions(自身):#问题列表
        """该请求的问题列表，从载体载荷转发。"""
        return 取字段(取字段(自身.等待,'payload'),'questions')#转发载体载荷上的问题

    def answer(自身,答案):#投递整批答案
        """投递整批答案；被拒绝的载体回执会抛出。"""
        回执=解开(自身.等待.respond({#投递成功应答
            'ok':True,#成功侧
            'value':{#应答值
                'sessionId':取字段(自身.等待,'sessionId'),#会话 id
                'answer':答案,#整批答案
            },#value 结束
        }))#respond 结束
        if not 取字段(回执,'accepted'):#回执未接受
            raise Exception('question response rejected: '+str(取字段(回执,'reason')))#抛出拒绝原因

    def cancel(自身):#取消等待
        """拒绝整次等待（宿主把工具调用结算为已取消）；被拒绝的回执会抛出。"""
        回执=解开(自身.等待.respond({#投递取消应答
            'ok':False,#失败侧
            'error':{#取消错误编码
                'code':'cancelled',#取消码
                'message':'the user closed this question request',#取消说明（字面量不译）
                'details':{},#无额外细节
            },#error 结束
        }))#respond 结束
        if not 取字段(回执,'accepted'):#回执未接受
            raise Exception('question cancellation rejected: '+str(取字段(回执,'reason')))#抛出拒绝原因
