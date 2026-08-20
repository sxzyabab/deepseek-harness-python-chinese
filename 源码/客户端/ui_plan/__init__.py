"""计划控件插件，节点半边。

对齐上游 `@deepseek-ai/dsh-client-ui-plan`。公开面仅中文名。纯界面插件：空 apply 仅占 Loader 行。计划行为本身（/plan 命令、计划投影单元、策略段）由 `@deepseek-ai/dsh-plan-mode` 拥有，在宿主名册上独立组合。
"""

__all__=['应用']#仅中文公开名

def 应用():#宿主插件体
    """此界面插件无宿主侧行为。"""
    return#空 apply，仅占 Loader 行
