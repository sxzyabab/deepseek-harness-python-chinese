from ....预设.智能体预设注册表.展示 import 是否内置预设,预设展示文本#出厂名解析
from .指南文案 import 指南中文,指南英文#帮助正文

__all__=['命名空间','中文','英文','取中文','是否内置预设','预设展示文本']

命名空间='settings.agentPreset'#词表命名空间

中文={#界面实际取到的简体中文
    **指南中文,
    'builtInGroup':'内置',#内置组
    'customGroup':'自定义',#自定义组
    'sectionIntro':'选择 Agent 的工具和工作方式。日常任务用「标准模式」，扩展 DSH 的能力用「创造模式」。',#导语
    'seatHint':'选择新任务使用的 Agent 预设',#芯片提示
    'headerHint':'本任务的 Agent 预设，在任务开始时确定',#页眉提示
    'nav':'Agent 预设',#导航
    'setDefault':'设为新任务默认',#设默认
    'view':'查看配置',#查看
    'presetStandardName':'标准模式',#标准名
    'presetStandardDescription':'处理代码、文件和资料，适合大多数任务。Agent 会按需使用检索、编辑和终端等工具。',#标准述
    'presetPtcName':'PTC 模式',#PTC 名
    'presetPtcDescription':'包含标准模式的所有能力，更适合批量调用工具，并对结果进行筛选、整理、去重、统计或汇总的任务。',#PTC 述
    'presetMinimalName':'极简模式',#极简名
    'presetMinimalDescription':'Agent 使用终端和图片读取工具，并支持上下文压缩，适合测试和对比其基础表现。',#极简述
    'presetCordisName':'创造模式',#创造名
    'presetCordisDescription':'用对话定制 DSH：让 Agent 编写插件，添加新功能或界面；也能组合工具和提示词，创建自己的模式。',#创造述
    'inUse':'新任务默认',#新任务默认
    'noDescription':'暂无描述。',#无描述
    'brokenBadge':'加载失败',#失败徽章
    'switchRefused':'无法切换到「{name}」：{reason}',#切换拒绝
    'standardUnavailable':'标准模式不可用，请恢复该模式或选择其他可用模式。',#标准不可用
    'close':'关闭',#关闭
    'creatorDraft':'让 Agent 帮我创建预设模式',#创造起草
    'createPlugin':'让 Agent 创建插件',#创建插件
    'createPluginDescription':'进入创造模式，制作属于你的 DSH 插件',#说明
    'createPluginChecking':'正在确认创造模式是否可用',#检查中
    'createPluginUnavailable':'暂时不可用，请重新打开菜单重试',#不可用
    'createPluginMissing':'当前配置未提供创造模式',#缺失
}#中文结束

英文={#登记用英文表。页面显示不走这里
    **指南英文,
    'builtInGroup':'Built-in',#内置组
    'customGroup':'Custom',#自定义组
    'sectionIntro':'Choose the agent’s tools and how it works. Use Standard mode for everyday tasks, or Creator mode to add capabilities to DSH.',#导语
    'seatHint':'Choose the agent preset for your new task',#芯片提示
    'headerHint':'The agent preset chosen when this task started',#页眉提示
    'nav':'Agent presets',#导航
    'setDefault':'Set as new task default',#设默认
    'view':'View configuration',#查看
    'presetStandardName':'Standard mode',#标准名
    'presetStandardDescription':'Work with code, files, and information. Suitable for most tasks, with search, editing, terminal commands, and other tools available as needed.',#标准述
    'presetPtcName':'PTC mode',#PTC 名
    'presetPtcDescription':'Includes all Standard mode capabilities. Better suited to tasks that call tools in batches and then filter, organize, deduplicate, count, or summarize the results.',#PTC 述
    'presetMinimalName':'Minimal mode',#极简名
    'presetMinimalDescription':'The agent uses a terminal and image reading, with context compaction. Useful for testing and comparing its basic performance.',#极简述
    'presetCordisName':'Creator mode',#创造名
    'presetCordisDescription':'Customize DSH through conversation. Let the agent write plugins that add features or UI, or combine tools and prompts to create your own mode.',#创造述
    'inUse':'New task default',#新任务默认
    'noDescription':'No description.',#无描述
    'brokenBadge':'Failed to load',#失败徽章
    'switchRefused':'Could not switch to {name}: {reason}',#切换拒绝
    'standardUnavailable':'Standard mode is unavailable. Restore it or choose another available mode.',#标准不可用
    'close':'Close',#关闭
    'creatorDraft':'Let the agent help me create a preset',#创造起草
    'createPlugin':'Let the agent create a plugin',#创建插件
    'createPluginDescription':'Enter Creator mode and make your own DSH plugin',#说明
    'createPluginChecking':'Checking whether Creator mode is available',#检查中
    'createPluginUnavailable':'Temporarily unavailable. Reopen this menu to retry',#不可用
    'createPluginMissing':'Creator mode is not included in this configuration',#缺失
}#英文结束

def 取中文(键):
    '显示用的中文表原文'
    return 中文[键]#原文
