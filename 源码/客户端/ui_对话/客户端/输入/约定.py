"""冻结的输入机约定（类型与队列投影面）。

对齐上游 `ui-conversation/src/client/input/contract.ts`。公开面仅中文名。
含 steerQueue（空草稿加速 Enter / 整队转向）与 InputState.queue。
机事件/效应以判别标签 `type` 的 dict 载荷表达。
"""
from ..约定.队列 import 队列行#队列行

__all__=[#公开面
    '草稿附件标识','输入目标','会话输入','会话输入解析','输入动作','输入通知',
    '撰写键盘','排队消息','编辑选区','编辑范围','出现','粘贴分量','粘贴尝试态',
    '输入机选项','输入状态','提交尝试','输入相位表','空输入状态','占位符',
    '输入事件种','输入效应种',
]#公开面结束

草稿附件标识=str#浏览器草稿图 id
排队消息=队列行#瞬时队列投影行
输入相位表=('plain','adjudicating','claimed','submitting')#相位
占位符='\ufffc'#U+FFFC 芯片占位

#编辑选区：半开 [start, end)
#编辑范围：选区 + insertedLength
#出现：U+FFFC 芯片一次出现
#粘贴分量 / 粘贴尝试态 / 提交尝试：机事件载荷形
编辑选区=dict#选区形
编辑范围=dict#编辑形
出现=dict#出现形
粘贴分量=dict#粘贴分量形
粘贴尝试态=dict#粘贴尝试形
提交尝试=dict#提交尝试形
输入通知=dict#level/text/seq
输入目标=dict#beginCommand/insertReference
会话输入=dict#每会话门面
会话输入解析=dict#for(actx)
输入动作=dict#公开 setDraft/addImages/…
撰写键盘=dict#含 steerQueue 的私有键盘面
输入机选项=dict#mergeWindowMs/now
输入状态=dict#draft/imageIds/phase/queue/…

输入事件种=(#机唯一写路径判别标签
    'draft-changed','begin-command','insert-ref','consume-token','set-invalid',
    'undo','redo','paste-begin','paste-upgrade','invalidate-paste','enter',
    'adjudicated','adjudication-failed','submit-settled','send-committed','release',
)#事件种结束

输入效应种=(#外壳执行的效应判别标签
    'adjudicate','begin-submit','default-sink','notice',
)#效应种结束

def 空输入状态():#初值
    """无草稿、无图、plain、空队列。"""
    return {#态
        'draft':'',#草稿
        'imageIds':[],#图
        'draftRev':0,#修订
        'phase':'plain',#相位
        'occurrences':[],#出现
        'queue':[],#队列
    }#结束
