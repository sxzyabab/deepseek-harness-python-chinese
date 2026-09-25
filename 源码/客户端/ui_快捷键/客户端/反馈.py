"""直接移除与行内改键共用的本地化失败文案。"""

__all__=['快捷键读取失败','快捷键失败']

def 快捷键读取失败(配置,运行时,翻译):
    """标明不可读偏好、恢复路径，以及仍在使用的绑定。"""
    位置=翻译('desktop-document' if 运行时=='desktop' else 'web-document')
    重载=翻译('desktop-reload' if 运行时=='desktop' else 'web-reload')
    错误键=配置['error'] if 配置.get('error') is not None else 'read'
    使用键='using-defaults' if 配置.get('usingDefaults') else 'using-accepted'
    return 翻译(错误键,{'location':位置,'reload':重载})+' '+翻译(使用键)

def 快捷键失败(结果,目录,翻译,运行时):
    """描述未成功的偏好写入，不丢失命令名。"""
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
