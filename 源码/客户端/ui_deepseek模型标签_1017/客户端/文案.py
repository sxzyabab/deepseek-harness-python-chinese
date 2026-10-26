__all__=['中文','英文','日文','西班牙文','法文','德文','俄文','葡萄牙文','中文句']

中文={'badge.label':'1017'}

英文={'badge.label':'1017'}

日文={'badge.label':'1017'}

西班牙文={'badge.label':'1017'}

法文={'badge.label':'1017'}

德文={'badge.label':'1017'}

俄文={'badge.label':'1017'}

葡萄牙文={'badge.label':'1017'}

def 中文句(键,参数=None):
    '按中文表原文填占位。界面不读英文表'
    模板=中文[键]
    if 参数 is None:
        return 模板
    结果=模板
    for 名,值 in 参数.items():
        结果=结果.replace('{'+名+'}','' if 值 is None else str(值))
    return 结果
