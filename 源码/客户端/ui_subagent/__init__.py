"""子智能体引用插件的节点半边。

对齐上游 `@deepseek-ai/dsh-client-ui-subagent`。公开面仅中文名。空 apply 只为让插件出现在宿主 cordis.yml / Loader 里；浏览器半经上游 client 入口交付，本 Python 迁移不承载 React/CSS UI。
"""

__all__=['应用']#仅中文公开名

def 应用():#宿主插件体——本源插件无宿主侧行为
    """空 apply，仅占 Loader 行。"""
    return#无贡献
