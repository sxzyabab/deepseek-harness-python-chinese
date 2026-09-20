import re#压空白行

__all__=['归一自动拒绝原因','本地化自动拒绝']#仅中文公开名

空白行=re.compile(r'[\r\n\u2028\u2029]+')#行分隔压成空格

def 归一自动拒绝原因(原因):
    """只整理给人看的文案；耐久错误仍保留原始原因。无可见文本则 None。"""
    if 原因 is None:#未记录
        return None#无
    归一=空白行.sub(' ',原因.strip(),count=0)#压行分隔
    return None if 归一=='' else 归一#空则无

def 本地化自动拒绝(拒绝,翻译):
    """折叠身份与展开 OUT 行。拒绝为 locale-neutral 事实；翻译走 conversation 命名空间。"""
    原因=归一自动拒绝原因(拒绝['reason'] if 'reason' in 拒绝 else None)#原始原因
    if 原因 is None:#无可见原因
        原因=翻译('tool.autoReviewReasonFallback')#回退文案
    return {#展示
        'summary':翻译('tool.autoReviewRejected'),#折叠摘要
        'output':翻译('tool.autoReviewNotExecuted',{'reason':原因}),#展开行
    }
