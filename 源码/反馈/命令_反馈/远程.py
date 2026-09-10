"""会话反馈 Host-for-Client Remote 贡献（对齐上游 `./remote`）。

对照 `@Remote`：`record`。服务键与命名空间均为 `sessionFeedback`。
"""
from ...typert.协议 import 严格编解码,调用描述符,远程贡献#制品辅助

__all__=['TYPERT_REMOTE','默认','远程贡献对象']#公开面

包名='@deepseek-ai/dsh-command-feedback'#上游包名
服务='sessionFeedback'#服务键
命名空间='sessionFeedback'#命名空间
类前=包名+'#SessionFeedbackService.'#调用 id 前缀

记录描述符=调用描述符(#record
    类前+'record',服务,命名空间,'record',
    [{'name':'request','wire':'request','source':'json','codec':严格编解码('SessionFeedbackRecordRequest')}],
    严格编解码('SessionFeedbackRecordResult'),
    {'file':'src/index.ts','line':100,'column':3},
)#结束

TYPERT_REMOTE=远程贡献(包名,[记录描述符])#贡献
远程贡献对象=TYPERT_REMOTE#中文别名
默认=TYPERT_REMOTE#default
