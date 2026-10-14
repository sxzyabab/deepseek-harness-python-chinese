'不改变原始检查数据的、按类型的横向预览'

__all__=['预览上限','检查器预览']

def 失败说明(错误):
    '失败句去掉绝对路径，其余原文保留'
    if isinstance(错误,BaseException) and len(错误.args)>0:
        原文=str(错误.args[0])
    else:
        原文=str(错误)
    留下=[]
    for 词 in 原文.split():
        去引=词.strip('\'"()[]{}<>')
        统一=去引.replace('\\','/')
        if 统一.startswith('/') or 统一.startswith('~'):
            continue
        if len(统一)>2 and 统一[0].isalpha() and 统一[1]==':' and 统一[2]=='/':
            continue
        留下.append(词)
    说明=' '.join(留下).strip()
    if 说明!='':
        return 说明
    if isinstance(错误,BaseException):
        return type(错误).__name__
    return '失败'

预览上限=240

增量预览字段={
    'tool-call-delta':('argumentsDelta',),
    'reasoning-delta':('text',),
}

def 预览(值,深度,隐藏根字段):
    '按深度裁剪一段横向预览'
    if isinstance(值,str):
        return 值[:180]
    if 值 is None or not isinstance(值,(dict,list)):
        return str(值)
    if 深度>1:
        return f'[{len(值)}]' if isinstance(值,list) else '{…}'
    字段=None
    if isinstance(值,dict) and isinstance(值.get('type'),str):
        字段=增量预览字段.get(值['type'])
    if isinstance(值,dict):
        原始=list(值.items())
    else:
        原始=[(str(下标),项) for 下标,项 in enumerate(值)]
    条目=[]
    for 键,项 in 原始:
        if 深度==0 and (键.lower()=='time' or 键 in 隐藏根字段):
            continue
        if 字段 is None:
            if 键.lower() in ('type','seq','sequence'):
                continue
        elif 键 not in 字段:
            continue
        条目.append((键,项))
    if len(条目)==1:
        return 预览(条目[0][1],深度+1,隐藏根字段)
    片段=[f'{键}: {预览(项,深度+1,隐藏根字段)}' for 键,项 in 条目[:5]]
    return ' · '.join(片段)[:预览上限]

def 检查器预览(值,隐藏根字段=None):
    '用类型专用增量字段和有界嵌套格式化横向数据'
    if 隐藏根字段 is None:
        隐藏根字段=()
    return 预览(值,0,隐藏根字段)
