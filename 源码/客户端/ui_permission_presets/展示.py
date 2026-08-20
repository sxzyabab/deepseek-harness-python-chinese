"""权限预设展示层。



对齐上游 `ui-permission-presets/src/client/presentation.ts`。公开面仅中文名。

"""



__all__=['完全访问预设','显示预设名','显示权限预设']#仅中文公开名



完全访问预设='danger-full-access'#需 GUI 风险门的预设机器值



def 显示预设名(名称):#kebab-case → Title Case

    """非 kebab 标签原样返回。"""

    import re#正则

    if not re.match(r'^[a-z0-9]+(-[a-z0-9]+)*$',名称):#非 kebab

        return 名称#原样

    return ' '.join(段[:1].upper()+段[1:] for 段 in 名称.split('-'))#Title Case



def 显示权限预设(值,名称):#按产品标签渲染

    """Full access 产品标签，或常规显示名。"""

    return 'Full access' if 值==完全访问预设 else 显示预设名(名称)#产品标签或常规


