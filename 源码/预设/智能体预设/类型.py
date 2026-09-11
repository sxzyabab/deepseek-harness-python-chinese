"""智能体预设域拥有的、对客户端安全的载荷与事件声明（纯文档模块）。

对齐上游 `agent-presets/src/types.ts`。公开面仅中文名。

名册行：id、trust、isDefault，可选 name/description/broken。
名册快照：presets、authorable、modeSelectionEnabled（未点名新会话是否启用可见模式选择）。
预设文档：agentPreset、trust、content，可选 name/description。

事件 `agent-preset/selected(sessionId, agentPreset)`：某会话已把不同的智能体预设提交进耐久日志。
"""
__all__=[]#无运行时导出
