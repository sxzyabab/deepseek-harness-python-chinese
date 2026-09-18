__all__=['命名空间','中文','英文']#仅中文公开名

命名空间='settings.pluginInventory'#词表命名空间

中文={#简体中文词条
    'tab':'插件列表',#设置分区标签
    'loading':'正在读取插件…',#读取中
    'clientSyncing':'正在同步本页面的插件…',#本页插件同步中
    'clientSyncFailed':'本页面的插件未能完成同步；服务端的启用状态保持不变。',#本页同步失败
    'clientSyncRetry':'重试本页面同步',#重试本页同步
    'error':'暂时无法读取插件。',#读取失败
    'retry':'重试',#重试
    'search':'搜索插件',#搜索框占位
    'empty':'暂无插件。',#无插件
    'emptySearch':'没有匹配的插件。',#搜索无匹配
    'presetTitle':'会话插件',#会话插件标题
    'presetSubtitle':'由 Agent 预设按会话组成',#会话插件副标题
    'countUnit':'个',#数量单位
    'switcherLabel':'选择要查看的 Agent 预设',#预设切换无障碍名
    'presetOptionDefault':'{name}（默认）',#默认预设选项
    'presetOptionBroken':'{name}（加载失败）',#加载失败预设选项
    'globalTitle':'全局插件',#全局插件标题
    'globalSubtitle':'系统与所有会话共用',#全局插件副标题
    'presetProvidedDetail':'全局已停用，由 Agent 预设按会话提供',#由预设按会话提供的说明
    'enabledIn':'启用于',#启用于某预设
    'viewInPreset':'去预设分组查看',#跳转预设分组
    'matchesInOtherPresets':'其他预设中还有 {count} 个匹配：',#其它预设匹配提示
    'failedCountLabel':'个失败',#失败计数标签
    'enabledTag':'已启用',#已启用徽章
    'disabledTag':'已停用',#已停用徽章
    'conditionalTag':'条件启用',#条件启用徽章
    'presetEnabledTag':'预设中启用',#预设中启用徽章
    'failedTag':'启动失败',#启动失败徽章
    'moduleLabel':'完整名称',#模块完整名标签
    'fromPreset':'来自',#来自预设
    'condition':'禁用条件',#禁用条件标签
    'configuration':'配置状态',#配置状态列
    'runtime':'运行状态',#运行状态列
    'unobserved':'未运行',#未运行阶段
    'pending':'等待依赖',#等待依赖阶段
    'loadingPhase':'加载中',#加载中阶段
    'active':'运行中',#运行中阶段
    'failed':'启动失败',#启动失败阶段
    'unloading':'卸载中',#卸载中阶段
}#中文结束

英文={#英文词条
    'tab':'Plugin list',#设置分区标签
    'loading':'Reading plugins…',#读取中
    'clientSyncing':'Syncing plugins on this page…',#本页插件同步中
    'clientSyncFailed':'Some plugins could not sync on this page. Host enablement is unchanged.',#本页同步失败
    'clientSyncRetry':'Retry this page',#重试本页同步
    'error':'Plugins are temporarily unavailable.',#读取失败
    'retry':'Retry',#重试
    'search':'Search plugins',#搜索框占位
    'empty':'No plugins are available.',#无插件
    'emptySearch':'No matching plugins.',#搜索无匹配
    'presetTitle':'Session plugins',#会话插件标题
    'presetSubtitle':'Composed per session by agent presets',#会话插件副标题
    'countUnit':'plugins',#数量单位
    'switcherLabel':'Choose the agent preset to inspect',#预设切换无障碍名
    'presetOptionDefault':'{name} (default)',#默认预设选项
    'presetOptionBroken':'{name} (failed to load)',#加载失败预设选项
    'globalTitle':'Global plugins',#全局插件标题
    'globalSubtitle':'Shared by the system and every session',#全局插件副标题
    'presetProvidedDetail':'Disabled globally; agent presets provide it per session',#由预设按会话提供的说明
    'enabledIn':'Enabled in',#启用于某预设
    'viewInPreset':'View in the preset group',#跳转预设分组
    'matchesInOtherPresets':'{count} more matches in other presets: ',#其它预设匹配提示
    'failedCountLabel':'failed',#失败计数标签
    'enabledTag':'Enabled',#已启用徽章
    'disabledTag':'Disabled',#已停用徽章
    'conditionalTag':'Conditional',#条件启用徽章
    'presetEnabledTag':'Enabled via presets',#预设中启用徽章
    'failedTag':'Failed',#启动失败徽章
    'moduleLabel':'Module',#模块完整名标签
    'fromPreset':'From',#来自预设
    'condition':'Disabled when',#禁用条件标签
    'configuration':'Configuration',#配置状态列
    'runtime':'Status',#运行状态列
    'unobserved':'Not running',#未运行阶段
    'pending':'Waiting for dependencies',#等待依赖阶段
    'loadingPhase':'Loading',#加载中阶段
    'active':'Running',#运行中阶段
    'failed':'Failed to start',#启动失败阶段
    'unloading':'Unloading',#卸载中阶段
}#英文结束
