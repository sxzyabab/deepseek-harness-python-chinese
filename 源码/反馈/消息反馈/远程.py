"""消息反馈 Host-for-Client Remote 贡献（对齐上游 `./remote`）。

对照 `@Remote`：`list` / `put` / `delete`。服务键与命名空间均为 `messageFeedback`。
宿主存储域依赖另面；本文件落盘可挂载的贡献描述符。
"""
from typert.protocol import 严格编解码,调用描述符,远程贡献#制品辅助

__all__=['TYPERT_REMOTE','默认','远程贡献对象']#公开面

包名='@deepseek-ai/dsh-message-feedback'#上游包名
服务='messageFeedback'#服务键
命名空间='messageFeedback'#命名空间
类前=包名+'#MessageFeedbackService.'#调用 id 前缀

列表描述符=调用描述符(#list
    类前+'list',服务,命名空间,'list',
    [{'name':'request','wire':'request','source':'json','codec':严格编解码('MessageFeedbackListRequest')}],
    严格编解码('MessageFeedbackListResult'),
    {'file':'src/index.ts','line':188,'column':3},
)#结束

写入描述符=调用描述符(#put
    类前+'put',服务,命名空间,'put',
    [{'name':'request','wire':'request','source':'json','codec':严格编解码('MessageFeedbackPutRequest')}],
    严格编解码('MessageFeedbackPutResult'),
    {'file':'src/index.ts','line':202,'column':3},
)#结束

删除描述符=调用描述符(#delete
    类前+'delete',服务,命名空间,'delete',
    [{'name':'request','wire':'request','source':'json','codec':严格编解码('MessageFeedbackDeleteRequest')}],
    严格编解码('MessageFeedbackDeleteResult'),
    {'file':'src/index.ts','line':267,'column':3},
)#结束

TYPERT_REMOTE=远程贡献(包名,[列表描述符,写入描述符,删除描述符])#贡献
远程贡献对象=TYPERT_REMOTE#中文别名
默认=TYPERT_REMOTE#default
