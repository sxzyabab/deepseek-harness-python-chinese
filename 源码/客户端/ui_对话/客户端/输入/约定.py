__all__=[#公开面
    '草稿附件标识','输入目标','会话输入','会话输入解析','输入动作','输入通知',
    '撰写键盘','编辑选区','编辑范围','出现','粘贴分量','粘贴尝试态',
    '输入机选项','输入状态','提交尝试','输入相位表','空输入状态','占位符',
    '输入事件种','输入效应种',
]#公开面结束

草稿附件标识=str#浏览器草稿图 id
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
会话输入=dict#每会话门面（含 focus）
会话输入解析=dict#按作用域取门面(actx)
输入动作=dict#公开 setDraft/addImages/…
撰写键盘=dict#含 steerQueue、bindFilePicker 的私有键盘面
输入机选项=dict#mergeWindowMs/now
输入状态=dict#draft/attachmentIds/phase/queue(=InboxState next-turn)/claim.name/…

#命令认领：name 目录名 / token 展示拼写 / hint? / attachments? / submit
#触发控制器另含 openReference(来源,引用)→是否打开预览

输入事件种=(#机唯一写路径判别标签
    'draft-changed','begin-command','insert-ref','consume-token','set-invalid',
    'undo','redo','paste-begin','paste-upgrade','invalidate-paste','enter',
    'adjudicated','adjudication-failed','submit-settled','send-committed','release',
)#事件种结束

输入效应种=(#外壳执行的效应判别标签
    'adjudicate','begin-submit','default-sink','notice',
)#效应种结束

def 空输入状态():#初值
    """无草稿、无附件、plain、空排队（对齐 InboxState next-turn）。"""
    return {#态
        'draft':'',#草稿
        'attachmentIds':[],#附件
        'draftRev':0,#修订
        'phase':'plain',#相位
        'occurrences':[],#出现
        'queue':[],#排队
    }#结束
