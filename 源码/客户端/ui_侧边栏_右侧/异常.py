import os

class 右侧侧栏错误(Exception):
    '本包右侧侧栏接线失败'

def _空说明(名):
    '没有可显示的说明时，只留类型名'
    if 名!='':
        return 名
    return '失败'

def _含绝对路径(统一):
    'Unix、家目录、UNC、file 链接，以及单独盘符开头的路径'
    if 统一.startswith('file://') or 统一.startswith('//') or 统一.startswith('/') or 统一.startswith('~/'):
        return True
    长度=len(统一)
    for 序号 in range(1,长度-1):
        if 统一[序号]!=':' or 统一[序号+1]!='/':
            continue
        if not 统一[序号-1].isalpha():
            continue
        if 序号>=2 and 统一[序号-2].isalnum():
            continue
        return True
    return False

def 异常原文(错误):
    '页面上留下这次异常自己的说明。去掉绝对路径、用户名和环境变量。'
    文=str(错误).strip()
    名=type(错误).__name__ if isinstance(错误,BaseException) else ''
    if 文=='':
        return _空说明(名)
    用户名=set()
    for 键 in ('USER','USERNAME','LOGNAME'):
        值=os.environ.get(键)
        if isinstance(值,str) and 值!='':
            用户名.add(值)
    环境路径=[]
    for 值 in os.environ.values():
        if isinstance(值,str) and len(值)>=3 and (('\\' in 值) or ('/' in 值)):
            环境路径.append(值.replace('\\','/'))
    留下=[]
    for 词 in 文.split():
        裸=词.strip('\'"')
        统一=裸.replace('\\','/')
        if _含绝对路径(统一):
            continue
        if 统一.startswith('$') or (len(统一)>=3 and 统一[0]=='%' and 统一[-1]=='%'):
            continue
        if 裸 in 用户名 or 统一 in 用户名:
            continue
        命中环境=False
        for 片段 in 环境路径:
            if 片段!='' and 片段 in 统一:
                命中环境=True
                break
        if 命中环境:
            continue
        留下.append(词)
    说明=' '.join(留下).strip()
    if 说明=='':
        return _空说明(名)
    return 说明
