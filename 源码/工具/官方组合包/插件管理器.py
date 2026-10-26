'插件管理器保护、隐藏、排序或标为实验性的包名'

__all__=[#仅中文公开名
    '受保护插件','隐藏组合包','扩展组合包','更多组合包','实验组合包',
]#公开面结束

#管理功能自身依赖这些插件，插件管理器拒绝禁用或移除；包含其中之一的组合包同样只读。去掉一个名字只取消这一条 management-required 拒绝
受保护插件={
    '@deepseek-ai/dsh-plugin-manager','@deepseek-ai/cordis-plugin-loader',
    '@deepseek-ai/cordis-plugin-include','@deepseek-ai/dsh-api-gateway',
    '@deepseek-ai/dsh-host-webserver','@deepseek-ai/dsh-client-modules',
    '@deepseek-ai/dsh-client-ui-settings-plugin-inventory','@deepseek-ai/dsh-client-ui-plugin-manager',
    '@deepseek-ai/dsh-host-plugin-inventory','@deepseek-ai/dsh-typert-registry',
    '@deepseek-ai/dsh-api-remotes','@deepseek-ai/dsh-api-remote-access',
    '@deepseek-ai/cordis-plugin-timer','@deepseek-ai/dsh-client-connection',
    '@deepseek-ai/dsh-host-frontend-static','@deepseek-ai/dsh-tools',
    '@deepseek-ai/dsh-hmr',
}#受保护结束

#内建配置档组合包与持久终端，没有插件管理器页面。宿主可用性与激活保持不变
隐藏组合包={
    '@deepseek-ai/dsh-base',
    '@deepseek-ai/dsh-web-app',
    '@deepseek-ai/dsh-headless',
    '@deepseek-ai/dsh-sdk-app',
    '@deepseek-ai/dsh-acp-app',
    '@deepseek-ai/dsh-sdk-minimal',
    '@deepseek-ai/dsh-experimental-terminal-bundle',
}#隐藏结束

#插件管理器主列表与更多列表按此顺序排在最前。是否出现在主列表由更多组合包决定，不由本列表决定
扩展组合包=[
    '@deepseek-ai/dsh-experimental-agent-team-profile',
    '@deepseek-ai/dsh-experimental-voice-input-bundle',
    '@deepseek-ai/dsh-experimental-plugin-market-bundle',
    '@deepseek-ai/dsh-experimental-auto-review',
]#扩展结束

#配置档启用之前，主列表不放这些可选组合包；包含全部合格组合包的更多列表按此顺序把它们排在最后
更多组合包=[
    '@deepseek-ai/dsh-personalized-recommendations',
    '@deepseek-ai/dsh-experimental-inspector-profile',
    '@deepseek-ai/dsh-cua-bundle',
    '@deepseek-ai/dsh-experimental-tool-worktree',
    '@deepseek-ai/dsh-experimental-cot-translation-bundle',
    '@deepseek-ai/dsh-experimental-session-search',
    '@deepseek-ai/dsh-experimental-session-titles-bundle',
    '@deepseek-ai/dsh-experimental-badge-skill-bundle',
    '@deepseek-ai/dsh-experimental-ralph-bundle',
    '@deepseek-ai/dsh-subagent-codex',
    '@deepseek-ai/dsh-subagent-claude-code',
]#更多结束

实验组合包={#插件管理器标上实验性徽章的官方组合包
    '@deepseek-ai/dsh-personalized-recommendations',
    '@deepseek-ai/dsh-cua-bundle',
    '@deepseek-ai/dsh-experimental-agent-team-profile',
    '@deepseek-ai/dsh-experimental-voice-input-bundle',
    '@deepseek-ai/dsh-experimental-auto-review',
    '@deepseek-ai/dsh-experimental-inspector-profile',
    '@deepseek-ai/dsh-experimental-tool-worktree',
    '@deepseek-ai/dsh-experimental-cot-translation-bundle',
    '@deepseek-ai/dsh-experimental-session-search',
    '@deepseek-ai/dsh-experimental-session-titles-bundle',
    '@deepseek-ai/dsh-experimental-badge-skill-bundle',
    '@deepseek-ai/dsh-experimental-ralph-bundle',
    '@deepseek-ai/dsh-experimental-plugin-market-bundle',
}#实验结束
