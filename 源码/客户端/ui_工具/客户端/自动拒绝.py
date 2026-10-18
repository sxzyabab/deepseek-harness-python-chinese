import re
from .文案 import 中文文案

__all__=['归一自动拒绝原因','本地化自动拒绝']

空白行=re.compile(r'[\r\n\u2028\u2029]+')

def 归一自动拒绝原因(原因):
    '只整理给人看的文案。没有可见文本则为 None'
    if 原因 is None:
        return None
    整理=空白行.sub(' ',原因.strip())
    if 整理=='':
        return None
    return 整理

def 本地化自动拒绝(拒绝):
    '折叠身份与展开输出。文案用中文表原文'
    原因=归一自动拒绝原因(拒绝['reason'])
    if 原因 is None:
        原因=中文文案('tool.autoReviewReasonFallback')
    return {
        'summary':中文文案('tool.autoReviewRejected'),
        'output':中文文案('tool.autoReviewNotExecuted',{'reason':原因}),
    }
