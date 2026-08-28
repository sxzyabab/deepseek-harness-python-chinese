"""工作区选择器插件的节点半边。

纯 UI 插件：空 apply 存在是为了让插件出现在宿主 cordis.yml / Loader 中。

对齐上游 `@deepseek-ai/dsh-client-ui-workspace`。公开面仅中文名。
"""

__all__=['应用']#仅中文公开名

def 应用():#空 apply，仅占 Loader 行
    """宿主插件体——工作区选择器插件无宿主侧行为。"""
    return#无宿主侧行为
