__all__=['槽装配错误','页面失败文案']#仅中文公开名

def 页面失败文案(错误):
    '页面上给调用方看的失败句。去掉绝对路径，其余原文保留。'
    if isinstance(错误,BaseException):
        名=type(错误).__name__
        原文=str(错误)
    else:
        名=''
        原文=str(错误)
    行出=[]
    for 行 in 原文.split('\n'):
        前导=行[:len(行)-len(行.lstrip(' '))]
        留下=[]
        for 词 in 行.split():
            裸=词.strip('\'"')
            统一=裸.replace('\\','/')
            if 统一.startswith('/') or 统一.startswith('~/') or (len(统一)>2 and 统一[0].isalpha() and 统一[1]==':' and 统一[2]=='/'):
                continue
            留下.append(词)
        行出.append(前导+' '.join(留下).rstrip())
    说明='\n'.join(行出).strip()
    if 说明=='':
        return 名 if 名!='' else '失败'
    return 说明

class 槽装配错误(Exception):
    '必须逃出组件错误边界的渲染器装配失败'
    pass#基类消息即可

class 槽组装错误(Exception):
    '缺少渲染器组装依赖。边界会再抛'
    pass#无额外字段
