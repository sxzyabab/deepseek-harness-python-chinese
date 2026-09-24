__all__=['设置命名空间','中文','英文','主题文案键']

设置命名空间='settings.theme'#外观行与字号行文案命名空间

中文={
    'appearance.title':'外观',
    'appearance.light':'浅色',
    'appearance.dark':'深色',
    'appearance.system':'跟随系统',
    'fontSize.title':'字号大小',
    'fontSize.description':'仅影响会话内容的字号',
    'fontSize.unit':'px',
    'fontSize.increase':'增大字号',
    'fontSize.decrease':'减小字号',
}

英文={
    'appearance.title':'Appearance',
    'appearance.light':'Light',
    'appearance.dark':'Dark',
    'appearance.system':'System',
    'fontSize.title':'Font size',
    'fontSize.description':'Only affects conversation content',
    'fontSize.unit':'px',
    'fontSize.increase':'Increase font size',
    'fontSize.decrease':'Decrease font size',
}

主题文案键=tuple(中文.keys())
