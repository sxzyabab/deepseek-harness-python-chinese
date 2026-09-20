from ...typert.协议 import 严格编解码,调用描述符,远程贡献#制品辅助

__all__=['默认','远程贡献表']#仅中文公开名；TYPERT_REMOTE 为 typert 框架槽不入表

包名='@deepseek-ai/dsh-message-feedback'服务='messageFeedback'#服务键
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

远程贡献表=远程贡献(包名,[列表描述符,写入描述符,删除描述符])#贡献
默认=远程贡献表
TYPERT_REMOTE=远程贡献表#typert框架槽
