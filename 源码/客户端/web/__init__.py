"""Web 壳库宿主入口。

对齐上游 `@deepseek-ai/dsh-client-web`。公开面仅中文名。

`AppWebEntry` 与模块表种子在浏览器半边；宿主面仅 Loader 登记。
"""
__all__=['应用']#仅中文公开名

def 应用():#宿主插件体
    """Vite 入口与模块表在浏览器半边；宿主无行为。"""
    return#空 apply
