__all__=['设置命名空间','中文','英文','主题文案键']#仅中文公开名

设置命名空间='settings.theme'#外观行文案命名空间

中文={#简体中文词条（键集合的权威源）
    'appearance.title':'外观',#外观标题
    'appearance.light':'浅色',#浅色主题
    'appearance.dark':'深色',#深色主题
    'appearance.system':'跟随系统',#跟随系统
}#中文词典结束

英文={#英文词条，键与中文权威源一致
    'appearance.title':'Appearance',#外观标题
    'appearance.light':'Light',#浅色主题
    'appearance.dark':'Dark',#深色主题
    'appearance.system':'System',#跟随系统
}#英文词典结束

主题文案键=tuple(中文.keys())#由中文词典键推导的键域
