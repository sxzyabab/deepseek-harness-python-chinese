"""在应用中打开的浏览器表面，节点半边。

对齐上游 `@deepseek-ai/dsh-client-ui-open-in-app`。纯 UI 插件：空 apply
只为出现在宿主 cordis.yml / Loader；浏览器半经 客户端/ 导出，由包的
dsh.client 声明发现。所驱动的路由在宿主包 `@deepseek-ai/dsh-host-open-in-app`
（本树：宿主/在应用中打开）。
"""
__all__=['应用']#仅中文公开名

def 应用():#宿主插件体
    """本表面插件无宿主侧行为。"""
    return#空 apply

apply=应用#框架槽
