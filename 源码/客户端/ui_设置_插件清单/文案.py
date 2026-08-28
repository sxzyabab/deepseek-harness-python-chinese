"""插件清单设置分区的文案词典。



对齐上游 `ui-settings-plugin-inventory/src/client/locales.ts`。公开面仅中文公开名。

"""



__all__=['命名空间','中文','英文']#仅中文公开名



命名空间='settings.pluginInventory'#词表命名空间



中文={#简体中文词条

    'tab':'插件列表',#设置分区标签

    'loading':'正在读取插件…',#读取中

    'error':'暂时无法读取插件。',#读取失败

    'retry':'重试',#重试

    'search':'搜索插件',#搜索框占位

    'catalog':'插件列表',#插件列表标题

    'empty':'暂无插件。',#无插件

    'emptySearch':'没有匹配的插件。',#搜索无匹配

    'enabledTag':'已启用',#已启用徽章

    'disabledTag':'已停用',#已停用徽章

    'configuration':'配置状态',#配置状态列

    'cordis':'Cordis 状态',#Cordis 状态列

    'unobserved':'未挂载',#未挂载阶段

    'pending':'等待依赖',#等待依赖阶段

    'loadingPhase':'加载中',#加载中阶段

    'active':'已挂载',#已挂载阶段

    'failed':'挂载失败',#挂载失败阶段

    'unloading':'卸载中',#卸载中阶段

}#中文结束



英文={#英文词条

    'tab':'Plugin list',#设置分区标签

    'loading':'Reading plugins…',#读取中

    'error':'Plugins are temporarily unavailable.',#读取失败

    'retry':'Retry',#重试

    'search':'Search plugins',#搜索框占位

    'catalog':'Plugin list',#插件列表标题

    'empty':'No plugins are available.',#无插件

    'emptySearch':'No matching plugins.',#搜索无匹配

    'enabledTag':'Enabled',#已启用徽章

    'disabledTag':'Disabled',#已停用徽章

    'configuration':'Configuration',#配置状态列

    'cordis':'Cordis status',#Cordis 状态列

    'unobserved':'Not mounted',#未挂载阶段

    'pending':'Waiting for dependencies',#等待依赖阶段

    'loadingPhase':'Loading',#加载中阶段

    'active':'Mounted',#已挂载阶段

    'failed':'Mount failed',#挂载失败阶段

    'unloading':'Unloading',#卸载中阶段

}#英文结束


