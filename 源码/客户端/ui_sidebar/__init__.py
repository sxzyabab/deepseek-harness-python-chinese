"""仅浏览器侧栏插件的宿主加载器入口。

对齐上游 `@deepseek-ai/dsh-client-ui-sidebar`。公开面仅中文名。
空 apply 只为让插件出现在宿主 cordis.yml / Loader 里；浏览器半见 `客户端/`。
"""

__all__=['应用']#仅中文公开名

def 应用():#宿主插件体——侧栏插件无宿主侧行为
    """空 apply，仅占 Loader 行。"""
    return#无贡献
