"""智能体预设界面插件，节点半边。

对齐上游 `@deepseek-ai/dsh-client-ui-agent-preset`。公开面仅中文名。空 apply 只是为了让插件出现在宿主 cordis.yml / Loader 里；浏览器半边经 exports["./client"] 把通用设置行交出去。
"""

__all__=['应用']#仅中文公开名

def 应用():#宿主插件体
    """此界面插件无宿主侧行为。"""
    return#空 apply，仅占 Loader 行
