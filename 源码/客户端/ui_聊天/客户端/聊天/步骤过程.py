__all__=['过程标题']

def 过程标题(摘要,翻译):
    """闭合组用前三类活动拼本地化标题，不含计数。摘要为 dict。"""
    标签表=[翻译('message.stepProcess.done.'+项['kind']) for 项 in 摘要['counts'][:3]]
    if len(标签表)==0:
        return 翻译('message.stepProcess.done.thinking')
    首=标签表[0]
    def 续写(标签):
        """首字母小写以接入并列。"""
        if 标签=='':
            return 标签
        return 标签[0].lower()+标签[1:]
    if len(标签表)==1:
        return 首
    次=标签表[1]
    if len(标签表)==2:
        前缀=翻译('message.stepProcess.sharedPrefix')
        共用=前缀!='' and 首.startswith(前缀) and 次.startswith(前缀)
        第二=续写(次[len(前缀):] if 共用 else 次)
        return 翻译('message.stepProcess.joinTwo',{'first':首,'second':第二})
    标题=翻译('message.stepProcess.comma').join([首]+[续写(项) for 项 in 标签表[1:]])
    if len(摘要['counts'])>3:
        return 翻译('message.stepProcess.more',{'title':标题})
    return 标题
