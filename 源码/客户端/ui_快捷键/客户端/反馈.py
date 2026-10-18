'直接移除和行内改键共用的失败文案。展示只用中文表'
from .文案 import 中文

__all__=['快捷键读取失败','快捷键失败']

def 套用(键,位置=None,重载=None,命令们=None):
    '按中文表原文填占位。键不在表里就原样返回'
    if 键 not in 中文:
        return 键
    文=中文[键]
    if 位置 is None and 重载 is None and 命令们 is None:
        return 文
    return 文.format(location=位置,reload=重载,commands=命令们)

def 快捷键读取失败(配置,运行时):
    '标明读不到的偏好、恢复办法，以及现在还在用的键位'
    if 运行时=='desktop':
        位置=中文['desktop-document']
        重载=中文['desktop-reload']
    else:
        位置=中文['web-document']
        重载=中文['web-reload']
    错误键=配置['error'] if 配置['error'] is not None else 'read'
    if 配置['usingDefaults']:
        使用句=中文['using-defaults']
    else:
        使用句=中文['using-accepted']
    return 套用(错误键,位置,重载)+' '+使用句

def 快捷键失败(结果,目录,运行时):
    '描述没写成的偏好。命令名留在句子里'
    if 结果['status']=='unreadable':
        return 快捷键读取失败(结果['snapshot'],运行时)
    议题=结果['issue'] if 'issue' in 结果 else None
    if 议题:
        return 中文[议题] if 议题 in 中文 else 议题
    if 结果['status']=='conflict':
        冲突=结果['conflicts'] if 'conflicts' in 结果 and 结果['conflicts'] is not None else []
        名表=[]
        for 标识 in 冲突:
            名=标识
            for 项 in 目录:
                if 项['id']==标识:
                    名=项['label']
                    break
            名表.append(名)
        return 套用('conflict',命令们=', '.join(名表))
    状态=结果['status']
    if 状态 in 中文:
        return 中文[状态]
    return 状态
