'直接移除与行内改键共用的本地化失败文案'
import os

__all__=['快捷键读取失败','快捷键失败','页面失败文案']

def 页面失败文案(错误):
    '页面上给调用方看的失败句。去掉绝对路径、用户名和环境变量，其余原文保留。'
    if isinstance(错误,BaseException):
        名=type(错误).__name__
        原文=str(错误.args[0]) if len(错误.args)>0 else ''
    else:
        名=''
        原文=str(错误)
    屏蔽名=set(os.environ)
    屏蔽值=set()
    for 键 in ('USERNAME','USER','LOGNAME','USERPROFILE','HOME'):
        值=os.environ.get(键)
        if isinstance(值,str) and 值!='':
            屏蔽值.add(值)
            基=os.path.basename(值.rstrip('\\/'))
            if 基!='':
                屏蔽值.add(基)
    for 值 in os.environ.values():
        if isinstance(值,str) and (len(值)>=8 or '\\' in 值 or '/' in 值):
            屏蔽值.add(值)
    留下=[]
    for 词 in 原文.split():
        裸=词.strip('\'"')
        统一=裸.replace('\\','/')
        if 统一.startswith('/') or 统一.startswith('~/') or (len(统一)>2 and 统一[0].isalpha() and 统一[1]==':' and 统一[2]=='/'):
            continue
        if 裸.startswith('$') and len(裸)>1:
            continue
        if len(裸)>2 and 裸.startswith('%') and 裸.endswith('%'):
            continue
        if '=' in 裸 and 裸.split('=',1)[0] in 屏蔽名:
            continue
        if 裸 in 屏蔽名 or 裸 in 屏蔽值 or 统一 in 屏蔽值:
            continue
        含敏感=False
        for 项 in 屏蔽值:
            if len(项)>=3 and 项 in 裸:
                含敏感=True
                break
        if 含敏感:
            continue
        留下.append(词)
    说明=' '.join(留下).strip()
    if 说明=='':
        return 名 if 名!='' else '失败'
    return 说明

def 快捷键读取失败(配置,运行时,翻译):
    '标明不可读偏好、恢复路径，以及仍在使用的绑定'
    位置=翻译('desktop-document' if 运行时=='desktop' else 'web-document')
    重载=翻译('desktop-reload' if 运行时=='desktop' else 'web-reload')
    错误键=配置['error'] if 配置.get('error') is not None else 'read'
    使用键='using-defaults' if 配置.get('usingDefaults') else 'using-accepted'
    return 翻译(错误键,{'location':位置,'reload':重载})+' '+翻译(使用键)

def 快捷键失败(结果,目录,翻译,运行时):
    '描述未成功的偏好写入，不丢失命令名'
    if 结果['status']=='unreadable':
        return 快捷键读取失败(结果['snapshot'],运行时,翻译)
    议题=结果.get('issue')
    if 议题:
        return 翻译(议题)
    if 结果['status']=='conflict':
        冲突=结果.get('conflicts') or []
        名表=[]
        for 标识 in 冲突:
            行=None
            for 项 in 目录:
                if 项.get('id')==标识:
                    行=项
                    break
            名表.append(行['label'] if 行 is not None and 'label' in 行 else 标识)
        return 翻译('conflict',{'commands':', '.join(名表)})
    return 翻译(结果['status'])

shortcutReadFailure=快捷键读取失败
shortcutFailure=快捷键失败
