"""外壳 chrome 与通用导航词典。

对齐上游 `ui-settings-general/src/client/locales.ts`。公开面仅中文名。
"""

__all__=['命名空间','中文','英文']#仅中文公开名

命名空间='settings'#词表命名空间

中文={#简体中文词条
    'trigger':'设置',#打开设置触发器
    'title':'设置',#设置面板标题
    'close':'关闭',#关闭设置
    'openDocument':'打开配置文件',#打开配置文件
    'openDocument.error':'无法打开配置文件',#打开配置文件失败
    'general.nav':'通用设置',#通用设置导航
}#中文结束

英文={#英文词条
    'trigger':'Settings',#打开设置触发器
    'title':'Settings',#设置面板标题
    'close':'Close',#关闭设置
    'openDocument':'Open configuration file',#打开配置文件
    'openDocument.error':'Could not open configuration file',#打开配置文件失败
    'general.nav':'General',#通用设置导航
}#英文结束
