'安装方选择、提供、按需安装或退役的组合包名'
from typing import TypedDict#配置档模板的字段

__all__=[#仅中文公开名
    '配置档模板','配置档模板表','安装持有配置档元组','已退役组合包','默认配置档组合包','可选组合包','按需组合包',
]#公开面结束

class 配置档模板(TypedDict):#随附配置档首次打开时使用的安装方默认值
    '随附配置档首次打开时使用的安装方默认值'
    bundles:list#有序组合包层列表

配置档模板表={#按名称索引、首次使用时自动初始化的随附配置档模板
    'acp':{'bundles':['@deepseek-ai/dsh-base','@deepseek-ai/dsh-acp-app']},#acp
    'web':{'bundles':['@deepseek-ai/dsh-base','@deepseek-ai/dsh-web-app']},#web
    'headless':{'bundles':['@deepseek-ai/dsh-base','@deepseek-ai/dsh-headless']},#headless
    'sdk':{'bundles':['@deepseek-ai/dsh-base','@deepseek-ai/dsh-sdk-app']},#sdk
    'sdk-minimal':{'bundles':['@deepseek-ai/dsh-sdk-minimal']},#sdk-minimal
}#模板结束

#早期版本写入随附配置档的安装方组合包元组；app-boot 只把完全一致的列表换成同名配置档模板，其余列表不动
安装持有配置档元组={
    'headless':['@deepseek-ai/dsh-base','@deepseek-ai/dsh-web-app','@deepseek-ai/dsh-headless'],#headless 旧元组
}#元组结束

#早期版本随附、安装不再携带的组合包；app-boot 从配置档里移除它们
#Web 组合自己挂载 Schedule
已退役组合包={
    '@deepseek-ai/dsh-experimental-schedule-bundle',
}#退役结束

默认配置档组合包=['@deepseek-ai/dsh-base']#没有随附模板的名称，dsh plugin init 使用的组合包列表

#安装随附、供人打开的组合包：须是安装的运行时依赖，声明 dsh.bundle.patch、icon 与 ./locale/*.json，且不被任何随附模板选中；除没有页面开关的持久终端外，插件管理器默认关闭
可选组合包=[
    '@deepseek-ai/dsh-personalized-recommendations',
    '@deepseek-ai/dsh-cua-bundle',
    '@deepseek-ai/dsh-experimental-session-search',
    '@deepseek-ai/dsh-experimental-ralph-bundle',
    '@deepseek-ai/dsh-experimental-terminal-bundle',
    '@deepseek-ai/dsh-experimental-badge-skill-bundle',
    '@deepseek-ai/dsh-experimental-session-titles-bundle',
    '@deepseek-ai/dsh-experimental-agent-team-profile',
    '@deepseek-ai/dsh-experimental-voice-input-bundle',
    '@deepseek-ai/dsh-experimental-cot-translation-bundle',
    '@deepseek-ai/dsh-experimental-auto-review',
    '@deepseek-ai/dsh-experimental-inspector-profile',
    '@deepseek-ai/dsh-experimental-plugin-market-bundle',
    '@deepseek-ai/dsh-experimental-tool-worktree',
]#可选结束

#可通过普通按需组合包安装器获得的公开 DSH 发行成员
按需组合包=[
    '@deepseek-ai/dsh-subagent-claude-code',
    '@deepseek-ai/dsh-subagent-codex',
]#按需结束
