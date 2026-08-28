"""命令界面插件，节点半边。

对齐上游 `@deepseek-ai/dsh-client-ui-commands`。公开面仅中文名。纯界面插件：空 apply 仅占 Loader 行；浏览器半边经 exports["./client"] 发出。宿主命令注册表本身另行挂载（bootHost + CommandUiRuntime）。
"""

__all__=['应用']#仅中文公开名

def 应用():#宿主插件体
    """此命令界面插件无宿主侧行为。"""
    return#空 apply，仅占 Loader 行
