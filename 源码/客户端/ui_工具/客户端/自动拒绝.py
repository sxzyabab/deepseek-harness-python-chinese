import re
from .调用模型 import 去掉绝对路径

__all__=['归一自动拒绝原因','本地化自动拒绝']

空白行=re.compile(r'[\r\n\u2028\u2029]+')

def 归一自动拒绝原因(原因):
    '只整理给人看的文案；耐久错误仍保留原始原因。无可见文本则 None'
    if 原因 is None:
        return None
    归一=空白行.sub(' ',原因.strip(),count=0)
    return None if 归一=='' else 归一

def 本地化自动拒绝(拒绝,翻译):
    '折叠身份与展开输出行。拒绝为与语言无关的事实；翻译走 conversation 命名空间'
    原因=归一自动拒绝原因(拒绝['reason'] if 'reason' in 拒绝 else None)
    if isinstance(原因,str):
        原因=去掉绝对路径(原因)
        if 原因=='':
            原因=None
    if 原因 is None:
        原因=翻译('tool.autoReviewReasonFallback')
    return {
        'summary':翻译('tool.autoReviewRejected'),
        'output':翻译('tool.autoReviewNotExecuted',{'reason':原因}),
    }
