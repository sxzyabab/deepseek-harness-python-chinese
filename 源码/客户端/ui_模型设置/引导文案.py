"""产品级 GUI 引导事实的持久化设置常量与内测声明文案。

对齐上游 `ui-settings-models/src/onboarding-copy.ts`。公开面仅中文名。
"""

__all__=['欢迎通知设置命名空间','欢迎通知确认字段','欢迎通知版本','欢迎通知文案']#仅中文公开名

欢迎通知设置命名空间='ui-onboarding'#引导设置命名空间
欢迎通知确认字段='welcomeNoticeVersion'#欢迎声明确认版本字段
欢迎通知版本='2026-08-13.1'#当前欢迎声明版本

欢迎通知文案={#双语内测声明文案
    'zh':{#简体中文
        'title':'内测声明',#标题
        'body':'DeepSeek Harness 目前的 0.1 版本仍处在面向 Harness 开发者进行测试的阶段，还有许多地方需要持续改进和打磨，希望听取广大开发者的反馈建议。预计 DeepSeek Harness 的核心插件以及基础 API 都会在接下来的一段时间内快速迭代、持续演化。\n\n我们期待与全球开发者一起，在开源、开放、可复用、可组合的基础设施之上，共同探索智能上限。欢迎全球 Harness 开发者加入 DSH 插件生态。',#正文
        'continueLabel':'继续',#继续按钮
    },#中文结束
    'en':{#英文
        'title':'Internal Testing Notice',#标题
        'body':"DeepSeek Harness 0.1 remains in testing for Harness developers. Many areas need further improvement, and we welcome feedback from the developer community. DeepSeek Harness's core plugins and foundational APIs will continue to evolve rapidly over the coming months.\n\nWe look forward to exploring the limits of intelligence with developers around the world, building on open-source, open, reusable, and composable infrastructure. We welcome Harness developers everywhere to join the DSH plugin ecosystem.",#正文
        'continueLabel':'Continue',#继续按钮
    },#英文结束
}#文案结束
