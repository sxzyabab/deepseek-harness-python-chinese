"""Cordis 动态插件卡片的 Node 半。

对齐上游 `@deepseek-ai/dsh-client-ui-cordis`。公开面仅中文名。空 apply 只为让插件出现在宿主 cordis.yml / Loader 里；浏览器半经上游 client 入口交付，本 Python 迁移不承载 React/CSS UI。
"""

__all__=['名称','应用']#仅中文公开名

名称='client-ui-cordis'#Cordis插件名（字面量）

def 应用():#宿主插件体——此界面插件在宿主侧无行为
    """空 apply，仅占 Loader 行。"""
    return#无贡献
